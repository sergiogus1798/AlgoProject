#!/usr/bin/env python3
"""Known-answer test of the rank search (M3): metrics by hand, a 4-strategy pool, admission, ledger."""

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd
from scipy.stats import rankdata

import ledger.study as study
from ledger import trials as ledger_trials
import portfolio.common.construct.real as real
import portfolio.common.construct.search.admission as admission
import portfolio.common.construct.search.choose as choose
import portfolio.common.construct.search.genetic as genetic
import portfolio.common.construct.search.trials_real as trials_real
import portfolio.common.construct.verdict.metrics as metrics

FAILURES = []
SEARCH = Path(__file__).resolve().parent.parent / "portfolio/common/construct/search"


def check(name: str, ok: bool) -> None:
    """Print one line per case; remember the failures."""
    print(f"{'OK   ' if ok else 'FALLO'}  {name}")
    if not ok:
        FAILURES.append(name)


def test_metrics_by_hand() -> None:
    """Six days worked out on paper: two drawdowns, the slope, R-cubed, gain-to-pain, a losing year."""
    dates = pd.date_range("2020-12-28", periods=6)
    pnl = np.array([1.0, -2.0, 1.0, 2.0, -1.0, 1.0])          # equity 1, -1, 0, 2, 1, 2
    day = dates.values.astype("datetime64[D]").astype(np.int64)
    depth, length = metrics.drawdowns(np.cumsum(pnl), day)
    check("drawdowns: depths 2 and 1", depth.tolist() == [2.0, 1.0])
    check("drawdowns: 3 and 2 days from the peak to the recovery", length.tolist() == [3.0, 2.0])

    got = metrics.table(pnl[None, :], dates, "calendar")
    slope = np.polyfit(np.arange(6) / 365.25, np.cumsum(pnl), 1)[0]
    check("RAR is the regression slope per year", np.isclose(got["rar"][0], slope))
    check("R-cubed = RAR / (mean depth 1.5 x mean length 2.5/365)",
          np.isclose(got["r_cubed"][0], slope / (1.5 * 2.5 / 365)))
    check("gain-to-pain = annual profit / the deepest drawdown (N = 1 year)",
          np.isclose(got["gain_to_pain"][0], (2.0 / (6 / 365.25)) / 2.0))
    check("P(losing year), calendar: 2020 wins +2, 2021 is flat -> 0 of 2",
          got["p_losing_year"][0] == 0.0)
    check("P(losing year), calendar: the mirror path loses 2020 only -> 1/2",
          metrics.table(-pnl[None, :], dates, "calendar")["p_losing_year"][0] == 0.5)
    check("Sharpe is mean over ddof=1 spread, per day",
          np.isclose(got["sharpe"][0], pnl.mean() / pnl.std(ddof=1)))

    down_then_up = np.concatenate([np.full(252, -1.0), np.full(252, 1.0)])
    rolling = metrics.table(down_then_up[None, :], pd.bdate_range("2015-01-01", periods=504), "rolling")
    # windows starting at row s cover s..s+251: the sum is negative for s < 126, zero at 126
    check("P(losing year), rolling: 126 of 253 windows lose",
          np.isclose(rolling["p_losing_year"][0], 126 / 253))


def tiny_pool() -> tuple[np.ndarray, pd.DatetimeIndex, np.ndarray]:
    """A, B, C, D: A and B earn 1 a day and carry opposite swings; C and D earn 0.3 with their own."""
    dates = pd.bdate_range("2014-01-01", periods=1040)
    rng = np.random.default_rng(7)
    swing = rng.normal(0, 12, dates.size)
    unit = np.array([1.0 + swing, 1.0 - 0.9 * swing,
                     0.3 + rng.normal(0, 12, dates.size), 0.3 + rng.normal(0, 12, dates.size)])
    graph = np.zeros((4, 4), dtype=bool)
    for a, b in [(0, 1), (0, 2), (2, 3)]:
        graph[a, b] = graph[b, a] = True
    return unit, dates, graph


def _independent_scores(unit: np.ndarray, dates: pd.DatetimeIndex, sets: list[tuple]) -> np.ndarray:
    """The same score computed the slow way: polyfit, a loop for the drawdowns, scipy's ranks."""
    t = (dates - dates[0]).days.to_numpy() / 365.25
    years = ((dates[-1] - dates[0]).days + 1) / 365.25
    rows = []
    for members in sets:
        path = unit[list(members)].mean(axis=0)
        equity = np.cumsum(path)
        peak, peak_day, low, episodes = 0.0, dates[0] - pd.Timedelta(days=1), 0.0, []
        for when, value in zip(dates, equity):
            if value >= peak:
                if low < peak:
                    episodes.append((peak - low, (when - peak_day).days))
                peak, peak_day, low = value, when, value
            low = min(low, value)
        if low < peak:
            episodes.append((peak - low, (dates[-1] - peak_day).days))
        episodes.sort(reverse=True)
        rar = np.polyfit(t, equity, 1)[0]
        top = episodes[:5]
        r3 = rar / (np.mean([d for d, _ in top]) * np.mean([n for _, n in top]) / 365)
        gtp = (equity[-1] / years) / np.mean([d for d, _ in episodes[:round(years)]])
        yearly = pd.Series(path, index=dates.year).groupby(level=0).sum()
        rows.append((rar, r3, gtp, -(yearly < 0).mean()))
    ranks = np.array([rankdata(col) for col in np.array(rows).T])   # mid-ranks, 1..n
    return ((ranks - 0.5) / len(sets)).mean(axis=0)


def test_tiny_pool() -> np.ndarray:
    """Seven admissible combinations; the hedged pair {A, B} is the best, by construction."""
    unit, dates, graph = tiny_pool()
    cfg = {"real": {"exhaustive_max": 100, "losing_year": "calendar", "rank_reference": None}}
    found = choose.choose(unit, dates, graph, cfg, np.random.default_rng(0))
    sets = [tuple(np.flatnonzero(m)) for m in found["members"]]
    check("exhaustive: 4 singles + 3 admissible pairs, no triangle -> 7 combinations",
          found["mode"] == "exhaustive" and sorted(sets) == sorted(
              [(0,), (1,), (2,), (3,), (0, 1), (0, 2), (2, 3)]))
    check("every combination scored is a clique",
          all(genetic.is_clique(graph, m) for m in found["members"]))
    check("the engine's scores equal the slow independent computation",
          np.allclose(found["score"], _independent_scores(unit, dates, sets)))
    check("the best portfolio is the hedged pair {A, B}", sets[found["best"]] == (0, 1))
    check("{A, B}: top R-cubed and gain-to-pain of the seven",
          found["table"]["r_cubed"].argmax() == found["best"]
          and found["table"]["gain_to_pain"].argmax() == found["best"])
    print(f"       {{A,B}}: score {found['score'][found['best']]:.3f} · "
          f"second best {np.sort(found['score'])[-2]:.3f} · 7 combinaciones")

    ga_cfg = {"real": {"exhaustive_max": 3, "losing_year": "calendar", "rank_reference": "seeds"},
              "search": {"seeds": 12, "ga": {"population": 12, "generations": 6, "elite": 0.2,
                                             "tournament": 3, "crossover": 0.8, "mutation": 0.4,
                                             "stagnation": 3}}}
    ga = choose.choose(unit, dates, graph, ga_cfg, np.random.default_rng(1))
    check("above exhaustive_max the GA runs, on cliques only, and finds {A, B} too",
          ga["mode"] == "ga" and all(genetic.is_clique(graph, m) for m in ga["members"])
          and tuple(np.flatnonzero(ga["members"][ga["best"]])) == (0, 1))
    check("the GA's table has one row per evaluation",
          len(ga["score"]) == len(ga["members"]) == len(ga["table"]["sharpe"]))
    ga_cfg["real"]["rank_reference"], refused = None, False
    try:
        choose.choose(unit, dates, graph, ga_cfg, np.random.default_rng(1))
    except SystemExit:
        refused = True
    check("the GA refuses to run without real.rank_reference", refused)
    return found


def test_admission() -> None:
    """A diversifier enters, a weaker clone does not, a vetoed pair blocks; the two readings differ."""
    rng = np.random.default_rng(3)
    d = 2000
    base = 0.05 + rng.normal(0, 1, (2, d))
    book = base.mean(axis=0)
    diversifier = 0.05 + rng.normal(0, 1, d)
    clone = 0.5 * book + rng.normal(0, 0.5, d) - 0.02                 # rho high, Sharpe lower
    noise = rng.normal(0, 60, d)
    loud = noise - noise.mean() + 0.6                                 # Sharpe 0.01, huge swings
    unit = np.vstack([base, diversifier, clone, loud])
    graph = ~np.eye(5, dtype=bool)
    graph[0, 3] = graph[3, 0] = False
    for how in admission.INCREMENTS:
        got = admission.judge(unit, graph, np.array([0, 1]), np.array([2, 3]), how)
        check(f"{how}: the independent diversifier enters",
              bool(got["enters"][0]) and got["increment"][0] > 0)
        check(f"{how}: the weaker clone adds nothing and is blocked by the member it fails with",
              not got["enters"][1] and got["increment"][1] < 0 and got["blocked_by"][1] == [0])
    check("the two readings disagree on a loud weak candidate: marginal > 0, finite < 0",
          admission.increment(base, loud, "marginal") > 0 > admission.increment(base, loud, "finite"))
    three = np.vstack([base, diversifier]).mean(axis=0)
    check("finite = Sharpe of the three minus Sharpe of the two", np.isclose(
        admission.increment(base, diversifier, "finite"),
        three.mean() / three.std(ddof=1) - book.mean() / book.std(ddof=1)))


def test_ledger_and_floor(found: dict) -> None:
    """Every evaluation is a trial; members' studies gain N, not sigma; the minimum-lot floor."""
    meta = {name: {"symbol": "USDJPY", "timeframe": "H1", "family": "t"} for name in "ABCD"}
    real_path = study.path
    with tempfile.TemporaryDirectory() as tmp:
        study.path = lambda s: Path(tmp) / f"{s}.jsonl"
        try:
            rows = trials_real.record(found, {"hash": "deadbeef" * 4}, meta, "test")
            pooled = ledger_trials.accumulated(study.read(rows[0]["study"]))
            member = ledger_trials.accumulated(study.read(rows[1]["study"]))
        finally:
            study.path = real_path
    check("ledger: the pool's row counts 7 trials on build at step 27",
          rows[0]["n_scored"] == 7 and rows[0]["segment"] == "build" and rows[0]["step"] == 27)
    check("ledger: one row per member plus the pool's", len(rows) == 5)
    check("ledger: the pool's study pools the Sharpes' spread",
          pooled["n"] == 7 and np.isclose(pooled["sigma"], found["table"]["sharpe"].std(ddof=1)))
    check("ledger: a member's study gains the looks and no spread",
          member["n"] == 4 * 7 and np.isnan(member["sigma"]))

    floor = real.floor_risk({"x": {"min_size": 0.1, "factor": 0.004}},
                            {"funded": {"min_lot": 0.01}, "real": {"account": 10000}})
    check("floor risk: half a 0.01 lot over 0.1 lots x 0.004 x 10,000 = 0.125 % per trade",
          np.isclose(floor["x"], 0.00125))


def test_run_folder(found: dict) -> None:
    """The run folder, the owner's summary and the admission pass, on the tiny pool."""
    unit, dates, graph = tiny_pool()
    ids = ["A", "B", "C", "D"]
    result = {"pool_name": "tiny", "kept": ids, "excluded": [], "identities": ids,
              "floor": {"A": 0.002, "B": 0.004, "C": 0.001, "D": 0.001}, "found": found,
              "root_seed": 1, "account": 10000.0, "unit": unit, "graph": {"graph": graph}}
    table = real.frame(result)
    real_runs = real.RUNS
    with tempfile.TemporaryDirectory() as tmp:
        real.RUNS = Path(tmp)
        try:
            out = real.write_run(result, table)
            manifest = json.loads((out / "manifest.json").read_text())
            rows = len(pd.read_parquet(out / "search.parquet"))
            judged = real.admit(result, out, "finite")
        finally:
            real.RUNS = real_runs
    text = real.summarise(result, table, None)
    print("       " + text.replace("\n", "\n       "))
    check("run folder: search.parquet has one row per evaluation, the manifest names {A, B}",
          rows == 7 and manifest["best_members"] == ["A", "B"] and manifest["verdict"] is None)
    check("a combination's floor risk is its most demanding member's: {A, B} -> 0.4 %",
          table["floor_risk"][found["best"]] == 0.004)
    check("summary: the cost next to the choice, and no verdict",
          "K=2" in text and "deja fuera 2 estrategias" in text and "Sin veredicto" in text
          and "0.80% del balance" in text)
    check("admission to {A, B}: C is admissible with A only, D with neither -> both blocked",
          judged["candidate"].tolist() == ["C", "D"] and judged["blocked_by"].tolist() == [1, 2]
          and not judged["enters"].any())


def test_build_only_source() -> None:
    """No module of the rank search names a later segment (PLAN §8.4 b)."""
    files = ["objective.py", "exhaustive.py", "admission.py", "choose.py"]
    text = "".join((SEARCH / f).read_text(encoding="utf-8") for f in files)
    check("search modules never name oos1 or oos2", "oos1" not in text and "oos2" not in text)


def main() -> None:
    """Run every case; exit non-zero on any failure."""
    test_metrics_by_hand()
    found = test_tiny_pool()
    test_admission()
    test_ledger_and_floor(found)
    test_run_folder(found)
    test_build_only_source()
    print(f"\n{'TODO OK' if not FAILURES else 'FALLOS: ' + ', '.join(FAILURES)}")
    sys.exit(1 if FAILURES else 0)


if __name__ == "__main__":
    main()
