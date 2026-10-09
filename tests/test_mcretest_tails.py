#!/usr/bin/env python3
"""T2 and T3 of the MC Retest from their definitions: the tail a re-run shares with the original
(whole, partial, none, a longer run), T3 on a hand-made original and three runs — one identical
in the window, one that parts inside it, one that cannot be dated — with its two «no data» cases,
T2's approximate excess, and an original that is not the harvest's trades one to one."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from studies.breakage.mcRetest.measure import excess
from studies.breakage.mcRetest.model.tails import common_suffix, window_excess

PNL = np.array([5.0, -2.0, 4.0, 1.0, 3.0, 6.0])          # total 17
# One of drift per trade: excess 4, -3, 3, 0, 2, 5. The window opens on the third trade, so the
# original's excess inside it is 3 + 0 + 2 + 5 = 10.
BASE = {"pnl": PNL, "drift": np.ones(6),
        "opened": pd.date_range("2020-01-01", periods=6).to_numpy()}
START = np.datetime64("2020-01-03")
IDENTICAL = np.array([4.0, 1.0, 3.0, 6.0])               # lost the two trades before the window
PARTS = np.array([9.0, 1.0, 3.0, 6.0])                   # shares three, its head is one trade
UNDATED = np.array([7.0, 7.0, 7.0])
CFG = {"min_tail": 3, "min_matched": 0.5}


def test_common_suffix() -> None:
    """Whole, a strict suffix, a partial tail, nothing, and a run longer than the original."""
    assert common_suffix(PNL, PNL) == 6
    assert common_suffix(IDENTICAL, PNL) == 4
    assert common_suffix(PARTS, PNL) == 3
    assert common_suffix(UNDATED, PNL) == 0
    assert common_suffix(np.r_[8.0, 8.0, PNL], PNL) == 6


def test_window_excess() -> None:
    """A tail over the whole window is the original's 10; a shorter one adds the head's P/L less
    the drift of the uncovered trade, pro rata: 7 + 9 - 1 x 1/3."""
    excess_, inside = PNL - 1.0, BASE["opened"] >= START
    assert window_excess(IDENTICAL, 4, excess_, BASE["drift"], inside) == 10.0
    assert np.isclose(window_excess(PARTS, 3, excess_, BASE["drift"], inside), 7 + 9 - 1 / 3)
    # a run that only lost trades inside the window collected no drift there
    assert window_excess(PNL[3:], 3, excess_, BASE["drift"], inside) == 7.0


def test_t3_known_answer() -> None:
    """Two of three runs are dated: median of 10 and 15.667 over 10."""
    got = excess.t3([IDENTICAL, PARTS, UNDATED], BASE, START, CFG)
    assert np.isclose(got["ret_med"], (10 + 7 + 9 - 1 / 3) / 2 / 10)
    assert np.isclose(got["matched_frac"], 2 / 3) and np.isclose(got["identical_frac"], 1 / 3)
    assert got["distinct"] == 3 and got["n"] == 3


def test_t3_short_tail_is_chance() -> None:
    """A run sharing only the last two trades is not dated when three are asked for."""
    got = excess.t3([np.array([0.0, 0.0, 3.0, 6.0]), IDENTICAL], BASE, START, CFG)
    assert got["matched_frac"] == 0.5 and got["ret_med"] == 1.0


def test_t3_no_data() -> None:
    """Too few dated runs, or one single result: no retention, and it says why."""
    few = excess.t3([IDENTICAL, PARTS, UNDATED], BASE, START, {**CFG, "min_matched": 0.7})
    assert np.isnan(few["ret_med"]) and np.isclose(few["matched_frac"], 2 / 3)
    one = excess.t3([PNL, PNL, PNL], BASE, START, CFG)
    assert np.isnan(one["ret_med"]) and one["distinct"] == 1 and one["matched_frac"] == 1.0


def test_t2_approximate_excess() -> None:
    """Totals 17, 11.5 and 6 less the original's drift of 6, against its excess of 11."""
    runs = [PNL, np.array([2.5, 2.0, 3.0, 2.0, 2.0]), np.array([1.0, 1, 1, 1, 1, 1, 0])]
    got = excess.t2(runs, BASE)
    assert np.isclose(got["ret_med_aprox"], 5.5 / 11) and np.isclose(got["f_pos"], 2 / 3)
    assert np.isclose(got["ret_p5_aprox"], 0.55 / 11) and np.isclose(got["ret_benef"], 11.5 / 17)
    assert np.isclose(got["same_count_frac"], 1 / 3) and np.isclose(got["count_dev_med"], 1 / 6)
    assert got["n"] == 3


def test_original_not_aligned() -> None:
    """A harvest of another length, or one trade five cents away, dates nothing."""
    trades = pd.DataFrame({"Close time": BASE["opened"], "pnl": PNL})
    assert excess.original(trades.iloc[1:], PNL, {}, 0.02) is None
    assert excess.original(trades.assign(pnl=PNL + [0, 0, 0.05, 0, 0, 0]), PNL, {}, 0.02) is None
