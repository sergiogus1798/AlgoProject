"""Question 3 — what breaks it? Effect sizes between tasks, measured in units of the control."""

import numpy as np
from scipy import stats

from strategies.retest.inputs import tasks


def control_sigma(control: np.ndarray) -> float:
    """The noise floor a re-run moves the result by even when nothing meaningful changed.

    Args:
        control: NetProfit of every simulation of the control task.

    Returns:
        Its standard deviation, USD. Every effect below is divided by this. Without it the
        six diagnostic tasks are read against an implicit zero that does not exist: a
        backtest re-run with only its starting bar moved still shifts by 57 to 579 USD on
        this battery, and an effect smaller than that is not a finding.
    """
    return float(np.std(np.asarray(control, dtype=np.float64)))


def cliffs_delta(worse: np.ndarray, better: np.ndarray) -> float:
    """How often one task's outcome beats the other's, on a scale that ignores units.

    Args:
        worse: One value per simulation of the first task.
        better: One value per simulation of the second.

    Returns:
        P(worse > better) - P(worse < better), in [-1, 1]. Zero means the two are
        interchangeable, -1 that the first is always below. It is a rank statistic, so it
        does not care about the shape of either distribution and it does not move when the
        number of simulations changes -- which is the whole reason it leads here.
    """
    a, b = np.asarray(worse, float), np.asarray(better, float)
    u = stats.mannwhitneyu(a, b, alternative="two-sided").statistic
    return float(2.0 * u / (a.size * b.size) - 1.0)


def contrast(left: np.ndarray, right: np.ndarray, sigma: float) -> dict:
    """One comparison between two tasks, effect size first.

    Args:
        left: NetProfit of every simulation of the first task.
        right: The same for the second.
        sigma: What control_sigma() returned for this strategy.

    Returns:
        The rank effect size, the shift of the medians in control sigmas, the ratio of
        dispersions, and the two p-values behind them.

        **The p-values are reported, never read as evidence, and never enter the
        multiplicity pool.** At a thousand simulations per task the Kolmogorov-Smirnov and
        Brown-Forsythe statistics scale with the square root of n, and n is how long SQX was
        left running -- so doubling the simulations doubles the exponent without the
        strategy changing at all. Measured on this battery all 30 pairs rejected, from
        6e-34 down to 0. A number that a setting drives to zero is not evidence.
    """
    a, b = np.asarray(left, float), np.asarray(right, float)
    return {"delta": cliffs_delta(a, b),
            "median_shift": float(np.median(a) - np.median(b)),
            "shift_in_sigmas": float((np.median(a) - np.median(b)) / sigma) if sigma else np.nan,
            "dispersion_ratio": float(np.std(a) / np.std(b)) if np.std(b) else np.inf,
            "ks_p": float(stats.ks_2samp(a, b).pvalue),
            "levene_p": float(stats.levene(a, b, center="median").pvalue)}


def ranking(per_task: dict, control: str, sigma: float) -> list[dict]:
    """Which perturbation cost the most, worst first.

    Args:
        per_task: {task key: NetProfit of every simulation}, the control included.
        control: Key of the control task.
        sigma: What control_sigma() returned for this strategy.

    Returns:
        One row per non-control task: how far its median fell below the control's, in
        control sigmas, and how much wider it spread. This is the answer to "what breaks
        it" -- a single ordered list, with the noise floor as the unit so that a large
        number means something.
    """
    base = float(np.median(per_task[control]))
    out = []
    for task, values in per_task.items():
        if task == control:
            continue
        values = np.asarray(values, float)
        out.append({"task": task, "role": tasks.ROLE[task],
                    "cost": base - float(np.median(values)),
                    "cost_in_sigmas": (base - float(np.median(values))) / sigma if sigma else np.nan,
                    "spread_vs_control": float(np.std(values) / sigma) if sigma else np.inf})
    return sorted(out, key=lambda row: -row["cost"])


def describe(per_task: dict, cfg: dict) -> dict:
    """Everything question 3 asks of one strategy.

    Args:
        per_task: {task key: NetProfit of every simulation}, the control included.
        cfg: What inputs.config.load() returned.

    Returns:
        The ranking of what cost most, and the named contrasts of tasks.CONTRASTS with the
        question each one asks. Nothing outside that list is compared: a contrast with no
        question behind it is a p-value looking for a use.
    """
    control = cfg["attribution"]["control_task"]
    sigma = control_sigma(per_task[control])
    pairs = {}
    for left, right, asks in tasks.CONTRASTS:
        if left in per_task and right in per_task:
            pairs[f"{left}_vs_{right}"] = {"asks": asks,
                                           **contrast(per_task[left], per_task[right], sigma)}
    return {"control_sigma": sigma, "ranking": ranking(per_task, control, sigma), "contrasts": pairs}
