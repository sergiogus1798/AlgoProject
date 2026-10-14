"""An `.abk` that is empty, truncated, bit-flipped, of another version or incoherent is refused and says why."""

import struct
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import bankfile, bankframes  # noqa: E402
from tests.test_perf66_algobank import KEYS, strategies, write  # noqa: E402


@pytest.fixture
def abk(tmp_path: Path) -> Path:
    """A well-formed `.abk` of three strategies."""
    path = tmp_path / "Results.abk"
    write(path, strategies())
    return path


def test_an_empty_databank_is_a_valid_file_with_empty_frames(tmp_path: Path) -> None:
    """A databank without strategies loads and gives empty frames with their columns."""
    path = tmp_path / "Empty.abk"
    write(path, [], decimals={})
    bank = bankfile.load(path, check=True)
    assert len(bank["names"]) == 0 and bankframes.texts(bank) == {}
    assert list(bankfile.trades(bank).columns) == [
        "Type",
        "Open time",
        "Open price",
        "Size",
        "Close time",
        "Close price",
        "Profit/Loss",
        "Balance",
        "Sample type",
        "Close type",
        "MAE ($)",
        "MFE ($)",
        "strategy",
    ]
    assert list(bankframes.metrics(bank).columns) == [
        "strategy",
        "result",
        "sample",
    ] + [k for k, _ in KEYS]
    assert list(bankframes.equity(bank).columns) == [
        "strategy",
        "result",
        "day",
        "equity",
    ]
    assert (
        not len(bankfile.trades(bank))
        and not len(bankframes.metrics(bank))
        and not len(bankframes.equity(bank))
    )


@pytest.mark.parametrize("keep", [0, 15, 219, 220, -205, -9, -1])
def test_a_truncated_file_is_refused_and_says_so(abk: Path, keep: int) -> None:
    """A file cut at any point is refused as truncated."""
    whole = abk.read_bytes()
    abk.write_bytes(whole[:keep] if keep else b"")
    with pytest.raises(bankfile.Unreadable, match="truncado"):
        bankfile.load(abk)


def test_a_wrong_crc_is_refused_when_checked(abk: Path) -> None:
    """A flipped bit fails the CRC when it is checked."""
    raw = bytearray(abk.read_bytes())
    raw[16 + 20] ^= 0x01  # one bit of the first order's open price
    abk.write_bytes(bytes(raw))
    with pytest.raises(bankfile.Unreadable, match="CRC"):
        bankfile.load(abk, check=True)


def test_another_version_or_another_file_is_refused(abk: Path, tmp_path: Path) -> None:
    """Another version or a non-abk file is refused."""
    raw = bytearray(abk.read_bytes())
    raw[8] = 2
    abk.write_bytes(bytes(raw))
    with pytest.raises(bankfile.Unreadable, match="versión 1"):
        bankfile.load(abk)
    other = tmp_path / "other.abk"
    other.write_bytes(b"PK\x03\x04" + bytes(400))
    with pytest.raises(bankfile.Unreadable, match="versión 1"):
        bankfile.load(other)


@pytest.mark.parametrize("field", ["type", "sample", "close_type"])
@pytest.mark.parametrize("text", ["", "N/A"])
def test_an_order_without_a_label_rejects_the_whole_file(
    tmp_path: Path, field: str, text: str
) -> None:
    """One order with an empty or N/A label rejects the whole file."""
    bank = strategies()
    bank[1]["orders"][2][field] = text  # one order of six, and a valid CRC
    path = tmp_path / "Results.abk"
    write(path, bank)
    with pytest.raises(bankfile.Unreadable, match=f"«{field}» sin etiqueta"):
        bankfile.load(path, check=True)


def test_sections_that_do_not_add_up_are_refused(tmp_path: Path) -> None:
    """An order naming a missing strategy is refused as incoherent."""
    bank = strategies()
    path = tmp_path / "Results.abk"
    write(path, bank)
    raw = bytearray(path.read_bytes())
    raw[16:20] = struct.pack(
        "<I", 7
    )  # the first order claims a strategy that is not there
    path.write_bytes(bytes(raw))
    with pytest.raises(bankfile.Unreadable, match="no cuadran"):
        bankfile.load(path)


def test_ticket_rule_compares_whole_seconds_like_tradepack(tmp_path: Path) -> None:
    """An order opening 400 ms before the previous closes (same second) does not keep `Ticket`."""
    from tests.test_perf66_algobank import T0, _order

    one = strategies()[0]
    one["orders"] = [
        _order(1, T0 - 2000, T0 + 700, 1.0, 2.0, 1.0, 1.0, 100.0, 0.0, 1.0),
        _order(2, T0 + 300, T0 + 5000, 1.0, 2.0, 1.0, 1.0, 101.0, 0.0, 1.0),
    ]
    path = tmp_path / "One.abk"
    write(path, [one])
    assert "Ticket" not in bankfile.trades(bankfile.load(path)).columns


@pytest.mark.parametrize("offsets", [(0, 3, 1, 5), (0, 1, 9, 5)])
def test_a_string_table_with_bad_offsets_is_unreadable(offsets: tuple) -> None:
    """Non-monotonic or out-of-range offsets raise `Unreadable`, never `UnicodeDecodeError`."""
    import numpy as np

    raw = np.frombuffer(struct.pack("<I4I", 3, *offsets) + b"abcde", dtype="u1")
    with pytest.raises(bankfile.Unreadable):
        bankfile._table(raw, "x")


def test_a_traded_symbol_without_decimals_gives_no_trades(tmp_path: Path) -> None:
    """A traded symbol without decimals makes `trades` refuse."""
    path = tmp_path / "Results.abk"
    write(path, strategies(), decimals={"XAUUSD": 2, "XAGUSD": -1})
    with pytest.raises(bankfile.Unreadable, match="XAGUSD"):
        bankfile.trades(bankfile.load(path))


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
