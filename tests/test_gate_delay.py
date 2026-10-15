#!/usr/bin/env python3
"""The one-bar delay of the gate (level 2): a price that does not move where a fill could land
keeps all of the edge, an edge made in the entry bar alone keeps none of it when the entry
slips, a mean excess that is not positive leaves both facts empty, the unmoved variant is
level 1a's own excess, and a trade shorter than the shift leaves the variant."""

import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from studies.screening.analysis import delay  # noqa: E402
from studies.screening.gate import level1a, level2  # noqa: E402

SPAN = ("2020-01-01", "2020-12-31")
CYCLE, CYCLES, ENTER, LEAVE, FALL = 20, 400, 2, 10, 15
FREE = {
    "point_value": 1.0,
    "tick_size": 0.01,
    "spread": 0.0,
    "slippage": 0.0,
    "commission_method": "SizeBased",
    "rounds": True,
    "commission": 0.0,
    "swap_long": 0.0,
    "swap_short": 0.0,
    "triple": 4,
    "rollover": 23,
}
DRIFT = {"window": "year", "variant": "a", "se_skew_kurt": True}


def sawtooth(rise: int) -> pd.DataFrame:
    """Hourly bars, flat but for +1 after bar `rise` of every 20 and -1 after bar 15: no drift."""
    phase = np.arange(CYCLE * CYCLES) % CYCLE
    open_ = 100.0 + ((phase > rise) & (phase <= FALL))
    return pd.DataFrame(
        {"Open": open_, "Close": np.roll(open_, -1)},
        index=pd.date_range(SPAN[0], periods=len(open_), freq="1h"),
    )


def trades(
    frame: pd.DataFrame, side: str = "Buy", identity: str = "x", sample: str = "OOS"
) -> pd.DataFrame:
    """One trade per cycle, in at bar 2 and out at bar 10, of lots between 1 and 2."""
    start = CYCLE * np.arange(1, CYCLES - 1)
    lots = np.random.default_rng(0).integers(100, 201, len(start)) / 100
    return pd.DataFrame(
        {
            "identity": identity,
            "Type": side,
            "Open time": frame.index[start + ENTER],
            "Close time": frame.index[start + LEAVE],
            "Size": lots,
            "sample": sample,
        }
    )


def gate(
    harvest: pd.DataFrame,
    frame: pd.DataFrame,
    costs: dict = FREE,
    drift: dict = DRIFT,
    **knobs: object,
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Levels 1a and 2 on one harvest: (level 2's facts, retraso.parquet by variant, data)."""
    cfg = {
        "drift": drift,
        "delay": {"variants": ["E+1", "S+1", "ES+1"], "on_build": False, **knobs},
    }
    alive = pd.Index(harvest["identity"].unique())
    with tempfile.TemporaryDirectory() as out:
        data = {
            "trades": harvest,
            "bars": frame,
            "costs": costs,
            "costs_build": costs,
            "out": Path(out),
            "market": {"windows": {"OOS": SPAN, "IS": SPAN}},
        }
        level1a.run(data, alive, cfg)
        facts = level2.run(data, alive, cfg)
        data["written"] = {
            p.name: pd.read_parquet(p) for p in Path(out).glob("retraso*")
        }
    return (
        facts,
        data["written"]["retraso.parquet"].set_index(["identity", "variant"]),
        data,
    )


def test_price_flat_where_a_fill_could_land_keeps_everything() -> None:
    """The move happens mid-hold: one bar earlier or later fills at the same price, ret = 1."""
    frame = sawtooth(rise=5)
    facts, table, _ = gate(trades(frame), frame, variants=["E+1", "S+1", "ES+1", "E-1"])
    assert (table["ret"] == 1.0).all() and len(table) == 4
    assert facts.loc["x", "retraso_ret_min"] == 1.0


def test_edge_in_the_entry_bar_alone_is_lost_one_bar_late() -> None:
    """The whole move is the entry bar's: E+1 and ES+1 keep 0, S+1 and E-1 keep 1; the worst is
    judged, with ITS paired t — every trade loses its own lots, so the t is that of the lots."""
    frame = sawtooth(rise=ENTER)
    harvest = trades(frame)
    facts, table, _ = gate(harvest, frame, variants=["S+1", "E-1", "E+1", "ES+1"])
    assert table["ret"].xs("x").to_dict() == {
        "S+1": 1.0,
        "E-1": 1.0,
        "E+1": 0.0,
        "ES+1": 0.0,
    }
    lots = harvest["Size"]
    known = lots.mean() / lots.std(ddof=1) * np.sqrt(len(lots))
    assert facts.loc["x", "retraso_ret_min"] == 0.0
    assert np.isclose(facts.loc["x", "retraso_t_delta"], known) and known > 1.65
    assert np.isclose(table.loc[("x", "E+1"), "t_delta"], known)
    assert np.isnan(table.loc[("x", "S+1"), "t_delta"])  # nothing lost: no t to give


def test_mean_excess_not_positive_leaves_both_facts_empty() -> None:
    """A short loses on the same bars: a negative over a negative is not a retention. The long
    beside it keeps its facts, and an identity alive with no trades reads empty."""
    frame = sawtooth(rise=ENTER)
    harvest = pd.concat([trades(frame, "Sell", "short"), trades(frame, "Buy", "long")])
    facts, table, data = gate(harvest, frame)
    assert facts.loc["short"].isna().all() and table["ret"].xs("short").isna().all()
    assert facts.loc["long", "retraso_ret_min"] == 0.0
    cfg = {"drift": DRIFT, "delay": {"variants": ["E+1"], "on_build": False}}
    with tempfile.TemporaryDirectory() as out:
        again = level2.run({**data, "out": Path(out)}, pd.Index(["long", "ghost"]), cfg)
    assert list(again.index) == ["long", "ghost"] and again.loc["ghost"].isna().all()
    assert list(again.columns) == list(level2.FACTS)


def test_unmoved_variant_is_level_1a_and_a_one_bar_trade_leaves_the_late_entry() -> (
    None
):
    """With costs and the per-window drift: shift (0, 0) reproduces level 1a's excess to the
    cent, and a one-bar trade does not exist entered a bar late: out of both means of E+1 (and
    of no other variant), so E+1's retention is that of the longer trades alone."""
    index = pd.date_range(SPAN[0], periods=6000, freq="1h")
    close = (
        500.0 + np.random.default_rng(3).integers(-30, 34, len(index)).cumsum() / 100
    )
    frame = pd.DataFrame(
        {"Open": np.r_[500.0, close[:-1]], "Close": close}, index=index
    )
    paid = {
        **FREE,
        "spread": -0.5,
        "slippage": 0.1,
        "swap_long": -5.0,
    }  # a rebate: mean > 0
    at = np.arange(50, 5900, 13)
    harvest = pd.DataFrame(
        {
            "identity": "x",
            "Type": "Buy",
            "Open time": index[at],
            "Close time": index[at + 1 + at % 7],
            "Size": 1.0,
            "sample": "OOS",
        }
    )
    drift = {"window": "quarter", "variant": "b", "se_skew_kurt": False}
    _, table, data = gate(harvest, frame, paid, drift)
    oos = data["oos"]
    assert np.allclose(
        delay.excess(oos, frame, SPAN, paid, drift), oos["excess"], atol=1e-9
    )
    late = delay.excess(oos, frame, SPAN, paid, drift, delay.SHIFTS["E+1"])
    one_bar = at % 7 == 0
    assert np.isnan(late[one_bar]).all() and np.isfinite(late[~one_bar]).all()
    for name in ("S+1", "ES+1"):
        assert np.isfinite(
            delay.excess(oos, frame, SPAN, paid, drift, delay.SHIFTS[name])
        ).all()
    assert oos["excess"].mean() > 0
    assert np.isclose(
        table.loc[("x", "E+1"), "ret"],
        late[~one_bar].mean() / oos["excess"][~one_bar].mean(),
    )
    assert np.isfinite(table.to_numpy(float)).all()


def test_on_build_writes_the_build_table_and_changes_no_fact() -> None:
    """The same trades as build and as oos1, at the same costs: the two tables are one."""
    frame = sawtooth(rise=ENTER)
    harvest = pd.concat([trades(frame), trades(frame, sample="IS")])
    off, _, _ = gate(harvest, frame)
    on, _, data = gate(harvest, frame, on_build=True)
    pd.testing.assert_frame_equal(on, off)
    pd.testing.assert_frame_equal(
        data["written"]["retraso_build.parquet"], data["written"]["retraso.parquet"]
    )


def test_a_stop_exit_never_moves() -> None:
    """Known answer: level 1a prices a stop-loss at SQX's price instead of dying or filling it
    at its bar's open, and level 2 leaves that exit where it was — S+1 changes nothing of a
    stopped trade and ES+1 is its E+1 — while a bar exit still slips."""
    index = pd.date_range(SPAN[0], periods=6000, freq="1h")
    open_ = (
        500.0 + np.random.default_rng(3).integers(-30, 34, len(index)).cumsum() / 100
    )
    frame = pd.DataFrame(
        {
            "Open": open_,
            "Close": np.r_[open_[1:], open_[-1]],
            "Low": open_ - 1,
            "High": open_ + 1,
        },
        index=index,
    )
    at = np.arange(50, 5900, 13)
    stopped = np.arange(len(at)) % 2 == 0
    harvest = pd.DataFrame(
        {
            "identity": "x",
            "Type": "Buy",
            "Open time": index[at],
            "Close time": index[at + 3],
            "Size": 1.0,
            "sample": "OOS",
            "Close price": open_[at + 3] - 0.5,
            "Close type": np.where(stopped, "SL", "Exit After X Bars"),
        }
    )
    _, _, data = gate(harvest, frame)
    oos = data["oos"]
    assert np.allclose(oos["pnl"], open_[at + 3] - 0.5 * stopped - open_[at])
    assert np.allclose(oos["stop"][stopped], open_[at + 3][stopped] - 0.5)
    assert oos["stop"][~stopped].isna().all()
    moved = {
        name: delay.excess(oos, frame, SPAN, FREE, DRIFT, delay.SHIFTS[name])
        for name in ("E+1", "S+1", "ES+1")
    }
    assert np.allclose(moved["S+1"][stopped], oos["excess"][stopped])
    assert np.allclose(moved["ES+1"][stopped], moved["E+1"][stopped])
    assert not np.isclose(moved["S+1"][~stopped], oos["excess"][~stopped]).all()


if __name__ == "__main__":
    for check in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        check()
        print("ok", check.__name__)
