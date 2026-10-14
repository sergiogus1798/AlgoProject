"""Read a trade list exported by SQX's orderstocsv, and the per-trade quantities derived from it."""

from pathlib import Path
from typing import cast

import pandas as pd

TIME = "%Y.%m.%d %H:%M:%S"
SIDE = {"Buy": 1.0, "Sell": -1.0}


def read(path: Path) -> pd.DataFrame:
    """One strategy's exported trades, times parsed and unfilled orders dropped.

    Args:
        path: A CSV written by `-tools action=orderstocsv`. Semicolon separated, 16 columns.

    Returns:
        The same columns, with `Open time` and `Close time` as datetimes. The last row can be
        an unfilled pending order (`Close type=EndTest`, blank close price); it is dropped.
    """
    d = pd.read_csv(path, sep=";")
    d = d[d["Close price"].notna()].copy()
    d["Open time"] = pd.to_datetime(d["Open time"], format=TIME)
    d["Close time"] = pd.to_datetime(d["Close time"], format=TIME)
    return cast(pd.DataFrame, d.reset_index(drop=True))


def cost(trades: pd.DataFrame, point_value: float) -> pd.Series:
    """What SQX actually charged per trade, recovered rather than assumed.

    Args:
        trades: One market's trades.
        point_value: Account currency per 1.0 of price per 1.0 lot, from the asset's file.

    Returns:
        Account currency per trade. Gross minus the reported P/L: on XAUUSD this measures a
        steady $8 per lot per side. Spread is already inside the fill prices and does not
        appear here; overnight trades carry swap on top.
    """
    # astype first: mapping a categorical returns a categorical, which will not multiply.
    direction = trades["Type"].astype("object").map(SIDE)  # pyright: ignore[reportArgumentType] -- pandas stubs reject a dict for map; it is a valid Mapping
    move = trades["Close price"] - trades["Open price"]
    return direction * move * trades["Size"] * point_value - trades["Profit/Loss"]


def excursions(trades: pd.DataFrame, point_value: float) -> pd.DataFrame:
    """MAE and MFE converted from account currency to price.

    Args:
        trades: One market's trades.
        point_value: As for cost().

    Returns:
        Columns mae and mfe, in price. Size varies per trade under risk-based sizing, so the
        conversion uses each trade's own size and a fixed divisor would be wrong.
    """
    scale = trades["Size"] * point_value
    return pd.DataFrame({"mae": trades["MAE ($)"].abs() / scale,
                         "mfe": trades["MFE ($)"].abs() / scale})

