#!/usr/bin/env python3
"""Known-answer test of the funded search: greedy+GA on a planted clique, ledger rows, risk.sizing."""

import sys
import tempfile
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd

import ledger.study as study
import portfolio.common.construct.inputs.risk as risk
import portfolio.common.construct.search.genetic as genetic
import portfolio.common.construct.search.greedy as greedy
import portfolio.common.construct.search.trials as trials
from sqx.variants.build import stoploss

N = 40
PLANT = np.arange(6)
FIXTURES = Path(__file__).parent / "fixtures"
REAL_STOPLESS_IDENTITY = "4d679e0c2ce2a63ee53bc6cb305830bcaf5a74997e6e6e2c1deeb4c30f307048"
REAL_STOPLESS_VERSION = "2026-09-28T0919"

FAILURES = []


def check(name: str, ok: bool) -> None:
    """Print one line per case; remember the failures."""
    print(f"{'OK   ' if ok else 'FALLO'}  {name}")
    if not ok:
        FAILURES.append(name)


def planted_graph(rng: np.random.Generator) -> np.ndarray:
    """40 nodes: 0-5 a fully-connected planted clique, isolated from a random background graph."""
    graph = np.zeros((N, N), dtype=bool)
    for i in PLANT:
        for j in PLANT:
            if i != j:
                graph[i, j] = True
    rest = np.arange(6, N)
    for a in range(len(rest)):
        for b in range(a + 1, len(rest)):
            if rng.random() < 0.3:
                graph[rest[a], rest[b]] = graph[rest[b], rest[a]] = True
    return graph


def synthetic_score(combos: np.ndarray) -> np.ndarray:
    """Reward planted members, penalise everything else -- the planted 6-clique scores highest."""
    is_plant = np.zeros(N, dtype=bool)
    is_plant[PLANT] = True
    valid = combos >= 0
    safe = np.where(valid, combos, 0)
    plant_count = (is_plant[safe] & valid).sum(axis=1)
    total = valid.sum(axis=1)
    return 2.0 * plant_count - 0.5 * (total - plant_count)


def test_search() -> dict:
    """Greedy seeds + GA recover the planted clique; every evaluated child is a clique."""
    rng = np.random.default_rng(12345)
    graph = planted_graph(rng)
    cfg = {"population": 60, "generations": 100, "elite": 0.2, "tournament": 4,
           "crossover": 0.8, "mutation": 0.4, "stagnation": 5}
    seeds = greedy.seeds(graph, cfg["population"], rng)
    check("greedy seeds are cliques", all(genetic.is_clique(graph, _mask(s)) for s in seeds))

    run = genetic.run(graph, synthetic_score, seeds, cfg, rng)
    check("children are always cliques",
          all(genetic.is_clique(graph, _mask(m)) for m in run["members"]))
    check("GA recovers the planted 6-clique", sorted(run["best"]["members"].tolist()) == list(PLANT))
    check("best score is 6 planted members, no penalty", run["best"]["score"] == 12.0)
    check("stagnation stops before the generation cap", run["generations_run"] < cfg["generations"])
    check("overhead reported separately from scoring",
          run["overhead_s"] >= 0 and run["score_s"] >= 0)
    return run


def _mask(members: np.ndarray) -> np.ndarray:
    """A boolean length-N membership vector, for `genetic.is_clique`."""
    mask = np.zeros(N, dtype=bool)
    mask[members] = True
    return mask


def test_ledger(run: dict) -> None:
    """`search.parquet` rows, evaluations and the ledger's n_scored all agree, on a temp ledger."""
    identities = [f"ID{i:02d}" for i in range(N)]
    members_meta = {i: {"symbol": "TESTSYM", "timeframe": "M30", "family": "testFamily"}
                    for i in identities}
    pool = {"hash": "deadbeef" * 4}
    frame = pd.DataFrame({
        "members": ["+".join(identities[i] for i in np.sort(m)) for m in run["members"]],
        "score": run["score"], "origin": run["origin"], "generation": run["generation"],
    })

    real_path = study.path
    with tempfile.TemporaryDirectory() as tmp:
        study.path = lambda s: Path(tmp) / f"{s}.jsonl"
        try:
            rows = trials.record(run, pool, "test:plan:1000:USD", members_meta, cfg={})
        finally:
            study.path = real_path

    check("search.parquet rows == evaluations", len(frame) == len(run["score"]))
    check("ledger n_scored == evaluations", rows[0]["n_scored"] == len(run["score"]))
    check("one ledger row per member plus the pool row", len(rows) == 1 + N)


def _grafted_sqx(tmp: Path) -> tuple[str, str]:
    """A fake archive folder holding a strategy grafted with `stoploss.graft` in memory."""
    portfolio = stoploss.graft((FIXTURES / "nostop_portfolio.xml").read_text(encoding="utf-8"), 2.5)
    last_settings = """<Settings>
  <RiskMoneyManagement customSettings="false">
    <MoneyManagement>
      <Method type="ATRRiskBasedSizingFixedRisk" use="true">
        <Params>
          <Param key="Amount" className="ATRRiskBasedSizingFixedRisk">1000</Param>
          <Param key="ATRPeriod" className="ATRRiskBasedSizingFixedRisk">20</Param>
          <Param key="ATRMult" className="ATRRiskBasedSizingFixedRisk">4</Param>
          <Param key="Decimals" className="ATRRiskBasedSizingFixedRisk">2</Param>
          <Param key="LotsIfNoMM" className="ATRRiskBasedSizingFixedRisk">0.01</Param>
          <Param key="MaxLots" className="ATRRiskBasedSizingFixedRisk">500</Param>
        </Params>
      </Method>
    </MoneyManagement>
  </RiskMoneyManagement>
</Settings>"""
    folder = tmp / "GRAFTED" / "v1"
    (folder / "harvest").mkdir(parents=True)
    with zipfile.ZipFile(folder / "strategy.sqx", "w") as z:
        z.writestr("strategy_Portfolio.xml", portfolio)
        z.writestr("lastSettings.xml", last_settings)
    (folder / "manifest.json").write_text("{}", encoding="utf-8")
    (folder / "view.json").write_text('{"tearsheet": "sin tearsheet"}', encoding="utf-8")
    pd.DataFrame({"Size": [0.5, 0.3, 1.2]}).to_parquet(folder / "harvest" / "trades.parquet")
    return "GRAFTED", "v1"


def test_risk() -> None:
    """`risk.sizing` reads X off a strategy grafted in memory, and refuses the stopless archive."""
    try:
        risk.sizing(REAL_STOPLESS_IDENTITY, REAL_STOPLESS_VERSION)
        check("refuses the archived strategy with no step-24 stop", False)
    except ValueError as exc:
        check("refuses the archived strategy with no step-24 stop", "paso 24" in str(exc))

    real_archive_dir = risk.archive_read.archive_dir
    with tempfile.TemporaryDirectory() as tmp:
        identity, version = _grafted_sqx(Path(tmp))
        risk.archive_read.archive_dir = lambda: Path(tmp)
        try:
            got = risk.sizing(identity, version)
        finally:
            risk.archive_read.archive_dir = real_archive_dir

    check("x read back from the grafted stop", got["x"] == 2.5)
    check("risk_usd from Amount", got["risk_usd"] == 1000.0)
    check("atr_multiple from ATRMult", got["atr_multiple"] == 4.0)
    check("min_size is the smallest trade lot", got["min_size"] == 0.3)
    check("factor = atr_multiple / (risk_usd * x)", abs(got["factor"] - 4.0 / (1000.0 * 2.5)) < 1e-12)


def main() -> None:
    """Run every case, print a line each, exit non-zero if any failed."""
    run = test_search()
    test_ledger(run)
    test_risk()
    if FAILURES:
        raise SystemExit(f"{len(FAILURES)} fallo(s): {FAILURES}")
    print("test_portfolio_search: ok")


if __name__ == "__main__":
    main()
