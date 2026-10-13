#!/usr/bin/env python3
"""`membank.take` hands an `.abk` over only when it is this databank's, and whole.

Covers (finished, same strategies, newer than the files) and adds the
data mode, the identities, a corrupt file, and `run` replacing only the banks it names. The `.abk`
files come from the struct writer of `test_perf66_algobank.py` (imported, not copied).
"""

import copy
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import bankfile, bankframes, sqxfile  # noqa: E402
from sqx.export import membank  # noqa: E402
from tests.test_perf66_algobank import SILVER, strategies, write  # noqa: E402

WRITTEN = 1_760_000_000.0          # the writer's fixed written_ms, in seconds


@pytest.fixture
def folder(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """The bank folder redirected under tmp_path."""
    monkeypatch.setattr(membank, "bank_dir", lambda project, role: tmp_path)
    return tmp_path


def _ids(bank: list[dict]) -> dict[str, str]:
    """File stem -> identity of each strategy, as the harvest computes it."""
    return {s["name"]: sqxfile._hashed(s["xml"]) for s in bank}


def test_take(folder: Path, capsys: pytest.CaptureFixture) -> None:
    """A dump is taken and stays for the next reader; every way of not being this databank's gives None and one line."""
    bank = strategies()
    write(folder / "R.abk", bank)
    ids = _ids(bank)
    ok = membank.take("P", "x", "R", ids, "main")
    assert ok is not None and sorted(ok["names"]) == sorted(ids)
    assert capsys.readouterr().out == "" and (folder / "R.abk").exists()     # stays for the bank's other reader
    assert membank.take("P", "x", "R", ids, "main") is not None
    bad = {"wrong data mode": (ids, "all"),
           "name missing in the file": ({**ids, "Strategy 9": "z"}, "main"),
           "name extra in the file": ({k: v for k, v in ids.items() if k != "Strategy 3.3.3"}, "main"),
           "one identity differs": ({**ids, "Strategy 2.1.1": "0"}, "main")}
    for case, (i, data) in bad.items():
        write(folder / "R.abk", bank)
        assert membank.take("P", "x", "R", i, data) is None, case
        assert len(capsys.readouterr().out.splitlines()) == 1, case


def test_take_refuses_missing_and_corrupt(folder: Path) -> None:
    """No file, a truncated file and a flipped byte are all None."""
    assert membank.take("P", "x", "R", {}, "main") is None
    write(folder / "R.abk", strategies())
    raw = bytearray((folder / "R.abk").read_bytes())
    raw[40] ^= 1
    (folder / "R.abk").write_bytes(raw)
    assert membank.take("P", "x", "R", _ids(strategies()), "main") is None
    (folder / "R.abk").write_bytes(bytes(raw[:50]))
    assert membank.take("P", "x", "R", _ids(strategies()), "main") is None


def test_unbound_binds_trades_to_the_sqx_result(folder: Path) -> None:
    """Count and net profit of the main result's filled orders; any other number names the first strategy."""
    write(folder / "R.abk", strategies())
    bank = bankfile.load(folder / "R.abk")
    ok = {"Strategy 2.1.1": {10: {"NumberOfTrades": 2, "NetProfit": 715.585}}}
    assert bankframes.unbound(bank, {**ok, "Strategy 10.4.7": {10: {"NumberOfTrades": 1, "NetProfit": 190.5}},
                                     "Strategy 3.3.3": {10: {"NumberOfTrades": 0, "NetProfit": 0.0}}}, 10) == ""
    full = {**ok, "Strategy 10.4.7": {10: {"NumberOfTrades": 1, "NetProfit": 190.5}},
            "Strategy 3.3.3": {10: {"NumberOfTrades": 0, "NetProfit": 0.0}}}
    for case, stats in {"other costs": {**full, "Strategy 2.1.1": {10: {"NumberOfTrades": 2, "NetProfit": 700.0}}},
                        "other count": {**full, "Strategy 2.1.1": {10: {"NumberOfTrades": 3, "NetProfit": 715.585}}},
                        "other block": {**full, "Strategy 2.1.1": {20: ok["Strategy 2.1.1"][10]}},
                        "no stats": {k: v for k, v in full.items() if k != "Strategy 3.3.3"}}.items():
        assert bankframes.unbound(bank, stats, 10).startswith(("Strategy 2.1.1", "Strategy 3.3.3")), case


def test_taken_banks_asks_each_side_its_own_databank_in_main_mode(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """`taken_banks` with a role: IS reads the build databank, OOS the retest one, both as "main"; no role, no look."""
    import argparse
    from studies.screening.gate import harvest
    for d in ("Results", "OOS"):
        (tmp_path / d).mkdir()
        (tmp_path / d / "S0.sqx").write_bytes(b"x")
    asked = []
    monkeypatch.setattr(harvest, "databank_dir", lambda p, d, install: tmp_path / d)
    monkeypatch.setattr(harvest.collect, "identities", lambda files: {f: "id" for f in files})
    monkeypatch.setattr(harvest.membank, "take", lambda *a: asked.append(a) or a[2])
    a = argparse.Namespace(project="P", databank="Results", oos_databank="OOS", role="custodian")
    assert harvest.taken_banks(a, tmp_path) == {"IS": "Results", "OOS": "OOS"}
    assert asked == [("P", "custodian", "Results", {"S0": "id"}, "main"), ("P", "custodian", "OOS", {"S0": "id"}, "main")]
    a.role = None
    assert harvest.taken_banks(a, tmp_path) == {} and len(asked) == 2


def test_run_keeps_the_first_modes_files(folder: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Two data modes mean two task runs; the second must not wipe what the first wrote."""
    modes = []
    monkeypatch.setattr(membank.toolproject, "cfx", lambda role: folder)
    monkeypatch.setattr(membank.install, "pending", lambda role: [])
    monkeypatch.setattr(membank.live, "call", lambda role, action, **kw: modes.append(kw["xmlConfig"]))

    def fake_run(role: str, project: str, config: str) -> str:
        """The snippet: writes the banks of the last call's mode, then _done.tsv."""
        banks = modes[-1].split("|")[1].split(";") if "|" in modes[-1] else []
        for b in banks:
            write(folder / f"{b}.abk", strategies()[:2])
        (folder / "_done.tsv").write_text("done\n")
        return "end"

    monkeypatch.setattr(membank.live, "run", fake_run)
    monkeypatch.setattr(membank.live, "records", lambda role, project: {"A": 2, "B": 2})
    monkeypatch.setattr(membank.toolproject, "settings", lambda snippet, args: args)
    (folder / "Other.abk").write_bytes(b"keep")
    assert membank.run("x", "P", {"A": "main", "B": "all"}) == {"A": 2, "B": 2}
    assert len(modes) == 2 and (folder / "A.abk").exists() and (folder / "Other.abk").read_bytes() == b"keep"


def _world(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, taken: set, skew: float = 0.0) -> tuple:
    """`collect.tables` over two sides of two fake strategies, SQX and the file readers faked."""
    from core import bankfile, exportdrv
    from studies.screening.gate import collect
    from tests.test_perf66_algobank import _csv, strategies, write
    bank, calls, real = strategies()[:2], {"jvm": 0, "pack": 0}, bankfile.pack
    other = copy.deepcopy(bank)          # the OOS databank: same strategies, other money
    other[0]["orders"][0]["pl"] += 1000.0
    tmp_path.mkdir(); write(tmp_path / "b.abk", bank); write(tmp_path / "o.abk", other)
    st = lambda n, p: {10: {"NumberOfTrades": n, "NetProfit": p}}       # noqa: E731
    stats = {"IS": {"Strategy 2.1.1": st(2, 715.585), "Strategy 10.4.7": st(1, 190.5)},
             "OOS": {"Strategy 2.1.1": st(2, 1715.585 + skew), "Strategy 10.4.7": st(1, 190.5)}}
    sides = {s: [tmp_path / s / f"{b['name']}.sqx" for b in bank] for s in ("IS", "OOS")}
    [(f.parent.mkdir(exist_ok=True), f.write_bytes(b"x")) for fs in sides.values() for f in fs]
    def jvm(src: Path, out: Path, data: str = "main") -> None:
        """Fake `orderstocsv`: one CSV per staged file."""
        calls["jvm"] += 1
        out.mkdir(parents=True)
        for f in src.glob("*.sqx"):
            _csv(out / f"{f.stem}.csv", next(b for b in (other if f.stem.startswith("OOS__") else bank)
                                             if f.stem.endswith(b["name"])), {"XAUUSD": 2, "XAGUSD": 3})

    monkeypatch.setattr(exportdrv, "trades", jvm)
    monkeypatch.setattr(bankfile, "pack", lambda *a: calls.update(pack=calls["pack"] + 1) or real(*a))
    monkeypatch.setattr(collect, "identities", lambda files: {f: f"id-{f.parent.name}-{f.stem}" for f in files})
    monkeypatch.setattr(collect, "_read", lambda stem: (stats[stem.split("__")[0]][stem.split("__", 1)[1]], pd.Series([0.0, 1.0]), "H1", 2))
    monkeypatch.setattr(collect.fanout, "run", lambda fn, d, w: [(k, fn(k)) for k in d])
    monkeypatch.setattr(collect, "metrics", lambda g: (pd.DataFrame({"Strategy Name": list(g), "x": 1.0}), "(IS)"))
    return collect.tables(sides, tmp_path / "w", {s: tmp_path / "exp" / s for s in sides},
                          {s: bankfile.load(tmp_path / ("b.abk" if s == "IS" else "o.abk")) for s in taken}), calls


def test_two_taken_banks_harvest_as_orderstocsv_does(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Both sides taken: no JVM, same tables and counts; one side missing: both go by orderstocsv."""
    both, c_both = _world(tmp_path / "a", monkeypatch, {"IS", "OOS"})
    csv, c_csv = _world(tmp_path / "b", monkeypatch, set())
    half, c_half = _world(tmp_path / "c", monkeypatch, {"IS"})
    assert (c_both, c_csv, c_half) == ({"jvm": 0, "pack": 2}, {"jvm": 1, "pack": 0}, {"jvm": 1, "pack": 0})
    assert both["IS"]["trades"]["Profit/Loss"].sum() != both["OOS"]["trades"]["Profit/Loss"].sum()
    bad, c_bad = _world(tmp_path / "d", monkeypatch, {"IS", "OOS"}, skew=5.0)      # the .sqx says another net profit
    assert c_bad["jvm"] == 1 and bad["OOS"]["packed"] == csv["OOS"]["packed"]
    for got, side, k in [(g, s, k) for g in (both, half) for s in ("IS", "OOS") for k in ("metrics", "trades", "equity")]:
        pd.testing.assert_frame_equal(got[side][k], csv[side][k], check_exact=True, check_categorical=True)
        assert got[side]["packed"] == csv[side]["packed"]


def test_unbound_binds_every_market_of_an_all_bank(folder: Path) -> None:
    """In "all" mode each market's count and net are bound, not only the main one's; a market the .sqx lacks is refused."""
    write(folder / "R.abk", strategies(), data=1)
    bank = bankfile.load(folder / "R.abk")
    main = {"Strategy 2.1.1": {10: {"NumberOfTrades": 2, "NetProfit": 715.585}},
            "Strategy 10.4.7": {10: {"NumberOfTrades": 1, "NetProfit": 190.5}},
            "Strategy 3.3.3": {10: {"NumberOfTrades": 0, "NetProfit": 0.0}}}
    silver = {10: {"NumberOfTrades": 2, "NetProfit": -27.25}}

    def every(**change: dict) -> dict:
        """`sqxstats.every` of each strategy; the silver result of 10.4.7 may be replaced."""
        got = {n: {"Main: XAUUSD_M1/H1": s, "Portfolio": {}} for n, s in main.items()}
        got["Strategy 10.4.7"][SILVER] = change.get("silver", silver)
        return got
    assert bankframes.unbound(bank, main, 10, every()) == ""
    for case, got in {"one trade's P/L altered": every(silver={10: {"NumberOfTrades": 2, "NetProfit": -20.0}}),
                      "one trade dropped": every(silver={10: {"NumberOfTrades": 1, "NetProfit": -50.0}})}.items():
        why = bankframes.unbound(bank, main, 10, got)
        assert why.startswith(f"Strategy 10.4.7 ({SILVER})"), case
    no_silver = every()
    del no_silver["Strategy 10.4.7"][SILVER]
    assert "no tiene" in bankframes.unbound(bank, main, 10, no_silver)
    assert "varios mercados" in bankframes.unbound(bank, main, 10)
