"""The map of spent data: which stretches of history a search has already looked at."""

from typing import Any

import pandas as pd

from core import assetdata


def by_segment(frame: pd.DataFrame) -> pd.DataFrame:
    """One row per segment read: a search over "oos1+oos2" (step 26) counts in each part."""
    return frame.assign(segment=frame["segment"].str.split("+")).explode("segment")


def spent(frame: pd.DataFrame) -> pd.DataFrame:
    """How many times each segment has been read, and by which steps.

    Args:
        frame: What `study.read` returned.

    Returns:
        One row per segment: searches, distinct steps, and the first and last time it was
        read. A segment read twenty times is not out-of-sample any more, whatever it is
        called in the config.
    """
    if not len(frame):
        return pd.DataFrame(columns=pd.Index(["segment", "searches", "steps", "first", "last"]))
    grouped = by_segment(frame).groupby("segment")
    return pd.DataFrame({"searches": grouped.size(),
                         "steps": grouped["step"].apply(lambda s: sorted(set(s))),
                         "first": grouped["ts"].min(),
                         "last": grouped["ts"].max()}).reset_index()


def virgin(frame: pd.DataFrame, symbol: str) -> dict[str, dict[str, Any]]:
    """What is left untouched of this asset's history.

    Args:
        frame: What `study.read` returned.
        symbol: The asset, for its declared segments.

    Returns:
        Every segment with its window and how many times it has been read -- zero being
        the interesting value. It is the only way to answer "is the holdout still a
        holdout", and the answer stops being yes silently.
    """
    segments = assetdata.load(symbol)["segments"]
    counts = by_segment(frame)["segment"].value_counts().to_dict() if len(frame) else {}
    return {name: {"from": str(spec["from"]), "to": str(spec["to"]),
                   "reads": int(counts.get(name, 0)),
                   "reserved_for": spec.get("reserved_for")}
            for name, spec in segments.items()}
