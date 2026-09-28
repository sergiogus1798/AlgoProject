"""Trade arithmetic on one sample: starting capital, win rate with its Wilson interval, concentration, exits."""

import math

import pandas as pd

Z95 = 1.959964          # two-sided 95 % normal quantile
TOP = 0.05              # the share of best trades whose weight in the net P&L is measured


def capital(trades: pd.DataFrame) -> float | None:
    """The account the sample's backtest started with: the first balance before its trade.

    Args:
        trades: One sample's trades, ascending in close time.

    Returns:
        Rounded to the unit (the export's balances carry a few cents of float noise), or
        None for a sample without trades.
    """
    if trades.empty:
        return None
    first = trades.iloc[0]
    return float(round(first["Balance"] - first["Profit/Loss"]))


def wilson(wins: int, n: int) -> tuple[float, float, float]:
    """Win rate and its 95 % Wilson score interval.

    Args:
        wins: Trades with P&L > 0.
        n: Trades, > 0.

    Returns:
        (rate, low, high), all in %.
    """
    p = wins / n
    centre = (p + Z95 ** 2 / (2 * n)) / (1 + Z95 ** 2 / n)
    half = Z95 * math.sqrt(p * (1 - p) / n + Z95 ** 2 / (4 * n * n)) / (1 + Z95 ** 2 / n)
    return 100 * p, 100 * (centre - half), 100 * (centre + half)


def concentration(pnl: pd.Series) -> tuple[int, float, float | None]:
    """How much of the net P&L the best `TOP` of trades carry.

    Args:
        pnl: Every trade's P&L of one sample.

    Returns:
        (trades in the top slice — at least one —, their P&L, their share of the net in
        %, None when the net is not positive: a share of a loss has no reading).
    """
    k = max(1, math.ceil(TOP * len(pnl)))
    top = float(pnl.nlargest(k).sum())
    net = float(pnl.sum())
    return k, top, (100 * top / net if net > 0 else None)


def by_exit(trades: pd.DataFrame) -> pd.DataFrame:
    """One row per exit type as the export spells it, busiest first.

    Args:
        trades: One sample's trades.

    Returns:
        Columns: salida, ops (trades), neto, medio (P&L), % gan. (P&L > 0), MAE, MFE (means).
    """
    g = trades.groupby("Close type", sort=False)
    out = pd.DataFrame({
        "ops": g.size(), "neto": g["Profit/Loss"].sum().round(2),
        "medio": g["Profit/Loss"].mean(),
        "% gan.": 100 * g["Profit/Loss"].apply(lambda s: (s > 0).mean()),
        "MAE": g["MAE ($)"].mean(), "MFE": g["MFE ($)"].mean()})
    out = out.round(2).sort_values("ops", ascending=False, kind="stable")
    return out.rename_axis("salida").reset_index()


def exit_paths(trades: pd.DataFrame) -> tuple[list[str], dict[str, list[float]]]:
    """Cumulative P&L of each exit type along the sample's trades, one point per trade.

    Args:
        trades: One sample's trades, ascending in close time.

    Returns:
        (close days as "YYYY-MM-DD", one per trade, {exit type: its running sum at every trade}).
        A type stays flat across the other types' trades, so every line has every point.
    """
    x = trades["Close time"].dt.strftime("%Y-%m-%d").tolist()
    paths = {t: trades["Profit/Loss"].where(trades["Close type"] == t, 0.0).cumsum().round(2)
             .tolist() for t in trades["Close type"].unique()}
    return x, paths


# How one trade's return is counted (plan 24 §10: «USD por lote» by default). Per lot takes the
# position size out, so a sizing rule that grows with the account does not fatten the tails.
UNITS = {"USD por lote": lambda t: t["Profit/Loss"] / t["Size"],
         "USD por operación": lambda t: t["Profit/Loss"]}
PERCENTILES = (5, 25, 75, 95)


def returns(trades: pd.DataFrame, unit: str) -> pd.Series:
    """Every trade's return in one of `UNITS`.

    Args:
        trades: One sample's trades, with `Profit/Loss` and `Size` (lots).
        unit: A key of `UNITS`.

    Returns:
        One value per trade, in close-time order.
    """
    return UNITS[unit](trades).astype(float)


def shape(values: pd.Series) -> dict[str, float | None]:
    """The distribution of per-trade returns: centre, spread, tails, percentiles.

    Args:
        values: One return per trade.

    Returns:
        mean, median, standard deviation, skewness and excess kurtosis (pandas' bias-corrected
        estimators, 0 for a normal), and the `PERCENTILES`; None where the sample is too short
        (skew needs 3 trades, kurtosis 4).
    """
    n = len(values)
    out = {"media": float(values.mean()) if n else None,
           "mediana": float(values.median()) if n else None,
           "desviación típica": float(values.std()) if n > 1 else None,
           "asimetría": float(values.skew()) if n > 2 else None,
           "curtosis (exceso)": float(values.kurt()) if n > 3 else None}
    return out | {f"percentil {q}": float(values.quantile(q / 100)) if n else None
                  for q in PERCENTILES}
