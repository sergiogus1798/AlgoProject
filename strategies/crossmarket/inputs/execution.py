"""What a worse broker would charge, per feed, so the stress stops using round numbers.

Reads execution.yaml. The cost the backtest really paid is never taken from here — that is
recovered per trade from SQX's own P/L in mechanics/pricing.py — and this only scales it."""

from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from core import assets, trades as tradeio

# parents[1]: the .yaml stays in the module root, where the manual names it.
FILE = Path(__file__).parents[1] / "execution.yaml"
DIVERGENCE = 0.25   # modelled against recovered cost; beyond this, one of the two is wrong


def load(feed: str) -> dict | None:
    """One feed's execution assumptions.

    Args:
        feed: The SQX symbol, exactly as the export names it.

    Returns:
        The parsed block, or None when the feed is not declared — a feed nobody has written
        numbers for gets the config.yaml defaults and a warning, never an invented value.
        When `asset_file` names a file in assets/ whose `spread.use` the owner has decided,
        that decided spread replaces the placeholder and the block says so.
    """
    declared = yaml.safe_load(FILE.read_text(encoding="utf-8")).get(feed)
    if declared is None:
        return None
    named = declared.get("asset_file")
    decided = assets.load(named)["spread"]["use"] if named else None
    if decided is None:
        return declared
    return {**declared, "spread_typical": float(decided), "source": f"assets/{named}.yaml"}


def shock(spec: dict | None, default: list[float]) -> list[float]:
    """The cost multiple range the stress draws from, per run.

    Args:
        spec: What load() returned.
        default: config.yaml's stress.cost_shock, used when the feed is not declared.

    Returns:
        [1.0, stress spread / typical spread]. A run drawing 2.4 means it paid 2.4x the cost
        the backtest paid — which is what a $0.60 spread is against a $0.25 one.
    """
    if spec is None or not spec["spread_typical"]:
        return default
    return [1.0, float(spec["spread_stress"] / spec["spread_typical"])]


def depth(spec: dict | None, mae_price: np.ndarray, default: float) -> float:
    """How much of its own adverse excursion a badly filled trade gives back.

    Args:
        spec: What load() returned.
        mae_price: Each trade's maximum adverse excursion, in price.
        default: config.yaml's stress.fill_depth.

    Returns:
        Typical slippage on both sides, as a fraction of the median MAE. Derived rather than
        assumed: giving back 25% of the excursion was a round number, while "two sides of the
        spread against a trade that typically ran $1.80 offside" is a measurement.
    """
    median = float(np.nanmedian(np.abs(mae_price)))
    if spec is None or not median:
        return default
    return min(2 * spec["slippage_typical"] * spec["tick_size"] / median, 1.0)


def modelled(spec: dict | None, aligned: pd.DataFrame, point_value: float) -> float:
    """Median round-turn cost this file implies, in USD per trade.

    Args:
        spec: What load() returned.
        aligned: One market's trades, as backtest.setting() kept them.
        point_value: What pricing.point_value() measured.

    Returns:
        Spread crossed once plus commission twice, at the real position sizes. NaN when the
        feed is not declared.
    """
    if spec is None:
        return float("nan")
    lots = aligned["Size"].to_numpy()
    spread = spec["spread_typical"] * spec["tick_size"] * lots * point_value
    return float(np.median(spread + 2 * spec["commission"] * lots))


def compare(fixed: dict, feed: str) -> dict:
    """What this file says a trade cost, against what SQX actually charged.

    Args:
        fixed: What backtest.setting() returned.
        feed: The market's SQX symbol.

    Returns:
        Keys charged, modelled, gap, diverges, source and reviewed. `charged` is measured from
        the export and is the truth; a gap past DIVERGENCE means the assumptions below are
        describing a different broker from the one the backtest was run against, which is a
        reason to distrust the stress, not the backtest.
    """
    spec = load(feed)
    charged = float(np.median(tradeio.cost(fixed["aligned"], fixed["point_value"])))
    said = modelled(spec, fixed["aligned"], fixed["point_value"])
    gap = float("nan") if not np.isfinite(said) or not charged else said / charged - 1
    return {"charged": charged, "modelled": said, "gap": gap,
            "diverges": bool(np.isfinite(gap) and abs(gap) > DIVERGENCE),
            "declared": spec is not None,
            "source": "" if spec is None else spec["source"],
            "reviewed": bool(spec is not None and spec["reviewed_by_owner"])}


def settings(fixed: dict, feed: str, cfg: dict) -> dict:
    """The stress parameters this market actually runs with.

    Args:
        fixed: What backtest.setting() returned.
        feed: The market's SQX symbol.
        cfg: What config.load() returned.

    Returns:
        config.yaml's stress block, with cost_shock and fill_depth replaced by the calibrated
        ones when stress.calibrate is on and the feed is declared. p_skip is never calibrated:
        nothing in the export says how often an order would have been missed, so it stays an
        explicit assumption and the panel prints it as one.
    """
    s = dict(cfg["stress"])
    if not s.get("calibrate", True):
        return {**s, "calibrated": False}
    spec = load(feed)
    mae = tradeio.excursions(fixed["aligned"], fixed["point_value"])["mae"].to_numpy()
    return {**s, "cost_shock": shock(spec, s["cost_shock"]),
            "fill_depth": depth(spec, mae, s["fill_depth"]),
            "calibrated": spec is not None}
