"""The values each parameter may take: the brief's own for the live ones, a rebuilt range for the frozen."""

import numpy as np

SHIFT = "shift1"


def live(design: dict, minimum: dict) -> dict[str, list[float]]:
    """The values each parameter that moves the result may take.

    Args:
        design: A parsed brief.
        minimum: The `minimum` block of `config.yaml`: `variants`, `widen_step`, `max_span`.

    Returns:
        Parameter name to its values, ascending. An integer parameter takes EVERY integer
        across the brief's span (at least +/-30 %, never narrowed), not only the brief's
        nine levels — a period 14..26 is thirteen values, not nine. A decimal one keeps the
        brief's levels. If the product still holds fewer than `minimum["variants"]` tuples,
        the integer spans widen symmetrically around the original, `widen_step` at a time,
        up to `max_span` (owner, 2026-09-26: never fewer than a thousand variants).
    """
    briefed = {p["name"]: (float(p["original"]), sorted(float(v) for v in p["levels"]))
               for p in design["parameters"]}
    integral = {n for n, (_, v) in briefed.items() if all(x.is_integer() for x in v)}

    def fill(span: float) -> dict[str, list[float]]:
        """Every parameter's values with the integer spans at least +/-`span` of the original."""
        out = {}
        for name, (origin, values) in briefed.items():
            if name not in integral or len(values) == 1:
                out[name] = values
                continue
            lo = min(values[0], np.floor(origin * (1 - span)))
            hi = max(values[-1], np.ceil(origin * (1 + span)))
            out[name] = [float(v) for v in range(int(max(lo, 1)), int(hi) + 1)]
        return out

    span = 0.0
    got = fill(span)
    while (np.prod([len(v) for v in got.values()]) < minimum["variants"]
           and span < minimum["max_span"] and integral):
        span = round(span + minimum["widen_step"], 6)
        got = fill(span)
    return got


def frozen(design: dict, settings: dict) -> dict[str, list[float]]:
    """Levels for the parameters the brief froze, rebuilt the way SQX builds its own.

    Args:
        design: A parsed brief.
        settings: The `design.frozen` block of `config.yaml`.

    Returns:
        Parameter name to levels. The brief gives a frozen parameter a value and no
        range, because the duplicate test proved it never moved a backtest. The coverage
        stratum varies it anyway, and needs somewhere to vary it to.

        The range is the one SQX uses for its own permutations, measured and recorded in
        `knowhow/sqx-format/declared-parameters.md`: +/-30 % of the value stepped and rounded, except a
        shift, which stays at its value (owner, 2026-09-26). Confirmed final by the owner
        (OPEN.md §23, 2026-09-29): not an open assumption. Rounding follows the value:
        integral in, integral out.
    """
    out = {}
    for item in design["frozen"]:
        value = float(item["value"])
        if item["name"].lower().endswith(SHIFT):   # owner, 2026-09-26: a shift never moves
            out[item["name"]] = [value]
            continue
        span = np.linspace(value * (1 - settings["span"]), value * (1 + settings["span"]),
                           settings["steps"])
        digits = 0 if float(value).is_integer() else 2
        out[item["name"]] = sorted({round(float(v), digits) for v in span})
    return out


def origin(design: dict) -> dict[str, float]:
    """The tuple the parent strategy was built with, over every parameter of the design.

    Args:
        design: A parsed brief.

    Returns:
        Name to value, live parameters and frozen ones together. It anchors the whole
        batch: it is the one variant the deletion stage refuses to touch, and the one
        whose result the inert pairs have to reproduce.
    """
    values = {p["name"]: float(p["original"]) for p in design["parameters"]}
    values.update({f["name"]: float(f["value"]) for f in design["frozen"]})
    return values


def nearest(values: list[float], target: float) -> int:
    """Index of the level closest to a value.

    Args:
        values: One parameter's levels, ascending.
        target: The value to locate.

    Returns:
        Position in `values`. Ties go to the lower level, which keeps the choice
        deterministic rather than dependent on floating-point noise.
    """
    return int(np.argmin([abs(v - target) for v in values]))


def centre(design: dict, levels: dict[str, list[float]]) -> dict[str, int]:
    """Where the dense stratum is centred, as an index per parameter.

    Args:
        design: A parsed brief.
        levels: Output of `live`.

    Returns:
        Parameter name to level index. The brief's `center` is the midpoint of the
        in-sample plateau, which need not be one of the levels, so it is snapped to the
        nearest one.
    """
    return {p["name"]: nearest(levels[p["name"]], float(p["center"]))
            for p in design["parameters"]}


def weights(design: dict) -> dict[str, float]:
    """How much variance each live parameter explains.

    Args:
        design: A parsed brief.

    Returns:
        Parameter name to eta-squared. The coarse factorial spends its budget in this
        order, so the parameter that decides the result is resolved finely and the one
        that barely moves it gets its two ends and nothing more.
    """
    return {p["name"]: float(p["eta2"]) for p in design["parameters"]}
