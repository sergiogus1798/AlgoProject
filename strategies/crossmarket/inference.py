"""Judge the runs: where the real one sits in its null, and what there is to distrust about it.

Nothing here decides whether to keep a strategy. It locates a real run in its own null, and it
names the reasons a market's number should be read with suspicion — it never drops one. The
owner reads the numbers and the warnings together and makes the call outside this study."""

import math

import pandas as pd

# Code is English; panel.WARNINGS_ES is the Spanish mirror the owner's pages render, the same
# way panel.RANDOMISES mirrors trade_models.RANDOMISES.
WARNINGS = {
    "few_trades": "too few trades on this market to say anything firm",
    "pending_fills": "some entries do not land on a bar open: pending-order fills no null "
                     "model reproduces",
    "fill_mismatch": "prices are not reproduced from the bars, so the real run and the null "
                     "are not priced alike",
    "no_drift": "the market has no drift distinguishable from zero, so E means nothing here",
    "calendar_lost": "the null does not keep the weekday and hour of the real entries",
    "short_sample": "the observed Sharpe needs more trades than there are to be "
                    "distinguishable from zero",
    "bad_hold_fit": "the distribution fitted to the holds does not describe them",
}


def warnings(row: dict, cfg: dict) -> list[str]:
    """Every reason to distrust one market's numbers, named.

    Args:
        row: One (strategy, market) row, after every test has written into it.
        cfg: What config.load() returned.

    Returns:
        Keys of WARNINGS, in the order they were checked. A market that collects warnings is
        still reported in full with every number it produced: the earlier build dropped such
        a market from the study entirely, which cost a Brent result at p = 0.005 because 8%
        of its entries were pending fills.
    """
    d = cfg["diagnostics"]
    checks = [("few_trades", row["trades"] < d["min_trades"]),
              ("pending_fills", row["on_bar_open"] < d["min_on_open"]),
              ("fill_mismatch", row["fill_error"] > 0),
              ("no_drift", not row["e_meaningful"]),
              ("calendar_lost", row["calendar_kept"] < 0.99),
              ("short_sample", not row["min_track_enough"]),
              ("bad_hold_fit", row["hold_ks_p"] < d["alpha"])]
    return [name for name, fired in checks if fired]


def family(rows: pd.DataFrame) -> str:
    """Which test a strategy's result actually is.

    Args:
        rows: That strategy's per-market rows.

    Returns:
        "entry" when every exit is the fixed bar cap, "entry+exit" otherwise. The models reuse
        the real holds without reproducing what set them — the Friday close excepted, which
        `trade_models.truncate` does reproduce — so for a strategy that exits on a signal the
        result is a joint test and must not be read as entry timing.
    """
    return "entry" if rows["bar_cap"].min() == 1.0 else "entry+exit"


def sweep_power(rows: list[dict], months: int | None, cfg: dict) -> dict:
    """Whether one window size of the sweep leaves its null enough room to mean anything.

    Args:
        rows: What sweep.blocks() returned for that size.
        months: Its length, None for the whole window.
        cfg: What config.load() returned.

    Returns:
        weak — one flag per block, set when it holds fewer than sweep.min_trades real trades
        or has less than sweep.min_free_share of its bars free; weak_share — the share of the
        real trades inside weak blocks; and reason — "" when the point may be computed,
        "short_window" under sweep.min_months, "weak_blocks" when weak_share exceeds
        sweep.max_weak_share. A crowded block can only put its trades back about where they
        were, and a null that reproduces the real run returns p near 0.5 whatever the timing
        was: block_shift measured exactly that before it wrapped. Such a point is withheld,
        never drawn as a number.
    """
    s = cfg["sweep"]
    weak = [r["trades"] < s["min_trades"] or r["free_share"] < s["min_free_share"]
            for r in rows]
    share = sum(r["trades"] for r, w in zip(rows, weak) if w) / sum(r["trades"] for r in rows)
    reason = ("short_window" if months is not None and months < s["min_months"]
              else "weak_blocks" if share > s["max_weak_share"] else "")
    return {"weak": weak, "weak_share": share, "reason": reason}


def sweep_trend(points: list[dict], cfg: dict) -> str:
    """Which way one model's p moves as the sweep's window shrinks, on one market.

    Args:
        points: That model's sweep points, widest window first; p is None where withheld.
        cfg: What config.load() returned.

    Returns:
        "unassessable" with fewer than two computed points; "no_pass" when none reaches
        diagnostics.alpha, since there is then no pass whose origin to ask about; otherwise
        "regime" when the narrowest computed p is more than sweep.evidence_drop orders of
        magnitude above the widest one, and "timing" when it is not. It compares the two ends
        only: it is the curve's caption, and the curve and its trade counts are the reading.
    """
    done = [p["p"] for p in points if p["p"] is not None]
    if len(done) < 2:
        return "unassessable"
    if min(done) > cfg["diagnostics"]["alpha"]:
        return "no_pass"
    return ("regime" if math.log10(done[-1] / done[0]) > cfg["sweep"]["evidence_drop"]
            else "timing")
