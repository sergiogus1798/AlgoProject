#!/usr/bin/env python3
"""Step 17 on one synthetic batch, from the seal to the facts and step 20: exact duplicates by
trade list, the two floors, the order on gross and the level on net, the SQX check, no data."""

import json
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import assetdata
from engines.variants import excess, panel
from engines.weekly import flip
from ledger import gate
from pipeline.autopilot import facts
from studies.closing.blindJoint import pieces
from studies.optimisation.wfc import one, report
from studies.optimisation.wfc.inputs import batch, config
from studies.optimisation.wfc.measure import reading

SYMBOL = "USDJPY"
CFG = config.load(["null.draws=400"])
COST = 3.0                       # what every synthetic trade pays


def as_trades(net: pd.DataFrame) -> pd.DataFrame:
    """Variants x days of net excess as one trade per cell, opened and closed within its day."""
    rows = net.rename_axis(columns="open").stack().rename("net").reset_index()
    return rows.assign(profit=rows["net"], gross=rows["net"] + COST,
                       close=rows["open"] + pd.Timedelta(hours=12))[batch.COLUMNS]


def synthetic(n: int = 150, seed: int = 3) -> tuple[pd.DataFrame, dict]:
    """A batch whose order persists and whose variants win: `metrics` and what `batch.read` returns.

    n design variants and the mother, 3 controls, 2 variants with the mother's very trades, one
    under the inside floor, one that never trades outside and one without exported trades.
    """
    rng = np.random.default_rng(seed)
    ids = ["P00000"] + [f"P{i:05d}" for i in range(1, n + 8)]
    skill = rng.normal(200.0, 100.0, len(ids))
    span = {leg: pd.date_range(assetdata.segment_start(assetdata.load(SYMBOL), leg),
                               periods=250, freq="B") for leg in panel.SEGMENTS}
    days = {leg: pd.DataFrame(skill[:, None] / 50 + rng.normal(0, 30, (1, 250))
                              + rng.normal(0, 10, (len(ids), 250)),
                              index=pd.Index(ids, name="variant_id"), columns=span[leg])
            for leg in panel.SEGMENTS}
    metrics = pd.DataFrame({"variant_id": ids, "param_a": rng.integers(5, 40, len(ids)),
                            "param_b": rng.integers(1, 9, len(ids)), "param_frozen": 14,
                            "stratum": ["origin"] + ["lhs"] * n + ["canary"] * 2 + ["inert"]
                            + ["lhs"] * 4})
    for label, count in (("build", 300), ("build+oos1", 500), ("oos1", 200), ("oos2", 120),
                         ("oos1+oos2", 320)):
        metrics[f"NumberOfTrades ({label})"] = count
    copies, thin, idle, lost = ids[-4:-2], ids[-2], ids[-1], ids[1]
    metrics.loc[metrics["variant_id"] == thin, ["NumberOfTrades (build)",
                                                "NumberOfTrades (build+oos1)"]] = 20
    metrics.loc[metrics["variant_id"] == idle, ["NumberOfTrades (oos1)", "NumberOfTrades (oos2)"]] = 0
    days = {leg: frame.drop(index=[lost] + ([idle] if leg == "oos2" else []))
            for leg, frame in days.items()}
    for leg in panel.SEGMENTS:           # SQX's figure: the trades exported, nothing for the rest
        metrics[f"NetProfit ({leg})"] = days[leg].sum(axis=1).reindex(ids).fillna(0.0).to_numpy()
    prints = pd.Series({v: "madre" if v in copies or v == ids[0] else v for v in ids if v != lost})
    return metrics, {"per": {leg: as_trades(frame) for leg, frame in days.items()},
                     "prints": prints, "prior": days["oos2"].sum(axis=1) - 5.0}


def unsealed(folder: Path) -> None:
    """A register that opens the block for today's rule of step 17, in a scratch folder."""
    gate.CALIBRATION = folder / "wfc_calibration.json"
    entry = yaml.safe_load(gate.CRITERIA.read_text(encoding="utf-8"))["steps"]["17"]
    gate.CALIBRATION.write_text(json.dumps({"criteria_sha256": gate.criteria_hash(entry),
                                            "abre": True, "fecha": "2026-10-07"}))


def test_a_synthetic_batch_from_the_seal_to_the_facts_and_step_20() -> None:
    """Sealed without a register; with one: filters counted, three compositions, facts as numbers."""
    metrics, got = synthetic()
    real = gate.CALIBRATION
    with tempfile.TemporaryDirectory() as tmp:
        try:
            gate.CALIBRATION = Path(tmp) / "none.json"
            with pytest.raises(PermissionError):
                one.run(metrics, got, SYMBOL, CFG)
            with pytest.raises(PermissionError):
                batch.read(Path(tmp), SYMBOL, "M30")              # before any trade is opened
            unsealed(Path(tmp))
            measured = one.run(metrics, got, SYMBOL, CFG)
            wrong = metrics.assign(**{"NetProfit (oos1)": metrics["NetProfit (oos1)"] + 500.0})
            off = one.run(wrong, got, SYMBOL, CFG)
        finally:
            gate.CALIBRATION = real
        assert off["c1"]["facts"]["descuadre_sqx"] == 1.0 and off["c3"]["facts"]["descuadre_sqx"] == 1.0
        assert "NetProfit de SQX" in off["c1"]["notes"][-1] and not off["c2"]["notes"]
        found = report.result("Strategy_1.2.3", measured, CFG, 0.0)
        file = Path(tmp) / "Strategy_1.2.3" / "estudios" / "wfc.json"
        file.parent.mkdir(parents=True)
        file.write_text(json.dumps(found), encoding="utf-8")
        rows = {r["key"]: r["value"] for r in facts.file_rows("wfc", file)}
        assert pieces.said(file)["state"] == "pass"
        file.write_text(json.dumps(found | {"facts": {"c1": {"estado": "limbo"}}}))
        assert pieces.said(file)["state"] == "watch"
    c1, c2, c3 = (measured[k]["facts"] for k in ("c1", "c2", "c3"))
    assert (c1["lote"], c1["controles"], c1["suelo_dentro"], c1["duplicados"]) == (158, 3, 1, 2)
    assert (c1["suelo_fuera"], c1["sin_valor"], c1["quedan"], c1["vivos"]) == (1, 1, 150, 2)
    assert c2["suelo_fuera"] == 1 and c2["quedan"] == 150         # the outside floor counts oos1 trades, for every composition (D20)
    assert c1["estado"] == "pasa" and c1["orden"] == "positivo" and c1["fuerte"]
    assert "estado" not in c2 and "estado" not in c3 and c2["orden"] == "positivo"
    assert c1["n_top"] == 30 and c1["nivel_top"] > c1["nivel_todas"] > 0
    assert c1["cuadrante_pp"] + c1["cuadrante_pn"] + c1["cuadrante_np"] + c1["cuadrante_nn"] == 150
    assert 0 < c1["r_sel"] and c1["r_sel_p5"] < 0 < c1["r_sel_p95"] < c1["r_sel"]
    assert c1["n_sin_suelos"] == 152 and c1["rho_sin_suelos"] == pytest.approx(c1["rho"], abs=0.1)
    assert c1["descuadre_sqx"] == 0.0 and c1["fines_de_semana"] == 0.0 and c1["p_mas_bloque"] is None
    kept = measured["c1"]["kept"]                     # the order on gross, the level on net
    net_in = pd.concat([got["per"][leg] for leg in ("build", "oos1")]).groupby("variant_id")["net"].sum()
    years_in = batch.years(assetdata.load(SYMBOL), ("build", "oos1"))
    assert np.allclose(kept["e_is"], net_in.reindex(kept["variant_id"]) / years_in)
    gross = one.values(panel.KEYS["c1"], metrics, got, assetdata.load(SYMBOL)).loc[kept["variant_id"]]
    assert np.allclose(gross["g_is"] - gross["e_is"], COST * 500 / years_in)
    assert c1["rho"] == pytest.approx(flip.spearman(gross["g_is"].to_numpy(), gross["g_oos"].to_numpy()))
    assert c1["nivel_top"] == pytest.approx(np.median(kept.loc[kept["top"], "e_oos"]))
    assert "nivel_top_deriva_previa" in c3 and "nivel_top_deriva_previa" not in c2
    years = batch.years(assetdata.load(SYMBOL), ("oos2",))
    assert c1["nivel_top_deriva_previa"] == pytest.approx(c1["nivel_top"] - 5.0 / years)
    assert rows["c1.estado"] == 1.0 and rows["c1.orden"] == 1.0 and rows["c1.fuerte"] == 1.0
    assert rows["c1.rho"] == pytest.approx(c1["rho"]) and 0 < rows["c1.p_mas"] <= 0.05
    assert found["verdict"]["label"] == "PASA" and found["verdict"]["score"].startswith("ρ 0,")
    assert found["summary"]["estado"] == "pasa" and "%" not in json.dumps(found["verdict"])
    blocks = found["tabs"][0]["blocks"]
    assert [b["kind"] for b in blocks] == ["table", "scatter", "scatter", "scatter", "table", "table"]
    assert blocks[1]["quadrants"] and blocks[1]["fit"]["r"] == pytest.approx(c1["rho"], abs=1e-5)


def test_no_data_is_limbo_and_the_years_are_the_engines() -> None:
    """Under 30 variants, or a mother idle outside: LIMBO with no number; years as per_year counts them."""
    metrics, got = synthetic(n=20)
    real = gate.CALIBRATION
    with tempfile.TemporaryDirectory() as tmp:
        try:
            unsealed(Path(tmp))
            few = one.run(metrics, got, SYMBOL, CFG)
            big, more = synthetic()
            big.loc[0, "NumberOfTrades (oos2)"] = 0
            idle = one.run(big, more, SYMBOL, CFG)
        finally:
            gate.CALIBRATION = real
    for measured, why in ((few, "menos de 30"), (idle, "la madre")):
        c1 = measured["c1"]["facts"]
        assert c1["estado"] == "limbo" and c1["orden"] == "sin_dato" and "rho" not in c1
        assert why in measured["c1"]["notes"][-1]
        assert report.result("M", measured, CFG, 0.0)["verdict"]["state"] == "watch"
    assert idle["c2"]["facts"]["orden"] == "positivo"             # she trades in oos1+oos2
    asset = assetdata.load(SYMBOL)
    one_unit = pd.DataFrame({"variant_id": ["a"], "excess": [1.0]})
    for legs in (("build",), ("build", "oos1"), ("oos1", "oos2"), ("oos2",)):
        per = excess.per_year(one_unit, batch.window(asset, legs)).iloc[0]
        assert per == pytest.approx(1.0 / batch.years(asset, legs))
    line = {"gross": np.arange(40.0), "net": np.arange(40.0)}
    weeks = np.eye(40) * np.arange(40.0)
    assert reading.measure(line, line, {"gross": weeks, "net": weeks}, 1.0,
                           CFG)["rho"] == pytest.approx(1.0)


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
