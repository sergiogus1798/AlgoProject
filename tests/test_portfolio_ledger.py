#!/usr/bin/env python3
"""The rank search's ledger rows on a temporary ledger (PLAN §8.5): trials counted, one row per segment read."""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd

import ledger.study as study
import portfolio.common.construct.real as real
import portfolio.common.construct.search.choose as choose
import portfolio.common.construct.search.trials_real as trials_real
from portfolio_planted import CALENDAR, NAMES, planted_cfg, planted_pool

FAILURES = []
POOL = {"hash": "feedc0de" * 8}


def check(name: str, ok: bool) -> None:
    """Print one line per case; remember the failures."""
    print(f"{'OK   ' if ok else 'FALLO'}  {name}")
    if not ok:
        FAILURES.append(name)


def main() -> None:
    """One search and one admission pass of the planted pool, written as the command writes them."""
    cfg = planted_cfg()
    result = {"pool_name": "plantado", "kept": NAMES, "excluded": [], "identities": NAMES,
              "floor": dict.fromkeys(NAMES, 0.001), "root_seed": 1, "account": 10000.0,
              "relaxed": cfg["relaxed"], "shift": "3",
              **real.on_build(planted_pool(), CALENDAR, np.ones(len(NAMES)), cfg)}
    result["found"] = choose.choose(result["unit"], result["dates"], result["graph"]["graph"], cfg,
                                    np.random.default_rng(0))
    meta = {n: {"symbol": "NIKKEI225" if n < "B" else "USDJPY", "timeframe": "M30", "family": "t"}
            for n in NAMES}
    real_path, real_runs = study.path, real.RUNS
    with tempfile.TemporaryDirectory() as tmp:
        study.path, real.RUNS = (lambda s: Path(tmp) / "ledger" / f"{s}.jsonl"), Path(tmp) / "runs"
        (Path(tmp) / "ledger").mkdir()
        try:
            out = real.write_run(result, real.frame(result))
            rows = trials_real.record(result["found"], POOL, meta, "exhaustive; relaxed=no")
            judged = real.admit(result, out, "finite")
            admission_row = trials_real.record_admission(judged, POOL, meta, "finite", "relaxed=no")
            parquet = pd.read_parquet(out / "search.parquet")
            studies = sorted(p.stem for p in (Path(tmp) / "ledger").glob("*.jsonl"))
            stored = study.read(rows[0]["study"])
        finally:
            study.path, real.RUNS = real_path, real_runs

    check("the search row's n_scored is the rows of search.parquet",
          rows[0]["n_scored"] == len(parquet) == len(result["found"]["score"]))
    check("one row per segment read: build, once, in the pool's study -- no later segment",
          stored["segment"].tolist() == ["build", "build"]
          and stored["criterion"].tolist() == ["portfolio/ranks4/exhaustive", "portfolio/admission/finite/sequence"])
    check("the pool's study and one per member study (Q12: both); 10 members of 2 studies -> 10 rows",
          studies == ["NIKKEI225_M30_t", "PORTFOLIO_feedc0defeed_construct", "USDJPY_M30_t"]
          and len(rows) == 1 + len(NAMES))
    check("n_in the pool, n_out the K chosen, step 27, symbols joined",
          rows[0]["n_in"] == 10 and rows[0]["n_out"] == 2 and rows[0]["step"] == 27
          and rows[0]["symbol"] == "NIKKEI225+USDJPY" and rows[0]["timeframe"] == "mixed")
    check("the admission row counts every judgement of every round as a trial",
          admission_row["n_scored"] == len(judged) and admission_row["n_in"] == 8
          and admission_row["n_out"] == int(judged["enters"].sum()))
    print(f"       {len(parquet)} combinaciones · admisión: {len(judged)} juicios en "
          f"{judged['round'].max()} rondas, entran {int(judged['enters'].sum())}")
    print(f"\n{'TODO OK' if not FAILURES else 'FALLOS: ' + ', '.join(FAILURES)}")
    sys.exit(1 if FAILURES else 0)


if __name__ == "__main__":
    main()
