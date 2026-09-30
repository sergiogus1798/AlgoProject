"""The command lines of the readings and closing families and the trade Monte Carlo, or why not."""

from pathlib import Path

from ui.daemon import runs
from ui.daemon.runner import where

NO_TF = ("el export no dice en qué timeframe corre la estrategia (manifest sin un único "
         "timeframe): córrelo desde la terminal")


def monkey(c: dict, strategy: str) -> list[str] | str:
    """The entry-timing null: one strategy on its own market, or every strategy of the export."""
    if not c["export"]:
        return runs.NO_TRADES
    frame = where.export_timeframe(Path(c["trades"]).parent)
    if not frame:
        return NO_TF
    # A cross-market export runs every market without --feed; one strategy reads the base one.
    feed = ["--feed", c["feed"]] if strategy or not c["multimarket"] else []
    return (["-m", "studies.readings.monkey.report", "--project", c["project"], "--databank",
             c["databank"], *feed, "--timeframe", frame]
            + (["--strategy", strategy] if strategy else []))


def profit_shape(c: dict, strategy: str) -> list[str] | str:
    """Which few trades and months one strategy's result rests on."""
    return runs.own_trades(c) or ["-m", "studies.readings.profitShape.report", "--export",
                                  c["trades"], "--strategy", strategy]


def entry_quality(c: dict, strategy: str) -> list[str] | str:
    """One strategy's entries against random ones at the same hours, on its own feed and grid."""
    if runs.own_trades(c):
        return runs.own_trades(c)
    frame = where.export_timeframe(Path(c["trades"]).parent)
    if not frame:
        return NO_TF
    return ["-m", "studies.readings.entryQuality.report", "--export", c["trades"], "--strategy",
            strategy, "--set", f"run.feed={c['feed']}", f"run.timeframe={frame}"]


def edge_cost(c: dict, strategy: str) -> list[str] | str:
    """Edge per unit of cost, over the newest cosecha."""
    if not c["harvest"]:
        return "necesita la cosecha de este databank (studies.screening.gate.harvest, skill /oos-gate)"
    return (["-m", "studies.readings.edgeCost.report", "--project", c["project"], "--databank",
             c["databank"], "--feed", c["feed"]] + (["--strategy", strategy] if strategy else []))


def conditional_map(c: dict, strategy: str) -> list[str] | str:
    """Step 22: one strategy's entries against the regime they were taken in."""
    if not c["harvest"]:
        return "necesita la cosecha de este databank (studies.screening.gate.harvest, skill /oos-gate)"
    frame = where.harvest_timeframe(c["harvest_dir"])
    if not frame:
        return "la cosecha mezcla varios timeframes: córrelo desde la terminal con run.timeframe"
    return ["-m", "studies.readings.conditionalMap.report", "--harvest", str(c["harvest_dir"]),
            "--strategy", strategy, "--set", f"run.symbol={c['asset']}", f"run.feed={c['feed']}",
            f"run.timeframe={frame}"]


def exposure(c: dict, strategy: str) -> list[str] | str:
    """Step 21: market time against buy and hold."""
    if runs.own_trades(c):
        return runs.own_trades(c)
    frame = where.export_timeframe(Path(c["trades"]).parent)
    # The occupancy grid is the export's own timeframe, not config.yaml's M30.
    return (["-m", "studies.closing.exposure.report", "--project", c["project"], "--databank",
             c["databank"], "--feed", c["feed"], "--symbol", c["asset"]]
            + (["--strategy", strategy] if strategy else [])
            + (["--set", f"study.timeframe={frame}"] if frame else []))


def atr_calculator(c: dict, strategy: str) -> list[str] | str:
    """Step 24: the stop's X from the MAE of the IS winners; spends its look in the ledger."""
    got = runs.atr_calculator(c | {"strategy": strategy})
    return got if isinstance(got, str) or strategy else got[:-2]


def monte_carlo(c: dict, strategy: str) -> list[str] | str:
    """The trade-level Monte Carlo over every strategy of the newest single-market export."""
    return runs.own_trades(c) or [
        "-m", "portfolio.common.monteCarlo.report", "--project", c["project"], "--databank",
        c["databank"], "--asset", c["asset"], "--day", c["export"]]


def blind_joint(c: dict, strategy: str) -> list[str] | str:
    """Step 20 over the WFM databank, signed under the family; its report asks the ledger's
    door itself and refuses while 17, 18 and 19 are not all recorded."""
    row, family = where.enrolled(c["project"]), where.family(c["project"])
    if family is None:
        return where.no_family(c["project"])
    return ["-m", "studies.closing.blindJoint.report", "--project", c["project"],
            "--wfm-databank", c["databank"], "--feed", c["feed"], "--symbol", c["asset"],
            "--timeframe", row["timeframe"], "--family", family]


STUDIES = {
    "monkey": {"plan": monkey, "one": True, "many": True, "sets": True},
    "profitShape": {"plan": profit_shape, "one": True, "many": False, "sets": True},
    "entryQuality": {"plan": entry_quality, "one": True, "many": False, "sets": True},
    "edgeCost": {"plan": edge_cost, "one": True, "many": True, "sets": True},
    "conditionalMap": {"plan": conditional_map, "one": True, "many": False, "sets": True},
    "exposure": {"plan": exposure, "one": True, "many": True, "sets": True},
    "atrCalculator": {"plan": atr_calculator, "one": True, "many": True, "sets": True},
    "monteCarlo": {"plan": monte_carlo, "one": False, "many": True, "sets": True},
    "structure": {"why": "lee un lote estructural ya retesteado y elige sus piernas (--work, "
                         "--databank): desde la terminal, tras sqx.structural"},
    "blindJoint": {"plan": blind_joint, "one": False, "many": True, "sets": True},
}
