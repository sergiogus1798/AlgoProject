"""What the data root holds per databank, and what every module already said about one strategy."""

import csv
import json
from pathlib import Path

import pandas as pd

from core.datapaths import pipeline_dir
from core.paths import DATA
from ui.daemon import runs

# The column that names the strategy, in the order the exports and the reports spell it.
NAME_COLUMNS = ("strategy", "Strategy Name", "strategy_build", "name")

# The metrics the table shows, by the label SQX gives them; `(IS)` and `[IS]` are both found.
KEY = ("Net profit", "# of trades", "Profit factor", "Sharpe Ratio", "Ret/DD Ratio", "Max DD %")

# A report file lying loose in the date folder belongs to the module its stem names.
LOOSE = {"exposure": "exposure", "decay": "decay", "cell": "wfm"}

# Every module that speaks per strategy: what it is called on screen and the step of
# WORKFLOW.md it serves. How each one is started lives in `runs.py`.
MODULES = {
    "gate": ("Puerta IS/OOS", "8"),
    "curate": ("Curado del databank", "8 → 9"),
    "crossmarket": ("Cross-market", "10"),
    "retest": ("MC Retest", "14"),
    "montecarlo": ("Monte Carlo de operaciones", "lectura extra"),
    "nulls": ("Nulo de entrada", "lectura extra"),
    "profitshape": ("Forma del beneficio", "lectura extra"),
    "entryquality": ("Calidad de la entrada", "lectura extra"),
    "exposure": ("Exposición", "21"),
    "wfc": ("Walk Forward Correlation", "17"),
    "wfm": ("Walk Forward Matrix", "19"),
    "decay": ("Decaimiento IS→OOS", "8"),
}


def name_column(columns: list[str]) -> str | None:
    """Which column names the strategy, if any.

    Args:
        columns: A table's header.

    Returns:
        The first of `NAME_COLUMNS` present, or None for a table that is not per strategy.
    """
    return next((c for c in NAME_COLUMNS if c in columns), None)


def manifest(folder: Path) -> dict:
    """The manifest of one export folder, or an empty dict when the auditor would flag it.

    Args:
        folder: A `metrics/` or `harvest/` leaf.

    Returns:
        The decoded JSON, or `{}` for a folder nobody signed.
    """
    f = folder / "manifest.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}


def databanks() -> list[dict]:
    """Every databank with a strategy table in the data root, grouped the way SQX groups them.

    Returns:
        One dict per export: `project`, `databank`, `source` (`metrics`, the one current
        CSV, or `harvest`, the newest cosecha joining build and retest), `date`, `rows` and
        `signed` — whether a manifest exists, and `asset`, the project's asset as its name
        says it, or None. Sorted by project, then databank.
    """
    out = []
    for f in sorted((DATA / "metrics").glob("*/*/metrics.csv")):
        m = manifest(f.parent)
        with f.open(encoding="utf-8") as fh:
            rows = sum(1 for _ in fh) - 1
        out.append({"project": f.parts[-3], "databank": f.parts[-2], "source": "metrics",
                    "date": m.get("date", ""), "rows": rows, "signed": bool(m)})
    # Newest day per cosecha; a bank folder another session is still filling has no table
    # yet and is simply not listed.
    latest = {f.parts[-4:-2]: f for f in sorted((DATA / "harvest").glob("*/*/*/metrics.parquet"))}
    for (project, bank), day in latest.items():
        m = manifest(day.parent)
        rows = pd.read_parquet(day, columns=["strategy_build"]).shape[0]
        out.append({"project": project, "databank": bank, "source": "harvest",
                    "date": day.parts[-2], "rows": rows, "signed": bool(m)})
    for d in out:
        d["asset"] = runs.guess_asset(d["project"])
    return sorted(out, key=lambda d: (d["project"], d["databank"], d["source"]))


def table(project: str, databank: str, source: str) -> pd.DataFrame:
    """The strategy table of one databank.

    Args:
        project: SQX project name.
        databank: Databank name.
        source: `metrics` or `harvest`, as `databanks()` reported it.

    Returns:
        One row per strategy, columns as the export wrote them.
    """
    if source == "metrics":
        return pd.read_csv(DATA / "metrics" / project / databank / "metrics.csv", sep=";")
    day = sorted((DATA / "harvest" / project / databank).glob("*/metrics.parquet"))[-1]
    return pd.read_parquet(day)


def strategies(project: str, databank: str, source: str) -> dict:
    """The strategies of one databank with the handful of metrics the list shows.

    Args:
        project: SQX project name.
        databank: Databank name.
        source: `metrics` or `harvest`.

    Returns:
        `columns` — the name, then each of `KEY` for IS and OOS where the export carries it,
        spelled `label · IS` — and `rows`, one list per strategy in the export's order.
    """
    d = table(project, databank, source)
    name = name_column(list(d.columns))
    picked = [(c, f"{k} · {tag}") for k in KEY for tag in ("IS", "OOS")
              for c in d.columns if c.startswith(k) and tag in c[len(k):]]
    cols = [name] + [c for c, _ in picked]
    rows = d[cols].astype(object).where(d[cols].notna(), None).values.tolist()
    return {"columns": ["estrategia"] + [label for _, label in picked], "rows": rows}


def hits(project: str, strategy: str) -> dict[str, list[dict]]:
    """Every row any report of the project wrote about one strategy, by module.

    Args:
        project: SQX project name; every databank of it is searched, because a verdict on
            a strategy built in `Results` may sit under `OOS` or `SPP_IS`.
        strategy: The strategy's name as SQX spells it.

    Returns:
        Module → list of `{databank, date, file, n, row}`, newest date first. `row` is the
        first matching line and `n` how many there were: a parameter grid has hundreds.
    """
    found: dict[str, list[dict]] = {}
    for f in sorted((DATA / "reports" / project).glob("*/*/**/*.csv"), reverse=True):
        with f.open(encoding="utf-8") as fh:
            header = next(csv.reader(fh))
        col = name_column(header)
        if not col:
            continue
        rows = pd.read_csv(f, dtype=str, keep_default_na=False)
        match = rows[rows[col] == strategy]
        if match.empty:
            continue
        rel = f.relative_to(DATA / "reports" / project)
        module = rel.parts[2] if len(rel.parts) > 3 else LOOSE.get(rel.stem.split("_")[0], rel.stem)
        found.setdefault(module, []).append({
            "databank": rel.parts[0], "date": rel.parts[1],
            "file": str(Path(*rel.parts[2:])), "n": len(match),
            "row": {k: v for k, v in match.iloc[0].items() if k != col and v != ""}})
    return found


def pages(project: str, strategy: str) -> list[str]:
    """The per-strategy HTML pages a module wrote, newest first.

    Args:
        project: SQX project name.
        strategy: The strategy's name.

    Returns:
        Absolute paths as strings, for the window to open in the browser.
    """
    return [str(p) for p in sorted((DATA / "reports" / project)
                                   .glob(f"*/*/*/estrategias/{strategy}.html"), reverse=True)]


def stages(project: str, strategy: str) -> dict:
    """What the pipeline ledger says about one mother, if it ever entered it.

    Args:
        project: SQX project name.
        strategy: The strategy's name; the ledger folder is its slug.

    Returns:
        `state.json` decoded, or `{}`.
    """
    f = pipeline_dir(project, strategy.replace(" ", "_").replace(".", "-")) / "state.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}


def results(project: str, databank: str, strategy: str, asset: str) -> dict:
    """Everything the data root knows about one strategy, module by module.

    Args:
        project: SQX project name.
        databank: The databank the window is showing, which a run reads its inputs from.
        strategy: The strategy's name.
        asset: The asset the project trades, which a run needs for its feed and its costs.

    Returns:
        `modules` — one entry per module of `MODULES`, in its order, each with its label,
        step, `hits` (possibly empty) and either `argv`, what the run button starts, or
        `reason`, why there is no button — then `others` for report folders no entry
        names, `pages` and `stages`.
    """
    found = hits(project, strategy)
    ctx = runs.context(project, databank, strategy, asset)
    modules = [{"module": m, "label": label, "step": step, "hits": found.pop(m, []),
                **runs.plan(m, ctx)} for m, (label, step) in MODULES.items()]
    return {"modules": modules, "others": found, "pages": pages(project, strategy),
            "stages": stages(project, strategy)}
