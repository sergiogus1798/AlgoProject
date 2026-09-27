"""Every study the window can show: family, title, step, whether it eliminates, and how it is run."""

from collections.abc import Callable
from pathlib import Path

from core.paths import ROOT
from ui.daemon.runner import table

# Family order is studies/CLAUDE.md's table; the trade-level Monte Carlo lives in portfolio/
# but reads one strategy, so the window files it under readings.
FAMILIES = ("screening", "transfer", "breakage", "optimisation", "closing", "readings", "data")

# key -> (family, package, title on screen, WORKFLOW step or None for a reading outside it).
# `analysis/` under screening is shared maths, not a study, and is deliberately absent.
STUDIES = {
    "gate": ("screening", "studies.screening.gate", "Puerta IS/OOS", "8"),
    "isOos": ("screening", "studies.screening.isOos", "Panel IS/OOS", "8"),
    "filters": ("screening", "studies.screening.filters", "Filtros candidatos", "8"),
    "replication": ("screening", "studies.screening.replication", "Replicación", "8"),
    "decay": ("screening", "studies.screening.decay", "Decaimiento IS→OOS", "8"),
    "monkeyExcess": ("screening", "studies.screening.monkeyExcess", "Exceso sobre el mono", "8"),
    "snoopingScreen": ("screening", "studies.screening.snoopingScreen",
                       "SPA y StepM contra buy & hold", "8"),
    "falsePositives": ("screening", "studies.screening.falsePositives", "Falsos positivos", "8"),
    "crossmarket": ("transfer", "studies.transfer.crossmarket", "Cross-market", "10"),
    "crossTF": ("transfer", "studies.transfer.crossTF", "Cross-timeframe", "12"),
    "mcRetest": ("breakage", "studies.breakage.mcRetest", "MC Retest", "14"),
    "spp": ("breakage", "studies.breakage.spp", "Permutación de parámetros (SPP)", "16"),
    "cloud": ("optimisation", "studies.optimisation.cloud", "Nube de parámetros", "16.5"),
    "wfc": ("optimisation", "studies.optimisation.wfc", "Walk Forward Correlation", "17"),
    "cscv": ("optimisation", "studies.optimisation.cscv", "CSCV / PBO", "18"),
    "marketSurfaces": ("optimisation", "studies.optimisation.marketSurfaces",
                       "Superficies por mercado", "18.5"),
    "wfm": ("optimisation", "studies.optimisation.wfm", "Walk Forward Matrix", "19"),
    "blindJoint": ("closing", "studies.closing.blindJoint", "Lectura conjunta ciega", "20"),
    "exposure": ("closing", "studies.closing.exposure", "Exposición contra buy & hold", "21"),
    "atrCalculator": ("closing", "studies.closing.atrCalculator", "Stop loss ATR", "24"),
    "monkey": ("readings", "studies.readings.monkey", "Test del mono", None),
    "profitShape": ("readings", "studies.readings.profitShape", "Forma del beneficio", None),
    "entryQuality": ("readings", "studies.readings.entryQuality", "Calidad de la entrada", None),
    "edgeCost": ("readings", "studies.readings.edgeCost", "Edge por coste", "8"),
    "conditionalMap": ("readings", "studies.readings.conditionalMap", "Mapa condicional", "22"),
    "structure": ("readings", "studies.readings.structure", "Estructura", "23"),
    "monteCarlo": ("readings", "portfolio.common.monteCarlo", "Monte Carlo de operaciones", None),
    "feedQuality": ("data", "studies.data.feedQuality", "Calidad del feed", "8"),
    "spread": ("data", "studies.data.spread", "Spread real de Darwinex", "8"),
}

# Gate = its verdict.csv is meant to remove strategies through /curate, which drops exactly
# the rows that say DESCARTAR and keeps every other word. A callable decides from the
# study's current config when that choice is the owner's knob.
ROLE: dict[str, str | Callable[[dict], bool]] = {
    # hard screens write DESCARTAR; /oos-gate hands its verdict.csv to /curate
    "gate": "gate",
    # a correlation map and predictor ranking over the population; no per-strategy verdict
    "isOos": "describe",
    # what a candidate IS filter would buy out of sample; proposes, removes nobody
    "filters": "describe",
    # whether one databank's conclusions hold on another; compares samples
    "replication": "describe",
    # verdict.csv with identity says MANTENER / DUDOSA / DESCARTAR per strategy
    "decay": "gate",
    # counts how many beat their monkeys and how many chance gives; population reading
    "monkeyExcess": "describe",
    # "annotates and removes nobody" (owner, 2026-09-25): every verdict.csv row is MANTENER
    "snoopingScreen": "describe",
    # not built yet
    "falsePositives": "describe",
    # many.py: "the verdict /curate applies" — DESCARTAR under the breadth floor
    "crossmarket": "gate",
    # verdict.csv carries one of five readings, never DESCARTAR, so /curate keeps every row
    "crossTF": "describe",
    # verdict.csv says STRONG..FAIL/INCONCLUSIVE, never DESCARTAR: /curate would keep every row
    "mcRetest": "describe",
    # a design brief for the variant factory, not a cut
    "spp": "describe",
    # reads the variant batch for peak vs plateau; "no elige nada" (WORKFLOW)
    "cloud": "describe",
    # the 17/18/18.5/19 pieces feed step 20's blind read and cut nobody before it
    "wfc": "describe",
    "cscv": "describe",
    "marketSurfaces": "describe",
    "wfm": "describe",
    # MANTENER for all while joint.pieces or joint.population is null; DESCARTAR once both set
    "blindJoint": lambda cfg: bool(cfg["joint"]["pieces"] and cfg["joint"]["population"]),
    # worth_it / not_worth_it, never DESCARTAR
    "exposure": "describe",
    # verdict block `info`, "never a choice" (README)
    "atrCalculator": "describe",
    # the trade-level readings describe one strategy; none writes DESCARTAR
    "monkey": "describe",
    "profitShape": "describe",
    "entryQuality": "describe",
    # "fabrica hipótesis, no filtra" (WORKFLOW step 22)
    "conditionalMap": "describe",
    # "Diagnóstico, nunca selección" (WORKFLOW step 23)
    "structure": "describe",
    # verdict.csv carries a tier, not a verdict column
    "monteCarlo": "describe",
    # DESCARTAR only with verdict.action = drop; mark today (ledger, 2026-09-26)
    "edgeCost": lambda cfg: cfg["verdict"]["action"] == "drop",
    # DESCARTAR only with alarm.action = drop; mark today (ledger, owner 2026-09-26)
    "feedQuality": lambda cfg: cfg["alarm"]["action"] == "drop",
    # DESCARTAR only with reprice.action = drop; mark today
    "spread": lambda cfg: cfg["reprice"]["action"] == "drop",
}


# Studies that write into a mother's variant batch (`estudios/`), not under reports/<P>/<D>/:
# /api/result cannot reach them yet, and the page says so instead of «sin resultado».
BATCH = {"cloud", "wfc", "cscv"}


def folder(key: str) -> Path:
    """The study's source folder.

    Args:
        key: Study key, e.g. "profitShape".

    Returns:
        Path under the repository.
    """
    return ROOT.joinpath(*STUDIES[key][1].split("."))


def role(key: str, cfg: dict | None) -> str:
    """Whether the study eliminates or only describes, under its current config.

    Args:
        key: Study key.
        cfg: Its current config, None for a study without one.

    Returns:
        "gate" or "describe".
    """
    said = ROLE[key]
    if isinstance(said, str):
        return said
    return "gate" if said(cfg) else "describe"


def entry(key: str, cfg: dict | None) -> dict:
    """One row of the catalogue.

    Args:
        key: Study key.
        cfg: Its current config, None for a study without one.

    Returns:
        key, family, title, step, role, one, many, runnable, why_not, source. `one`, `many`,
        `runnable` and `why_not` are the runner's (`ui.daemon.runner.table`), so the window
        never offers a button the runner refuses. A study the window never starts has no
        scope there; its `one`/`many` then say what its files can judge.
    """
    family, _, title, step = STUDIES[key]
    why = table.why_not(key)
    if why:
        here = folder(key)
        one = (here / "one.py").exists()
        many = (here / "many.py").exists() or ((here / "report.py").exists() and not one)
    else:
        one, many = table.STUDIES[key]["one"], table.STUDIES[key]["many"]
    return {"key": key, "family": family, "title": title, "step": step, "role": role(key, cfg),
            "one": one, "many": many, "runnable": why is None, "why_not": why,
            "source": "batch" if key in BATCH else "reports"}


def ordered() -> list[str]:
    """Every study key in family order, then in the order of `STUDIES`.

    Returns:
        Keys.
    """
    return sorted(STUDIES, key=lambda k: FAMILIES.index(STUDIES[k][0]))
