#!/usr/bin/env python3
"""Known-answer test for studies.breakage.spp.model.mapa: the floored grid, d / d_DD / puesto,
s, m_dd, the tails, z_decay and a flat grid, all on a hand-made grid of twelve permutations."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from studies.breakage.spp.model import mapa

GRID = {
    "min_trades": 30,
    "fixed": ["*Shift[0-9]", "*Shf[0-9]"],
    "iqr_floor": 0.001,
    "min_noise_n": 100,
}
CFG = {
    "grid": GRID,
    "verdict": {"margin": 1.0},
    "criteria": {"is_floor": {"SharpeRatio": 0.1}},
}
NAMES = ["P1", "ATRShift1", "FooShf1"]


def close(got: float, want: float, tol: float = 1e-9) -> bool:
    """Whether two numbers agree."""
    return abs(got - want) <= tol


def grid() -> pd.DataFrame:
    """The mother (-1), nine good permutations 1..9, a thin one (0), a shifted one (10), a clone (11)."""
    rows = [
        dict(
            permutation=-1,
            P1=10,
            ATRShift1=1,
            FooShf1=1,
            NetProfit=800,
            NumberOfTrades=100,
            AvgProfitPerYear=100,
            SharpeRatio=2.0,
            ProfitFactor=2.0,
            Drawdown=14,
            TotalDataYears=8,
        )
    ]
    for k in range(1, 10):
        rows.append(
            dict(
                permutation=k,
                P1=10 + k,
                ATRShift1=1,
                FooShf1=1,
                NetProfit=80 * k,
                NumberOfTrades=100,
                AvgProfitPerYear=10 * k,
                SharpeRatio=0.1 * k,
                ProfitFactor=1 + 0.1 * k,
                Drawdown=2 * k,
                TotalDataYears=8,
            )
        )
    rows.append(
        dict(
            rows[1],
            permutation=0,
            NetProfit=5000,
            NumberOfTrades=20,
            AvgProfitPerYear=5000,
        )
    )
    rows.append(
        dict(rows[1], permutation=10, ATRShift1=3, NetProfit=7777)
    )  # a shift moved
    rows.append(dict(rows[2], permutation=11))  # same backtest as 2
    return pd.DataFrame(rows).set_index("permutation")


def test_the_floored_grid_and_what_it_dropped() -> None:
    """Mother, clone, shifted row and thin row all leave; the fractions say how many."""
    frame, info = mapa.floored(grid(), NAMES, GRID)
    assert sorted(frame.index) == list(range(1, 10)), frame.index
    assert info["n"] == 9
    assert close(info["fijos_frac"], 1 / 12)  # one of the twelve non-mother rows
    assert close(info["excluidas_frac"], 0.1)  # one of the ten distinct rows
    fixed = [
        mapa.is_fixed(n, GRID["fixed"])
        for n in ("IsShift1", "FooShf1", "P1", "CBlock_WssShfDbl31")
    ]
    assert fixed == [True, True, False, False]  # WssShf* is a real period, not a shift


def test_the_four_readings_and_their_signs() -> None:
    """Benefit 10..90 against a real 100; drawdown 2..18 against a real 14, sign flipped."""
    w = mapa.window(grid(), NAMES, CFG)
    b, dd = w["metrics"]["benef_anual"], w["metrics"]["drawdown"]
    assert (b["real"], b["median"], b["iqr"]) == (100, 50, 40)
    assert close(b["d"], 1.25) and close(b["puesto"], 1.0)
    assert close(b["s"], 0.5) and close(b["p10"], 18) and close(b["p5"], 14)
    assert close(dd["d"], -0.5)  # (median 10 - real 14) / IQR 8
    assert close(dd["puesto"], 2 / 9)  # only 16 and 18 are larger than 14
    assert close(dd["m_dd"], 17.2 / 14)
    assert close(w["metrics"]["sharpe"]["d"], (2.0 - 0.5) / 0.4)
    assert (
        close(w["frac_vecinos_rentables"], 1.0)
        and w["n"] == 9
        and w["sobresale"] is None
    )


def test_a_flat_grid_gives_nan_and_a_losing_real_no_shrinkage() -> None:
    """IQR 0: d is NaN, not infinite; real <= 0: s is NaN."""
    r = mapa.reading(np.full(9, 5.0), 9.0, False, 0.001)
    assert np.isnan(r["d"]) and r["median"] == 5.0 and r["puesto"] == 1.0
    g = grid()
    g.loc[-1, "AvgProfitPerYear"] = -3
    assert np.isnan(mapa.window(g, NAMES, CFG)["metrics"]["benef_anual"]["s"])


def test_across_the_two_windows() -> None:
    """z_decay = delta median over sqrt(1/8 + 1/4); r_s only above the build floor."""

    def side(median: float, years: float) -> dict:
        """A window reduced to what `across` reads."""
        return {
            "metrics": {"sharpe": {"median": median}},
            "years": years,
            "n": 9,
            "frame": pd.DataFrame(
                {"SharpeRatio": [median - 0.1, median, median + 0.1]}
            ),
        }

    got = mapa.across(side(0.5, 8), side(0.3, 4), CFG)
    assert close(got["z_decay"], -0.2 / np.sqrt(1 / 8 + 1 / 4)) and close(
        got["r_s"], 0.6
    )
    assert close(got["a"], 0.5 / 9)  # one tie (0.4) out of nine pairs, nothing above
    assert np.isnan(mapa.across(side(0.05, 8), side(0.3, 4), CFG)["r_s"])


if __name__ == "__main__":
    test_the_floored_grid_and_what_it_dropped()
    test_the_four_readings_and_their_signs()
    test_a_flat_grid_gives_nan_and_a_losing_real_no_shrinkage()
    test_across_the_two_windows()
    print("ok")
