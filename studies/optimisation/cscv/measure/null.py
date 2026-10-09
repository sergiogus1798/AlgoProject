"""The panel with nothing to choose: every column at one Sharpe, its weeks redrawn with replacement."""

import numpy as np

from engines.resample import draws
from studies.optimisation.cscv.measure import cscv, outputs

WEEKS = 52          # a year, to turn an annual Sharpe into a weekly one
# One stream per (kind, draw), whatever process runs it: the null on net, the null on gross,
# then one kind per planted Sharpe.
NET, GROSS, PLANTED = 0, 1, 2


def standard(values: np.ndarray) -> dict:
    """The panel with each column's own mean and deviation taken out.

    Args:
        values: Weeks down, variants across; every column moves.

    Returns:
        `u` (mean 0, deviation 1 with ddof=1, per column), `u2` (its square) and `m`, the
        median over columns of mean / deviation: the panel's median Sharpe per week.
    """
    mean, spread = values.mean(axis=0), values.std(axis=0, ddof=1)
    u = (values - mean) / spread
    return {"u": u, "u2": u * u, "m": float(np.median(mean / spread))}


def redrawn(shared: dict, rows: np.ndarray, mean: np.ndarray, blocks: int) -> dict:
    """Block sums of the equalised panel at redrawn weeks, without building the panel.

    Every column is `u + mean`: deviation 1 and Sharpe `mean`, so the common deviation of
    the proposal (its `s`) cancels in every Sharpe and is taken as 1.

    Args:
        shared: What standard() returned.
        rows: The week drawn at each position, the same for every column.
        mean: Each column's mean per week: the panel's median Sharpe, plus what is planted.
        blocks: Contiguous pieces of the redrawn history.

    Returns:
        What `cscv.sums` would return for `(u + mean)[rows]`.
    """
    weeks = len(shared["u"])
    times = np.stack([np.bincount(piece, minlength=weeks)
                      for piece in np.array_split(rows, blocks)]).astype(np.float64)
    n = times.sum(axis=1)
    s1, s2 = times @ shared["u"], times @ shared["u2"]
    return {"n": n, "s1": s1 + n[:, None] * mean,
            "s2": s2 + 2 * mean * s1 + n[:, None] * mean * mean}


def draw(shared: dict, member: np.ndarray, seed: int, kind: int, index: int, delta: float,
         knobs: dict) -> dict:
    """One CSCV on one bootstrap sample of the equalised panel.

    Args:
        shared: What standard() returned for the panel (net or gross).
        member: `cscv.partitions`.
        seed: The run's root seed.
        kind: NET, GROSS, or PLANTED + the position of `delta` among the planted Sharpes.
        index: Which draw; (kind, index) is the stream's spawn key under the root seed.
        delta: Annual Sharpe added to a share of the columns; 0 for the null.
        knobs: `blocks`, `block_weeks`, `share`, `chunk`, `bins`, `reach`, `tolerance`.

    Returns:
        `outputs.summary` of that sample. The weeks come from the stationary bootstrap of
        Politis and Romano (geometric blocks of mean `block_weeks`, with replacement), then
        the planted columns are drawn afresh in every sample.
    """
    rng = np.random.default_rng(np.random.SeedSequence(seed, spawn_key=(kind, index)))
    weeks, width = shared["u"].shape
    rows = draws.stationary(1, weeks, rng, knobs["block_weeks"])[0]
    mean = np.full(width, shared["m"])
    if delta:
        mean[rng.choice(width, max(1, round(knobs["share"] * width)), replace=False)] += (
            delta / np.sqrt(WEEKS))
    found = cscv.run(redrawn(shared, rows, mean, knobs["blocks"]), member, knobs["chunk"],
                     knobs["bins"], knobs["reach"])
    return outputs.summary(found, knobs["tolerance"])
