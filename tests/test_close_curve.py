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
BARS = pd.DataFrame(
    {"High": 1.10, "Low": 1.00, "Close": 1.05},
    index=pd.date_range(D1, periods=3 * 1440, freq="1min"),
)
BARS.loc[BARS.index >= D2, "Close"] = 1.06
BARS.loc[BARS.index >= D3, "Close"] = 1.04
# A: long 2 lots, 1.05 -> 1.07 over one night. Commission 10, Profit/Loss = 0.02*2*1000 - 10 = 30.
#    Day 1: worst wick (1.00-1.05)*2000 - 10 = -110, close (1.05-1.05)*2000 - 10 = -10.
#    Day 2: the same -110 before the exit, then 30 booked: the day earns 30 - (-10) = 40.
# B: short 1 lot twice, both inside one day. Day 2: 1.05 -> 1.03, P/L 20 - 5 = 15, worst wick
#    (1.05-1.10)*1000 - 5 = -55. Day 3: 1.05 -> 1.06, P/L -10 - 5 = -15, worst 15 - 55 = -40.
TRADES = pd.DataFrame(
    {
        "identity": ["A", "B", "B"],
        "Type": ["Buy", "Sell", "Sell"],
        "Size": [2.0, 1.0, 1.0],
        "Open time": [
            D1 + pd.Timedelta(hours=10),
            D2 + pd.Timedelta(hours=9),
            D3 + pd.Timedelta(hours=9),
        ],
        "Close time": [
            D2 + pd.Timedelta(hours=12),
            D2 + pd.Timedelta(hours=15),
            D3 + pd.Timedelta(hours=15),
        ],
        "Open price": [1.05, 1.05, 1.05],
        "Close price": [1.07, 1.03, 1.06],
        "Profit/Loss": [30.0, 15.0, -15.0],
        "sample": "OOS",
    }
)
PROFIT = pd.DataFrame(
    {"A": [-10.0, 40.0, 0.0], "B": [0.0, 15.0, -15.0]}, index=[D1, D2, D3]
)
LOW = pd.DataFrame(
    {"A": [-110.0, -110.0, 30.0], "B": [0.0, -55.0, -40.0]}, index=[D1, D2, D3]
)


def batch(folder: Path, mother: str, with_trades: bool) -> Path:
    """One mother's variant batch: the origin's daily increments of SQX's curve, and its trades."""
    folder.mkdir()
    pd.DataFrame(
        {"variant_id": ["P00000", "P00001"], "origin": [True, False]}
    ).to_parquet(folder / "manifest.parquet")
    LOW[[mother]].diff().fillna(LOW[[mother]]).set_axis(["P00000"], axis=1).to_parquet(
        folder / "equity.parquet"
    )
    if with_trades:
        TRADES[TRADES["identity"] == mother].drop(columns="identity").assign(
            variant_id="P00000"
        ).to_parquet(folder / joint.TRADES)
    return folder


def tolerance_failures() -> list[str]:
    """Half a tick x lots open is licensed; a full tick is not."""
    # Prices exported with 2 decimals, point value 100, 3 lots open on D2: half a tick is
    # 0.5 x 0.01 x 100 x 3 = 1.5 per day; 1.4 passes, a full tick (3.0) still fails.
    held = pd.DataFrame(
        {
            "Open price": [100.25, 100.5],
            "Close price": [100.75, 101.0],
            "Size": [3.0, 3.0],
            "Open time": [D2 + pd.Timedelta(hours=1)] * 2,
            "Close time": [D2 + pd.Timedelta(hours=2)] * 2,
        }
    ).iloc[:1]
    allowed = joint.tolerance(held, pd.Index([D1, D2, D3]), 100.0)
    if not np.allclose(allowed, [1.0, 1.5, 1.0]) or not (1.4 <= allowed[D2] < 3.0):
        return [f"tolerancia por lotes abiertos: {allowed.tolist()}"]
    # USDJPY M30 gorilla: 2.89 + 2.87 − 2.89 − 2.87 leaves −4e-16 lots, which left a NaN bound
    t1, t2 = D1 + pd.Timedelta(hours=4), D1 + pd.Timedelta(hours=14)
    drift = pd.DataFrame(
        {
            "Open price": [100.25, 100.5],
            "Close price": [100.75, 101.0],
            "Size": [2.89, 2.87],
            "Open time": [t1, t2],
            "Close time": [t2, D2 + pd.Timedelta(minutes=30)],
        }
    )
    allowed = joint.tolerance(drift, pd.Index([D1, D2, D3]), 100.0)
    if allowed.isna().any():
        return [f"tolerancia con deriva de coma flotante: {allowed.tolist()}"]

    return []


def swap_failures() -> list[str]:
    """`measured` against same-day trades carrying a rollover swap, small and large."""
    failures: list[str] = []
    rng = np.random.default_rng(0)
    move = rng.uniform(-5, 5, 60)
    swapped = pd.DataFrame(
        {
            "Type": "Buy",
            "Open time": pd.Timestamp("2020-01-02 01:00"),
            "Close time": pd.Timestamp("2020-01-02 09:00"),
            "Open price": 100.0,
            "Close price": 100.0 + move,
            "Size": 1.0,
            "Profit/Loss": VALUE * move - PER_LOT,
        }
    )
    swapped.loc[:2, "Profit/Loss"] -= (
        40.0  # a rollover inside the day: swap, not commission
    )
    value2, commission2 = closecurve.measured(swapped)
    if not np.isclose(value2, VALUE) or not np.isclose(commission2["value"], PER_LOT):
        failures.append(f"el swap arrastra el ajuste: {value2} {commission2}")
    swapped.loc[:5, "Profit/Loss"] -= (
        600.0  # XAUUSD M15: swaps big enough to bias every residual past 0.5
    )
    value3, commission3 = closecurve.measured(swapped)
    if not np.isclose(value3, VALUE) or not np.isclose(commission3["value"], PER_LOT):
        failures.append(f"swaps grandes vacían el recorte: {value3} {commission3}")
    return failures


def main() -> None:
    """Run every check and exit non-zero on any failure."""
    failures = []
    a = TRADES[TRADES["identity"] == "A"]

    table = days.server_days(
        paths.minute_path(
            a,
            BARS,
            VALUE,
            paths.entry_commission(a, {"method": "SizeBased", "value": PER_LOT}, VALUE),
        ),
        "UTC",
        "UTC",
    )
    if not np.allclose(
        reconcile.low_equity(table), [-110.0, -110.0]
    ) or not np.allclose(days.daily_pnl(table), [-10.0, 40.0]):
        failures.append(
            f"comisión desde la entrada: {reconcile.low_equity(table).tolist()} "
            f"{days.daily_pnl(table).tolist()}"
        )
    bare = days.server_days(paths.minute_path(a, BARS, VALUE), "UTC", "UTC")
    if not np.allclose(reconcile.low_equity(bare), [-100.0, -100.0]) or not np.isclose(
        days.daily_pnl(bare).sum(), 30.0
    ):
        failures.append(
            "sin comisión: el mínimo no es el de la mecha sola, o los días no suman"
        )
    pct = paths.entry_commission(a, {"method": "PercentageBased", "value": 0.5}, VALUE)
    if not np.allclose(pct, 0.005 * 1.05 * VALUE * 2.0):
        failures.append(f"comisión en porcentaje: {pct}")

    value, commission = closecurve.measured(TRADES)
    if not np.isclose(value, VALUE) or not np.isclose(commission["value"], PER_LOT):
        failures.append(f"medido de las operaciones: {value} {commission}")
    failures += swap_failures()
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
            failures.append(
                "blindJoint no se niega cuando al lote le faltan las operaciones"
            )

    failures += tolerance_failures()

    for line in failures:
        print("FALLA:", line)
    print("ok" if not failures else f"{len(failures)} fallos")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
