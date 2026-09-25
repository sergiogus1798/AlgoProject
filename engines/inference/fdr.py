"""Benjamini-Hochberg over a family of tests: which of them may be named as discoveries."""


def discoveries(rows: list[dict], alpha: float = 0.05) -> set[str]:
    """Which of a family of tests survive Benjamini-Hochberg control of the FDR.

    Args:
        rows: One dict per test, each carrying "metric" and "p".
        alpha: False discovery rate to hold across the whole family.

    Returns:
        The metric names that survive. Every in-sample metric is tested against the same
        outcome at once, so the plain 5% level would be expected to hand back one false
        positive in every twenty metrics tested.
    """
    ordered = sorted(rows, key=lambda r: r["p"])
    below = [i for i, r in enumerate(ordered, 1) if r["p"] <= i / len(rows) * alpha]
    return {r["metric"] for r in ordered[: max(below, default=0)]}
