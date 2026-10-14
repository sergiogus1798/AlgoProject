"""The command lines of the readings and closing families and the trade Monte Carlo, or why not."""

from pathlib import Path

from ui.daemon import runs
from ui.daemon.runner import rootseed, where

NO_TF = runs.NO_TF


def exported(c: dict) -> list[str] | str:
    """Every strategy of the databank's trade export: what «Run todo el databank» means for a
    study whose command reads one strategy (owner, 2026-10-01) — one job each, folded by
    `runner.batch.fold` into one forked batchrun."""
    if not c["export"]:
        return runs.NO_TRADES
    return (
        where.distinct(Path(c["trades"]), "strategy")
        or "el export no nombra estrategias"
    )


def monkey(c: dict, strategy: str) -> list[str] | str:
    """The entry-timing null: one strategy on its own market, or every strategy of the export."""
    if not c["export"]:
        return runs.NO_TRADES
    frame = where.export_timeframe(Path(c["trades"]).parent)
    if not frame:
        return NO_TF
    # A cross-market export runs every market without --feed; one strategy reads the base one.
    feed = ["--feed", c["feed"]] if strategy or not c["multimarket"] else []
    return [
        "-m",
        "studies.readings.monkey.report",
        "--project",
        c["project"],
        "--databank",
        c["databank"],
        *feed,
        "--timeframe",
        frame,
        "--seed",
        str(rootseed.root(c["project"], c["databank"])),
    ] + (["--strategy", strategy] if strategy else [])


def entry_quality(c: dict, strategy: str) -> list[str] | str:
    """One strategy's entries against random ones at the same hours, on its own feed and grid."""
    if bad := runs.own_trades(c):
        return bad
    frame = where.export_timeframe(Path(c["trades"]).parent)
    if not frame:
        return NO_TF
    return [
        "-m",
        "studies.readings.entryQuality.report",
        "--export",
        c["trades"],
        "--strategy",
        strategy,
        "--set",
        f"run.feed={c['feed']}",
        f"run.timeframe={frame}",
    ]


def edge_cost(c: dict, strategy: str) -> list[str] | str:
    """Edge per unit of cost, over the newest cosecha."""
    if not c["harvest"]:
        return "necesita la cosecha de este databank (studies.screening.gate.harvest, skill /oos-gate)"
    return [
        "-m",
        "studies.readings.edgeCost.report",
        "--project",
        c["project"],
        "--databank",
        c["databank"],
        "--feed",
        c["feed"],
    ] + (["--strategy", strategy] if strategy else [])


def exposure(c: dict, strategy: str) -> list[str] | str:
    """Step 21: market time against buy and hold."""
    if bad := runs.own_trades(c):
        return bad
    frame = where.export_timeframe(Path(c["trades"]).parent)
    # The occupancy grid is the export's own timeframe, not config.yaml's M30.
    return (
        [
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
        ]
        + (["--strategy", strategy] if strategy else [])
        + (["--set", f"study.timeframe={frame}"] if frame else [])
    )


def monte_carlo(c: dict, strategy: str) -> list[str] | str:
    """The trade-level Monte Carlo over every strategy of the newest single-market export, or
    one strategy of it alone."""
    return runs.own_trades(c) or (
        [
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
        + (["--strategy", strategy] if strategy else [])
    )


def blind_joint(c: dict, strategy: str) -> list[str] | str:
    """Step 20 over the WFM databank, signed under the family; its report asks the ledger's
    door itself and refuses while 17, 18 and 19 are not all recorded."""
    row, family = where.enrolled(c["project"]), where.family(c["project"])
    if family is None or row is None:
        return where.no_family(c["project"])
    # Always the project's own WFM databank, whichever tab the button was pressed from
    # (T2, 2026-09-30: the open databank was passed blindly, e.g. a Cross Market one).
    # Imported here: databank.cells → results.catalogue → runner → this module → layout → cells.
    from ui.daemon.databank import layout

    wfm = layout.databank(c["project"], layout.outputs(c["project"]), "wfm", ["wfm"])
    return [
        "-m",
        "studies.closing.blindJoint.report",
        "--project",
        c["project"],
        "--wfm-databank",
        wfm,
        "--feed",
        c["feed"],
        "--symbol",
        c["asset"],
        "--timeframe",
        row["timeframe"],
        "--family",
        family,
    ]


STUDIES = {
    "monkey": {"plan": monkey, "one": True, "many": True, "sets": True},
    "entryQuality": {
        "plan": entry_quality,
        "one": True,
        "many": True,
        "sets": True,
        "population": exported,
    },
    "edgeCost": {"plan": edge_cost, "one": True, "many": True, "sets": True},
    "exposure": {"plan": exposure, "one": True, "many": True, "sets": True},
    "monteCarlo": {"plan": monte_carlo, "one": True, "many": True, "sets": True},
    "blindJoint": {"plan": blind_joint, "one": False, "many": True, "sets": True},
}
