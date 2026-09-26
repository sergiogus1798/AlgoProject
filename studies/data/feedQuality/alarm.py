"""Whether the flagged trades earn more than any subset of the same size: the owner's test (2.12)."""

import hashlib

import numpy as np

CHUNK = 1000
ALARM, QUIET, SHORT = "alarma", "sin alarma", "insuficiente"


def draws(pnl: np.ndarray, size: int, shuffles: int, seed: str) -> np.ndarray:
    """Net P/L sums of random subsets of `size` trades, drawn without replacement.

    Args:
        pnl: Net P/L per trade (after costs).
        size: How many trades each subset holds: the number flagged.
        shuffles: B, the number of subsets.
        seed: Anything stable — the strategy's identity — so a rerun reads the same p.

    Returns:
        B sums.
    """
    rng = np.random.default_rng(int(hashlib.sha256(seed.encode()).hexdigest()[:16], 16))
    out = []
    for done in range(0, shuffles, CHUNK):
        n = min(CHUNK, shuffles - done)
        pick = rng.random((n, len(pnl))).argpartition(size - 1, axis=1)[:, :size]
        out.append(pnl[pick].sum(axis=1))
    return np.concatenate(out)


def test(pnl: np.ndarray, flagged: np.ndarray, cfg: dict, seed: str) -> dict:
    """The alarm on one strategy's trades.

    Args:
        pnl: Net P/L per trade, IS and OOS together (owner, 2026-09-26).
        flagged: One bool per trade.
        cfg: inputs.config()'s dict.
        seed: The strategy's identity.

    Returns:
        {"n", "flagged", "observed" (the flagged sum), "p", "draws", "verdict", "at_risk"
        (the flagged share of the total profit, None when the total is not positive),
        "flagged_pnl"}. p = (1 + #{S_b >= S_obs}) / (B + 1), one-sided: only a flagged set
        that earns MORE than chance is an alarm. Under `min_flagged` there is no test.
    """
    al = cfg["alarm"]
    m, total, observed = int(flagged.sum()), float(pnl.sum()), float(pnl[flagged].sum())
    got = {"n": len(pnl), "flagged": m, "observed": observed, "flagged_pnl": observed,
           "at_risk": observed / total if total > 0 else None, "p": None, "draws": None,
           "verdict": SHORT}
    if m < al["min_flagged"]:
        return got
    got["draws"] = draws(pnl, m, al["shuffles"], seed)
    # A tie is a tie: the same trades summed in another order differ in the last float bits.
    tie = 1e-9 * np.abs(pnl).sum()
    got["p"] = float((1 + np.sum(got["draws"] >= observed - tie)) / (al["shuffles"] + 1))
    got["verdict"] = ALARM if got["p"] < al["p_max"] else QUIET
    return got
