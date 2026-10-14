"""Encargo 66 §1.5 and §4.1: one root per monkey run, saved; `--only` merges under it."""

import json
import sys
from collections.abc import Callable
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.study import draws
from studies.readings.monkey import report
from ui.daemon import runs
from ui.daemon.runner import readings, rootseed

NAMES = list("ABCDEF")


def _ctx(tmp: Path, frames: list[str] | None = None) -> dict:
    """A databank context whose export manifest declares `frames` (H1 when None)."""
    day = tmp / "raw"
    day.mkdir(exist_ok=True)
    (day / "manifest.json").write_text(
        json.dumps({"source": {"timeframes": frames if frames is not None else ["H1"]}})
    )
    return {
        "export": "d",
        "trades": str(day / "t.csv"),
        "project": "Test_X",
        "databank": "D",
        "feed": "F_M1",
        "multimarket": False,
        "strategy": "A",
    }


def test_launchers_share_one_root_and_reuse_the_saved_one(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Every subprocess of a run gets the same --seed; a second launch reads the manifest's."""
    monkeypatch.setattr(
        rootseed, "report_dir", lambda p, d, day: tmp_path / "proj" / "D" / "day"
    )
    c = _ctx(tmp_path)
    seeds = {readings.monkey(c, s)[-1] if s else None for s in NAMES}  # --strategy last
    argvs = [readings.monkey(c, s) for s in NAMES]
    got = {a[a.index("--seed") + 1] for a in argvs}
    assert len(got) == 1 and all("--timeframe" in a for a in argvs) and seeds
    one = runs.nulls(c)
    assert (
        one[one.index("--seed") + 1] in got
        and one[one.index("--timeframe") + 1] == "H1"
    )
    out = tmp_path / "proj" / "D" / "day" / "monkey"
    out.mkdir(parents=True)
    next(tmp_path.glob("proj/.seed-*")).unlink()
    (out / "manifest.json").write_text(json.dumps({"source": {"seed": 4242}}))
    assert rootseed.root("Test_X", "D") == 4242  # the manifest wins once a run wrote it


def test_nulls_without_timeframe_fails_loudly(tmp_path: Path) -> None:
    """No single timeframe: the sentence for the window, never the report's M30 default."""
    assert runs.nulls(_ctx(tmp_path, [])) == runs.NO_TF


@pytest.fixture
def harness(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """report.main over a fake export whose p-values are a function of (root, strategy)."""
    out = tmp_path / "rep"
    monkeypatch.setattr(report, "report_dir", lambda *a: out)
    monkeypatch.setattr(
        report.inputs, "newest", lambda p, d: tmp_path / "x" / "t.parquet"
    )
    monkeypatch.setattr(report.inputs, "markets", lambda p: ["F_M1"])
    monkeypatch.setattr(report.inputs, "bars", lambda f, t: None)
    monkeypatch.setattr(
        report.inputs,
        "trades",
        lambda *a: pd.DataFrame(
            {"strategy": [n for n in NAMES for _ in range(2)], "x": 1.0}
        ),
    )
    monkeypatch.setattr(
        report.output, "identify", lambda folder, names: {n: f"id{n}" for n in names}
    )
    monkeypatch.setattr(
        report.output,
        "population",
        lambda folder, name, res, title: (
            folder.mkdir(parents=True, exist_ok=True),
            (folder / "monkey.json").write_text(
                json.dumps(
                    {
                        k: v
                        for k, v in res.items()
                        if k not in ("computed_at", "wall_s")
                    },
                    default=str,
                )
            ),
        ),
    )
    monkeypatch.setattr(
        report,
        "write_manifest",
        lambda out_, src, cmd, counts: (
            out_.mkdir(parents=True, exist_ok=True),
            (out_ / "manifest.json").write_text(json.dumps({"source": src})),
        ),
    )

    def many(sample: dict, frames: dict, cfg: dict, workers: int) -> dict:
        """A stand-in for many.run: p-values that are a pure function of (root, strategy)."""
        names = sorted({k[0] for k in sample})
        seed = cfg["nulls"]["seed"]
        p = [float(np.random.default_rng([seed, ord(n)]).random()) for n in names]
        panel = pd.DataFrame(
            {"strategy": names, "market": "F_M1", "n": 2, "p_a_x": p}
        ).set_index("strategy")
        rows = [
            draws.record("monkey", "p", 0.0, np.array([seed, ord(n)]), strategy=n)
            for n in names
        ]
        return {
            "population": report.many.population(panel, 1, cfg, 0.0),
            "panel": panel,
            "draws": rows,
        }

    monkeypatch.setattr(report.many, "run", many)

    def run(*args: str) -> Path:
        """Run report.main with these arguments; the monkey folder it wrote."""
        monkeypatch.setattr(
            sys, "argv", ["r", "--project", "Test_X", "--databank", "D", *args]
        )
        report.main()
        return out / "monkey"

    return run


def test_only_equals_full_and_keeps_the_root(harness: Callable, tmp_path: Path) -> None:
    """Half + --only of the other half == the full run, nulls and distributions, one seed."""
    full = harness("--seed", "7", "--limit", "0")
    a = pd.read_csv(full / "nulls.csv", index_col=0)
    da = (
        pd.read_parquet(full / draws.FILE)
        .sort_values("strategy")
        .reset_index(drop=True)
    )
    summary = (full / "monkey.json").read_text()
    (full / "monkey.json").unlink()
    (full / "nulls.csv").unlink()
    (full / draws.FILE).unlink()
    harness("--seed", "7", "--limit", "3")  # first three strategies
    rest = tmp_path / "rest.txt"
    rest.write_text("\n".join(NAMES[3:]))
    harness("--only", str(rest))  # no --seed: the saved root
    out = full
    b = pd.read_csv(out / "nulls.csv", index_col=0)
    db = (
        pd.read_parquet(out / draws.FILE).sort_values("strategy").reset_index(drop=True)
    )
    assert (
        out / "monkey.json"
    ).read_text() == summary  # all but computed_at and wall_s
    assert_frame_equal(a, b)
    assert_frame_equal(da, db)
    assert json.loads((out / "manifest.json").read_text())["source"]["seed"] == 7
    with pytest.raises(SystemExit):
        harness("--only", str(rest), "--seed", "8")


def test_only_without_a_previous_run_refuses(harness: Callable, tmp_path: Path) -> None:
    """No manifest to merge into: a clear refusal, nothing written."""
    names = tmp_path / "n.txt"
    names.write_text("A")
    with pytest.raises(SystemExit):
        harness("--only", str(names))


def test_root_is_one_value_under_a_race_and_planning_makes_no_result_folder(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Sixteen threads at once read one root; no `monkey/` folder (a result day) is created."""
    from concurrent.futures import ThreadPoolExecutor

    monkeypatch.setattr(
        rootseed, "report_dir", lambda p, d, day: tmp_path / "proj" / "D" / day
    )
    with ThreadPoolExecutor(16) as pool:
        got = list(pool.map(lambda _: rootseed.root("Test_X", "D"), range(64)))
    assert len(set(got)) == 1
    assert [p.name for p in (tmp_path / "proj").iterdir() if p.is_dir()] == []
    assert len(list((tmp_path / "proj").glob(".seed*"))) == 1  # the temp files are gone


@pytest.mark.parametrize(
    "extra,field",
    [(["--set", "nulls.draws=7"], "draws"), (["--timeframe", "H1"], "timeframe")],
)
def test_only_refuses_a_run_computed_differently(
    harness: Callable, tmp_path: Path, extra: list[str], field: str
) -> None:
    """Draws, timeframe: the real config loader sees a different value than the manifest's and refuses."""
    full = harness("--seed", "7")
    before = (full / "nulls.csv").read_text()
    names = tmp_path / "n.txt"
    names.write_text("A")
    with pytest.raises(SystemExit, match=field):
        harness("--only", str(names), *extra)
    assert (full / "nulls.csv").read_text() == before


def test_only_refuses_another_export(
    harness: Callable, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A newer export (another input file) never merges into the older run's nulls.csv."""
    harness("--seed", "7")
    monkeypatch.setattr(
        report.inputs, "newest", lambda p, d: tmp_path / "y" / "t.parquet"
    )
    names = tmp_path / "n.txt"
    names.write_text("A")
    with pytest.raises(SystemExit, match="input"):
        harness("--only", str(names))
