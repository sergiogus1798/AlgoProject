"""The command lines of the transfer and breakage families (steps 9-16), or why the window cannot start one."""

from pathlib import Path

from core.paths import DATA
from ui.daemon.runner import where

NO_CROSS = ("necesita el export del retest cross-market de este databank (skill /crossmarket); si "
            "ya corrió, abre la estrategia desde la pestaña Cross Market de Databanks")


def crossmarket(c: dict, strategy: str) -> list[str] | str:
    """Step 10: breadth over every market of the cross-market export, or one strategy in full."""
    if not c["multimarket"]:
        return NO_CROSS
    return (["-m", "studies.transfer.crossmarket.report", "--project", c["project"],
             "--databank", c["databank"], "--asset", c["asset"], "--day", c["export"]]
            + (["--strategy", strategy] if strategy else []))


def cross_tf(c: dict, strategy: str) -> list[str] | str:
    """Step 11: every cell of the cross-timeframe matrix, against the fabrication it came from,
    or one mother alone (feedback 2026-09-30 §1/§5: the owner saw "Run" silently process the
    whole population; `studies.transfer.crossTF.report --strategy` now reads that one mother's
    row of `scaling.parquet` and nothing else, so "esta estrategia" is a real, cheaper run and
    not just a hidden button)."""
    if not c["export"]:
        return "necesita el export del retest cross-timeframe de este databank (skill /crosstf)"
    made = where.scaling_day(c["project"], Path(c["trades"]))
    if not made:
        return (f"ningún crosstf/{c['project']}/*/scaling.parquet de ese día o anterior nombra "
                "las estrategias de este export: no es un retest cross-timeframe (skill /crosstf)")
    return (["-m", "studies.transfer.crossTF.report", "--project", c["project"], "--databank",
             c["databank"], "--asset", c["asset"], "--day", c["export"], "--fabricated", made]
            + (["--strategy", strategy] if strategy else []))


MCR_ALL = "MCR_All"      # `ui.daemon.loader.afterrun`'s MC ingest target


def mc_retest(c: dict, strategy: str) -> list[str] | str:
    """Step 14 over the newest ingest of the eight MC Retest tasks — one ingest, `MCR_All`,
    whichever of the eight databanks the step or the panel names (📓 2026-09-30: the chain
    passed «MCR 1 Bar» and step 14 was refused beside a fresh ingest). Any other databank's
    page is refused, so it offers the jump to the MC Retest tab instead."""
    if not c["databank"].replace(" ", "_").startswith("MCR"):
        return "el MC Retest lee los databanks MCR, no este"
    found = where.newest(DATA / "raw" / c["project"] / MCR_ALL, "*/sims")
    if not found:
        return "necesita la ingesta del MC Retest (MCR_All; se hace sola al parar el worker)"
    # The ingest names «1.26.46», the databank «Strategy 1.26.46»: the report takes either.
    return (["-m", "studies.breakage.mcRetest.report", "--project", c["project"], "--databank",
             MCR_ALL, "--day", found.parent.name]
            + (["--strategy", strategy] if strategy else []))


def spp(c: dict, strategy: str) -> list[str] | str:
    """Step 15: each strategy's permutation profile over the newest SPP export."""
    found = where.newest(DATA / "raw" / c["project"] / c["databank"].replace(" ", "_"), "*/spp")
    if not found:
        return "necesita el export del SPP de este databank (skill /spp)"
    return (["-m", "studies.breakage.spp.report", "--project", c["project"], "--databank",
             c["databank"].replace(" ", "_"), "--day", found.parent.name]
            + (["--strategy", strategy] if strategy else []))


STUDIES = {
    "crossmarket": {"plan": crossmarket, "one": True, "many": True, "sets": True},
    "crossTF": {"plan": cross_tf, "one": True, "many": True, "sets": True},
    "mcRetest": {"plan": mc_retest, "one": True, "many": True, "sets": True},
    "spp": {"plan": spp, "one": True, "many": True, "sets": True},
}


def only_options(c: dict) -> list[dict]:
    """Crossmarket's sub-tests runnable alone: each market of the export but the base one.

    Args:
        c: What `runs.context` built.

    Returns:
        `[{"key": feed, "label": feed}, ...]`; empty when the export is not cross-market.
    """
    return [{"key": f, "label": f} for f in c["markets"] if c["multimarket"] and f != c["feed"]]
