#!/usr/bin/env python3
"""The funded verdict end to end (F4, Q11 d): oos1 alone, then oos2 once, a ledger row per segment opened."""

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# first: test_portfolio_stageb plants the data root, which must precede every project import
from test_portfolio_stageb import BUILD, complete, small_cfg  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import ledger.study as study  # noqa: E402
from ledger import record as ledger_record  # noqa: E402
from portfolio.common.construct import funded, funded_b  # noqa: E402
from test_portfolio_mc_paths import bar_world, lenient_plan  # noqa: E402


def test_verdict_end_to_end() -> None:
    """A synthetic pool through `funded_b.build`: oos1 alone, then oos2 once, a ledger row per segment opened."""
    cfg = small_cfg()
    cfg["verdict"]["pass_percentile"] = (
        None  # the criterion left unset: the verdict says so
    )
    plan = lenient_plan(target=0.04, max_loss=0.10, phases=2, daily_loss=0.05)
    calendar = {
        "build": BUILD,
        "oos1": (pd.Timestamp("2022-01-01"), pd.Timestamp("2022-06-30")),
        "oos2": (pd.Timestamp("2022-07-01"), pd.Timestamp("2022-12-31")),
    }
    world = complete(
        bar_world(51, 5, "2021-01-04", "2023-01-01", edge=6.0), plan, cfg, calendar
    )
    world["pool"] = {"hash": "feedface" * 8}
    pool_study = "PORTFOLIO_feedfacefeed_construct"
    bar = small_cfg()
    bar["verdict"]["pass_percentile"] = 0.0  # a TEST value: every winner passes oos1
    real_path = study.path
    with tempfile.TemporaryDirectory() as tmp:
        study.path = lambda s: Path(tmp) / "ledger" / f"{s}.jsonl"
        try:
            result = funded_b.build(world, cfg, np.random.default_rng(3))
            v = result["verdict"]
            no_sigma = funded_b.build(world, bar, np.random.default_rng(3))["verdict"]
            ledger_record.log(
                pool_study,
                {
                    "step": 27,
                    "launched_by": "real",
                    "segment": "build",
                    "n_in": 5,
                    "n_out": 2,
                    "criterion": "portfolio/ranks4/exhaustive",
                    "symbol": "TESTSYM",
                    "timeframe": "mixed",
                },
                np.random.default_rng(0).normal(0, 0.02, 50),
            )
            read = funded_b.build(world, bar, np.random.default_rng(3))["verdict"]
            again = funded_b.build(world, bar, np.random.default_rng(4))["verdict"]
            rows = study.read(pool_study)
            (Path(tmp) / "manifest.json").write_text("{}")
            funded_b.write(Path(tmp), result, {"root_seed": 3})
            blob = json.loads((Path(tmp) / "verdict.json").read_text())
        finally:
            study.path = real_path
    assert result["segments"] == ["oos1", "oos2"] and v["pass"] is None
    assert (
        v["label"] == "SIN CRITERIO (falta verdict.pass_percentile)"
        and v["oos2"]["state"] == "not_opened"
    )
    assert (
        set(v["oos1"]["measures"]) == {"start_p", "mc_p"} and len(result["nulls"]) == 3
    )
    for m in v["oos1"]["measures"].values():
        assert 0.0 <= m["percentile"] <= 1.0 and m["n"] == 3
    assert v["cost"] == {
        "n_pool": 5,
        "n_stage_a": 20,
        "n_shortlist": len(result["stage_b"]["table"]),
        "n_settings": 9,
        "null_draws": 3,
        "null_candidates": 20,
        "segments": ["oos1"],
    }
    assert v["chosen"]["members"] == result["stage_b"]["winner"]["members"].split("+")
    assert (
        len(v["hold"]["short"]) == v["hold"]["n_pairs"]
    )  # 6 months of judging: under the minimum
    assert result["judged"]["n_starts"] > 50
    assert (
        funded_b.summarise(world, result)
        .splitlines()[-1]
        .startswith("Veredicto: SIN CRITERIO (falta")
    )
    assert no_sigma["oos2"]["state"] == "no_sigma" and no_sigma["pass"] is None
    assert read["oos2"]["state"] in ("pass", "fail") and read["pass"] is (
        read["oos2"]["state"] == "pass"
    )
    assert (
        read["oos2"]["n"] == 50
        and not read["oos2"]["stored"]
        and read["cost"]["segments"] == ["oos1", "oos2"]
    )
    same = again["chosen"]["members"] == read["chosen"]["members"]
    assert again["oos2"].get("stored") if same else again["oos2"]["state"] == "refused"
    looks = rows[rows["criterion"] == f"portfolio/funded_verdict/{plan['plan_key']}"]
    assert looks["segment"].tolist() == [
        "oos1",
        "oos1",
        "oos1",
        "oos2",
        "oos1",
    ]  # oos2: one row, ever
    assert "sin_criterio" in looks["note"].iloc[0] and (looks["n_in"] == 1).all()
    assert blob["verdict"]["pass"] is None and len(blob["nulls"]) == 3

    no_oos1 = dict(world, calendar={"build": BUILD})
    refused = funded_b.build(no_oos1, cfg, np.random.default_rng(3))
    assert refused["verdict"] is None and "oos1" in refused["reason"]


def test_a_rerun_keeps_the_earlier_stage_b() -> None:
    """OPEN #104-4: the second stage B of a run goes to a new run folder; the first is left as it was."""
    with tempfile.TemporaryDirectory() as tmp:
        kept, funded.RUNS = funded.RUNS, Path(tmp)
        try:
            run = Path(tmp) / "2026-01-01T0000_Test_p_firm_plan"
            run.mkdir()
            (run / "manifest.json").write_text(
                json.dumps({"pool": "Test_p", "plan": "firm:plan"})
            )
            (run / "search.parquet").write_bytes(b"stage A")
            assert funded_b.target(run) == run, (
                "the first stage B writes in the stage-A run's folder"
            )
            (run / "stageb.parquet").write_bytes(b"first")
            (run / "verdict.json").write_text('{"winner": "first"}')
            second, third = funded_b.target(run), funded_b.target(run)
            assert len({run, second, third}) == 3, "each rerun gets a folder of its own"
            assert (run / "stageb.parquet").read_bytes() == b"first" and "first" in (
                run / "verdict.json"
            ).read_text()
            assert (second / "search.parquet").read_bytes() == b"stage A"
            assert (
                not (second / "stageb.parquet").exists()
                and not (second / "verdict.json").exists()
            )
            assert (
                json.loads((second / "manifest.json").read_text())["stage_a_run"]
                == run.name
            )
        finally:
            funded.RUNS = kept


def test_sizing_reads_the_pool_frozen_version() -> None:
    """OPEN #104-1: a member archived again after the pool froze it is sized off the frozen version."""
    seen = []
    real = (funded.archive_read.versions, funded.risk.sizing)
    funded.archive_read.versions = lambda identity: ["v1", "v2"]
    funded.risk.sizing = lambda identity, version: seen.append(version) or {"factor": 1}
    try:
        funded.size_members(["A"], {"A": "v1"})
        funded.size_members(["B"])
        try:
            funded.size_members(["A", "B"], {"A": "v1"})
            raise AssertionError(
                "a pool that lacks the member must not fall back to latest"
            )
        except KeyError:
            pass
    finally:
        funded.archive_read.versions, funded.risk.sizing = real
    assert seen == ["v1", "v2", "v1"], seen


def test_a_pool_with_one_identity_at_two_versions_is_refused() -> None:
    """OPEN #104-1: two versions of one identity have no single frozen one."""
    real = funded.pool_mod.declared
    funded.pool_mod.declared = lambda name, cfg: {
        "members": [
            {"identity": "A", "version": "v1"},
            {"identity": "A", "version": "v2"},
        ]
    }
    try:
        funded.frozen_versions("Test_p", {})
        raise AssertionError("expected ValueError")
    except ValueError as exc:
        assert "dos versiones" in str(exc)
    finally:
        funded.pool_mod.declared = real


def test_stage_b_seed_lands_in_the_manifest() -> None:
    """OPEN #104-3: the stage-B seed is written into the run's manifest.json."""
    with tempfile.TemporaryDirectory() as tmp:
        run = Path(tmp)
        (run / "manifest.json").write_text(json.dumps({"pool": "Test_p"}))
        empty = pd.DataFrame({"x": [1]})
        result = {
            "stage_b": {"table": empty, "rows": empty, "winner": None},
            "stability": None,
            "segments": None,
            "verdict": None,
            "nulls": None,
        }
        funded_b.write(run, result, {"root_seed": 7})
        assert json.loads((run / "manifest.json").read_text())["stage_b_seed"] == 7


if __name__ == "__main__":
    test_sizing_reads_the_pool_frozen_version()
    test_a_pool_with_one_identity_at_two_versions_is_refused()
    test_stage_b_seed_lands_in_the_manifest()
    test_a_rerun_keeps_the_earlier_stage_b()
    test_verdict_end_to_end()
    print("test_portfolio_verdict_funded: ok")
