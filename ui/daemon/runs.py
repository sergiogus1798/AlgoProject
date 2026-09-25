"""What running one analysis module on one strategy means: the command, given what exists on disk."""

import pyarrow.parquet as pq

from core import assetdata
from core.paths import DATA

# Module -> the argv after `python3`, or a sentence saying why the window cannot start it.
# Every entry reads only `ctx`, which `context()` fills from the data root and the asset file;
# a module whose inputs are not there answers with the reason instead of failing later.


def context(project: str, databank: str, strategy: str, asset: str) -> dict:
    """Everything a run may need, found once.

    Args:
        project: SQX project name.
        databank: The databank on screen.
        strategy: The strategy's name.
        asset: The asset the project trades, as `assets/symbols/` spells it.

    Returns:
        `feed`, the asset's SQX symbol; `export`, the newest `raw/` day of this databank
        holding trades, or None; `trades`, that parquet; `multimarket`, whether it is a
        cross-market retest (a `Symbol` column) rather than the strategy on its own market;
        `harvest`, whether a cosecha exists; `split` and `end`, the first out-of-sample day
        and the last day of `oos1`.
    """
    a = assetdata.load(asset)
    days = sorted((DATA / "raw" / project / databank).glob("*/trades.parquet"))
    oos = a["segments"]["oos1"]
    return {"project": project, "databank": databank, "strategy": strategy, "asset": asset,
            "feed": a["sqx_symbol"], "export": days[-1].parts[-2] if days else None,
            "trades": str(days[-1]) if days else None,
            "multimarket": bool(days) and "Symbol" in pq.read_schema(days[-1]).names,
            "harvest": any((DATA / "harvest" / project / databank).glob("*/metrics.parquet")),
            "split": f"{oos['from']}-01-01", "end": f"{oos['to']}-12-31"}


NO_TRADES = "necesita un export raw de operaciones de este databank (skill /export)"
MIXED = ("el export de este databank es cross-market, mezcla mercados: este módulo lee la "
         "estrategia en su propio mercado")


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
        return "necesita la cosecha de este databank (gate.harvest, skill /oos-gate)"
    return ["-m", "gate.report", "--project", c["project"], "--databank", c["databank"],
            "--feed", c["feed"]]


def monte_carlo(c: dict) -> list[str] | str:
    """Trade-level Monte Carlo over the databank's newest trades export."""
    if own_trades(c):
        return own_trades(c)
    return ["-m", "strategies.monteCarlo.report", "--project", c["project"], "--databank",
            c["databank"], "--asset", c["asset"], "--export", c["export"]]


def nulls(c: dict) -> list[str] | str:
    """The entry-timing null of this one strategy."""
    if own_trades(c):
        return own_trades(c)
    return ["-m", "nulls.one", "--project", c["project"], "--databank", c["databank"],
            "--feed", c["feed"], "--strategy", c["strategy"]]


def exposure(c: dict) -> list[str] | str:
    """Step 21: market time against buy and hold, this strategy only."""
    if own_trades(c):
        return own_trades(c)
    return ["-m", "strategies.exposure.report", "--project", c["project"], "--databank",
            c["databank"], "--feed", c["feed"], "--symbol", c["asset"], "--strategy",
            c["strategy"]]


def profitshape(c: dict) -> list[str] | str:
    """Which few trades and months the result depends on; prints, writes nothing."""
    if own_trades(c):
        return own_trades(c)
    return ["-m", "strategies.profitShape.report", "--export", c["trades"], "--strategy",
            c["strategy"]]


def entryquality(c: dict) -> list[str] | str:
    """The entry alone, against random entries at the same hours; prints, writes nothing."""
    if own_trades(c):
        return own_trades(c)
    return ["-m", "strategies.entryQuality.report", "--export", c["trades"], "--strategy",
            c["strategy"]]


def decay(c: dict) -> list[str] | str:
    """IS to OOS decay of the whole databank, split at the asset's first oos1 day."""
    return ["-m", "tasks.reports.decay", "--project", c["project"], "--databank",
            c["databank"], "--split", c["split"], "--end", c["end"]]


def mc_retest(c: dict) -> list[str] | str:
    """Step 14 over the MC Retest export of this project."""
    return ["-m", "strategies.retest.report", "--project", c["project"]]


def wfm(c: dict) -> list[str] | str:
    """Step 19 over the project's newest WFM export."""
    return ["-m", "strategies.walkForwardMatrix.report", "--project", c["project"]]


def crossmarket(c: dict) -> list[str] | str:
    """Step 10; needs the cross-market retest export of this databank."""
    if not c["multimarket"]:
        return "necesita el export del retest cross-market (skill /crossmarket)"
    return ["-m", "strategies.crossmarket.report", "--project", c["project"], "--databank",
            c["databank"], "--asset", c["asset"], "--export", c["export"]]


RUNS = {"gate": gate, "monteCarlo": monte_carlo, "nulls": nulls, "exposure": exposure,
        "profitshape": profitshape, "entryquality": entryquality, "decay": decay,
        "mcRetest": mc_retest, "wfm": wfm, "crossmarket": crossmarket,
        "curate": lambda c: "es una skill: /curate, desde Claude Code",
        "wfc": lambda c: "se corre desde el pipeline, sobre el lote de variantes"}


def plan(module: str, c: dict) -> dict:
    """Whether the window may start this module here, and with what.

    Args:
        module: A key of `RUNS`.
        c: What `context()` built.

    Returns:
        `{argv: [...]}` when it can run, `{reason: "..."}` when it cannot.
    """
    got = RUNS[module](c)
    return {"argv": got} if isinstance(got, list) else {"reason": got}


def guess_asset(project: str) -> str | None:
    """Which asset a project trades, read off its name.

    Args:
        project: SQX project name, e.g. "TestUSDJPY_Workflow_v1".

    Returns:
        The longest asset symbol the name contains, or None — the window then asks. Exports
        do not record the feed, so the name is the only free evidence.
    """
    found = [s for s in assetdata.symbols() if s.lower() in project.lower()]
    return max(found, key=len) if found else None
