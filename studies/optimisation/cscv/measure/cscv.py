"""Combinatorially symmetric cross-validation off block sums: each half of the blocks chooses, the other judges."""

import itertools

import numpy as np
from numba import njit

# A half whose n·Σx² − (Σx)² is under this share of n·Σx² never moved: its Sharpe reads 0.
FLAT = 1e-12


def partitions(blocks: int) -> np.ndarray:
    """The halves of the blocks that contain the first one, as a 0/1 matrix.

    Args:
        blocks: Contiguous pieces the history is cut into; 16 gives C(15,7) = 6,435 rows.

    Returns:
        Halves x blocks. Each row and its complement are two partitions (in and out swapped),
        so the C(16,8) = 12,870 partitions are these rows read both ways.

    Raises:
        ValueError: `blocks` is odd, which is not the published statistic (halves must be equal).
    """
    if blocks % 2 or blocks < 2:
        raise ValueError(f"CSCV needs an even number of blocks (at least 2), got {blocks}: "
                         "the published statistic splits them into two equal halves")
    rest = np.array(list(itertools.combinations(range(1, blocks), blocks // 2 - 1)))
    member = np.zeros((len(rest), blocks))
    member[:, 0] = 1.0
    np.put_along_axis(member, rest, 1.0, axis=1)
    return member


def sums(values: np.ndarray, blocks: int) -> dict:
    """Each block's rows, column sums and sums of squares: all a partition ever reads.

    Args:
        values: Weeks down, variants across.
        blocks: Contiguous pieces of near-equal length (they differ by one row at most).

    Returns:
        `n` (blocks,), `s1` and `s2` (blocks x variants).
    """
    pieces = np.array_split(values, blocks)
    return {"n": np.array([len(p) for p in pieces], dtype=np.float64),
            "s1": np.stack([p.sum(axis=0) for p in pieces]),
            "s2": np.stack([np.square(p).sum(axis=0) for p in pieces])}


def sharpe(n: np.ndarray, s1: np.ndarray, s2: np.ndarray, safe: bool) -> np.ndarray:
    """Per-period Sharpe (deviation with ddof=1) from sums; `s2` is overwritten.

    Args:
        n: Rows summed, one per row of `s1` (a column) or a scalar.
        s1, s2: Sums and sums of squares.
        safe: True when no entry can have zero variance, which skips the guard.

    Returns:
        mean / deviation = s1 · sqrt((n − 1) / n) / sqrt(n · s2 − s1²); 0 where nothing moved.
    """
    scale = np.sqrt((n - 1.0) / n)
    s2 *= n
    floor = None if safe else s2 * FLAT
    s2 -= s1 * s1
    if safe:
        np.sqrt(s2, out=s2)
        np.divide(s1, s2, out=s2)
        s2 *= scale
        return s2
    moved = s2 > floor
    np.sqrt(s2, out=s2, where=moved)
    out = np.zeros_like(s1)
    np.divide(s1, s2, out=out, where=moved)
    out *= scale
    return out


def edges(got: dict, reach: float) -> tuple[float, float]:
    """The range of half-sample Sharpes worth a bin: the full-sample ones, widened.

    Args:
        got: What sums() returned.
        reach: Standard errors of a half-sample Sharpe (1 / sqrt(rows of a half)) added on
            each side; what falls beyond lands in the end bins.
    """
    n = got["n"].sum()
    whole = sharpe(n, got["s1"].sum(axis=0), got["s2"].sum(axis=0), False)
    wide = reach / np.sqrt(n / 2)
    return float(whole.min() - wide), float(whole.max() + wide)


@njit(cache=True, nogil=True)
def _rows(train: np.ndarray, test: np.ndarray, track: int, lo: float, per_bin: float, to: int,
          pick: np.ndarray, sr_in: np.ndarray, sr_out: np.ndarray, omega: np.ndarray,
          own: np.ndarray, own_omega: np.ndarray, hist: np.ndarray) -> None:
    """One pass per partition: the pick in `train`, its rank in `test`, and `test`'s histogram.

    Args:
        train, test: Partitions x variants, the Sharpes that choose and the ones that judge.
        track: The column followed, or -1 for none (`own` and `own_omega` are then not written).
        lo, per_bin: Left edge of the histogram and bins per unit of Sharpe.
        to: Where this chunk starts in the per-partition outputs.
        pick, sr_in, sr_out, omega, own, own_omega, hist: Written in place, as run() returns them.

    A NaN wins the choice (the first one, as `argmax`) and, like anything beyond int64, counts in
    bin 0: what the cast to int64 gave on x86 before this kernel.
    """
    width, last = train.shape[1], hist.size - 1
    for i in range(train.shape[0]):
        best, at = train[i, 0], 0
        for j in range(1, width):
            v = train[i, j]
            if v > best or (v != v and best == best):
                best, at = v, j
        chosen, mine = test[i, at], test[i, max(track, 0)]
        below = under = 0
        for j in range(width):
            v = test[i, j]
            below += v < chosen
            under += v < mine
            x, cell = (v - lo) * per_bin, 0
            if x >= 0.0:
                cell = np.int64(x) if x <= last else last if x < 9.223372036854775807e18 else 0
            hist[cell] += 1
        pick[to + i], sr_in[to + i], sr_out[to + i] = at, best, chosen
        omega[to + i] = (below + 1) / (width + 1)
        if track >= 0:
            own[to + i], own_omega[to + i] = mine, (under + 1) / (width + 1)


def run(got: dict, member: np.ndarray, chunk: int, bins: int, reach: float,
        track: int | None = None) -> dict:
    """Choose by Sharpe in one half and score in the other, for every partition.

    Args:
        got: What sums() returned.
        member: What partitions() returned.
        chunk: Halves scored at once; bounds the working set to a dozen chunk x variants arrays.
        bins: Bins of the histogram of every variant's out-of-sample Sharpe.
        reach: As edges().
        track: A column whose own out-of-sample Sharpe and rank are kept (the mother).

    Returns:
        One entry per partition (2 x halves; the second half of each array is the complements):
        `pick` (column chosen), `sr_in`, `sr_out` (its per-period Sharpe in and out), `omega`
        (its relative rank out, (1 + #below) / (N + 1)); `hist` (bins,) the count of all
        variants' out-of-sample Sharpes over `lo`..`hi`; with `track`, `track_out` and
        `track_omega`.
    """
    n, s1, s2 = got["n"], got["s1"], got["s2"]
    all_n, all1, all2 = n.sum(), s1.sum(axis=0), s2.sum(axis=0)
    # A half is half the blocks: it has variance as soon as one of its blocks has.
    flat = (n[:, None] * s2 - s1 * s1 <= FLAT * n[:, None] * s2).sum(axis=0)
    safe = bool(flat.max() < len(n) // 2)
    halves, width = member.shape[0], s1.shape[1]
    lo, hi = edges(got, reach)
    per_bin = bins / (hi - lo)
    out = {"pick": np.empty(2 * halves, np.int64), "sr_in": np.empty(2 * halves),
           "sr_out": np.empty(2 * halves), "omega": np.empty(2 * halves),
           "hist": np.zeros(bins, np.int64), "lo": lo, "hi": hi}
    if track is not None:
        out |= {"track_out": np.empty(2 * halves), "track_omega": np.empty(2 * halves)}
    own, own_omega = out.get("track_out", out["omega"]), out.get("track_omega", out["omega"])
    for at in range(0, halves, chunk):
        take = member[at:at + chunk]
        size = (take @ n)[:, None]
        a1, a2 = take @ s1, take @ s2
        b1, b2 = all1 - a1, all2 - a2
        first, second = sharpe(size, a1, a2, safe), sharpe(all_n - size, b1, b2, safe)
        for side, (train, test) in enumerate(((first, second), (second, first))):
            _rows(train, test, -1 if track is None else track, lo, per_bin, at + side * halves,
                  out["pick"], out["sr_in"], out["sr_out"], out["omega"], own, own_omega,
                  out["hist"])
    return out
