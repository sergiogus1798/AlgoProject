#!/usr/bin/env python3
"""Golden of the M1 rebuild on the CURRENT feed: one USDJPY_M1 strategy against SQX's daily curve."""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import assetdata, barstore  # noqa: E402
from core.paths import harvest_dir  # noqa: E402
from portfolio.common.construct.equity import (
    closecurve,
    days,
    excursions,
    paths,
    reconcile,
    sqxcurve,
)  # noqa: E402

# One strategy of the population that reconciles at 99.9 % (3,729 of 3,732, 2026-10-04), built on
# `USDJPY_M1` in EETUS after the feeds were unified. `trades.parquet` holds build and oos1 only:
# the harvest's `oos2_*` files are never opened.
HARVEST = harvest_dir("Test_Calib_USDJPY_H1_momentumL", "Results", "2026-10-02")
IDENTITY = "000eafdf6b0809552389ebc4d4b636a16a0ee5b843b7cfa7a09338f945df06dc"
SYMBOL, FEED, CLOCK = "USDJPY", "USDJPY_M1", "EETUS"


def _low(
    trades: pd.DataFrame, bars: pd.DataFrame, value: float, cost: object
) -> tuple[pd.Series, float]:
    """One leg's rebuilt daily lowest equity, and how far its days are from summing to its trades."""
    table = days.server_days(paths.minute_path(trades, bars, value, cost), CLOCK, CLOCK)
    return reconcile.low_equity(table), abs(
        days.daily_pnl(table).sum() - trades["Profit/Loss"].sum()
    )


def check_golden() -> None:
    """Both legs within 1 $ of SQX's curve on ≥ 99 % of days with the card's commission charged
    from the entry (as `equity/universe.py::_commission`), and NOT without it; MAE/MFE licensed."""
    if not HARVEST.exists():
        print(
            "skip: the harvest of Test_Calib_USDJPY_H1_momentumL is not on this machine"
        )
        return
    only = [("identity", "==", IDENTITY)]
    trades = pd.read_parquet(HARVEST / "trades.parquet", filters=only)
    sqx = sqxcurve.from_harvest(
        pd.read_parquet(HARVEST / "equity.parquet", filters=only), SYMBOL
    )
    bars = barstore.source(FEED, ["High", "Low", "Close"])
    card = assetdata.load(SYMBOL)["costs"]["commission"]["use"]
    value, _ = closecurve.measured(trades)

    for sample, segment in sqxcurve.SAMPLE_TO_SEGMENT.items():
        leg = trades[trades["sample"] == sample]
        ref = sqx.loc[sqx["segment"] == segment, "low"]
        low, gap = _low(
            leg, bars, value, paths.entry_commission(leg, card[segment], value)
        )
        got = reconcile.curve(low, ref, 1.0, 0.99)
        bare = reconcile.curve(_low(leg, bars, value, 0.0)[0], ref, 1.0, 0.99)
        assert gap < 1e-6, f"{segment}: Σ daily != Σ Profit/Loss, gap={gap}"
        assert got["verdict"] == "ok", (
            f"{segment}: rebuild misses SQX's daily low {got}"
        )
        assert bare["verdict"] == "out", (
            f"{segment}: the rebuild matches with no commission {bare}"
        )
        print(
            f"ok: {segment} — {got['n_days']} days, exact {got['exact']:.4f}, max gap "
            f"{got['max_gap']:.2f} $; without the commission {bare['exact']:.4f}"
        )

    lic = excursions.licence(
        trades, excursions.rebuild(trades, bars, value), tolerance=1.0, min_share=0.99
    )
    assert lic["licensed"], f"MAE/MFE licence refused {lic}"
    print(
        f"ok: MAE/MFE — n={lic['n']} mae_exact={lic['mae_exact']:.3f} mfe_exact={lic['mfe_exact']:.3f}"
    )


def main() -> None:
    """Run the check; a failure raises and exits non-zero."""
    check_golden()
    print("ok")


if __name__ == "__main__":
    main()
