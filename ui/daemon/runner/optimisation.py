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
    found = where.newest(DATA / "raw" / c["project"] / c["databank"].replace(" ", "_"), "*/wfm")
    if not found:
        return "necesita el export de la Walk-Forward Matrix de este databank (skill /wfm)"
    return (["-m", "studies.optimisation.wfm.report", "--project", c["project"], "--databank",
             c["databank"], "--day", found.parent.name]
            + (["--strategy", strategy] if strategy else []))


def mothers(project: str) -> list[str] | str:
    """Every mother with a variant batch of this project, as `core.datapaths.variants_dir` names it.

    Args:
        project: Project name.

    Returns:
        Names sorted, reversing the one space `variants_dir` turned into an underscore (a
        mother is always "Strategy N.N.N", one word and one space) — or the Spanish sentence
        why there is none. What "Run todo el databank" means for a batch study whose input is
        one mother's variant batch, not one strategy of the databank's own export (owner,
        2026-09-30 §8.4/§8.5): every mother, not the population `where.distinct` would find.
    """
    root = DATA / "strategyPermutations" / project
    found = sorted(d.name.replace("_", " ", 1) for d in root.iterdir() if d.is_dir()) \
        if root.is_dir() else []
    return found or f"ningún lote de variantes en {project} (skill /variants)"


# The batch studies take the mother as their strategy, and all of them declare `population`:
# table.jobs runs one job per mother that has a batch — cscv fans out on its own per job
# (jobs.WIDE) and runs them side by side; the others are grouped by `runner.batch.fold` into
# one forked batchrun (cloud and wfc gained «Run todo el databank» this way, owner 2026-10-01).
STUDIES = {
    "cloud": {"plan": cloud, "one": True, "many": True, "sets": True,
              "population": lambda c: mothers(c["project"])},
    "wfc": {"plan": wfc, "one": True, "many": True, "sets": True,
            "population": lambda c: mothers(c["project"])},
    "cscv": {"plan": cscv, "one": True, "many": True, "sets": True,
             "population": lambda c: mothers(c["project"])},
    "marketSurfaces": {"plan": market_surfaces, "one": True, "many": True, "sets": True,
                       "population": lambda c: mothers(c["project"])},
    "wfm": {"plan": wfm, "one": True, "many": True, "sets": True},
}
