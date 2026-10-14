"""Encargo 66, piece B4: studies that ran in series inside their process, wide, with the same numbers.

Each test runs the study twice, once with `fanout.run` swapped for a plain loop and once
for real, and compares the results exactly (frame-equal, not approximate).
"""

import io
import sys
import tempfile
import threading
import time
from collections.abc import Callable, Iterator
from contextlib import redirect_stdout
from pathlib import Path
from typing import Any

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import fanout, paths
from core.study import result as envelope
from pipeline.autopilot import call, closing, survivors
from studies.closing.blindJoint import many as joint_many
from studies.closing.exposure import inputs as exp_inputs, many as exp_many, one as exp_one
from studies.data.spread import scan
from studies.screening.decay import report as decay_report
from studies.transfer.crossTF import cells
from tests import test_blindjoint as bj
from tests import test_crosstf_facts as cf
from tests import test_crosstf_tf_null as tf


def serial(work: Callable, costs: Any, workers: Any) -> Iterator:
    """`fanout.run` as a loop in this process: the oracle."""
    for key in costs:
        yield key, work(key)


@pytest.fixture
def both(monkeypatch: pytest.MonkeyPatch) -> Callable:
    """Call `fn()` serially and then wide; hand back both results."""
    def go(fn: Callable) -> tuple:
        """Run `fn` serially, then wide."""
        real = fanout.run
        monkeypatch.setattr(fanout, "run", serial)
        one = fn()
        monkeypatch.setattr(fanout, "run", real)
        return one, fn()
    return go


def test_crosstf_cells_and_no_raw_draws(both: Callable, monkeypatch: pytest.MonkeyPatch) -> None:
    """Wide and serial crossTF cells agree and carry no raw draws."""
    sink = []
    real = cells.panel
    monkeypatch.setattr(cells, "panel", lambda *a: real(*a, sink=sink))
    a, b = both(cf.panel)
    assert_frame_equal(a, b)
    half = len(sink) // 2
    assert half and all(r["draws"] is None or len(r["draws"]) == 0 for r in sink)
    assert [(r["metric"], r["observed"], r["n_ge"], r["mean"], r["sd"]) for r in sink[:half]] == \
           [(r["metric"], r["observed"], r["n_ge"], r["mean"], r["sd"]) for r in sink[half:]]
    assert all(len(r["counts"]) for r in sink)       # the histogram stays


def test_crosstf_tf_table_per_mother(both: Callable) -> None:
    """The per-mother sibling table is the same wide and serial."""
    frames = tf.noise()
    got = pd.concat([tf.family(i) for i in range(4)], ignore_index=True)
    a, b = both(lambda: tf.read(got, frames)["siblings"])
    assert_frame_equal(a, b)


def test_exposure_members(both: Callable, monkeypatch: pytest.MonkeyPatch) -> None:
    """Exposure members and table are the same wide and serial."""
    def fake(name: str, inp: Any, cfg: Any) -> dict:
        """A canned exposure result per strategy name."""
        return {"strategy": name, "identity": "i-" + name,
                "summary": {k: float(len(name)) for k in exp_many.SHOWN if k not in ("strategy", "notes")}
                | {"notes": ""}}
    monkeypatch.setattr(exp_one, "run", fake)
    monkeypatch.setattr(envelope, "progress", lambda *a, **k: None)
    inp = {"strategies": [f"S{i}" for i in range(9)]}
    cfg = exp_inputs.config([])
    a, b = both(lambda: exp_many.run(inp, cfg))
    assert a["members"] == b["members"] and [m["strategy"] for m in b["members"]] == inp["strategies"]
    assert_frame_equal(a["table"], b["table"])


def test_blindjoint_members(both: Callable) -> None:
    """Blind-joint members are the same wide and serial."""
    pop = bj.mothers({f"m{i}": ["pass", "watch", "pass", "pass"] for i in range(5)},
                     {"m4": ["wfc"]}).assign(identity="i")
    a, b = both(lambda: joint_many.run({"population": pop, "refused": "política", "source": "t"}, bj.CFG))
    strip = lambda ms: [{k: v for k, v in m.items() if k not in ("computed_at", "wall_s")} for m in ms]
    assert len(b["members"]) == 5 and strip(a["members"]) == strip(b["members"])


def test_spread_scan_per_asset(both: Callable, monkeypatch: pytest.MonkeyPatch,
                               capsys: pytest.CaptureFixture[str]) -> None:
    """The spread scan prints the same text wide and serial."""
    cfg = {"assets": {n: {} for n in "ABCDEFGHIJ"}}
    got = lambda s: {"proposal": [{"tramo": "t", "% días medidos": 1.0, "spread medio (pb)": 2.0,
                                   "comisión % propuesta": 3.0, "puntos equivalentes": ord(s)}],
                     "relative": {"constant": True, "worst": 1.0}, "model": s, "error_backwards": 0.1,
                     "declared": s, "mc_multiples": {"min": 1.0, "max": 2.0}}
    monkeypatch.setattr(scan, "one", lambda s, c: got(s))
    monkeypatch.setattr(scan.inputs, "config", lambda over: cfg)
    monkeypatch.setattr(scan, "progress", lambda *a: None)
    monkeypatch.setattr(sys, "argv", ["scan"])

    def text() -> str:
        """Capture the scan's stdout."""
        buf = io.StringIO()
        with redirect_stdout(buf):
            scan.main()
        return buf.getvalue()
    a, b = both(text)
    assert a == b and a.count("relativo") == 10


def test_decay_reads(both: Callable, monkeypatch: pytest.MonkeyPatch) -> None:
    """Decay reads and curves are the same wide and serial."""
    files = [Path(f"/x/S{i}.sqx") for i in range(450)]       # more than one BLOCK
    a, b = both(lambda: decay_report.read_all(lambda f: f.stem * 2, files))
    assert a == b == [f.stem * 2 for f in files]
    curve = lambda f: pd.Series([float(len(f.stem))] * 3)
    monkeypatch.setattr(decay_report.sqxstats, "equity", curve)
    monkeypatch.setattr(Path, "glob", lambda self, pat: files[:300])
    x, y = both(lambda: decay_report.curves(Path("/x"), None, "2020-01-01", None))
    assert list(x) == list(y) and all(x[k].equals(y[k]) for k in x) and len(x) == 300


def test_closing_jobs_run_concurrently_and_all_of_them(monkeypatch: pytest.MonkeyPatch) -> None:
    """Closing jobs overlap in time and none is dropped."""
    seen, live, top, lock = [], [0], [0], threading.Lock()

    def run(argv: list) -> None:
        """Record one job, tracking peak concurrency."""
        with lock:
            live[0] += 1
            top[0] = max(top[0], live[0])
        time.sleep(0.05)
        with lock:
            live[0] -= 1
            seen.append(argv)
    jobs = [["-m", "x", str(i)] for i in range(8)]
    mothers = pd.DataFrame({"identity": list("abcdefgh"), "strategy": list("abcdefgh")})
    monkeypatch.setattr(survivors, "about", lambda p: {"symbol": "S"})
    monkeypatch.setattr(closing.identity, "spelt", lambda *a: {})
    monkeypatch.setattr(call, "window", lambda *a: jobs)
    monkeypatch.setattr(call, "run", run)
    assert closing.reading("P", "exposure", "D", mothers).endswith("8 madre(s)")
    assert sorted(seen) == sorted(jobs) and 1 < top[0] <= closing.WIDTH


def test_closing_a_failing_job_still_stops_the_step(monkeypatch: pytest.MonkeyPatch) -> None:
    """A job that exits makes the whole closing step exit."""
    mothers = pd.DataFrame({"identity": ["a", "b"], "strategy": ["a", "b"]})
    monkeypatch.setattr(survivors, "about", lambda p: {"symbol": "S"})
    monkeypatch.setattr(closing.identity, "spelt", lambda *a: {})
    monkeypatch.setattr(call, "window", lambda *a: [["-m", "x"], ["-m", "y"]])
    monkeypatch.setattr(call, "run", lambda argv: (_ for _ in ()).throw(SystemExit("boom")))
    with pytest.raises(SystemExit):
        closing.reading("P", "exposure", "D", mothers)


SAMPLE = ("Trade_NIKKEI225_M30_volatilidadL", "Retest Markets - Family", "NIKKEI225", "2026-10-04")


@pytest.mark.skipif(not (paths.DATA / "scratch/paso10_travel/2026-10-07/crossmarket.json").is_file(),
                    reason="needs the real crossmarket sample on the data root")
def test_crossmarket_travel_real_sample(both: Callable) -> None:
    """Crossmarket travel on the real sample is the same wide and serial."""
    from studies.transfer.crossmarket.travel import run

    def go() -> Any:
        """Run the travel study into a scratch dir."""
        with tempfile.TemporaryDirectory(dir=paths.DATA / "scratch") as tmp:
            return run.run(*SAMPLE, Path(tmp) / "o")
    a, b = both(go)
    assert_frame_equal(a["verdict"], b["verdict"])
    assert_frame_equal(a["markets"], b["markets"])
    assert len(a["draws"]) == len(b["draws"]) > 0
    assert [(r["metric"], r["observed"], r["n_ge"]) for r in a["draws"]] == \
           [(r["metric"], r["observed"], r["n_ge"]) for r in b["draws"]]
