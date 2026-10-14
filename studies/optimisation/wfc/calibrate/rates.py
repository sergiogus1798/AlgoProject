"""Where families land in the owner's table: the criterion, and the one without a null on the level beside it."""

from collections.abc import Mapping, Sequence
from typing import Any, TypedDict, cast
import numpy as np
import pandas as pd

from core import fanout
from core.study import result
from engines.weekly import flip
from studies.optimisation.wfc.calibrate import families
from studies.optimisation.wfc.measure import reading
from studies.optimisation.wfc.verdict import state

CELLS = tuple(f"{o}/{w}" for o in ("positivo", "neutro", "perverso")
              for w in ("gana", "no_gana")) + (state.NO_DATA,)
STATES = ("pasa", "limbo", "no_pasa")
JOB: dict = {}        # what _scenario reads; set by table() before the fork


def both(values: np.ndarray) -> dict[str, np.ndarray]:
    """A synthetic family's excess as `reading.measure` takes it: it has no cost, gross is net."""
    return {"gross": values, "net": values}


def flips(weeks: np.ndarray, years: float, cfg: dict) -> np.ndarray:
    """The out-of-sample excess per year under the very sign draws `reading.measure` judged with.

    `measure` draws its first null from the first child of `null.seed`, as here: the same
    draws x variants matrix.
    """
    knobs = cfg["null"]
    seed = np.random.SeedSequence(knobs["seed"]).spawn(2)[0]
    return flip.signs(seed, knobs["draws"], len(weeks), knobs["block_weeks"]) @ weeks / years


def sd_rho(e_is: np.ndarray, weeks: np.ndarray, years: float, cfg: dict) -> float:
    """The deviation of rho across the sign-flip draws, which says how alike the variants are."""
    return float(flip.spearman(e_is, flips(weeks, years, cfg)).std())


def without_level_null(order: str, found: dict, cfg: dict) -> str:
    """The state had the level only to be above zero, as the proposal's table was first written.

    Not the criterion: the comparison the calibration prints beside it.
    """
    return state.state(order, found["nivel_top"], found["n"], cfg["panel"]["min_variants"],
                       found["p_nivel"], 1.0)


def cell(found: str, top_level: float) -> str:
    """The cell of the table of section 6: the order's class and whether the top wins outside."""
    return found if found == state.NO_DATA else f"{found}/{'gana' if top_level > 0 else 'no_gana'}"


class Landed(TypedDict):
    """A family's cell, state with and without the level null, level p and null spread."""

    casilla: str
    estado: str
    estado_sin: str
    p_nivel: float
    sd_rho_nulo: float


def landed(e_is: np.ndarray, e_oos: np.ndarray, weeks: np.ndarray, years: float,
           cfg: dict) -> Landed:
    """One family under the criterion and under the one without a null on the level.

    Returns:
        `casilla`, `estado` (the criterion: the top wins when its median is above zero and
        beats its null) and `estado_sin` (the same measures, the median above zero being
        enough), `p_nivel`, `sd_rho_nulo`.
    """
    found = reading.measure(both(e_is), both(e_oos), both(weeks), years, cfg)
    said = state.judge(found, cfg)
    return {"casilla": cell(said["orden"], found["nivel_top"]), "estado": said["estado"],
            "estado_sin": without_level_null(said["orden"], found, cfg),
            "p_nivel": found["p_nivel"], "sd_rho_nulo": sd_rho(e_is, weeks, years, cfg)}


def shares(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """The rate of every cell and state over the families of landed(), and their dependence.

    Returns:
        One rate per name of CELLS and STATES (the criterion) and per STATES again with
        the suffix `_sin` (without a null on the level), `familias`, and the 5th, 50th and
        95th percentiles across families of `sd_rho_nulo` (None when no family was measured).
    """
    got = pd.DataFrame(rows)
    spread = cast(pd.Series, pd.to_numeric(got["sd_rho_nulo"])).dropna()
    low, mid, high = np.percentile(spread, [5, 50, 95]) if len(spread) else (None, None, None)
    return ({name: float((got["casilla"] == name).mean()) for name in CELLS}
            | {name: float((got["estado"] == name).mean()) for name in STATES}
            | {f"{name}_sin": float((got["estado_sin"] == name).mean()) for name in STATES}
            | {"familias": len(got),
               "sd_rho_p5": low, "sd_rho_p50": mid, "sd_rho_p95": high})


def _scenario(index: int) -> dict:
    """The rates of one scenario of JOB, on its own stream of random numbers."""
    spec, cfg, wfc = JOB["specs"][index], JOB["cfg"], JOB["wfc"]
    rng = np.random.default_rng([cfg["seed"], index])
    years = spec["anos_fuera"]
    return shares([landed(*families.draw(spec, cfg, rng), years, wfc)
                   for _ in range(cfg["families"])])


def table(specs: list[dict], cfg: dict, wfc: dict, workers: int) -> pd.DataFrame:
    """Every scenario's rates, one row each, in the order of `specs`.

    Args:
        specs: What `families.specs` returned.
        cfg: The calibration's config.
        wfc: The WFC's config, the criterion under calibration.
        workers: Processes to spread the scenarios over.

    Returns:
        The scenario's own columns followed by what shares() returns.
    """
    JOB.update(specs=specs, cfg=cfg, wfc=wfc)
    done = {}
    for index, got in fanout.run(_scenario, {i: s["anos_fuera"] for i, s in enumerate(specs)},
                                 workers):
        done[index] = specs[index] | got
        result.progress(90 * len(done) // len(specs), f"{len(done)} de {len(specs)} escenarios")
    return pd.DataFrame([done[i] for i in range(len(specs))])
