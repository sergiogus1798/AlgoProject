"""The eight kinds of block a study result is made of, built from raw numbers and checked."""

import json

import numpy as np

# The five words a block may colour itself with; the window's scale (ui/desktop/theme.py)
# has one colour per word and no other. MANTENER, FAIL or worth_it live in verdict.csv.
STATES = ("pass", "fail", "watch", "info", "none")

# Every key a block of each kind must carry, beyond "kind". Optional keys are not listed.
KINDS = {
    "distribution": ("title", "unit", "bins", "counts", "real", "median", "band",
                     "percentiles", "p", "note"),
    "cone": ("title", "unit", "x", "bands", "real", "split"),
    "grid": ("title", "rows", "cols", "values", "scale", "levels", "labels"),
    "scatter": ("title", "x_label", "y_label", "points", "quadrants", "fit"),
    "bars": ("title", "unit", "items", "reference"),
    "lines": ("title", "unit", "x", "series"),
    "table": ("title", "columns", "rows", "align", "note"),
    "verdict": ("label", "state", "score", "meaning", "parts"),
}
PERCENTILES = (1, 5, 10, 25, 50, 75, 90, 95, 99)
CONE_LEVELS = ("2.5", "25", "50", "75", "97.5")


def _num(value: float) -> float | None:
    """A float JSON can carry: NaN and infinities become None."""
    value = float(value)
    return value if np.isfinite(value) else None


def plain(value: object, digits: int | None = None) -> object:
    """Any nested structure made of what JSON can hold: numpy scalars unwrapped, NaN to None.

    Args:
        value: A dict, list, tuple, array, scalar or string.
        digits: Significant digits floats are rounded to; None keeps them whole. A drawing
            needs six, and seventeen made a strategy's result three times heavier.

    Returns:
        The same structure with plain Python leaves; dict keys become strings.
    """
    if isinstance(value, dict):
        return {str(k): plain(v, digits) for k, v in value.items()}
    if isinstance(value, (list, tuple, np.ndarray)):
        return [plain(v, digits) for v in value]
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    if isinstance(value, (int, np.integer)):
        return int(value)
    if isinstance(value, (float, np.floating)):
        v = _num(value)
        return v if v is None or digits is None else float(f"{v:.{digits}g}")
    return value


def thin(length: int, most: int = 400) -> list[int]:
    """Which positions of a long series a drawing keeps: evenly spaced, both ends included.

    Args:
        length: Points in the series.
        most: The most a line needs to look like itself; a trade-by-trade path of 5,000
            points draws the same at 400 and weighs twelve times less.

    Returns:
        Sorted indices, every one of them when the series is already short.
    """
    return sorted(set(np.linspace(0, length - 1, min(length, most)).astype(int).tolist()))


def distribution(title: str, unit: str, values: np.ndarray, real: float, note: str,
                 p: float | None = None, band: tuple[float, float] = (5, 95),
                 bins: int = 60) -> dict:
    """The null's distribution with the real value marked, aggregated from the raw draws.

    Args:
        title: What the reader is looking at, in Spanish.
        unit: "USD", "%", "R" or "".
        values: One statistic per simulated run; NaN runs are dropped.
        real: The observed value.
        note: One sentence saying how to read it.
        p: The test's p-value, when it has one.
        band: Percentiles bounding the shaded band.
        bins: Histogram bins over the draws' range, widened to include the real value.

    Returns:
        A "distribution" block. The draws never leave: only the histogram does.
    """
    v = np.asarray(values, dtype=float)
    v = v[np.isfinite(v)]
    lo, hi = min(v.min(), real), max(v.max(), real)
    counts, edges = np.histogram(v, bins=bins, range=(lo, hi if hi > lo else lo + 1))
    return {"kind": "distribution", "title": title, "unit": unit,
            "bins": [float(e) for e in edges], "counts": [int(c) for c in counts],
            "real": _num(real), "median": _num(np.median(v)),
            "band": [_num(np.percentile(v, band[0])), _num(np.percentile(v, band[1]))],
            "percentiles": {str(q): _num(np.percentile(v, q)) for q in PERCENTILES},
            "p": None if p is None else _num(p), "note": note}


def cone(title: str, unit: str, x: list, paths: np.ndarray, real: list,
         split: str | None = None) -> dict:
    """An equity cone with the real curve on top, aggregated from simulated paths.

    Args:
        title: What the reader is looking at.
        unit: Unit of the curve.
        x: One label per point: ISO dates, or progress 0..100.
        paths: Simulated curves, shape (runs, len(x)).
        real: The observed curve, len(x).
        split: Where the out-of-sample starts, if it does.

    Returns:
        A "cone" block carrying five percentiles per point, never the runs.
    """
    q = np.percentile(np.asarray(paths, dtype=float), [float(c) for c in CONE_LEVELS], axis=0)
    return {"kind": "cone", "title": title, "unit": unit, "x": list(x),
            "bands": {c: [_num(v) for v in row] for c, row in zip(CONE_LEVELS, q)},
            "real": [_num(v) for v in real], "split": split}


def verdict(label: str, state: str, meaning: str, score: float | None = None,
            parts: list[dict] | None = None) -> dict:
    """A categorical call and the sentence that explains it — the label is never shown alone.

    Args:
        label: The word as the module says it.
        state: One of STATES.
        meaning: What the label means.
        score: A composite score, where the module has one.
        parts: {"label", "state", "value", "note"} per family or gate that made the call.

    Returns:
        A "verdict" block.
    """
    return {"kind": "verdict", "label": label, "state": state, "score": score,
            "meaning": meaning, "parts": parts or []}


def table(title: str, frame: object, note: str = "", digits: int = 4) -> dict:
    """A table block from a DataFrame, numbers right-aligned and rounded.

    Args:
        title: What the table shows.
        frame: A pandas DataFrame; its index is dropped, so reset it first if it matters.
        note: One sentence under it.
        digits: Rounding for floats.

    Returns:
        A "table" block.
    """
    def cell(v: object) -> object:
        """One cell, JSON-safe."""
        if isinstance(v, (bool, np.bool_)):
            return bool(v)
        if isinstance(v, (int, np.integer)):
            return int(v)
        if isinstance(v, (float, np.floating)):
            return None if not np.isfinite(v) else round(float(v), digits)
        return None if v is None else str(v)

    numeric = [str(t).startswith(("int", "float")) for t in frame.dtypes]
    return {"kind": "table", "title": title, "columns": [str(c) for c in frame.columns],
            "rows": [[cell(v) for v in row] for row in frame.itertuples(index=False)],
            "align": ["right" if n else "left" for n in numeric], "note": note}


def _check(block: dict, where: str) -> None:
    """Refuse a block of an unknown kind, a missing key or a sixth state word."""
    kind = block["kind"]
    if kind not in KINDS:
        raise ValueError(f"{where}: kind {kind!r} is not one of the eight; ask before adding")
    missing = [k for k in KINDS[kind] if k not in block]
    if missing:
        raise ValueError(f"{where}: {kind} lacks {missing}")
    states = [block.get("state")] + [i.get("state") for i in block.get("items", [])
                                     + block.get("parts", [])]
    wrong = {s for s in states if s is not None and s not in STATES}
    if wrong:
        raise ValueError(f"{where}: state {wrong} is not one of {STATES}")


def validate(result: dict) -> dict:
    """Check a whole study result against the contract and that it serialises as JSON.

    Args:
        result: What a module's one.run() or many.run() returned.

    Returns:
        The same result, so the call can wrap the return statement.
    """
    if result.get("verdict"):
        _check(result["verdict"], "verdict")
    for tab in result["tabs"]:
        for i, block in enumerate(tab["blocks"]):
            _check(block, f"{tab['name']}[{i}]")
    for w in result.get("warnings", []):
        if w["state"] not in STATES:
            raise ValueError(f"warning {w['code']}: state {w['state']!r}")
    json.dumps(result, allow_nan=False)
    return result
