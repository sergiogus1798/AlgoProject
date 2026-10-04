"""The optional keys of a block: a distribution's series and shift, a grid's mark and scale."""

import numpy as np


def extensions(block: dict, where: str) -> None:
    """Check the optional keys: a distribution's series and shift, a grid's mark and scale."""
    if block["kind"] == "distribution":
        width = np.diff(block["bins"])
        for s in block.get("series", []):
            if {"label", "counts", "n", "median"} - set(s) or len(s["counts"]) != len(width):
                raise ValueError(f"{where}: series {s.get('label')!r} malformed")
            if abs(float(np.dot(s["counts"], width)) - 1) > 1e-3:
                raise ValueError(f"{where}: series {s['label']!r} is not a density of area 1")
        if block.get("shift") is not None and {"median", "ks_p"} - set(block["shift"]):
            raise ValueError(f"{where}: shift lacks median or ks_p")
    if block["kind"] == "grid":
        mark, span = block.get("mark"), block.get("scale_range")
        if mark is not None and (mark["row"] not in block["rows"]
                                 or mark["col"] not in block["cols"] or "label" not in mark):
            raise ValueError(f"{where}: mark {mark} is not a cell of the grid")
        if span is not None and not (len(span) == 2 and span[0] < span[1]):
            raise ValueError(f"{where}: scale_range {span} is not [lo, hi]")
