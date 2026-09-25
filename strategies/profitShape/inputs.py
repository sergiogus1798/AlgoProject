"""What the study is run on: its knobs and one strategy's trades on one sample."""

from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from core.paths import ROOT
from nulls import inputs as nullinputs

CONFIG = ROOT / "strategies" / "profitShape" / "config.yaml"


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


def stream(packed: Path, strategy: str, sample: str) -> dict:
    """One strategy's trades in time order, with the three arrays every test reads.

    Args:
        packed: The `trades.parquet` an export wrote.
        strategy: Its name exactly as the export spells it.
        sample: A value of the `Sample type` column -- "IST", "OOS1".

    Returns:
        `trades` sorted by entry time, `pnl` net per trade, `wins`, and `daily`, the same
        P&L summed per calendar day for the tests that have to run in calendar time.

        Sorted by entry time and not left in SQX's order: the runs test and the CUSUM are
        statements about a sequence, and a sequence in the wrong order is a different
        statement. SQX does report them in order; sorting makes that not matter.
    """
    frame = nullinputs.sample(packed, strategy, sample).sort_values("Open time")
    pnl = frame["Profit/Loss"].to_numpy(np.float64)
    stamped = pd.Series(pnl, index=pd.DatetimeIndex(frame["Open time"]))
    return {"trades": frame.reset_index(drop=True), "pnl": pnl, "wins": pnl > 0,
            "daily": stamped.groupby(pd.Grouper(freq="D")).sum()}
