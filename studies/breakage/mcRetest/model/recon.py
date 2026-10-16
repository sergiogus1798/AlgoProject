"""The 30 metrics reconstructible from a P/L vector, and the declaration of what the rest are."""

from typing import Any

import numpy as np

from studies.breakage.mcRetest.model import counts, drawdown, runs

# Every metric SQX varies with the confidence level, sorted into exactly one of four sets.
# integrity.py asserts the partition, so "absent from RECON" can never be read as "unimportant".
RECON = {
    "NetProfit": counts.net_profit,
    "NumberOfTrades": counts.number_of_trades,
    "GrossProfit": counts.gross_profit,
    "GrossLoss": counts.gross_loss,
    "ProfitFactor": counts.profit_factor,
    "NumberOfProfits": counts.number_of_profits,
    "NumberOfLosses": counts.number_of_losses,
    "WinningPct": counts.winning_pct,
    "AvgWin": counts.avg_win,
    "AvgLoss": counts.avg_loss,
    "AvgTrade": counts.avg_trade,
    "Expectancy": counts.avg_trade,
    "WinLossRatio": counts.win_loss_ratio,
    "PayoutRatio": counts.payout_ratio,
    "MaxProfit": counts.max_profit,
    "MaxLoss": counts.max_loss,
    "StandardDev": counts.standard_dev,
    "SQN": counts.sqn,
    "KellyFormula": counts.kelly_formula,
    "Drawdown": drawdown.deepest,
    "DrawdownPct": drawdown.deepest_pct,
    "AvgDrawdown": drawdown.avg_drawdown,
    "AvgPctDrawdown": drawdown.avg_pct_drawdown,
    "ReturnDDRatio": drawdown.return_dd_ratio,
    "RecoveryFactor": drawdown.recovery_factor,
    "MaxConsecWins": runs.max_consec_wins,
    "MaxConsecLosses": runs.max_consec_losses,
    "AvgConsecWins": runs.avg_consec_wins,
    "AvgConsecLosses": runs.avg_consec_losses,
    "ZScore": runs.zscore,
}

# Which way "worse" runs. A confidence level is an order statistic, so every metric needs a
# direction, and the losing half of the table runs the other way: level 100 of Drawdown is the
# DEEPEST fall, while level 100 of NetProfit is the SMALLEST profit.
# MaxLoss is here too, and its consequence is a trap: SQX's level-100 MaxLoss is the value
# closest to zero, so the "99% confidence" worst trade is the mildest one, not the harshest.
HIGHER_IS_WORSE = frozenset(
    {
        "GrossLoss",
        "Drawdown",
        "DrawdownPct",
        "AvgDrawdown",
        "AvgPctDrawdown",
        "NumberOfLosses",
        "AvgLoss",
        "StandardDev",
        "MaxConsecLosses",
        "AvgConsecLosses",
        "MaxLoss",
    }
)

# Computed by SQX on the DAILY equity curve, which no simulation file carries. A per-trade
# version is a different object and travels under a different name, never these.
ANALOGUE = {
    "SharpeRatio": "per-trade, not over the daily equity curve SQX uses; fails its table by 70%",
    "SortinoRatio": "same daily-equity basis as SharpeRatio",
    "UlcerIndex": "every trade-indexed variant fails the stored table by 61% or worse",
    "RSquared": "SQX fits the daily equity curve; trade-indexed gives 0.897 against 0.92",
    "Stability": "related to RSquared but not equal to it, and still uncalibrated",
}

EXCLUDED = {
    "AvgAbsTrade": "sits at a constant ratio of 1.00215 to mean(|pnl|) with no formula found, "
    "and barely moves between simulations, so it informs nothing"
}


def parts(pnl_cents: np.ndarray, offsets: np.ndarray, capital: float) -> dict[str, Any]:
    """The shared intermediates every metric reads, computed once per task and strategy.

    Args:
        pnl_cents: Every simulation's P/L concatenated, in cents, as core.sqxretest gives it.
        offsets: Where each simulation starts, length sims + 1.
        capital: Account the drawdown percentages are measured against, USD.

    Returns:
        The reductions each metric needs, plus the paths the sequence-dependent ones need.
        One dict is the shared signature of the registry: every function in RECON takes this
        and returns one value per simulation.
    """
    pnl = pnl_cents.astype(np.float64) / 100.0
    wins, losses = np.where(pnl > 0, pnl, 0.0), np.where(pnl < 0, pnl, 0.0)
    shared = {
        "pnl": pnl,
        "offsets": offsets,
        "capital": capital,
        "n": np.diff(offsets).astype(np.float64),
        "total": drawdown.reduce(np.add, pnl, offsets),
        "sq_sum": drawdown.reduce(np.add, pnl**2, offsets),
        "wins_sum": drawdown.reduce(np.add, wins, offsets),
        "losses_sum": drawdown.reduce(np.add, losses, offsets),
        "wins_n": drawdown.reduce(np.add, (pnl > 0).astype(np.float64), offsets),
        "losses_n": drawdown.reduce(np.add, (pnl < 0).astype(np.float64), offsets),
        # 🔬 A trade that closed at exactly zero is HALF a win to SQX. Measured
        # 2026-09-24 on USDJPY H1: with 1 zero in 506 trades its Winning Percent is
        # 51.680, exactly between 51.581 (wins/n) and 51.779 ((wins+zeros)/n), and the
        # same split holds on every strategy that has one. Gold never produced a zero,
        # which is why the reconstruction reconciled there and fails here.
        "wins_rate_n": drawdown.reduce(
            np.add, np.where(pnl > 0, 1.0, np.where(pnl == 0, 0.5, 0.0)), offsets
        ),
        "largest": drawdown.reduce(np.maximum, pnl, offsets),
        "smallest": drawdown.reduce(np.minimum, pnl, offsets),
    }
    return runs.prepare(drawdown.prepare(shared))


def frame(
    pnl_cents: np.ndarray, offsets: np.ndarray, capital: float
) -> dict[str, np.ndarray]:
    """Every reconstructible metric of every simulation.

    Args:
        pnl_cents: Every simulation's P/L concatenated, in cents.
        offsets: Where each simulation starts, length sims + 1.
        capital: Account the drawdown percentages are measured against, USD.

    Returns:
        {metric name: one value per simulation}. This is the study's main table; everything
        downstream reads it and nothing downstream reopens a .sqx.
    """
    shared = parts(pnl_cents, offsets, capital)
    return {name: metric(shared) for name, metric in RECON.items()}
