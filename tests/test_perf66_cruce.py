"""Encargo 66, the SQX crossing made faster: each fast path equal to the serial one it replaced."""

import time
import zipfile
from pathlib import Path

import pandas as pd
import pytest

from core import fanout, identities, proc, sqxfile, sqxview
from core.store import extra
from sqx.variants import neighbourbatch, tuples
from sqx.variants.build import fabricate, rewrite

FIXTURE = Path(__file__).parent / "fixtures" / "strategy.sqx"
CFG = {
    "n": 30,
    "entry_pct": 15,
    "exit_pct": 30,
    "seed": 0,
    "int_floor": 1,
    "fixed": [
        r"(Shift|Shf)\d*$",
        r"(Method|Mth|Mode|Mde|Type|AppliedPrice|AppPrc|Fld|Str)\d*$",
    ],
}


def slow(key: int) -> int:
    """A task that raises when it is key 0 and otherwise takes a while."""
    if key == 0:
        raise ValueError("boom")
    time.sleep(0.3)
    return key


def test_a_failing_task_cancels_the_queue() -> None:
    """Twenty tasks of 0.3 s on two workers took 3 s to surface the error; now only the running ones."""
    costs = {0: 100, **{i: 1 for i in range(1, 21)}}
    started = time.time()
    with pytest.raises(ValueError, match="boom"):
        list(fanout.run(slow, costs, 2))
    assert time.time() - started < 1.5


def test_the_frame_is_the_serial_rows_in_the_input_order() -> None:
    """`sqxview.frame` across processes: the rows `_row` gives one by one, in the order of the dict."""
    files = {n: FIXTURE for n in ("Strategy 9", "Strategy 10", "Strategy 2")}
    sqxview._FILES = files
    serial = pd.DataFrame([sqxview._row(n) for n in files])
    pd.testing.assert_frame_equal(sqxview.frame(files), serial, check_exact=True)
    assert list(serial["Strategy Name"]) == list(files)


def test_identities_across_processes_fill_the_parent_cache(tmp_path: Path) -> None:
    """The hashes come back equal to the serial ones and a later `identity()` reads them from the cache."""
    copies = []
    for i in range(3):
        copies.append(tmp_path / f"S{i}.sqx")
        copies[-1].write_bytes(FIXTURE.read_bytes())
    want = {f: sqxfile.identity(f) for f in copies}
    sqxfile._SEEN.clear()
    assert identities.many(copies, 2) == want
    assert len(sqxfile._SEEN) == len(copies)


@pytest.mark.parametrize("categorical", [True, False])
def test_family_over_categories_is_family_over_text(categorical: bool) -> None:
    """A categorical column is tested per category: same rows as `astype(str)`, a NaN row included."""
    strategy = pd.Series(["A", "A_Scaled H1", "B", None, "AB", "nan", "A"] * 3)
    frame = pd.DataFrame(
        {
            "strategy": strategy.astype("category") if categorical else strategy,
            "identity": pd.Series(list("xyzxyzx") * 3).astype("category"),
            "v": range(21),
        },
        index=pd.Index(list("abcdefg") * 3),
    )
    for name, ident in (("A", ""), ("A", "x"), ("nan", ""), ("zzz", "z"), ("B", "y")):
        said = frame["strategy"].astype(str)
        hit = said.eq(name) | said.str.startswith(f"{name}_Scaled")
        hit |= (
            (frame.index == ident) | frame["identity"].astype(str).eq(ident)
            if ident
            else False
        )
        pd.testing.assert_frame_equal(
            extra.family(frame, name, ident), frame[hit], check_exact=True
        )


def test_the_neighbour_files_are_the_serial_ones_to_the_byte(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Two mothers written in blocks across processes against the one-by-one loop, entry stamps frozen."""
    monkeypatch.setattr(
        time, "localtime", lambda *_: time.gmtime(1_700_000_000)
    )  # zip stamps "now"
    monkeypatch.setattr(fabricate, "BLOCK", 7)
    mothers = tmp_path / "m"
    mothers.mkdir()
    for name in ("Strategy A", "Strategy B"):
        (mothers / f"{name}.sqx").write_bytes(FIXTURE.read_bytes())
    rows = neighbourbatch.plan(sorted(mothers.glob("*.sqx")), CFG)
    for path, own in rows.groupby("mother", sort=False):
        parent = rewrite.members(Path(path))
        for row in own.to_dict("records"):
            wanted = (
                {}
                if row["origin"]
                else {k: v for k, v in tuples.from_columns(row).items() if v == v}
            )
            parts = rewrite.variant(
                parent,
                row["variant_id"],
                fabricate.name_of(row["strategy"], row["variant_id"]),
                wanted,
            )
            (tmp_path / "old").mkdir(exist_ok=True)
            rewrite.save(
                tmp_path / "old" / f"{row['variant_id']}.sqx", parts, "minimal"
            )
    neighbourbatch.write(rows, tmp_path / "new", "minimal")
    old = {p.name: p.read_bytes() for p in (tmp_path / "old").iterdir()}
    assert old and old == {p.name: p.read_bytes() for p in (tmp_path / "new").iterdir()}
    assert len(old) == len(rows) and zipfile.is_zipfile(
        tmp_path / "new" / "M000N0001.sqx"
    )


def test_the_chain_loads_no_trades_of_an_unread_databank(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`chain.load` plans metrics for every databank but the trades only of those someone reads."""
    from ui.daemon.launch import chain
    from ui.daemon.loader import afterrun

    asked = []
    monkeypatch.setattr(chain.loader, "status", lambda project, databank: databank)
    monkeypatch.setattr(
        chain.loader,
        "commands",
        lambda project, now: {
            "metrics": ("python", ["metrics", now]),
            "trades": ("conductor", ["trades", now]),
        },
    )
    monkeypatch.setattr(
        proc, "command", lambda argv: asked.append(tuple(argv)) or (0, "")
    )
    banks = ["Results", *sorted(afterrun.UNREAD_TRADES)]
    for bank in banks:
        assert chain.load("Test_P", bank) == []
    assert {a for a in asked if a[0] == "metrics"} == {("metrics", b) for b in banks}
    assert {a for a in asked if a[0] == "trades"} == {("trades", "Results")}


def test_the_cross_tf_input_bank_exports_no_trades() -> None:
    """Python fills `CrossTF_Input` and no task backtests it there: a scaled sibling's `.sqx`
    carries its mother's stored result and SQX's memory none, so its `.abk` never matched."""
    from ui.daemon.loader import afterrun

    assert (
        "CrossTF_Input" in afterrun.UNREAD_TRADES
        and "CrossTF_Mothers" not in afterrun.UNREAD_TRADES
    )


def test_the_execute_phases_land_in_their_buckets(tmp_path: Path) -> None:
    """`execute.sqx` is SQX computing and `execute.sync` its sync; what is left of `execute` stays `resto`."""
    from pipeline.autopilot import timing

    path = tmp_path / "fases.csv"
    rows = [
        (1050.0, 40, "execute.sqx", ""),
        (1060.0, 10, "execute.sync", ""),
        (1070.0, 70, "execute", ""),
        (1100.0, 100, "accion", "16.5"),
    ]
    path.write_text(
        "".join(
            f"{end - s:.3f},{s:.3f},{name},{detail},1\n"
            for end, s, name, detail in rows
        ),
        encoding="utf-8",
    )
    own = timing.own(pd.read_csv(path, names=timing.COLUMNS)).set_index("phase")
    assert own["bucket"].to_dict() == {
        "accion": "resto",
        "execute": "resto",
        "execute.sqx": "sqx",
        "execute.sync": "sync",
    }
    assert own["own"].round(3).to_dict() == {
        "accion": 30,
        "execute": 20,
        "execute.sqx": 40,
        "execute.sync": 10,
    }


@pytest.fixture
def loader_world(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict:
    """A tmp install (`Results` and `OOS`, two files each) under the REAL `state.status` / `commands` / `load`."""
    import os

    from sqx.databank import find, state

    top = tmp_path / "top"
    banks = top / "user" / "projects" / "Test_P" / "databanks"
    for bank in ("Results", "OOS"):
        (banks / bank).mkdir(parents=True)
        for n in ("A", "B"):
            (banks / bank / f"{n}.sqx").write_bytes(b"x")
    world = {"cross": False, "started": [], "ids": None}
    monkeypatch.setattr(find, "install_of", lambda p, d: ("custodian", top))
    monkeypatch.setattr(find, "spelled", lambda p, d: d)
    monkeypatch.setattr(
        find, "partner", lambda t, p, d: "OOS" if d == "Results" else None
    )
    monkeypatch.setattr(
        find, "files", lambda t, p, d: sorted((banks / d).glob("*.sqx"))
    )
    monkeypatch.setattr(find, "writing", lambda t, p: False)
    monkeypatch.setattr(find, "cross_market", lambda files: world["cross"])
    monkeypatch.setattr(find, "feed", lambda f: "EURUSD_M1")
    monkeypatch.setattr(
        find,
        "roster",
        lambda p, d: (
            world["ids"](d)
            if world["ids"]
            else {f.stem: f.stem for f in (banks / d).glob("*.sqx")}
        ),
    )
    monkeypatch.setattr(state.jobs, "listing", lambda: [])
    monkeypatch.setattr(state, "fingerprint", lambda files: "sig")
    monkeypatch.setattr(
        state, "export_dir", lambda p, d, day, batch="": tmp_path / "raw" / d / day
    )
    monkeypatch.setattr(
        state, "harvest_dir", lambda p, d, day: tmp_path / "harvest" / d / day
    )
    monkeypatch.setattr(state, "metrics_export", lambda p, d: tmp_path / "metrics" / d)
    monkeypatch.setattr(
        state.jobs,
        "start",
        lambda name, argv, meta, lane: world["started"].append((meta["loader"], argv)),
    )

    def exported(bank: str, kind: str = "raw") -> None:
        """Leave a manifest newer than the bank's files, as a finished export does."""
        folder = tmp_path / kind / bank / "2026-01-01"
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "manifest.json").write_text("{}")
        os.utime(folder / "manifest.json", (time.time() + 60, time.time() + 60))

    world["exported"], world["tmp"] = exported, tmp_path
    return world


def exports_flag(todo: dict) -> list[str]:
    """The harvest's `--exports`, when asked."""
    return [a for a in todo.get("harvest", ("", []))[1] if a == "--exports"]


def test_commands_asks_the_harvest_for_exports_when_either_side_is_stale(
    loader_world: dict,
) -> None:
    """The step-7 case: the build's trades fresh, the retest's not -> still one pass; cross-market -> none."""
    from sqx.databank import state

    now = state.status("Test_P", "Results")
    assert exports_flag(state.commands("Test_P", now)) == ["--exports"]  # both stale
    assert exports_flag(state.commands("Test_P", now, exports=False)) == []
    loader_world["cross"] = True
    assert exports_flag(state.commands("Test_P", now)) == []  # `export_retest`'s shape
    loader_world["cross"] = False
    loader_world["exported"]("Results")
    now = state.status("Test_P", "Results")
    assert now["pieces"]["trades"]["state"] == "fresh"
    assert exports_flag(state.commands("Test_P", now)) == [
        "--exports"
    ]  # only the partner's are due
    loader_world["exported"]("OOS")
    assert (
        exports_flag(state.commands("Test_P", state.status("Test_P", "Results"))) == []
    )


def test_load_queues_the_trades_unless_the_harvest_covers_the_whole_databank(
    loader_world: dict,
) -> None:
    """A build with an unpaired strategy keeps its trades job (after the harvest); a fully paired one has the harvest write them."""
    from sqx.databank import state

    state.load("Test_P", "Results")
    assert [k for k, _ in loader_world["started"]] == ["metrics", "harvest"]
    assert "--exports" in loader_world["started"][1][1]
    for ids in (
        lambda d: (
            {"A": "A", "B": "B"} if d == "Results" else {"A": "A"}
        ),  # one unpaired
        lambda d: {"X": "A"},
    ):  # two files, one identity
        loader_world["started"].clear()
        loader_world["ids"] = ids
        state.load("Test_P", "Results")
        assert [k for k, _ in loader_world["started"]] == [
            "metrics",
            "harvest",
            "trades",
        ]
        assert "--exports" not in loader_world["started"][1][1]


@pytest.mark.parametrize("wrote,runs", [(True, 0), (False, 1)])
def test_chain_load_over_the_real_commands_skips_the_trades_the_harvest_wrote(
    loader_world: dict, monkeypatch: pytest.MonkeyPatch, wrote: bool, runs: int
) -> None:
    """`chain.load`: the real `commands` puts the harvest first with `--exports`; `export_trades` runs only if it left them stale."""
    from ui.daemon.launch import chain

    asked: list[str] = []

    def command(argv: list[str]) -> tuple[int, str]:
        """Stand-in for the child: a harvest with `--exports` leaves both trade exports."""
        asked.append(argv[1].rsplit(".", 1)[-1])
        if argv[1].endswith("harvest") and "--exports" in argv and wrote:
            loader_world["exported"]("Results")
            loader_world["exported"]("OOS")
        return 0, ""

    monkeypatch.setattr(proc, "command", command)
    assert chain.load("Test_P", "Results") == []
    assert (
        asked[:2] == ["export_metrics", "harvest"]
        and asked.count("export_trades") == runs
    )


def test_window_chain_prints_a_batch_that_lost_strategies(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    """Without a `tell` (the window's chain) the «FALLARON» line goes to the job's own log."""
    from ui.daemon.launch import chain

    monkeypatch.setattr(chain.workflow, "context", lambda p: {})
    monkeypatch.setattr(chain, "feeds", lambda n, c: [])
    monkeypatch.setattr(chain.rail, "BY_N", {"8": {}})
    monkeypatch.setattr(chain.rail, "refusal", lambda n, k, c: None)
    monkeypatch.setattr(
        chain.rail,
        "plan",
        lambda spec, k, c, db, picked: [
            {"label": "f", "argv": ["-m", "x"], "about": {}}
        ],
    )
    monkeypatch.setattr(
        chain,
        "floored",
        lambda argv, key="", picked=None: (0, "FALLARON 2 de 16: a, b"),
    )
    assert chain.python_step("P", {"n": "8", "tests": ["filters"]}) == []
    assert "filters: FALLARON 2 de 16: a, b" in capsys.readouterr().out


def test_a_failed_harvest_does_not_take_the_trades_job_with_it(
    loader_world: dict, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The harvest that carried `--exports` failed: the next load offers the trades again (not the failed harvest)."""
    from sqx.databank import state

    job = {
        "loader": "harvest",
        "project": "Test_P",
        "databank": "Results",
        "rc": 1,
        "cancelled": False,
        "tail": ["boom"],
    }
    monkeypatch.setattr(state.jobs, "listing", lambda: [job])
    state.load("Test_P", "Results")
    assert [k for k, _ in loader_world["started"]] == ["metrics", "trades"]
    loader_world["started"].clear()
    state.load(
        "Test_P", "Results", retry=True
    )  # the owner's retry: the harvest again, with the trades inside it
    assert [k for k, _ in loader_world["started"]] == ["metrics", "harvest"]
