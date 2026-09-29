"""The owner's most-restrictive-broker rule: one winner PER SEGMENT, in its own method and value."""


def commission_usd(method: str, value: float, price: float, point_value: float) -> float:
    """One broker's round-turn commission on a single 1.0-lot trade, in dollars.

    Args:
        method: `"SizeBased"` (value already $/lot) or `"PercentageBased"` (value is a %).
        value: The broker's own figure, in its own unit.
        price: The instrument's price the trade opens at.
        point_value: `$` per 1.0 of price and 1.0 of lot (the asset's `instrument.point_value`).

    Returns:
        Dollars per lot, round turn — the two methods' common currency for comparison.
    """
    return value if method == "SizeBased" else value / 100 * price * point_value


def per_segment(brokers: dict, prices: dict, point_value: float) -> dict:
    """The most expensive confirmed broker in EACH segment, kept in its own method and value.

    Owner's rule, 2026-09-29 — "aplica el máximo de cada a la hora de buildear y testear":
    SQX takes one commission method per task, and a project prices each segment's task on
    its own (`build`, `oos1`, `oos2`), so the winner is picked separately in each one rather
    than at the single segment where brokers disagree most. A `%` broker and a `$/lot` broker
    cannot be read off directly against each other, so both are priced in dollars at that
    segment's own median price first — but the winner is written back in ITS OWN method and
    value, never converted: gold's build can carry Infinox's `SizeBased 8` while its oos2
    carries Darwinex's `PercentageBased 0.005`, because that is what SQX's `<Setup>` for
    each of those tasks actually charges.

    Args:
        brokers: `{name: {method, value, confirmed, ...}}`; entries with `confirmed` falsy
            (unconfirmed, or a figure the owner has not decided to apply) are ignored.
        prices: `{segment: median price}` over the window that segment charges. A segment
            need not carry a real price when every confirmed broker is `SizeBased` (the
            price cancels out of the comparison); it still requires an entry to know which
            segments to produce.

    Returns:
        `{segment: {"broker", "method", "value", "usd_per_lot"}}`, one entry per key of
        `prices`. `usd_per_lot` is only the figure the comparison was decided on; `method`
        and `value` are the winner's own, ready to write into that segment's `<Setup>`.

    Raises:
        ValueError: No broker is confirmed — nothing to compare, `use` stays as it was.
    """
    confirmed = {n: b for n, b in brokers.items() if b.get("confirmed")}
    if not confirmed:
        raise ValueError("ningún broker confirmado: nada que comparar")
    out = {}
    for seg, price in prices.items():
        usd = {n: commission_usd(b["method"], b["value"], price, point_value)
               for n, b in confirmed.items()}
        winner = max(usd, key=usd.get)
        out[seg] = {"broker": winner, "method": confirmed[winner]["method"],
                    "value": confirmed[winner]["value"], "usd_per_lot": round(usd[winner], 4)}
    return out
