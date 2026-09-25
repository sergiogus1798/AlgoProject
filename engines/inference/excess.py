"""Observed against chance: how many of a family of tests passed, and how many should have."""

import numpy as np

LAMBDA = 0.5        # Storey's cut: p above it are taken as coming from strategies with no edge


def share_null(p: np.ndarray, cut: float = LAMBDA) -> float:
    """Storey's estimate of what fraction of a family has no edge at all.

    Args:
        p: One p-value per test.
        cut: Where to split. Tests above it are assumed to be null, which is close enough
            to true because a real edge almost never produces a large p.

    Returns:
        A fraction in [0, 1]. Assuming every test is null instead — the textbook shortcut —
        overstates how many passes were luck, by exactly the factor this corrects.

    It degenerates to 0 when almost no p-value is large, which is what a family with
    pervasive signal looks like. That is not an error and must not be clipped away: it is
    the estimator saying "I see no null tests here". A report shows it beside the
    all-null count rather than instead of it, because 0 expected reads as absurd alone.
    """
    return float(min((p > cut).sum() / ((1 - cut) * len(p)), 1.0))


def excess(p: np.ndarray, alpha: float) -> dict:
    """How many tests passed, how many chance alone would have, and what is left over.

    Args:
        p: One p-value per test.
        alpha: The level each test was read at.

    Returns:
        `observed` passes, `expected_all_null` if not one test had an edge, `expected`
        using Storey's share, the `excess` over the all-null count, and `fdr`, the
        fraction of the passes that are probably luck. `excess` deliberately uses the
        all-null count: it is the conservative reading and the one that survives Storey
        degenerating on a family with pervasive signal.

    This answers a question about the FAMILY that no single p-value can: a population can
    carry obvious signal -- many more passes than chance -- while not one of its members is
    extreme enough to be named. The two readings are independent and both belong in a report.
    """
    n = len(p)
    observed = int((p < alpha).sum())
    null_share = share_null(p)
    expected = null_share * alpha * n
    return {"n": n, "observed": observed, "expected_all_null": alpha * n,
            "expected": expected, "share_null": null_share,
            "excess": observed - alpha * n,
            "fdr": float(alpha * n / observed) if observed else float("nan")}


def resolution(p: np.ndarray, alpha: float, draws: int) -> dict:
    """Whether the p-values are fine-grained enough for the correction to read them.

    Args:
        p: One p-value per test.
        alpha: The false discovery rate the family is held to.
        draws: Null runs behind each p, which sets the smallest one observable.

    Returns:
        The `floor` of 1/(draws+1), the `bar` Benjamini-Hochberg sets for the single best
        test, whether that bar is `reachable` at all, how many p sit `saturated` at the
        floor, and `draws_needed` to reach it.

    ⚠️ `reachable` is about RANK ONE only. Benjamini-Hochberg steps up, so a family whose
    best test cannot clear alpha/n can still have k tests clear k*alpha/n and be named.
    An unreachable bar therefore explains nothing on its own -- it is only worth raising
    where nothing was named at all.
    """
    floor = 1 / (draws + 1)
    bar = alpha / len(p)
    return {"floor": floor, "bar": bar, "reachable": floor <= bar,
            "saturated": int((p <= floor).sum()),
            "draws_needed": int(np.ceil(1 / bar)) - 1}
