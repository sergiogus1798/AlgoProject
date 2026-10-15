#!/usr/bin/env python3
"""Step 18 from a batch to its facts: the panel's screen, the result's shape, trades into cells, the loss against its null."""

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engines.weekly import panel as weekly
from studies.optimisation.cscv import contract, many, report
from studies.optimisation.cscv.inputs import batch
from studies.optimisation.cscv.measure import outputs, queue
from studies.optimisation.cscv.verdict import state
from tests.test_cscv import TOL, cfg_of, noise


def synthetic(width: int = 80, edge: float = 0.25) -> tuple[pd.DataFrame, dict]:
    """A batch as `inputs.batch.read` returns it: the mother, a copy of her, two controls, one thin variant."""
    ids = [f"P{i:05d}" for i in range(width + 4)]
    index = pd.date_range("2012-01-02", periods=400, freq="7D", name="week")
    net = pd.DataFrame(
        noise(7, 400, len(ids), 0.05) + edge * (np.arange(len(ids)) == 9),
        index=index,
        columns=ids,
    )
    net[ids[1]] = net[ids[0]]
    rng = np.random.default_rng(2)
    metrics = pd.DataFrame(
        {
            "variant_id": ids,
            "param_a": rng.integers(5, 40, len(ids)),
            "param_b": rng.integers(1, 9, len(ids)),
            "param_frozen": 14,
            "stratum": ["origin"] + ["lhs"] * (width + 1) + ["canary", "inert"],
        }
    )
    info = pd.DataFrame({"trades": 300, "print": ids}, index=ids)
    info.loc[ids[1], "print"] = ids[0]  # the same trade list as the mother
    info.loc[ids[2], "trades"] = 20  # under 15 x 2 live parameters
    return metrics, {
        "net": net,
        "gross": net + 0.02,
        "info": info,
        "years": 7.7,
        "cached": False,
        "wall_s": 0.0,
    }


def test_a_synthetic_batch_from_the_panel_to_the_facts() -> None:
    """Controls, the copy and the thin variant leave, the mother stays, and the facts are the contract's."""
    metrics, cells = synthetic()
    cfg = cfg_of()
    measured, perf = many.run({"lote": (metrics, cells)}, cfg)
    got = measured["lote"]
    facts, counts = got["facts"], got["counts"]
    assert (
        counts["controles"] == 2
        and counts["duplicados"] == 1
        and counts["suelo_parametros"] == 1
    )
    assert counts["vivos"] == 2 and facts["n"] == 80 and got["names"][0] == "P00000"
    assert abs(facts["duplicados_pct"] - 1 / 82) < 1e-12
    for key in (
        "p_perdida",
        "p_perdida_sobre_p95",
        "pbo_sobre_p95",
        "pbo",
        "pbo_p",
        "beta",
        "r2",
        "orden_estable",
        "hc",
        "duplicados_pct",
        "n",
        "estado",
    ):
        assert key in facts, key
    assert {"pbo_p5", "pbo_p95", "pbo_mediana", "p_perdida", "p_perdida_p95"} <= set(
        facts["nulo"]
    )
    assert facts["p_perdida_sobre_p95"] == int(
        facts["p_perdida"] > facts["nulo"]["p_perdida_p95"]
    )
    assert (
        set(facts["potencia"]) == {"d01", "d02", "d03"}
        and "puesto_mediano" in facts["madre"]
    )
    assert facts["pbo_sobre_p95"] == int(facts["pbo"] >= facts["nulo"]["pbo_p95"])
    assert (
        facts["estado"] == state.state(facts, cfg) == "pasa"
        and facts["p_perdida"] < 0.05
    )
    assert got["read"]["seleccion"]["mas_elegida"] == "P00009"
    found = report.result("lote", got, perf, cells, cfg, time.time())
    assert found["verdict"]["state"] == "pass" and found["facts"]["estado"] == "pasa"
    assert found["verdict"]["label"].startswith("PASA — no descarta")
    assert {
        "wall_s",
        "procesos",
        "sorteos",
        "mem_proceso_max_mb",
        "cpu_s",
        "panel_s",
    } <= set(found["rendimiento"])
    assert [t["name"] for t in found["tabs"]] == [
        "lectura",
        "degradacion",
        "seleccion",
        "potencia",
    ]
    assert len(contract.cloud(got)["points"]) == contract.SHOWN


def test_too_few_variants_is_limbo_with_nothing_measured() -> None:
    """Under `panel.min_variants` after the filters: no CSCV, `sin dato`, LIMBO."""
    metrics, cells = synthetic(20)
    cfg = cfg_of()
    measured, perf = many.run({"lote": (metrics, cells)}, cfg)
    facts = measured["lote"]["facts"]
    assert set(facts) == {"n", "duplicados_pct", "estado"} and perf == {}
    assert (
        facts["n"] == 20
        and facts["estado"] == "limbo"
        and abs(facts["duplicados_pct"] - 1 / 22) < 1e-12
    )
    found = report.result("lote", measured["lote"], perf, cells, cfg, time.time())
    assert (
        found["verdict"]["state"] == "watch"
        and "Sin dato" in found["verdict"]["meaning"]
    )


def test_trades_become_the_weekly_cells_whatever_the_cut() -> None:
    """Synthetic trades priced in groups of variants equal the whole priced at once; a copy shares its print."""
    index = pd.date_range("2019-12-01", "2021-01-31 23:00", freq="h")
    opened = 100.0 + np.cumsum(np.random.default_rng(0).normal(0.02, 1, len(index)))
    bars = pd.DataFrame(
        {"Open": opened, "High": opened + 1.5, "Low": opened - 1.5, "Close": opened},
        index=index,
    )
    costs = {
        "point_value": 1.0,
        "tick_size": 0.01,
        "spread": 0.5,
        "slippage": 0.25,
        "commission_method": "SizeBased",
        "rounds": True,
        "commission": 2.0,
        "swap_long": 0.0,
        "swap_short": 0.0,
        "triple": 2,
        "rollover": 0,
    }
    asset = {
        "sqx_symbol": None,
        "segments": {
            "build": {"from": "2020-01-01", "to": "2020-04-30"},
            "oos1": {"from": "2020-05-01", "to": "2020-08-31"},
            "oos2": {"from": "2020-09-01", "to": "2020-12-31"},
        },
    }
    rng, frames = np.random.default_rng(1), []
    for leg, bounds in asset["segments"].items():
        for v in range(40):
            start = pd.Timestamp(bounds["from"]) + pd.to_timedelta(
                np.sort(rng.integers(24, 2400, 12)), "h"
            )
            frames.append(
                pd.DataFrame(
                    {
                        "variant_id": f"P{v:03d}",
                        "leg": leg,
                        "Type": "Buy",
                        "Size": 1.0,
                        "Open time": start,
                        "Close time": start + pd.Timedelta(hours=7),
                        "Open price": 0.0,
                        "Close price": 0.0,
                        "Profit/Loss": 0.0,
                    }
                )
            )
    trades = pd.concat(frames, ignore_index=True)
    copy = trades[trades["variant_id"] == "P000"].assign(variant_id="P999")
    trades = pd.concat([trades, copy], ignore_index=True)
    term = {"window": "year", "variant": "b"}
    wide, info = batch.build(
        trades, bars, asset, {leg: costs for leg in asset["segments"]}, term, 8
    )
    whole = pd.concat(
        [
            weekly.per_trade(
                trades[trades["leg"] == leg], bars, costs, (b["from"], b["to"]), term
            )
            for leg, b in asset["segments"].items()
        ]
    )
    want = weekly.weekly(whole, ("2020-01-01", "2020-12-31"), units=wide["net"].columns)
    assert np.allclose(wide["net"], want["net"]) and np.allclose(
        wide["gross"], want["gross"]
    )
    assert (wide["gross"].sum() > wide["net"].sum()).all() and (
        info["trades"] == 36
    ).all()
    assert (
        info.loc["P999", "print"] == info.loc["P000", "print"]
        and info["print"].nunique() == 40
    )


def facts_of(lost: float, null_lost: list[float], cfg: dict) -> dict:
    """state.facts on a hand-made reading: only the probability of loss and its null vary."""
    row = {
        "pbo": 0.3,
        "beta": -0.5,
        "r2": 0.1,
        "hc": 0.2,
        "primer_orden": True,
        "segundo_orden": True,
        "brecha": 0.0,
    }
    draws = pd.DataFrame([row | {"pbo": 0.5, "p_perdida": x} for x in null_lost])
    read = {
        "real": row | {"p_perdida": lost},
        "bruto": row | {"p_perdida": lost},
        "seleccion": {"distintas": 3, "peso": 0.5},
        "madre": None,
    }
    return state.facts(
        read,
        {"nulo": draws, "nulo_bruto": draws},
        {"quedan": 100, "duplicados_pct": 0.0},
        cfg,
    )


def test_the_loss_is_read_against_its_own_null_s_percentile() -> None:
    """Null losses 0.00 .. 1.00 in 101 steps: p95 = 0.95, median 0.50; over it is strict."""
    cfg, null_lost = cfg_of(), list(np.linspace(0, 1, 101))
    got = facts_of(0.2, [x * 0.2 for x in null_lost], cfg)
    assert np.isclose(got["nulo"]["p_perdida_p95"], 0.19) and np.isclose(
        got["nulo"]["p_perdida"], 0.1
    )
    assert got["p_perdida_sobre_p95"] == 1 and got["estado"] == "limbo"
    assert facts_of(0.19, [x * 0.2 for x in null_lost], cfg)["estado"] == "pasa"
    assert facts_of(0.0, [0.0] * 50, cfg)["p_perdida_sobre_p95"] == 0  # 0 is not over 0
    assert facts_of(0.6, [x * 0.2 for x in null_lost], cfg)["estado"] == "no_pasa"
    lower = facts_of(
        0.15, [x * 0.2 for x in null_lost], cfg_of("state.p_perdida_null_pct=50")
    )
    assert (
        np.isclose(lower["nulo"]["p_perdida_p95"], 0.1) and lower["estado"] == "limbo"
    )


def over_its_null(mean: float, shared: float, count: int) -> tuple[float, float, float]:
    """Share of no-edge panels over their own null's p95 of loss, its standard error, and the share in LIMBO."""
    cfg = cfg_of("null.draws=100", "perf.workers=96", "power.deltas=[]")
    made = {i: noise(1000 + i, 400, 60, mean, shared) for i in range(count)}
    found, _ = queue.run(
        {i: {"net": x, "gross": x, "track": None} for i, x in made.items()}, cfg
    )
    counts = {"quedan": 60, "duplicados_pct": 0.0}
    said = [
        state.facts(
            {
                "real": outputs.summary(got["net"], TOL),
                "bruto": got["gross"],
                "seleccion": {"distintas": 0, "peso": 0.0},
                "madre": None,
            },
            got["draws"],
            counts,
            cfg,
        )
        for got in found.values()
    ]
    over = float(np.mean([f["p_perdida_sobre_p95"] for f in said]))
    return (
        over,
        float(np.sqrt(over * (1 - over) / count)),
        float(np.mean([f["estado"] == "limbo" for f in said])),
    )


def test_no_edge_is_over_its_null_s_p95_at_most_one_time_in_twenty() -> None:
    """Near 5 % with independent columns; under it when the columns share a factor.

    The null is equalised to the panel's OWN median Sharpe and then redrawn, so the real
    loss sits at the centre of its null: a shared factor moves both together and the real
    one never reaches the tail. The rule is conservative on correlated variants.
    """
    over, error, limbo = over_its_null(0.10, 0.0, 300)
    print(
        f"     columnas independientes, Sharpe semanal 0,10: sobre el p95 de su nulo {over:.3f} "
        f"± {error:.3f}; en LIMBO {limbo:.3f} (300 paneles, 100 sorteos)"
    )
    assert 0.02 <= over <= 0.09 and limbo <= over, (over, limbo)
    over, error, limbo = over_its_null(0.03, 0.6, 200)
    print(
        f"     columnas correlacionadas 0,6, Sharpe semanal 0,03: sobre el p95 de su nulo {over:.3f} "
        f"± {error:.3f}; en LIMBO {limbo:.3f} (200 paneles, 100 sorteos)"
    )
    assert over <= 0.02 and limbo <= over, (over, limbo)


if __name__ == "__main__":
    for name, test in list(globals().items()):
        if name.startswith("test_"):
            began = time.time()
            test()
            print(f"  ok   {name} ({time.time() - began:.1f} s)")
    print("todas las propiedades se cumplen")
