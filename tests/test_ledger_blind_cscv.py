#!/usr/bin/env python3
"""ledger.blind.from_batch reads the CSCV's contract envelope (estudios/cscv.json), not the old flat file."""

import json
import sys
import tempfile
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ledger import blind


def main() -> None:
    """A batch holding only the envelope yields its step-18 rows (one per segment) with its n and its note."""
    with tempfile.TemporaryDirectory() as tmp:
        batch = Path(tmp) / "Strategy_1.2.3"
        (batch / "estudios").mkdir(parents=True)
        (batch / "estudios" / "cscv.json").write_text(
            json.dumps(
                {
                    "computed_at": "2026-10-15T21:30:36",
                    "summary": {"n": 999, "p_perdida": 0.0567, "pbo": 0.2037},
                }
            ),
            encoding="utf-8",
        )
        frame = pd.DataFrame({"step": [19], "note": ["x"]})
        got = blind.from_batch(batch, {"symbol": "X", "timeframe": "H1"}, frame)
    assert len(got) == 3 and got[0]["step"] == 18 and got[0]["n_in"] == 999, got
    assert "P pérdida 0.057 PBO 0.204" in got[0]["note"], got[0]["note"]
    print("ok: from_batch lee el sobre estudios/cscv.json")


if __name__ == "__main__":
    main()
