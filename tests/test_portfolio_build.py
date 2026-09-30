#!/usr/bin/env python3
"""Known-answer test of the universe builder (M1): one archived strategy, temp pool and cache root."""

import resource
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import portfolio.common.construct.equity.store as store  # noqa: E402
import portfolio.common.construct.inputs.pool as pool  # noqa: E402
from portfolio.common.construct import universe as command  # noqa: E402
from portfolio.common.construct.equity import blocks, matrix, universe  # noqa: E402
from portfolio.common.construct.inputs import config, source  # noqa: E402

IDENTITY = "4d679e0c2ce2a63ee53bc6cb305830bcaf5a74997e6e6e2c1deeb4c30f307048"
VERSION = "2026-09-28T0919"
FAILURES = []


def check(name: str, ok: bool, detail: str = "") -> None:
    """Print one check's result and remember failures."""
    print(f"{'OK   ' if ok else 'FALLO'}  {name} {detail}")
    if not ok:
        FAILURES.append(name)


def main() -> None:
    """Build a one-strategy pool in a temp cache root; check every contract of `equity.universe`."""
    with tempfile.TemporaryDirectory() as tmp:
        pool.ROOT = Path(tmp) / "pool"
        store.ROOT = Path(tmp) / "universe"
        pool.declare("uno", [{"identity": IDENTITY, "version": VERSION}], added_by="test")

        cfg = config.load([])
        t0 = time.perf_counter()
        out = universe.build("uno", cfg)
        wall = time.perf_counter() - t0
        peak_mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
        print(f"build: {wall:.2f} s, pico {peak_mb:.0f} MB")

        data = universe.load(out)
        manifest = data["manifest"]
        check("the member is kept", manifest["members"]["kept"] == [IDENTITY],
              f"{manifest['members']}")
        check("no excluded member", manifest["members"]["excluded"] == [])
        check("reconciled ok and licensed",
              (data["reconcile"]["verdict"] == "ok").all()
              and data["reconcile"]["licensed"].all(), f"{data['reconcile']}")

        trades = source.load(IDENTITY, VERSION)["trades"]
        total_pnl = float(trades["Profit/Loss"].sum())
        total_daily = float(data["daily"][IDENTITY].sum())
        check("sum(daily.parquet) == sum(Profit/Loss)",
              abs(total_daily - total_pnl) < 1e-6, f"{total_daily} vs {total_pnl}")

        for firm, frame in data["days"].items():
            one = frame[frame["identity"] == IDENTITY].sort_values("day")
            mtm = one["closed"] + one["float_end"] - one["float_end"].shift(1).fillna(0.0)
            check(f"days_{firm}: closed+float_end diff sums to Profit/Loss",
                  abs(float(mtm.sum()) - total_pnl) < 1e-6, f"{mtm.sum()} vs {total_pnl}")

            m5 = data["m5"][firm]
            joint = blocks.joint_day_low([m5["low"][IDENTITY]], m5["block_days"])
            joint.index = pd.to_datetime(joint.index)
            table_low = one.set_index("day")["low"]
            common = joint.index.intersection(table_low.index)
            check(f"m5_{firm} joint_day_low == days_{firm} low (one member)",
                  np.allclose(joint.loc[common].to_numpy(), table_low.loc[common].to_numpy(),
                              atol=0.01), f"n={len(common)}")

        check("hantec is flagged unconfirmed", "hantec" in manifest["unconfirmed_clocks"])

        out2 = universe.build("uno", config.load([]))
        check("a second build with the same pool+config reuses the cache", out2 == out, f"{out2} vs {out}")

        out3 = universe.build("uno", config.load(["equity.excursion_tolerance=2.0"]))
        check("a config override never reuses the cache", out3 != out, f"{out3} vs {out}")

        rng = np.random.default_rng(2)
        days_ix = pd.bdate_range("2008-01-01", "2022-12-30")
        base = rng.normal(size=len(days_ix))
        daily = pd.DataFrame({"A": base, "B": 0.95 * base + 0.3 * rng.normal(size=len(days_ix)),
                              "C": rng.normal(size=len(days_ix))}, index=days_ix)
        fake = {"daily": daily, "monthly": matrix.monthly(daily),
                "manifest": {"calendar": manifest["calendar"]}}
        got = command.screen(fake, config.load([]), Path(tmp))
        check("screen: the clone pair A-B is rejected, A-C and B-C pass",
              got["n_admissible_pairs"] == 2 and not got["graph"][0, 1], f"{got['counts']}")
        check("screen: pairs.parquet written", (Path(tmp) / "pairs.parquet").is_file())

    if FAILURES:
        print(f"\n{len(FAILURES)} fallo(s): {FAILURES}")
        sys.exit(1)
    print("\ntodo OK")


if __name__ == "__main__":
    main()
