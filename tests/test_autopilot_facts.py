#!/usr/bin/env python3
"""The autopilot's facts: every number a step-8 study writes per strategy reaches a key a
criteria.yaml rule can name, joined by identity, and the gate keeps every screen's numbers."""

import sys
import tempfile
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.autopilot import facts, run
from studies.readings.entryQuality import contract
from studies.screening.gate import cascade, one


def keyed(rows: list[dict]) -> dict[tuple[str, str], float]:
    """(strategy, key) -> value, the not-numbers dropped as `gather` drops them."""
    return {(r["strategy"], r["key"]): r["value"] for r in rows if r["value"] is not None}


def test_folder_reads_every_per_strategy_number() -> None:
    """A scorecard indexed by identity with object-dtype pass flags, a verdict.csv with numbers,
    True/False and words, a one-market nulls.csv and a two-market one."""
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        pd.DataFrame({"strategy": ["A", "B", None, None], "died_at": [None, "mono", "presencia",
                                                                     "presencia"],
                      "mono_passed": [True, False, None, None],
                      "degradacion_t": [2.5, 1.0, None, None], "survives": [True, False] * 2},
                     index=pd.Index(["ia", "ib", "ic", "id"], name="identity")
                     ).to_parquet(out / "scorecard.parquet")
        pd.DataFrame({"strategy": ["A", "B"], "identity": ["ia", "ib"],
                      "verdict": ["MANTENER", "DESCARTAR"], "verdict_state": ["pass", "fail"],
                      "neto con slippage real [OOS]": [12.5, -3.0], "broken": ["", "OOS"],
                      "superior": ["True", "False"], "p": ["", "0.004"]}
                     ).to_csv(out / "verdict.csv", index=False)
        pd.DataFrame({"strategy": ["A", "B"], "identity": ["ia", "ib"], "market": ["X", "X"],
                      "p_timing_sharpe": [0.01, 0.6]}).to_csv(out / "nulls.csv", index=False)
        rows = facts.from_folder("s", out)
        got = keyed(rows)
        assert got[("A", "scorecard.mono_passed")] == 1.0
        assert got[("B", "scorecard.mono_passed")] == 0.0
        assert got[("A", "scorecard.degradacion_t")] == 2.5
        assert ("B", "scorecard.degradacion_t") in got
        assert {r["identity"] for r in rows if r["key"].startswith("scorecard.")} == {"ia", "ib"}
        assert got[("A", "verdict_csv.neto_con_slippage_real_oos")] == 12.5
        assert got[("A", "verdict_csv.superior")] == 1.0
        assert got[("B", "verdict_csv.p")] == 0.004 and ("A", "verdict_csv.p") not in got
        assert got[("A", "verdict_csv.state_pass")] == 1.0
        assert got[("B", "verdict_csv.state_pass")] == 0.0
        assert got[("B", "verdict_csv.drop")] == 1.0
        assert got[("A", "nulls_csv.p_timing_sharpe")] == 0.01
        assert not any(k[1].endswith((".broken", ".verdict", ".market", ".verdict_state"))
                       for k in got)

        pd.DataFrame({"strategy": ["A", "A"], "market": ["X", "Y"],
                      "p_timing_sharpe": [0.01, 0.6]}).to_csv(out / "nulls.csv", index=False)
        assert not any(k.startswith("nulls_csv") for _, k in keyed(facts.from_folder("s", out)))


def test_reading_and_delay_rows_are_addressable() -> None:
    """A reading (a verdict block in a tab) gives `<tab>.verdict_pass`; entryQuality's delay
    table keeps `d` as its first cell, so the 1-bar row has one key on any timeframe."""
    table = pd.DataFrame({"d": [1, 2], "entregado": [5.0, 9.0], "esperanza_neta": [40.0, 36.0],
                          "DCR": [0.1, 0.2], "veces_el_coste": [0.3, 0.5]}).set_index("d")
    tab = contract.delay_tab({"on_tf": table, "on_m1": table},
                             {"run": {"timeframe": "H4"}, "verdict": {"dcr_high": 0.3}})
    got = dict(facts.flatten({"tabs": [tab]}))
    assert got["delay.verdict_pass"] is True
    assert got["delay.en_barras_de_la_estrategia.1.dcr"] == 0.1
    assert got["delay.en_minutos.2.entregado"] == 9.0


def test_cascade_keeps_every_column_a_screen_returns() -> None:
    """degradacion's t, years and concentration land in the scorecard as their own columns."""
    def first(data: dict, alive: pd.Index, cfg: dict) -> pd.DataFrame:
        """A screen with two extra numbers beside value, passed and note."""
        return pd.DataFrame({"value": 1.0, "passed": alive == "a", "note": "", "t": 2.0,
                             "years_positive": 3.0}, index=alive)

    cascade.SCREENS["fake"] = first
    data = {"metrics": pd.DataFrame({"strategy": ["A", "B"], "strategy_build": ["A", "B"]},
                                    index=pd.Index(["a", "b"], name="identity")),
            "missing": pd.DataFrame(columns=["identity", "strategy_build"])}
    scores, _ = cascade.run(data, {"screens": [{"name": "fake", "kind": "hard"}]}, say=False)
    assert list(scores["fake_t"]) == [2.0, 2.0] and list(scores["fake_years_positive"]) == [3.0] * 2
    assert list(scores["survives"]) == [True, False]
    del cascade.SCREENS["fake"]


def test_an_early_death_is_an_explicit_zero() -> None:
    """A strategy that dies at the first hard screen still has `<screen>_passed` = 0 for it,
    `survives` = 0 and `verdict.pass` = 0 — facts a rule can fail it on — and no fact at all
    for the screen it never reached (missing = limbo, owner 2026-10-01)."""
    def early(data: dict, alive: pd.Index, cfg: dict) -> pd.DataFrame:
        """Passes only `a`."""
        return pd.DataFrame({"value": 1.0, "passed": alive == "a", "note": ""}, index=alive)

    def late(data: dict, alive: pd.Index, cfg: dict) -> pd.DataFrame:
        """Passes whoever reaches it."""
        return pd.DataFrame({"value": 2.0, "passed": True, "note": ""}, index=alive)

    cascade.SCREENS.update(early=early, late=late)
    cfg = {"screens": [{"name": "early", "kind": "hard"}, {"name": "late", "kind": "hard"}]}
    data = {"metrics": pd.DataFrame({"strategy": ["A", "B"], "strategy_build": ["A", "B"]},
                                    index=pd.Index(["a", "b"], name="identity")),
            "missing": pd.DataFrame(columns=["identity", "strategy_build"])}
    scores, _ = cascade.run(data, cfg, say=False)
    with tempfile.TemporaryDirectory() as tmp:
        scores.to_parquet(Path(tmp) / "scorecard.parquet")
        got = keyed(facts.from_folder("gate", Path(tmp)))
    assert got[("B", "scorecard.early_passed")] == 0.0 and got[("B", "scorecard.survives")] == 0.0
    assert got[("A", "scorecard.late_passed")] == 1.0 and got[("A", "scorecard.survives")] == 1.0
    assert ("B", "scorecard.late_passed") not in got and ("B", "scorecard.late_value") not in got
    said = {n: dict(facts.flatten(one.run(i, scores, cfg))) for n, i in (("A", "a"), ("B", "b"))}
    assert said["A"]["verdict.pass"] is True and said["B"]["verdict.pass"] is False
    del cascade.SCREENS["early"], cascade.SCREENS["late"]


def test_after_cut_keeps_a_judged_reading_before_the_judge() -> None:
    """profitShape runs before step 8's judge when a rule names it; entryQuality still after."""
    actions = [{"n": "8", "kind": "python", "title": "t",
                "tests": ["gate", "monkey", "profitShape", "entryQuality"]},
               {"n": "8", "kind": "judge"}]
    cfg = {"steps": {"8": {"rules": [{"fact": "profitShape.concentration.verdict_pass",
                                      "pass": ">= 1"}]}}}
    got = run.after_cut(actions, cfg)
    assert got[0]["tests"] == ["gate", "monkey", "profitShape"]
    assert got[1]["kind"] == "judge" and got[2]["tests"] == ["entryQuality"] and got[2]["cut"]
    plain = run.after_cut(actions, {"steps": {"8": {"rules": []}}})
    assert plain[2]["tests"] == ["profitShape", "entryQuality"]


if __name__ == "__main__":
    test_folder_reads_every_per_strategy_number()
    test_reading_and_delay_rows_are_addressable()
    test_cascade_keeps_every_column_a_screen_returns()
    test_an_early_death_is_an_explicit_zero()
    test_after_cut_keeps_a_judged_reading_before_the_judge()
    print("ok")
