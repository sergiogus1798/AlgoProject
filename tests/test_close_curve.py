#!/usr/bin/env python3
"""The close-to-close rebuild on a hand-computed case: commission from the entry, and the joint study's panel."""

import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from portfolio.common.construct.equity import closecurve, days, paths, reconcile  # noqa: E402
from studies.closing.blindJoint import inputs as joint  # noqa: E402

VALUE, PER_LOT = 1000.0, 5.0
D1, D2, D3 = (pd.Timestamp(d) for d in ("2024-01-02", "2024-01-03", "2024-01-04"))
SPAN = (D1, D3 + pd.Timedelta(days=1))
# Three days of M1 bars: High 1.10 and Low 1.00 every minute; the close is 1.05, 1.06, 1.04.
BARS = pd.DataFrame({"High": 1.10, "Low": 1.00, "Close": 1.05},
                    index=pd.date_range(D1, periods=3 * 1440, freq="1min"))
BARS.loc[BARS.index >= D2, "Close"] = 1.06
BARS.loc[BARS.index >= D3, "Close"] = 1.04
# A: long 2 lots, 1.05 -> 1.07 over one night. Commission 10, Profit/Loss = 0.02*2*1000 - 10 = 30.
#    Day 1: worst wick (1.00-1.05)*2000 - 10 = -110, close (1.05-1.05)*2000 - 10 = -10.
#    Day 2: the same -110 before the exit, then 30 booked: the day earns 30 - (-10) = 40.
# B: short 1 lot twice, both inside one day. Day 2: 1.05 -> 1.03, P/L 20 - 5 = 15, worst wick
#    (1.05-1.10)*1000 - 5 = -55. Day 3: 1.05 -> 1.06, P/L -10 - 5 = -15, worst 15 - 55 = -40.
TRADES = pd.DataFrame({
    "identity": ["A", "B", "B"], "Type": ["Buy", "Sell", "Sell"], "Size": [2.0, 1.0, 1.0],
    "Open time": [D1 + pd.Timedelta(hours=10), D2 + pd.Timedelta(hours=9), D3 + pd.Timedelta(hours=9)],
    "Close time": [D2 + pd.Timedelta(hours=12), D2 + pd.Timedelta(hours=15), D3 + pd.Timedelta(hours=15)],
    "Open price": [1.05, 1.05, 1.05], "Close price": [1.07, 1.03, 1.06],
    "Profit/Loss": [30.0, 15.0, -15.0], "sample": "OOS"})
PROFIT = pd.DataFrame({"A": [-10.0, 40.0, 0.0], "B": [0.0, 15.0, -15.0]}, index=[D1, D2, D3])
LOW = pd.DataFrame({"A": [-110.0, -110.0, 30.0], "B": [0.0, -55.0, -40.0]}, index=[D1, D2, D3])


def batch(folder: Path, mother: str, with_trades: bool) -> Path:
    """One mother's variant batch: the origin's daily increments of SQX's curve, and its trades."""
    folder.mkdir()
    pd.DataFrame({"variant_id": ["P00000", "P00001"], "origin": [True, False]}) \
        .to_parquet(folder / "manifest.parquet")
    LOW[[mother]].diff().fillna(LOW[[mother]]).set_axis(["P00000"], axis=1) \
        .to_parquet(folder / "equity.parquet")
    if with_trades:
        TRADES[TRADES["identity"] == mother].drop(columns="identity") \
            .assign(variant_id="P00000").to_parquet(folder / joint.TRADES)
    return folder


def main() -> None:
    """Run every check and exit non-zero on any failure."""
    failures = []
    a = TRADES[TRADES["identity"] == "A"]

    table = days.server_days(paths.minute_path(a, BARS, VALUE, paths.entry_commission(
        a, {"method": "SizeBased", "value": PER_LOT}, VALUE)), "UTC", "UTC")
    if not np.allclose(reconcile.low_equity(table), [-110.0, -110.0]) \
            or not np.allclose(days.daily_pnl(table), [-10.0, 40.0]):
        failures.append(f"comisión desde la entrada: {reconcile.low_equity(table).tolist()} "
                        f"{days.daily_pnl(table).tolist()}")
    bare = days.server_days(paths.minute_path(a, BARS, VALUE), "UTC", "UTC")
    if not np.allclose(reconcile.low_equity(bare), [-100.0, -100.0]) \
            or not np.isclose(days.daily_pnl(bare).sum(), 30.0):
        failures.append("sin comisión: el mínimo no es el de la mecha sola, o los días no suman")
    pct = paths.entry_commission(a, {"method": "PercentageBased", "value": 0.5}, VALUE)
    if not np.allclose(pct, 0.005 * 1.05 * VALUE * 2.0):
        failures.append(f"comisión en porcentaje: {pct}")

    value, commission = closecurve.measured(TRADES)
    if not np.isclose(value, VALUE) or not np.isclose(commission["value"], PER_LOT):
        failures.append(f"medido de las operaciones: {value} {commission}")
    profit, low = closecurve.panel(TRADES, BARS, value, commission)
    if not np.allclose(profit, PROFIT) or not np.allclose(low.fillna(LOW), LOW):
        failures.append(f"panel:\n{profit}\n{low}")

    joint.read_bars = lambda feed, columns: BARS[columns]
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        batches = {"A": batch(tmp / "a", "A", True), "B": batch(tmp / "b", "B", True)}
        got = joint.panel(batches, SPAN, "X_M1")
        if not np.allclose(got, PROFIT) or joint.trades_door(batches) is not None:
            failures.append(f"blindJoint:\n{got}")
        batches["B"] = batch(tmp / "c", "B", False)
        if "B" not in (joint.trades_door(batches) or ""):
            failures.append("blindJoint no se niega cuando al lote le faltan las operaciones")

    for line in failures:
        print("FALLA:", line)
    print("ok" if not failures else f"{len(failures)} fallos")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
