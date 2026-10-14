#!/usr/bin/env python3
"""Known-answer test of a stopped trade's exit: its real minute inside the bar, and SQX's MAE/MFE with the exit fill in them."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from portfolio.common.construct.equity import excursions, stopexit  # noqa: E402

FAILURES = []


def check(name: str, ok: bool) -> None:
    """Print one line per case; remember the failures."""
    print(f"{'OK   ' if ok else 'FALLO'}  {name}")
    if not ok:
        FAILURES.append(name)


def main() -> None:
    """Two hours of flat M1 at 100 with one dip to 90 at 01:17 and a gap up to 105 at 01:30."""
    index = pd.date_range("2024-01-02 00:00", periods=120, freq="min")
    bars = pd.DataFrame(
        {"Open": 100.0, "High": 100.5, "Low": 99.5, "Close": 100.0}, index=index
    )
    bars.loc["2024-01-02 01:17", "Low"] = 90.0
    bars.loc["2024-01-02 01:30":, ["Open", "High", "Low", "Close"]] = [
        105.0,
        105.5,
        104.5,
        105.0,
    ]
    stamp = pd.Timestamp("2024-01-02 01:00")
    trades = pd.DataFrame(
        {
            "Type": ["Buy", "Buy", "Buy", "Buy"],
            "Open time": pd.Timestamp("2024-01-02 00:00"),
            "Open price": 100.0,
            "Size": 1.0,
            "Close time": [stamp, stamp, pd.Timestamp("2024-01-02 01:30"), stamp],
            "Close price": [
                92.0,
                80.0,
                104.0,
                100.0,
            ],  # reached at 01:17 · beyond every wick · a gap exit
            "Close type": ["SL", "SL", "Exit Signal", "Exit Signal"],
        }
    )

    moved = stopexit.retime(trades, bars, "M30")["Close time"]
    check(
        "a stop moves to the first minute whose wick reaches its price",
        moved[0] == pd.Timestamp("2024-01-02 01:17"),
    )
    check(
        "a stop slipped beyond every wick moves to the bar's most adverse minute",
        moved[1] == pd.Timestamp("2024-01-02 01:17"),
    )
    check(
        "any other exit keeps its stamp",
        moved[2] == trades["Close time"][2] and moved[3] == stamp,
    )
    late = bars.copy()
    late.loc["2024-01-02 01:45", "Low"] = 85.0
    check(
        "with an H1 bar the same stamp looks 60 minutes on",
        stopexit.retime(trades.assign(**{"Close price": 88.0}), late, "H1")[
            "Close time"
        ][0]
        == pd.Timestamp("2024-01-02 01:45"),
    )

    timed = stopexit.retime(trades, bars, "M30")
    got = stopexit.fills(excursions.rebuild(timed, bars, 2.0), timed, bars, 2.0)
    check(
        "a stopped trade's MAE is its move to its own fill",
        np.allclose(got["mae"][:2], [-16.0, -40.0]),
    )
    check(
        "a stopped trade's MFE stays the wicks'",
        np.allclose(got["mfe"][:2], [1.0, 1.0]),
    )
    check(
        "a gap exit's MFE reaches the exit minute's open, before slippage",
        np.isclose(got["mfe"][2], 10.0),
    )
    check(
        "an exit inside the range changes nothing",
        np.isclose(got["mae"][3], -1.0) and np.isclose(got["mfe"][3], 1.0),
    )
    sys.exit(1 if FAILURES else 0)


if __name__ == "__main__":
    main()
