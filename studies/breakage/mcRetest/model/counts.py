"""The metrics that are reductions over the trades of a simulation, with SQX's own conventions."""

import numpy as np


def net_profit(p: dict) -> np.ndarray:
    """Total profit of each simulation.

    Args:
        p: What recon.parts() returned.

    Returns:
        USD per simulation.
    """
    return p["total"]


def number_of_trades(p: dict) -> np.ndarray:
    """How many trades each simulation produced.

    Args:
        p: What recon.parts() returned.

    Returns:
        Trade count per simulation. It varies: randomising a parameter changes which signals
        fire, so this is a response of the strategy and not a constant of the study.
    """
    return p["n"].astype(np.float64)


def gross_profit(p: dict) -> np.ndarray:
    """Sum of the winning trades.

    Args:
        p: What recon.parts() returned.

    Returns:
        USD per simulation.
    """
    return p["wins_sum"]


def gross_loss(p: dict) -> np.ndarray:
    """Sum of the losing trades, positive.

    Args:
        p: What recon.parts() returned.

    Returns:
        USD per simulation. SQX stores this as a positive magnitude, not a negative sum.
    """
    return -p["losses_sum"]


def profit_factor(p: dict) -> np.ndarray:
    """Gross profit over gross loss.

    Args:
        p: What recon.parts() returned.

    Returns:
        A ratio per simulation, inf where nothing lost. The most outlier-sensitive metric
        here: one large trade moves it far more than it moves net profit.
    """
    return np.divide(p["wins_sum"], -p["losses_sum"],
                     out=np.full_like(p["wins_sum"], np.inf), where=p["losses_sum"] < 0)


def number_of_profits(p: dict) -> np.ndarray:
    """How many trades made money.

    Args:
        p: What recon.parts() returned.

    Returns:
        Count per simulation.
    """
    return p["wins_n"].astype(np.float64)


def number_of_losses(p: dict) -> np.ndarray:
    """How many trades lost money.

    Args:
        p: What recon.parts() returned.

    Returns:
        Count per simulation. A trade of exactly zero is neither, which is why this is
        counted rather than derived from the total.
    """
    return p["losses_n"].astype(np.float64)


def winning_pct(p: dict) -> np.ndarray:
    """Share of trades that made money, with a flat trade counted as half a win.

    Args:
        p: What recon.parts() returned.

    Returns:
        Percent per simulation. The half is SQX's own convention, measured — see
        `recon.parts`. It matters only on instruments whose tick can close a trade at
        exactly zero, and there it is the difference between reconciling and not.
    """
    return 100.0 * p["wins_rate_n"] / p["n"]


def avg_win(p: dict) -> np.ndarray:
    """Mean winning trade.

    Args:
        p: What recon.parts() returned.

    Returns:
        USD per simulation.
    """
    return np.divide(p["wins_sum"], p["wins_n"], out=np.zeros_like(p["wins_sum"]),
                     where=p["wins_n"] > 0)


def avg_loss(p: dict) -> np.ndarray:
    """Mean losing trade, positive.

    Args:
        p: What recon.parts() returned.

    Returns:
        USD per simulation. Stored positive, as SQX stores it -- a signed reconstruction
        comes out with the wrong sign and looks like a factor-of-two error.
    """
    return np.divide(-p["losses_sum"], p["losses_n"], out=np.zeros_like(p["losses_sum"]),
                     where=p["losses_n"] > 0)


def avg_trade(p: dict) -> np.ndarray:
    """Mean trade.

    Args:
        p: What recon.parts() returned.

    Returns:
        USD per simulation. SQX stores the same number twice, as AvgTrade and Expectancy.
    """
    return p["total"] / p["n"]


def win_loss_ratio(p: dict) -> np.ndarray:
    """Winning trades per losing trade.

    Args:
        p: What recon.parts() returned.

    Returns:
        A count ratio per simulation. **Not** mean win over mean loss -- that is PayoutRatio,
        and the two are different columns despite the names. Calibrated against SQX.
    """
    return np.divide(p["wins_n"].astype(np.float64), p["losses_n"],
                     out=np.full(p["n"].shape, np.inf), where=p["losses_n"] > 0)


def payout_ratio(p: dict) -> np.ndarray:
    """Mean win over mean loss.

    Args:
        p: What recon.parts() returned.

    Returns:
        A ratio per simulation. This is the one the Kelly fraction uses as its R.
    """
    return np.divide(avg_win(p), avg_loss(p), out=np.full(p["n"].shape, np.inf),
                     where=avg_loss(p) > 0)


def max_profit(p: dict) -> np.ndarray:
    """Largest single winning trade.

    Args:
        p: What recon.parts() returned.

    Returns:
        USD per simulation.
    """
    return p["largest"]


def max_loss(p: dict) -> np.ndarray:
    """Largest single losing trade, signed.

    Args:
        p: What recon.parts() returned.

    Returns:
        USD per simulation, negative. SQX ranks this metric in the opposite direction to
        MaxProfit -- see recon.REVERSED -- so its worst confidence level is the mildest
        worst trade, not the harshest.
    """
    return p["smallest"]


def standard_dev(p: dict) -> np.ndarray:
    """Spread of the trades of each simulation.

    Args:
        p: What recon.parts() returned.

    Returns:
        USD per simulation, population deviation. SQX uses ddof=0 here; measured against
        its stored tables, ddof=1 misses by 0.47 and ddof=0 by 0.008.
    """
    mean = p["total"] / p["n"]
    return np.sqrt(np.maximum(p["sq_sum"] / p["n"] - mean ** 2, 0.0))


def sqn(p: dict) -> np.ndarray:
    """System Quality Number.

    Args:
        p: What recon.parts() returned.

    Returns:
        A ratio per simulation. SQX caps the sample-size factor at 100 trades --
        sqrt(min(n, 100)), not sqrt(n) -- which on 763 trades is the difference between
        0.77 and 2.12.
    """
    sd = standard_dev(p)
    return np.divide(np.sqrt(np.minimum(p["n"], 100)) * (p["total"] / p["n"]), sd,
                     out=np.zeros_like(sd), where=sd > 0)


def kelly_formula(p: dict) -> np.ndarray:
    """Optimal fraction of capital per bet under the classic Kelly criterion.

    Args:
        p: What recon.parts() returned.

    Returns:
        Percent per simulation, from the win rate and PayoutRatio. A theoretical ceiling on
        sizing and never a sizing: the fractional variant is what anyone actually uses.
        Its win rate leaves flat trades out — wins / (wins + losses) — unlike WinningPct's
        half-a-win: 🔬 2026-09-25 on USDJPY (~1.7 flat trades per 511) that is the only form
        that lands on SQX's stored level at all eleven confidence levels.
    """
    r, w = payout_ratio(p), p["wins_n"] / (p["wins_n"] + p["losses_n"])
    return 100.0 * np.divide(w * r - (1 - w), r, out=np.zeros_like(r), where=np.isfinite(r) & (r > 0))
