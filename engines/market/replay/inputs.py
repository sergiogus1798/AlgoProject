"""A stop harvest made ready to replay: its trades on their bar grid, each with its stop's ATR multiple."""

import json
from pathlib import Path
from typing import TypedDict

import numpy as np
import pandas as pd

from core import barstore
from engines.market import reprice

SEGMENT = {"IS": "build", "OOS": "oos1"}


class Ready(TypedDict):
    """Everything `walk.replay` and `reconcile.reconcile` take, for one harvest."""

    bars: pd.DataFrame
    trades: (
        pd.DataFrame
    )  # the harvest's rows plus enter, leave, side, offset, coef, cap, slippage
    feed: str
    timeframe: str


def coefs(folder: Path) -> pd.Series:
    """Each identity's stop multiple, from the variant batch the harvest's manifest names.

    Args:
        folder: A `harvest/<P>/Stop_p90/<day>` folder (the step-24 grafted-stop harvest).

    Returns:
        ATR multiple by identity. Raises when the manifest names no batch: a harvest without
        a grafted stop has no stop to replay.
    """
    source = json.loads((folder / "manifest.json").read_text())["source"]
    if "batch" not in source or "variants" not in source:
        raise ValueError(
            f"{folder}/manifest.json names no stop batch: not a Stop_p90 harvest"
        )
    batch = pd.read_parquet(Path(source["batch"]) / "manifest.parquet").set_index(
        "variant_id"
    )
    names = pd.read_parquet(folder / "metrics.parquet", columns=["strategy"])[
        "strategy"
    ]
    variant = pd.Series(names).map(pd.Series(source["variants"]))
    return pd.Series(variant).map(pd.Series(batch["x"])).astype(float)


def ready(folder: Path) -> Ready:
    """One stop harvest on its strategies' own timeframe, every trade located on the bar grid.

    Args:
        folder: A `harvest/<P>/Stop_p90/<day>` folder.

    Returns:
        Bars and trades; `offset` is SQX's fill minus the entry bar's open (the entry offset
        measured per trade), `cap` the strategy's longest trade in bars, `slippage` and `tick`
        the segment's, in price, at today's asset card.
    """
    source = json.loads((folder / "manifest.json").read_text())["source"]
    feed = source["feed"]
    timeframe = str(
        pd.read_parquet(folder / "metrics.parquet", columns=["TimeFrame [IS]"]).iloc[
            0, 0
        ]
    )
    bars = barstore.read(feed, timeframe)
    t = pd.read_parquet(folder / "trades.parquet")
    coef = coefs(folder)
    if coef.isna().any():
        raise ValueError(
            f"{folder}: {coef.isna().sum()} strategies with no stop multiple in the batch"
        )
    t["enter"] = reprice.located(bars, t["Open time"].to_numpy(), feed)
    t["leave"] = reprice.located(bars, t["Close time"].to_numpy(), feed)
    if ((t["enter"] < 1) | (t["leave"] < 0)).any():
        raise ValueError(
            f"{folder}: trades off the bar grid; sync the bars (python3 -m sqx.export.sync_bars)"
        )
    kinds = set(t["Type"].astype(str))
    if not kinds <= {"Buy", "Sell"}:
        raise ValueError(
            f"{folder}: trade Type {sorted(kinds - {'Buy', 'Sell'})} is neither Buy nor Sell"
        )
    t["side"] = np.where(t["Type"].astype(str) == "Sell", -1.0, 1.0)
    t["offset"] = t["Open price"].to_numpy() - bars["Open"].to_numpy()[t["enter"]]
    t["coef"] = pd.Series(t["identity"]).map(pd.Series(coef)).to_numpy()
    t["cap"] = (t["leave"] - t["enter"]).groupby(t["identity"]).transform("max")
    card = {s: reprice.costs(feed, seg) for s, seg in SEGMENT.items()}
    t["slippage"] = (
        pd.Series(t["sample"])
        .map(pd.Series({s: c["slippage"] for s, c in card.items()}))
        .astype(float)
    )
    t["tick"] = (
        pd.Series(t["sample"])
        .map(
            pd.Series(
                {s: c.get("tick_step") or c["tick_size"] for s, c in card.items()}
            )
        )
        .astype(float)
    )
    return {"bars": bars, "trades": t, "feed": feed, "timeframe": timeframe}
