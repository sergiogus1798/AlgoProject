"""Benjamini-Hochberg over a family of tests: which of them may be named as discoveries."""

from collections.abc import Mapping, Sequence
from typing import Any


def _refuse_nan(rows: Sequence[Mapping[str, Any]]) -> None:
    """Raise on a NaN p: it sorts nowhere, so it would be named a discovery and misorder the rest."""
    if any(r["p"] != r["p"] for r in rows):
        raise ValueError("fdr: NaN p-value in the family; drop untestable rows first")


def discoveries(rows: Sequence[Mapping[str, Any]], alpha: float = 0.05) -> set[str]:
    """Which of a family of tests survive Benjamini-Hochberg control of the FDR.

    Args:
        rows: One dict per test, each carrying "metric" and "p".
        alpha: False discovery rate to hold across the whole family.

    Returns:
        The metric names that survive. Every in-sample metric is tested against the same
        outcome at once, so the plain 5% level would be expected to hand back one false
        positive in every twenty metrics tested.
    """
    _refuse_nan(rows)
    ordered = sorted(rows, key=lambda r: r["p"])
    below = [i for i, r in enumerate(ordered, 1) if r["p"] <= i / len(rows) * alpha]
    return {r["metric"] for r in ordered[: max(below, default=0)]}


def adjusted(rows: Sequence[Mapping[str, Any]]) -> dict[str, float]:
    """The Benjamini-Hochberg adjusted p of every test of a family.

    Args:
        rows: One dict per test, each carrying "metric" and "p".

    Returns:
        {metric: q}, the smallest FDR at which that test would be named: q <= alpha exactly
        when discoveries(rows, alpha) names it.
    """
    _refuse_nan(rows)
    ordered = sorted(rows, key=lambda r: r["p"])
    out, q = {}, 1.0
    for i in range(len(ordered), 0, -1):
        q = min(q, ordered[i - 1]["p"] * len(ordered) / i)
        out[ordered[i - 1]["metric"]] = q
    return out
