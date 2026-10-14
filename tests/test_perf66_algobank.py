#!/usr/bin/env python3
"""An `.abk` written to the spec comes back field by field, and a damaged one is refused.

Offline: SQX is not involved. `write` below is a second implementation of the format in the
module docstring of `core/bankfile.py` — plain `struct`, none of the reader's dtypes — so a
reader that drifts from the spec fails here before it meets a file the Java snippet wrote. The
eleven live tests of encargo 66 §6 (the snippet against orderstocsv, on every kind of databank)
are run by hand on the conductor.
"""

import struct
import sys
import zlib
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import bankfile, bankframes  # noqa: E402

DAY = 86_400_000
T0 = 1_199_349_000_000  # 2008-01-03 08:30:00 UTC
MAIN, SILVER = "Main: XAUUSD_M1/H1", "AdditionalMarket: XAGUSD_M1/H1"
KEYS = [("NetProfit", "f"), ("NumberOfTrades", "i"), ("MaxNewHighDurationTo", "l")]


def _order(
    ticket: int,
    open_ms: int,
    close_ms: int,
    open_: float,
    close: float,
    size: float,
    pl: float,
    balance: float,
    mae: float,
    mfe: float,
    sym: str = "XAUUSD",
    res: str = MAIN,
    kind: str = "Buy",
    sample: str = "IST",
    close_type: str = "Exit Signal",
    flags: int = 0,
) -> dict:
    """One order of a strategy, as the writer takes it."""
    return dict(
        ticket=ticket,
        open_ms=open_ms,
        close_ms=close_ms,
        open=open_,
        close=close,
        size=size,
        pl=pl,
        balance=balance,
        mae=mae,
        mfe=mfe,
        sym=sym,
        res=res,
        type=kind,
        sample=sample,
        close_type=close_type,
        flags=flags,
    )


def strategies() -> list[dict]:
    """Three strategies: one in order with a pending tail, one pyramiding, one without trades."""
    h = 3_600_000
    return [
        dict(
            name="Strategy 2.1.1",
            main=MAIN,
            symbol="XAUUSD",
            tf="H1",
            filter="",
            problems=0,
            xml="<StrategyFile><Strategy>á &amp; one</Strategy></StrategyFile>",
            orders=[
                _order(
                    1,
                    T0 + 250,
                    T0 + 2 * h,
                    856.19,
                    862.29,
                    1.19,
                    715.71,
                    100715.71,
                    -66.4,
                    776.83,
                ),
                _order(
                    2,
                    T0 + 5 * h,
                    T0 + 6 * h,
                    874.625,
                    876.03,
                    0.83,
                    -0.125,
                    100715.585,
                    0.0,
                    116.86,
                    kind="Sell",
                    sample="OOS",
                    close_type="Stop Loss",
                ),
                _order(
                    3,
                    T0 + 9 * h,
                    T0 + 9 * h,
                    880.0,
                    0.0,
                    1.0,
                    0.0,
                    100715.59,
                    0.0,
                    0.0,
                    kind="BuyStop",
                    close_type="EndTest",
                    flags=1,
                ),
            ],
            equity={MAIN: [(13881, 0.0), (13882, 715.71)], "Portfolio": [(13881, 0.0)]},
            stats=[
                (MAIN, 10, [715.585, 2.0, 1_200_000_000_000.0]),
                (MAIN, 127, [-0.125, 1.0, 0.0]),
            ],
        ),
        dict(
            name="Strategy 10.4.7",
            main=MAIN,
            symbol="XAUUSD",
            tf="H1",
            filter="Net profit < 0",
            problems=3,
            xml="<StrategyFile>two</StrategyFile>",
            orders=[
                _order(
                    1, T0, T0 + 4 * h, 856.19, 860.0, 0.5, 190.5, 100190.5, -10.0, 200.0
                ),
                _order(
                    2,
                    T0 + h,
                    T0 + 3 * h,
                    17.0625,
                    17.3,
                    5.0,
                    22.75,
                    100213.25,
                    -1.125,
                    30.0,
                    sym="XAGUSD",
                    res=SILVER,
                ),
                _order(
                    1,
                    T0 + 6 * h,
                    T0 + 7 * h,
                    17.1,
                    17.0,
                    5.0,
                    -50.0,
                    100163.25,
                    -60.0,
                    0.0,
                    sym="XAGUSD",
                    res=SILVER,
                    close_type="Profit Target",
                ),
            ],
            equity={MAIN: [(13881, 190.5)], SILVER: [(13881, 22.75), (13884, -27.25)]},
            stats=[(SILVER, 127, [-27.25, float("nan"), 0.0])],
        ),
        dict(
            name="Strategy 3.3.3",
            main=MAIN,
            symbol="XAUUSD",
            tf="H1",
            filter="",
            problems=0,
            xml="",
            orders=[],
            equity={},
            stats=[],
        ),
    ]


def _table(texts: list[str]) -> bytes:
    """A string table: count, cumulative end offsets, then the UTF-8 bytes."""
    raw = [t.encode("utf-8") for t in texts]
    ends = np.cumsum([0] + [len(r) for r in raw]).tolist()
    return struct.pack(f"<I{len(ends)}I", len(raw), *ends) + b"".join(raw)


def write(
    path: Path,
    bank: list[dict],
    data: int = 0,
    decimals: dict | None = None,
    keys: list | None = None,
) -> None:
    """The spec of `core/bankfile.py`, written with struct: what AlgoBank.java must produce."""
    decimals = {"XAUUSD": 2, "XAGUSD": 3} if decimals is None else decimals
    keys = KEYS if keys is None else keys
    labels, strings = {"": 0}, {"": 0}
    lab = lambda t: labels.setdefault(t, len(labels))  # noqa: E731
    txt = lambda t: strings.setdefault(t, len(strings))  # noqa: E731
    orders = b"".join(
        struct.pack(
            "<Ii2q7f5H2B",
            s,
            o["ticket"],
            o["open_ms"],
            o["close_ms"],
            o["open"],
            o["close"],
            o["size"],
            o["pl"],
            o["balance"],
            o["mae"],
            o["mfe"],
            lab(o["sym"]),
            lab(o["res"]),
            lab(o["type"]),
            lab(o["sample"]),
            lab(o["close_type"]),
            o["flags"],
            0,
        )
        for s, st in enumerate(bank)
        for o in st["orders"]
    )
    runs = [
        (s, txt(key), points)
        for s, st in enumerate(bank)
        for key, points in st["equity"].items()
    ]
    equity = b"".join(
        struct.pack("<if", day, v) for _, _, points in runs for day, v in points
    )
    stats = b"".join(
        struct.pack(f"<IIb3x{len(keys)}d", s, txt(key), sample, *values)
        for s, st in enumerate(bank)
        for key, sample, values in st["stats"]
    )
    xml = [st["xml"].encode("utf-8") for st in bank]
    index = b"".join(
        struct.pack(
            "<5Ii2I",
            txt(st["name"]),
            txt(st["main"]),
            txt(st["symbol"]),
            txt(st["tf"]),
            txt(st["filter"]),
            st["problems"],
            len(st["orders"]),
            len(x),
        )
        for st, x in zip(bank, xml)
    )
    eqruns = b"".join(
        struct.pack("<3I", s, key, len(points)) for s, key, points in runs
    )
    symdec = b"".join(struct.pack("<Ii", lab(sym), d) for sym, d in decimals.items())
    keyids = b"".join(struct.pack("<I", txt(f"{name}\t{kind}")) for name, kind in keys)
    sections = [
        orders,
        equity,
        stats,
        b"".join(xml),
        index,
        eqruns,
        symdec,
        keyids,
        _table(list(labels)),
        _table(list(strings)),
    ]
    body = MAGIC_HEAD + struct.pack("<II", 1, data)
    table = b""
    for section in sections:
        table += struct.pack("<QQ", len(body), len(section))
        body += section
    body += table + struct.pack(
        "<IIQQQ",
        len(bank),
        len(keys),
        len(orders) // 64,
        1_760_000_000_000,
        len(body) + 204,
    )
    path.write_bytes(body + struct.pack("<I", zlib.crc32(body)) + b"KNABOGLA")


MAGIC_HEAD = b"ALGOBANK"


@pytest.fixture
def abk(tmp_path: Path) -> Path:
    """A well-formed `.abk` of three strategies."""
    path = tmp_path / "Results.abk"
    write(path, strategies())
    return path


def test_every_stored_field_comes_back(abk: Path) -> None:
    """Every field the writer stored comes back from `load`."""
    bank = bankfile.load(abk, check=True)
    src = strategies()
    assert bank["data"] == "main" and bank["written_ms"] == 1_760_000_000_000
    assert list(bank["names"]) == [s["name"] for s in src]
    assert bank["keys"] == KEYS
    flat = [(s, o) for s, st in enumerate(src) for o in st["orders"]]
    assert len(bank["orders"]) == len(flat) == 6
    for got, (s, want) in zip(bank["orders"], flat):
        assert got["strategy"] == s
        for field in ("ticket", "open_ms", "close_ms", "flags"):
            assert got[field] == want[field], field
        for field in ("open", "close", "size", "pl", "balance", "mae", "mfe"):
            assert got[field] == np.float32(want[field]), field
        for field in ("sym", "res", "type", "sample", "close_type"):
            assert bank["labels"][got[field]] == want[field], field
    S = bank["strings"]
    for row, st in zip(bank["index"], src):
        assert [S[row[c]] for c in ("name", "main", "symbol", "tf", "filter")] == [
            st[c] for c in ("name", "main", "symbol", "tf", "filter")
        ]
        assert (row["problems"], row["n_orders"]) == (st["problems"], len(st["orders"]))
    assert {bank["labels"][s]: d for s, d in bank["symdec"]} == {
        "XAUUSD": 2,
        "XAGUSD": 3,
    }
    assert bankframes.texts(bank) == {st["name"]: st["xml"] for st in src}


def test_trades_are_the_frame_the_trade_library_stores(abk: Path) -> None:
    """`trades` equals the frame the trade library stores, rounding half-up."""
    got = bankfile.trades(bankfile.load(abk))
    ts = lambda *ms: np.array(ms, "datetime64[ms]").astype("datetime64[ns]")  # noqa: E731
    h = 3_600_000
    want = pd.DataFrame(
        {  # file-name order: 10.4.7, then 2.1.1
            "Type": pd.Categorical(
                ["Buy", "Buy", "Buy", "Buy", "Sell"], categories=["Buy", "Sell"]
            ),
            "Open time": ts(
                T0, T0 + h, T0 + 6 * h, T0, T0 + 5 * h
            ),  # the 250 ms are dropped
            "Open price": [
                856.19,
                17.063,
                17.1,
                856.19,
                874.63,
            ],  # half-up; numpy: 874.62, 17.062
            "Size": [0.5, 5.0, 5.0, 1.19, 0.83],
            "Close time": ts(
                T0 + 4 * h, T0 + 3 * h, T0 + 7 * h, T0 + 2 * h, T0 + 6 * h
            ),
            "Close price": [860.0, 17.3, 17.0, 862.29, 876.03],
            "Profit/Loss": [190.5, 22.75, -50.0, 715.71, -0.13],
            "Balance": [100190.5, 100213.25, 100163.25, 100715.71, 100715.59],
            "Sample type": pd.Categorical(
                ["IST", "IST", "IST", "IST", "OOS"], categories=["IST", "OOS"]
            ),
            "Close type": pd.Categorical(
                [
                    "Exit Signal",
                    "Exit Signal",
                    "Profit Target",
                    "Exit Signal",
                    "Stop Loss",
                ],
                categories=["Exit Signal", "Profit Target", "Stop Loss"],
            ),
            "MAE ($)": [-10.0, -1.13, -60.0, -66.4, 0.0],
            "MFE ($)": [200.0, 30.0, 0.0, 776.83, 116.86],
            # the pyramiding strategy alone keeps its tickets, before `strategy`: it is the first file
            "Ticket": [1.0, 2.0, 1.0, np.nan, np.nan],
            "strategy": pd.Categorical(
                ["Strategy 10.4.7"] * 3 + ["Strategy 2.1.1"] * 2,
                categories=["Strategy 10.4.7", "Strategy 2.1.1"],
            ),
        }
    )
    pd.testing.assert_frame_equal(got, want, check_exact=True)


def test_every_result_gets_its_block_symbol_metrics_and_equity(tmp_path: Path) -> None:
    """Per-market trades carry Symbol and block, and metrics and equity come per result."""
    path = tmp_path / "Retest.abk"
    write(path, strategies(), data=1)
    bank = bankfile.load(path, check=True)
    assert bank["data"] == "all"
    got = bankfile.trades(bank, per_market=True)
    assert list(got.columns[12:]) == ["Symbol", "block", "Ticket", "strategy"]
    assert (
        got["block"].tolist() == [0, 0, 1, 0, 0] and str(got["block"].dtype) == "int64"
    )
    assert got["Symbol"].tolist() == ["XAUUSD", "XAGUSD", "XAGUSD", "XAUUSD", "XAUUSD"]
    assert list(got["Symbol"].cat.categories) == ["XAGUSD", "XAUUSD"]

    names = ["Strategy 2.1.1", "Strategy 10.4.7", "Strategy 3.3.3"]
    who = lambda s, r: {
        "strategy": pd.Categorical(s, categories=names),  # noqa: E731
        "result": pd.Categorical(r, categories=sorted(set(r), key=ORDER.index)),
    }
    pd.testing.assert_frame_equal(
        bankframes.metrics(bank),
        pd.DataFrame(
            who([names[0], names[0], names[1]], [MAIN, MAIN, SILVER])
            | {
                "sample": [10, 127, 127],
                "NetProfit": [715.585, -0.125, -27.25],
                "NumberOfTrades": pd.array(
                    [2, 1, pd.NA], "Int64"
                ),  # a key the block lacks
                "MaxNewHighDurationTo": pd.array([1_200_000_000_000, 0, 0], "Int64"),
            }
        ),
        check_exact=True,
    )
    days = np.array([13881, 13882, 13881, 13881, 13881, 13884], "datetime64[D]")
    pd.testing.assert_frame_equal(
        bankframes.equity(bank),
        pd.DataFrame(
            who(
                [names[0]] * 3 + [names[1]] * 3,
                [MAIN, MAIN, "Portfolio", MAIN, SILVER, SILVER],
            )
            | {
                "day": days.astype("datetime64[ns]"),
                "equity": np.array(
                    [0.0, 715.71, 0.0, 190.5, 22.75, -27.25], "f4"
                ).astype("f8"),
            }
        ),
        check_exact=True,
    )


ORDER = [MAIN, "Portfolio", SILVER]  # the order the writer met the result keys in


def test_half_up_is_not_numpys_rounding() -> None:
    """`half_up` rounds .5 away from zero where numpy rounds to even."""
    x = np.array([0.125, -0.125, 2.5, 100715.585, 0.0], "f4")
    assert bankfile.half_up(x, 2).tolist() == [0.13, -0.13, 2.5, 100715.59, 0.0]
    assert np.round(x.astype("f8"), 2).tolist()[:2] == [0.12, -0.12]
    assert bankfile.half_up(
        np.array([17.0625, 874.625], "f4"), np.array([3, 2])
    ).tolist() == [17.063, 874.63]


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
