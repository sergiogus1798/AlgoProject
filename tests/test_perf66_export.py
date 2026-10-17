"""Encargo 66, the step export: harvest, export and piece each leave only what they should."""

import shutil
from pathlib import Path
from typing import Any

import pytest


# ---- 5.1 / 5.3 / 7.2a: the step export ----------------------------------------------------

CSV_HEAD = (
    "Ticket;Symbol;Type;Open time;Open price;Size;Close time;Close price;Profit/Loss;"
    "Balance;Sample type;Close type;MAE ($);MFE ($)\n"
)


def fake_orderstocsv(source: Path, out_dir: Path, data: str = "main") -> str:
    """The lowest function that needs SQX: one CSV per .sqx, its rows a function of the file name."""
    out_dir.mkdir(parents=True, exist_ok=True)
    for _n, f in enumerate(sorted(Path(source).glob("*.sqx"))):
        base = len(
            f.stem.removeprefix("IS__").removeprefix("OOS__")
        )  # the same strategy under any prefix
        rows = "".join(
            f"{t};EURUSD;Buy;2020.01.{t + 1:02d} 10:00:00;1.{base}0;1.0;2020.01.{t + 1:02d} 12:00:00;"
            f"1.{base}5;{t * 3.5 - base};{10000 + t};In Sample;Exit After X Bars;-1.5;{base}.25\n"
            for t in range(1, 6)
        )
        (out_dir / f"{f.stem}.csv").write_text(CSV_HEAD + rows)
    return ""


def test_the_harvest_exports_are_the_export_trades_ones_to_the_byte(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """5.1: `harvest --exports` leaves in each databank's raw folder what `export_trades` left."""
    import sys
    from core import exportdrv, manifest
    from sqx.export import export_trades
    from studies.screening.gate import harvest

    real = (
        Path.home() / "Desktop/SQX_w2/user/projects/Test_USA500_H1_indicesIBS/databanks"
    )
    if not (real / "OOS" / "Strategy 1.13.354.sqx").exists():
        pytest.skip("the real build/retest pair is not on this machine")
    import importlib
    from core import (
        sqxfile as sqxfile_mod,
        tradepack,
    )  # test_export_manifests.py swaps their functions at import

    importlib.reload(tradepack)
    importlib.reload(sqxfile_mod)
    for name in ("Results", "OOS"):  # a real pair, copied: read only
        (tmp_path / "databanks" / name).mkdir(parents=True)
        shutil.copy(
            real / name / "Strategy 1.13.354.sqx", tmp_path / "databanks" / name
        )
    monkeypatch.setattr(exportdrv, "trades", fake_orderstocsv)
    monkeypatch.setattr(sqxfile_mod, "symbol", lambda f: ("EURUSD", "EURUSD_M30"))
    for mod, label in ((export_trades, "old"), (harvest, "new")):
        monkeypatch.setattr(
            mod, "databank_dir", lambda p, d, install=None: tmp_path / "databanks" / d
        )
        monkeypatch.setattr(
            export_trades, "project_dir", lambda p, install=None: tmp_path
        )
        monkeypatch.setattr(
            mod,
            "export_dir",
            lambda p, d, day, batch="", label=label: tmp_path / label / "raw" / d / day,
        )
    monkeypatch.setattr(
        harvest, "harvest_dir", lambda p, d, day: tmp_path / "new" / "harvest" / d / day
    )
    for argv, mod in (
        (["--databank", "Results", "--symbol", "EURUSD"], export_trades),
        (["--databank", "OOS", "--symbol", "EURUSD"], export_trades),
    ):
        monkeypatch.setattr(sys, "argv", ["x", "--project", "Test_P", *argv])
        mod.main()
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "x",
            "--project",
            "Test_P",
            "--databank",
            "Results",
            "--oos-databank",
            "OOS",
            "--exports",
        ],
    )
    harvest.main()
    for bank in ("Results", "OOS"):
        old = next((tmp_path / "old" / "raw" / bank).iterdir())
        new = next((tmp_path / "new" / "raw" / bank).iterdir())
        for name in ("trades.parquet", "timeframes.csv", "identity.csv"):
            assert (old / name).read_bytes() == (new / name).read_bytes(), (bank, name)
        assert manifest.read(old)["counts"] == manifest.read(new)["counts"]
        assert sorted(x.name for x in old.iterdir()) == sorted(
            x.name for x in new.iterdir()
        )
        assert (old / "lineage.csv").read_bytes() == (
            new / "lineage.csv"
        ).read_bytes(), bank


@pytest.fixture
def export_world(monkeypatch: pytest.MonkeyPatch) -> tuple[dict, Any]:
    """afterrun with the install, the loader and the pieces stubbed: it records what ran and what it asked about."""
    from ui.daemon import progress
    from sqx.worker import guard as workerguard
    from ui.daemon.loader import afterrun, find, state

    world = {"ran": [], "asked": [], "needs": {}}
    every = [
        ("Test_P", "OOS"),
        ("Test_P", "Results"),
        ("Test_P", "WFM"),
        ("Test_P", "Other"),
    ]
    monkeypatch.setattr(progress, "installs", lambda: {"custodian": Path("/x")})
    monkeypatch.setattr(workerguard, "marked", lambda role: {"project": "Test_P"})
    monkeypatch.setattr(afterrun, "banks", lambda top, only=None: every)
    monkeypatch.setattr(
        find, "partner", lambda top, p, d: "OOS" if d == "Results" else None
    )
    monkeypatch.setattr(afterrun, "extras", lambda *a, **k: [])
    monkeypatch.setattr(state, "status", lambda p, d: world["asked"].append(d) or d)
    monkeypatch.setattr(
        state,
        "commands",
        lambda p, now, exports=True: {
            k: ("python", ["-m", k, now]) for k in world["needs"].get(now, ())
        },
    )

    def piece(argv: list[str]) -> int:
        """Stand-in for `afterrun.piece`: records the call and lets a harvest clear the trades need."""
        world["ran"].append((argv[1], argv[2]))
        if argv[1] == "harvest":  # the harvest wrote both trade exports
            world["needs"]["Results"] = [
                k for k in world["needs"]["Results"] if k != "trades"
            ]
            world["needs"]["OOS"] = [
                k for k in world["needs"].get("OOS", []) if k != "trades"
            ]
        return 0

    monkeypatch.setattr(afterrun, "piece", piece)
    return world, afterrun


def test_one_harvest_pass_leaves_no_trades_to_export(
    export_world: tuple[dict, Any],
) -> None:
    """5.1: the build's harvest goes first and the trades it wrote are not exported again."""
    world, afterrun = export_world
    world["needs"] = {"OOS": ["trades"], "Results": ["harvest", "trades", "metrics"]}
    assert afterrun.export("custodian") == 0
    assert world["ran"] == [("harvest", "Results"), ("metrics", "Results")]


def test_a_side_the_harvest_left_out_still_gets_its_trades(
    export_world: tuple[dict, Any],
) -> None:
    """5.1: when the pairing took a side partly, the loader still says its trades are stale and they run."""
    world, afterrun = export_world
    world["needs"] = {"Results": ["harvest", "trades"]}
    afterrun.piece = lambda argv: (
        world["ran"].append((argv[1], argv[2])) or 0
    )  # the harvest fixes nothing
    afterrun.export("custodian")
    assert world["ran"] == [("harvest", "Results"), ("trades", "Results")]


def test_the_step_export_touches_only_its_outputs_and_the_stale_rest_stays_stale(
    export_world: tuple[dict, Any], tmp_path: Path
) -> None:
    """7.2a: the OOS retest's step exports it and the build's harvest; `Other` and `WFM` are never read or signed."""
    from ui.daemon.loader import state

    world, afterrun = export_world
    world["needs"] = {n: ["metrics", "trades"] for n in ("OOS", "WFM", "Other")} | {
        "Results": ["harvest"]
    }
    assert afterrun.export("custodian", names={"OOS"}) == 0
    assert sorted(set(world["ran"])) == [
        ("harvest", "Results"),
        ("metrics", "OOS"),
    ]  # the harvest wrote OOS's trades
    assert not {"WFM", "Other"} & set(
        world["asked"]
    )  # no status, so no signature written for them
    kept = tmp_path / "Other.sqx"  # and an export that was never made reads stale
    kept.write_bytes(b"x")
    assert state.age(None, [kept]) == "missing"
    world["ran"].clear()
    afterrun.export("custodian")  # the stop's export (no names) still does the rest
    assert {d for _, d in world["ran"]} >= {"WFM", "Other", "OOS"}


def test_a_piece_runs_in_this_process_with_its_arguments(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """5.3: `-m module args` runs here; its exit code, a message or an exception is the failure it was as a subprocess."""
    import sys
    from ui.daemon.loader import afterrun

    (tmp_path / "perf66_piece.py").write_text(
        "import sys\nopen(sys.argv[1], 'a').write(' '.join(sys.argv[1:]) + '\\n')\n"
        "if sys.argv[2] == 'exit': sys.exit(3)\nif sys.argv[2] == 'say': sys.exit('bad')\n"
        "if sys.argv[2] == 'raise': raise ValueError\n"
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    log, before = tmp_path / "log", list(sys.argv)
    rc = [
        afterrun.piece(["-m", "perf66_piece", str(log), a])
        for a in ("ok", "exit", "say", "raise")
    ]
    assert rc == [0, 3, 1, 1] and sys.argv == before
    assert log.read_text().splitlines()[0] == f"{log} ok"


# ---- review fixes: names in either spelling, scope, liverun.export -------------------------

REAL_PROJECT = (
    Path.home() / "Desktop/SQX_w2/user/projects/Test_NIKKEI225_M30_simpleL_live"
)


def test_step_names_in_the_folder_spelling_run_every_extra_in_scope(
    export_world: tuple[dict, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    """The step's outputs are spelled as the folders are («SPP IS»): the REAL `EXTRA` must run for each in scope."""
    from ui.daemon.loader import afterrun
    from ui.daemon.loader.extrasdef import EXTRA

    banks = REAL_PROJECT / "databanks"
    held = (
        {d.name for d in banks.glob("*") if any(d.glob("*.sqx"))}
        if banks.is_dir()
        else set()
    )
    want = {n for n, (src, *_) in EXTRA.items() for b in src if b in held}
    if not want:
        pytest.skip("the real project with extras databanks is not on this machine")
    world, _ = export_world
    monkeypatch.undo()  # the fixture's stubs go; re-install only what a read-only run needs
    from ui.daemon import progress
    from sqx.worker import guard as workerguard
    from ui.daemon.loader import state

    ran: list[str] = []
    monkeypatch.setattr(
        progress, "installs", lambda: {"custodian": REAL_PROJECT.parents[2]}
    )
    monkeypatch.setattr(
        workerguard, "marked", lambda role: {"project": REAL_PROJECT.name}
    )
    monkeypatch.setattr(
        afterrun,
        "banks",
        lambda top, only=None: [(REAL_PROJECT.name, b) for b in sorted(held)],
    )
    monkeypatch.setattr(state, "status", lambda p, d: {"error": "x"})
    monkeypatch.setattr(state, "commands", lambda p, now, exports=True: {})
    monkeypatch.setattr(state, "age", lambda done, files: "stale")
    monkeypatch.setattr(afterrun, "piece", lambda argv: ran.append(argv[1]) or 0)
    monkeypatch.setattr(afterrun.find, "partner", lambda top, p, d: None)
    assert afterrun.export("custodian", names=set(held)) == 0
    assert len(ran) == len(want), (ran, want)
    sent = {afterrun.norm(b) for b in held}
    assert (
        afterrun.extras(REAL_PROJECT.name, "r", REAL_PROJECT.parents[2], sent) != []
    )  # underscore spelling too


def test_scope_takes_either_spelling_and_adds_the_build_of_a_retest(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`scope`: names in either spelling pick the same databanks; a retest in scope pulls its build in for the harvest only."""
    from ui.daemon.loader import afterrun, find

    every = [("P", "Results"), ("P", "OOS"), ("P", "SPP IS")]
    monkeypatch.setattr(afterrun, "banks", lambda top, only=None: every)
    monkeypatch.setattr(
        find, "partner", lambda top, p, d: "OOS" if d == "Results" else None
    )
    assert afterrun.scope(Path("/x"), "P", None) == dict.fromkeys(every, True)
    assert (
        afterrun.scope(Path("/x"), "P", {"SPP_IS"})
        == afterrun.scope(Path("/x"), "P", {"SPP IS"})
        == {("P", "SPP IS"): True}
    )
    assert afterrun.scope(Path("/x"), "P", {"OOS"}) == {
        ("P", "OOS"): True,
        ("P", "Results"): False,
    }


def test_a_step_scoped_harvest_asks_for_exports_so_the_retest_costs_no_second_pass(
    export_world: tuple[dict, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Step 7: the build is in scope for its harvest only, and `commands` is asked with exports on."""
    from ui.daemon.loader import state

    world, afterrun = export_world
    flags: list[tuple[str, bool]] = []
    monkeypatch.setattr(
        state,
        "commands",
        lambda p, now, exports=True: flags.append((now, exports)) or {},
    )
    afterrun.export("custodian", names={"OOS"})
    assert ("Results", True) in flags
