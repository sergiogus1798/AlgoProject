"""The simulated distribution behind a z or a p, kept so nobody reruns a test to look at it."""

import json
import os
from pathlib import Path

import numpy as np
import pandas as pd

from core.store.write import locked

FILE = "distribuciones.parquet"
BINS = 200        # over the whole range of the draws, never clipped
EMPTY = np.array([], np.float32)
LISTS = ("draws", "low", "high", "edges")   # float lists: byte-stream-split halves them (measured)
TAIL = 100        # the lowest and the highest draws kept exact when the draws themselves are not


def record(test: str, metric: str, observed: float, drawn: np.ndarray, identity: str = "",
           raw: bool = True, strategy: str = "", mother: str = "", **where: object) -> dict:
    """One simulated distribution as a row: what `numpy.histogram` gives, and the tails exact.

    Args:
        test: The test that drew it, e.g. `gate.3c`.
        metric: The scorecard column it backs, e.g. `z_mono`.
        observed: The real run's statistic, on the draws' own scale.
        drawn: The same statistic over every simulated run.
        identity: The strategy, when the distribution is one strategy's.
        raw: Keep the draws themselves (sorted, float32 — some 11 KB per 5,000 on disk): any
            other binning or quantile can then be redone. False for what comes thousands at a
            time (a cell of a tensor): the histogram and the TAIL extremes of each side
            (`low`, `high`, empty when the draws are kept) stay.
        strategy: Its name in the project: what a table is cut by when the identity is not
            at hand (a step-12 sister is `<mother>_Scaled<TF>`).
        mother: The strategy a sister was scaled from; the store files the row under it.
        **where: What tells this distribution from its siblings (rung, market, timeframe,
            seed…), kept as JSON in `where`.

    Returns:
        `identity, strategy, mother, test, metric, where, observed, n, n_finite, n_ge, n_le, mean, sd, edges,
        counts, low, high, draws`. `counts` has BINS entries over [min, max] of the finite
        draws and `edges` one more; `n_ge` and `n_le` are how many draws reach the observed
        from each side, infinite ones included, counted before any rounding — the integers every
        empirical p is made of. No finite draw: empty
        lists, `n_finite` 0, never a histogram that looks healthy.
    """
    drawn = np.sort(np.asarray(drawn, float).ravel())
    fine = drawn[np.isfinite(drawn)]
    counts, edges = np.histogram(fine, BINS) if len(fine) else (np.array([], int), np.array([]))
    kept = fine.astype(np.float32)
    return {"identity": identity, "strategy": strategy, "mother": mother, "test": test, "metric": metric,
            "where": json.dumps(where, ensure_ascii=False, sort_keys=True, default=str),
            "observed": float(observed), "n": len(drawn), "n_finite": len(fine),
            "n_ge": int((drawn >= observed).sum()), "n_le": int((drawn <= observed).sum()),
            "mean": float(fine.mean()) if len(fine) else np.nan,
            "sd": float(fine.std(ddof=1)) if len(fine) > 1 else np.nan,
            "edges": edges.tolist(), "counts": counts.tolist(),
            "low": EMPTY if raw else kept[:TAIL], "high": EMPTY if raw else kept[-TAIL:],
            "draws": kept if raw else EMPTY}


def save(folder: Path | None, rows: list[dict]) -> None:
    """Write a study's distributions beside its report, replacing those of the same tests.

    Args:
        folder: The study's report folder; None (a level run with no report) keeps nothing.
        rows: What `record` returned. Nothing is written for an empty list.

    A study that runs in parts (the gate's levels) calls this once per part: the rows of other
    tests already in the file stay.
    """
    if not rows or folder is None:
        return
    new, path = pd.DataFrame(rows), Path(folder) / FILE
    if path.exists():
        old = pd.read_parquet(path)
        new = pd.concat([old[~old["test"].isin(set(new["test"]))], new], ignore_index=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    new.to_parquet(tmp, index=False, compression="zstd", compression_level=19,
                   use_dictionary=[c for c in new.columns if c not in (*LISTS, "counts")],
                   use_byte_stream_split=[f"{c}.list.element" for c in LISTS])
    os.replace(tmp, path)        # whole or not at all: a truncated file would stop the next save


def merge(folder: Path, rows: list[dict]) -> None:
    """`save` for a run that covers only some strategies of a shared report folder.

    Args:
        folder: The study's report folder.
        rows: `record` rows, each with its `strategy`: the file's rows of the same tests and
            those strategies are replaced, every other row stays — a `--strategy` run keeps
            the population's.
    """
    if not rows:
        return
    path, new = Path(folder) / FILE, pd.DataFrame(rows)
    with locked(Path(folder)):      # `--strategy` runs side by side read, change and rewrite one file
        if path.exists():
            old = pd.read_parquet(path)
            mine = old["strategy"].isin(set(new["strategy"]))
            rows = old[old["test"].isin(set(new["test"])) & ~mine].to_dict("records") + rows
        save(folder, rows)
