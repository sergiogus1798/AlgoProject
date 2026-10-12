"""What an entry records about its authors' selection: whether their sample covers our build."""

import pandas as pd

from core import assetdata


def symbols(entry: dict, classes: dict[str, list[str]]) -> list[str]:
    """The assets an entry speaks of: the ones it names, else every asset of its classes."""
    every = [s for group in classes.values() for s in group]
    named = [s for s in every if s in str(entry["assets"])]
    return named or [s for k, v in classes.items() if k in str(entry["asset_class"])
                     for s in v] or every


def overlap(sample_from: int | None, sample_to: int | None, assets: list[str],
            segment: str = "build") -> str:
    """The `overlaps_is` line (`overlaps_oos1`, `overlaps_oos2`): the authors' sample years against
    one segment's windows of the assets.

    Args:
        sample_from, sample_to: First and last year of the paper's sample; None when the
            source does not state it.
        assets: Symbols of `assets/symbols/`.
        segment: `build`, `oos1` or `oos2`.

    Returns:
        "not stated in source" without both years; else yes, partly or no, with the years.
    """
    if sample_from is None or sample_to is None:
        return "not stated in source"
    try:
        spans = [assetdata.window(assetdata.load(s), segment) for s in assets]
    except ValueError:    # a segment whose dates are not decided yet
        return f"not decided: {segment} has no dates"
    lo = min(pd.Timestamp(a, unit="ms").year for a, _ in spans)
    hi = max((pd.Timestamp(b, unit="ms") - pd.Timedelta(days=1)).year for _, b in spans)
    ours = f"{segment} {lo}-{hi}"
    if sample_to < lo or sample_from > hi:
        return f"no: sample {sample_from}-{sample_to} is outside {ours}"
    if sample_from <= lo and sample_to >= hi:
        return f"yes, fully: sample {sample_from}-{sample_to} covers {ours}"
    return f"partly: sample {sample_from}-{sample_to} against {ours}"
