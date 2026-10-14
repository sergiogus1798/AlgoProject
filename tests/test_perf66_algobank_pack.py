"""`bankfile.pack` against `tradepack.pack` of the same strategies written as CSVs (split from test_perf66_algobank)."""

import sys
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from test_perf66_algobank import T0, _order, strategies, write  # noqa: E402

from core import bankfile, tradepack  # noqa: E402


def _csv(path: Path, st: dict, decimals: dict) -> None:
    """One strategy as `orderstocsv` writes it: text numbers rounded half-up, a pending close blank."""
    r = lambda v, d: str(
        Decimal(float(np.float32(v))).quantize(Decimal(1).scaleb(-d), ROUND_HALF_UP)
    )  # noqa: E731
    t = lambda ms: pd.Timestamp(ms, unit="ms").strftime("%Y.%m.%d %H:%M:%S")  # noqa: E731
    rows = [
        "Ticket;Symbol;Type;Open time;Open price;Size;Close time;Close price;Profit/Loss;Balance;"
        "Sample type;Close type;MAE ($);MFE ($);Time in trade;Comment"
    ]
    for o in st["orders"]:
        d = decimals[o["sym"]]
        rows.append(
            ";".join(
                [
                    str(o["ticket"]),
                    o["sym"],
                    o["type"],
                    t(o["open_ms"]),
                    r(o["open"], d),
                    r(o["size"], 2),
                    t(o["close_ms"]),
                    "" if o["flags"] else r(o["close"], d),
                    r(o["pl"], 2),
                    r(o["balance"], 2),
                    o["sample"],
                    o["close_type"],
                    r(o["mae"], 2),
                    r(o["mfe"], 2),
                    "",
                    "",
                ]
            )
        )
    path.write_text("\n".join(rows) + "\n")


@pytest.mark.parametrize("data", [0, 1])
@pytest.mark.parametrize(
    "only",
    [
        None,
        {"Strategy 2.1.1", "Strategy 3.3.3"},
        {"Strategy 3.3.3", "Strategy 10.4.7", "X", "X(1)"},
    ],
)
def test_pack_equals_the_pack_of_the_csvs(
    tmp_path: Path, data: int, only: set | None
) -> None:
    """`bankfile.pack` writes the Parquet and returns the dict `tradepack.pack` makes of the same CSVs."""
    one = [_order(1, T0, T0 + 3_600_000, 1.0, 2.0, 1.0, 1.0, 100001.0, 0.0, 1.0)]
    bank = strategies() + [
        dict(strategies()[2], name=n, orders=o)
        for n, o in (("Strategy 1.1.1", []), ("X", one), ("X(1)", one))
    ]
    write(tmp_path / "b.abk", bank, data=data)
    pick = sorted(
        (s for s in bank if only is None or s["name"] in only),
        key=lambda s: s["name"] + ".csv",
    )
    files = [
        tmp_path / f"{s['name']}.csv" for s in pick
    ]  # "Strategy 1.1.1" is empty; F3: X(1) < X
    for f, st in zip(files, pick):
        _csv(f, st, {"XAUUSD": 2, "XAGUSD": 3})
    want = tradepack.pack(files, tmp_path / "want.parquet", bool(data))
    assert (
        bankfile.pack(
            bankfile.load(tmp_path / "b.abk"),
            tmp_path / "got.parquet",
            bool(data),
            only,
        )
        == want
    )
    pd.testing.assert_frame_equal(
        pd.read_parquet(tmp_path / "got.parquet"),
        pd.read_parquet(tmp_path / "want.parquet"),
        check_exact=True,
        check_categorical=True,
    )


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
