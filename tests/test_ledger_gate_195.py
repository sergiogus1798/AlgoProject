"""Step 19.5 (the single oos2 reading) passes the door as WFM's 19; any other unlisted step does not."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.assetdata import AUTONOMOUS
from ledger import gate


def test_195_reads_oos2_as_19(monkeypatch: pytest.MonkeyPatch) -> None:
    """Under ALGO_AUTONOMOUS the 19.5 cut row passes on oos2; step 16 is still refused."""
    monkeypatch.setenv(AUTONOMOUS, "1")
    gate.allow(19.5, "oos2", "EURUSD")  # gorilla's run died here, 2026-10-15
    with pytest.raises(PermissionError):
        gate.allow(16, "oos2", "EURUSD")


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
