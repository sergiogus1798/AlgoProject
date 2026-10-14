"""The calendar null: how far each cell's mean per lot strays when the same trades are shuffled across cells.

Two shuffles, one per kind of cell (the table is the README's §The null):

| dimension | what is held fixed | what is shuffled |
|---|---|---|
| weekday, hour | each UTC year-month's trades and their values; each cell's trade count | which of that month's trades sits in which cell |
| month | each year-month block whole (its trades, its sum) | which calendar month each block is called |

Shuffling inside a year-month keeps a volatile month, or equity that grew, from reading as an
hour or a day; relabelling whole blocks keeps a trend inside one July from counting as many
independent Julys. Both are exchangeable under «the calendar does not matter».
"""

import numpy as np

CHUNK = 1000  # draws per pass: CHUNK x trades floats in memory at once


def onehot(codes: np.ndarray, k: int) -> np.ndarray:
    """codes (n,) in 0..k-1 as an n x k matrix of 0/1."""
    out = np.zeros((codes.size, k))
    out[np.arange(codes.size), codes] = 1.0
    return out


def _p(ge: np.ndarray, le: np.ndarray, draws: int) -> np.ndarray:
    """Two-sided Monte Carlo p from the counts of draws at or beyond the observed, each side."""
    return np.minimum(1.0, 2 * (np.minimum(ge, le) + 1) / (draws + 1))


def within_strata(
    values: np.ndarray,
    strata: np.ndarray,
    hot: np.ndarray,
    draws: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """Two-sided p of each cell's sum, shuffling values only inside their stratum.

    One shuffle serves every cell family at once: the columns of `hot` may stack several
    dimensions and anchors, since the shuffle does not depend on them. Within a stratum each
    cell keeps its trade count, so a cell's sum and its mean rank the draws alike.

    Args:
        values: Per-trade value (account currency per lot).
        strata: Per-trade stratum id (any integers).
        hot: n x K 0/1 matrix, trade i in cell j.
        draws: Shuffles.
        rng: Seeded generator.

    Returns:
        (K,) p per cell; NaN for a cell with no trade.
    """
    order = np.argsort(strata, kind="stable")
    values, hot = values[order], hot[order]
    rank = np.unique(strata[order], return_inverse=True)[1].astype(float)
    observed = values @ hot
    ge, le = np.zeros(hot.shape[1]), np.zeros(hot.shape[1])
    for start in range(0, draws, CHUNK):
        b = min(CHUNK, draws - start)
        # rank + U(0,1) sorts every trade inside its own stratum, in random order there
        idx = np.argsort(rank[None, :] + rng.random((b, values.size)), axis=1)
        sums = values[idx] @ hot
        ge += (sums >= observed - 1e-9).sum(axis=0)
        le += (sums <= observed + 1e-9).sum(axis=0)
    return np.where(hot.sum(axis=0) > 0, _p(ge, le, draws), np.nan)


def relabel_blocks(
    values: np.ndarray,
    blocks: np.ndarray,
    hot: np.ndarray,
    draws: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """Two-sided p of each cell's mean, permuting which cell each whole block belongs to.

    Args:
        values: Per-trade value (account currency per lot).
        blocks: Per-trade block id; every trade of one block shares one cell.
        hot: n x k 0/1 matrix, trade i in cell j (a function of the block).
        draws: Permutations.
        rng: Seeded generator.

    Returns:
        (k,) p per cell; NaN for a cell with no trade. A permuted cell that gets no block has
        no mean and counts on neither side, which only makes p larger.
    """
    ids, inverse = np.unique(blocks, return_inverse=True)
    block_sum = np.bincount(inverse, weights=values)
    block_n = np.bincount(inverse).astype(float)
    block_cell = np.zeros(ids.size, dtype=int)
    block_cell[inverse] = hot.argmax(axis=1)
    k = hot.shape[1]
    hot = onehot(block_cell, k)
    count = block_n @ hot
    with np.errstate(invalid="ignore", divide="ignore"):
        observed = (block_sum @ hot) / count
    ge, le = np.zeros(k), np.zeros(k)
    for start in range(0, draws, CHUNK):
        b = min(CHUNK, draws - start)
        cells = block_cell[np.argsort(rng.random((b, ids.size)), axis=1)]
        rows = np.repeat(np.arange(b), ids.size)
        sums, ns = np.zeros((b, k)), np.zeros((b, k))
        np.add.at(sums, (rows, cells.ravel()), np.tile(block_sum, b))
        np.add.at(ns, (rows, cells.ravel()), np.tile(block_n, b))
        with np.errstate(invalid="ignore", divide="ignore"):
            means = sums / ns
        ge += (means >= observed - 1e-12).sum(axis=0)
        le += (means <= observed + 1e-12).sum(axis=0)
    return np.where(count > 0, _p(ge, le, draws), np.nan)
