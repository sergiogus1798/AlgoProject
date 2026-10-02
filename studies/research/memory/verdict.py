"""The verdict writer: closes a finished autopilot run's row in templates/runs.csv."""

import csv
import os
from pathlib import Path

from core.datapaths import DATA, template_runs
from studies.research.memory import attempts, sources
from studies.research.memory.sources import CONFIG

COLUMNS = ["template", "symbol", "timeframe", "project", "date", "strategies_built",
           "strategies_kept", "verdict", "report"]
STEP = {"built": "6", "oos": "7", "gate": "8", "markets": "9", "mcr": "13", "spp": "15"}
AUTO = "auto"


def sentence(row: dict) -> str:
    """The verdict in the owner's language: the funnel, then how it ended.

    Args:
        row: One `attempts.table()` row.
    """
    funnel = " -> ".join(f"{s} {row[s]}" for s in CONFIG["stages"] if row[s] != "")
    end = {"survivors": f"llegaron {row['survivors']} al final del paso 15",
           "died": f"murio en el paso {STEP.get(row['died_at'], '?')} ({row['died_at']})",
           "failed": f"inconcluso: fallo en el paso {row['failed_at']}",
           "incomplete": f"incompleto: ultimo tramo {row['last_stage']}",
           "unknown": "sin datos del embudo"}[row["outcome"].split("@")[0]]
    dev = "; corte de desarrollo en el paso 8 (sorteo): no es evidencia" if row["dev_cut"] else ""
    return f"{AUTO}: embudo {funnel or '-'}; {end}{dev}"


def write(path: Path, rows: list[dict], fields: list[str]) -> None:
    """Rewrite a CSV through a temp file, so a crash leaves the old one."""
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    os.replace(tmp, path)


def close_run(run_dir: Path, runs_csv: Path | None = None, registry_row: dict | None = None) -> dict:
    """Close the attempt of a finished autopilot run: counts per stage and the verdict.

    Fills `strategies_built`, `strategies_kept` and `verdict` of the project's row in runs.csv,
    appending the row when the project has none. A `verdict` the owner typed (not starting with
    `auto`) is kept, and then so are the counts; an `auto` one is rewritten on each close, so a
    resumed project ends with its latest funnel. Safe to call after a failed run: it records
    «inconcluso». Reads every run of the project, not only this one.

    Args:
        run_dir: `AlgoData/autopilot/<project>/<stamp>/`.
        runs_csv: The table to update; templates/runs.csv by default.
        registry_row: The project's projects/registry.csv row; looked up by name by default.

    Returns:
        The runs.csv row as written.
    """
    project, path = run_dir.parent.name, runs_csv or template_runs()
    old = sources.read_csv(path)
    mine = next((r for r in reversed(old) if r["project"] == project), None)
    reg = registry_row if registry_row is not None else sources.registry_projects().get(project, {})
    row = attempts.one(project, reg, mine or {}, sources.templates(), set(), run_dir.parent.parent)
    last = row[row["last_stage"]] if row["last_stage"] else ""
    new = {"template": row["template"], "symbol": row["symbol"], "timeframe": row["timeframe"],
           "project": project, "date": row["date"], "strategies_built": str(row["built"]),
           "strategies_kept": str(last), "verdict": sentence(row),
           "report": str((run_dir / "resumen.md").relative_to(DATA)
                         if run_dir.is_relative_to(DATA) else run_dir / "resumen.md")}
    if mine is None:
        old.append(new)
        mine = new
    else:
        owned = not mine["verdict"] or mine["verdict"].startswith(AUTO)
        for k, v in new.items():
            if (owned and k in ("verdict", "strategies_kept") or not mine.get(k)) and v != "":
                mine[k] = v
    write(path, old, list(old[0]) if old and path.exists() else COLUMNS)
    return mine
