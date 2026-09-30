"""THE COMMAND: list every archivable survivor and near-survivor of every workflow step; runs none."""

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

from core.archive.read import versions
from core.datapaths import project_registry, variants_dir
from core.paths import DATA

# studies/CLAUDE.md's family table: which numbered workflow step a study's verdict.csv judges.
# `cloud`, `profitShape` and `entryQuality` are deliberately absent — WORKFLOW.md calls them
# extra readings, not steps, so they never enter the furthest-step count.
STUDY_STEP = {
    "gate": "8", "isOos": "8", "filters": "8", "replication": "8", "decay": "8",
    "monkeyExcess": "8", "snoopingScreen": "8", "feedQuality": "8", "spread": "8",
    "edgeCost": "8", "monkey": "8",
    "crossmarket": "10", "crossTF": "12", "mcRetest": "14", "spp": "16",
    "wfc": "17", "cscv": "18", "marketSurfaces": "18.5", "wfm": "19",
    "blindJoint": "20", "exposure": "21", "conditionalMap": "22", "structure": "23",
    "atrCalculator": "24",
}
SURVIVOR_WORDS = {"MANTENER", "survives", "worth_it", "predicts", "PASS"}
NEAR_WORDS = {"DUDOSA", "INCONCLUSIVE"}
# (study, word) pairs that inform without filtering: the workflow carries the strategy on and the
# next step's word rules (owner, 2026-09-30: every H1 mother read FAIL at 14 and reached 16.5).
NOT_A_FILTER = {("mcRetest", "FAIL")}


def _classify(word: str) -> str:
    """`survivor`, `near` or `other`, per the owner's settled word lists (root CLAUDE.md #14)."""
    if word in SURVIVOR_WORDS:
        return "survivor"
    if word in NEAR_WORDS:
        return "near"
    return "other"


def _latest_days(project_dir: Path) -> dict[tuple[str, str], str]:
    """The newest report day for each (databank, study) under one project."""
    latest: dict[tuple[str, str], str] = {}
    for verdict in project_dir.glob("*/*/*/verdict.csv"):
        databank, day, study = verdict.parts[-4], verdict.parts[-3], verdict.parts[-2]
        key = (databank, study)
        if day > latest.get(key, ""):
            latest[key] = day
    return latest


def _judgments(project_dir: Path) -> dict[str, list[dict]]:
    """Every step judgment of every identity, from the latest day of each (databank, study)."""
    latest = _latest_days(project_dir)
    by_identity: dict[str, list[dict]] = defaultdict(list)
    for (databank, study), day in latest.items():
        step = STUDY_STEP.get(study)
        if step is None:
            continue
        frame = pd.read_csv(project_dir / databank / day / study / "verdict.csv",
                            dtype=str, keep_default_na=False)
        if "identity" not in frame.columns:
            continue
        for identity, word, name in zip(frame["identity"], frame["verdict"], frame["strategy"]):
            if identity and (study, word) not in NOT_A_FILTER:  # crossmarket ships it empty
                by_identity[identity].append({"step": step, "word": word, "study": study,
                                              "databank": databank, "strategy": name})
    return by_identity


def _furthest(entries: list[dict]) -> dict:
    """The furthest step among a strategy's judgments; ties keep the most conservative word."""
    order = ("other", "near", "survivor")
    top = max(float(e["step"]) for e in entries)
    at_top = [e for e in entries if float(e["step"]) == top]
    worst = min(at_top, key=lambda e: order.index(_classify(e["word"])))
    return {**worst, "class": _classify(worst["word"])}


def _carried(project: str) -> set[str]:
    """Names of the mothers the workflow carried to a 16.5 variant batch (its folder names).

    Paired by name: the batch's `P00000.sqx` is renamed by the variant writer, so its identity is
    not the mother's. The owner's rule (2026-09-30): what the workflow carried forward is a
    candidate whatever the words of the steps before it said; the line shows those words.
    """
    root = variants_dir(project, "_").parent
    return {d.parent.name.replace("_", " ") for d in root.glob("*/sqx")} if root.is_dir() else set()


def _family(project: str) -> str:
    """The template folder name a project builds, from the last matching row of the registry."""
    row = None
    with project_registry().open(newline="", encoding="utf-8") as fh:
        for candidate in csv.DictReader(fh):
            if candidate["name"] == project:
                row = candidate
    return Path(row["template"]).parent.name if row else ""


def _report(project: str, project_dir: Path) -> None:
    """Print one project's header, its candidates' archive commands, and what was left out."""
    by_identity = _judgments(project_dir)
    if not by_identity:
        return
    print(f"\n=== {project} ===")
    family = _family(project)
    survivors = near = skipped_archived = 0
    left_out: Counter = Counter()
    carried = _carried(project)
    for identity, entries in by_identity.items():
        best = _furthest(entries)
        if any(e["strategy"] in carried for e in entries):
            words = ", ".join(sorted({f"{e['study']} {e['word']}" for e in entries}))
            best = {"class": "survivor", "step": "16.5", "study": "llevada al 16.5",
                    "word": f"[{words}]", "databank": "Results"}
        if best["class"] == "other":
            left_out[best["word"]] += 1
            continue
        if versions(identity):
            skipped_archived += 1
            continue
        if best["class"] == "survivor":
            survivors += 1
            label = "SUPERVIVIENTE"
        else:
            near += 1
            label = "DUDOSA"
        print(f"  [{label}] paso {best['step']} · {best['study']} · {best['word']} · {identity[:12]}…")
        print(f"    python3 -m core.archive archive --project {project} --databank "
              f"{best['databank']} --identity {identity} --step {best['step']} --family {family}")
    print(f"  {survivors} supervivientes, {near} dudosas, {skipped_archived} ya archivadas")
    for word, n in sorted(left_out.items()):
        print(f"  descartadas por «{word}»: {n}")


def main() -> None:
    """`python3 -m portfolio.common.construct.candidates [--project P]` — prints, runs nothing."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--project")
    args = parser.parse_args()
    reports_root = DATA / "reports"
    projects = [args.project] if args.project else sorted(p.name for p in reports_root.iterdir())
    for project in projects:
        project_dir = reports_root / project
        if project_dir.is_dir():
            _report(project, project_dir)


if __name__ == "__main__":
    main()
