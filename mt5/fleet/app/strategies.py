"""Live strategies across the whole fleet: each magic's record, and whether the same magic entered together on every account."""

from mt5.fleet.app import eas, floors, fmt, history, read


def accounts(rows: list[dict]) -> list[dict]:
    """The fleet's accounts as `record()` and `pairing()` read them: only those whose history the collector has."""
    return [
        {
            "login": r["beat"]["login"],
            "label": fmt.who(r["beat"], r["stage"]),
            "name": fmt.firm_phase(r["stage"])
            if r["stage"]
            else fmt.who(r["beat"], None),
            "size": r["stage"]["size"] if r["stage"] else None,
            "offset": floors.server_offset(r["beat"]),
            "trades": history.trades(r["deals"]),
            "excursions": history.excursions(r["beat"]["login"]),
        }
        for r in rows
        if r["deals"] is not None
    ]


def label(magic: int, comments: dict[int, str], register: dict[int, str]) -> str:
    """A magic's strategy: the reconciler's register, else the name in its trades' comments, else the magic."""
    return (
        eas.strategy_key(register[magic])
        if magic in register
        else comments.get(magic, f"magic {magic}")
    )


def record(accounts: list[dict], register: dict[int, str]) -> list[dict]:
    """Per magic over all accounts: trades, result, win rate, worst floating loss, first trade.

    Args:
        accounts: One dict per account: `login`, `label`, `offset` (server clock minus UTC, seconds),
            `trades` (`history.trades()`) and `excursions` (`history.excursions()` or None).
        register: `{magic: strategy}` of the reconciler, any firm.

    Returns:
        Rows of `magic`, `strategy`, `accounts` (how many carry it), `trades` (closed ones), `net`,
        `win_rate` (closed trades with a net gain; None with no closed trade), `worst_mae` (the
        lowest floating profit any of its positions reached, collector's 1-minute resolution; None
        without excursions) and `first` (its first entry, server clock); biggest net loss first.
    """
    comments = {
        t["magic"]: eas.strategy_key(t["comment"])
        for a in accounts
        for t in a["trades"]
    }
    magics = sorted(comments)
    rows = []
    for m in magics:
        mine = [(a, t) for a in accounts for t in a["trades"] if t["magic"] == m]
        closed = [t for _, t in mine if t["close"]]
        lows = [
            e["min_profit"]
            for a in accounts
            for e in (a["excursions"] or {}).values()
            if e["magic"] == m
        ]
        rows.append(
            {
                "magic": m,
                "strategy": label(m, comments, register),
                "accounts": len({a["login"] for a, _ in mine}),
                "trades": len(closed),
                "net": sum(t["net"] for t in closed),
                "win_rate": sum(t["net"] > 0 for t in closed) / len(closed)
                if closed
                else None,
                "worst_mae": min(lows) if lows else None,
                "first": min((t["open"] - a["offset"], t["open"]) for a, t in mine)[1],
            }
        )
    return sorted(rows, key=lambda r: r["net"])


def group(
    entries: list[tuple[int, str]], accounts: list[str], tolerance: int
) -> list[list[tuple[int, str]]]:
    """Cluster one side's entries of one magic: each group holds at most one entry per account, all within `tolerance` s of its first.

    Args:
        entries: (UTC epoch, account label), any order.
        accounts: Every account that carries the magic.
        tolerance: Seconds.
    """
    entries, used, groups = sorted(entries), set(), []
    for i, (t, who) in enumerate(entries):
        if i in used:
            continue
        used.add(i)
        g = [(t, who)]
        for other in (a for a in accounts if a != who):
            near = [
                (abs(x - t), j)
                for j, (x, w) in enumerate(entries)
                if j not in used and w == other and abs(x - t) <= tolerance
            ]
            if near:
                used.add(min(near)[1])
                g.append(entries[min(near)[1]])
        groups.append(g)
    return groups


def pairing(accounts: list[dict], register: dict[int, str], now: int) -> list[dict]:
    """Per magic carried by two or more accounts, its entries of the last `pair_days` days paired across them.

    Args:
        accounts: As `record()`.
        register: As `record()`.
        now: UTC epoch seconds.

    Returns:
        Per such magic: `magic`, `strategy`, `accounts` (labels), `complete` (entries that every
        account made together), and `lonely`: dicts of `time` (server clock of its first account), `side`, `present`, `missing`
        for each group some account missed.
    """
    comments = {
        t["magic"]: eas.strategy_key(t["comment"])
        for a in accounts
        for t in a["trades"]
    }
    offsets = {a["label"]: a["offset"] for a in accounts}
    since, tol = (
        now - read.CFG["pair_days"] * 86400,
        read.CFG["pair_tolerance_min"] * 60,
    )
    out = []
    for m in sorted(comments):
        who = sorted(
            {a["label"] for a in accounts if any(t["magic"] == m for t in a["trades"])}
        )
        if len(who) < 2:
            continue
        lonely, complete = [], 0
        for side in ("buy", "sell"):
            entries = [
                (t["open"] - a["offset"], a["label"])
                for a in accounts
                for t in a["trades"]
                if t["magic"] == m
                and t["side"] == side
                and t["open"] - a["offset"] >= since
            ]
            for g in group(entries, who, tol):
                present = sorted(w for _, w in g)
                if present == who:
                    complete += 1
                else:
                    lonely.append(
                        {
                            "time": g[0][0] + offsets[g[0][1]],
                            "side": side,
                            "present": present,
                            "missing": [w for w in who if w not in present],
                        }
                    )
        out.append(
            {
                "magic": m,
                "strategy": label(m, comments, register),
                "accounts": who,
                "complete": complete,
                "lonely": lonely,
            }
        )
    return out
