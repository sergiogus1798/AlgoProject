#!/usr/bin/env python3
"""Known-answer test for step 18.5: the worked example, the weights, the exclusions, the split of oos2."""

import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import assetdata
from core.study import blocks
from engines.weekly import flip
from studies.optimisation.marketSurfaces import one, report
from studies.optimisation.marketSurfaces.inputs import batch, config, markets
from studies.optimisation.marketSurfaces.measure import order, reading
from studies.optimisation.marketSurfaces.verdict import call

N, WEEKS, FEEDS = 80, 60, [f"M{i}_M1" for i in range(7)]
IDS = [f"P{i:05d}" for i in range(N)]
CFG = config.load(["null.draws=199", "power.draws=40", "markets.min_common=50", "workers=1"])
CFG["panel"] = {"floor_is_per_param": 1, "floor_oos_per_year": 10, "min_variants": 30}
TABLE = pd.DataFrame({"feed": FEEDS, "category": ["family"] * 5 + ["structural"] * 2,
                      "data_from": None, "group": [0, 0, 0, -1, -1, -1, -1]})


def leg(rng: np.random.Generator, start: str, tilt: np.ndarray | None = None) -> dict:
    """One market's leg as `inputs.batch.one` returns it: noise the variants share, plus a tilt."""
    week = pd.date_range(start, periods=WEEKS, freq="W-MON", name="week")
    gross = rng.normal(size=(WEEKS, 1)) + rng.normal(size=(WEEKS, N)) + (0 if tilt is None else tilt)
    frame = pd.DataFrame(gross, index=week, columns=IDS)
    return {"gross": frame, "net": frame - 0.05, "n": np.full(N, 40), "trades": 40 * N,
            "straddle": 0.02, "gap": 0.0}


def batch_data(seed: int, oos2: bool, tilt: float = 0.0) -> tuple[dict, dict, dict]:
    """A synthetic batch: seven markets, no edge unless `tilt` ties them to the main order."""
    rng, late = np.random.default_rng(seed), np.random.default_rng(seed + 1000)
    main ={"build": leg(rng, "2012-01-02"), "oos1": leg(rng, "2020-01-06")}
    x = sum(main[k]["gross"].to_numpy().sum(axis=0) for k in main)
    lean = tilt * (x - x.mean()) / x.std()
    data = {one.MAIN: {"legs": main, "prints": pd.Series([f"h{i}" for i in range(N)], index=IDS)}}
    for feed in FEEDS:
        legs = {"build": leg(rng, "2012-01-02", lean), "oos1": leg(rng, "2020-01-06", lean)}
        data[feed] = {"legs": legs | ({"oos2": leg(late, "2024-01-01", lean)} if oos2 else {})}
    design = {"ids": IDS, "mother": IDS[0], "k": 2, "params": pd.DataFrame(
        {"param_a": np.arange(N) % 4, "param_b": np.arange(N) // 4 % 5, "param_c": 1}, index=IDS)}
    years = {m: {"build": 1.0, "oos1": 1.0, "oos2": 1.0} for m in data}
    return data, design, years


def check_example() -> None:
    """The proposal's five variants: rho 0.80 and -0.50, joint 0.15 with weights of 1."""
    main, dax, gold = (np.array(v, float) for v in ([5, 4, 3, 2, 1], [4, 5, 2, 3, 1], [1, 4, 2, 5, 3]))
    assert np.isclose(flip.spearman(main, dax), 0.80) and np.isclose(flip.spearman(main, gold), -0.50)
    assert np.isclose(order.joint(np.array([0.80, -0.50]), order.weights([-1, -1])), 0.15)
    cfg = config.load(["markets.min_common=5", "markets.min_weight=2", "null.draws=99"])
    table = pd.DataFrame({"feed": ["DAX", "ORO"], "category": ["family", "structural"], "group": -1})
    panels = {f: {"gross": v[None, :], "net": v[None, :], "ok": np.ones(5, bool)}
              for f, v in (("DAX", dax), ("ORO", gold))}
    found = reading.measure(main, main >= 5, panels, table, 0, cfg, np.random.SeedSequence(1))
    assert np.allclose(found["mercados"]["rho"], [0.80, -0.50]) and np.isclose(found["orden"]["rho"], 0.15)
    assert found["orden"]["peso"] == 2 and set(np.round(np.abs(found["nulo"]), 9)) == {0.15}


def check_weights() -> None:
    """A group of near-identical markets shares one vote, whoever of it is in the mean."""
    assert np.allclose(order.weights([0, 0, 0, -1, -1]), [1 / 3] * 3 + [1, 1])
    assert np.allclose(order.weights([0, 0, -1]), [0.5, 0.5, 1]) and order.weights([0, -1]).sum() == 2
    nikkei = markets.declared("NIKKEI225")
    trio = nikkei[nikkei["group"] >= 0]
    assert set(trio["feed"]) == {"USA500_M1", "USATEC_M1", "DJ30_M1"}
    assert np.isclose(order.weights(nikkei["group"]).sum(), len(nikkei) - 2)
    assert set(assetdata.markets("NIKKEI225")["categories"]) == {"family", "structural"}
    data, design, years = batch_data(3, False)
    found = one.measure(data, design, TABLE, years, CFG, False)["principal"]
    assert np.allclose(found["mercados"]["weight"], [1 / 3] * 3 + [1] * 4) and found["orden"]["peso"] == 5


def check_exclusions() -> None:
    """Too many ties or too few common variants leave a market out; under the weight floor, no call."""
    data, design, years = batch_data(4, False)
    for name in ("build", "oos1"):
        flat = data[FEEDS[3]]["legs"][name]
        flat["gross"].iloc[:, : N * 3 // 4] = flat["gross"].iloc[:, [0]].to_numpy()
        data[FEEDS[4]]["legs"][name]["n"] = np.where(np.arange(N) < 45, 40, 0)
    measured = one.measure(data, design, TABLE, years, CFG, False)
    rows = measured["principal"]["mercados"].set_index("feed")
    assert rows.at[FEEDS[3], "ties"] >= 0.75 and not rows.at[FEEDS[3], "included"]
    assert rows.at[FEEDS[4], "n"] == 45 and not rows.at[FEEDS[4], "included"]
    assert rows.at[FEEDS[3], "weight"] == 0 and measured["principal"]["orden"]["peso"] == 3
    facts, state = one.facts(measured, CFG)
    assert "estado" not in facts["orden"] and state == "watch" and facts["orden"]["mercados"] == 3
    assert call.order({"rho": 0.3, "p_mas": 0.01, "p_menos": 0.99, "peso": 4.9}, 0.05, 5) == "sin_dato"


def check_main_untouched() -> None:
    """Only the other markets are flipped, and one sign vector serves every market."""
    data, design, years = batch_data(5, False)
    seen, real = [], flip.spearman
    reading.flip.spearman = lambda fixed, redrawn: seen.append(fixed.copy()) or real(fixed, redrawn)
    try:
        found = one.measure(data, design, TABLE, years, CFG, False)
    finally:
        reading.flip.spearman = real
    x = found["totals"][one.MAIN]
    build = data[one.MAIN]["legs"]["build"]["gross"].to_numpy().sum(axis=0)   # the reference's side
    assert len(seen) > len(FEEDS) and all(np.array_equal(s, x) for s in seen[:-1])
    assert np.array_equal(seen[-1], build)
    same = {f: data[FEEDS[3]] for f in FEEDS}
    twin = one.measure({one.MAIN: data[one.MAIN]} | same, design, TABLE, years, CFG, False)["principal"]
    alone = reading.measure(x, np.zeros(N, bool), {FEEDS[3]: {
        k: batch.stacked(list(data[FEEDS[3]]["legs"].values()), k) for k in ("gross", "net")}
        | {"ok": np.ones(N, bool)}}, TABLE.iloc[[3]], 0, CFG | {"markets": CFG["markets"] | {"min_weight": 1}},
        np.random.SeedSequence(CFG["null"]["seed"]).spawn(3)[0], planted=False)
    assert np.allclose(twin["nulo"], alone["nulo"]), "identical markets must share every week's sign"


def check_oos2_split() -> None:
    """Without the flag no oos2 leg is asked for, read or reported; with it, the block appears."""
    assert "oos2" not in sum(one.legs(FEEDS, False).values(), ()) and one.legs(FEEDS, True)[one.MAIN] == one.INSIDE
    data, design, years = batch_data(6, False)
    facts, _ = one.facts(one.measure(data, design, TABLE, years, CFG, False), CFG)
    assert "oos2" not in facts and {"rho", "p_mas", "p_menos", "nulo_p5", "nulo_p95", "mercados"} <= set(facts["orden"])
    assert {"valor", "nulo_p5", "bajo_p5"} <= set(facts["prima"]) and set(facts["potencia"]) == {"r01", "r02", "r03"}
    data, design, years = batch_data(6, True)
    both, _ = one.facts(one.measure(data, design, TABLE, years, CFG, True), CFG)
    assert set(both["oos2"]) == {"rho", "p_mas", "p_menos", "mercados", "perverso", "sin_dato"} and both["oos2"]["sin_dato"] == 0
    blind = one.measure(data, design, TABLE, years, CFG, True)
    blind["oos2"]["orden"] = blind["oos2"]["orden"] | {"peso": 0.0}
    gap, state = one.facts(blind, CFG)
    assert gap["oos2"]["sin_dato"] == 1 and "perverso" not in gap["oos2"] and state == "watch", "oos2 sin dato must be LIMBO"
    assert both["orden"] == facts["orden"] and both["prima"] == facts["prima"], "oos2 moved the deciding reading"
    asked, real = [], pd.read_parquet
    with tempfile.TemporaryDirectory() as tmp:
        pd.DataFrame({"variant_id": IDS[:2], "leg": ["build", "oos2"], "market": "Main"}
                     | dict.fromkeys(batch.fingerprint.COLUMNS, 0.0)).to_parquet(Path(tmp) / batch.TRADES)
        batch._JOB.update(work=Path(tmp), feed="X", timeframe="M30", ids=["none"], legs=one.legs([], False),
                          asset=assetdata.load("NIKKEI225"), drift={}, costs=CFG["costs"])
        batch.barstore.read = lambda feed, timeframe: None
        batch.pd.read_parquet = lambda path, **kw: asked.append(kw["filters"]) or real(path, **kw)
        try:
            got = batch.one(one.MAIN)
        finally:
            batch.pd.read_parquet = real
    assert set(got["legs"]) == set(one.INSIDE) and "oos2" not in str(asked) and len(asked) == 2


def check_determinism_and_states() -> None:
    """One seed, one result, whatever the chunk; and the worst reading names the state.

    To nine digits: the chunked product rounds its last bit by the CPU's BLAS kernel, and
    gorilla's 7950X gave -0.6231758175072347 where this server gives ...346 (📓 2026-10-11)."""
    data, design, years = batch_data(7, True, tilt=0.4)
    first = one.facts(one.measure(data, design, TABLE, years, CFG, True), CFG)
    again = one.facts(one.measure(data, design, TABLE, years, CFG | {"null": CFG["null"] | {"chunk": 7}}, True), CFG)
    other = one.facts(one.measure(data, design, TABLE, years, CFG | {"null": CFG["null"] | {"seed": 9}}, True), CFG)
    assert blocks.plain(first, 9) == blocks.plain(again, 9) and first[0]["orden"]["nulo_p95"] != other[0]["orden"]["nulo_p95"]
    assert first[0]["orden"]["estado"] == "positivo" and first[1] == "pass"
    turned = one.facts(one.measure(*batch_data(7, False, tilt=-0.4)[:1], design, TABLE, years, CFG, False), CFG)
    assert turned[0]["orden"]["estado"] == "perverso" and turned[1] == "fail"
    assert [call.step(*k) for k in (("neutro", False, None), ("positivo", True, None), ("neutro", False, "perverso"),
                                    ("sin_dato", None, None), ("perverso", False, "positivo"),
                                    ("neutro", False, "sin_dato"))] == ["pass", "watch", "watch", "watch", "fail", "watch"]
    measured = one.measure(data, design, TABLE, years, CFG, True)
    res = report.result("Strategy_1", measured, "MAIN", [FEEDS[0]], CFG, 0.0)
    assert res["verdict"]["label"] == "PASA · la zona viaja" and res["facts"]["oos2"]["perverso"] == 0 and res["facts"]["oos2"]["sin_dato"] == 0
    assert [t["name"] for t in res["tabs"]] == ["principal", "prima", "referencia", "oos2"]
    assert res["warnings"][0]["code"] == "costs_provisional" and FEEDS[0] in res["warnings"][0]["text"]


def rates(rho: float, families: int = 300, feeds: int = 10) -> dict[str, float]:
    """Share of synthetic families read each way when every market carries a true Spearman `rho`.

    Each week has a shock every market and variant shares, one per market and one per variant,
    all symmetric; the transmission is a constant weekly lean along the main market's order.
    """
    cfg = CFG | {"markets": CFG["markets"] | {"min_weight": 5.0}}
    table = pd.DataFrame({"feed": [f"F{i}" for i in range(feeds)], "category": "family", "group": -1})
    lean, said = rho / np.sqrt(1 - rho ** 2) / np.sqrt(WEEKS), []
    for family in range(families):
        rng = np.random.default_rng([family, round(rho * 100)])
        x, world = rng.normal(size=N), rng.normal(size=(WEEKS, 1))
        panels = {}
        for feed in table["feed"]:
            weekly = world + rng.normal(size=(WEEKS, 1)) + rng.normal(size=(WEEKS, N)) + lean * x
            panels[feed] = {"gross": weekly, "net": weekly, "ok": np.ones(N, bool)}
        found = reading.measure(x, x > 1, panels, table, None, cfg, np.random.SeedSequence(family),
                                planted=False)
        said.append(call.order(found["orden"], cfg["null"]["alpha"], cfg["markets"]["min_weight"]))
    return {word: said.count(word) / families for word in ("positivo", "neutro", "perverso")}


def check_rates() -> None:
    """No edge: about 5 % read positive and 5 % perverse. A planted rho of 0.2: nearly always seen."""
    none, planted = rates(0.0), rates(0.2, families=100)
    print(f"   sin ventaja, 300 familias x 10 mercados: {none}\n   rho* 0,2, 100 familias: {planted}")
    assert 0.02 <= none["positivo"] <= 0.09 and 0.02 <= none["perverso"] <= 0.09, none
    assert planted["positivo"] > 0.8 and planted["perverso"] == 0, planted


def check_nothing_usable() -> None:
    """No usable variant, or a value past the colour scale, is a NaN and a cell — not a crash.

    Step 18.5 died three times on them (📓 2026-10-04 quantile and fit of nothing on
    Trade_NIKKEI225_M30_volatilidadL; 2026-10-06 a grid value beyond the last colour)."""
    from core.study.render import grids as drawn
    from studies.optimisation.marketSurfaces.measure import premium
    assert np.isnan(premium.premium(np.arange(5.0), np.zeros(5, bool)))
    cell = {"rows": ["a"], "cols": ["x"], "values": [[99.0]], "labels": None,
            "scale": "sequential", "scale_range": [0, 1], "levels": None, "title": "t"}
    assert "<rect" in drawn.grid(cell)


def main() -> None:
    """Run every check; the first that fails raises."""
    for check in (check_example, check_weights, check_exclusions, check_main_untouched,
                  check_oos2_split, check_determinism_and_states, check_rates,
                  check_nothing_usable):
        check()
        print(f"ok {check.__name__}: {check.__doc__.splitlines()[0]}")


if __name__ == "__main__":
    main()
