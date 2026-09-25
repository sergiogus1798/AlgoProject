"""What the study is run on: its knobs, one strategy's trades, its bars and its window."""

from pathlib import Path

import pandas as pd
import yaml

from core.assetdata import load as load_asset, window as asset_window
from core.barstore import read as read_bars
from core.paths import DATA, ROOT

CONFIG = ROOT / "strategies" / "exposure" / "config.yaml"


def config(overrides: list[str]) -> dict:
    """The study's knobs, with command-line overrides applied.

    Args:
        overrides: Dotted `section.key=value` strings, as `--set` passes them.

    Returns:
        What config.yaml holds, each override parsed as YAML so numbers stay numbers.
    """
    cfg = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    for item in overrides:
        dotted, raw = item.split("=", 1)
        section, key = dotted.split(".", 1)
        cfg[section][key] = yaml.safe_load(raw)
    return cfg


def newest(project: str, databank: str) -> Path:
    """The most recent dated trade export of one databank.

    Args:
        project: Project name.
        databank: Databank name as SQX shows it.

    Returns:
        Its `trades.parquet`. Exports are dated and immutable, so the newest is the one
        with the most strategies in it, never a partially refreshed older one.
    """
    folder = DATA / "raw" / project / databank.replace(" ", "_")
    return sorted(folder.glob("*/trades.parquet"))[-1]


def sample(packed: Path, which: str) -> pd.DataFrame:
    """Every strategy's trades on one sample of the export.

    Args:
        packed: The `trades.parquet` an export wrote.
        which: A value of the `Sample type` column -- "IST" in sample, "OOS1" out of it.

    Returns:
        The export cut to that sample, in the order SQX reported it. Read once and grouped
        by caller: the file is one frame of a million rows, and re-reading it per strategy
        is the difference between seconds and an hour.
    """
    frame = pd.read_parquet(packed)
    return frame[frame["Sample type"] == which]


def bars(feed: str, timeframe: str, span: tuple[pd.Timestamp, pd.Timestamp]) -> pd.DataFrame:
    """The bars of the window this study is measured over.

    Args:
        feed: The SQX feed name, e.g. "XAUUSD_DukasM1_Infinox".
        timeframe: "M30", "H1" and the rest; resampled from M1 and cached by barstore.
        span: First and last instant of the segment, as `window` returns them.

    Returns:
        One row per bar, indexed by open time, cut to the segment. The cut is what makes
        occupancy a share of the market's open hours rather than of wall-clock time.
    """
    frame = read_bars(feed, timeframe)
    return frame[(frame.index >= span[0]) & (frame.index < span[1])]


def window(symbol: str, segment: str) -> tuple[pd.Timestamp, pd.Timestamp]:
    """The segment's dates, as the policy file declares them.

    Args:
        symbol: Asset name, e.g. "XAUUSD".
        segment: "build", "oos1" or "oos2".

    Returns:
        First instant and the instant after the last, both UTC-naive to match the bars.
        These come from `assets/_policy.yaml` and never from the trades: a strategy that
        happened not to trade in the first two years of its window would otherwise be
        credited with a shorter window and a higher occupancy than it had.
    """
    start, end = asset_window(load_asset(symbol), segment)
    return (pd.Timestamp(start, unit="ms"), pd.Timestamp(end, unit="ms"))


def point_value(symbol: str) -> float:
    """Account currency per 1.0 of price and 1.0 of lot.

    Args:
        symbol: Asset name, e.g. "XAUUSD".

    Returns:
        The figure SQX holds for the instrument, read from the asset file.
    """
    return float(load_asset(symbol)["instrument"]["point_value"])
