"""Read SQX's own history files without SQX: a tick feed into one row per minute of spread, an M1 feed into bars.

The format, read from `SQDataLib.jar` (`newDataFormat.TickDataReader`, 2026-09-27): a header of
Java UTF strings — version "4.2", type "D" (plain; "C" is encrypted and refused), "ABCDEFGH", a
long, an int count of (UTF, int) pairs, and "SnRbTs" — then records. Every 1,000 records a
15-byte magic chain 0..14 and a 4-byte block index. A record is two config bytes and four
big-endian unsigned values — time, ask, bid, volume — each 1, 2, 4 or 8 bytes wide and applied
to the previous one as minus, plus or as-is; the two bits of each come from the config bytes.
Prices are integers over 10^6. Times are milliseconds on the feed's own naive clock, the same
clock as its bars (`knowhow/export/feed-clock-timezones.md`).

Ticks are never held: hundreds of millions per feed. Each minute keeps what a spread study reads.
An M1 file (`*_M1.dat`, `OhlcDataReader`) is the same format with three config bytes and six
values — time, open, high, low, close, volume; c0 = time<<4 | open, c1 = high<<4 | low,
c2 = close<<4 | volume, each nibble logic<<2 | width.
"""

from pathlib import Path

import numpy as np
import pandas as pd
from numba import njit

from core.datapaths import bar_file, tick_file

PRICE = 1e6
BLOCK = 1000
CHAIN = 15 + 4
MINUTE = 60_000
COLUMNS = ("n", "spread_open", "spread_twa", "spread_min", "spread_max",
           "bid_open", "bid_high", "bid_low", "bid_close")


def _utf(buf: np.ndarray, pos: int) -> tuple[str, int]:
    """One Java `readUTF` string and the position after it."""
    size = int(buf[pos]) << 8 | int(buf[pos + 1])
    return bytes(buf[pos + 2:pos + 2 + size]).decode(), pos + 2 + size


def _data_start(buf: np.ndarray) -> int:
    """Check the header and return where the first magic chain starts."""
    version, pos = _utf(buf, 0)
    kind, pos = _utf(buf, pos)
    assert (version, kind) == ("4.2", "D"), f"tick file {version!r}/{kind!r}: only plain 4.2 is read"
    _, pos = _utf(buf, pos)
    pos += 8
    pairs = int.from_bytes(bytes(buf[pos:pos + 4]), "big")
    pos += 4
    for _ in range(pairs):
        _, pos = _utf(buf, pos)
        pos += 4
    end, pos = _utf(buf, pos)
    assert end == "SnRbTs", "tick file header damaged"
    return pos


@njit(cache=True)
def _value(buf: np.ndarray, pos: int, width: int) -> tuple[int, int]:
    """An unsigned big-endian integer of 1, 2, 4 or 8 bytes."""
    n = 1 << width
    v = np.int64(0)
    for i in range(n):
        v = (v << 8) | np.int64(buf[pos + i])
    return v, pos + n


@njit(cache=True)
def _apply(prev: int, v: int, logic: int) -> int:
    """Minus, plus or as-is: how a stored value moves the running one."""
    if logic == 0:
        return prev - v
    if logic == 1:
        return prev + v
    return v


@njit(cache=True)
def _minutes(buf: np.ndarray, start: int, capacity: int) -> tuple[np.ndarray, np.ndarray, int]:
    """Decode every tick and fold it into its minute; returns the filled rows."""
    minute = np.empty(capacity, np.int64)
    out = np.empty((capacity, 9), np.float64)
    pos, count, rows, size = start, 0, -1, len(buf)
    t = a = b = vol = np.int64(0)
    cur, t_last, s_last, acc, t_first = np.int64(-1), np.int64(0), 0.0, 0.0, np.int64(0)
    while pos + 6 <= size:
        if count % BLOCK == 0:
            pos += CHAIN
        if pos + 6 > size:
            break
        c0, c1 = buf[pos], buf[pos + 1]
        widths = (c0 >> 4) & 3, c0 & 3, (c1 >> 4) & 3, c1 & 3
        need = 2
        for w in widths:
            need += 1 << w
        if pos + need > size:
            break
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
        if m != cur:
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
    return minute[:rows + 1], out[:rows + 1], count


@njit(cache=True)
def _bars(buf: np.ndarray, start: int, capacity: int) -> tuple[np.ndarray, np.ndarray]:
    """Decode every M1 bar: times in ms and open, high, low, close."""
    stamp = np.empty(capacity, np.int64)
    out = np.empty((capacity, 4), np.float64)
    pos, count, size = start, 0, len(buf)
    prev = np.zeros(6, np.int64)
    order = np.array([0, 1, 2, 3, 4, 5])
    while pos + 9 <= size and count < capacity:
        if count % BLOCK == 0:
            pos += CHAIN
        if pos + 9 > size:
            break
        c = buf[pos], buf[pos + 1], buf[pos + 2]
        nibbles = ((c[0] >> 4) & 15, c[0] & 15, (c[1] >> 4) & 15, c[1] & 15, (c[2] >> 4) & 15, c[2] & 15)
        need = 3
        for nb in nibbles:
            need += 1 << (nb & 3)
        if pos + need > size:
            break
        pos += 3
        for k in order:
            v, pos = _value(buf, pos, nibbles[k] & 3)
            prev[k] = _apply(prev[k], v, nibbles[k] >> 2)
        stamp[count] = prev[0]
        for k in range(4):
            out[count, k] = prev[k + 1] / PRICE
        count += 1
    return stamp[:count], out[:count]


def bars(feed: str) -> pd.DataFrame:
    """One M1 feed of SQX's own history (`<feed>_M1.dat`) as bars, for feeds the bar library lacks.

    Returns:
        Open, High, Low, Close indexed by bar open time on the feed's clock. Matches the
        library's SQX export on 8,734,187 of 8,734,300 USDJPY bars; the rest are a duplicated
        hour in the file.
    """
    buf = np.memmap(bar_file(feed), np.uint8, mode="r")
    start = _data_start(buf)
    stamp, rows = _bars(buf, start, len(buf) // 9)
    frame = pd.DataFrame(rows, columns=["Open", "High", "Low", "Close"],
                         index=pd.to_datetime(stamp, unit="ms"))
    frame.index.name = "t"
    # Two hours of USDJPY 2003–2004 are stored twice; SQX's own export keeps the first.
    return frame[~frame.index.duplicated()].sort_index()


def read(path: Path) -> tuple[pd.DataFrame, int]:
    """One tick file as a minute table of spread and bid.

    Args:
        path: A `*_TICK.dat`.

    Returns:
        A frame indexed by minute open `t` (the feed's naive clock), only minutes that had a
        tick: `n` ticks; `spread_open` the spread of the minute's first tick — what a market
        order at that bar's open pays at DATATICK precision; `spread_twa` the spread weighted
        by how long each tick stood until the next or the minute's end; `spread_min/max`;
        and the bid's open/high/low/close. Spreads in price units. Plus the tick count.
    """
    buf = np.memmap(path, np.uint8, mode="r")
    start = _data_start(buf)
    first, _ = _value(np.asarray(buf[start + CHAIN + 2:start + CHAIN + 10]), 0, 3)
    capacity = int((pd.Timestamp.now().value // 1_000_000 - first) // MINUTE) + 2
    stamp, rows, ticks = _minutes(buf, start, capacity)
    frame = pd.DataFrame(rows, columns=COLUMNS, index=pd.to_datetime(stamp, unit="ms"))
    frame.index.name = "t"
    return frame.astype({"n": np.int32}), int(ticks)


def minutes(feed: str) -> tuple[pd.DataFrame, int]:
    """`read()` of one tick feed's history, e.g. "XAUUSD_TICK"."""
    return read(tick_file(feed))
