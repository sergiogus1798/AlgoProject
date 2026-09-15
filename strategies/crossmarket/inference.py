"""Judge the runs: where the real one sits in its null, and what there is to distrust about it.

Nothing here decides whether to keep a strategy. It locates a real run in its own null, and it
names the reasons a market's number should be read with suspicion — it never drops one. The
owner reads the numbers and the warnings together and makes the call outside this study."""

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
