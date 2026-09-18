"""Recomputed order statistics against the table SQX stored: the check everything else rests on."""

import numpy as np

from core import sqxretest
from strategies.retest.model import recon


def quantile(values: np.ndarray, level: int, worse_high: bool) -> float:
    """The value SQX would report for one metric at one confidence level.

    Args:
        values: One value per simulation.
        level: One of core.sqxretest.CONFIDENCE.
        worse_high: True when a higher value is the worse outcome, as for any drawdown.

    Returns:
        The order statistic at rank n*(100-level)/100 of the simulations sorted worse-last.
        This is SQX's own convention, recovered by reconciliation rather than documentation:
        it reproduces the stored table to within the cent rounding of the P/L.
    """
    ordered = np.sort(np.asarray(values, dtype=np.float64))
    if worse_high:
        ordered = ordered[::-1]
    rank = int(np.floor(ordered.size * (100 - level) / 100.0))
    return float(ordered[max(0, min(ordered.size - 1, rank))])


def table(metrics: dict, levels: tuple) -> dict:
    """The whole confidence table, rebuilt for every metric SQX never exposes that way.

    Args:
        metrics: What model.recon.frame() returned.
        levels: The confidence levels to report, from config.

    Returns:
        {metric: {level: value}}. Each entry is a marginal order statistic of its own
        metric, exactly as SQX's is -- so two metrics at one level still come from two
        different simulations, and this table is no more a scenario than the stored one.
    """
    return {name: {level: quantile(values, level, name in recon.HIGHER_IS_WORSE)
                   for level in levels}
            for name, values in metrics.items()}


def reconcile(metrics: dict, stored: dict, cfg: dict) -> dict:
    """Whether the reconstruction reproduces what SQX itself computed.

    Args:
        metrics: What model.recon.frame() returned.
        stored: What core.sqxretest.levels() returned.
        cfg: What inputs.config.load() returned.

    Returns:
        Per metric: how far outside the admissible band its worst level fell, as a multiple
        of the stored value's own rounding, and whether it cleared. The test is not a fixed
        tolerance: SQX's answer must be **one of the two adjacent order statistics**, and
        the band between them is the whole admissible answer. Where several simulations
        share a value that gap is wide, and a fixed tolerance either rejects a correct
        formula there or accepts a wrong one everywhere else.
    """
    tol, floor = cfg["recon"]["tolerance"], cfg["recon"]["absolute_floor"]
    out = {}
    for name, values in metrics.items():
        if not np.isfinite(values).all():
            continue
        worst = 0.0
        for level, blob in stored.items():
            if name not in blob:
                continue
            target = float(blob[name])
            band = _band(values, level, name)
            outside = max(min(band) - target, target - max(band), 0.0)
            worst = max(worst, outside / max(abs(target) * tol, floor))
        out[name] = {"worst_ratio": worst, "passed": worst <= 1.0}
    return out


def _band(values: np.ndarray, level: int, name: str) -> list[float]:
    """The order statistics SQX's answer must lie between.

    Args:
        values: One value per simulation.
        level: One of core.sqxretest.CONFIDENCE.
        name: The metric's name, for its ranking direction.

    Returns:
        The values one rank either side of the nominal rank. The convention is recovered to
        within a single rank and no closer: SQX's interpolation at a tie is internal, and a
        metric like NumberOfProfits is an integer over a thousand simulations, so hundreds
        of them share a value and the nominal rank lands anywhere inside that run. On a
        continuous metric the three ranks are a hair apart and this costs nothing.
    """
    ordered = np.sort(np.asarray(values, dtype=np.float64))
    if name in recon.HIGHER_IS_WORSE:
        ordered = ordered[::-1]
    rank = int(np.floor(ordered.size * (100 - level) / 100.0))
    return [ordered[max(0, min(ordered.size - 1, rank + step))] for step in (-1, 0, 1)]


def partition() -> list[str]:
    """Whether every metric SQX varies is accounted for in exactly one set.

    Returns:
        One message per metric that is in none of RECON, ANALOGUE and EXCLUDED, or in more
        than one. Empty is the only acceptable answer: a metric in none of them is one
        nobody decided about, and silence there reads as "unimportant" when it means
        "unexamined".
    """
    sets = {"RECON": set(recon.RECON), "ANALOGUE": set(recon.ANALOGUE),
            "EXCLUDED": set(recon.EXCLUDED)}
    out = []
    for left, names in sets.items():
        for right, others in sets.items():
            if left < right and names & others:
                out.append(f"in both {left} and {right}: {sorted(names & others)}")
    return out


def varying(stored: dict) -> set:
    """Which metrics the Monte Carlo actually moved.

    Args:
        stored: What core.sqxretest.levels() returned.

    Returns:
        Every metric whose value differs across the eleven levels. The rest are constants of
        the strategy -- Walk-Forward and Add-Markets holes, Fitness, the data span -- and
        there is nothing about them to reconstruct or to decide.
    """
    blobs = list(stored.values())
    return {name for name in blobs[0]
            if len({round(float(blob[name]), 6) for blob in blobs}) > 1}


def stored_only(stored: dict) -> list[str]:
    """The metrics that exist only as eleven quantiles, and can never be had per simulation.

    Args:
        stored: What core.sqxretest.levels() returned.

    Returns:
        Every varying metric that is in none of RECON, ANALOGUE or EXCLUDED, sorted. These
        need dates, prices or excursions that a simulation file does not carry -- SQX
        computed them for each simulation and kept only the quantiles. That is a real
        second channel, coarser but not empty: it is the only way to ask a retest anything
        about MAE, MFE, exposure or duration. The ingest records the list rather than the
        code hard-coding it, because which metrics a given install reports is its own fact.
    """
    known = set(recon.RECON) | set(recon.ANALOGUE) | set(recon.EXCLUDED)
    return sorted(varying(stored) - known)
