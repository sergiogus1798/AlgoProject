"""The command lines of the optimisation family (steps 16.5-19), or why the window cannot start one."""

from core.paths import DATA
from ui.daemon.runner import where


def cloud(c: dict, strategy: str) -> list[str] | str:
    """The parameter cloud of one mother's variant batch."""
    work = where.batch(c["project"], strategy, ("metrics.parquet", "equity.parquet"))
    return work if isinstance(work, str) else [
        "-m", "studies.optimisation.cloud.report", "--work", str(work)]


def wfc(c: dict, strategy: str) -> list[str] | str:
    """Step 17: in against out over one mother's variant batch."""
    work = where.batch(c["project"], strategy, ("metrics.parquet", "collected.json"))
    return work if isinstance(work, str) else [
        "-m", "studies.optimisation.wfc.report", "--work", str(work)]


def cscv(c: dict, strategy: str) -> list[str] | str:
    """Step 18: the probability the selection overfits, over one mother's variant batch."""
    work = where.batch(c["project"], strategy, ("metrics.parquet", "equity.parquet"))
    return work if isinstance(work, str) else [
        "-m", "studies.optimisation.cscv.report", "--work", str(work)]


def wfm(c: dict, strategy: str) -> list[str] | str:
    """Step 19 over the newest Walk-Forward Matrix export of this databank."""
    found = where.newest(DATA / "raw" / c["project"] / c["databank"], "*/wfm")
    if not found:
        return "necesita el export de la Walk-Forward Matrix de este databank (skill /wfm)"
    return ["-m", "studies.optimisation.wfm.report", "--project", c["project"], "--databank",
            c["databank"], "--day", found.parent.name]


# The three batch studies take the mother as their strategy; `many` would be every mother at
# once, which none of their commands does.
STUDIES = {
    "cloud": {"plan": cloud, "one": True, "many": False, "sets": True},
    "wfc": {"plan": wfc, "one": True, "many": False, "sets": True},
    "cscv": {"plan": cscv, "one": True, "many": False, "sets": True},
    "wfm": {"plan": wfm, "one": False, "many": True, "sets": True},
    "marketSurfaces": {"why": "escribe su mirada en el ledger bajo la familia de plantillas, que "
                              "la ventana no sabe: córrelo desde la terminal con --work y "
                              "--family"},
}
