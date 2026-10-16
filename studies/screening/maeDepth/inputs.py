"""Every knob, and what one run reads: the gate's harvest, the bars and the ATR of the feed."""

from pathlib import Path
from typing import Any, TypedDict

import numpy as np
import pandas as pd

from core import assetdata
from core.barstore import read as read_bars
from core.study import config as study_config
from engines.market import atr as sqx_atr
from ledger import thresholds

CONFIG = Path(__file__).with_name("config.yaml")


class Inputs(TypedDict):
    """What one run reads: the harvest's trades, the bars' index and ATR, the market."""

    trades: pd.DataFrame
    names: pd.Series
    timeframe: str
    index: pd.DatetimeIndex
    atr: np.ndarray
    point_value: float
    symbol: str


SEGMENTS = {
    "IS": "build",
    "OOS": "oos1",
}  # the harvest's `sample` -> the ledger's segment


def config(overrides: list[str]) -> dict[str, Any]:
    """Every knob, with command-line overrides applied.

    Args:
        overrides: "section.key=value" strings, as --set gives them.

    Returns:
        The parsed config.yaml with every `ledger:<key>` replaced by the ledger's value.
    """
    return study_config.apply(thresholds.fill(study_config.load(CONFIG, [])), overrides)


def load(folder: Path, feed: str, cfg: dict) -> Inputs:
    """What `many.run` reads.

    Args:
        folder: A `studies.screening.gate.harvest` folder.
        feed: SQX feed name of the main market, e.g. "USDJPY_M1".
        cfg: What `config` returned.

    Returns:
        `trades` (the harvest's, last row without a close price dropped), `names` (identity ->
        strategy name), `timeframe`, `index` and `atr` on the strategy's bars, `point_value`.
    """
    metrics = pd.read_parquet(
        folder / "metrics.parquet", columns=["strategy", "TimeFrame [IS]"]
    )
    timeframe = metrics["TimeFrame [IS]"].iloc[0]
    trades = pd.read_parquet(folder / "trades.parquet")
    trades = pd.DataFrame(trades[trades["Close price"].notna()]).reset_index(drop=True)
    bars = read_bars(feed, timeframe)
    symbol = assetdata.symbol_for(feed)
    if symbol is None:
        raise SystemExit(f"ningún fichero de assets/symbols/ declara el feed {feed!r}")
    return Inputs(
        trades=trades,
        names=pd.Series(metrics["strategy"]),
        timeframe=timeframe,
        index=pd.DatetimeIndex(bars.index),
        atr=sqx_atr.sqx(bars, cfg["depth"]["atr_period"]),
        point_value=float(assetdata.load(symbol)["instrument"]["point_value"]),
        symbol=symbol,
    )


def window(trades: pd.DataFrame) -> tuple[str, str]:
    """First open and last close of some trades, as dates, for the ledger row."""
    return str(trades["Open time"].min().date()), str(trades["Close time"].max().date())
