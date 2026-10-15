#!/usr/bin/env python3
"""Known-answer test of the weight walk-forward (M8): windows, the planted reversal, noise, the ledger rows."""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd

import ledger.study as study
import portfolio.common.construct.walkforward as walkforward
import portfolio.common.construct.wf as wf
from portfolio.common.construct.inputs import config

FAILURES = []
POOL = {"hash": "feedc0de" * 8}
NAMES = ["A", "B"]
CALENDAR = {
    "build": (pd.Timestamp("2000-01-01"), pd.Timestamp("2008-12-31")),
    "oos1": (pd.Timestamp("2009-01-01"), pd.Timestamp("2026-12-31")),
    "oos2": (pd.Timestamp("2027-01-01"), pd.Timestamp("2028-12-31")),
}


def check(name: str, ok: bool) -> None:
    """Print one line per case; remember the failures."""
    print(f"{'OK   ' if ok else 'FALLO'}  {name}")
    if not ok:
        FAILURES.append(name)


def world(swap: bool, seed: int) -> dict:
    """Two independent members earning the same; with `swap` their volatilities (1 and 4) trade places every 9 years.

    A is the quiet one on build. Weights fixed there are wrong in the first 9 of the 18 test years;
    weights re-estimated each January on the last year are wrong one year in nine.
    """
    rng = np.random.default_rng(seed)
    days = pd.bdate_range(CALENDAR["build"][0], CALENDAR["oos2"][1])
    quiet_a = (
        ((days.year - 2000) // 9) % 2 == 0 if swap else np.ones(len(days), dtype=bool)
    )
    sigma = (
        np.where(quiet_a, 1.0, 4.0),
        np.where(quiet_a, 4.0, 1.0) if swap else np.ones(len(days)),
    )
    daily = pd.DataFrame(
        {n: 0.5 + s * rng.normal(size=len(days)) for n, s in zip(NAMES, sigma)},
        index=days,
    )
    return {
        "daily": daily,
        "calendar": CALENDAR,
        "scale": np.ones(2),
        "identities": NAMES,
        "members_meta": {
            n: {"symbol": "NIKKEI225", "timeframe": "M30", "family": "t"} for n in NAMES
        },
    }


def main() -> None:
    """The windows by hand, the reversal detected where it is planted and nowhere else, the looks logged."""
    days = pd.bdate_range("2010-01-01", "2023-12-29")
    cuts = walkforward.folds(days, pd.Timestamp("2020-01-01"), 0, 3)
    check(
        "windows: 2020 and 2023 start a test window of 3 years, estimation is everything before",
        [(c["estimate_from"], c["test_from"], c["test_to"]) for c in cuts]
        == [
            (days[0], pd.Timestamp("2020-01-01"), pd.Timestamp("2023-01-01")),
            (days[0], pd.Timestamp("2023-01-01"), pd.Timestamp("2023-12-30")),
        ],
    )
    check(
        "a 2-year lookback starts 2 years before its window",
        walkforward.folds(days, pd.Timestamp("2020-01-01"), 2, 1)[1]["estimate_from"]
        == pd.Timestamp("2019-01-01"),
    )

    cfg = config.load(["wf.confidence=0.95", "wf.lookback_years=1", "wf.step_years=1"])
    check(
        "the committed bar is 0.95 joint (owner 2026-10-15) and AlphaForge's 3 years stand",
        config.load()["wf"]["confidence"] == 0.95
        and config.load()["wf"]["step_years"] == 3,
    )
    real_path = study.path
    with tempfile.TemporaryDirectory() as tmp:
        study.path = lambda s: Path(tmp) / f"{s}.jsonl"
        try:
            got = wf.run(world(True, 1), NAMES, cfg, np.random.default_rng(2))
            rows = wf.record(got, POOL, cfg)
            noise = wf.run(world(False, 3), NAMES, cfg, np.random.default_rng(4))
            once = wf.run(
                world(True, 1),
                NAMES,
                {**cfg, "wf": {**cfg["wf"], "step_years": 30}},
                np.random.default_rng(5),
            )
        finally:
            study.path = real_path
    t = got["table"].set_index(["method", "arm"])
    check(
        "only build and oos1 days are read: 18 windows, the last test day inside oos1",
        len(got["cuts"]) == 18
        and got["dates"][-1] <= CALENDAR["oos1"][1]
        and got["dates"][0] >= CALENDAR["oos1"][0],
    )
    fixed = (
        got["weights"]
        .query("window == 0 and method == 'risk_parity'")
        .set_index("identity")["weight"]
    )
    check(
        "risk parity fixed on build overweights A, the quiet one there (0.8 but for one year's sampling)",
        0.72 < fixed["A"] < 0.88,
    )
    for method in ("risk_parity", "min_variance", "hrp"):
        check(
            f"{method}: held fixed it does not beat equal weight, re-estimated it does -> the reversal condition",
            not t.loc[(method, "fixed"), "beats"]
            and t.loc[(method, "reestimated"), "beats"]
            and got["states"][method] == "only_reestimated",
        )
        check(
            f"{method}: re-estimated beats itself held fixed, the whole interval above 0",
            t.loc[(method, "reestimated"), "lo_fixed"] > 0,
        )
    check(
        "the sentence says #5's reversal condition is met and decides nothing itself",
        "revierte" in wf.sentence(got, cfg) and "dueño" in wf.sentence(got, cfg),
    )
    check(
        "no volatility pattern: no method beats equal weight, fixed or re-estimated",
        set(noise["states"].values()) == {"no"}
        and "se mantienen los pesos iguales" in wf.sentence(noise, cfg),
    )
    few = {
        k: v
        for k, v in got["paths"].items()
        if k in (("equal", "fixed"), ("hrp", "fixed"), ("hrp", "reestimated"))
    }
    narrow = walkforward.compare(
        {**got, "paths": few}, cfg, np.random.default_rng(9)
    ).set_index(["method", "arm"])
    wide = walkforward.compare(got, cfg, np.random.default_rng(9)).set_index(
        ["method", "arm"]
    )
    check(
        "Bonferroni: the same arm's interval is wider with more intervals compared",
        wide.loc[("hrp", "reestimated"), "lo"]
        < narrow.loc[("hrp", "reestimated"), "lo"],
    )
    check(
        "one test window: the two arms are the same path",
        len(once["cuts"]) == 1
        and np.array_equal(
            once["paths"]["hrp", "fixed"], once["paths"]["hrp", "reestimated"]
        ),
    )
    mine = [r for r in rows if r["criterion"] == "portfolio/weights_wf"]
    looked = [r for r in mine if r["segment"] == "oos1"]
    check(
        "ledger: one row per segment read in the pool's study and in the members', none on another segment",
        sorted(r["segment"] for r in mine) == ["build"] * 3 + ["oos1"] * 3
        and len(rows) == 6,
    )
    check(
        "ledger: the oos1 row counts every arm compared (7) and how many beat equal weight (3)",
        all(
            r["n_scored"] == 7
            and r["n_in"] == 7
            and r["n_out"] == 3
            and r["step"] == 27
            for r in looked
        ),
    )
    try:
        config.load(["weights.method=hrp"])
        check("another method cannot be selected by a knob", False)
    except SystemExit:
        check("another method cannot be selected by a knob", True)
    print(f"\n{'TODO OK' if not FAILURES else 'FALLOS: ' + ', '.join(FAILURES)}")
    sys.exit(1 if FAILURES else 0)


if __name__ == "__main__":
    main()
