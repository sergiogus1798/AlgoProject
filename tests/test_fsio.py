"""core.fsio.atomic_write: text and bytes, seal, no leftover, overwrite."""

import os
from pathlib import Path

from core.fsio import atomic_write


def test_atomic_write(tmp_path: Path) -> None:
    """Text and bytes land whole, a seal makes them read-only, overwrite works, no tmp remains."""
    p = tmp_path / "a" / "f.txt"
    atomic_write(p, "ñ")
    assert p.read_bytes() == "ñ".encode()
    atomic_write(p, b"\x00\x01", seal=True, durable=True)
    assert p.read_bytes() == b"\x00\x01"
    assert not os.access(p, os.W_OK) or os.geteuid() == 0
    atomic_write(p, "again")  # overwrite a sealed file
    assert p.read_text() == "again"
    assert [x.name for x in p.parent.iterdir()] == ["f.txt"]
