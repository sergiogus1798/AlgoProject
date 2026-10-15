#!/usr/bin/env python3
"""A real cell queued after a test on the same key is a real cell: not smoke, the config's build, no
precision override (the ledger merges every line of a key). A `claude -p` that exits non-zero raises
instead of setting the cell aside as a question. No SQX; the data root is a temp folder."""

import os
import sys
import tempfile
import types
from pathlib import Path

TMP = Path(tempfile.mkdtemp())
os.environ["ALGO_DATA_ROOT"] = str(TMP)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.campaign import ledger, palette, plan  # noqa: E402


def main() -> None:
    """Seed a test line, queue the same key for real, read it back; then a failing expert."""
    row = {
        "template": "tA",
        "symbol": "XAUUSD",
        "timeframe": "H1",
        "direction": "long",
        "family": "tendencia",
        "palette": "experto",
        "points": 1,
        "prior": "",
        "evidence": "none",
        "project": "Trade_XAUUSD_H1_tA",
    }
    ledger.mark(
        {**row, "project": "Test_XAUUSD_H1_tA"},
        "pending",
        test=True,
        strategies=3000,
        minutes=15,
        precision=1,
    )
    plan.candidates = lambda: [row]
    plan.queue(1)
    got = ledger.following()
    assert not got["test"] and got["project"] == "Trade_XAUUSD_H1_tA", got
    assert (got["strategies"], got["minutes"], got["precision"]) == (10000, 180, None)
    palette.subprocess.run = lambda *a, **k: types.SimpleNamespace(
        stdout="", stderr="usage limit", returncode=1
    )
    try:
        palette.choose(row)
    except RuntimeError:
        print("ok")
        return
    raise AssertionError("a failed claude -p must raise")


if __name__ == "__main__":
    main()
