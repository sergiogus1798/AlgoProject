#!/usr/bin/env python3
"""The tick-file reader on a file written by hand, and a trade repriced at a spread worked out by hand."""

import struct
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import tickfile
from studies.data.spread import band, verdict

T0 = 1_600_000_020_000  # 2020-09-13 12:27:00 UTC, the start of a minute
WIDTH = {1: 0, 2: 1, 4: 2, 8: 3}
FMT = {1: ">B", 2: ">H", 4: ">I", 8: ">Q"}
MINUS, PLUS, ASIS = 0, 1, 2


def utf(text: str) -> bytes:
    """A Java writeUTF string."""
    return struct.pack(">H", len(text)) + text.encode()


def record(fields: list[tuple[int, int, int]]) -> bytes:
    """Two config bytes and four values; each field is (value, width in bytes, logic)."""
    (t, tw, tl), (a, aw, al), (b, bw, bl), (v, vw, vl) = fields
    c0 = tl << 6 | WIDTH[tw] << 4 | al << 2 | WIDTH[aw]
    c1 = bl << 6 | WIDTH[bw] << 4 | vl << 2 | WIDTH[vw]
    return bytes([c0, c1]) + b"".join(struct.pack(FMT[w], x) for x, w, _ in fields)


def write(path: Path, ticks: list[tuple[int, int, int]]) -> None:
    """A plain 4.2 tick file: the first tick as-is, every later one as a delta, a chain every 1,000."""
    out = [
        utf("4.2"),
        utf("D"),
        utf("ABCDEFGH"),
        struct.pack(">qi", 0, 0),
        utf("SnRbTs"),
    ]
    prev = None
    for n, (t, ask, bid) in enumerate(ticks):
        if n % 1000 == 0:
            out.append(bytes(range(15)) + struct.pack(">i", n // 1000))
        if prev is None:
            out.append(
                record([(t, 8, ASIS), (ask, 8, ASIS), (bid, 8, ASIS), (0, 1, ASIS)])
            )
        else:
            fields = []
            for now, was in ((t, prev[0]), (ask, prev[1]), (bid, prev[2])):
                d = now - was
                width = 1 if abs(d) < 256 else 2 if abs(d) < 65536 else 4
                fields.append((abs(d), width, PLUS if d >= 0 else MINUS))
            out.append(record(fields + [(0, 1, PLUS)]))
        prev = (t, ask, bid)
    path.write_bytes(b"".join(out))


def main() -> None:
    """Fail loudly on any value that is not the hand-computed one."""
    failures = []
    # Minute 1: 1,500 ticks every 40 ms, bid 100.000000 rising by 1e-6, spread alternating
    # 0.2 and 0.4 -> crosses a magic chain; minute 2: two ticks, spread 0.5 for 30 s then 0.1.
    ticks = [
        (
            T0 + 40 * i,
            100_000_000 + i + (200_000 if i % 2 == 0 else 400_000),
            100_000_000 + i,
        )
        for i in range(1500)
    ]
    ticks += [
        (T0 + 60_000, 101_500_000, 101_000_000),
        (T0 + 90_000, 101_100_000, 101_000_000),
    ]
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "X_TICK.dat"
        write(path, ticks)
        got, count = tickfile.read(path)
    first, second = got.iloc[0], got.iloc[1]
    checks = {
        "tick count": (count, 1502),
        "minutes": (len(got), 2),
        "minute stamp": (got.index[0], pd.Timestamp(T0, unit="ms")),
        "n": (first["n"], 1500),
        "spread_open": (first["spread_open"], 0.2),
        "spread_min/max": ((first["spread_min"], first["spread_max"]), (0.2, 0.4)),
        "bid open/close": (
            (first["bid_open"], first["bid_close"]),
            (100.0, 100.001499),
        ),
        # 0.2 and 0.4 alternate for 40 ms each; the last (i=1499, 0.4) stands 0 ms to the end
        "spread_twa": (round(first["spread_twa"], 9), 0.3),
        "second minute twa": (round(second["spread_twa"], 9), 0.3),
        "second minute open": (second["spread_open"], 0.5),
    }
    for name, (value, want) in checks.items():
        if (
            not np.allclose(
                np.asarray(value, float), np.asarray(want, float), rtol=0, atol=1e-9
            )
            if not isinstance(want, pd.Timestamp)
            else value != want
        ):
            failures.append(f"{name}: {value} != {want}")

    # A spread built as 2 · price^0.5 times lognormal noise: the mean's exponent must read 0.5
    # and the 2.5-97.5 % band must leave ~2.5 % out on each side.
    rng = np.random.default_rng(7)
    price = np.exp(rng.uniform(np.log(1000), np.log(30000), 2000))
    fake = pd.DataFrame(
        {"price": price, "spread": 2 * price**0.5 * np.exp(rng.normal(0, 0.2, 2000))},
        index=pd.date_range("2018-01-01", periods=2000, freq="D"),
    )
    curves = band.fit(fake, [0.025, 0.5, 0.975])
    out = band.coverage(fake, curves, "0.025", "0.975")
    below = (out["% por debajo"] * out["días"]).sum() / out["días"].sum()
    above = (out["% por encima"] * out["días"]).sum() / out["días"].sum()
    if abs(curves["media"]["b"] - 0.5) > 0.02 or not (
        1.5 < below < 3.5 and 1.5 < above < 3.5
    ):
        failures.append(
            f"band: b={curves['media']['b']:.3f}, fuera {below:.1f} % / {above:.1f} %"
        )

    # One definition of a segment's points: price doubles while the relative spread halves.
    # mean(rel) 1.5e-4 at mean price 150 with a 0.01 tick = 2.25 points, in the report's
    # table and in the function the onboarding calls.
    seg = pd.DataFrame(
        {"rel": [2e-4, 1e-4], "price": [100.0, 200.0], "source": "medido"},
        index=pd.to_datetime(["2020-01-01", "2020-01-02"]),
    )
    window = {
        "build": (
            seg.index[0].value // 10**6,
            (seg.index[-1] + pd.Timedelta(days=1)).value // 10**6,
        )
    }
    shown = verdict.propose(seg, window, 0.01, 1.0)["puntos equivalentes"].iloc[0]
    if not np.allclose([shown, verdict.points(seg, 0.01, 1.0)], 2.25):
        failures.append(
            f"points of a segment: report {shown}, onboard {verdict.points(seg, 0.01, 1.0)} != 2.25"
        )

    print("\n".join(failures) if failures else "ok")
    sys.exit(bool(failures))


if __name__ == "__main__":
    main()
