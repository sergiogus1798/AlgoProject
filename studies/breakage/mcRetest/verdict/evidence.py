"""Question 4 — do I believe it? What survives once shape, dependence and multiplicity are paid for."""

import numpy as np
import pandas as pd
from scipy import stats

from core import significance


def empirical_sharpe(metrics: dict, cfg: dict) -> dict:
    """The Sharpe of every re-run, read straight off the simulations.

    Args:
        metrics: The reconstructed metrics of one task, one array per name.
        cfg: What inputs.config.load() returned.

    Returns:
        The share of re-runs that kept a positive Sharpe, and the distribution's quantiles.
        **This is a per-trade analogue on SQX's own ddof=0 basis, not SQX's SharpeRatio**,
        which is computed over the daily equity curve no simulation carries. It travels
        under its own name for that reason and must never be compared against the value
        SQX stored for the original.
        It answers the same question as the analytic route from the other direction: the
        analytic one asks how likely a single realisation's edge is to be zero, this one
        asks how often the edge survived a thousand plausible perturbations of the world.
    """
    sharpe = np.divide(metrics["AvgTrade"], metrics["StandardDev"],
                       out=np.zeros_like(metrics["AvgTrade"]), where=metrics["StandardDev"] > 0)
    return {"p_positive": float(np.mean(sharpe > cfg["evidence"]["psr_benchmark"])),
            "median": float(np.median(sharpe)),
            "p5": float(np.percentile(sharpe, 5)),
            "p95": float(np.percentile(sharpe, 95))}


def analytic_sharpe(original_pnl: np.ndarray, cfg: dict) -> dict:
    """The probability the unperturbed backtest's edge is above the benchmark.

    Args:
        original_pnl: The original backtest's P/L per trade, USD.
        cfg: What inputs.config.load() returned.

    Returns:
        What core.significance.psr() returned. No Deflated Sharpe: it needs the population
        of strategies tried during generation, which does not exist at this stage, and a
        thousand retests of one strategy are not a thousand selection trials -- feeding them
        in as N would produce a credible, false number. Both sibling studies refuse it for
        the same reason.

        `cfg["evidence"]["psr_benchmark"]` stays 0 here, unlike `crossmarket` and
        `monteCarlo` (OPEN.md #71): the honest benchmark needs the market's own bars and the
        trades' prices and times, which this study's ingest never reads (`measure/store.py`
        keeps 30 reconstructed metrics and raw P/L, nothing that prices a trade). Recorded
        rather than silently assumed correct: `POSSIBLE_IMPROVEMENTS.md` #10.
    """
    return significance.psr(np.asarray(original_pnl, dtype=np.float64),
                            cfg["evidence"]["psr_benchmark"])


def effective_bets(returns: pd.DataFrame) -> dict:
    """How many independent strategies a correlated set really amounts to.

    Args:
        returns: One column per strategy, one row per date, of the ORIGINAL backtests --
            never of the simulations, which carry no dates.

    Returns:
        Meucci's effective number of bets: the exponential of the entropy of the correlation
        matrix's eigenvalue spectrum, with the raw count beside it.

        Measured here it **refutes the assumption it was added to confirm**. Four of the
        five strategies share a generation template, and both the plan and its source
        document took that to mean they were not five independent draws. On the daily
        returns of the original backtests the ENB is **4.81 of 5** -- only one pair
        correlates at all, at 0.41, and the rest sit near zero. A shared template constrains
        the *shape of the rules*, not the *timing of the trades*, and it is the second that
        a correlation sees.

        It **describes**; it does not choose the correction. Letting an ENB estimated from
        five short series pick between two FDR procedures would be letting noise decide,
        and the conservative choice costs little at this pool size.
    """
    matrix = returns.corr().to_numpy()
    eigenvalues = np.clip(np.linalg.eigvalsh(matrix), 1e-12, None)
    weights = eigenvalues / eigenvalues.sum()
    return {"enb": float(np.exp(-(weights * np.log(weights)).sum())),
            "n": int(matrix.shape[0]),
            "ratio": float(np.exp(-(weights * np.log(weights)).sum()) / matrix.shape[0])}


def corrected(p_values: dict, cfg: dict) -> dict:
    """The p-values of the battery, paid for.

    Args:
        p_values: {label: p}, only from tests whose p actually discriminates.
        cfg: What inputs.config.load() returned.

    Returns:
        The q-value of each label, whether it survives, and the size of the pool it was
        corrected in -- a q reported without its pool size is not a number.

        **Benjamini-Yekutieli, not Hochberg**, and unconditionally at this scale: four of
        the five strategies share a template, so positive dependence cannot be assumed. The
        price is the harmonic factor, and it is the honest one to pay.

        The pool holds only the dip tests. The between-task p-values are excluded because a
        thousand simulations drive them to zero whatever is true, and Jarque-Bera is
        excluded because it rejected 40 of 40 -- both would spend the budget on certain
        rejections and widen everyone else's q for nothing.
    """
    labels = sorted(p_values)
    method, alpha = cfg["evidence"]["method"], cfg["evidence"]["alpha"]
    if not labels:
        return {"pool": 0, "method": method, "results": {}}
    values = np.array([p_values[label] for label in labels], dtype=np.float64)
    m = values.size
    factor = float(np.sum(1.0 / np.arange(1, m + 1))) if method == "by" else 1.0
    order = np.argsort(values)                       # ascending, the step-up order
    scaled = values[order] * m * factor / np.arange(1, m + 1)
    monotone = np.minimum.accumulate(scaled[::-1])[::-1]   # enforce q non-decreasing in p
    q = np.empty(m)
    q[order] = np.clip(monotone, 0.0, 1.0)
    return {"pool": m, "method": method, "factor": factor,
            "results": {label: {"p": float(values[i]), "q": float(q[i]),
                                "survives": bool(q[i] <= alpha)}
                        for i, label in enumerate(labels)}}


def rank_stability(original: dict, stressed: dict, cfg: dict) -> dict:
    """Whether the ranking of strategies survives the retest.

    Args:
        original: {strategy: its unperturbed net profit}.
        stressed: {strategy: its 5th percentile under the production task}.
        cfg: What inputs.config.load() returned.

    Returns:
        Kendall's tau between the two orderings, or a refusal when there are too few
        strategies to measure one. **At five strategies it is not measurable**: the null has
        120 points, the smallest two-sided p is 0.0167, and a bootstrap interval spans
        almost the whole range. Printing tau = 0.6 from five strategies is how a study
        acquires a conclusion it cannot support. At databank scale it becomes the single
        most useful number here.
    """
    names = sorted(set(original) & set(stressed))
    if len(names) < cfg["evidence"]["ranks_min_strategies"]:
        return {"measurable": False, "n": len(names),
                "needed": cfg["evidence"]["ranks_min_strategies"]}
    got = stats.kendalltau([original[n] for n in names], [stressed[n] for n in names])
    return {"measurable": True, "n": len(names),
            "tau": float(got.statistic), "p": float(got.pvalue)}
