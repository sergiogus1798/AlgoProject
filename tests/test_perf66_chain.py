"""Encargo 66, the launch chain: RAM and cores reserved by weight, a step's tests dispatched together."""

from pathlib import Path
from types import ModuleType

import pytest


def chain_fakes(monkeypatch: pytest.MonkeyPatch, free_gb: float) -> list:
    """`chain.floored` on a fake machine: `free_gb` free, and every command a recorded no-op."""
    from ui.daemon.launch import chain
    monkeypatch.setattr(chain.psutil, "virtual_memory", lambda: type("M", (), {"available": free_gb * 1e9}))
    monkeypatch.setitem(chain._RUNNING, "n", 0)
    monkeypatch.setitem(chain._RUNNING, "gb", 0.0)
    monkeypatch.setitem(chain._RUNNING, "cores", 0)
    monkeypatch.setitem(chain._RUNNING, "stop", False)
    monkeypatch.setattr(chain.time, "sleep", lambda s: (_ for _ in ()).throw(TimeoutError))
    return []


def test_floored_second_heavy_waits_and_light_ones_pack(monkeypatch: pytest.MonkeyPatch) -> None:
    """Free RAM for one heavy job above the floor: the second heavy waits (it would sleep),
    three light ones still start together."""
    from ui.daemon import jobs
    from ui.daemon.launch import chain
    heavy = jobs.weight({"study": "gate"}) * chain.GB_PER_WEIGHT
    chain_fakes(monkeypatch, jobs.FLOOR_GB + heavy + 0.1 + 3 * 3 * chain.GB_PER_WEIGHT)
    ran = []
    monkeypatch.setattr(chain, "command", lambda argv: (ran.append(argv), (0, ""))[1])
    # nothing runs yet: a first heavy one always starts (and stays "running" for this test)
    chain._RUNNING.update(n=1, gb=heavy, cores=jobs.weight({"study": "gate"}))
    with pytest.raises(TimeoutError):        # second heavy: no room for its reservation -> sleeps
        chain.floored(["x"], "gate")
    chain._RUNNING.update(n=1, gb=0.0, cores=0)
    for _ in range(3):                       # light ones fit beside it
        chain._RUNNING["n"] += 1
        assert chain.floored(["y"], "entryQuality") == (0, "")
        chain._RUNNING["n"] -= 1
    assert ran == [["y"]] * 3


def test_floored_reserves_cumulatively(monkeypatch: pytest.MonkeyPatch) -> None:
    """Two threads measuring the same free figure do not both pass: the first's reservation counts."""
    from ui.daemon import jobs
    from ui.daemon.launch import chain
    chain_fakes(monkeypatch, jobs.FLOOR_GB + 0.8)       # room for one light (0.75), not two
    seen = []

    def hold(argv: list[str]) -> tuple[int, str]:
        """Stand-in command: records the reservation and tries a second floored job inside."""
        seen.append(dict(chain._RUNNING))
        with pytest.raises(TimeoutError):
            chain.floored(["second"], "entryQuality")
        return 0, ""
    monkeypatch.setattr(chain, "command", hold)
    chain._RUNNING["n"] = 1                              # something else of the chain runs
    assert chain.floored(["first"], "entryQuality") == (0, "")
    assert seen[0]["gb"] == pytest.approx(3 * chain.GB_PER_WEIGHT)


def test_python_step_runs_tests_together_with_monkey_excess_last(monkeypatch: pytest.MonkeyPatch,
                                                                 tmp_path: Path) -> None:
    """Two independent tests overlap in time; monkeyExcess starts only once both have ended;
    the failures come back in the tests' order."""
    import threading
    from ui.daemon.launch import chain
    log, lock, both = [], threading.Lock(), threading.Barrier(2, timeout=5)
    monkeypatch.setattr(chain.workflow, "context", lambda p: {})
    monkeypatch.setattr(chain, "feeds", lambda n, c: [])
    monkeypatch.setattr(chain.rail, "BY_N", {"8": {}})
    monkeypatch.setattr(chain.rail, "refusal", lambda n, k, c: None)
    monkeypatch.setattr(chain.rail, "plan", lambda spec, k, c, db, picked: [{"label": k, "argv": [k], "about": {}}])

    def fake(argv: list[str], key: str = "", picked: int | None = None) -> tuple[int, str]:
        """Stand-in for `chain.floored`: monkeyExcess runs alone, the rest meet at a barrier."""
        if argv[0] != "monkeyExcess":
            both.wait()                                  # fails (BrokenBarrier) if run one by one
        with lock:
            log.append(argv[0])
        return (1, "boom") if argv[0] == "a" else (0, "")
    monkeypatch.setattr(chain, "floored", fake)
    got = chain.python_step("P", {"n": "8", "tests": ["monkeyExcess", "a", "b"]})
    assert log[-1] == "monkeyExcess" and sorted(log[:2]) == ["a", "b"]
    assert got == ["a: boom"]


def run_threads(chain: ModuleType, jobs_: list[tuple[str, str]], monkeypatch: pytest.MonkeyPatch) -> list[tuple[str, int]]:
    """Run `floored` for (key, name) pairs in threads on a machine with plenty of RAM; a command
    sleeps 0.15 s and records (name, how many were running). Returns the log of overlaps."""
    import threading
    import time
    real = time.sleep
    chain_fakes(monkeypatch, 500)
    monkeypatch.setattr(chain.time, "sleep", lambda s: real(0.02))
    seen, lock = [], threading.Lock()

    def cmd(argv: list[str]) -> tuple[int, str]:
        """Stand-in command: notes which names run together."""
        with lock:
            live.append(argv[0])
            seen.append((argv[0], tuple(live)))
        real(0.15)
        with lock:
            live.remove(argv[0])
        return 0, ""
    live: list[str] = []
    monkeypatch.setattr(chain, "command", cmd)
    ts = [threading.Thread(target=chain.floored, args=([n], k)) for k, n in jobs_]
    [t.start() for t in ts]
    [t.join() for t in ts]
    return seen


def test_two_wide_never_overlap_and_light_never_beside_wide(monkeypatch: pytest.MonkeyPatch) -> None:
    """With RAM to spare, only the cores gate: gate and feedQuality never run together, and a
    light study never starts beside a wide one."""
    from ui.daemon import jobs
    from ui.daemon.launch import chain
    seen = run_threads(chain, [("gate", "g"), ("feedQuality", "f"), ("decay", "d"),
                               ("entryQuality", "e1"), ("filters", "e2")], monkeypatch)
    wide = {"g", "f", "d"}
    for name, live in seen:
        assert len(wide & set(live)) <= 1, (name, live)
        assert not (wide & set(live) and set(live) - wide), (name, live)
    assert {"decay", "gate", "feedQuality"} <= jobs.WIDE


def test_light_studies_pack(monkeypatch: pytest.MonkeyPatch) -> None:
    """Sixteen light commands (weight 3 each) run together."""
    from ui.daemon import jobs
    from ui.daemon.launch import chain
    seen = run_threads(chain, [("filters", f"l{i}") for i in range(jobs.SLOTS // jobs.LIGHT)], monkeypatch)
    assert max(len(live) for _, live in seen) == jobs.SLOTS // jobs.LIGHT


def test_every_module_that_fans_out_is_wide() -> None:
    """A module under studies/ that calls `fanout.run` and belongs to a startable study of the
    catalogue has that study in `jobs.WIDE` (a calibrator and a data scan are not studies)."""
    from core.paths import ROOT
    from ui.daemon import jobs
    from ui.daemon.runner import table
    keys = {k for k, v in table.STUDIES.items() if "plan" in v}
    missing = []
    for f in (ROOT / "studies").rglob("*.py"):
        if "fanout.run(" not in f.read_text(encoding="utf-8") or "calibrate" in f.parts:
            continue
        for k in keys & set(f.relative_to(ROOT).parts) - jobs.WIDE:
            missing.append(f"{k}: {f.relative_to(ROOT)}")
    assert not missing, missing


def test_python_step_folds_light_plans_and_tells_the_lost(monkeypatch: pytest.MonkeyPatch) -> None:
    """Sixteen one-strategy plans of a light study become ONE command (was 16 subprocesses);
    a batch that exits 0 with «FALLARON …» in its tail reaches `tell`."""
    from ui.daemon.launch import chain
    monkeypatch.setattr(chain.workflow, "context", lambda p: {})
    monkeypatch.setattr(chain, "feeds", lambda n, c: [])
    monkeypatch.setattr(chain.rail, "BY_N", {"8": {}})
    monkeypatch.setattr(chain.rail, "refusal", lambda n, k, c: None)
    plans = [{"label": "filters", "argv": ["-m", "x", "--strategy", str(i)], "about": {"strategy": str(i)}}
             for i in range(16)]
    monkeypatch.setattr(chain.rail, "plan", lambda spec, k, c, db, picked: plans)
    monkeypatch.setattr(chain.batch, "PLANS", Path(__import__("tempfile").mkdtemp()))
    calls, told = [], []
    monkeypatch.setattr(chain, "floored", lambda argv, key="", picked=None:
                        (calls.append((argv, picked)), (0, "terminado / FALLARON 2 de 16: a, b"))[1])
    assert chain.python_step("P", {"n": "8", "tests": ["filters"]}, tell=told.append) == []
    assert len(calls) == 1 and "ui.daemon.runner.batchrun" in calls[0][0] and calls[0][1]
    assert told == ["filters: FALLARON 2 de 16: a, b"]
