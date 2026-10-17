#!/usr/bin/env python3
"""Contract L2: what a sweep tried, not only what it chose -- one line per value tested."""

import argparse
import uuid
from datetime import datetime, timezone

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from core.store.write import locked
from ledger import shards, study as studymod
from ledger.trials import SHARPE_UNITS

KINDS = ("parameter", "threshold", "config", "template", "block")
SWEEP_UNIT = (
    "sweep"  # a look that adds to N and never reaches sigma (see trials.accumulated)
)

# Contract L2. A search_id groups the tests of one sweep; L1 stays one line per search.
COLUMNS = (
    "study",
    "ts",
    "step",
    "launched_by",
    "search_id",
    "kind",
    "name",
    "value",
    "input_hash",
    "config_hash",
    "score",
    "score_unit",
    "chosen",
    "provenance",
    "why",
    "fix",
)


def path(study: str) -> Path:
    """The study's L2 file: `ledger/tried/<study>.jsonl`, a folder `study.studies()` does not glob."""
    return studymod.path(study).parent / "tried" / f"{study}.jsonl"


def read(study: str) -> pd.DataFrame:
    """Every test ever recorded for one study, oldest first; empty with the contract's columns."""
    rows = shards.read_all(path(study))
    return (
        pd.DataFrame(rows, columns=pd.Index(COLUMNS))
        if not rows
        else pd.DataFrame(rows)
    )


def _append(study: str, rows: list[dict]) -> None:
    """Append the rows in one write, so two sessions never interleave half a sweep. Never rewrites."""
    file = shards.shard_path(path(study))  # one writer per file (D27)
    file.parent.mkdir(parents=True, exist_ok=True)
    with file.open("a", encoding="utf-8") as handle:
        handle.write("".join(shards.stamp(r) + "\n" for r in rows))


def _stamp(study: str, **row: object) -> dict[str, Any]:
    """One L2 line: every column present, the study and the time stamped."""
    return {
        **{k: None for k in COLUMNS},
        "study": study,
        "fix": False,
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        **row,
    }


def sweep(
    study: str,
    kind: str,
    name: str,
    values: list,
    launched_by: str,
    scores: list | None = None,
    score_unit: str | None = None,
    chosen: str | None = None,
    step: int | None = None,
    input_hash: str | None = None,
    config_hash: str | None = None,
    provenance: str = "propia",
    why: str = "",
    fix: bool = False,
) -> str:
    """Write one line per value a sweep tested, and which one was kept. The one writer of L2.

    Args:
        study: What `study.study_id` returned.
        kind: One of KINDS.
        name: The parameter, threshold, config, template or block swept.
        values: Every value tested, the chosen one included.
        launched_by: Who or what swept (session, agent, command line).
        scores: What each value scored, in the order of `values`; per observation when it is a Sharpe.
        score_unit: Its unit (`per_period`, `annualised`, or anything else, which counts but never
            reaches sigma). Defaults to `per_period` when scores are given.
        chosen: The value kept, or None for a sweep that only looked.
        provenance: Where the idea came from: propia, a book with its page, a paper, the web.
        why: The reason for the choice, kept on every line.
        fix: The sweep was repeated because the code failed, not as another attempt: it never counts.

    Returns:
        The `search_id` all the lines share.

    Raises:
        ValueError: Unknown kind, no values, scores of another length, or a chosen not among them.
    """
    if kind not in KINDS:
        raise ValueError(f"ledger.tried: kind {kind!r} no es uno de {KINDS}")
    if not values:
        raise ValueError("ledger.tried: un barrido sin valores no es un barrido")
    if scores is not None and len(scores) != len(values):
        raise ValueError("ledger.tried: tantas puntuaciones como valores")
    if chosen is not None and str(chosen) not in [str(v) for v in values]:
        raise ValueError(
            f"ledger.tried: el elegido {chosen!r} no está entre los valores probados"
        )
    sid = uuid.uuid4().hex[:12]
    unit = score_unit or ("per_period" if scores is not None else None)
    _append(
        study,
        [
            _stamp(
                study,
                step=step,
                launched_by=launched_by,
                search_id=sid,
                kind=kind,
                name=name,
                value=v,
                input_hash=input_hash,
                config_hash=config_hash,
                score=None if scores is None else scores[i],
                score_unit=unit,
                chosen=chosen is not None and str(v) == str(chosen),
                provenance=provenance,
                why=why,
                fix=fix,
            )
            for i, v in enumerate(values)
        ],
    )
    return sid


def note_run(
    study: str, module: str, input_hash: str, config_hash: str, launched_by: str
) -> str | None:
    """Record one run of a study module; a run over the same input under another config joins the first's search.

    Args:
        study: What `study.study_id` returned.
        module: The module's dotted name.
        input_hash: Fingerprint of what it read.
        config_hash: Fingerprint of the config it ran under (`core.study.config.fingerprint`).
        launched_by: As in `sweep`.

    Returns:
        The `search_id`, or None when this very run (same input, same config) was already noted.
        Running the gate three times with three thresholds is a sweep of three, and nobody has to say so.
    """
    with locked(
        path(study).parent
    ):  # read-then-append: two runs at once each opened their own search
        return _note_run(study, module, input_hash, config_hash, launched_by)


def _note_run(
    study: str, module: str, input_hash: str, config_hash: str, launched_by: str
) -> str | None:
    """Record a re-run (same module and input, new config) once; the search id, or None if already recorded."""
    seen = read(study)
    seen = pd.DataFrame(
        seen[
            (seen["kind"] == "config")
            & (seen["name"] == module)
            & (seen["input_hash"] == input_hash)
        ]
        if len(seen)
        else seen
    )
    if len(seen) and (seen["config_hash"] == config_hash).any():
        return None
    sid = seen["search_id"].iloc[0] if len(seen) else uuid.uuid4().hex[:12]
    _append(
        study,
        [
            _stamp(
                study,
                launched_by=launched_by,
                search_id=sid,
                kind="config",
                name=module,
                value=config_hash,
                input_hash=input_hash,
                config_hash=config_hash,
                chosen=True,
                provenance="propia",
                why="reejecución detectada",
            )
        ],
    )
    return sid


def note_project_run(
    project: str, module: str, input_key: str, cfg: dict, launched_by: str
) -> str:
    """`note_run` for a project's study, found through the registry; the line to print.

    Args:
        project: Project name, as `registry.csv` knows it.
        module: The module's dotted name.
        input_key: What identifies its input (a harvest folder, an export day).
        cfg: The parsed config with `--set` applied; its fingerprint tells one run from another.
        launched_by: As in `sweep`.
    """
    from core.study.config import fingerprint
    from ledger.steprows import signed

    sign = signed(project)
    if sign is None:
        return "Ledger: sin plantilla en registry.csv, la corrida no se compara con las anteriores"
    sid = note_run(
        sign[0], module, f"{project}|{input_key}", fingerprint(cfg), launched_by
    )
    return (
        "Ledger: misma entrada y misma configuración que una corrida ya apuntada"
        if sid is None
        else f"Ledger: corrida apuntada en {sign[0]} ({sid}); otra configuración sobre la misma "
        "entrada se cuenta como un ensayo más"
    )


def summary(study: str) -> pd.DataFrame:
    """One row per sweep: tests, the one chosen, and how many of them count toward N.

    A sweep counts only if something was chosen (a look that chose nothing counts nothing) and is
    not marked `fix`; a rerun group (`kind=config`) counts its runs after the first.

    Returns:
        `search_id, kind, name, probados, elegido, cuenta`.
    """
    frame = read(study)
    out = []
    g: pd.DataFrame
    for sid, g in pd.DataFrame(
        frame[~frame["fix"].astype(bool)] if len(frame) else frame
    ).groupby("search_id", sort=False):
        kept = g[g["chosen"].astype(bool)]
        runs = g["kind"].iloc[0] == "config"
        out.append(
            {
                "search_id": sid,
                "kind": g["kind"].iloc[0],
                "name": g["name"].iloc[0],
                "probados": len(g),
                "elegido": ", ".join(map(str, kept["value"])) if not runs else "",
                "cuenta": max(len(g) - 1, 0) if runs else (len(g) if len(kept) else 0),
            }
        )
    return pd.DataFrame(
        out,
        columns=pd.Index(
            ["search_id", "kind", "name", "probados", "elegido", "cuenta"]
        ),
    )


def as_rows(study: str) -> pd.DataFrame:
    """The counted sweeps as L1-shaped rows, for `trials.accumulated`: `n_scored`, Sharpe moments, unit.

    Scores in a Sharpe unit and at least two of them enter sigma; anything else (no scores, one
    score, another unit) is unit `sweep` and only raises N.
    """
    frame = read(study)
    counted = pd.Series(
        summary(study).set_index("search_id")["cuenta"]
        if len(frame)
        else pd.Series(dtype=int)
    )
    rows = []
    for sid, k in pd.Series(counted[counted > 0]).items():
        g = pd.DataFrame(
            frame[(frame["search_id"] == sid) & ~frame["fix"].astype(bool)]
        )
        score = pd.Series(pd.to_numeric(g["score"], errors="coerce")).to_numpy(float)
        unit = g["score_unit"].iloc[0]
        row = {
            "ts": g["ts"].iloc[0],
            "step": g["step"].iloc[0],
            "n_scored": int(k),
            "score_unit": SWEEP_UNIT,
        }
        if (
            unit in SHARPE_UNITS
            and np.isfinite(score).sum() >= 2
            and np.isfinite(score).sum() == k
        ):
            row |= {
                "score_unit": unit,
                "sharpe_mean": float(np.mean(score)),
                "sharpe_std": float(np.std(score, ddof=1)),
            }
        rows.append(row)
    return pd.DataFrame(
        rows,
        columns=pd.Index(
            ["ts", "step", "n_scored", "score_unit", "sharpe_mean", "sharpe_std"]
        ),
    )


def with_sweeps(frame: pd.DataFrame, study: str) -> pd.DataFrame:
    """`frame` (the L1 searches) plus the study's counted sweeps: what `trials.accumulated` should eat."""
    extra = as_rows(study)
    return pd.concat([frame, extra], ignore_index=True) if len(extra) else frame


def main() -> None:
    """Note a sweep done by hand, outside any command that records its own."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--study", required=True)
    ap.add_argument(
        "--name",
        required=True,
        help="the parameter, threshold, config, template or block",
    )
    ap.add_argument(
        "--values", required=True, help="every value tried, comma-separated"
    )
    ap.add_argument("--kind", default="parameter", choices=KINDS)
    ap.add_argument("--scores", help="what each scored, comma-separated, same order")
    ap.add_argument("--unit", help="scores' unit: per_period, annualised or any other")
    ap.add_argument(
        "--chosen", help="the value kept; leave out if the sweep only looked"
    )
    ap.add_argument("--why", default="", help="the reason for the choice")
    ap.add_argument("--step", type=int)
    ap.add_argument(
        "--provenance",
        default="propia",
        help="propia, a book and page, a paper, the web",
    )
    ap.add_argument("--by", default="mano", help="who swept")
    ap.add_argument(
        "--fix",
        action="store_true",
        help="repeated only because the code failed: not counted",
    )
    a = ap.parse_args()
    values = [v.strip() for v in a.values.split(",")]
    scores = [float(s) for s in a.scores.split(",")] if a.scores else None
    sid = sweep(
        a.study,
        a.kind,
        a.name,
        values,
        a.by,
        scores,
        a.unit,
        a.chosen,
        a.step,
        provenance=a.provenance,
        why=a.why,
        fix=a.fix,
    )
    row = summary(a.study).set_index("search_id").loc[sid] if not a.fix else None
    print(
        f"{a.study}: {len(values)} pruebas apuntadas ({sid})"
        + (
            f" · probados {row['probados']}, elegido {row['elegido'] or 'ninguno'}, cuentan {row['cuenta']}"
            if row is not None
            else " · marcado --fix, no cuenta"
        )
    )


if __name__ == "__main__":
    main()
