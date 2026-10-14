"""The values each parameter may take: the plateau for the live ones, a rebuilt range for the frozen."""

import numpy as np

SHIFT = "shift1"


def live(design: dict) -> dict[str, list[float]]:
    """The values each LIVE parameter may take: its plateau on the in-sample SPP, nothing wider.

    Args:
        design: A parsed brief; each parameter carries `class` (live, shift) and `plateau`.

    Returns:
        Parameter name to its values, ascending. An integer parameter takes EVERY integer of
        `[plateau.from, plateau.to]`; a decimal one the brief's own levels inside it, with
        both ends. A shift is not here: it is fixed at the mother's value in every variant.
        The box is drawn from the build window only (hard rule of the proposal, §2.1).
    """
    out = {}
    for p in design["parameters"]:
        if p["class"] != "live":
            continue
        lo, hi = float(p["plateau"]["from"]), float(p["plateau"]["to"])
        if all(float(x).is_integer() for x in (p["original"], lo, hi)):
            out[p["name"]] = [float(v) for v in range(int(lo), int(hi) + 1)]
        else:
            inside = {float(v) for v in p["levels"] if lo <= v <= hi}
            out[p["name"]] = sorted(inside | {lo, hi})
    return out


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
        if (
            item["name"].lower().endswith(SHIFT)
        ):  # owner, 2026-09-26: a shift never moves
            out[item["name"]] = [value]
            continue
        span = np.linspace(
            value * (1 - settings["span"]),
            value * (1 + settings["span"]),
            settings["steps"],
        )
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
