#!/usr/bin/env python3
"""Step 12 reads oos1 only and prices in that a sibling re-reads its mother's years (2026-10-02,
an agent's proposal pending the owner): every cell is measured on its oos1 trades against a null
drawn inside oos1; `z` is its distance from that null; `z_new` is what a sibling adds beyond its
mother; the mother's `combined_*` sum her usable siblings; under 30 trades a sibling reads
`no_data`, never `inherited`; the control is shown, not read; rounding and the floor discard no
sibling; a seed replays the run; and every numeric column is a fact of the mother."""

import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import assetdata
from engines.nulls import inputs as nullinputs
from pipeline.autopilot import facts
from studies.transfer.crossTF import cells, inputs, verdict

FEED = "XAUUSD_M1"
START = pd.Timestamp(assetdata.window(assetdata.load("XAUUSD"), "oos1")[0], unit="ms")
SCALING = pd.DataFrame({"mother": ["A", "A"], "name": ["A_ScaledH4", "A_ScaledM30"],
                        "source_tf": ["H1", "H1"], "target_tf": ["H4", "M30"],
                        "ratio": [4.0, 0.5], "n_scaled": [3, 3],
                        "max_rounding_shift": [0.125, 0.0], "clamped": [False, False],
                        "unverified": ["", ""]})
CFG = {"verdict": {"statistic": "sharpe", "rung": "timing", "alpha": 0.05},
       "usable": {"min_trades": 30}}


def bars(rule: str) -> pd.DataFrame:
    """Four years of a seeded random walk around the oos1 start, as bars of one timeframe."""
    index = pd.date_range(START - pd.Timedelta(days=730), periods=4 * 365 * 48, freq="30min")
    close = pd.Series(1000 + np.random.default_rng(7).normal(0, 1, len(index)).cumsum(), index)
    frame = close.resample(rule).ohlc().rename(columns=str.capitalize)
    return frame.assign(Open=frame["Close"].shift(1).fillna(1000.0))


def trades(frame: pd.DataFrame, strategy: str, block: int, every: int) -> pd.DataFrame:
    """One long trade every `every` bars, open to open three bars later, 5 of cost each."""
    at = np.arange(20, len(frame) - 10, every)
    move = frame["Open"].to_numpy()[at + 3] - frame["Open"].to_numpy()[at]
    return pd.DataFrame({"strategy": strategy, "block": block, "Open time": frame.index[at],
                         "Close time": frame.index[at + 3],
                         "Open price": frame["Open"].to_numpy()[at],
                         "Close price": frame["Open"].to_numpy()[at + 3], "Size": 1.0,
                         "Profit/Loss": 100.0 * move - 5.0})


def panel(seed: int = 1, cfg: dict = CFG) -> pd.DataFrame:
    """A mother, her H4 sibling and a thin M30 one, measured as the study measures them."""
    frames = {"H1": bars("1h"), "H4": bars("4h"), "M30": bars("30min")}
    packed = pd.concat([trades(frames["H1"], "A", 0, 60), trades(frames["H4"], "A", 1, 400),
                        trades(frames["M30"], "A", 2, 900),
                        trades(frames["H4"], "A_ScaledH4", 1, 15),
                        trades(frames["H1"], "A_ScaledH4", 0, 61),
                        trades(frames["M30"], "A_ScaledM30", 2, 2500),
                        trades(frames["H1"], "A_ScaledM30", 0, 63)], ignore_index=True)
    nullcfg = nullinputs.config(["nulls.draws=200"] + nullinputs.seeded(seed)) | {"feed": FEED}
    return cells.panel(inputs.plan(SCALING, ["H1", "H4", "M30"]), inputs.oos(packed, FEED),
                       frames, nullcfg, cfg)


def cell(got: pd.DataFrame, role: str, timeframe: str) -> pd.Series:
    """The one cell of that role on that timeframe (the first, for the two controls)."""
    return got[(got["role"] == role) & (got["timeframe"] == timeframe)].iloc[0]


def test_only_oos1_is_read_and_a_seed_replays_it() -> None:
    """Half the synthetic trades open before oos1 and none of them is counted; the same seed
    gives the same p, another seed another one."""
    base = cell(panel(), "baseline", "H1")
    written = len(trades(bars("1h"), "A", 0, 60))
    assert 0 < base["trades"] < written and abs(base["trades"] - written / 2) < 3
    assert abs(base["z"] - (base["seen"] - base["null_mean"]) / base["null_sd"]) < 1e-12
    assert cell(panel(), "baseline", "H1")["p"] == base["p"]
    assert cell(panel(2), "baseline", "H1")["null_mean"] != base["null_mean"]


def test_what_a_sibling_adds_and_what_the_mother_sums() -> None:
    """z_new is the sibling's z with its mother's taken out at the pair's own correlation; the
    mother sums the usable siblings that have one; the thin M30 sibling has none."""
    got = panel()
    base, h4, m30 = cell(got, "baseline", "H1"), cell(got, "scaled", "H4"), \
        cell(got, "scaled", "M30")
    rho = min(max(h4["corr_vs_baseline"], 0.0), cells.MOST_ALIKE)
    assert abs(h4["z_new"] - (h4["z"] - rho * base["z"]) / np.sqrt(1 - rho ** 2)) < 1e-12
    assert m30["trades"] < 30 and np.isnan(m30["z_new"]) and np.isnan(m30["p"])
    assert base["combined_n_tested"] == 1 and base["combined_z_new"] == h4["z_new"]
    assert base["combined_z_new_max"] == h4["z_new"] and np.isnan(h4["combined_z_new"])
    assert h4["rounding_shift"] == 0.125 and h4["clamped"] == 0.0 and h4["unverified"] == 0.0


def reading(z_new: float, p: float, seen: float, trades: int = 100, control: float = 0.0,
            baseline: float = 0.1, scaling: pd.DataFrame = SCALING) -> str:
    """The study's reading of one hand-made H4 sibling."""
    made = pd.DataFrame([
        {"role": "baseline", "strategy": "A", "mother": "A", "timeframe": "H1", "seen": baseline},
        {"role": "control", "strategy": "A_ScaledH4", "mother": "A", "timeframe": "H1",
         "seen": control},
        {"role": "scaled", "strategy": "A_ScaledH4", "mother": "A", "timeframe": "H4",
         "seen": seen, "p": p, "z": 2.0, "z_new": z_new, "trades": trades, "warnings": []}])
    return verdict.read(made, scaling, CFG)["reading"].iloc[0]


def test_the_reading() -> None:
    """Both tests for `survives`; under 30 trades `no_data`, never `inherited`; the control
    decides nothing, whatever the baseline's sign; only an unverified length is `unusable`."""
    assert reading(2.0, 0.01, 0.2) == "survives"
    assert reading(1.0, 0.01, 0.2) == "inherited"          # significant, but its mother's doing
    assert reading(2.0, 0.20, 0.2) == "inherited"
    assert reading(-1.0, 0.90, -0.1) == "fails"
    assert reading(float("nan"), float("nan"), 0.3, trades=12) == "no_data"
    assert reading(float("nan"), float("nan"), float("nan"), trades=0) == "silent"
    assert reading(2.0, 0.01, 0.2, control=-5.0) == "survives"
    assert reading(2.0, 0.01, 0.2, control=-0.06, baseline=-0.10) == "survives"
    assert reading(2.0, 0.01, 0.2, scaling=SCALING.assign(unverified="CBlock_XInt11")) == \
        "unusable"
    # owner, 2026-10-02 («Redondea donde puedas, ya está»): rounding and the floor discard nobody
    assert reading(2.0, 0.01, 0.2, scaling=SCALING.assign(clamped=True,
                                                          max_rounding_shift=3.0)) == "survives"
    assert "control_failed" not in verdict.MEANS and "no_data" in verdict.MEANS


def test_every_numeric_column_is_a_fact_of_the_mother() -> None:
    """The sibling's cells are keyed under its mother, the combined ones under `combined.`, and
    a NaN is no fact at all (limbo)."""
    with tempfile.TemporaryDirectory() as tmp:
        panel().to_parquet(Path(tmp) / "cells.parquet", index=False)
        pd.DataFrame({"mother": ["A", "A"], "timeframe": ["H4", "M30"],
                      "reading": ["inherited", "no_data"]}
                     ).to_csv(Path(tmp) / "verdict.csv", index=False)
        rows = [r for r in facts.crosstf_rows(Path(tmp)) if r["value"] is not None]
    got = {r["key"]: r["value"] for r in rows}
    assert {r["strategy"] for r in rows} == {"A"}
    for key in ("cells.scaled.H4.z", "cells.scaled.H4.z_new", "cells.scaled.H4.rounding_shift",
                "cells.control.H4.clamped", "cells.scaled.H4.corr_vs_baseline",
                "cells.scaled.M30.trades", "cells.scaled.H4.sharpe_vs_original",
                "combined.z_new", "combined.z_new_max", "reading.M30.no_data"):
        assert key in got, key
    assert got["combined.n_tested"] == 1.0 and got["reading.n_no_data"] == 1.0
    assert "cells.scaled.M30.z_new" not in got and "cells.baseline.H1.rounding_shift" not in got
    assert not any(k.startswith("cells.") and "combined" in k for k in got)


def test_usable_min_trades_is_the_studys_own_knob() -> None:
    """`usable.min_trades` above a cell's trade count gives it no p (it was read from the nulls' config)."""
    got = panel(cfg={**CFG, "usable": {"min_trades": 10_000}})
    assert got[got["role"] == "scaled"]["p"].isna().all()


def test_idle_months_count_as_zero_in_the_correlation() -> None:
    """Two cells identical for 6 months and both idle for 5 more (to the last close): rho is that of the 11-month frame."""
    months = pd.date_range("2024-01-15", periods=6, freq="MS") + pd.Timedelta(days=14)
    pl = np.array([5.0, -3.0, 8.0, 1.0, -6.0, 4.0])
    one = pd.DataFrame({"Close time": months, "Profit/Loss": pl})
    other = pd.DataFrame({"Close time": months, "Profit/Loss": pl * 2 + np.array([1, 0, 2, 0, 1, 0])})
    late = pd.DataFrame({"Close time": [pd.Timestamp("2024-12-20")], "Profit/Loss": [0.0]})
    plan = pd.DataFrame({"mother": ["A", "A"], "strategy": ["A", "B"], "block": [0, 0],
                         "timeframe": ["H1", "H4"], "role": ["baseline", "scaled"]})
    packed = pd.concat([one.assign(strategy="A", block=0), other.assign(strategy="B", block=0),
                        late.assign(strategy="C", block=0)], ignore_index=True)
    got = cells.correlations(plan, packed)["corr"].iloc[0]
    twelve = np.corrcoef(np.r_[pl, np.zeros(5)], np.r_[pl * 2 + np.array([1, 0, 2, 0, 1, 0]), np.zeros(5)])[0, 1]
    assert abs(got - twelve) < 1e-9, (got, twelve)


def test_a_sibling_that_lost_money_never_survives() -> None:
    """seen -0.01 with p 0.01 and z_new 2.5 (better than its random twins, still a loss): `fails`."""
    assert reading(2.5, 0.01, -0.01) == "fails"


if __name__ == "__main__":
    test_only_oos1_is_read_and_a_seed_replays_it()
    test_what_a_sibling_adds_and_what_the_mother_sums()
    test_the_reading()
    test_every_numeric_column_is_a_fact_of_the_mother()
    test_usable_min_trades_is_the_studys_own_knob()
    test_idle_months_count_as_zero_in_the_correlation()
    test_a_sibling_that_lost_money_never_survives()
    print("ok")
