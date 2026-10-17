#!/usr/bin/env python3
"""Step 26's row 5: a relative drawdown gap over the limit passes when the points apart are few (P26h)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from mt5 import compare  # noqa: E402
from mt5.verify import firms, judge  # noqa: E402
from test_mt5verify import trades  # noqa: E402


def main() -> None:
    """The same 20 % smaller P&L: 0.8 points apart on 10,000 passes, 3.1 on 1,000 fails."""
    th = firms.config()["thresholds"]
    sqx = trades(60, 1)
    shrunk = sqx.assign(**{"Profit/Loss": sqx["Profit/Loss"] * 0.8})
    failures = []
    for deposit, want in ((10000, "pass"), (1000, "fail")):
        got = judge.rows(sqx, shrunk, compare.pair(sqx, shrunk, 60), deposit, th)
        five = next(r for r in got if r["row"] == "5")
        if five["value"] <= th["dd_rel_gap_max"] or five["state"] != want:
            failures.append(f"fila 5 con depósito {deposit}: {five}")
    for line in failures:
        print("FALLA:", line)
    print("ok" if not failures else f"{len(failures)} fallos")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
