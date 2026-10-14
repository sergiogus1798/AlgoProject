"""numpy's `Generator.permuted` and its sums inside one numba kernel: the gate's Q under shuffles, no matrix held."""

import numpy as np
from numba import njit

from engines.nulls import pcg

_M32, _S1, _S32 = np.uint64(2**32 - 1), np.uint64(1), np.uint64(32)


def between(
    centred: np.ndarray,
    starts: np.ndarray,
    sizes: np.ndarray,
    permutations: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """The between-period sum of squares of every shuffle of the trades across periods.

    Args:
        centred: One figure per trade minus their mean, each period's trades together.
        starts, sizes: Where each period begins and how many trades it holds.
        permutations: How many shuffles.
        rng: A PCG64 generator (`engines.nulls.pcg`); left where `rng.permuted` would leave it.

    Returns:
        One per shuffle, bit for bit `(np.add.reduceat(rng.permuted(rows, axis=1), starts,
        axis=1) ** 2 / sizes).sum(axis=1)` over `permutations` copies of `centred`.
    """
    if (
        sizes[-1] < 1
    ):  # an empty period inside is read as numpy does; a trailing one starts past the last trade
        raise ValueError(
            "the last period is empty: the kernel would read past the trades"
        )
    state, inc = pcg.load(rng)
    out = np.empty(permutations)
    _shuffled(
        np.asarray(centred, float),
        starts.astype(np.int64),
        sizes.astype(float),
        state,
        pcg.jump(inc, 1),
        out,
    )
    pcg.store(rng, state)
    return out


@njit(cache=True, nogil=True)
def _leaf(a: np.ndarray, lo: int, n: int) -> float:
    """numpy's sum of up to 128 doubles from a[lo]: eight running sums, then the tail."""
    total, whole = 0.0, n - n % 8 if n >= 8 else 0
    if whole:
        r0, r1, r2, r3 = a[lo], a[lo + 1], a[lo + 2], a[lo + 3]
        r4, r5, r6, r7 = a[lo + 4], a[lo + 5], a[lo + 6], a[lo + 7]
        for i in range(lo + 8, lo + whole, 8):
            r0, r1, r2, r3 = r0 + a[i], r1 + a[i + 1], r2 + a[i + 2], r3 + a[i + 3]
            r4, r5, r6, r7 = r4 + a[i + 4], r5 + a[i + 5], r6 + a[i + 6], r7 + a[i + 7]
        total = ((r0 + r1) + (r2 + r3)) + ((r4 + r5) + (r6 + r7))
    for i in range(lo + whole, lo + n):
        total += a[i]
    return total


@njit(cache=True, nogil=True)
def _pairwise(a: np.ndarray, lo: int, n: int) -> float:
    """numpy's pairwise sum of n doubles from a[lo]; a stack, since numba's cache breaks recursion."""
    if n <= 128:
        return _leaf(a, lo, n)
    todo, sums, t, k = np.empty((128, 2), np.int64), np.empty(64), 1, 0
    todo[0] = lo, n
    while t:
        t -= 1
        at, m = todo[t]
        if m < 0:  # both halves summed: left + right
            k -= 1
            sums[k - 1] += sums[k]
        elif m <= 128:
            sums[k] = _leaf(a, at, m)
            k += 1
        else:
            half = m // 2 - m // 2 % 8
            todo[t], todo[t + 1], todo[t + 2] = (
                (0, -1),
                (at + half, m - half),
                (at, half),
            )
            t += 3
    return sums[0]


# No cache=True: this inlines engines/nulls/pcg.py, and numba does not invalidate a disk cache when only that file changes.
@njit(nogil=True, error_model="numpy")
def _shuffled(
    centred: np.ndarray,
    starts: np.ndarray,
    sizes: np.ndarray,
    st: np.ndarray,
    one: np.ndarray,
    out: np.ndarray,
) -> None:
    """between()'s statistic of one shuffle per entry of `out`.

    `st` is what `pcg.load` gave and `one` its single step; `st` ends where numpy would be. The
    shuffle is `Generator.permuted`'s: Fisher-Yates from the last trade down, each index a
    masked 32-bit half of a 64-bit word, redrawn while above i. The sums are numpy's:
    `reduceat` is a[0] + pairwise(the rest), `.sum()` pairwise over the row.
    """
    n, g = centred.size, sizes.size
    hi, lo, have, spare = st[0], st[1], st[2] != 0, st[3]
    work, term = np.empty(n), np.empty(g)
    for p in range(out.size):
        work[:] = centred
        mask = _M32
        for i in range(n - 1, 0, -1):
            top = np.uint64(i)
            while top <= mask >> _S1:
                mask >>= _S1
            while True:
                if have:
                    v, have = spare, False
                else:
                    hi, lo = pcg.step(hi, lo, one)
                    x = pcg.word(hi, lo)
                    v, spare, have = x & _M32, x >> _S32, True
                v &= mask
                if v <= top:
                    break
            j = np.int64(v)
            work[i], work[j] = work[j], work[i]
        for b in range(g):
            count = (starts[b + 1] if b + 1 < g else n) - starts[b]
            # reduceat hands back the element itself where a period is empty
            s = work[starts[b]] + (
                _pairwise(work, starts[b] + 1, count - 1) if count > 1 else 0.0
            )
            term[b] = s * s / sizes[b]
        out[p] = _pairwise(term, 0, g)
    st[0], st[1], st[2], st[3] = hi, lo, np.uint64(have), spare
