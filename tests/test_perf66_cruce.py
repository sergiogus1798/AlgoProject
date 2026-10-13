"""Encargo 66, the SQX crossing made faster: each fast path equal to the serial one it replaced."""

import time
import zipfile
from pathlib import Path

import pandas as pd
import pytest

from core import fanout, identities, sqxfile, sqxview
from core.store import extra
from sqx.variants import neighbourbatch, tuples
from sqx.variants.build import fabricate, rewrite

FIXTURE = Path(__file__).parent / "fixtures" / "strategy.sqx"
CFG = {"n": 30, "entry_pct": 15, "exit_pct": 30, "seed": 0, "int_floor": 1,
       "fixed": [r"(Shift|Shf)\d*$", r"(Method|Mth|Mode|Mde|Type|AppliedPrice|AppPrc|Fld|Str)\d*$"]}


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
    frame = pd.DataFrame({"strategy": strategy.astype("category") if categorical else strategy,
                          "identity": pd.Series(list("xyzxyzx") * 3).astype("category"),
                          "v": range(21)}, index=pd.Index(list("abcdefg") * 3))
    for name, ident in (("A", ""), ("A", "x"), ("nan", ""), ("zzz", "z"), ("B", "y")):
        said = frame["strategy"].astype(str)
        hit = said.eq(name) | said.str.startswith(f"{name}_Scaled")
        hit |= (frame.index == ident) | frame["identity"].astype(str).eq(ident) if ident else False
        pd.testing.assert_frame_equal(extra.family(frame, name, ident), frame[hit], check_exact=True)


def test_the_neighbour_files_are_the_serial_ones_to_the_byte(tmp_path: Path,
                                                             monkeypatch: pytest.MonkeyPatch) -> None:
    """Two mothers written in blocks across processes against the one-by-one loop, entry stamps frozen."""
    monkeypatch.setattr(time, "localtime", lambda *_: time.gmtime(1_700_000_000))   # zip stamps "now"
    monkeypatch.setattr(fabricate, "BLOCK", 7)
    mothers = tmp_path / "m"
    mothers.mkdir()
    for name in ("Strategy A", "Strategy B"):
        (mothers / f"{name}.sqx").write_bytes(FIXTURE.read_bytes())
    rows = neighbourbatch.plan(sorted(mothers.glob("*.sqx")), CFG)
    for path, own in rows.groupby("mother", sort=False):
        parent = rewrite.members(Path(path))
        for row in own.to_dict("records"):
            wanted = {} if row["origin"] else {k: v for k, v in tuples.from_columns(row).items()
                                               if v == v}
            parts = rewrite.variant(parent, row["variant_id"],
                                    fabricate.name_of(row["strategy"], row["variant_id"]), wanted)
            (tmp_path / "old").mkdir(exist_ok=True)
            rewrite.save(tmp_path / "old" / f"{row['variant_id']}.sqx", parts, "minimal")
    neighbourbatch.write(rows, tmp_path / "new", "minimal")
    old = {p.name: p.read_bytes() for p in (tmp_path / "old").iterdir()}
    assert old and old == {p.name: p.read_bytes() for p in (tmp_path / "new").iterdir()}
    assert len(old) == len(rows) and zipfile.is_zipfile(tmp_path / "new" / "M000N0001.sqx")


def test_the_chain_loads_no_trades_of_an_unread_databank(monkeypatch: pytest.MonkeyPatch) -> None:
    """`chain.load` plans metrics for every databank but the trades only of those someone reads."""
    from ui.daemon.launch import chain
    from ui.daemon.loader import afterrun
    asked = []
    monkeypatch.setattr(chain.loader, "status", lambda project, databank: databank)
    monkeypatch.setattr(chain.loader, "commands", lambda project, now: {
        "metrics": ("python", ["metrics", now]), "trades": ("conductor", ["trades", now])})
    monkeypatch.setattr(chain, "command", lambda argv: asked.append(tuple(argv)) or (0, ""))
    banks = ["Results", *sorted(afterrun.UNREAD_TRADES)]
    for bank in banks:
        assert chain.load("Test_P", bank) == []
    assert {a for a in asked if a[0] == "metrics"} == {("metrics", b) for b in banks}
    assert {a for a in asked if a[0] == "trades"} == {("trades", "Results")}


def test_the_execute_phases_land_in_their_buckets(tmp_path: Path) -> None:
    """`execute.sqx` is SQX computing and `execute.sync` its sync; what is left of `execute` stays `resto`."""
    from pipeline.autopilot import timing
    path = tmp_path / "fases.csv"
    rows = [(1050.0, 40, "execute.sqx", ""), (1060.0, 10, "execute.sync", ""),
            (1070.0, 70, "execute", ""), (1100.0, 100, "accion", "16.5")]
    path.write_text("".join(f"{end - s:.3f},{s:.3f},{name},{detail},1\n"
                            for end, s, name, detail in rows), encoding="utf-8")
    own = timing.own(pd.read_csv(path, names=timing.COLUMNS)).set_index("phase")
    assert own["bucket"].to_dict() == {"accion": "resto", "execute": "resto",
                                       "execute.sqx": "sqx", "execute.sync": "sync"}
    assert own["own"].round(3).to_dict() == {"accion": 30, "execute": 20, "execute.sqx": 40,
                                             "execute.sync": 10}
