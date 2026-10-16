"""Step 8 writes a missing `price_rounding` from the build's trades (tie -> tick) and leaves a present one alone."""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import assetdata, assetwrite
from engines.market import rounding
from studies.screening.gate import inputs


def test_missing_rounding_is_measured_and_written() -> None:
    """A card without the field: measured on the IS trades only, a tie written as tick with its why."""
    saved = (assetdata.load, rounding.measure, assetwrite.set_price_rounding)
    card: dict = {}
    seen: list = []
    assetdata.load = lambda s: card
    rounding.measure = lambda s, t, seg, tf: (
        seen.append((s, set(t["sample"]), seg, tf)) or {"use": None, "why": "x"}
    )
    assetwrite.set_price_rounding = lambda s, u, w: card.update(
        price_rounding={"use": u, "why": w}
    )
    trades = pd.DataFrame(
        {"sample": ["IS", "OOS"], "identity": ["a", "a"], "Type": ["Buy", "Buy"]}
    )
    try:
        inputs.ensure_rounding("EURUSD_M1", trades, "M30")
        inputs.ensure_rounding(
            "EURUSD_M1", trades, "M30"
        )  # present now: no second measurement
    finally:
        assetdata.load, rounding.measure, assetwrite.set_price_rounding = saved
    assert seen == [("EURUSD", {"IS"}, "build", "M30")], seen
    assert (
        card["price_rounding"]["use"] == "tick"
        and "tie" in card["price_rounding"]["why"]
    )


if __name__ == "__main__":
    test_missing_rounding_is_measured_and_written()
    print("test_gate_rounding: ok")
