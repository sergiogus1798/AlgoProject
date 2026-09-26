"""The four withheld results of each mother — 17, 18, 18.5 and 19 — as their own studies said them."""

import json
from pathlib import Path

import pandas as pd

from core.paths import DATA, report_dir

# Each piece, the step it is, and where its result lives. The first three are written beside
# the mother's variant batch; the WFM reads SQX's own matrix, one export for every mother.
PIECES = {"wfc": 17, "cscv": 18, "marketSurfaces": 18.5, "wfm": 19}
NAMES = {"wfc": "WFC", "cscv": "CSCV", "marketSurfaces": "superficies", "wfm": "WFM"}


def batches(project: str) -> dict[str, Path]:
    """Every variant batch of the project, by the mother it was fabricated from.

    Args:
        project: Project name.

    Returns:
        {mother name as SQX spells it: batch folder}. The folder carries the mother's name
        with underscores (`Strategy_1.28.59`); the batch does not record the mother's
        identity, so the match with the WFM is by name.
    """
    root = DATA / "strategyPermutations" / project
    return {p.name.replace("_", " "): p for p in sorted(root.iterdir()) if p.is_dir()}


def wfm_report(project: str, databank: str) -> Path:
    """The newest reading of the project's WFM export.

    Args:
        project: Project name.
        databank: The WFM databank, as `studies.optimisation.wfm.report` was run on it.

    Returns:
        Its `wfm/` folder.
    """
    parent = report_dir(project, databank, "x").parent
    return sorted(parent.glob("*/wfm/verdict.csv"))[-1].parent


def said(file: Path) -> dict:
    """One piece's call, as the study that computed it wrote it.

    Args:
        file: A result JSON of the contract.

    Returns:
        label, state, the one-line meaning and when it was computed. The state is the
        study's own — step 20 reads it and never re-derives it, so a threshold lives in
        one place.
    """
    result = json.loads(file.read_text(encoding="utf-8"))
    verdict = result["verdict"]
    return {"label": verdict["label"], "state": verdict["state"],
            "score": verdict.get("score"), "meaning": verdict["meaning"],
            "computed_at": result["computed_at"], "summary": result.get("summary") or {}}


def population(project: str, wfm_databank: str) -> pd.DataFrame:
    """Every mother that reached step 20, with the pieces it has and those it lacks.

    Args:
        project: Project name.
        wfm_databank: As wfm_report() takes it.

    Returns:
        One row per mother: `identity` (from the WFM verdict), `batch`, `complete`,
        `missing` and one `<piece>` column holding what said() returned, or None. A mother
        is complete only with all four: WORKFLOW step 20 is blind until the four exist, so
        a mother with the WFM alone is listed and never read.
    """
    folder = wfm_report(project, wfm_databank)
    wfm = pd.read_csv(folder / "verdict.csv").set_index("strategy")
    found = batches(project)
    rows = []
    for mother in sorted(set(wfm.index) | set(found)):
        batch = found.get(mother)
        files = {p: batch / "estudios" / f"{p}.json" if batch else None
                 for p in ("wfc", "cscv", "marketSurfaces")}
        files["wfm"] = folder / "estrategias" / f"{mother}.json" if mother in wfm.index else None
        have = {p: f for p, f in files.items() if f is not None and f.exists()}
        missing = [p for p in PIECES if p not in have]
        rows.append({"mother": mother, "batch": batch,
                     "identity": wfm["identity"].get(mother) if mother in wfm.index else None,
                     "complete": not missing, "missing": missing,
                     # Read only when all four are there: an incomplete mother stays blind.
                     **{p: said(have[p]) if not missing else None for p in PIECES}})
    return pd.DataFrame(rows).set_index("mother").assign(wfm_source=str(folder))
