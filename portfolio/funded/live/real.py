"""The real trades of one strategy, from the fleet's history, a CSV override, and their R."""
from pathlib import Path
from typing import cast

import pandas as pd

from core.paths import MT5_ACCOUNTS, MT5_DATA
from mt5 import compare
from mt5.fleet.app import history
from mt5.reconcile import live, register


def from_fleet(strategy: str, firm: str) -> tuple[pd.DataFrame, Path, str]:
    """The closed trades of a strategy on a firm's account, by the magic the live register gives it.

    Args:
        strategy: Its name in the register (`AlgoData/mt5/reconcile/register.csv`).
        firm: The register's and `mt5_accounts`' key.

    Returns:
        (trades in the project's trade frame, the strategy's .sqx, its timeframe). Stops when
        the collector has no history for the account.
    """
    rows = register.read(MT5_DATA / "reconcile" / "register.csv")
    mine = cast(pd.DataFrame, rows[(rows["strategy"] == strategy) & (rows["firm"] == firm)])
    if mine.empty:
        raise SystemExit(f"{strategy}/{firm}: no está en el registro de estrategias en real")
    deals = history.deals(MT5_ACCOUNTS[firm]["login"])
    if deals is None:
        raise SystemExit(f"{firm}: el colector no tiene aún el historial de la cuenta")
    frame = live.trades([{**d, "position_id": d["position"]} for d in deals])
    sqx = Path(mine["sqx"].iloc[0])
    split, _ = live.by_strategy(frame, firm, rows)
    return split[strategy].dropna(subset=["Close time"]), sqx, register.market(sqx)[1]


def r_values(real: pd.DataFrame, sqx: pd.DataFrame) -> list[float]:
    """The real trades' P&L in R, oldest close first: 1 R is the judge's mean SQX loss.

    Args:
        real, sqx: Both already in points (`compare.in_points`), so the units match.
    """
    r = compare.mean_loss(sqx)
    return (real.sort_values("Close time")["Profit/Loss"] / r).tolist()
