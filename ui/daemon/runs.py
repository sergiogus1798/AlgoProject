"""What running one analysis module on one strategy means: the command, given what exists on disk."""

from pathlib import Path
from typing import Any

from core import assetdata
from core.paths import DATA
from studies.run import where
from ui.daemon.runner import rootseed

# Module -> the argv after `python3`, or a sentence saying why the window cannot start it.
# Every entry reads only `ctx`, which `context()` fills from the data root and the asset file;
# a module whose inputs are not there answers with the reason instead of failing later.


def context(project: str, databank: str, strategy: str, asset: str) -> dict[str, Any]:
    """Everything a run may need, found once.

    Args:
        project: SQX project name.
        databank: The databank on screen.
        strategy: The strategy's name.
        asset: The asset the project trades, as `assets/symbols/` spells it.

    Returns:
        `feed`, the asset's SQX symbol; `export`, the newest `raw/` day of this databank
        holding trades, or None; `trades`, that parquet; `multimarket`, whether it is a
        cross-market retest (its `Symbol` column names more than one feed — every export
        carries the column since 2026-09-24) rather than the strategy on its own market, and
        `markets`, those feeds; `harvest`, whether a cosecha exists, and `harvest_dir`, the
        newest one; `split` and `end`, the first out-of-sample day and the last day of `oos1`.
    """
    a = assetdata.load(asset)
    # The window and layout.py hand over the databank exactly as SQX spells it, spaces and
    # all ("Retest Markets - Family"); every export lands on disk with underscores
    # (`core.paths.report_dir` et al.). Without this, a databank whose name is not already
    # underscore-safe found no export and no harvest here, however much either held — the
    # Cross Market tab's own databank read "necesita el export del retest cross-market" about
    # itself (feedback 2026-09-29 §1.4).
    folder = databank.replace(" ", "_")
    days = sorted((DATA / "raw" / project / folder).glob("*/trades.parquet"))
    harvests = sorted((DATA / "harvest" / project / folder).glob("*/metrics.parquet"))
    oos = a["segments"]["oos1"]
    feeds = where.markets(days[-1]) if days else []
    return {
        "project": project,
        "databank": databank,
        "strategy": strategy,
        "asset": asset,
        "feed": a["sqx_symbol"],
        "export": days[-1].parts[-2] if days else None,
        "trades": str(days[-1]) if days else None,
        "markets": feeds,
        "multimarket": len(feeds) > 1,
        "harvest": bool(harvests),
        "harvest_dir": harvests[-1].parent if harvests else None,
        "split": f"{oos['from']}-01-01",
        "end": f"{oos['to']}-12-31",
    }


NO_TF = (
    "el export no dice en qué timeframe corre la estrategia (manifest sin un único "
    "timeframe): córrelo desde la terminal"
)
NO_TRADES = "necesita un export raw de operaciones de este databank (skill /export)"
MIXED = (
    "el export de este databank es cross-market, mezcla mercados: este módulo lee la "
    "estrategia en su propio mercado"
)


def own_trades(c: dict) -> str | None:
    """Why a single-market module cannot read this databank's export, or None when it can.

    Args:
        c: What `context()` built.

    Returns:
        The sentence for the window, or None.
    """
    return NO_TRADES if not c["export"] else (MIXED if c["multimarket"] else None)


def gate(c: dict) -> list[str] | str:
    """Step 8: the whole databank through the gate; needs its cosecha."""
    if not c["harvest"]:
        return "necesita la cosecha de este databank (studies.screening.gate.harvest, skill /oos-gate)"
    return [
        "-m",
        "studies.screening.gate.report",
        "--project",
        c["project"],
        "--databank",
        c["databank"],
        "--feed",
        c["feed"],
    ]


def monte_carlo(c: dict) -> list[str] | str:
    """Trade-level Monte Carlo over the databank's newest trades export."""
    if bad := own_trades(c):
        return bad
    return [
        "-m",
        "portfolio.common.monteCarlo.report",
        "--project",
        c["project"],
        "--databank",
        c["databank"],
        "--asset",
        c["asset"],
        "--day",
        c["export"],
        "--seed",
        str(rootseed.root(c["project"], c["databank"])),
    ]


def nulls(c: dict) -> list[str] | str:
    """The entry-timing null of this one strategy."""
    if bad := own_trades(c):
        return bad
    frame = where.export_timeframe(Path(c["trades"]).parent)
    if (
        not frame
    ):  # never the report's M30 default: a wrong grid prices every monkey wrong
        return NO_TF
    return [
        "-m",
        "studies.readings.monkey.report",
        "--project",
        c["project"],
        "--databank",
        c["databank"],
        "--feed",
        c["feed"],
        "--timeframe",
        frame,
        "--strategy",
        c["strategy"],
        "--seed",
        str(rootseed.root(c["project"], c["databank"])),
    ]


def exposure(c: dict) -> list[str] | str:
    """Step 21: market time against buy and hold, this strategy only."""
    if bad := own_trades(c):
        return bad
    return [
        "-m",
        "studies.closing.exposure.report",
        "--project",
        c["project"],
        "--databank",
        c["databank"],
        "--feed",
        c["feed"],
        "--symbol",
        c["asset"],
        "--strategy",
        c["strategy"],
    ]


def entryquality(c: dict) -> list[str] | str:
    """The entry alone, against random entries at the same hours; prints, writes nothing."""
    if bad := own_trades(c):
        return bad
    return [
        "-m",
        "studies.readings.entryQuality.report",
        "--export",
        c["trades"],
        "--strategy",
        c["strategy"],
    ]


def decay(c: dict) -> list[str] | str:
    """IS to OOS decay of the whole databank, split at the asset's first oos1 day."""
    return [
        "-m",
        "studies.screening.decay.report",
        "--project",
        c["project"],
        "--databank",
        c["databank"],
        "--split",
        c["split"],
        "--end",
        c["end"],
    ]


def mc_retest(c: dict) -> list[str] | str:
    """Step 14 over the MC Retest export of this project."""
    return ["-m", "studies.breakage.mcRetest.report", "--project", c["project"]]


def wfm(c: dict) -> list[str] | str:
    """Step 19 over the project's newest WFM export."""
    return ["-m", "studies.optimisation.wfm.report", "--project", c["project"]]


def crossmarket(c: dict) -> list[str] | str:
    """Step 10; needs the cross-market retest export of this databank."""
    if not c["multimarket"]:
        return "necesita el export del retest cross-market (skill /crossmarket)"
    return [
        "-m",
        "studies.transfer.crossmarket.report",
        "--project",
        c["project"],
        "--databank",
        c["databank"],
        "--asset",
        c["asset"],
        "--day",
        c["export"],
        "--seed",
        str(rootseed.root(c["project"], c["databank"])),
    ]


RUNS = {
    "gate": gate,
    "monteCarlo": monte_carlo,
    "monkey": nulls,
    "exposure": exposure,
    "entryQuality": entryquality,
    "decay": decay,
    "mcRetest": mc_retest,
    "wfm": wfm,
    "crossmarket": crossmarket,
    "curate": lambda c: "es una skill: /curate, desde Claude Code",
    "wfc": lambda c: "se corre desde el pipeline, sobre el lote de variantes",
}


def plan(module: str, c: dict) -> dict[str, Any]:
    """Whether the window may start this module here, and with what.

    Args:
        module: A key of `RUNS`.
        c: What `context()` built.

    Returns:
        `{argv: [...]}` when it can run, `{reason: "..."}` when it cannot.
    """
    got = RUNS[module](c)
    return {"argv": got} if isinstance(got, list) else {"reason": got}
