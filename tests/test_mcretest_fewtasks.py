#!/usr/bin/env python3
"""The MC Retest study on an ingest that holds only `bar` and `ohlc` (the chain since 2026-10-07):
one strategy and the population assemble without the production task — no stress tab, the old
verdict INCONCLUSIVE and never FAIL — and the tab «Fragilidad» carries T1 alone (T2 and T3 are
gone, encargo 65 §3d), under keys `pipeline.autopilot.facts.flatten` names by test, window and
measure, none by row order."""

import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.autopilot.facts import flatten
from studies.breakage.mcRetest import many, one
from studies.breakage.mcRetest.contract import retention
from studies.breakage.mcRetest.inputs import config
from studies.breakage.mcRetest.measure import store
from studies.breakage.mcRetest.model import recon

NAME, TRADES, RUNS = "1.2.3", 40, 30
KEYS = {"project": "P", "databank": "MCR_All", "day": "2026-10-07"}


def ingest(root: Path, cfg: dict) -> dict:
    """A two-task ingest of one strategy on an hourly grid: load.load()'s inputs."""
    rng = np.random.default_rng(7)
    grid = pd.date_range("2019-01-01", periods=12000, freq="h")
    cents = rng.integers(-3000, 6000, TRADES)
    opened = grid[700 + 250 * np.arange(TRADES)]
    dated = pd.DataFrame({"strategy": NAME, "Type": "Buy", "Open time": opened,
                          "Close time": opened + pd.Timedelta(hours=10), "Size": 1.0,
                          "cost": 0.0, "pnl": cents / 100.0})
    runs = {"bar": [cents[k % 4:] for k in range(RUNS)],
            "ohlc": [cents + rng.integers(-400, 400, TRADES) for _ in range(RUNS)]}
    capital, sims, original = cfg["ingest"]["capital"], [], []
    for task, vectors in runs.items():
        offsets = np.r_[0, np.cumsum([v.size for v in vectors])]
        flat = np.concatenate(vectors)
        sims.append(pd.DataFrame({"task": task, "strategy": NAME, "sim": range(RUNS),
                                  **recon.frame(flat, offsets, capital)}))
        original.append({"task": task, "strategy": NAME, **{
            k: float(v[0]) for k, v in recon.frame(cents, np.array([0, TRADES]), capital).items()}})
        store.write(pd.DataFrame({"task": task, "strategy": NAME,
                                  "sim": np.repeat(range(RUNS), np.diff(offsets)),
                                  "pnl_cents": flat}), root / store.PNL, ["task", "strategy"], "zstd")
        store.write(pd.DataFrame({"task": task, "strategy": NAME, "pnl_cents": cents}),
                    root / store.ORIGINAL_PNL, ["task"], "zstd")
    store.write(pd.concat(sims), root / store.SIMS, ["task", "strategy"], "zstd")
    store.write(pd.DataFrame(original), root / store.ORIGINAL, [], "zstd")
    store.write(dated, root / store.BUILD, ["strategy"], "zstd")
    store.write(dated.tail(8), root / store.TRADES, ["strategy"], "zstd")
    store.write(pd.DataFrame(columns=["strategy", "date", "ret"]), root / store.RETURNS, [], "zstd")
    ran = {"usable": True, "stored": RUNS, "declared": RUNS, "identity": "id-1"}
    return {"keys": KEYS, "sims": store.load_sims(**KEYS), "original": store.load_original(**KEYS),
            "levels": pd.DataFrame({"task": ["bar"], "strategy": [NAME], "level": [95],
                                    "metric": ["NetProfit"], "value": [1.0]}),
            "provenance": {f"bar/{NAME}": {**ran, "methods": {"RandomizeStartingBar":
                                                               {"MaxChange": "500"}}},
                           f"ohlc/{NAME}": {**ran, "methods": {"RandomizeHistoryDataOHLC": {}}}},
            "identity": {NAME: "id-1"}, "trades": None, "asset": None, "folder": root}


def test_only_bar_and_ohlc() -> None:
    """Both entry points run, the result says what it could not judge, and the facts are named."""
    cfg = config.load(["fragility.n_resamples=99"])
    real = store.root
    with tempfile.TemporaryDirectory() as tmp:
        store.root = lambda project, databank, day: Path(tmp)
        inputs = ingest(Path(tmp), cfg)
        try:
            got = one.run(NAME, inputs, cfg)
            population = many.run(inputs, cfg)
        finally:
            store.root = real

    assert [t["name"] for t in got["tabs"]] == ["verdict", "cost", "tasks", "levels"]
    assert got["verdict"]["label"] == "INCONCLUSIVE"
    assert got["summary"]["blocked_by"] == "sin_tarea_de_produccion"
    facts = dict(flatten(got))
    assert not [k for k in facts if "#" in k]
    assert not [k for k in facts if k.startswith("fragilidad.")]   # no neighbour batch: no T1
    assert len(population["members"]) == 1
    # without the stress task its three columns are absent, and so is their help (OPEN.md #109)
    tables = [b for t in population["population"]["tabs"] for b in t["blocks"] if b.get("help")]
    assert tables and all(len(b["help"]) == len(b["columns"]) for b in tables)
    assert population["members"][0]["verdict"]["label"] == "INCONCLUSIVE"


def test_t1_facts_enter_the_tab() -> None:
    """T1's flat facts become one row per window, and `t1.rho_vec` the row of both."""
    tab = retention.tab({"t1.build.ret_med": 0.8, "t1.oos1.ret_med": 0.2, "t1.rho_vec": 0.4})
    facts = {k: v for k, v in flatten({"tabs": [tab]}) if v is not None}
    assert facts == {"fragilidad.t1.build.ret_med": 0.8, "fragilidad.t1.oos1.ret_med": 0.2,
                     "fragilidad.t1.ambas.rho_vec": 0.4}
    assert retention.tab(None) is None


def test_the_neighbour_table_carries_its_manifest() -> None:
    """`t1.measure` files its parquet with a manifest beside it (OPEN.md #109: the 2026-10-08
    export had none, and the audit cannot tell such a folder from a torn one)."""
    import json

    from core import manifest
    from studies.breakage.mcRetest.neighbours import t1
    was = (t1.assetdata.load, t1.barstore.read, t1.reprice.costs, t1.engines_excess.per_trade, t1.gate.market, t1.export_dir)
    with tempfile.TemporaryDirectory() as tmp:
        root, legs = Path(tmp), [{"segment": "build", "databank": "B"}]
        (root / "ran.json").write_text(json.dumps({"legs": legs}))
        pd.DataFrame({"variant_id": ["V0"], "strategy": ["M"], "neighbour": [0]}).to_parquet(
            root / "manifest.parquet")
        raw = root / "raw" / "B" / "d" / t1.BATCH
        raw.mkdir(parents=True)
        pd.DataFrame({"strategy": ["V0"], "Symbol": ["F"],
                      "Close time": [pd.Timestamp("2020-01-01")]}).to_parquet(raw / "trades.parquet")
        pd.DataFrame({"strategy": ["V0"]}).to_csv(raw / "identity.csv")
        t1.assetdata.load = lambda symbol: {"sqx_symbol": "F", "segments": {"build": {"from": 1, "to": 2}}}
        t1.barstore.read = t1.reprice.costs = lambda *a: None
        t1.engines_excess.per_trade = lambda trades, *a: pd.DataFrame(
            {"variant_id": trades["variant_id"], "profit": [1.0], "drift": [0.5]})
        t1.gate.market = lambda feed: {"risk": 1.0}
        t1.export_dir = lambda project, bank, day, *tag: root / "raw" / bank / day
        try:
            out = t1.measure("P", root, "X", "M30", "d")
        finally:
            t1.assetdata.load, t1.barstore.read, t1.reprice.costs, t1.engines_excess.per_trade, t1.gate.market, t1.export_dir = was
        assert manifest.read(out.parent)["counts"] == {t1.FILE: 1}


if __name__ == "__main__":
    test_only_bar_and_ohlc()
    test_t1_facts_enter_the_tab()
    test_the_neighbour_table_carries_its_manifest()
    print("ok")
