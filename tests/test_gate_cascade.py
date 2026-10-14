#!/usr/bin/env python3
"""The gate's cascade over its levels: a strategy leaves at its first Fail and gets nothing of
the levels after it, the cascade switched off computes everything and gives the same verdict,
the funnel counts per level and rule, and a run resumes at a level."""

import sys
from pathlib import Path
from types import SimpleNamespace

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.autopilot import criteria, facts
from studies.screening.gate import cascade, one

P = cascade.PREFIX
A = {"x": 1.0, "y": 0.0, "z": 1.0}        # level "0": y fails
B = {"x": 2.0, "y": 2.0, "z": 0.5}        # level "1a": z is limbo; y would pass
RULES = [{"fact": P + "a", "pass": ">= 1", "missing": "fail"},
         {"fact": P + "b", "pass": ">= 1", "limbo": ">= 0", "missing": "fail"},
         {"fact": "otro.estudio", "pass": ">= 1"}]
SEEN = []                                  # who each run of level "1a" was handed


def fake(monkeypatch: object, b: dict = B) -> None:
    """Two levels in place of the real eight: `a` from A, `b` from `b`."""
    def second(data: dict, alive: pd.Index, cfg: dict) -> pd.DataFrame:
        """Level "1a": fact `b`, and a note of who it was handed."""
        SEEN.append(sorted(alive))
        return pd.DataFrame({"b": [b[i] for i in alive]}, index=alive)

    first = SimpleNamespace(FACTS=("a",), run=lambda data, alive, cfg: pd.DataFrame(
        {"a": [A[i] for i in alive]}, index=alive))
    levels = (("0", first), ("1a", SimpleNamespace(FACTS=("b",), run=second)))
    monkeypatch.setattr(cascade, "LEVELS", levels)
    monkeypatch.setattr(one, "LEVELS", levels)


def harvest(out: Path) -> dict:
    """Three paired strategies and nobody missing."""
    return {"metrics": pd.DataFrame({"strategy": ["X", "Y", "Z"], "strategy_build": ["X", "Y", "Z"]},
                                    index=pd.Index(["x", "y", "z"], name="identity")),
            "missing": pd.DataFrame(columns=["identity", "strategy_build"]), "out": out}


def judged(scores: pd.DataFrame) -> dict[str, str]:
    """The judge's own verdict from the scorecard's facts, every rule read."""
    long = (scores[["a", "b"]].astype(float).add_prefix(P).rename_axis("who").reset_index()
            .melt("who", var_name="key").dropna())
    return {w: s for w, (s, _) in criteria.outcomes(long, list(scores.index), RULES[:2]).items()}


def test_a_fall_stops_the_levels_after_it(monkeypatch: object, tmp_path: Path) -> None:
    """y falls at level 0: level 1a never sees it, its `b` is empty, its reason is the one rule
    it failed; z stands in limbo; the rule on another study's fact is not the cascade's."""
    fake(monkeypatch)
    SEEN.clear()
    scores, funnel = cascade.run(harvest(tmp_path), {"cascade": {"on": True}}, RULES, say=False)
    assert SEEN == [["x", "z"]] and pd.isna(scores.loc["y", "b"])
    assert scores.loc["y", ["cayo_nivel", "cayo_regla"]].tolist() == ["0", P + "a=0.0"]
    assert scores["survives"].tolist() == [True, False, True]
    assert scores["limbo"].tolist()[0] == "" and scores.loc["z", "limbo"] == P + "b=0.5"
    assert funnel[["level", "entered", "passed", "limbo", "died"]].values.tolist() == [
        ["0", 3, 2, 0, 1], ["1a", 2, 2, 1, 0]]
    said = cascade.verdict(scores, "strategy").set_index("strategy")
    assert said["verdict"].tolist() == ["MANTENER", "DESCARTAR", "MANTENER"]
    assert said.loc["Y", "reason"] == f"nivel 0: {P}a=0.0"
    labels = [one.run(i, scores, {})["verdict"]["label"] for i in scores.index]
    assert labels == ["MANTENER", "DESCARTAR", "LIMBO"]
    scores.to_parquet(tmp_path / "scorecard.parquet")
    got = {(r["strategy"], r["key"]): r["value"] for r in facts.from_folder("gate", tmp_path)
           if r["value"] is not None}
    assert got[("Y", "scorecard.survives")] == 0.0 and got[("Y", "scorecard.a")] == 0.0
    assert ("Y", "scorecard.b") not in got and got[("Z", "scorecard.b")] == 0.5


def test_off_computes_everything_and_says_the_same(monkeypatch: object, tmp_path: Path) -> None:
    """With `cascade.on` false level 1a runs on all three, and verdict, level, rule and funnel
    are the ones the cascade gave — and both are what the judge reads from the facts."""
    fake(monkeypatch)
    on, f_on = cascade.run(harvest(tmp_path), {"cascade": {"on": True}}, RULES, say=False)
    SEEN.clear()
    off, f_off = cascade.run(harvest(tmp_path), {"cascade": {"on": False}}, RULES, say=False)
    assert SEEN == [["x", "y", "z"]] and off["b"].notna().all()
    same = ["cayo_nivel", "cayo_regla", "survives", "limbo"]
    assert on[same].fillna("").equals(off[same].fillna("")) and f_on.equals(f_off)
    assert judged(on) == judged(off) == {"x": "pass", "y": "fail", "z": "limbo"}


def test_a_run_resumes_at_a_level(monkeypatch: object, tmp_path: Path) -> None:
    """`start="1a"` keeps level 0 as the first run left it and judges level 1a again."""
    fake(monkeypatch)
    data, cfg = harvest(tmp_path), {"cascade": {"on": True}}
    first, _ = cascade.run(data, cfg, RULES, say=False)
    first.to_parquet(tmp_path / "scorecard.parquet")
    pd.DataFrame(columns=["identity"]).to_parquet(tmp_path / "operaciones.parquet")
    fake(monkeypatch, {"x": -1.0, "y": 2.0, "z": 2.0})
    SEEN.clear()
    again, funnel = cascade.run(data, cfg, RULES, start="1a", say=False)
    assert SEEN == [["x", "z"]] and again["a"].equals(first["a"])
    assert again["cayo_nivel"].tolist() == ["1a", "0", None] and again.loc["z", "limbo"] == ""
    assert funnel[["level", "died"]].values.tolist() == [["0", 1], ["1a", 1]]


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-q"]))
