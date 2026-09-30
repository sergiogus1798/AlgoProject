"""Every colour a block is painted in: the contract states, the series and the heat scales."""

from ui.desktop.theme import C, T

# The data says `state`; only this file says what colour that is (core/study/CONTRACT.md §2).
STATE_COLOUR = {"pass": C["promising"], "fail": C["dead"], "watch": C["weak"],
                "info": C["accent"], "none": C["pending"], "stale": C["faint"],
                "missing": C["untried"]}
STATE_LABEL = {"pass": "pasa", "fail": "falla", "watch": "vigilar", "info": "informa",
               "none": "sin juicio", "stale": "caducado", "missing": "no corrido"}


def colour(state: str) -> str:
    """The colour of one state, grey for anything the contract does not name.

    Args:
        state: One of the contract's five words, `stale` or `missing`.

    Returns:
        A hex colour.
    """
    return STATE_COLOUR.get(state, C["pending"])


def label(state: str) -> str:
    """The Spanish word for one state, the raw value quoted when it is unknown.

    Args:
        state: As in `colour`.

    Returns:
        The word the window prints.
    """
    return STATE_LABEL.get(state, f"«{state}»")


# What a chart paints, beside the states. The simulated mass is the accent, the real run is
# the brightest ink on the black ground and drawn thickest: the one line the eye must find.
SIM = C["accent"]
REAL = T["text"]
MEDIAN = T["muted"]
# Series with no state of their own: fixed order, never green, red or amber (those are verdicts).
SERIES = ("#4c8dff", "#f28e2b", "#b07aff", "#2ec4d6", "#ff7eb6", "#e6e6e6")
# Discrete heat scales, nine steps. Diverging runs red (low) to blue (high) through a pale
# middle, so a negative cell never reads as the green of a pass; sequential is one hue.
DIVERGING = ("#b2182b", "#d6604d", "#f4a582", "#fddbc7", "#f7f7f7",
             "#d1e5f0", "#92c5de", "#4393c3", "#2166ac")
SEQUENTIAL = ("#f7fbff", "#deebf7", "#c6dbef", "#9ecae1", "#6baed6",
              "#4292c6", "#2171b5", "#08519c", "#08306b")
# One strategy's curves, IS and OOS in two tones of one family (owner, 2026-09-28): violet is
# SQX's own curve, orange → red the one at the real spread and slippage. A lines series or a
# bar item names one of these keys as `ink`; the Estrategia page's equity reads the same map.
CURVE = {"sqx.IS": "#8a7dff", "sqx.OOS": "#e2a6ff", "real.IS": "#f28e2b", "real.OOS": "#ff4d5e"}
