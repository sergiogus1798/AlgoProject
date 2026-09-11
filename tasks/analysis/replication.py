"""Does a conclusion drawn on one sample of strategies hold on another, independently generated one."""

import numpy as np

from tasks.analysis import correlations, improvement

DRAWS = 2000
SEED = 20260904


def hit_gap(reference: np.ndarray, sample: np.ndarray, level: float,
            draws: int = DRAWS) -> dict:
    """Difference in out-of-sample hit rate between two independent samples.

    Args:
        reference: The target metric for every strategy of the reference sample.
        sample: The same metric for every strategy of the sample being checked.
        level: Break-even from analysis.improvement.breakeven.
        draws: Resamples of each sample.

    Returns:
        Keys gap (sample minus reference, as a share) with lo and hi, its 95% interval.
        Both samples are resampled because neither is a subset of the other: these are
        separate generation runs, so both carry their own sampling error.
    """
    rng = np.random.default_rng(SEED)
    a = (sample[rng.integers(0, sample.size, (draws, sample.size))] > level).mean(axis=1)
    b = (reference[rng.integers(0, reference.size, (draws, reference.size))] > level).mean(axis=1)
    return {"gap": float((sample > level).mean() - (reference > level).mean()),
            "lo": float(np.quantile(a - b, 0.025)), "hi": float(np.quantile(a - b, 0.975))}


def carried(reference: dict[str, np.ndarray], sample: dict[str, np.ndarray],
            candidate: dict, target: str) -> dict:
    """Apply one sample's filter threshold to another sample and see what it delivers there.

    Args:
        reference: Numeric columns of the sample the filter was chosen on.
        sample: Numeric columns of the sample being checked.
        candidate: One entry from analysis.improvement.candidates.
        target: Full name of the out-of-sample column.

    Returns:
        Keys predicted (the hit rate the filter reached on the reference), share (what
        fraction of the sample clears the same threshold), n, observed (the hit rate among
        those) and lo/hi, the 95% interval on observed minus predicted. The threshold is the
        reference's quantile in the metric's own units, not the sample's, so a sample already
        selected on that metric shows a share near 1 — that is the point, and it is what
        makes predicted and observed comparable.
    """
    level = improvement.breakeven(target)
    column, cut = candidate["metric"], candidate["cut"] / 100
    edge = (np.quantile(reference[column], 1 - cut) if candidate["side"] == "top"
            else np.quantile(reference[column], cut))
    kept = (reference[column] >= edge if candidate["side"] == "top"
            else reference[column] <= edge)
    passes = (sample[column] >= edge if candidate["side"] == "top"
              else sample[column] <= edge)
    y, base = sample[target][passes], reference[target][kept]
    gap = hit_gap(base, y, level)
    return {"predicted": float((base > level).mean()),
            "share": float(passes.mean()),
            "n": int(passes.sum()),
            "observed": float((y > level).mean()),
            "lo": gap["lo"], "hi": gap["hi"]}


def restriction(reference: np.ndarray, sample: np.ndarray) -> float:
    """How much narrower a metric's spread is in one sample than in another.

    Args:
        reference, sample: The same metric column in each sample.

    Returns:
        The sample's standard deviation over the reference's. Well below 1 means the sample
        was selected on this metric, which attenuates every correlation it appears in: a
        weaker correlation there is expected and is not evidence against the conclusion.
    """
    return float(sample.std() / reference.std())


def predictors(columns: dict[str, np.ndarray], target: str, is_metrics: list[str]) -> dict:
    """Spearman of every in-sample metric against one outcome, keyed by metric.

    Args:
        columns: Numeric columns of one sample.
        target: Full name of the out-of-sample column.
        is_metrics: Full names of the in-sample columns to test.

    Returns:
        One entry per metric, its Spearman correlation with the target.
    """
    return {m: correlations.correlate(columns[m], columns[target])["spearman"]
            for m in is_metrics}


def stability(reference: dict, sample: dict) -> float:
    """How well two samples agree on which in-sample metrics predict an outcome.

    Args:
        reference, sample: predictors() output for the same metric list.

    Returns:
        Spearman between the two correlation vectors. Near 1 means both samples rank the
        predictors the same way even where the correlations themselves differ in size.
    """
    names = sorted(set(reference) & set(sample))
    return correlations.correlate(np.array([reference[m] for m in names]),
                                  np.array([sample[m] for m in names]))["spearman"]
