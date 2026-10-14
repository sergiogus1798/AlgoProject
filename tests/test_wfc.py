#!/usr/bin/env python3
"""Known answers of step 17: the order read before costs against the weekly sign-flip null and
the level after them, the top and R_sel's guard, and the owner's table cell by cell."""

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engines.weekly import flip
from studies.optimisation.wfc.inputs import config
from studies.optimisation.wfc.measure import level, order, reading
from studies.optimisation.wfc.verdict import state

CFG = config.load(["null.draws=400"])


def both(values: np.ndarray) -> dict:
    """An excess that carries no cost: gross is net."""
    return {"gross": values, "net": values}


def test_the_order_is_read_before_costs_and_the_level_after() -> None:
    """Costs that grow with the rank inside: gross keeps the order, net loses the level; the
    null is the weekly flip of the engine, the first child of the root seed."""
    rng = np.random.default_rng(0)
    skill = np.arange(60.0)
    gross = skill / 50 + rng.normal(0, 2.0, (140, 1)) + rng.normal(0, 0.3, (140, 60))
    weeks = {"gross": gross, "net": gross - skill / 20}  # the best pay the most
    e_oos = {k: w.sum(axis=0) / 2.7 for k, w in weeks.items()}
    e_is = {"gross": skill * 30.0, "net": skill * 30.0 - 600.0}
    found = reading.measure(e_is, e_oos, weeks, 2.7, CFG)
    assert found["rho"] == pytest.approx(flip.spearman(e_is["gross"], e_oos["gross"]))
    assert found["rho"] > 0.9 > flip.spearman(e_is["net"], e_oos["net"])
    best = level.top(e_is["net"], 0.2)
    assert (
        found["nivel_top"] == pytest.approx(np.median(e_oos["net"][best]))
        and found["nivel_top"] < 0
    )
    signs = flip.signs(
        np.random.SeedSequence(CFG["null"]["seed"]).spawn(2)[0], 400, 140, 1
    )
    assert signs.shape == (400, 140) and set(np.unique(signs)) == {-1.0, 1.0}
    want = flip.tails(
        found["rho"], flip.spearman(e_is["gross"], signs @ weeks["gross"])
    )
    assert {k: found[k] for k in want} == want and found["p_mas"] <= 0.05
    tops = np.median((signs @ weeks["net"] / 2.7)[:, best], axis=1)
    assert found["p_nivel"] == (1 + (tops >= found["nivel_top"]).sum()) / 401
    assert state.judge(found, CFG) == {
        "orden": "positivo",
        "fuerte": True,
        "estado": "no_pasa",
    }


def test_too_many_weekend_straddles_draw_the_null_again_in_wider_blocks() -> None:
    """Under the warning nothing more is drawn; over it, p+ and p- in two-week blocks and their class."""
    assert (CFG["null"]["block_weeks"], CFG["null"]["straddle_warn"]) == (1, 0.1)
    assert (
        CFG["annotate"]["block_weeks"] == 2 and config.load()["null"]["draws"] == 2000
    )
    rng = np.random.default_rng(5)
    weeks = rng.normal(0.3, 1.0, (120, 50)) + rng.normal(0, 1.0, (120, 1))
    e_oos, e_is = weeks.sum(axis=0), rng.normal(size=50)
    calm = reading.measure(both(e_is), both(e_oos), both(weeks), 1.0, CFG, 0.10)
    assert calm["fines_de_semana"] == 0.10 and calm["p_mas_bloque"] is None
    assert "orden_bloque" not in state.judge(calm, CFG)
    loud = reading.measure(both(e_is), both(e_oos), both(weeks), 1.0, CFG, 0.11)
    wide = flip.signs(
        np.random.SeedSequence(CFG["null"]["seed"]).spawn(2)[1], 400, 120, 2
    )
    assert (wide[:, 0::2] == wide[:, 1::2]).all()
    want = flip.tails(loud["rho"], flip.spearman(e_is, wide @ weeks))
    assert (loud["p_mas_bloque"], loud["p_menos_bloque"]) == (
        want["p_mas"],
        want["p_menos"],
    )
    assert {
        k: v for k, v in loud.items() if "bloque" not in k and k != "fines_de_semana"
    } == {k: v for k, v in calm.items() if "bloque" not in k and k != "fines_de_semana"}
    assert state.judge(loud, CFG)["orden_bloque"] in ("positivo", "neutro", "perverso")


def test_the_top_its_level_and_the_guarded_retention() -> None:
    """The best fifth, R_sel 1 / -1 / 0 by construction, and no quotient over a null premium."""
    x = np.arange(100.0)
    best = level.top(x, 0.20)
    assert best.sum() == 20 and best[80:].all()
    assert (
        level.top(np.r_[np.zeros(70), np.ones(30)], 0.20).sum() == 30
    )  # ties: some more
    assert level.retention(x, x, best, 0.05) == pytest.approx(1.0)
    assert level.retention(x, -x, best, 0.05) == pytest.approx(-1.0)
    assert level.retention(x, np.full(100, 7.0), best, 0.05) == pytest.approx(0.0)
    assert level.retention(x, np.vstack([x, -x]), best, 0.05) == pytest.approx(
        [1.0, -1.0]
    )
    flat = np.r_[np.zeros(95), np.full(5, 1e-9)]  # premium ~ 0
    assert level.retention(flat, x, level.top(flat, 0.20), 0.05) is None
    assert level.retention(np.ones(100), x, level.top(np.ones(100), 0.20), 0.05) is None


def test_the_partial_rho_removes_what_a_shared_control_explains() -> None:
    """Two sides that agree only through the trade count: rho is high, the partial is not."""
    rng = np.random.default_rng(2)
    trades = rng.uniform(50, 500, 400)
    inside, outside = trades + rng.normal(0, 40, 400), trades + rng.normal(0, 40, 400)
    assert flip.spearman(inside, outside) > 0.8
    assert abs(order.partial(inside, outside, trades[:, None])) < 0.1
    skill = rng.normal(0, 100, 400)
    assert order.partial(inside + skill, outside + skill, trades[:, None]) > 0.7


def test_the_owners_table_cell_by_cell() -> None:
    """Every cell: four orders x the top's median (above zero and beating its null at 0.05,
    above zero without beating it, at or under zero with either p), then the «strong» label."""
    won, unbeaten, lost, lost_far = (
        (5.0, 0.05),
        (5.0, 0.051),
        (0.0, 0.99),
        (-5.0, 0.001),
    )
    table = {
        ("positivo", won): "pasa",
        ("neutro", won): "pasa",
        ("perverso", won): "limbo",
        ("sin_dato", won): "limbo",
    }
    table |= {
        (found, unbeaten): "limbo"
        for found in ("positivo", "neutro", "perverso", "sin_dato")
    }
    table |= {
        (found, top): "limbo" if found == "sin_dato" else "no_pasa"
        for found in ("positivo", "neutro", "perverso", "sin_dato")
        for top in (lost, lost_far)
    }
    assert len(table) == 16
    assert {
        k: state.state(k[0], k[1][0], 100, 30, k[1][1], 0.05) for k in table
    } == table
    assert (
        state.state("positivo", 5.0, 29, 30, 0.01, 0.05) == "limbo"
    )  # under 30 variants
    assert state.state("positivo", -5.0, 29, 30, 0.99, 0.05) == "limbo"
    assert state.classify(0.4, 0.01, 0.99, 0.05) == "positivo"
    assert state.classify(-0.4, 0.99, 0.05, 0.05) == "perverso"
    assert state.classify(0.1, 0.051, 0.9, 0.05) == "neutro"
    assert state.classify(np.nan, 0.001, 0.001, 0.05) == "sin_dato"  # not «positivo»
    found = {
        "rho": 0.31,
        "p_mas": 0.01,
        "p_menos": 0.99,
        "nivel_top": -1.0,
        "n": 100,
        "p_nivel": 0.5,
    }
    assert state.judge(found, CFG) == {
        "orden": "positivo",
        "fuerte": True,
        "estado": "no_pasa",
    }
    assert state.judge(found | {"rho": 0.29}, CFG)["fuerte"] is False


def test_the_level_must_beat_its_null() -> None:
    """judge() cuts `p_nivel` at `level.alpha`: above zero without beating the null is LIMBO."""
    alpha = CFG["level"]["alpha"]
    assert alpha == 0.05
    base = {"rho": 0.1, "p_mas": 0.5, "p_menos": 0.5, "nivel_top": 5.0, "n": 100}
    assert state.judge(base | {"p_nivel": 0.01}, CFG)["estado"] == "pasa"
    assert state.judge(base | {"p_nivel": alpha}, CFG)["estado"] == "pasa"
    for p_nivel in (0.051, 0.5, 0.99):
        assert state.judge(base | {"p_nivel": p_nivel}, CFG)["estado"] == "limbo"
        assert (
            state.judge(base | {"p_nivel": p_nivel, "p_mas": 0.01}, CFG)["estado"]
            == "limbo"
        )
    assert (
        state.judge(base | {"p_nivel": 0.01, "p_menos": 0.01}, CFG)["estado"] == "limbo"
    )
    for p_nivel in (0.01, 0.99):  # at or under zero: no p rescues or worsens it
        assert (
            state.judge(base | {"p_nivel": p_nivel, "nivel_top": 0.0}, CFG)["estado"]
            == "no_pasa"
        )
        assert (
            state.judge(base | {"p_nivel": p_nivel, "nivel_top": -5.0}, CFG)["estado"]
            == "no_pasa"
        )
    x = np.arange(100.0)
    flipped = np.tile(x, (19, 1)) - 1000.0
    assert level.p_value(
        np.median(flipped[:, level.top(x, 0.2)], axis=1), 0.0
    ) == pytest.approx(1 / 20)  # none at or above
    assert level.p_value(np.median(flipped[:, level.top(x, 0.2)], axis=1), -1e9) == 1.0


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
