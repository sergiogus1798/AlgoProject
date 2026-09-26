#!/usr/bin/env python3
"""SQX's ATR against a series worked out by hand, gap and running-mean start included."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engines.market import atr

# Five bars, period 3. True ranges 2, 2, 3, 1, 8.5 (the last one gaps up from 11.5).
# Divisors 1, 2, 3, 3, 3: the first three are a running mean, then Wilder.
BARS = pd.DataFrame({"High": [10, 11, 13, 12, 20], "Low": [8, 9, 10, 11, 19],
                     "Close": [9, 10, 12, 11.5, 19.5]})
EXPECTED = [2.0, 2.0, 7 / 3, 17 / 9, 110.5 / 27]


def main() -> None:
    """Fail loudly on any value that is not the hand-computed one."""
    failures = []
    got = atr.sqx(BARS, 3)
    if not np.allclose(got, np.round(EXPECTED, 6), rtol=0, atol=1e-12):
        failures.append(f"sqx(): {got.tolist()} != {EXPECTED}")
    if not np.allclose(atr.true_range(BARS), [2, 2, 3, 1, 8.5]):
        failures.append(f"true_range(): {atr.true_range(BARS).tolist()}")
    # Past the start, the recurrence is Wilder's smoothing and nothing else: a constant
    # true range must converge on that constant.
    flat = pd.DataFrame({"High": np.full(400, 2.0), "Low": np.zeros(400), "Close": np.ones(400)})
    if abs(atr.sqx(flat, 20)[-1] - 2.0) > 1e-9:
        failures.append("un rango verdadero constante no converge a esa constante")
    if failures:
        raise SystemExit("\n".join(failures))
    print("test_atr: ok")


if __name__ == "__main__":
    main()
