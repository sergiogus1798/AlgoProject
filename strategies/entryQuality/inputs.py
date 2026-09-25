"""What the study is run on: its knobs, one strategy's trades, and the bars under them."""

from pathlib import Path

import numpy as np
import pandas as pd

from core.study import config as study_config
from core.trades import SIDE
from nulls import calibrate, inputs as nullinputs

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


def located(packed: Path, strategy: str, cfg: dict, frame: pd.DataFrame) -> dict:
    """One strategy's trades placed on the bar grid, with everything priced off it.

    Args:
        packed: The `trades.parquet` an export wrote.
        strategy: Its name exactly as the export spells it.
        cfg: The `run` block of config.yaml.
        frame: The bars of the timeframe the strategy was built on.

    Returns:
        `trades`, `entry` bar index, `side` as +1/-1, `atr` at entry, `point_value` and
        `charged` per trade.

        ⚠️ The ATR is read at the bar **before** the entry. Taking it on the entry bar
        itself would fold that bar's own high and low into the scale every excursion is
        divided by, which is information the entry did not have.
    """
    trades = nullinputs.sample(packed, strategy, cfg["sample"]).sort_values("Open time")
    trades = trades.reset_index(drop=True)
    entry = frame.index.searchsorted(trades["Open time"].to_numpy())
    value = calibrate.point_value(trades)
    scale = calibrate.atr(frame, cfg["atr"])
    return {"trades": trades, "entry": entry,
            "side": trades["Type"].map(SIDE).to_numpy(np.float64),
            "atr": scale[entry - 1], "point_value": value,
            "charged": calibrate.charged(trades, value),
            "size": trades["Size"].to_numpy(np.float64)}


def usable(found: dict, horizon: int, bars: int) -> np.ndarray:
    """Which trades have a full forward path inside the data and a defined ATR.

    Args:
        found: What `located` returned.
        horizon: The longest forward walk the study takes, in bars.
        bars: How many bars the frame holds.

    Returns:
        A boolean mask. A trade whose path runs off the end of the data would have its
        excursions cut short at a different k than every other trade, and the curve would
        then mix horizons without saying so.
    """
    return (found["entry"] + horizon < bars) & np.isfinite(found["atr"])
