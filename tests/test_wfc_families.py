#!/usr/bin/env python3
"""Step 17 on synthetic families whose answer is known: with no edge the order is called «perverso»
(or «positivo») at most alpha of the time, and a family planted in each of the six cells of the
owner's table (order positivo / neutro / perverso x the top wins / does not) lands in its cell and
takes that cell's state, and a family with no edge is PASA about alpha of the time, not half.
Run as a script it also prints a measurement that gates nothing: how
often a FLAT edge traded at unequal frequencies is called «positivo», before and after costs."""

import sys
from functools import cache
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from studies.optimisation.wfc.calibrate import families
from studies.optimisation.wfc.inputs import config
from studies.optimisation.wfc.measure import reading
from studies.optimisation.wfc.verdict import state

FAMILIES, VARIANTS, WEEKS_IN, WEEKS_OUT, YEAR = 300, 120, 312, 104, families.YEAR
CFG = config.load(["null.draws=400"])
# kind -> (mean weekly excess, its spread across variants, how the spread carries outside):
# +1 the same variants are good outside, -1 the best inside are the worst outside.
KINDS = {
    "sin ventaja": (0.0, 0.0, 1),
    "ventaja con orden": (0.55, 0.13, 1),
    "todas ganan, sin orden": (0.55, 0.0, 1),
    "todas ganan, orden invertido": (0.55, 0.13, -1),
    "orden, y todo pierde": (-0.55, 0.13, 1),
    "todas pierden, sin orden": (-0.55, 0.0, 1),
    "todas pierden, orden invertido": (-0.55, 0.13, -1),
}
# kind -> its cell of the table of section 6 (order, the top wins) and that cell's state.
CELLS = {
    "ventaja con orden": ("positivo", "pasa"),
    "todas ganan, sin orden": ("neutro", "pasa"),
    "todas ganan, orden invertido": ("perverso", "limbo"),
    "orden, y todo pierde": ("positivo", "no_pasa"),
    "todas pierden, sin orden": ("neutro", "no_pasa"),
    "todas pierden, orden invertido": ("perverso", "no_pasa"),
}
ORDERS, STATES = ("positivo", "neutro", "perverso"), ("pasa", "limbo", "no_pasa")
# The flat edge of flat(): trades a week of the slowest and the fastest variant, the gross
# edge of a trade (one trade's deviation is ~1.08), the cost of a trade, the noise of its own.
FREQUENCY, EDGE, COST, OWN = (0.5, 3.0), 0.11, 0.05, 0.4


def both(values: np.ndarray) -> dict:
    """An excess that carries no cost: gross is net."""
    return {"gross": values, "net": values}


def said(e_is: dict, e_oos: dict, weeks: dict) -> dict:
    """The words of one family, as the study says them."""
    return state.judge(reading.measure(e_is, e_oos, weeks, WEEKS_OUT / YEAR, CFG), CFG)


def shares(words: list[dict]) -> dict:
    """The share of the families in each order and in each state."""
    return {o: np.mean([w["orden"] == o for w in words]) for o in ORDERS} | {
        s: np.mean([w["estado"] == s for w in words]) for s in STATES
    }


@cache
def rates() -> pd.DataFrame:
    """The share of FAMILIES families of each kind in each order and in each state."""
    rng = np.random.default_rng(48)
    return pd.DataFrame(
        {
            kind: shares(
                [
                    said(
                        *(
                            both(part)
                            for part in families.family(
                                *shape, VARIANTS, WEEKS_IN, WEEKS_OUT, rng
                            )
                        )
                    )
                    for _ in range(FAMILIES)
                ]
            )
            for kind, shape in KINDS.items()
        }
    ).T


def test_no_edge_is_called_perverse_at_most_alpha() -> None:
    """The weekly sign-flip null holds its size on each tail, within three simulation errors."""
    alpha = CFG["null"]["alpha"]
    most = alpha + 3 * np.sqrt(alpha * (1 - alpha) / FAMILIES)
    got = rates()
    for kind in ("sin ventaja", "todas ganan, sin orden", "todas pierden, sin orden"):
        assert (
            got.loc[kind, "perverso"] <= most and got.loc[kind, "positivo"] <= most
        ), got
    assert got.loc["sin ventaja", "perverso"] > 0, got


def test_each_planted_family_lands_in_its_cell_of_the_table() -> None:
    """One planted family per cell of section 6: its order, and the state the table gives it."""
    got = rates()
    for kind, (order, call) in CELLS.items():
        floor = (
            0.85 if order == "neutro" else 0.9
        )  # a neutral order is missed alpha per tail
        assert got.loc[kind, order] >= floor and got.loc[kind, call] >= floor, (
            kind,
            got,
        )
    assert got.loc["todas ganan, orden invertido", "pasa"] == 0
    assert got.loc[[k for k in KINDS if "pierde" in k], "pasa"].max() == 0


def test_no_edge_passes_at_most_alpha_and_waits_in_limbo() -> None:
    """The level must beat its null: no edge is PASA at most `level.alpha`, NO PASA half the time
    (a median under zero) and LIMBO the rest (a median above zero that is noise)."""
    alpha, got = CFG["level"]["alpha"], rates().loc["sin ventaja"]
    assert got["pasa"] <= alpha + 3 * np.sqrt(alpha * (1 - alpha) / FAMILIES), got
    assert abs(got["no_pasa"] - 0.5) <= 3 * np.sqrt(0.25 / FAMILIES), got
    assert abs(got["limbo"] - (0.5 - got["pasa"])) <= 3 * np.sqrt(0.25 / FAMILIES), got


def flat(per_trade: bool, rng: np.random.Generator) -> tuple[dict, dict, dict]:
    """One family with the same positive level for every variant and no order to find.

    The variants differ only in how often they trade; every trade pays COST. A week's gross
    excess is its trades' edge plus a common factor and noise of its own, both growing with
    the root of the trades.

    Args:
        per_trade: True gives every TRADE the same gross edge, so a variant's level per year
            grows with its frequency; False gives every VARIANT the same gross level per
            year, its edge per trade shrinking with its frequency.
        rng: The generator.

    Returns:
        (e_is, e_oos, weeks) as `reading.measure` takes them, `gross` and `net`.
    """
    often = rng.uniform(*FREQUENCY, VARIANTS)
    edge = EDGE if per_trade else EDGE * np.mean(FREQUENCY) / often

    def side(weeks: int) -> dict:
        """Weeks x variants of excess, before and after costs."""
        trades = rng.poisson(often, (weeks, VARIANTS))
        gross = trades * edge + np.sqrt(trades) * (
            rng.normal(size=(weeks, 1)) + OWN * rng.normal(size=trades.shape)
        )
        return {"gross": gross, "net": gross - COST * trades}

    inside, outside = side(WEEKS_IN), side(WEEKS_OUT)
    return (
        {k: w.sum(axis=0) / (WEEKS_IN / YEAR) for k, w in inside.items()},
        {k: w.sum(axis=0) / (WEEKS_OUT / YEAR) for k, w in outside.items()},
        outside,
    )


def flat_rates() -> pd.DataFrame:
    """The measurement: each reading of «flat» with the order read on gross (the study) and on net."""
    rng = np.random.default_rng(17)
    rows = {}
    for name, per_trade in (
        ("mismo nivel por año", False),
        ("mismo margen por operación", True),
    ):
        drawn = [flat(per_trade, rng) for _ in range(FAMILIES)]
        rows[f"{name} · orden en bruto"] = shares([said(*family) for family in drawn])
        rows[f"{name} · orden en neto"] = shares(
            [
                said(*({"gross": part["net"], "net": part["net"]} for part in family))
                for family in drawn
            ]
        )
    return pd.DataFrame(rows).T


if __name__ == "__main__":
    print(
        f"{FAMILIES} familias por fila, {VARIANTS} variantes, {WEEKS_OUT} semanas fuera, "
        f"{CFG['null']['draws']} sorteos, alpha {CFG['null']['alpha']}\n"
        f"{rates().round(3).to_string()}\n"
    )
    test_no_edge_is_called_perverse_at_most_alpha()
    test_each_planted_family_lands_in_its_cell_of_the_table()
    test_no_edge_passes_at_most_alpha_and_waits_in_limbo()
    print(
        "ok\n\nMedida, no criterio — ventaja PLANA (ningún orden real), frecuencias de "
        f"{FREQUENCY[0]} a {FREQUENCY[1]} operaciones por semana, margen bruto {EDGE} y coste "
        f"{COST} por operación:\n{flat_rates().round(3).to_string()}"
    )
