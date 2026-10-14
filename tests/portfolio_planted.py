"""A synthetic pool whose right portfolio is known: shared by the M3/M4 tests, not a test itself."""

import numpy as np
import pandas as pd
import pyarrow as pa

# OPEN #104-5: pyarrow 25 aborts at interpreter exit (exit 134, after the test's own «TODO OK»)
# when a short process that called `pd.read_parquet` ends while Arrow's CPU pool is still
# starting — 7 and 9 of 60 copies of test_portfolio_ledger at once. One CPU thread removes it.
# Here and not in the engine: it is the tests of the planted pool that are short enough to
# flake, and a reader-wide choice is the owner's
# (knowhow/eng/pyarrow-read-parquet-aborts-at-exit-under-load.md).
pa.set_cpu_count(1)

NAMES = ["A", "B", "A_dup", "hedge"] + [f"N{k}" for k in range(6)]
CALENDAR = {
    "build": (pd.Timestamp("2010-01-01"), pd.Timestamp("2019-12-31")),
    "oos1": (pd.Timestamp("2020-01-01"), pd.Timestamp("2021-12-31")),
    "oos2": (pd.Timestamp("2022-01-01"), pd.Timestamp("2023-12-29")),
}
SEED = 1


def planted_pool(seed: int = SEED) -> pd.DataFrame:
    """Ten members over build, oos1 and oos2; on build the best portfolio is {A, B}.

    A and B earn well and are nearly independent: together their swings halve and neither
    loses more often. `A_dup` is A itself earning less (rho = 1): the pair filter must keep it
    away from A. `hedge` mirrors A and B (rho = -0.64 with each) and earns a little: {A, B, hedge}
    would be by far the smoothest path of the pool, and the owner's rule (Q6, |rho| > 0.30
    rejects, negative too) must refuse it. N0..N5 are loud and earn nothing: any of them dilutes a combination.
    After build the roles flip: A and B lose, the N's earn -- the later segments would pick
    another portfolio, so a search that read them is caught.

    Returns:
        days x members daily P&L, 2010-2023, business days.
    """
    rng = np.random.default_rng(seed)
    days = pd.bdate_range(CALENDAR["build"][0], CALENDAR["oos2"][1])
    z = rng.normal(size=(len(NAMES), len(days)))
    late = np.asarray(days > CALENDAR["build"][1])
    a = 0.10 + z[0]
    cols = {
        "A": a,
        "B": 0.12 + z[1],
        "A_dup": a - 0.02,
        "hedge": 0.04 - 0.64 * (z[0] + z[1]) + 0.42 * z[3],
    }
    for k in range(6):
        cols[f"N{k}"] = 3.0 * z[4 + k]
    frame = pd.DataFrame(cols, index=days)[NAMES]
    frame.loc[late, ["A", "B", "A_dup", "hedge"]] -= 0.5
    frame.loc[late, NAMES[4:]] += 1.5
    return frame


def planted_cfg(**real: object) -> dict:
    """The committed config at the owner's thresholds, with `real.<knob>` overrides."""
    from portfolio.common.construct.inputs import config

    return config.load([f"real.{k}={v}" for k, v in real.items()])
