"""The news rule on a trade list, in pure Python: which releases move a symbol, and what the filter does to each trade."""
import numpy as np
import pandas as pd

CURRENCIES = ["USD", "EUR", "GBP", "JPY", "AUD", "NZD", "CAD", "CHF", "CNY", "OIL"]


def moves(symbol: str, tag: str, firm: dict) -> bool:
    """newsMovesSymbol() of the EA: the tag is in the symbol's name, or the symbol is one of its country's."""
    sym = symbol.upper()
    return tag in sym or any(f in sym for f in firm["country_of"].get(tag, []))


def for_symbol(releases: pd.DataFrame, symbol: str, firm: dict) -> pd.DataFrame:
    """The rows of a tester file the EA keeps when it trades `symbol`, sorted by time."""
    keep = {tag for tag in releases["tag"].unique() if moves(symbol, tag, firm)}
    return releases[releases["tag"].isin(keep)].sort_values("time", ignore_index=True)


def spans(releases: pd.DataFrame, firm: dict) -> pd.DataFrame:
    """Per release, the three windows the EA applies, as the EA computes them.

    Returns:
        time, title, and: block_from/block_to (no entry, both ends included), close_from/close_to
        (it closes what is open; close_to excluded), rule_from/rule_to (the firm's own window).
    """
    m = lambda n: pd.Timedelta(minutes=n)   # noqa: E731
    t = releases["time"]
    return pd.DataFrame({
        "time": t, "title": releases["title"],
        "block_from": t - m(max(firm["block_before"], firm["close_before"])), "block_to": t + m(firm["block_after"]),
        "close_from": t - m(firm["close_before"]), "close_to": t - m(firm["rule_minutes"]),
        "rule_from": t - m(firm["rule_minutes"]), "rule_to": t + m(firm["rule_minutes"])})


def _first_inside(lo: np.ndarray, hi: np.ndarray, start: np.ndarray, end: np.ndarray) -> np.ndarray:
    """For each [lo, hi], the index of the first span [start, end] it overlaps, -1 if none (spans sorted by start)."""
    first = np.searchsorted(end, lo, side="left")          # first span not wholly before lo
    ok = (first < len(start)) & (start[np.minimum(first, len(start) - 1)] <= hi)
    return np.where(ok, first, -1)


def expected(trades: pd.DataFrame, releases: pd.DataFrame, firm: dict) -> pd.DataFrame:
    """What the filter does to each trade of an UNFILTERED run, taken one trade at a time.

    Args:
        trades: `Open time`, `Close time` (server clock), as mt5.report.trades gives them.
        releases: A symbol's rows (for_symbol), server clock.
        firm: One entry of firms.FIRMS.

    Returns:
        The trades plus `fate` — "blocked" (its entry falls in a no-entry window), "cut" (open
        when a close window starts: the EA closes it at the first tick from `cut_at` on),
        "kept" — and `release`, the time of the release responsible. It does not follow the
        knock-on: a trade the EA takes because an earlier one was cut is not in `trades`.
    """
    s = spans(releases, firm)
    opened, closed = trades["Open time"].to_numpy(), trades["Close time"].to_numpy()
    blocked = _first_inside(opened, opened, s["block_from"].to_numpy(), s["block_to"].to_numpy())
    # cut: a close window starting while the trade is open, the trade still open when it does
    after = np.searchsorted(s["close_from"].to_numpy(), opened, side="right")
    cut = np.where((after < len(s)) & (s["close_from"].to_numpy()[np.minimum(after, len(s) - 1)] < closed), after, -1)
    fate = np.select([blocked >= 0, cut >= 0], ["blocked", "cut"], "kept")
    which = np.where(blocked >= 0, blocked, cut)
    out = trades.copy()
    out["fate"] = fate
    out["release"] = s["time"].to_numpy()[np.maximum(which, 0)]
    out.loc[fate == "kept", "release"] = pd.NaT
    out["cut_at"] = np.where(fate == "cut", s["close_from"].to_numpy()[np.maximum(cut, 0)], np.datetime64("NaT"))
    return out


def violations(trades: pd.DataFrame, releases: pd.DataFrame, firm: dict) -> pd.DataFrame:
    """The trades of a FILTERED run that break what the filter promises — an empty frame is the pass.

    Returns:
        One row per breach: the trade's times, `release`, and `breach` — "entry in block
        window", "open across the release" (open before rule_from and still open after
        rule_to), or "close in the firm's window" (an SL, TP or exit inside rule_from..rule_to).
    """
    s = spans(releases, firm)
    opened, closed = trades["Open time"].to_numpy(), trades["Close time"].to_numpy()
    checks = [("entry in block window", _first_inside(opened, opened, s["block_from"].to_numpy(), s["block_to"].to_numpy())),
              ("close in the firm's window", _first_inside(closed, closed, s["rule_from"].to_numpy(), s["rule_to"].to_numpy()))]
    nxt = np.searchsorted(s["rule_from"].to_numpy(), opened, side="right")
    across = np.where((nxt < len(s)) & (s["rule_to"].to_numpy()[np.minimum(nxt, len(s) - 1)] < closed), nxt, -1)
    checks.append(("open across the release", across))
    rows = [trades.loc[hit >= 0, ["Open time", "Close time"]].assign(
        release=s["time"].to_numpy()[hit[hit >= 0]], breach=label) for label, hit in checks]
    return pd.concat(rows).sort_values("Open time", ignore_index=True)
