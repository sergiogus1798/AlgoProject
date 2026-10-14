#!/usr/bin/env python3
"""The autopilot's facts: every number a step-8 study writes per strategy reaches a key a
criteria.yaml rule can name, joined by identity."""

import sys
import tempfile
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.autopilot import facts, run
from studies.readings.entryQuality import contract


def keyed(rows: list[dict]) -> dict[tuple[str, str], float]:
    """(strategy, key) -> value, the not-numbers dropped as `gather` drops them."""
    return {
        (r["strategy"], r["key"]): r["value"] for r in rows if r["value"] is not None
    }


def test_folder_reads_every_per_strategy_number() -> None:
    """A scorecard indexed by identity with object-dtype pass flags, a verdict.csv with numbers,
    True/False and words, a one-market nulls.csv and a two-market one."""
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        pd.DataFrame(
            {
                "strategy": ["A", "B", None, None],
                "cayo_nivel": [None, "1a", "0", "0"],
                "sanidad_passed": [True, False, None, None],
                "drift_excess_t": [2.5, 1.0, None, None],
                "survives": [True, False] * 2,
            },
            index=pd.Index(["ia", "ib", "ic", "id"], name="identity"),
        ).to_parquet(out / "scorecard.parquet")
        pd.DataFrame(
            {
                "strategy": ["A", "B"],
                "identity": ["ia", "ib"],
                "verdict": ["MANTENER", "DESCARTAR"],
                "verdict_state": ["pass", "fail"],
                "neto con slippage real [OOS]": [12.5, -3.0],
                "broken": ["", "OOS"],
                "superior": ["True", "False"],
                "p": ["", "0.004"],
            }
        ).to_csv(out / "verdict.csv", index=False)
        pd.DataFrame(
            {
                "strategy": ["A", "B"],
                "identity": ["ia", "ib"],
                "market": ["X", "X"],
                "p_timing_sharpe": [0.01, 0.6],
            }
        ).to_csv(out / "nulls.csv", index=False)
        rows = facts.from_folder("s", out)
        got = keyed(rows)
        assert got[("A", "scorecard.sanidad_passed")] == 1.0
        assert got[("B", "scorecard.sanidad_passed")] == 0.0
        assert got[("A", "scorecard.drift_excess_t")] == 2.5
        assert ("B", "scorecard.drift_excess_t") in got
        assert {r["identity"] for r in rows if r["key"].startswith("scorecard.")} == {
            "ia",
            "ib",
        }
        assert got[("A", "verdict_csv.neto_con_slippage_real_oos")] == 12.5
        assert got[("A", "verdict_csv.superior")] == 1.0
        assert (
            got[("B", "verdict_csv.p")] == 0.004 and ("A", "verdict_csv.p") not in got
        )
        assert got[("A", "verdict_csv.state_pass")] == 1.0
        assert got[("B", "verdict_csv.state_pass")] == 0.0
        assert got[("B", "verdict_csv.drop")] == 1.0
        assert got[("A", "nulls_csv.p_timing_sharpe")] == 0.01
        assert not any(
            k[1].endswith((".broken", ".verdict", ".market", ".verdict_state"))
            for k in got
        )

        pd.DataFrame(
            {
                "strategy": ["A", "A"],
                "market": ["X", "Y"],
                "p_timing_sharpe": [0.01, 0.6],
            }
        ).to_csv(out / "nulls.csv", index=False)
        assert not any(
            k.startswith("nulls_csv") for _, k in keyed(facts.from_folder("s", out))
        )


def test_a_per_market_parquet_gives_one_key_per_market() -> None:
    """crossmarket's `markets.parquet` — one row per strategy and market — reaches a rule as
    `markets.<market>.<col>`; a table that repeats a (strategy, market) pair is still skipped."""
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        table = pd.DataFrame(
            {
                "strategy": ["A", "A", "B"],
                "identity": ["ia", "ia", "ib"],
                "market": ["EURUSD_M1", "UKOIL.cash_M1", "EURUSD_M1"],
                "category": ["family"] * 3,
                "z": [2.1, -0.4, 0.3],
            }
        )
        table.to_parquet(out / "markets.parquet")
        rows = facts.from_folder("crossmarket", out)
        got = keyed(rows)
        assert got[("A", "markets.eurusd_m1.z")] == 2.1
        assert got[("A", "markets.ukoil_cash_m1.z")] == -0.4
        assert got[("B", "markets.eurusd_m1.z")] == 0.3
        assert ("B", "markets.ukoil_cash_m1.z") not in got
        assert {r["identity"] for r in rows} == {"ia", "ib"}
        assert not any("category" in k or k.endswith(".market") for _, k in got)
        pd.concat([table, table]).to_parquet(out / "markets.parquet")
        assert facts.from_folder("crossmarket", out) == []


def test_reading_and_delay_rows_are_addressable() -> None:
    """A reading (a verdict block in a tab) gives `<tab>.verdict_pass`; entryQuality's delay
    table keeps `d` as its first cell, so the 1-bar row has one key on any timeframe."""
    table = pd.DataFrame(
        {
            "d": [1, 2],
            "entregado": [5.0, 9.0],
            "esperanza_neta": [40.0, 36.0],
            "DCR": [0.1, 0.2],
            "veces_el_coste": [0.3, 0.5],
        }
    ).set_index("d")
    tab = contract.delay_tab(
        {"on_tf": table, "on_m1": table},
        {"run": {"timeframe": "H4"}, "verdict": {"dcr_high": 0.3}},
    )
    got = dict(facts.flatten({"tabs": [tab]}))
    assert got["delay.verdict_pass"] is True
    assert got["delay.en_barras_de_la_estrategia.1.dcr"] == 0.1
    assert got["delay.en_minutos.2.entregado"] == 9.0


def test_after_cut_keeps_a_judged_reading_before_the_judge() -> None:
    """entryQuality runs before step 8's judge when a rule names it; the monkey after the cut,
    on whoever is left."""
    actions = [
        {
            "n": "8",
            "kind": "python",
            "title": "t",
            "tests": ["gate", "monkey", "entryQuality"],
        },
        {"n": "8", "kind": "judge"},
    ]
    cfg = {
        "steps": {
            "8": {
                "rules": [
                    {"fact": "entryQuality.concentration.verdict_pass", "pass": ">= 1"}
                ]
            }
        }
    }
    got = run.after_cut(actions, cfg)
    assert got[0]["tests"] == ["gate", "entryQuality"]
    assert got[1]["kind"] == "judge" and got[2]["tests"] == ["monkey"]
    assert got[2]["cut"]
    plain = run.after_cut(actions, {"steps": {"8": {"rules": []}}})
    assert plain[2]["tests"] == ["monkey", "entryQuality"]
    # monkeyExcess reads the panel monkey writes: it never stays behind, before the cut — and it
    # is not run after it either, where the monkey of a picked list writes no panel
    both = [{**actions[0], "tests": ["gate", "monkeyExcess", "monkey"]}, actions[1]]
    got = run.after_cut(both, {"steps": {"8": {"rules": []}}})
    assert got[0]["tests"] == ["gate"] and got[2]["tests"] == ["monkey"]


if __name__ == "__main__":
    test_folder_reads_every_per_strategy_number()
    test_a_per_market_parquet_gives_one_key_per_market()
    test_reading_and_delay_rows_are_addressable()
    test_after_cut_keeps_a_judged_reading_before_the_judge()
    print("ok")
