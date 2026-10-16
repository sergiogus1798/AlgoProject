"""The simulated distribution behind a z or a p, kept so nobody reruns a test to look at it."""

import hashlib
import io
import json
import re
from pathlib import Path
from typing import Any, cast

import numpy as np
import pandas as pd

from core.fsio import atomic_write
from core.store.write import locked

FILE = "distribuciones.parquet"
BINS = 200  # over the whole range of the draws, never clipped
EMPTY = np.array([], np.float32)
LISTS = (
    "draws",
    "low",
    "high",
    "edges",
)  # float lists: byte-stream-split halves them (measured)
SHARDS = (
    "distribuciones"  # per-strategy files of a deferred `merge`, until `consolidate`
)
TAIL = (
    100  # the lowest and the highest draws kept exact when the draws themselves are not
)


def record(
    test: str,
    metric: str,
    observed: float,
    drawn: np.ndarray,
    identity: str = "",
    raw: bool = True,
    strategy: str = "",
    mother: str = "",
    **where: object,
) -> dict[str, Any]:
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
    counts, edges = (
        np.histogram(fine, BINS) if len(fine) else (np.array([], int), np.array([]))
    )
    kept = fine.astype(np.float32)
    return {
        "identity": identity,
        "strategy": strategy,
        "mother": mother,
        "test": test,
        "metric": metric,
        "where": json.dumps(where, ensure_ascii=False, sort_keys=True, default=str),
        "observed": float(observed),
        "n": len(drawn),
        "n_finite": len(fine),
        "n_ge": int((drawn >= observed).sum()),
        "n_le": int((drawn <= observed).sum()),
        "mean": float(fine.mean()) if len(fine) else np.nan,
        "sd": float(fine.std(ddof=1)) if len(fine) > 1 else np.nan,
        "edges": edges.tolist(),
        "counts": counts.tolist(),
        "low": EMPTY if raw else kept[:TAIL],
        "high": EMPTY if raw else kept[-TAIL:],
        "draws": kept if raw else EMPTY,
    }


def _write(path: Path, df: pd.DataFrame) -> None:
    """The one writer of the parquet: whole or not at all (a truncated file would stop the next save)."""
    buf = io.BytesIO()
    df.to_parquet(
        buf,
        index=False,
        compression="zstd",
        compression_level=9,  # 19 took 24 s vs 1.6 s, file +6 %
        use_dictionary=[c for c in df.columns if c not in (*LISTS, "counts")],
        use_byte_stream_split=[f"{c}.list.element" for c in LISTS],
        row_group_size=1_000,  # one group of 42,538 rows held > 2**31 list elements: unreadable
    )
    atomic_write(path, buf.getvalue())


def save(folder: Path | None, rows: list[dict]) -> None:
    """Write a study's distributions beside its report, replacing those of the same tests.

    Args:
        folder: The study's report folder; None (a level run with no report) keeps nothing.
        rows: What `record` returned. Nothing is written for an empty list.

    A study that runs in parts (the gate's levels) calls this once per part: the rows of other
    tests already in the file stay. Read, change and rewrite happen under the folder's lock
    (re-entrant, so `merge` and `consolidate` hold it around this call without deadlock).
    """
    if not rows or folder is None:
        return
    new, path = pd.DataFrame(rows), Path(folder) / FILE
    with locked(Path(folder)):
        consolidate(folder)  # deferred rows are older than this save: fold them first
        if path.exists():
            old = pd.read_parquet(path)
            new = cast(
                pd.DataFrame,
                pd.concat(
                    [old[~old["test"].isin(list(set(new["test"])))], new],
                    ignore_index=True,
                ),
            )
        _write(path, new)


def _replace(old: pd.DataFrame, new: pd.DataFrame) -> pd.DataFrame:
    """`old` without the rows of `new`'s tests and strategies, then `new`: what a merge means."""
    gone = old["test"].isin(list(set(new["test"]))) & old["strategy"].isin(
        list(set(new["strategy"]))
    )
    return cast(pd.DataFrame, pd.concat([old[~gone], new], ignore_index=True))


def merge(folder: Path, rows: list[dict], defer: bool = False) -> None:
    """`save` for a run that covers only some strategies of a shared report folder.

    Args:
        folder: The study's report folder.
        rows: `record` rows, each with its `strategy`: the file's rows of the same tests and
            those strategies are replaced, every other row stays — a `--strategy` run keeps
            the population's.
        defer: True from a `--strategy` process: the rows go to their own file
            `distribuciones/<strategy>.parquet` (no shared file, so no lock fight and no
            rewriting of everyone's rows) and stay invisible until `consolidate(folder)` runs
            once at the end of the phase.
    """
    if not rows:
        return
    new = pd.DataFrame(rows)
    if defer:
        for name, part in new.groupby("strategy", sort=False, dropna=False):
            safe = re.sub(r"[^\w.-]", "_", str(name)) or "_"
            if (
                safe != name
            ):  # two names that sanitise alike (or None) must not share a file
                safe += "-" + hashlib.sha1(repr(name).encode()).hexdigest()[:8]
            shard = Path(folder) / SHARDS / f"{safe}.parquet"
            with locked(
                shard.parent
            ):  # two tests of one strategy at once: still one file
                _write(
                    shard,
                    _replace(pd.read_parquet(shard), part) if shard.exists() else part,
                )
        return
    path = Path(folder) / FILE
    with locked(
        Path(folder)
    ):  # `--strategy` runs side by side read, change and rewrite one file
        consolidate(folder)
        save(
            folder,
            (_replace(pd.read_parquet(path), new) if path.exists() else new).to_dict(
                "records"
            ),
        )


def consolidate(folder: Path) -> int:
    """Fold the deferred per-strategy files into `distribuciones.parquet`, once, and delete them.

    Args:
        folder: The study's report folder.

    Returns:
        How many strategy files were folded (0: nothing was deferred, nothing is touched).
    """
    folder = Path(folder)
    if not any((folder / SHARDS).glob("*.parquet")):  # the usual case: no lock, no I/O
        return 0
    with locked(folder), locked(folder / SHARDS):
        shards = sorted((folder / SHARDS).glob("*.parquet"))
        if not shards:
            return 0
        path = folder / FILE
        df = pd.read_parquet(path) if path.exists() else None
        for shard in shards:
            part = pd.read_parquet(shard)
            df = part if df is None else _replace(df, part)
        assert df is not None  # `shards` is not empty, so the loop below ran
        _write(path, df)
        for shard in shards:
            shard.unlink()
    return len(shards)


def read(folder: Path) -> pd.DataFrame | None:
    """The folder's distributions, deferred strategy files folded in first (one fold per burst).

    Returns:
        The rows of `distribuciones.parquet`; None when the folder has none.
    """
    consolidate(folder)
    path = Path(folder) / FILE
    return pd.read_parquet(path) if path.exists() else None


def reset(folder: Path) -> None:
    """Forget the folder's distributions: the parquet and every deferred strategy file.

    Whatever deletes or replaces `distribuciones.parquet` calls this, never `unlink` on `FILE`
    alone — a pending file would come back at the next read.
    """
    folder = Path(folder)
    with locked(folder), locked(folder / SHARDS):
        (folder / FILE).unlink(missing_ok=True)
        for shard in (folder / SHARDS).glob("*.parquet"):
            shard.unlink()
