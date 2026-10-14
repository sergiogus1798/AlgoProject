"""What the open stops would cost: each position's loss at its SL and the equity if all of them hit."""

from typing import Any


LEVEL_TEXT = {"daily": "diario", "max": "total"}


def v2(beat: dict) -> bool:
    """Whether the beat carries the tick data schema 2 added."""
    return beat.get("schema", 1) >= 2


def position_loss(position: dict) -> float | None:
    """Account currency lost (negative) or locked in (positive) if this position's SL is hit.

    Args:
        position: A beat position of schema 2 (`tick_size`, `tick_value_loss`).

    Returns:
        None when the position has no SL.
    """
    if position["sl"] == 0:
        return None
    direction = 1 if position["side"] == "buy" else -1
    ticks = (
        (position["sl"] - position["price_current"]) * direction / position["tick_size"]
    )
    return ticks * position["tick_value_loss"] * position["volume"]


def reading(beat: dict, floor: dict | None) -> dict[str, Any]:
    """The account's stop risk.

    Args:
        beat: FleetBeacon's JSON.
        floor: `floors.reading()`, or None for an account with no plan.

    Returns:
        `losses` (one per position: a number, or None without SL or on a schema-1 beat),
        `no_sl` (positions with no SL, readable on any schema), `equity_at_stops` (None on schema 1;
        it leaves out the positions with no SL), and `breaks`: which floors it falls under
        ("daily", "max").
    """
    no_sl = sum(p["sl"] == 0 for p in beat["positions"])
    if not v2(beat):
        return {
            "losses": [None] * len(beat["positions"]),
            "no_sl": no_sl,
            "equity_at_stops": None,
            "breaks": [],
        }
    losses = [position_loss(p) for p in beat["positions"]]
    at_stops = beat["equity"] + sum(x for x in losses if x is not None)
    breaks = [k for k in ("daily", "max") if floor and at_stops < floor[f"{k}_floor"]]
    return {
        "losses": losses,
        "no_sl": no_sl,
        "equity_at_stops": at_stops,
        "breaks": breaks,
    }


def reasons(risk: dict) -> list[tuple[str, str]]:
    """The red reasons a stop risk gives, worst first, as (level, Spanish text)."""
    out = [
        ("red", f"Los stops romperían el suelo {LEVEL_TEXT[k]}") for k in risk["breaks"]
    ]
    if risk["no_sl"]:
        out.append(
            (
                "red",
                "Posición sin SL"
                if risk["no_sl"] == 1
                else f"{risk['no_sl']} posiciones sin SL",
            )
        )
    return out
