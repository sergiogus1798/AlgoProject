"""Family C: what the same trades are worth under worse fills, worse costs and missed entries."""

import numpy as np


def skip(stream: dict, n: int, rng: np.random.Generator, cfg: dict) -> np.ndarray:
    """Miss trades at random, as a live system does.

    Args:
        stream: What stream.build() returned.
        n: Simulations to draw.
        rng: Fresh generator.
        cfg: The family_c section of the config.

    Returns:
        One row of per-trade P&L per simulation. A missed trade is set to zero rather than
        removed, so every row stays the same length: net profit and drawdown are identical
        either way, and neither of this test's floors is computed from the trade count.
    """
    keep = rng.random((n, stream["pnl"].size)) >= cfg["p_skip"]
    return stream["pnl"] * keep


def cost_shock(stream: dict, n: int, rng: np.random.Generator, cfg: dict) -> np.ndarray:
    """Charge each trade a worse commission and swap than the backtest did.

    Args:
        stream: What stream.build() returned.
        n: Simulations to draw.
        rng: Fresh generator.
        cfg: The family_c section of the config.

    Returns:
        One row of per-trade P&L per simulation. The multiplier is applied to the cost SQX
        actually booked, and only the increment is subtracted: the P&L is already net, so
        charging the whole modelled cost would count it twice.
    """
    lo, hi = cfg["cost_shock_range"]
    factor = rng.uniform(lo, hi, (n, stream["cost"].size))
    return stream["pnl"] - stream["cost"] * (factor - 1.0)


def fill_degrade(stream: dict, n: int, rng: np.random.Generator, cfg: dict) -> np.ndarray:
    """Give back part of what each trade had already given up at its worst point.

    Args:
        stream: What stream.build() returned.
        n: Simulations to draw.
        rng: Fresh generator.
        cfg: The family_c section of the config.

    Returns:
        One row of per-trade P&L per simulation. A degraded trade moves toward its own MAE,
        so it is only ever worsened as far as the market really went against that position —
        a flat haircut would invent losses the trade never had a chance to take.
    """
    n_trades = stream["pnl"].size
    hit = rng.random((n, n_trades)) < cfg["fill_frac"]
    depth = rng.uniform(0.0, cfg["fill_depth"], (n, n_trades)) * hit
    return stream["pnl"] - depth * (stream["pnl"] - stream["mae"])


def spread_widen(stream: dict, n: int, rng: np.random.Generator, cfg: dict) -> np.ndarray:
    """Pay a wider spread on every trade.

    Args:
        stream: What stream.build() returned.
        n: Simulations to draw.
        rng: Fresh generator.
        cfg: The family_c section of the config.

    Returns:
        One row of per-trade P&L per simulation. Applied to all trades, not a sample: a
        backtest's spread is a single fixed number and reality is worse than it every time,
        which is exactly what a fixed backtest spread hides.
    """
    lo, hi = cfg["spread_scale"]
    factor = rng.uniform(lo, hi, (n, stream["spread"].size))
    return stream["pnl"] - stream["spread"] * factor


STRESS = {"skip": skip, "cost_shock": cost_shock, "fill_degrade": fill_degrade,
          "spread_widen": spread_widen}

# What each sub-test claims to model, and the floor it has to clear. The floors live in
# scoring.py; this table is what the report prints beside each of them.
TITLES = {"skip": "Entradas perdidas", "cost_shock": "Costes hasta el doble",
          "fill_degrade": "Ejecuciones degradadas", "spread_widen": "Spread más ancho"}
MODELS = {"skip": "entries the live system does not take",
          "cost_shock": "commission and swap up to twice what SQX charged",
          "fill_degrade": "fills that give back part of the trade's own worst excursion",
          "spread_widen": "a spread wider than the fixed one the backtest assumed"}
