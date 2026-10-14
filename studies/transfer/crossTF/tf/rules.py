"""T0 to T4 and the verdict per mother: from measured siblings to pass, limbo or fail, with why."""

from typing import Any, TypedDict, cast

import numpy as np
import pandas as pd

RANK = {
    "pass": 0,
    "limbo": 1,
    "fail": 2,
}  # the vocabulary of pipeline/autopilot/criteria.py


def comparable(made: pd.DataFrame, limit: float) -> pd.Series:
    """T0 on what the fabrication did: why a sibling is another strategy, "" when it is not.

    Args:
        made: One row per sibling with `unverified`, `clamped` (truthy when set) and
            `rounding_shift`.
        limit: tf.comparable.rounding_shift.

    Returns:
        "unverified", "clamped", "rounding_shift" or "", the first that applies.
    """
    return pd.Series(
        np.select(
            [
                made["unverified"].fillna(0).astype(bool),
                made["clamped"].fillna(0).astype(bool),
                made["rounding_shift"] > limit,
            ],
            ["unverified", "clamped", "rounding_shift"],
            "",
        ),
        index=made.index,
    )


def why(*reasons: pd.Series) -> pd.Series:
    """The first non-empty reason of each row, in the order given."""
    out = reasons[0].astype(object)
    for nxt in reasons[1:]:
        out = out.where(out != "", nxt)
    return out


def few(n: pd.Series, least: int, reason: str = "few_trades") -> pd.Series:
    """`reason` where a window holds fewer than `least` trades (no window at all included)."""
    return pd.Series(np.where(n >= least, "", reason), index=n.index)


def centre(values: pd.Series, pair: pd.Series, least: int) -> pd.Series:
    """The median of each timeframe pair's population, NaN for one of fewer than `least`."""
    by = values.groupby(pair)
    return by.transform("median").where(cast(pd.Series, by.transform("count")) >= least)


def percentile(values: pd.Series, pair: pd.Series, least: int) -> pd.Series:
    """Where each value stands in its pair's population, 0..1; NaN for one of fewer than `least`."""
    by = values.groupby(pair)
    return by.rank(pct=True).where(cast(pd.Series, by.transform("count")) >= least)


def z_frec(
    n_mother: pd.Series, n_sibling: pd.Series, phi: pd.Series, m_pop: pd.Series
) -> pd.Series:
    """T1's z: the log ratio of trades over the same period, centred on the pair's population.

    Args:
        n_mother, n_sibling: Trades over build + oos1; the period is the same, so the ratio of
            counts is the ratio of rates.
        phi: The overdispersion of the mother's yearly counts in the build, already bounded.
        m_pop: centre() of the same log ratio.
    """
    return (np.log(n_sibling / n_mother) - m_pop) / np.sqrt(
        phi * (1 / n_sibling + 1 / n_mother)
    )


def t1(z: pd.Series, f: dict) -> np.ndarray:
    """T1 per sibling: |z_frec| up to `pass` passes, beyond `fail` fails; no z is limbo."""
    return np.select(
        [z.abs() <= f["pass"], z.abs() > f["fail"]], ["pass", "fail"], "limbo"
    )


def t2a(ret: pd.Series, z_delta: pd.Series, r: dict) -> np.ndarray:
    """T2a per sibling: ret at or over `pass` passes; ret <= 0 with z_delta at or over `z`
    fails; anything else, no data included, is limbo."""
    return np.select(
        [ret >= r["pass"], (ret <= 0) & (z_delta >= r["z"])], ["pass", "fail"], "limbo"
    )


def t2b(z_build: pd.Series, b: dict) -> np.ndarray:
    """T2b per sibling: z_build at or over `pass` passes, at or under `fail` fails; no z is limbo."""
    return np.select(
        [z_build >= b["pass"], z_build <= b["fail"]], ["pass", "fail"], "limbo"
    )


def _both(states: pd.Series, expected: int) -> str:
    """A test over the neighbours that have data: pass and fail both need every expected
    neighbour measured, and all of them agreeing."""
    full = 0 < expected == len(states)
    if full and (states == "fail").all():
        return "fail"
    return "pass" if full and (states == "pass").all() else "limbo"


class Mother(TypedDict):
    """§6 for one mother: her three tests, the far-sibling brake, the phase-1 state, the final state and why."""

    t1: str
    t2a: str
    t2b: str
    t3: str
    phase1: str
    state: str
    why: str


def mother(rows: pd.DataFrame, expected: int, low_ret: float) -> Mother:
    """§6 for one mother, from her siblings' rows.

    Args:
        rows: Her rows of the siblings table: `role` ("neighbour", "far", "note"), the states
            `t1`, `t2a`, `t2b`, why each has no data (`t1_why`, `t2a_why`, `t2b_why`, "" when
            measured) and `ret`.
        expected: How many neighbours her timeframe has in tf.neighbours.
        low_ret: tf.retention.low.

    Returns:
        `t1`, `t2a`, `t2b`, `t3`, `phase1`, `state` and `why`. A test passes only with every
        expected neighbour measured and passing, so one comparable neighbour caps the mother at
        limbo and none leaves her there. T1 fails on any neighbour; T2a on an isolated peak in
        oos1 (both neighbours failing, or one failing and the other under `low_ret`); T2b on
        both neighbours at or under chance in the build. `t3` is "limbo" when the far sibling,
        comparable, fails T2a — it only lowers a pass — and "pass" otherwise.

        UNDECIDED (encargo 47, owner's call): the ONLY measured neighbour failing T2a or T2b.
        §6 says «decide ella», §5 defines the isolated peak on two neighbours. Until he rules
        it is limbo, with `t2a_lone_fail` / `t2b_lone_fail` in `why`.
    """
    near, far = rows[rows["role"] == "neighbour"], rows[rows["role"] == "far"]
    a, b, f = (near.loc[near[f"{t}_why"] == "", t] for t in ("t2a", "t2b", "t1"))
    s1 = "fail" if (f == "fail").any() else _both(f, expected)
    s2a = _both(a, expected)
    if (
        len(a) == expected
        and (a == "fail").any()
        and (near.loc[a.index[a != "fail"], "ret"] < low_ret).all()
    ):
        s2a = "fail"
    s2b = _both(b, expected)
    brakes = bool(((far["t2a_why"] == "") & (far["t2a"] == "fail")).any())
    phase1 = "limbo" if s2a == "pass" and brakes else s2a
    worst = max((s1, s2a, s2b), key=lambda s: RANK[s])
    state = "limbo" if worst == "pass" and brakes else worst
    lone = lambda s: len(s) < expected and len(s) > 0 and bool((s == "fail").all())
    said = [
        w
        for w, hit in (
            ("frequency", s1 == "fail"),
            ("isolated_peak_oos1", s2a == "fail"),
            ("isolated_peak_build", s2b == "fail"),
            ("far_brakes", brakes),
            ("t2a_lone_fail", lone(a)),
            ("t2b_lone_fail", lone(b)),
        )
        if hit
    ]
    if state == "limbo":
        said += sorted(
            {
                f"{r.timeframe}:{w}"
                for r in cast(Any, near.itertuples())
                for w in (r.t2a_why, r.t2b_why, r.t1_why)
                if w
            }
        )
        said += [f"neighbours={len(near)}/{expected}"] if len(near) < expected else []
    return Mother(
        t1=s1,
        t2a=s2a,
        t2b=s2b,
        t3="limbo" if brakes else "pass",
        phase1=phase1,
        state=state,
        why=";".join(said),
    )


def overlap(
    mother_open: np.ndarray, sibling_open: np.ndarray, bar_seconds: float
) -> float:
    """T4: the share of a sibling's entries within one bar of the mother of one of her entries.

    Args:
        mother_open, sibling_open: Entry times, datetime64.
        bar_seconds: The length of one bar of the MOTHER's timeframe.

    Returns:
        0..1; NaN when either has no trade.
    """
    if len(mother_open) == 0 or len(sibling_open) == 0:
        return np.nan
    hers = np.sort(np.asarray(mother_open, "datetime64[s]").astype(np.int64))
    mine = np.asarray(sibling_open, "datetime64[s]").astype(np.int64)
    at = np.searchsorted(hers, mine)
    gap = np.minimum(
        np.abs(mine - hers[np.clip(at - 1, 0, len(hers) - 1)]),
        np.abs(hers[np.clip(at, 0, len(hers) - 1)] - mine),
    )
    return float(np.mean(gap < bar_seconds))
