"""Step 14's T1 measure: excess per neighbour and window on a market whose drift is known, and its facts."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from pipeline.autopilot.facts import flatten
from studies.breakage.mcRetest.neighbours import excess, t1

# Hourly opens 100 + S·j + A·(j odd), in a constant range of 20: the ATR is flat, so a blind
# trade held h bars earns S·h on average in any year, and the drift term is exactly that. A long
# entered on an even bar and held an odd number of bars earns A on top (excess +A·lots);
# entered on an odd bar, A less (excess −A·lots); held an even number of bars, nothing.
S, A = 0.01, 1.0
COSTS = {"point_value": 1.0, "tick_size": 0.01, "spread": 0.0, "slippage": 0.0,
         "commission_method": "SizeBased", "commission": 0.0, "swap_long": 0.0,
         "swap_short": 0.0, "triple": 2, "rollover": 0}
DRIFT = {"window": "year", "variant": "d"}
SPANS = {"build": ("2019-01-01", "2019-12-31"), "oos1": ("2020-01-01", "2020-12-31")}
GOOD, BAD, FLAT = (0, 1), (1, 1), (0, 2)        # (bar parity at entry, bars held)
# variant -> window -> its trades. Excess: mother 4 and 2; N1 2 and 1; N2 −1 and 3.
TRADES = {"M000N0000": {"build": [GOOD] * 4, "oos1": [GOOD] * 2},
          "M000N0001": {"build": [GOOD] * 3 + [BAD], "oos1": [GOOD, FLAT]},
          "M000N0002": {"build": [BAD, FLAT], "oos1": [GOOD] * 3}}


def bars() -> pd.DataFrame:
    """The market above, from December 2018 (the ATR's warm-up) to January 2021."""
    index = pd.date_range("2018-12-01", "2021-01-31 23:00", freq="h")
    opened = 100 + S * np.arange(len(index)) + A * (np.arange(len(index)) % 2)
    return pd.DataFrame({"Open": opened, "High": opened + 10, "Low": opened - 10,
                         "Close": opened}, index=index)


def trades(market: pd.DataFrame, window: str) -> pd.DataFrame:
    """Every variant's trades of one window, spread over its year, as an export carries them."""
    first = market.index.get_loc(pd.Timestamp(SPANS[window][0]))
    first += first % 2                                  # an even bar
    rows = []
    for variant, held in TRADES.items():
        for k, (parity, hold) in enumerate(held[window]):
            at = first + 500 * (k + 1) + parity
            rows.append({"variant_id": variant, "Type": "Buy", "Size": 1.0,
                         "Open time": market.index[at], "Close time": market.index[at + hold]})
    return pd.DataFrame(rows)


def table() -> pd.DataFrame:
    """The per-neighbour table as `t1.measure` assembles it from the two windows' totals."""
    market = bars()
    out = pd.DataFrame({"variant_id": list(TRADES), "strategy": "Strategy 1.2.3",
                        "neighbour": [0, 1, 2]})
    for window, span in SPANS.items():
        got = excess.totals(trades(market, window), market, COSTS, span, DRIFT)
        out = out.merge(got.add_prefix(f"{window}_"), left_on="variant_id", right_index=True)
    return out


def test_excess_is_profit_minus_the_years_drift() -> None:
    """Each variant's totals are the hand count: ±A per odd-hold trade, S per bar of drift."""
    got = table().set_index("variant_id")
    assert got["build_excess"].round(9).tolist() == [4.0, 2.0, -1.0]
    assert got["oos1_excess"].round(9).tolist() == [2.0, 1.0, 3.0]
    assert got["build_drift"].round(9).tolist() == [4 * S, 4 * S, 3 * S]
    assert got["build_profit"].round(9).tolist() == [4 + 4 * S, 2 + 4 * S, -1 + 3 * S]
    assert got["build_trades"].tolist() == [4, 4, 2]


def test_facts_are_the_retention_of_the_excess(tmp_path: Path,
                                               monkeypatch: pytest.MonkeyPatch) -> None:
    """ret_med, f_pos, ret_benef, beta_share and rho_vec by hand; None without a batch."""
    monkeypatch.setattr(t1, "export_dir",
                        lambda project, databank, day, batch="": tmp_path / project / databank / day)
    stored = tmp_path / "P" / t1.STORE / "2026-10-06" / t1.FILE
    stored.parent.mkdir(parents=True)
    table().to_parquet(stored, index=False)

    got = t1.facts("P", "2026-10-07", "1.2.3")       # measured the day before, short spelling
    assert got["t1.build.ret_med"] == pytest.approx(0.5 / 4)        # median of 2 and −1, over 4
    assert got["t1.build.f_pos"] == 0.5 and got["t1.build.n"] == 2
    assert got["t1.build.ret_p5"] == pytest.approx((-1 + 0.05 * 3) / 4)
    assert got["t1.build.ret_benef"] == pytest.approx((0.5 + 3.5 * S) / (4 + 4 * S))
    assert got["t1.build.beta_share"] == pytest.approx(4 * S / (4 + 4 * S))
    assert got["t1.oos1.ret_med"] == pytest.approx(2 / 2) and got["t1.oos1.f_pos"] == 1.0
    assert got["t1.rho_vec"] == pytest.approx(-1.0)      # the better on build, the worse on oos1
    assert len(got) == 13 and len(t1.table("P", "2026-10-07", "Strategy 1.2.3")) == 3

    assert t1.facts("P", "2026-10-07", "Strategy 7.7.7") is None     # not in the batch
    assert t1.facts("P", "2026-10-05", "1.2.3") is None              # before it was measured
    assert t1.facts("Other", "2026-10-07", "1.2.3") is None          # no batch at all
    keys = dict(flatten({"summary": got}))               # how facts.py would name a summary of it
    assert keys["summary.t1_build_ret_med"] == got["t1.build.ret_med"]


def test_a_mother_without_excess_has_no_retention() -> None:
    """Original excess at or below zero: the retentions are NaN (the judge's limbo), f_pos stays."""
    rows = table()
    rows.loc[rows["neighbour"] == 0, "build_excess"] = 0.0
    got = t1.summary(rows)
    assert np.isnan(got["t1.build.ret_med"]) and got["t1.build.f_pos"] == 0.5
