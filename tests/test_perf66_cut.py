"""Encargo 66 §5.4, §5.5, §7.2b and §9.2: the cut's faster paths give today's answers.

Oracles are the old logic, kept here: a fresh pack of the cut databank for 7.2b, the serial loops for 5.4/5.5.
"""

import shutil
import time
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from core import manifest, sqxfile, tradepack, tradestore
from core.study import identity as study_identity
from sqx.curate import apply_verdict, aftercut

FIXTURE = Path(__file__).parent / "fixtures" / "strategy.sqx"
REAL = (
    Path.home()
    / "Desktop"
    / "SQX_w2"
    / "user"
    / "projects"
    / "Test_USDJPY_M30_doubleROCLong_10k"
    / "databanks"
    / "SPP IS"
)


def sqx_copies(tmp: Path, n: int) -> list[Path]:
    """n .sqx: real ones read-only-copied when the sample exists, else copies of the fixture."""
    real = sorted(REAL.glob("*.sqx"))[:6] if REAL.is_dir() else []
    out = tmp / "bank"
    out.mkdir()
    for i in range(n):
        shutil.copy(real[i] if i < len(real) else FIXTURE, out / f"S{i:03d}.sqx")
    return sorted(out.glob("*.sqx"))


# ---------------------------------------------------------------- 5.4 / 5.5


def test_identities_serial_equal_parallel_and_record_csv_identical(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Pooled identities equal serial ones and the record CSV is byte-identical."""
    files = sqx_copies(tmp_path, 30)  # above POOL_FROM: forked
    sqxfile._SEEN.clear()
    got = study_identity.hashed(files)
    sqxfile._SEEN.clear()
    assert got == {f: sqxfile.identity(f) for f in files}
    names = {files[0].stem: "", files[1].stem: "x"}
    outs = []
    for pool in (True, False):
        sqxfile._SEEN.clear()
        monkeypatch.setattr(
            apply_verdict,
            "hashed",
            study_identity.hashed
            if pool
            else lambda fs: {f: sqxfile.identity(f) for f in fs},
        )
        out = tmp_path / f"out{pool}"
        out.mkdir()
        apply_verdict.record(
            files[0].parent,
            names,
            {n: "r" for n in names},
            out,
            "000000",
            "P_none",
            "D_none",
        )
        outs.append((out / "before-000000.csv").read_bytes())
    assert outs[0] == outs[1]


def test_apply_verdict_hashes_each_file_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """5.5: `mismatched` then `record` over N files costs N hashes, not 2N."""
    files = sqx_copies(tmp_path, 12)
    calls = []
    real = sqxfile._hashed
    monkeypatch.setattr(sqxfile, "_hashed", lambda text: calls.append(1) or real(text))
    sqxfile._SEEN.clear()
    known = apply_verdict.hashed(files)
    ident = {f.stem: known[f] for f in files}
    assert apply_verdict.mismatched(files[0].parent, ident) == []
    out = tmp_path / "o"
    out.mkdir()
    apply_verdict.record(files[0].parent, ident, {}, out, "000000", "P_none", "D_none")
    assert len(calls) == len(files)


def test_a_pool_hash_is_remembered_by_the_parent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Hashes computed in the pool are not recomputed by the parent."""
    files = sqx_copies(tmp_path, 25)
    sqxfile._SEEN.clear()
    study_identity.hashed(files)
    calls = []
    real = sqxfile._hashed
    monkeypatch.setattr(sqxfile, "_hashed", lambda text: calls.append(1) or real(text))
    [sqxfile.identity(f) for f in files]
    assert calls == []


# ---------------------------------------------------------------- 7.2b


def synthetic(
    name: str, rows: int, close: list[str], size: float | int, ticket: bool, seed: int
) -> pd.DataFrame:
    """Seeded synthetic trades of one strategy."""
    rng = np.random.default_rng(seed)
    t = pd.date_range("2024-01-01", periods=rows, freq="h")
    frame = pd.DataFrame(
        {
            "Type": rng.choice(["Buy", "Sell"] if name[-1] != "5" else ["Buy"], rows),
            "Open time": t,
            "Open price": rng.normal(100, 1, rows),
            "Size": np.full(rows, size),
            "Close time": t + pd.Timedelta(minutes=30),
            "Close price": rng.normal(100, 1, rows),
            "Profit/Loss": rng.normal(0, 50, rows),
            "Balance": rng.normal(10000, 100, rows),
            "Sample type": "IS",
            "Close type": rng.choice(close, rows),
            "MAE ($)": rng.normal(0, 5, rows),
            "MFE ($)": rng.normal(0, 5, rows),
        }
    )
    if ticket:
        frame["Ticket"] = np.arange(rows)
    return frame.assign(strategy=name)


def export(
    tmp: Path, specs: dict[str, dict], monkeypatch: pytest.MonkeyPatch, label: str
) -> Path:
    """An export folder as `export_trades` leaves it, packed from synthetic per-strategy frames."""
    frames = {n: synthetic(n, seed=int(n[1:]), **s) for n, s in specs.items()}
    monkeypatch.setattr(
        tradestore,
        "_prepared",
        lambda path, per_market: (
            frames[path.stem],
            "Ticket" in frames[path.stem],
            False,
        ),
    )
    src = tmp / f"csv_{label}"
    src.mkdir(parents=True)
    files = []
    for n in specs:
        (src / f"{n}.csv").write_text("x")
        files.append(src / f"{n}.csv")
    out = tmp / label
    out.mkdir(parents=True)
    tradepack.WORKERS = 2
    packed = tradepack.pack(files, out / "trades.parquet", per_market=False)
    (out / "timeframes.csv").write_text(
        "strategy,timeframe\n" + "".join(f"{n},H1\n" for n in specs)
    )
    (out / "identity.csv").write_text(
        "strategy,identity\n" + "".join(f"{n},id_{n}\n" for n in specs)
    )
    (out / "lineage.csv").write_text(
        "strategy,identity,mother\n" + "".join(f"{n},id_{n},id_{n}\n" for n in specs)
    )
    manifest.write(out, {"project": "P"}, "cmd", {**packed, "timeframes": ["H1"]})
    return out


NORMAL = {
    f"S{i}": dict(
        rows=40 + i,
        close=["SL", "TP"] + (["TS"] if i == 2 else []),
        size=0.1 * (i + 1),
        ticket=False,
    )
    for i in range(1, 7)
}


def cut(
    tmp: Path, specs: dict, drop: list[str], monkeypatch: pytest.MonkeyPatch
) -> tuple[str, Path, Path]:
    """(refilter's answer, the filtered folder, the fresh export of the survivors)."""
    old = export(tmp, specs, monkeypatch, "old/2026-10-10")
    kept = {n: s for n, s in specs.items() if n not in drop}
    fresh = export(tmp, kept, monkeypatch, "fresh")
    monkeypatch.setattr(aftercut, "export_dir", lambda p, d, day: old.parent / "x")
    say = aftercut.refilter("P", "D", {n: f"id_{n}" for n in specs}, set(kept))
    return say, old, fresh


def test_refilter_gives_what_a_fresh_export_of_the_cut_databank_gives(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Refiltering an export equals packing the cut databank afresh."""
    say, old, fresh = cut(
        tmp_path, NORMAL, ["S2", "S5"], monkeypatch
    )  # S2 holds the only "TS", S5 only Buy
    assert say
    a, b = (
        pd.read_parquet(old / "trades.parquet"),
        pd.read_parquet(fresh / "trades.parquet"),
    )
    assert_frame_equal(a, b)
    assert (
        a["Close type"].cat.categories.tolist()
        == b["Close type"].cat.categories.tolist()
        == ["SL", "TP"]
    )
    import pyarrow.parquet as pq

    assert (
        pq.read_schema(old / "trades.parquet").remove_metadata()
        == pq.read_schema(fresh / "trades.parquet").remove_metadata()
    )
    for f in ("timeframes.csv", "identity.csv", "lineage.csv"):
        assert (old / f).read_bytes() == (fresh / f).read_bytes()
    ma, mb = manifest.read(old)["counts"], manifest.read(fresh)["counts"]
    assert {k: v for k, v in ma.items() if k != "cut_from"} == mb and ma[
        "cut_from"
    ] == 6


def test_refilter_leaves_the_export_alone_when_it_cannot_guarantee(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Refilter declines when its result could differ from a fresh pack."""
    # the only survivors without Ticket: a fresh pack has no such column, the cut would keep an empty one
    ticket = {**NORMAL, "S1": {**NORMAL["S1"], "ticket": True}}
    say, old, fresh = cut(tmp_path, ticket, ["S1"], monkeypatch)
    assert say == "" and len(pd.read_parquet(old / "trades.parquet")) > len(
        pd.read_parquet(fresh / "trades.parquet")
    )
    # whole-number sizes in every survivor, a fractional one in the dropped: a fresh pack types Size int64
    ints = {n: {**s, "size": 1} for n, s in NORMAL.items()}
    ints["S6"] = {**ints["S6"], "size": 0.5}
    tmp2 = tmp_path / "two"
    tmp2.mkdir()
    say, old, fresh = cut(tmp2, ints, ["S6"], monkeypatch)
    assert (
        say == ""
        and str(pd.read_parquet(fresh / "trades.parquet")["Size"].dtype) == "int64"
    )
    assert str(pd.read_parquet(old / "trades.parquet")["Size"].dtype) == "float64"


def test_refilter_wants_the_export_to_be_of_these_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Refilter declines an export made of other files or an empty cut."""
    old = export(tmp_path, NORMAL, monkeypatch, "old/2026-10-10")
    monkeypatch.setattr(aftercut, "export_dir", lambda p, d, day: old.parent / "x")
    before = {n: f"id_{n}" for n in NORMAL}
    other = {**before, "S2": "another"}
    assert aftercut.refilter("P", "D", other, {"S1"}) == ""
    assert aftercut.refilter("P", "D", before, set()) == ""
    assert len(pd.read_parquet(old / "trades.parquet")) == sum(
        40 + i for i in range(1, 7)
    )


def test_trimmed_on_a_real_export_keeps_order_and_categories() -> None:
    """Trimming a real export keeps row order and categories."""
    real = sorted(
        Path.home().glob("Desktop/AlgoData/raw/*/*/*/trades.parquet"),
        key=lambda p: p.stat().st_size,
    )
    if not real:
        pytest.skip("no export on disk")
    frame = pd.read_parquet(real[len(real) // 2])
    names = list(dict.fromkeys(frame["strategy"].astype(str)))
    keep = set(names[::2])
    t0 = time.perf_counter()
    sub = aftercut._trimmed(frame, keep)
    print(
        f"\n_trimmed {len(frame)} rows in {time.perf_counter() - t0:.3f}s -> {'declined' if sub is None else len(sub)}"
    )
    if sub is not None:
        want = frame[frame["strategy"].astype(str).isin(keep)].reset_index(drop=True)
        for c in tradestore.CATEGORICAL:
            if c in sub:
                assert sub[c].cat.categories.tolist() == sorted(
                    set(want[c].astype(str))
                )
                want[c] = pd.Categorical(
                    want[c].astype(str), categories=sub[c].cat.categories
                )
        assert_frame_equal(sub, want)


def test_refilter_survives_an_export_retest_manifest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A manifest without `kept_ticket` / `torn_blocks` (`export_retest`'s) is cut, not a KeyError."""
    old = export(tmp_path, NORMAL, monkeypatch, "old/2026-10-10")
    doc = manifest.read(old)
    doc["counts"].pop("kept_ticket", None)
    doc["counts"].pop("torn_blocks", None)
    manifest.write(old, doc["source"], doc["command"], doc["counts"])
    monkeypatch.setattr(aftercut, "export_dir", lambda p, d, day: old.parent / "x")
    kept = {n for n in NORMAL if n != "S1"}
    assert aftercut.refilter("P", "D", {n: f"id_{n}" for n in NORMAL}, kept)
    assert manifest.read(old)["counts"]["strategies"] == len(kept)


def test_apply_verdict_wires_trades_fresh_and_a_failing_refilter_never_interrupts_the_cut(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    """`apply(trades_fresh=True)` calls `refilter` once; if it raises the cut stands and its record is written; unset it is not called."""
    import pipeline.autopilot.judge as judge

    files = sqx_copies(tmp_path, 3)
    bank = files[0].parent
    csv = tmp_path / "verdict.csv"
    ids = apply_verdict.hashed(files)
    csv.write_text(
        "strategy,verdict,identity\n"
        + "".join(
            f"{f.stem},{apply_verdict.DROP if f.stem == 'S000' else 'KEEP'},{ids[f]}\n"
            for f in files
        )
    )
    calls: list[tuple] = []
    kept_copy = (bank / "S000.sqx").read_bytes()

    def boom(*a: object) -> str:
        """A refilter that fails after the files are gone."""
        calls.append(a)
        raise KeyError("torn_blocks")

    monkeypatch.setattr(aftercut, "refilter", boom)
    monkeypatch.setattr(apply_verdict, "databank_dir", lambda p, d, install=None: bank)
    monkeypatch.setattr(apply_verdict, "report_dir", lambda p, d, day: tmp_path / "rep")
    monkeypatch.setattr(apply_verdict, "is_up", lambda role: False)
    monkeypatch.setattr(apply_verdict.live, "mine", lambda role: False)
    out = apply_verdict.apply("P", "D", csv, "custodian", trades_fresh=True)
    assert len(calls) == 1 and out["removed"] == 1 and out["after"] == 2
    assert (
        out["out"] / "manifest.json"
    ).exists() and "refilter failed" in capsys.readouterr().out
    calls.clear()
    (bank / "S000.sqx").write_bytes(kept_copy)  # the dropped file back for a second cut
    apply_verdict.apply("P", "D", csv, "custodian")
    assert calls == []
    monkeypatch.setattr(
        judge.state, "status", lambda p, b: {"pieces": {"trades": {"state": "fresh"}}}
    )
    assert judge.trades_fresh("P", "D") is True
    monkeypatch.setattr(
        judge.state, "status", lambda p, b: {"pieces": {"trades": {"state": "stale"}}}
    )
    assert judge.trades_fresh("P", "D") is False
