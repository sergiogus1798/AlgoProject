"""What the study is run on: its knobs, one strategy's trades, and the bars they sat on."""

from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from core.barstore import read as read_bars
from core.paths import ROOT

CONFIG = ROOT / "nulls" / "config.yaml"


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


def sample(packed: Path, strategy: str, which: str) -> pd.DataFrame:
    """One strategy's trades on one sample of its backtest.

    Args:
        packed: The `trades.parquet` an export wrote.
        strategy: Its name exactly as the export spells it.
        which: A value of the `Sample type` column -- "IST" in sample, "OOS1" out of it.

    Returns:
        That strategy's trades on that sample, in the order SQX reported them.
    """
    frame = pd.read_parquet(packed)
    return frame[(frame["strategy"] == strategy) & (frame["Sample type"] == which)]


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
