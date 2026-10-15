"""What the study is run on: its knobs, one strategy's trades, and the bars under them."""

import json
from pathlib import Path
from typing import Any, cast, TypedDict

import numpy as np
import pandas as pd

from core.study import config as study_config
from ledger import thresholds
from core.trades import SIDE
from engines.market import calibrate
from engines.market.replay import inputs as replay
from engines.nulls import inputs as nullinputs

CONFIG = Path(__file__).with_name("config.yaml")


def config(overrides: list[str]) -> dict[str, Any]:
    """The study's knobs, with command-line overrides applied.

    Args:
        overrides: Dotted `section.key=value` strings, as `--set` passes them; each keeps
            the type of the value it replaces (core.study.config).

    Returns:
        What config.yaml holds, each `ledger:<key>` replaced by the number
        `ledger/thresholds.yaml` declares.
    """
    return study_config.apply(thresholds.fill(study_config.load(CONFIG, [])), overrides)


class Located(TypedDict):
    """One strategy's trades on the bar grid: the frame, entry bar, side, ATR, size and cost bases."""

    trades: pd.DataFrame
    entry: np.ndarray
    side: np.ndarray
    atr: np.ndarray
    point_value: float
    charged: np.ndarray
    size: np.ndarray


SAMPLE = {"IST": "IS", "OOS1": "OOS"}  # `Sample type` -> the harvest's `sample`


def stopped(packed: Path) -> replay.Ready | None:
    """The replay-ready harvest when `packed` is a grafted-stop harvest, None for any other export.

    Args:
        packed: The `trades.parquet` an export or a harvest wrote.

    Returns:
        A strategy with a stop is read by tier 2, which needs the stop's ATR multiple, only
        a `Stop_p90` harvest carries it: so an export that has SL exits and is not one raises
        (a tier 1 delay would hold the stop where it was and overstate the result).
    """
    note = packed.parent / "manifest.json"
    if note.exists() and "variants" in json.loads(note.read_text()).get("source", {}):
        return replay.ready(packed.parent)
    if packed.exists() and "SL" in set(
        pd.read_parquet(packed, columns=["Close type"])["Close type"]
    ):
        raise ValueError(
            f"{packed}: trades closed by a stop in an export that is no Stop_p90 harvest; "
            f"the delay of a stop needs the harvest (engines/market/replay)"
        )
    return None


def located(
    packed: Path,
    strategy: str,
    cfg: dict,
    frame: pd.DataFrame,
    harvest: replay.Ready | None = None,
) -> Located:
    """One strategy's trades placed on the bar grid, with everything priced off it.

    Args:
        packed: The `trades.parquet` an export wrote.
        strategy: Its name exactly as the export spells it.
        cfg: The `run` block of config.yaml.
        frame: The bars of the timeframe the strategy was built on.
        harvest: What `stopped` returned; the strategy's rows are then read from it.

    Returns:
        `trades`, `entry` bar index, `side` as +1/-1, `atr` at entry, `point_value` and
        `charged` per trade.

        ⚠️ The ATR is read at the bar **before** the entry. Taking it on the entry bar
        itself would fold that bar's own high and low into the scale every excursion is
        divided by, which is information the entry did not have.
    """
    if harvest is None:
        trades = nullinputs.sample(packed, strategy, cfg["sample"])
    else:
        names = pd.read_parquet(packed.parent / "metrics.parquet", columns=["strategy"])
        rows = harvest["trades"]
        mine = (rows["identity"] == names.index[names["strategy"] == strategy][0]) & (
            rows["sample"] == SAMPLE[cfg["sample"]]
        )
        trades = rows.loc[mine]
    trades = trades.sort_values("Open time")
    trades = trades.reset_index(drop=True)
    entry = np.maximum(
        frame.index.searchsorted(trades["Open time"].to_numpy(), side="right") - 1, 0
    )
    value = calibrate.point_value(trades)
    scale = calibrate.atr(frame, cfg["atr"])
    return {
        "trades": trades,
        "entry": entry,
        "side": trades["Type"].map(cast("Any", SIDE)).to_numpy(np.float64),
        "atr": scale[entry - 1],
        "point_value": value,
        "charged": calibrate.charged(trades, value),
        "size": trades["Size"].to_numpy(np.float64),
    }


def usable(found: Located, horizon: int, bars: int) -> np.ndarray:
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
