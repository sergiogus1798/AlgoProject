"""One strategy's cumulative net result per account, from the closed trades of `history.trades()`; no Qt."""


def curves(accounts: list[dict], magic: int) -> list[dict]:
    """The cumulative net of this magic on each account that has traded it.

    Args:
        accounts: As `strategies.record()`: `login`, `name`, `size` (account size or None), `trades`.
        magic: The strategy's magic.

    Returns:
        Per account with a closed trade of the magic, oldest account first as given: `login`, `name`,
        `size`, `times` (server epochs: the first entry, then each close), `cum` (net after each trade,
        0 at the start), `pct` (`cum` in % of `size`; None without size), `trades`, `net`, `win_rate`
        and `max_dd` (largest fall from a peak of the curve, in % of `size`; None without size).
    """
    out = []
    for a in accounts:
        mine = sorted(
            (t for t in a["trades"] if t["magic"] == magic and t["close"]),
            key=lambda t: t["close"],
        )
        if not mine:
            continue
        cum, total = [0.0], 0.0
        for t in mine:
            total += t["net"]
            cum.append(total)
        size = a["size"]
        pct = [100 * c / size for c in cum] if size else None
        peak, dd = 0.0, 0.0
        for c in pct or []:
            peak, dd = max(peak, c), max(dd, peak - c)
        out.append(
            {
                "login": a["login"],
                "name": a["name"],
                "size": size,
                "times": [min(t["open"] for t in mine)] + [t["close"] for t in mine],
                "cum": cum,
                "pct": pct,
                "trades": len(mine),
                "net": total,
                "win_rate": sum(t["net"] > 0 for t in mine) / len(mine),
                "max_dd": dd if pct else None,
            }
        )
    return out


def combined(chosen: list[dict]) -> dict | None:
    """The sum of these curves as a step series over the union of their times.

    Each curve holds its last value between its own points and 0 before its first one. `pct` is the
    summed net over the summed sizes, None if any curve has no size.
    """
    if not chosen:
        return None
    times = sorted({t for c in chosen for t in c["times"]})

    def at(c: dict, t: int) -> float:
        """This curve's cumulative net at time `t`."""
        value = 0.0
        for x, y in zip(c["times"], c["cum"]):
            if x <= t:
                value = y
        return value

    cum = [sum(at(c, t) for c in chosen) for t in times]
    sizes = [c["size"] for c in chosen]
    total = sum(sizes) if all(sizes) else None
    return {
        "times": times,
        "cum": cum,
        "pct": [100 * x / total for x in cum] if total else None,
    }
