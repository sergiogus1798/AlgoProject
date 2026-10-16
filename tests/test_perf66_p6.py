"""Encargo 66, pass 6: each speed-up equal to the code it replaced, and the latent crashes made clear."""

import ast
import json
import multiprocessing as mp
import sys
import zipfile
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import depmap
from core import wfmatrix
from core.study import blocks, draws, output
from core.store import late, save, verify
from engines.market import atr
from ledger import cells
from studies.breakage.mcRetest.measure import originals
from studies.research.memory import sources
from studies.screening.gate import inputs
from studies.transfer.crossTF.tf import run as tf_run


def _equity(tmp_path: Path, rows: list[tuple]) -> Path:
    """A tiny equity.parquet of (sample, day, identity, equity) rows."""
    path = tmp_path / "equity.parquet"
    pd.DataFrame(rows, columns=["sample", "day", "identity", "equity"]).assign(
        day=lambda f: pd.to_datetime(f["day"])
    ).to_parquet(path, index=False)
    return path


def test_a_wide_equals_pivot_with_gaps(tmp_path: Path) -> None:
    """The dictionary-codes scatter gives the pivot's frame, gaps and column order included."""
    rng = np.random.default_rng(1)
    rows = [
        (s, d, i, float(rng.normal()))
        for s in ("IS", "OOS")
        for i in ("zeta", "Alpha", "mid", "b")
        for d in pd.date_range("2020-01-01", periods=30, freq="D")
        if rng.random() > 0.2
    ]
    path = _equity(tmp_path, rows)
    old = {
        s: b.pivot(index="day", columns="identity", values="equity")
        for s, b in pd.read_parquet(path).groupby("sample")
    }
    new = inputs.wide(path)
    assert list(new) == list(old)
    for s in old:
        assert_frame_equal(old[s], new[s], check_exact=True)
        assert old[s].equals(new[s])


def test_a_wide_raises_on_a_repeated_day_and_identity(tmp_path: Path) -> None:
    """`pivot` refuses a duplicated (day, identity); so does the scatter."""
    path = _equity(
        tmp_path, [("IS", "2020-01-01", "a", 1.0), ("IS", "2020-01-01", "a", 2.0)]
    )
    with pytest.raises(ValueError):
        pd.read_parquet(path).pivot(index="day", columns="identity", values="equity")
    with pytest.raises(ValueError):
        inputs.wide(path)


def test_b_one_draws_save_equals_two(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`tf_run.write` given the old reading's rows saves once; the file holds what two saves held."""
    rec = lambda test, v: draws.record(test, "z", v, np.arange(20.0), strategy="s")  # noqa: E731
    before, kept = [rec("a", 1.0), rec("b", 2.0)], [rec("b", 3.0), rec("c", 4.0)]
    ref = tmp_path / "ref"
    ref.mkdir()
    draws.save(ref, [rec("old", 0.0)])
    draws.save(ref, before)
    draws.save(ref, kept)

    def fake_read(*args: object) -> dict:
        """What `read` gives: the new rows go to the sink, the two tables are returned."""
        args[-1].extend(kept)
        return {
            "siblings": pd.DataFrame({"x": [1]}),
            "mothers": pd.DataFrame({"state": ["ok"]}),
        }

    monkeypatch.setattr(tf_run, "read", fake_read)
    monkeypatch.setattr(
        tf_run,
        "inputs",
        SimpleNamespace(
            made=lambda plan: None,
            cards=lambda feed: (None, None, ""),
            oos1=lambda *a: None,
            build=lambda *a: None,
        ),
    )
    monkeypatch.setattr(tf_run, "sizing", SimpleNamespace(doctrine=lambda: {}))
    out = tmp_path / "out"
    out.mkdir()
    draws.save(out, [rec("old", 0.0)])
    got = {"plan": 0, "feed": 0, "trades": 0, "frames": 0, "identity": 0}
    tf_run.write(
        out, got, {"tf": 0, "run": {"blocks": [0]}}, tmp_path, tmp_path, before
    )
    one, two = (pd.read_parquet(p / draws.FILE) for p in (out, ref))
    assert_frame_equal(one.reset_index(drop=True), two.reset_index(drop=True))


def _look(args: tuple[str, str]) -> None:
    """One process spends its look and notes its judgement."""
    folder, project = args
    cells.look_oos2(project, 8)
    cells.note(project, 5)


def test_c_cells_lose_no_update_under_concurrency(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Eight processes at once: the look counter reads 8 and `projects.csv` keeps all 8 rows."""
    for name, value in (
        ("FOLDER", tmp_path),
        ("EXTRAS", tmp_path / "extras.json"),
        ("PROJECTS", tmp_path / "projects.csv"),
        ("JUDGEMENTS", tmp_path / "j.csv"),
        ("CRITERIA", tmp_path / "criteria.yaml"),
    ):
        monkeypatch.setattr(cells, name, value)
    (tmp_path / "criteria.yaml").write_text("x")
    monkeypatch.setattr(
        cells,
        "describe",
        lambda row, tpl: {
            "symbol": "X",
            "timeframe": "H1",
            "direction": "long",
            "family": "f",
            "template": "t",
        },
    )
    monkeypatch.setattr(
        sources, "registry_projects", lambda: {f"P{i}": {} for i in range(8)}
    )
    monkeypatch.setattr(sources, "templates", lambda: {})
    with mp.get_context("fork").Pool(8) as pool:
        pool.map(_look, [(str(tmp_path), f"P{i}") for i in range(8)], chunksize=1)
    assert (
        json.loads((tmp_path / "extras.json").read_text())["X_H1_long_f"]["oos2"] == 8
    )
    assert len(pd.read_csv(tmp_path / "projects.csv")) == 8


def test_d_output_writes_whole_files_and_leaves_no_temp(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The same bytes on disk as `write_text` gave, and no hidden temporary beside them."""
    monkeypatch.setattr(
        output.page, "page", lambda result, title, lede: f"<h1>{title}ñ</h1>{lede}"
    )
    monkeypatch.setattr(output.markdown, "render", lambda result, title: f"# {title}\n")
    result = {"strategy": "Strategy 1.2.3", "v": "ñ"}
    path = output.member(tmp_path, result, "T", "L")
    output.population(tmp_path, "pop", result, "T")
    assert path.read_bytes() == json.dumps(result, ensure_ascii=False).encode()
    assert (tmp_path / "pop.html").read_text() == "<h1>Tñ</h1>"
    assert (tmp_path / "pop.md").read_text() == "# T\n"
    assert not [p for p in tmp_path.rglob("*") if p.name.endswith(".tmp")]


def test_e_store_save_with_no_step_8_row_saves_nothing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A project with no step-8 row has no run to number: the answer is empty, not a ValueError."""
    monkeypatch.setattr(save, "verdicts", lambda name: {})
    assert save.project("P", []) == {"saved": [], "no_sqx": [], "problems": {}}


def test_e_late_unpaired_survives_a_header_only_table(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A table with a header and no rows cuts nothing; there is no cut file to remove."""
    study = tmp_path / "reports" / "P" / "db" / "day" / "study"
    study.mkdir(parents=True)
    (study / "t.csv").write_text("name,v\n")
    monkeypatch.setattr(late, "DATA", tmp_path)
    monkeypatch.setattr(late, "names", lambda *a: {"A"})
    found = late.unpaired("P", "id", set(), set(), tmp_path / "tmp")
    assert not [
        f for f in found if "population" not in f[2]
    ]  # nothing of its own was cut


def test_e_distribution_of_nothing_finite_says_so() -> None:
    """All-NaN draws raise a ValueError that names the title, not an IndexError."""
    with pytest.raises(ValueError, match="Mi título"):
        blocks.distribution("Mi título", "", np.full(5, np.nan), 0.0, "n")


def test_f_one_parse_serves_every_tool(tmp_path: Path) -> None:
    """The cached tree and its node list are the file's own, and a second ask costs no parse."""
    src = tmp_path / "m.py"
    src.write_text(
        '"""Doc."""\nimport numpy.linalg\nfrom pandas import x\n\n\ndef f():\n    import json\n'
    )
    assert depmap.tree(src) is depmap.tree(src) and depmap.nodes(src) is depmap.nodes(
        src
    )
    assert [type(n) for n in depmap.nodes(src)] == [
        type(n) for n in ast.walk(ast.parse(src.read_text()))
    ]
    assert depmap.imports_of(src) == {"numpy", "pandas", "json"}
    assert depmap.summary(src) == "Doc."


def test_g_originals_reads_only_its_rows_and_the_same_frame(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The filtered read gives the frame the full read followed by a mask gave."""
    rng = np.random.default_rng(2)
    n = 60
    frame = pd.DataFrame(
        {
            "identity": rng.choice(["i1", "i2", "i3"], n),
            "sample": rng.choice(["IS", "OOS"], n),
            "Type": rng.choice(["Buy", "Sell"], n),
            "Open time": pd.date_range("2020", periods=n, freq="h"),
            "Close time": pd.date_range("2020", periods=n, freq="h")
            + pd.Timedelta("30min"),
            "Size": rng.random(n),
            "Open price": rng.random(n) * 10,
            "Close price": rng.random(n) * 10,
            "Profit/Loss": rng.normal(size=n),
            "extra": rng.random(n),
        }
    )
    (tmp_path / "trades.parquet").parent.mkdir(exist_ok=True)
    frame.to_parquet(tmp_path / "trades.parquet", index=False)
    monkeypatch.setattr(originals, "latest_harvest", lambda p, d: tmp_path)
    ids = {"S1": "i1", "S3": "i3"}
    new = originals.read("P", "Results", ids, 5.0)
    by = {v: k for k, v in ids.items()}
    old = frame[frame["identity"].isin(by) & (frame["sample"] == "OOS")].copy()
    old["strategy"] = old["identity"].map(by)
    old["cost"] = originals.core_trades.cost(old, 5.0)
    old["pnl"] = old["Profit/Loss"]
    assert_frame_equal(
        new, old[originals.KEEP].reset_index(drop=True), check_exact=True
    )
    assert originals.read("P", "Results", {}, 5.0).empty


def test_h_atr_is_bit_identical_to_the_python_loop() -> None:
    """The compiled recurrence equals the per-bar loop to the last bit, NaNs included."""
    rng = np.random.default_rng(3)
    close = 100 + rng.normal(size=5000).cumsum()
    bars = pd.DataFrame(
        {
            "High": close + rng.random(5000),
            "Low": close - rng.random(5000),
            "Close": close,
        }
    )
    bars.loc[2500, "High"] = np.nan
    for period in (14, 20):
        tr = atr.true_range(bars)
        out, value = np.empty_like(tr), tr[0]
        out[0] = value
        for i in range(1, len(tr)):
            k = min(i + 1, period)
            value = ((k - 1) * value + tr[i]) / k
            out[i] = value
        assert np.array_equal(
            np.round(out, atr.ROUND), atr.sqx(bars, period), equal_nan=True
        )


def test_i_zip_archives_are_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`wfmatrix` and `verify` close every ZipFile they open."""
    path = tmp_path / "a.sqx"
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("settings.xml", "<R><ResultsMap><Results/></ResultsMap></R>")
    opened = []

    class Tracked(zipfile.ZipFile):
        """A ZipFile that remembers every instance."""

        def __init__(self, *a: object, **k: object) -> None:
            """Open as usual and note it."""
            super().__init__(*a, **k)
            opened.append(self)

    monkeypatch.setattr(zipfile, "ZipFile", Tracked)
    wfmatrix.results(path)
    wfmatrix.matrix(path)
    assert verify._damaged(path) is None
    assert len(opened) == 3 and all(z.fp is None for z in opened)


def test_stopexit_close_before_the_first_bar_does_not_read_the_last_bar() -> None:
    """A close before the first bar is clamped, not read from the last bar."""
    from portfolio.common.construct.equity import stopexit

    bars = pd.DataFrame(
        {"Open": [10.0, 99.0]},
        index=pd.to_datetime(["2024-01-01 10:00", "2024-01-01 10:01"]),
    )
    trades = pd.DataFrame(
        {
            "Type": ["Buy"],
            "Close type": ["TP"],
            "Open price": [10.0],
            "Size": [1.0],
            "Close price": [10.0],
            "Close time": pd.to_datetime(["2024-01-01 09:00"]),
        }
    )
    rebuilt = pd.DataFrame({"mae": [0.0], "mfe": [0.0]})
    got = stopexit.fills(rebuilt, trades, bars, 1.0)
    assert got["mfe"][0] == 0.0 and got.attrs["clamped"] == 1  # last bar would give 89
