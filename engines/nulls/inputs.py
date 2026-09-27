"""What the study is run on: its knobs, one strategy's trades, and the bars they sat on."""

from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

from core.barstore import read as read_bars
from core.paths import DATA
from core.study import config as study_config

CONFIG = Path(__file__).with_name("config.yaml")


def config(overrides: list[str]) -> dict:
    """The study's knobs, with command-line overrides applied.

    Args:
        overrides: Dotted `section.key=value` strings, as `--set` passes them; each keeps
            the type of the value it replaces (core.study.config).

    Returns:
        What config.yaml holds.
    """
    return study_config.load(CONFIG, overrides)


def markets(packed: Path) -> list[str]:
    """The markets one export holds, when it holds more than its own.

    Args:
        packed: The `trades.parquet` an export wrote.

    Returns:
        The feeds of its `Symbol` column, sorted, for a `data=all` export (cross-market);
        empty for a one-market export, whose feed is only in its manifest.
    """
    if "Symbol" not in pq.read_schema(packed).names:
        return []
    return sorted(pd.read_parquet(packed, columns=["Symbol"])["Symbol"].astype(str).unique())


def trades(packed: Path, which: str, feed: str = "", strategy: str = "") -> pd.DataFrame:
    """The trades of one sample of an export, of one market and one strategy when asked.

    Args:
        packed: The `trades.parquet` an export wrote.
        which: A value of the `Sample type` column -- "IST" in sample, "OOS1" out of it.
        feed: The market to keep. Required for an export of several markets: 📓 2026-09-26,
            reading a cross-market export by strategy alone handed the monkey the trades of
            ten markets as one strategy, priced on one market's bars, with nothing failing.
        strategy: The strategy to keep; every strategy when empty.

    Returns:
        The rows, in the order SQX reported them. Filtered while reading, so a 12 M-row
        cross-market export costs what its one market costs.
    """
    held = markets(packed)
    if len(held) > 1 and not feed:
        raise SystemExit(f"{packed} tiene {len(held)} mercados ({', '.join(held)}): di cuál "
                         f"con --feed, o córrelo por mercado")
    filters = [("Sample type", "==", which)]
    filters += [("Symbol", "==", feed)] if held and feed else []
    filters += [("strategy", "==", strategy)] if strategy else []
    return pd.read_parquet(packed, filters=filters).reset_index(drop=True)


def sample(packed: Path, strategy: str, which: str, feed: str = "") -> pd.DataFrame:
    """One strategy's trades on one sample of its backtest.

    Args:
        packed: The `trades.parquet` an export wrote.
        strategy: Its name exactly as the export spells it.
        which: A value of the `Sample type` column -- "IST" in sample, "OOS1" out of it.
        feed: Its market, which an export of several markets needs (see trades()).

    Returns:
        That strategy's trades on that sample, in the order SQX reported them.
    """
    return trades(packed, which, feed, strategy)


def bars(feed: str, timeframe: str) -> pd.DataFrame:
    """The bars a strategy was priced on.

    Args:
        feed: The SQX feed name, e.g. "XAUUSD_DukasM1_Infinox".
        timeframe: "M30", "H1" and the rest; resampled from M1 and cached by barstore.

    Returns:
        One row per bar, indexed by open time.
    """
    return read_bars(feed, timeframe)


def on_grid(trades: pd.DataFrame, index: pd.DatetimeIndex, max_hold: int) -> dict:
    """Locate every trade on the bar grid, and refuse if one does not fit.

    Args:
        trades: One strategy's trades on one sample.
        index: The bars' open times.
        max_hold: barrier.max_hold, the ceiling on the forward scan.

    Returns:
        Keys `entry` and `exit` as bar indices, `hold` in bars, `size` in lots, and
        `window`, the first and last bar index the sample occupies.

    Raises:
        SystemExit: A hold exceeds the scan ceiling. Truncating it would silently price a
            different trade than the one SQX ran, and the whole reconciliation rests on
            that not happening.
    """
    entry = index.searchsorted(trades["Open time"].to_numpy())
    leave = index.searchsorted(trades["Close time"].to_numpy())
    hold = leave - entry
    if hold.max() > max_hold:
        raise SystemExit(f"nulls: un trade dura {hold.max()} barras y barrier.max_hold "
                         f"es {max_hold}; sube el techo en vez de truncar el trade")
    return {"entry": entry, "exit": leave, "hold": hold,
            "size": trades["Size"].to_numpy(np.float64),
            "window": (int(entry.min()), int(leave.max()))}


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
