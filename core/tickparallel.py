"""`tickfile.read` in parallel: a walk over the record headers finds where each block starts, and jobs
of whole blocks are decoded at once.

Every block begins with an absolute record (time, ask and bid stored as-is, checked on 1.81 M blocks
of four feeds), so a job can start at any block with no running state. A minute belongs to the job
that holds its FIRST tick: that job reads on past its last record until the minute ends, and the next
job skips the ticks of that minute (it learns the minute by decoding the one block before its start).
So every minute is folded by one job, tick by tick in file order, exactly as `tickfile._minutes`
does: the result is bit-identical to the serial decode.
"""

import numpy as np
from numba import njit, prange

from core.tickfile import BLOCK, CHAIN, MINUTE, PRICE, Num, _apply, _value

# No `cache=True` here: numba keys its disk cache on THIS file only, and these kernels inline the decoders of
# core/tickfile.py, so an edit there would leave stale machine code that differs silently from the serial read.
JOB_BLOCKS = 4096          # blocks per job: 4 M ticks, ~20 ms of decoding each, ~100 jobs on a big feed


@njit
def skeleton(buf: np.ndarray, start: int) -> tuple[np.ndarray, int, bool]:
    """Walk the headers only: where each block's first record is, how many records, all-absolute?

    Stops where `tickfile._minutes` stops (a record that does not fit), so the counts agree.

    Returns:
        (position of each block's first record, number of records, True when the first record of
        every block stores time, ask and bid as-is).
    """
    size = len(buf)
    starts = np.empty(len(buf) // (BLOCK * 6) + 2, np.int64)
    pos, count, blocks, here, absolute = start, 0, 0, 0, True
    while pos + 6 <= size:
        if count % BLOCK == 0:
            pos += CHAIN
            here = pos
        if pos + 6 > size:
            break
        c0, c1 = buf[pos], buf[pos + 1]
        need = 2 + (1 << ((c0 >> 4) & 3)) + (1 << (c0 & 3)) + (1 << ((c1 >> 4) & 3)) + (1 << (c1 & 3))
        if pos + need > size:
            break
        if count % BLOCK == 0:
            starts[blocks] = here
            blocks += 1
            absolute = absolute and ((c0 >> 6) & 3) == 2 and ((c0 >> 2) & 3) == 2 and ((c1 >> 6) & 3) == 2
        pos += need
        count += 1
    return starts[:blocks], count, absolute


@njit
def _last_minute(buf: np.ndarray, pos: int) -> Num:
    """The minute of the last tick of the full block whose chain starts at `pos`."""
    t = a = b = vol = np.int64(0)  # noqa: F841 numba typing
    pos += CHAIN
    for _ in range(BLOCK):
        c0, c1 = buf[pos], buf[pos + 1]
        pos += 2
        v, pos = _value(buf, pos, (c0 >> 4) & 3)
        t = _apply(t, v, (c0 >> 6) & 3)
        for w in ((c0 & 3), ((c1 >> 4) & 3), (c1 & 3)):
            v, pos = _value(buf, pos, w)
    return t // MINUTE


@njit
def _job(buf: np.ndarray, pos: int, records: int, left: int, skip: int, minute: np.ndarray,
         out: np.ndarray) -> int:
    """Fold the minutes that start in `records` ticks from the chain at `pos`; the rows used.

    Same arithmetic as `tickfile._minutes`. Ticks of minute `skip` at the start belong to the
    previous job and are passed over; the last minute is read to its end even past `records`
    (never past `left`, the ticks the file still holds). Returns -1 when the rows given do not fit.
    """
    rows, count = -1, 0
    t = a = b = vol = np.int64(0)
    cur, t_last, s_last, acc, t_first = np.int64(-1), np.int64(0), 0.0, 0.0, np.int64(0)
    while count < left:
        if count % BLOCK == 0:
            pos += CHAIN
        c0, c1 = buf[pos], buf[pos + 1]
        pos += 2
        v, pos = _value(buf, pos, (c0 >> 4) & 3)
        t = _apply(t, v, (c0 >> 6) & 3)
        v, pos = _value(buf, pos, c0 & 3)
        a = _apply(a, v, (c0 >> 2) & 3)
        v, pos = _value(buf, pos, (c1 >> 4) & 3)
        b = _apply(b, v, (c1 >> 6) & 3)
        v, pos = _value(buf, pos, c1 & 3)
        vol = _apply(vol, v, (c1 >> 2) & 3)
        count += 1
        spread, bid, m = (a - b) / PRICE, b / PRICE, t // MINUTE
        if count > records and m != cur:
            break
        if rows < 0 and m == skip:
            continue
        if m != cur:
            if rows + 1 >= len(minute):
                return -1
            if rows >= 0:
                end = (cur + 1) * MINUTE
                out[rows, 2] = (acc + s_last * (end - t_last)) / (end - t_first)
            rows += 1
            cur, acc, t_first = m, 0.0, t
            minute[rows] = m * MINUTE
            out[rows, 0] = 0
            out[rows, 1] = spread
            out[rows, 3] = spread
            out[rows, 4] = spread
            out[rows, 5] = bid
            out[rows, 6] = bid
            out[rows, 7] = bid
        else:
            acc += s_last * (t - t_last)
        out[rows, 0] += 1
        out[rows, 3] = min(out[rows, 3], spread)
        out[rows, 4] = max(out[rows, 4], spread)
        out[rows, 6] = max(out[rows, 6], bid)
        out[rows, 7] = min(out[rows, 7], bid)
        out[rows, 8] = bid
        t_last, s_last = t, spread
    if rows >= 0:
        end = (cur + 1) * MINUTE
        out[rows, 2] = (acc + s_last * (end - t_last)) / (end - t_first)
    return rows + 1


@njit(parallel=True)
def _jobs(buf: np.ndarray, starts: np.ndarray, size: int, per_job: np.ndarray, skip: np.ndarray,
          room: np.ndarray, minute: np.ndarray, out: np.ndarray, used: np.ndarray) -> None:
    """Run every job (`size` blocks each) at once; job j writes into rows room[j]..room[j+1]."""
    for j in prange(len(per_job) - 1):
        lo = room[j]
        used[j] = _job(buf, starts[j * size] - CHAIN, per_job[j + 1] - per_job[j],
                       per_job[-1] - per_job[j], skip[j], minute[lo:room[j + 1]], out[lo:room[j + 1]])


def decode(buf: np.ndarray, start: int, size: int = JOB_BLOCKS) -> tuple[np.ndarray, np.ndarray, int] | None:
    """`tickfile._minutes` by jobs of `size` blocks; None when it cannot be trusted.

    None means: a block does not start from an absolute record, the file is small, or ticks go back
    in time (a job would outgrow its rows). The caller then decodes serially.

    Returns:
        (minute open times in ms, the nine columns, tick count), as `_minutes` does.
    """
    starts, count, absolute = skeleton(buf, start)
    if not absolute or len(starts) < 2 * size:
        return None
    jobs = -(-len(starts) // size)
    per_job = np.minimum(np.arange(jobs + 1) * size * BLOCK, count)
    first = np.array([_value(buf, int(s) + 2, 3)[0] for s in starts[::size]])
    if (np.diff(first) < 0).any():          # time back at a job edge: the rows of a job could go negative
        return None
    nxt = np.append(first[1:], first[-1] + (per_job[-1] - per_job[-2]) * MINUTE)   # a loose bound for the tail
    room = np.concatenate([[0], np.cumsum(np.minimum((nxt - first) // MINUTE + 2, per_job[1:] - per_job[:-1]))])
    minute, out = np.empty(room[-1], np.int64), np.empty((room[-1], 9), np.float64)
    used = np.zeros(jobs, np.int64)
    skip = np.array([-1] + [_last_minute(buf, int(starts[j * size - 1]) - CHAIN) for j in range(1, jobs)])
    _jobs(buf, starts, size, per_job, skip, room, minute, out, used)
    if (used < 0).any():
        return None
    keep = np.concatenate([np.arange(room[j], room[j] + used[j]) for j in range(jobs)])
    return minute[keep], out[keep], int(count)
