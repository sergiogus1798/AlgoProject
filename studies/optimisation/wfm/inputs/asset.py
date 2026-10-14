"""The asset a WFM export traded: its bars, its three segments, the two cost cards and the drift term."""

from pathlib import Path
from typing import Any, TypedDict

import pandas as pd
import yaml

from core import assetdata, barstore
from engines.market import reprice

SEGMENTS = ("build", "oos1", "oos2")
CLEAN = "oos2"  # the only segment nobody used to choose anything
# The excess is step 14's: the gate's drift block, never a copy of its values.
GATE = Path(__file__).resolve().parents[3] / "screening" / "gate" / "config.yaml"


class Asset(TypedDict):
    """The asset behind one feed: bars, segment windows, the span, two cost cards and the drift."""

    name: str | None
    feed: str
    bars: pd.DataFrame
    windows: dict[str, tuple[str, str]]
    span: tuple[str, str]
    charged: reprice.Costs
    real: reprice.Costs
    drift: Any


def of(feed: str, timeframe: str, charged: str) -> Asset:
    """Everything the measures need about the asset behind one SQX feed.

    Args:
        feed: The trades' `Symbol`, e.g. "NIKKEI225_M1".
        timeframe: The strategies' own, e.g. "M30".
        charged: The segment whose costs the export's task was charged with.

    Returns:
        `name`, `feed`, `bars` (the whole file), `windows` (segment -> (first day, last day)
        as full dates, both inside), `span` (the first day of `build` and the last of `oos2`,
        the bars the drift is measured on), `charged` and `real` (`reprice.costs` of the
        charged segment and of `oos2`) and `drift`, the gate's block.
    """
    name = assetdata.symbol_of(feed)
    data = assetdata.load(name)
    windows: dict[str, tuple[str, str]] = {}
    for name in SEGMENTS:
        last = data["segments"][name]["to"]
        windows[name] = (
            assetdata.segment_start(data, name),
            f"{last}-12-31" if isinstance(last, int) else str(last),
        )
    return {
        "name": name,
        "feed": feed,
        "bars": barstore.read(feed, timeframe),
        "windows": windows,
        "span": (windows[SEGMENTS[0]][0], windows[CLEAN][1]),
        "charged": reprice.costs(feed, charged),
        "real": reprice.costs(feed, CLEAN),
        "drift": yaml.safe_load(GATE.read_text(encoding="utf-8"))["drift"],
    }
