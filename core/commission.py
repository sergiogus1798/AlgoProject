"""The owner's most-restrictive-broker rule: one dollar figure, method-agnostic, for comparison."""


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


def most_restrictive(brokers: dict, prices: dict, point_value: float) -> dict:
    """Which confirmed broker charges most, and in which segment they disagree most.

    Owner's rule, 2026-09-29: a `%` broker and a `$/lot` broker cannot be read off directly
    against each other, so both are priced in dollars at each charged segment's own median
    price (`build`, `oos1`, `oos2`) and the segment where they disagree MOST decides — not
    the cheapest segment, which is the one least representative of the difference, and not a
    flat average, which would hide a segment where one broker is actually the worst.

    Args:
        brokers: `{name: {method, value, confirmed, ...}}`; entries with `confirmed` falsy
            (unconfirmed, or a figure the owner has not decided to apply) are ignored.
        prices: `{segment: median price}` over the window that segment charges.
        point_value: The asset's own `instrument.point_value`.

    Returns:
        `{"winner", "segment", "usd_per_lot", "by_segment": {segment: {broker: usd}}}`.

    Raises:
        ValueError: No broker is confirmed — nothing to compare, `use` stays as it was.
    """
    confirmed = {n: b for n, b in brokers.items() if b.get("confirmed")}
    if not confirmed:
        raise ValueError("ningún broker confirmado: nada que comparar")
    by_segment = {seg: {n: commission_usd(b["method"], b["value"], price, point_value)
                         for n, b in confirmed.items()}
                  for seg, price in prices.items()}
    segment = max(by_segment, key=lambda s: max(by_segment[s].values()) - min(by_segment[s].values()))
    winner = max(by_segment[segment], key=by_segment[segment].get)
    return {"winner": winner, "segment": segment, "usd_per_lot": by_segment[segment][winner],
            "by_segment": by_segment}


def use_value(data_class: str, result: dict, prices: dict, point_value: float) -> float:
    """The winning broker's cost, in the `use` field's own unit for this asset's class.

    Args:
        data_class: `"forex"` (`use` is $/lot flat) or `"no_forex"` (`use` is % of notional).
        result: What `most_restrictive()` returned.
        prices: The same `{segment: median price}` dict it was given.
        point_value: The asset's own `instrument.point_value`.

    Returns:
        Forex: the winning segment's dollar figure, unchanged — SQX's forex commission is
        one flat `SizeBased` value, not one per segment, so the segment that decided the
        winner is also the one that prices it.
        No_forex: that dollar figure turned back into a %, at the winning segment's own
        price — a `PercentageBased` winner comes back out at its own declared %, unchanged.
    """
    if data_class == "forex":
        return round(result["usd_per_lot"], 4)
    price = prices[result["segment"]]
    return round(result["usd_per_lot"] / (price * point_value) * 100, 6)
