"""Admission to a base (Q16 c): pair filters against each member and Sharpe, one entry at a time."""

import numpy as np
import pandas as pd

INCREMENTS = ("finite", "marginal")


def _sharpe(path: np.ndarray) -> float:
    """Daily Sharpe, not annualised; infinite or NaN for a flat path (std 0).

    Such a candidate never enters: `increment` multiplies it by a correlation that is NaN for a
    flat path, so its increment is NaN and `gain > 0` is False (`finite` stays finite).
    """
    return float(path.mean() / path.std(ddof=1))


def increment(base: np.ndarray, candidate: np.ndarray, how: str) -> float:
    """What the candidate adds to the base's build Sharpe.

    Args:
        base: [K, D] the members' daily P&L per unit of risk on build.
        candidate: [D] the candidate's.
        how: "finite" -- the Sharpe of the K+1 at equal weight minus the Sharpe of the K;
            "marginal" -- the Euler derivative at zero weight, `SR_c - rho(c, base) * SR_base`,
            positive exactly when a small allocation to the candidate raises the Sharpe.

    Returns:
        The increment, in daily Sharpe.
    """
    book = base.mean(axis=0)
    if how == "finite":
        return _sharpe(np.vstack([base, candidate]).mean(axis=0)) - _sharpe(book)
    return _sharpe(candidate) - float(np.corrcoef(candidate, book)[0, 1]) * _sharpe(book)


def judge(unit: np.ndarray, graph: np.ndarray, base: np.ndarray, candidates: np.ndarray,
          how: str) -> pd.DataFrame:
    """One round: each candidate against the same base; none is added.

    Args:
        unit: [N, D] every strategy's daily P&L per unit of risk on build, 0 outside history.
        graph: N x N bool admissible adjacency.
        base: The base portfolio's member indices.
        candidates: Indices to judge, none of them in the base.
        how: As `increment`.

    Returns:
        One row per candidate: `candidate`, `blocked_by` (base members it has no admissible
        pair with), `increment` (written here, on build, before any verdict reads a later
        stretch) and `enters` (no member blocks it and the increment is above 0).
    """
    rows = []
    for c in candidates:
        blocked = base[~graph[c, base]]
        gain = increment(unit[base], unit[c], how)
        rows.append({"candidate": int(c), "blocked_by": blocked.tolist(), "increment": gain,
                     "enters": blocked.size == 0 and gain > 0})
    return pd.DataFrame(rows)


def sequence(unit: np.ndarray, graph: np.ndarray, base: np.ndarray, candidates: np.ndarray,
             how: str) -> pd.DataFrame:
    """Admit in sequence (owner, 2026-10-05): the best increment enters, the rest are re-judged.

    Two candidates that each help the base may not help it together (two clones of one idea):
    judged against a fixed base both would enter. Here the base grows by one per round and
    every candidate left faces the pair filters and the increment against the NEW base.

    Args:
        unit, graph, how: As `judge`.
        base: The starting portfolio's member indices.
        candidates: Indices to judge, none of them in the base.

    Returns:
        One row per judgement, round after round: `round` (from 1), `candidate`, `blocked_by`,
        `increment`, `admissible` (`judge`'s `enters`: could enter that round) and `enters`
        (the one that did: the highest increment among the admissible). The last round is the
        one where nobody enters, unless every candidate got in.
    """
    base, left, rounds = np.asarray(base), list(candidates), []
    while left:
        judged = judge(unit, graph, base, np.array(left), how).rename(columns={"enters": "admissible"})
        judged.insert(0, "round", len(rounds) + 1)
        gains = judged["increment"].where(judged["admissible"])
        judged["enters"] = gains.notna() & (judged.index == gains.idxmax()) if bool(gains.notna().any()) else False
        rounds.append(judged)
        if not bool(judged["enters"].any()):
            break
        winner = int(judged.loc[judged["enters"], "candidate"].iloc[0])
        base = np.append(base, winner)
        left.remove(winner)
    columns = ["round", "candidate", "blocked_by", "increment", "admissible", "enters"]
    return pd.concat(rounds, ignore_index=True) if rounds else pd.DataFrame(columns=pd.Index(columns))
