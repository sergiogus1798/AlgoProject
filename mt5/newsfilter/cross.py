"""Cross the two calendar histories: Forex Factory's red folder against MT5's HIGH releases, minute by minute."""

import argparse
import json
from typing import Any

import numpy as np
import pandas as pd

from mt5.newsfilter import forexfactory, history

OUT = history.CAL / "cross.json"
LONELY = history.CAL / "cross_unmatched.parquet"
CURRENCIES = ["USD", "EUR", "GBP", "JPY", "AUD", "NZD", "CAD", "CHF", "CNY"]
NEAR = pd.Timedelta(minutes=15)  # same release, a different minute
CLASSES = ["same_minute_high", "same_minute_lower", "near_high", "hour_off", "alone"]


def moments(rows: pd.DataFrame) -> pd.DataFrame:
    """One row per (currency, minute): several figures of one release are one moment to a filter."""
    return rows.groupby(["currency", "utc"], as_index=False).agg(
        what=("what", " | ".join)
    )  # pyright: ignore[reportReturnType]  # pandas/numpy stubs lose the type through indexing


def nearest_gap(times: np.ndarray, other: np.ndarray) -> np.ndarray:
    """For each time, the signed gap in minutes to the nearest of `other` (sorted); NaN if none."""
    if not len(other):
        return np.full(len(times), np.nan)
    at = (
        np.searchsorted(other, times).clip(1, len(other) - 1)
        if len(other) > 1
        else np.zeros(len(times), int)
    )
    left, right = other[np.maximum(at - 1, 0)], other[at]
    pick = np.where(np.abs(times - left) <= np.abs(right - times), left, right)
    return (pick - times) / np.timedelta64(1, "m")


def classify(
    mine: pd.DataFrame, high: pd.DataFrame, anyrank: pd.DataFrame
) -> pd.Series:
    """Where each moment of `mine` stands in the other calendar.

    Args:
        mine: Moments of one calendar (currency, utc).
        high: The other calendar's top-rated moments.
        anyrank: The other calendar's moments at any rating.

    Returns:
        One of CLASSES per row: the other side has a top-rated release that same minute; has
        one rated lower that minute; has a top-rated one within NEAR; has one exactly an hour
        away (a clock disagreement, not a rating one); or nothing.
    """
    out = pd.Series("alone", index=mine.index)
    for cur, rows in mine.groupby("currency"):
        t = rows["utc"].to_numpy()
        gap_high = nearest_gap(
            t, high.loc[high["currency"] == cur, "utc"].sort_values().to_numpy()
        )
        gap_any = nearest_gap(
            t, anyrank.loc[anyrank["currency"] == cur, "utc"].sort_values().to_numpy()
        )
        label = np.select(
            [
                gap_high == 0,
                gap_any == 0,
                np.abs(gap_high) <= NEAR / pd.Timedelta(minutes=1),  # pyright: ignore[reportOperatorIssue]  # pandas stubs: Timedelta/Timestamp unions with NaT
                np.abs(gap_high) == 60,
            ],
            CLASSES[:4],
            "alone",
        )
        out.loc[rows.index] = label
    return out


def cross(first_year: int) -> dict[str, Any]:
    """Count both directions over the span the two histories share, up to today.

    Returns:
        {"span", "ff_red": {class: n}, "mt5_high": {class: n}, "by_year": ...}; the moments
        that found no top-rated twin in the same minute go to cross_unmatched.parquet.
    """
    mt5 = history.load()
    mt5 = mt5[
        (mt5["time_mode"] != "Event takes all day") & mt5["currency"].isin(CURRENCIES)
    ]
    ff = forexfactory.load()
    ff = ff[ff["currency"].isin(CURRENCIES)]
    start = max(
        mt5["utc"].min(), ff["utc"].min(), pd.Timestamp(year=first_year, month=1, day=1)
    )
    end = min(
        pd.Timestamp.now(tz="UTC").tz_localize(None), mt5["utc"].max(), ff["utc"].max()
    )
    mt5 = mt5[mt5["utc"].between(start, end)].assign(  # pyright: ignore[reportAttributeAccessIssue]  # pandas/numpy stubs lose the type through indexing
        what=lambda d: d["country"] + ":" + d["code"]
    )
    ff = ff[ff["utc"].between(start, end)].assign(what=lambda d: d["event"])  # pyright: ignore[reportAttributeAccessIssue]  # pandas/numpy stubs lose the type through indexing
    red, ff_all = moments(ff[ff["impact"] == "High"]), moments(ff)  # pyright: ignore[reportArgumentType]  # pandas/numpy stubs lose the type through indexing
    high, mt5_all = moments(mt5[mt5["importance"] == 3]), moments(mt5)  # pyright: ignore[reportArgumentType]  # pandas/numpy stubs lose the type through indexing
    red["class"] = classify(red, high, mt5_all)
    high["class"] = classify(high, red, ff_all)
    lonely = pd.concat([red.assign(side="ff_red"), high.assign(side="mt5_high")])
    lonely[lonely["class"] != "same_minute_high"].to_parquet(LONELY)
    count = lambda d: {c: int((d["class"] == c).sum()) for c in CLASSES}  # noqa: E731
    by_year = {
        str(y): {
            "ff_red": count(red[red["utc"].dt.year == y]),
            "mt5_high": count(high[high["utc"].dt.year == y]),
        }
        for y in range(start.year, end.year + 1)
    }
    out = {
        "span": [str(start), str(end)],
        "ff_red": {"moments": len(red), **count(red)},
        "mt5_high": {"moments": len(high), **count(high)},
        "by_year": by_year,
    }
    OUT.write_text(json.dumps(out, indent=1))
    return out


def main() -> None:
    """CLI: python3 -m mt5.newsfilter.cross [--from YEAR]."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--from",
        dest="first",
        type=int,
        default=history.FIRST_YEAR,
        help="primer año del cruce; por defecto todo lo que compartan las dos fuentes",
    )
    got = cross(ap.parse_args().first)
    names = {
        "same_minute_high": "mismo minuto, también máxima",
        "same_minute_lower": "mismo minuto, la otra la puntúa menos",
        "near_high": "a 15 min o menos",
        "hour_off": "a una hora exacta (reloj)",
        "alone": "sin pareja",
    }
    print(f"cruce de {got['span'][0]} a {got['span'][1]} UTC  ->  {OUT}")
    for side, label in (
        ("ff_red", "Carpeta roja de Forex Factory, vista desde MT5"),
        ("mt5_high", "Importancia alta de MT5, vista desde Forex Factory"),
    ):
        n = got[side]["moments"]
        print(f"{label}: {n} momentos (divisa + minuto)")
        for c in CLASSES:
            print(f"  {names[c]:<40} {got[side][c]:>6}  {got[side][c] / n:6.1%}")


if __name__ == "__main__":
    main()
