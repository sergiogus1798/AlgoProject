"""The command lines of the optimisation family (steps 16.5-19), or why the window cannot start one."""

from core.paths import DATA
from ui.daemon.runner import where


def cloud(c: dict, strategy: str) -> list[str] | str:
    """The parameter cloud of one mother's variant batch."""
    work = where.batch(c["project"], strategy, ("metrics.parquet", "equity.parquet"))
    # The project's own asset: config.yaml names the donor (XAUUSD), which the window showed as
    # what ran on a USDJPY project (owner, 2026-09-28, «chau USD»).
    return work if isinstance(work, str) else [
        "-m", "studies.optimisation.cloud.report", "--work", str(work),
        "--set", f"run.symbol={c['asset']}"]


def signed(c: dict, strategy: str, module: str, needs: tuple[str, ...]) -> list[str] | str:
    """A batch study that signs its look in the ledger under the project's template family.

    Args:
        c: What `runs.context` built.
        strategy: The mother.
        module: The study's report module.
        needs: Files the study reads inside the batch.

    Returns:
        The argv with `--work` and `--family`, or why not: no batch, two batches, or no
        template in the registry (owner, Q9 of plan 24: no template, nothing signed).
    """
    family = where.family(c["project"])
    if family is None:
        return where.no_family(c["project"])
    work = where.batch(c["project"], strategy, needs)
    return work if isinstance(work, str) else [
        "-m", module, "--work", str(work), "--family", family]


def wfc(c: dict, strategy: str) -> list[str] | str:
    """Step 17: in against out over one mother's variant batch, the composition config.yaml says."""
    return signed(c, strategy, "studies.optimisation.wfc.report",
                  ("metrics.parquet", "collected.json"))


def cscv(c: dict, strategy: str) -> list[str] | str:
    """Step 18: the probability the selection overfits, over one mother's variant batch."""
    return signed(c, strategy, "studies.optimisation.cscv.report",
                  ("metrics.parquet", "equity.parquet"))


def market_surfaces(c: dict, strategy: str) -> list[str] | str:
    """Step 18.5: the same parameter region on every market, over one mother's batch."""
    return signed(c, strategy, "studies.optimisation.marketSurfaces.report",
                  ("metrics.parquet", "segments.parquet", "equity_markets.parquet"))


def wfm(c: dict, strategy: str) -> list[str] | str:
    """Step 19 over the newest Walk-Forward Matrix export of this databank."""
    found = where.newest(DATA / "raw" / c["project"] / c["databank"], "*/wfm")
    if not found:
        return "necesita el export de la Walk-Forward Matrix de este databank (skill /wfm)"
    return ["-m", "studies.optimisation.wfm.report", "--project", c["project"], "--databank",
            c["databank"], "--day", found.parent.name]


# The batch studies take the mother as their strategy; `many` would be every mother at once,
# which none of their commands does.
STUDIES = {
    "cloud": {"plan": cloud, "one": True, "many": False, "sets": True},
    "wfc": {"plan": wfc, "one": True, "many": False, "sets": True},
    "cscv": {"plan": cscv, "one": True, "many": False, "sets": True},
    "marketSurfaces": {"plan": market_surfaces, "one": True, "many": False, "sets": True},
    "wfm": {"plan": wfm, "one": False, "many": True, "sets": True},
}
