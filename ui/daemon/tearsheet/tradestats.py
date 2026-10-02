"""Trade arithmetic on one sample: starting capital, exits, and the per-trade return and its shape."""

import pandas as pd


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


# How one trade's return is counted (default «USD por operación», owner 2026-09-30 — `ui.daemon.
# strategy.stats.DEFAULT_UNIT`). Per lot takes the position size out, so a sizing rule that grows
# with the account does not fatten the tails; it stays selectable, just not the default any more.
UNITS = {"USD por lote": lambda t: t["Profit/Loss"] / t["Size"],
         "USD por operación": lambda t: t["Profit/Loss"]}
SHORT = {"USD por lote": "$/lote", "USD por operación": "$/trade"}    # owner: «65.36 $/trade»


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
    """The distribution of per-trade returns: centre, spread and tails.

    Args:
        values: One return per trade.

    Returns:
        mean, standard deviation, skewness and excess kurtosis (pandas' bias-corrected
        estimators, 0 for a normal); None where the sample is too short (skew needs 3 trades,
        kurtosis 4). The median and the percentiles are the histogram's row, not repeated here.
    """
    n = len(values)
    return {"media": float(values.mean()) if n else None,
            "desviación típica": float(values.std()) if n > 1 else None,
            "asimetría": float(values.skew()) if n > 2 else None,
            "curtosis (exceso)": float(values.kurt()) if n > 3 else None}
