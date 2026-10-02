"""What the profile is run on: the config, the build bars of an asset, and its cost per trade."""

import time
from pathlib import Path

import numpy as np
import pandas as pd

from core import assetdata, barstore
from core.paths import bar_source
from core.study import config as study_config
from core.symbols import current

CONFIG = Path(__file__).with_name("config.yaml")
SEGMENT = "build"      # the only segment the profile may read
PRICES = ["Open", "High", "Low", "Close"]


def config(overrides: list[str] | None = None) -> dict:
    """The parsed config.yaml with its overrides; a null seed becomes a fresh, recorded root."""
    cfg = study_config.load(CONFIG, overrides or [])
    if cfg["nulls"]["seed"] is None:
        cfg["nulls"]["seed"] = int(np.random.SeedSequence().entropy % 2 ** 32)
    return cfg


def span(symbol: str) -> tuple[pd.Timestamp, pd.Timestamp]:
    """The asset's build segment: its first instant, and the first instant after it.

    Raises ValueError when the asset has no build dates: a window is never invented.
    """
    lo, hi = assetdata.window(assetdata.load(symbol), SEGMENT)
    return pd.Timestamp(lo, unit="ms"), pd.Timestamp(hi, unit="ms")


def cut(m1: pd.DataFrame, symbol: str) -> pd.DataFrame:
    """The M1 bars of the build segment and nothing else.

    Args:
        m1: A feed's M1 bars, indexed by bar open time.
        symbol: The asset whose build window applies.

    Returns:
        The rows inside [from, to). This is the one place bars enter the profile: whatever
        comes after the build end is dropped here, before any resampling or measure.
    """
    lo, hi = span(symbol)
    return m1[(m1.index >= lo) & (m1.index < hi)]


def minute_bars(symbol: str, fresh_minutes: int) -> pd.DataFrame | None:
    """The build segment's M1 bars of one asset, or None while its feed is being rewritten.

    Args:
        symbol: Asset as `assets/symbols/` spells it.
        fresh_minutes: A file modified within this many minutes, or during the read, is not
            trusted.
    """
    path = bar_source(current(assetdata.load(symbol)["sqx_symbol"]))
    stamp = path.stat().st_mtime
    if time.time() - stamp < fresh_minutes * 60:
        return None
    m1 = cut(barstore.source(assetdata.load(symbol)["sqx_symbol"], PRICES), symbol)
    return m1 if path.stat().st_mtime == stamp else None


def bars(m1: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    """M1 bars resampled the way core.barstore does, without touching its cache."""
    agg = {k: barstore.AGG[k] for k in PRICES}
    return m1.resample(barstore.RULE[timeframe]).agg(agg).dropna()


def cost(asset: dict, price: np.ndarray) -> np.ndarray:
    """What one round trip costs in the build segment, in price units, at each entry price.

    Args:
        asset: What core.assetdata.load() returned.
        price: Entry prices.

    Returns:
        Spread plus slippage on both fills plus the segment's commission — the ideaExpert's
        "total por operación". The swap is not in it: it depends on the nights held.
    """
    use = asset["costs"]
    half = asset["segments"][SEGMENT]["spread"]
    tick = asset["instrument"]["tick_size"]
    points = use[f"spread_{half}"]["use"] + 2 * use[f"slippage_{half}"]["use"]
    fee = use["commission"]["use"][SEGMENT]
    if fee["method"] == "SizeBased":
        return points * tick + fee["value"] / asset["instrument"]["point_value"] + 0 * price
    return points * tick + fee["value"] / 100 * price
