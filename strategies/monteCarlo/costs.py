"""What the broker charged and what a worse broker would charge, per asset and per trade."""

import numpy as np
import pandas as pd

from core import assets, trades

DIVERGENCE = 0.25   # modelled against recovered cost; beyond this the cost file is suspect


def load(symbol: str) -> dict:
    """The cost facts of one asset, taken from its file in assets/.

    Args:
        symbol: Asset name as assets/ calls it, e.g. "XAUUSD".

    Returns:
        point_value (USD per 1.0 of price per lot), tick_size, spread in points and
        commission in USD per lot per side. The values are SQX's own defaults rather than
        the `use:` overrides: this study reproduces and stresses a backtest SQX already ran,
        so the costs that belong in it are the ones that were actually charged in it.
    """
    data = assets.load(symbol)
    return {"symbol": symbol,
            "point_value": float(data["point_value"]["sqx_default"]),
            "tick_size": float(data["tick_size"]),
            "spread": float(data["spread"]["sqx_default"]),
            "commission": float(str(data["commission"]["sqx_default"]).split()[-1]),
            "pending": assets.pending(data)}


def recovered(frame: pd.DataFrame, asset: dict) -> np.ndarray:
    """Cost SQX actually charged per trade, measured rather than assumed.

    Args:
        frame: One strategy's trades.
        asset: What load() returned.

    Returns:
        USD per trade, positive. Gross minus net P&L: commission and swap together, exactly
        as the backtest booked them. The trade export carries no cost column, so this
        subtraction is the only honest source of a per-trade cost here.
    """
    return trades.cost(frame, asset["point_value"]).to_numpy()


def spread_cost(frame: pd.DataFrame, asset: dict) -> np.ndarray:
    """What one round trip costs at the asset's quoted spread.

    Args:
        frame: One strategy's trades.
        asset: What load() returned.

    Returns:
        USD per trade. Spread is inside the fill prices SQX used, so this is the size of the
        extra cost a wider spread would add, not a cost to be subtracted twice.
    """
    return (asset["spread"] * asset["tick_size"] * asset["point_value"]
            * frame["Size"].to_numpy())


def crosscheck(frame: pd.DataFrame, asset: dict) -> dict:
    """Modelled commission against the cost the backtest really booked.

    Args:
        frame: One strategy's trades.
        asset: What load() returned.

    Returns:
        Both medians, their ratio and whether it diverges beyond DIVERGENCE. A mismatch
        means the asset file describes a different instrument than the one that was traded,
        which invalidates every Family C number without invalidating anything else — so it
        is a warning that travels with the report, not a refusal to run.
    """
    modelled = 2 * asset["commission"] * frame["Size"].to_numpy()
    real = recovered(frame, asset)
    ratio = float(np.median(modelled) / np.median(real))
    return {"modelled": float(np.median(modelled)), "recovered": float(np.median(real)),
            "ratio": ratio, "diverges": bool(abs(ratio - 1) > DIVERGENCE)}
