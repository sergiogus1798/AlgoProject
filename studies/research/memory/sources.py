"""Readers of the memory's sources: the two registries, runs.csv and the autopilot's resumen.md."""

import csv
import re
from pathlib import Path

import yaml

from core.datapaths import project_registry, template_registry, template_runs
from core.researchpaths import autopilot_runs

CONFIG = yaml.safe_load((Path(__file__).parent / "config.yaml").read_text(encoding="utf-8"))
ROW = re.compile(r"^\| (\S+) \| (\w+) \| (\d+) \| (.*) \|$")
PAIR = re.compile(r"([^:·|;]+?): (\d+) → (\d+)")
TOTAL = re.compile(r"Total ([\d.]+) min\.")
FAILED = re.compile(r"\*\*Falló\*\* en el paso (\S+?)\.")
FALLO = re.compile(r"# Fallo en el paso (\S+)")
TEMPLATE_IN_PATH = re.compile(r"templates/library/([^/]+)/")
TITLE_STAGE = {"CONSTRUCCION": "built", "Retest Markets - Family": "markets",
               "MCR 8": "mcr", "SPP OOS": "spp"}


def read_csv(path: Path) -> list[dict]:
    """A CSV as dicts; an absent file is an empty table."""
    if not path.exists():
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def registry_projects() -> dict[str, dict]:
    """projects/registry.csv by project name, the latest row when a name repeats."""
    return {r["name"]: r for r in read_csv(project_registry())}


def runs_by_project() -> dict[str, dict]:
    """templates/runs.csv by project name."""
    return {r["project"]: r for r in read_csv(template_runs())}


def templates() -> dict[str, dict]:
    """templates/registry.csv by template name."""
    return {r["name"]: r for r in read_csv(template_registry())}


def template_of(registry_row: dict) -> str:
    """The library template a project was cloned from, '' when its path is not in the library."""
    found = TEMPLATE_IN_PATH.search(registry_row.get("template", ""))
    return found.group(1) if found else ""


def stage_of(step: str, title: str) -> str:
    """The stage a `title: A → B` pair of a resumen row counts, '' when it is not one."""
    if step == "8":
        return "gate" if title == "OOS" else ""
    if title == "OOS" and step in ("6+7", "7"):
        return "oos"
    return next((s for t, s in TITLE_STAGE.items() if title.startswith(t)), "")


def parse_resumen(text: str) -> dict:
    """What one run's resumen.md says.

    Returns:
        `stages` {stage: strategies left}, `crosstf` the CrossTF cell count or None, `minutes`
        (Total), `failed` the step it failed at or '', `dev_cut` True when step 8 kept a random
        draw instead of judging.
    """
    out = {"stages": {}, "crosstf": None, "minutes": 0.0, "failed": "", "dev_cut": False}
    for line in text.splitlines():
        row = ROW.match(line)
        if row:
            step, _, _, what = row.groups()
            out["dev_cut"] |= step == "8" and "por sorteo" in what
            for title, _, after in PAIR.findall(what):
                if title.strip() == "CrossTF":
                    out["crosstf"] = int(after)
                elif stage_of(step, title.strip()):
                    out["stages"][stage_of(step, title.strip())] = int(after)
        total = TOTAL.search(line)
        if total:
            out["minutes"] = float(total.group(1))
            out["failed"] = (FAILED.search(line) or [None, ""])[1]
    return out


def autopilot_project(project: str, root: Path | None = None) -> dict:
    """Every autopilot run of a project folded into one record, the newest run winning per stage.

    Args:
        project: Project name.
        root: Folder holding `<project>/<stamp>/`; the autopilot's own by default.

    Returns:
        `parse_resumen`'s keys with `runs` (how many), `first`/`last` stamps, `minutes` summed;
        `failed` is the newest run's (read from fallo.md, which the final summary cannot erase).
        `runs` is 0 when the project never ran.
    """
    folder = (root or autopilot_runs()) / project
    stamps = sorted(p for p in folder.glob("*/resumen.md")) if folder.exists() else []
    merged = {"stages": {}, "crosstf": None, "minutes": 0.0, "failed": "", "dev_cut": False,
              "runs": len(stamps), "first": "", "last": ""}
    for path in stamps:
        one = parse_resumen(path.read_text(encoding="utf-8"))
        merged["stages"].update(one["stages"])
        merged["crosstf"] = one["crosstf"] if one["crosstf"] is not None else merged["crosstf"]
        merged["minutes"] += one["minutes"]
        merged["dev_cut"] |= one["dev_cut"]
        fallo = path.parent / "fallo.md"   # the more reliable sign: a final summary can drop the error
        found = FALLO.match(fallo.read_text(encoding="utf-8")) if fallo.exists() else None
        merged["failed"] = found.group(1) if found else one["failed"]
    if stamps:
        merged["first"], merged["last"] = stamps[0].parent.name, stamps[-1].parent.name
    return merged
