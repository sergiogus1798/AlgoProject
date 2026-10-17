"""The export's fingerprint of a .sqx does not move when SQX reorders `optimizationProfile.bin`."""

import zipfile
from pathlib import Path

from sqx.databank import state


def _sqx(folder: Path, profile: bytes) -> Path:
    """One strategy file in a folder of its own: the fingerprint caches by path and date."""
    folder.mkdir()
    with zipfile.ZipFile(folder / "a.sqx", "w") as z:
        z.writestr("strategy_Portfolio.xml", "<a/>")
        z.writestr("optimizationProfile.bin", profile)
        z.writestr("other.bin", b"abc")
    return folder / "a.sqx"


def test_reordered_profile_is_the_same_strategy(tmp_path: Path) -> None:
    """Same bytes in another order: equal. One byte value changed, same size: different."""
    one = state.fingerprint([_sqx(tmp_path / "1", bytes(range(200)) * 50)])
    same = state.fingerprint([_sqx(tmp_path / "2", bytes(reversed(range(200))) * 50)])
    other = state.fingerprint([_sqx(tmp_path / "3", bytes(range(1, 201)) * 50)])
    assert one == same != other
