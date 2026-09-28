"""The rows steps 17, 18 and 19 did not write, rebuilt from the results they left on disk."""

import json
import re
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from core.paths import DATA, report_dir
from ledger import study as studymod

SEGMENTS = ("build", "oos1", "oos2")   # all three read by each: WFC and CSCV over the batch's
                                       # joined curve, the WFM over build..oos2


def computed(file: Path) -> str:
    """When a study result was computed, in UTC like every live row's `ts`."""
    local = datetime.fromisoformat(json.loads(file.read_text(encoding="utf-8"))["computed_at"])
    return local.astimezone(timezone.utc).isoformat(timespec="seconds")


def rows(step: float, base: dict, n: int, ts: str, criterion: str, note: str) -> list[dict]:
    """One search as one row per segment it read, as `marketSurfaces` records itself."""
    return [{**base, "ts": ts, "step": step, "segment": s, "n_in": n, "n_out": n,
             "criterion": criterion, "note": note} for s in SEGMENTS]


def recorded(frame: pd.DataFrame, step: int, batch: Path) -> bool:
    """Whether the study already holds a live row of this step for this batch.

    Args:
        frame: What `study.read` returned.
        step: 17 or 18.
        batch: The variant batch.

    Returns:
        True when a row not marked `backfill` opens its note with `lote <batch name>` —
        the note `engines.variants.look.log` writes since 2026-09-27, when the WFC and the
        CSCV began to record their own look. Rebuilding it too would count one look twice.
    """
    notes = frame.loc[frame["step"] == step, "note"].fillna("")
    return bool(notes.str.match(rf"lote {re.escape(batch.name)}( ·|$)").any())


def from_batch(batch: Path, base: dict, frame: pd.DataFrame) -> list[dict]:
    """The WFC's and the CSCV's rows for one mother's variant batch.

    Args:
        batch: `strategyPermutations/<project>/<mother>/`, holding `wfc.json` and
            `cscv.json` and their contract results in `estudios/`.
        base: The fields every row shares.
        frame: The study's ledger as it stands; a step the batch already recorded live is
            not rebuilt.

    Returns:
        Their rows, soft: a correlation and a PBO read a batch and remove nobody, so
        `n_out = n_in` and the call goes in the note.
    """
    found = []
    if (batch / "wfc.json").exists() and not recorded(frame, 17, batch):
        w = json.loads((batch / "wfc.json").read_text(encoding="utf-8"))
        found += rows(17, {**base, "launched_by": "studies.optimisation.wfc.report"},
                      w["n"] + w["dropped"] + w["dropped_thin"],
                      computed(batch / "estudios" / "wfc.json"), "wfc/rho",
                      f"backfill · {batch.name} · {w['call']} rho {w['rho']:.3f} "
                      f"IC [{w['ci95'][0]:.3f}, {w['ci95'][1]:.3f}] · IS {w['in_sample']} "
                      f"OOS {w['out_of_sample']}")
    if (batch / "cscv.json").exists() and not recorded(frame, 18, batch):
        c = json.loads((batch / "cscv.json").read_text(encoding="utf-8"))
        found += rows(18, {**base, "launched_by": "studies.optimisation.cscv.report"},
                      c["n"], computed(batch / "estudios" / "cscv.json"), "cscv/pbo",
                      f"backfill · {batch.name} · PBO argmax {c['pbo_argmax']:.3f} "
                      f"DSR {c['dsr']:.3f} · {c['periods']} periodos {c['period']}")
    return found


def from_wfm(folder: Path, base: dict) -> list[dict]:
    """The WFM's rows, from one reading of its export.

    Args:
        folder: `reports/<project>/<databank>/<day>/wfm/`.
        base: The fields every row shares.

    Returns:
        Its rows, soft: the reading marks and deletes nobody (SQX's own area rule marks
        FAILED without deleting, by doctrine).
    """
    verdict = pd.read_csv(folder / "verdict.csv")
    first = sorted((folder / "estrategias").glob("*.json"))[0]
    return rows(19, {**base, "launched_by": "studies.optimisation.wfm.report"}, len(verdict),
                computed(first), "wfm/rho",
                f"backfill · {folder} · {verdict['verdict'].value_counts().to_dict()}")


def rebuild(project: str, wfm_databank: str, study: str, symbol: str,
            timeframe: str) -> list[dict]:
    """Every row 17, 18 and 19 would have written for one project.

    Args:
        project: Project name.
        wfm_databank: The WFM databank, as `studies.optimisation.wfm.report` read it.
        study: What `study.study_id` returned.
        symbol: The asset.
        timeframe: The build's grid.

    Returns:
        The rows, not yet written, each marked `backfill` in its note and stamped with its
        result's own computation time. The newest WFM reading is the one taken. A batch
        whose WFC or CSCV already wrote its own rows gets none rebuilt for that step.
    """
    base = {"study": study, "symbol": symbol, "timeframe": timeframe, "config_hash": None}
    frame = studymod.read(study)
    found = []
    for batch in sorted((DATA / "strategyPermutations" / project).iterdir()):
        found += from_batch(batch, base, frame)
    wfm = sorted(report_dir(project, wfm_databank, "x").parent.glob("*/wfm/verdict.csv"))[-1]
    return found + from_wfm(wfm.parent, base)
