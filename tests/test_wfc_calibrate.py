#!/usr/bin/env python3
"""The calibration of step 17 against known answers: with no edge the criterion passes
about alpha of the families and the one without a null on the level half of them, a large planted edge passes both,
a cost lowers the false PASA; the register opens only under its caps and the seal obeys it; the
rehearsal reads build and oos1 of the batches that hold every variant's trades, and nothing else."""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_wfc_batch import SYMBOL, synthetic

from ledger import gate
from studies.optimisation.wfc.calibrate import families, page, rates, record, rehearsal
from studies.optimisation.wfc.calibrate.__main__ import load
from studies.optimisation.wfc.inputs import config
from engines.weekly import flip
from studies.optimisation.wfc.measure import level, reading

WFC = config.load(["null.draws=300"])
CFG = load(["families=200", "family.variants=60", "family.years_in=6.0", "grid.years_out=[2.0]",
            "grid.edges=[0.5, 3.0]", "grid.costs=[-1.5]", "reference.years_out=2.0",
            "sensitivity.own_noise=[]"])


def test_the_level_is_judged_with_the_very_draws_of_the_order() -> None:
    """flips() rebuilds the sign draws of `measure`: the rho's tail comes out identical."""
    e_is, e_oos, weeks = families.family(0.0, 0.0, 1, 40, 100, 60, np.random.default_rng(1))
    assert weeks.shape == (60, 40) and np.allclose(weeks.sum(axis=0) / (60 / families.YEAR), e_oos)
    found = reading.measure(*(rates.both(part) for part in (e_is, e_oos, weeks)), 1.2, WFC)
    flat = rates.flips(weeks, 1.2, WFC)
    assert flip.tails(found["rho"], flip.spearman(e_is, flat))["p_mas"] == found["p_mas"]
    assert 0 < found["p_nivel"] <= 1
    tops = np.median(flat[:, level.top(e_is, WFC["level"]["top_share"])], axis=1)
    assert found["p_nivel"] == (1 + (tops >= found["nivel_top"]).sum()) / (1 + len(tops))


def test_the_sharpe_planted_is_the_sharpe_measured() -> None:
    """weekly() turns an annualised Sharpe into the mean the average variant needs."""
    _, _, weeks = families.family(families.weekly(2.0, 0.4), 0.0, 1, 400, 10, 20000,
                                  np.random.default_rng(2), 0.4)
    sharpe = weeks.mean() / np.sqrt(weeks.var(axis=0).mean()) * np.sqrt(families.YEAR)
    assert sharpe == pytest.approx(2.0, abs=0.2)       # one 385-year path of the common factor


def test_each_family_lands_where_it_was_planted() -> None:
    """No edge: the criterion passes ~alpha and the one without a null on the level ~0.475; a cost lowers it; a large edge passes both."""
    table = rates.table(families.specs(CFG), CFG, WFC, 8).set_index(["tipo", "sharpe"])
    n, alpha = CFG["families"], WFC["null"]["alpha"]
    none = table.loc[(families.NONE, 0.0)]
    assert abs(none["pasa_sin"] - 0.5 * (1 - alpha)) <= 3 * np.sqrt(0.25 / n), none
    assert none["pasa"] <= alpha + 3 * np.sqrt(alpha * (1 - alpha) / n), none
    assert none["no_pasa"] == none["no_pasa_sin"]            # the null moves PASA to LIMBO only
    assert none[list(rates.CELLS)].sum() == pytest.approx(1.0)
    assert none[list(rates.STATES)].sum() == pytest.approx(1.0)
    assert table.loc[(families.NONE, -1.5), "pasa_sin"] <= 0.1
    for kind in (families.FLAT, families.ORDER):
        assert table.loc[(kind, 3.0), ["pasa", "pasa_sin"]].min() >= 0.9, table
        assert table.loc[(kind, 0.5), "pasa"] < table.loc[(kind, 0.5), "pasa_sin"]
    assert table.loc[(families.ORDER, 3.0), "positivo/gana"] >= 0.9


def scored(false: float, failed: float) -> pd.DataFrame:
    """A table of rates with the reference cells (and a cell at another length) and nothing else."""
    def row(kind: str, sharpe: float, years: float, pasa: float, no_pasa: float) -> dict:
        """One scenario's rates; the ones without a null on the level are fixed at 0.5 and 0.1."""
        return {"bloque": "rejilla", "tipo": kind, "sharpe": sharpe, "anos_fuera": years,
                "pasa": pasa, "no_pasa": no_pasa, "pasa_sin": 0.5, "no_pasa_sin": 0.1}
    return pd.DataFrame([row(families.NONE, 0.0, 2.0, false, 0.0),
                         row(families.FLAT, 0.5, 2.0, 0.2, 0.01),
                         row(families.ORDER, 0.5, 2.0, 0.2, failed),
                         row(families.NONE, 0.0, 9.0, 1.0, 0.0)])


def test_the_register_opens_only_under_both_caps_and_the_seal_obeys(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """abre is the criterion against its caps; `gate.seal` reads exactly this file."""
    assert record.decide(scored(0.39, 0.25), CFG)["abre"]
    sick = record.decide(scored(0.47, 0.10), CFG)
    assert "falso PASA" in sick["motivo"] and "0,47" in sick["motivo"] and "." not in sick["motivo"]
    late = record.decide(scored(0.10, 0.30), CFG)
    assert not late["abre"] and late["falso_no_pasa"] == pytest.approx(0.30)   # the worse kind
    assert late["falso_pasa_sin"] == 0.5 and late["falso_no_pasa_sin"] == 0.1
    monkeypatch.setattr(gate, "CALIBRATION", tmp_path / "wfc_calibration.json")
    empty = {"lotes": [], "tasas": None}
    for false, opens in ((0.47, False), (0.30, True)):
        table = scored(false, 0.10)
        register = record.build(record.decide(table, CFG), table, empty, CFG, WFC)
        record.write(gate.CALIBRATION, register)
        assert json.loads(gate.CALIBRATION.read_text())["abre"] is opens
        assert {"fecha", "criteria_sha256", "abre", "tasas"} <= set(register)
        if opens:
            gate.seal(17, "oos2", SYMBOL)
        else:
            with pytest.raises(PermissionError, match="abre: false"):
                gate.seal(17, "oos2", SYMBOL)


def test_the_rehearsal_reads_build_and_oos1_of_the_batches_with_trades(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """No batch: «0 lotes». One with trades: measured build -> oos1, no column of oos2 opened."""
    assert rehearsal.run(tmp_path, WFC) == {"lotes": [], "tasas": None}
    assert page.rehearsal({"lotes": [], "tasas": None}).startswith("0 lotes")
    metrics, got = synthetic()
    for name, trades in (("Strategy_1.2.3", True), ("Strategy_4.5.6", False)):
        work = tmp_path / "Test_X" / name
        work.mkdir(parents=True)
        metrics.to_parquet(work / "metrics.parquet")
        if trades:
            (work / "variant_trades.parquet").touch()
    asked = []

    def read(work: Path, symbol: str, timeframe: str, legs: tuple) -> dict:
        """What `batch.read` would return for the two spent legs."""
        asked.append(legs)
        return {"per": {leg: got["per"][leg] for leg in legs}, "prints": got["prints"]}

    monkeypatch.setattr(rehearsal.look, "market", lambda work: (SYMBOL, "M30"))
    monkeypatch.setattr(rehearsal.batch, "read", read)
    monkeypatch.setattr(gate, "CALIBRATION", tmp_path / "none.json")     # no register is needed
    seen = rehearsal.metrics(tmp_path / "Test_X" / "Strategy_1.2.3")
    assert not [c for c in seen if "oos2" in c] and "NetProfit (oos1)" in seen
    found = rehearsal.run(tmp_path, WFC)
    assert asked == [("build", "oos1")] and len(found["lotes"]) == 1
    row = found["lotes"][0]
    assert row["lote"] == "Test_X/Strategy_1.2.3" and row["casilla"] == "positivo/gana"
    assert row["estado"] == "pasa" and row["estado_sin"] == "pasa" and row["p_nivel"] <= 0.05
    assert 0 < row["sd_rho_nulo"] < 1
    assert found["tasas"]["pasa"] == 1.0 and found["tasas"]["familias"] == 1
    assert "1 lotes" in page.rehearsal(found) and "Test_X/Strategy_1.2.3" in page.rehearsal(found)


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
