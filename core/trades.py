"""Read a trade list exported by SQX's orderstocsv, and split it into one frame per market."""

from pathlib import Path

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
    return d.reset_index(drop=True)


def by_market(trades: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Split a `data=all` export into its per-market results.

    Args:
        trades: What read() returned.

    Returns:
        {SQX feed name: that market's trades}, in the order SQX wrote them, which puts the
        main result first and each AdditionalMarket after it. The ticket numbering restarts
        at 1 inside every block, so it is not a key across markets.
    """
    return {s: g.reset_index(drop=True) for s, g in trades.groupby("Symbol", sort=False)}


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
    direction = trades["Type"].map(SIDE)
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


def on_bar_open(trades: pd.DataFrame, opens: pd.Index) -> float:
    """Share of entries landing exactly on a bar open.

    Args:
        trades: One market's trades.
        opens: The bar open times of that market and timeframe.

    Returns:
        A fraction. Below 1 means some entries were pending orders filled inside a bar, which
        is a price-conditional selection a synthetic trade cannot reproduce: a market well
        below 1 has to be reported, not silently tested. Membership of the real bar index is
        the only test that works at every timeframe — an M30 bar opens on the half hour too.
    """
    return float(trades["Open time"].isin(opens).mean())
