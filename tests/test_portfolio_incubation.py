#!/usr/bin/env python3
"""Known-answer test of M9's contract and reading: the band by hand, the record, bad rows, calibration, a lost edge."""

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd

import ledger.study as study
from portfolio.common.construct.incubation import band, record, run
from portfolio.common.construct.inputs import config

FAILURES = []
MEMBERS = ["a" * 64, "b" * 64]
COMPARISON = {
    "figure": "pnl",
    "history": ["oos1", "oos2"],
    "band": [5, 100],
}  # TEST values, in no YAML
EDGE, MONTH = 0.2, 21


def check(name: str, ok: bool) -> None:
    """Print one line per case; remember the failures."""
    print(f"{'OK   ' if ok else 'FALLO'}  {name}")
    if not ok:
        FAILURES.append(name)


def long(
    days: pd.DatetimeIndex, pnl: np.ndarray, segment: str, source: str
) -> pd.DataFrame:
    """Rows in the contract's shape: `pnl` [2, D], one row per member per day."""
    return pd.concat(
        [
            pd.DataFrame(
                {
                    "day": days,
                    "identity": m,
                    "pnl": p,
                    "segment": segment,
                    "source": source,
                }
            )
            for m, p in zip(MEMBERS, pnl)
        ],
        ignore_index=True,
    )


def judged_run(folder: Path, rng: np.random.Generator) -> None:
    """A run folder with the hand-off of a 2-member portfolio earning `EDGE` a day at sigma 1 (after the weights)."""
    days = pd.bdate_range("2012-01-02", "2023-12-29")
    pnl = EDGE + np.sqrt(2) * rng.normal(size=(2, len(days)))
    daily = long(days, pnl, "oos1", "rebuild")
    daily.loc[daily["day"] < "2014-01-01", "segment"] = "build"
    daily.loc[daily["day"] >= "2020-01-01", "segment"] = "oos2"
    (folder / "handoff").mkdir(parents=True)
    daily.to_parquet(folder / "handoff" / "daily.parquet", index=False)
    portfolio = {
        "run_id": folder.name,
        "pool": "sintetico",
        "pool_hash": "feedc0de" * 8,
        "weights": dict.fromkeys(MEMBERS, 0.5),
        "members": [{"identity": m, "version": "v1"} for m in MEMBERS],
        "verdict": "PASA",
        "relaxed_thresholds": {},
    }
    (folder / "handoff" / "portfolio.json").write_text(
        json.dumps(portfolio), encoding="utf-8"
    )


def fresh(n: int, mean: float, rng: np.random.Generator) -> pd.DataFrame:
    """n business days after the history, the portfolio earning `mean` a day at sigma 1."""
    return long(
        pd.bdate_range("2024-01-01", periods=n),
        mean + np.sqrt(2) * rng.normal(size=(2, n)),
        "incubation",
        "paper",
    )


def main() -> None:
    """The band on six numbers, then a registered synthetic portfolio read like the command reads it."""
    got = band.read(np.arange(1.0, 7.0), np.array([3.0, 3.0]), "pnl", [0, 100])
    check(
        "band by hand: windows of 2 over 1..6 sum 3, 5, 7, 9, 11; a stretch summing 6 is inside, at the 40th percentile",
        (
            got["low"],
            got["high"],
            got["state"],
            got["percentile"],
            got["windows"],
            got["independent"],
        )
        == (3.0, 11.0, "inside", 40.0, 5, 3),
    )
    check(
        "a stretch summing 2 is below the band and flagged",
        band.read(np.arange(1.0, 7.0), np.ones(2), "pnl", [0, 100])["flagged"],
    )
    check(
        "a stretch longer than the history has no band and is not flagged",
        band.read(np.ones(3), np.ones(4), "pnl", [0, 100])
        == {
            "state": "no_band",
            "flagged": False,
            "days": 4,
            "windows": 0,
            "independent": 0,
        },
    )
    check(
        "the committed comparison is answered: figure, history and band (owner 2026-10-15, F5)",
        record.missing(config.load()) == [],
    )

    meta = {
        m: {"symbol": "NIKKEI225", "timeframe": "M30", "family": "t"} for m in MEMBERS
    }
    real_path, real_root = study.path, record.ROOT
    with tempfile.TemporaryDirectory() as tmp:
        study.path, record.ROOT = (
            (lambda s: Path(tmp) / f"{s}.jsonl"),
            Path(tmp) / "incubation",
        )
        try:
            judged_run(Path(tmp) / "run", np.random.default_rng(0))
            rec = record.register(
                Path(tmp) / "run", COMPARISON, dict.fromkeys(MEMBERS, 1.0)
            )
            loaded, folder = record.load(rec["portfolio_hash"][:6])
            check(
                "the record freezes the portfolio, the comparison and the history named (2014…2023), and says it is not running",
                loaded == rec
                and rec["comparison"] == COMPARISON
                and rec["history"]["from"] == "2014-01-01"
                and rec["history"]["to"] == "2023-12-29"
                and rec["running"] is False,
            )
            try:
                record.register(
                    Path(tmp) / "run",
                    {**COMPARISON, "band": [1, 99]},
                    dict.fromkeys(MEMBERS, 1.0),
                )
                check("a second registration of the same portfolio is refused", False)
            except SystemExit:
                check(
                    "a second registration of the same portfolio is refused",
                    json.loads((folder / "record.json").read_text())["comparison"][
                        "band"
                    ]
                    == [5, 100],
                )
            good = fresh(252, EDGE, np.random.default_rng(1))
            bad = {
                "otro miembro": good.assign(identity="c" * 64),
                "un día de la historia": good.assign(day=pd.Timestamp("2023-06-01")),
                "otro segmento": good.assign(segment="oos2"),
                "fuente desconocida": good.assign(source="demo"),
                "pnl no finito": good.assign(pnl=np.nan),
                "día repetido": pd.concat([good, good.head(1)]),
                "columnas de más": good.assign(extra=1),
            }
            check(
                "rows that honour the contract have no problem",
                record.validate(rec, good) == [],
            )
            for name, rows in bad.items():
                check(f"bad rows named: {name}", len(record.validate(rec, rows)) >= 1)
            first = run.read(rec, folder, good, meta, "prueba")
            check(
                "a year drawn from the backtest's own distribution is inside the band, not flagged",
                first["state"] == "inside" and first["days"] == 252,
            )
            ledger = [
                json.loads(line)
                for line in (Path(tmp) / "PORTFOLIO_feedc0defeed_construct.jsonl")
                .read_text()
                .splitlines()
            ]
            check(
                "the reading is one ledger row at step 27 on segment «incubation», and one line of readings.jsonl",
                [
                    (r["step"], r["segment"], r["n_in"], r["n_out"], r["criterion"])
                    for r in ledger
                ]
                == [(27, "incubation", 1, 1, "portfolio/incubation/pnl")]
                and len((folder / "readings.jsonl").read_text().splitlines()) == 1,
            )
            days = len(record.path(rec, pd.read_parquet(folder / "history.parquet")))
            flags = {"same": [], "lost": []}
            for seed in range(
                300
            ):  # each draw its OWN ten-year history: one history's band is off by its own luck
                rng = np.random.default_rng(100 + seed)
                history = EDGE + rng.normal(size=days)
                for name, mean in (("same", EDGE), ("lost", 0.0)):
                    path = mean + rng.normal(size=12 * MONTH)
                    flags[name].append(
                        [
                            band.read(history, path[: m * MONTH], "pnl", [5, 100])[
                                "flagged"
                            ]
                            for m in range(1, 13)
                        ]
                    )
            same, lost = np.array(flags["same"]), np.array(flags["lost"])
            check(
                f"calibration: a 12-month stretch of the history's own law is flagged at 5-10 %, not at the nominal 5 %, of 300 times ({same[:, -1].mean():.1%})",
                0.02 < same[:, -1].mean() < 0.15,
            )
            check(
                f"the edge removed: flagged at the 12-month reading in most of 300 draws ({lost[:, -1].mean():.1%})",
                lost[:, -1].mean() > 0.80,
            )
            print(
                f"       12 monthly readings: the same law is flagged at least once in {same.any(axis=1).mean():.1%} of the draws, "
                f"the edge removed in {lost.any(axis=1).mean():.1%} (repeated looks are not corrected)"
            )
            check(
                "a lost edge is flagged at some reading within the 12 months in over 9 of 10 draws",
                lost.any(axis=1).mean() > 0.90,
            )
        finally:
            study.path, record.ROOT = real_path, real_root
    print(f"\n{'TODO OK' if not FAILURES else 'FALLOS: ' + ', '.join(FAILURES)}")
    sys.exit(1 if FAILURES else 0)


if __name__ == "__main__":
    main()
