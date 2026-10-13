"""What the reading opens: the mothers' variant batches, their oos2 trades, the oos2 dates and her daily P&L."""

from pathlib import Path

import numpy as np
import pandas as pd

from core.assetdata import load as load_asset, window as asset_window
from core.datapaths import variants_dir
from core.study import config as study_config
from ledger import thresholds
from portfolio.common.construct.equity import closecurve

CONFIG = Path(__file__).with_name("config.yaml")
STEP = 19           # the policy's reserve names WFM (19), not this reading; `ledger.gate.seal` refuses any other number
SEGMENT = "oos2"
TRADES = "trades.parquet"   # per variant, in the batch folder: step 16.5's harvest writes it


def config(overrides: list[str]) -> dict:
    """The reading's knobs, with command-line `section.key=value` overrides applied."""
    return study_config.apply(thresholds.fill(study_config.load(CONFIG, [])), overrides)


def batches(project: str) -> dict[str, Path]:
    """The mothers' variant batches of a project that hold their trades: {folder name: path}."""
    root = variants_dir(project, "x").parent
    return {b.name: b for b in sorted(root.iterdir()) if (b / TRADES).exists()}


def window(symbol: str) -> tuple[pd.Timestamp, pd.Timestamp]:
    """The oos2 dates as the policy declares them: first instant, instant after the last."""
    start, end = asset_window(load_asset(symbol), SEGMENT)
    return pd.Timestamp(start, unit="ms"), pd.Timestamp(end, unit="ms")


def mother_trades(batch: Path, span: tuple[pd.Timestamp, pd.Timestamp]) -> pd.DataFrame:
    """One mother's own trades inside oos2 (schema T plus `variant_id`): the variant the manifest flags `origin`."""
    origin = pd.read_parquet(batch / "manifest.parquet", columns=["variant_id", "origin"])
    mine = origin.loc[origin["origin"], "variant_id"].item()
    trades = pd.read_parquet(batch / TRADES, filters=[("variant_id", "==", mine)])
    if isinstance(trades.index, pd.RangeIndex):      # the filtered read renumbers; the labels are the file's rows
        ids = pd.read_parquet(batch / TRADES, columns=["variant_id"])["variant_id"].to_numpy()
        trades.index = np.flatnonzero(ids == mine)
    return trades[(trades["Open time"] >= span[0]) & (trades["Close time"] < span[1])]


def daily(trades: pd.DataFrame, bars: pd.DataFrame) -> pd.Series:
    """The mother's mark-to-market P&L per feed day, flat days 0 (`closecurve`): sums to her trades' Profit/Loss."""
    if trades.empty:
        return pd.Series(0.0, index=bars.index.normalize().unique())
    profit, _ = closecurve.panel(trades.assign(identity="m"), bars, *closecurve.measured(trades))
    return profit["m"]
