"""Step 26 as an autopilot action: every refusal of the preflight, and the loop over a stubbed job."""

import copy
import json
import shutil
import sys
from collections.abc import Callable
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import assetdata, sqxfile  # noqa: E402
from core.paths import DATA  # noqa: E402
from mt5.verify import autopilot, firms, pool  # noqa: E402
from ui.daemon.mt5bridge import runs  # noqa: E402

PROJECT = "Test_USDJPY_donchianUpperCrossUp_H1"
MOTHERS = DATA / "structural" / PROJECT / "mothers"
# The real check of each strategy (2026-09-30), which the stubbed job copies as its own.
REAL = {"Strategy 16.9.76": "20260930-141713_Strategy_16_9_76",     # FTMO pass, Hantec fail
        "Strategy 21.9.59": "20260930-141929_Strategy_21_9_59",     # fail on both
        "Strategy 10.9.72": "20260930-142145_Strategy_10_9_72"}     # FTMO pass, Hantec fail
REAL_RUNS = pool.RUNS
PARAMS = {"start": "2022-06-01", "end": "2026-09-24", "model": "ohlc_m1",
          "firms": ["ftmo", "hantec"]}
ACCOUNTS = {"ftmo": {"login": 111, "server": "FTMO-Test"},
            "hantec": {"login": 222, "server": "Hantec-Test"}}


def finalist(name: str) -> dict:
    """A finalist as the autopilot hands it, described from its real file."""
    file = MOTHERS / f"{name}.sqx"
    return {"strategy": name, "identity": sqxfile.identity(file), "mother": name,
            "sqx": str(file), "symbol": "USDJPY", "timeframe": "H1"}


FINALISTS = [finalist(n) for n in REAL]


@pytest.fixture(autouse=True)
def free(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A free conductor, a closed terminal, two saved accounts; no install or terminal is
    probed, and the register and the checks live in a temp folder."""
    monkeypatch.setattr(runs.advance, "busy", lambda role, project, own_log=False: [])
    monkeypatch.setattr(runs.wine, "terminal_running", lambda: False)
    for module in (runs, firms, autopilot):
        monkeypatch.setattr(module, "MT5_ACCOUNTS", ACCOUNTS)
    monkeypatch.setattr(pool, "ROOT", tmp_path / "pool")
    monkeypatch.setattr(pool, "RUNS", tmp_path / "verify")


def stub(crash_on: str = "") -> Callable[[list[str], Path], int]:
    """A job that leaves the real check of its strategy on disk, as a new run, or crashes."""
    calls = []

    def job(argv: list[str], log: Path) -> int:
        """Copy run.json and result.json of the strategy's real check under a new run name."""
        file = Path(argv[argv.index("--strategy") + 1])
        calls.append(argv)
        run = f"2026100{len(calls)}-000000_{file.stem.replace(' ', '_').replace('.', '_')}"
        (pool.RUNS / run).mkdir(parents=True)
        meta = json.loads((REAL_RUNS / REAL[file.stem] / "run.json").read_text(encoding="utf-8"))
        meta.update({"run": run, "file": str(file.resolve())})
        if file.stem == crash_on:
            meta = {**meta, "state": "failed", "error": "SQX rechazó `action=start`"}
        else:
            shutil.copy(REAL_RUNS / REAL[file.stem] / "result.json", pool.RUNS / run)
        (pool.RUNS / run / "run.json").write_text(json.dumps(meta), encoding="utf-8")
        return 1 if file.stem == crash_on else 0

    job.calls = calls
    return job


def reasons(finalists: list[dict], params: dict) -> str:
    """The refusal's reasons as one text; the check must not be ok."""
    got = autopilot.check(PROJECT, finalists, params)
    assert not got["ok"] and got["reasons"]
    return "\n".join(got["reasons"])


def test_everything_given_and_free_is_ok_and_says_what_runs() -> None:
    """The confirmation names every strategy, the conductor and each firm's account."""
    got = autopilot.check(PROJECT, FINALISTS, PARAMS)
    assert got == {"ok": True, "reasons": [], "text": got["text"]}
    for piece in (*REAL, "conductor", "SQX_w1", "FTMO: cuenta 111 en FTMO-Test",
                  "Hantec: cuenta 222 en Hantec-Test", "ohlc_m1", "2022-06-01", "2026-09-24",
                  "3 estrategias", "pool"):
        assert piece in got["text"], piece


@pytest.mark.parametrize("key", ["start", "end", "model", "firms"])
def test_each_missing_parameter_is_a_refusal_not_a_default(key: str) -> None:
    """Dates, model and firms are the owner's each time."""
    for params in ({k: v for k, v in PARAMS.items() if k != key}, {**PARAMS, key: ""}):
        assert f"falta «{key}»" in reasons(FINALISTS, params)


def test_the_windows_own_refusals() -> None:
    """A wrong model, an inverted window, a firm with no saved account, nothing to verify."""
    assert "elige el modelo del tester" in reasons(FINALISTS, {**PARAMS, "model": "ticks"})
    assert "acaba antes de empezar" in reasons(FINALISTS, {**PARAMS, "start": "2027-01-01"})
    assert "sin cuenta guardada: the5ers" in reasons(FINALISTS, {**PARAMS, "firms": ["the5ers"]})
    assert "no hay estrategia que verificar" in reasons([], PARAMS)
    assert autopilot.check(PROJECT, FINALISTS, {**PARAMS, "start": "MT5"})["ok"]


def test_a_busy_conductor_and_an_open_terminal_refuse(monkeypatch: pytest.MonkeyPatch) -> None:
    """Said once, however many finalists there are."""
    monkeypatch.setattr(runs.advance, "busy", lambda role, project, own_log=False:
                        ["install ocupado: el puerto 5060 de SQX_w1 responde"])
    monkeypatch.setattr(runs.wine, "terminal_running", lambda: True)
    got = autopilot.check(PROJECT, FINALISTS, PARAMS)["reasons"]
    assert got.count("install ocupado: el puerto 5060 de SQX_w1 responde") == 1
    assert sum("el terminal de MT5 está abierto" in r for r in got) == 1 and len(got) == 2


def test_a_missing_symbol_or_commission_is_a_reason(monkeypatch: pytest.MonkeyPatch) -> None:
    """Neither the firm's symbol nor its commission is ever guessed."""
    real = assetdata.load

    def without(*keys: str) -> Callable[[str], dict]:
        """The asset's card with hantec taken out of `mt5` or of the commission's brokers."""
        def load(symbol: str) -> dict:
            """The real card, edited on a copy."""
            data = copy.deepcopy(real(symbol))
            if "mt5" in keys:
                del data["mt5"]["hantec"]
            if "commission" in keys:
                data["costs"]["commission"]["brokers"]["hantec"]["value"] = None
            return data
        return load

    monkeypatch.setattr(assetdata, "load", without("mt5"))
    assert "USDJPY no tiene símbolo de Hantec" in reasons(FINALISTS, PARAMS)
    monkeypatch.setattr(assetdata, "load", without("commission"))
    got = reasons(FINALISTS, PARAMS)
    assert "USDJPY no tiene comisión confirmada de Hantec" in got and "FTMO" not in got


def test_a_finalist_that_is_not_its_file_is_a_reason(tmp_path: Path) -> None:
    """A missing file, a missing key, another identity or timeframe than the file's."""
    one = FINALISTS[0]
    assert "no existe" in reasons([{**one, "sqx": str(tmp_path / "x.sqx")}], PARAMS)
    assert "le falta mother" in reasons([{k: v for k, v in one.items() if k != "mother"}], PARAMS)
    assert "la finalista dice" in reasons([{**one, "identity": "0" * 64}], PARAMS)
    assert "la finalista dice" in reasons([{**one, "timeframe": "H4"}], PARAMS)


def test_run_records_every_verdict_and_goes_on_past_a_fail(tmp_path: Path,
                                                           monkeypatch: pytest.MonkeyPatch) -> None:
    """3 finalists × 2 firms: six rows; 21.9.59 validates nowhere and the loop still ends."""
    job = stub()
    monkeypatch.setattr(autopilot, "job", job)
    line = autopilot.run(PROJECT, FINALISTS, PARAMS, tmp_path / "paso-26")
    assert len(job.calls) == 3
    assert job.calls[0] == ["-m", "mt5.verify.run", "--strategy", FINALISTS[0]["sqx"], "--from",
                            "2022-06-01", "--to", "2026-09-24", "--model", "ohlc_m1",
                            "--firms", "ftmo,hantec"]
    assert "FTMO 2 de 3" in line and "Hantec 0 de 3" in line and line.startswith("3 verificadas")
    assert len(pool.history("ftmo")) == 3 and len(pool.history("hantec")) == 3
    assert set(pool.read("ftmo")["strategy"]) == {"Strategy 16.9.76", "Strategy 10.9.72"}
    assert pool.read("hantec").empty
    row = pool.history("ftmo").iloc[0]
    assert (row["project"], row["mother"]) == (PROJECT, "Strategy 16.9.76")
    assert row["identity"] == FINALISTS[0]["identity"] and row["run"].startswith("20261001-")
    seen = (tmp_path / "paso-26" / "verificados.csv").read_text(encoding="utf-8")
    assert seen.count("\n") == 7


def test_run_stops_on_a_crashed_job_and_keeps_what_was_done(tmp_path: Path,
                                                            monkeypatch: pytest.MonkeyPatch) -> None:
    """The second job crashes: the first finalist is in the register, the third never runs."""
    job = stub(crash_on="Strategy 21.9.59")
    monkeypatch.setattr(autopilot, "job", job)
    with pytest.raises(SystemExit) as stop:
        autopilot.run(PROJECT, FINALISTS, PARAMS, tmp_path / "paso-26")
    assert "Strategy 21.9.59 se cayó (código 1): SQX rechazó" in str(stop.value)
    assert len(job.calls) == 2 and list(pool.history("ftmo")["strategy"]) == ["Strategy 16.9.76"]


def test_run_refuses_before_any_job_when_the_preflight_does(tmp_path: Path,
                                                            monkeypatch: pytest.MonkeyPatch) -> None:
    """The same preflight again at launch, as the window does."""
    job = stub()
    monkeypatch.setattr(autopilot, "job", job)
    monkeypatch.setattr(runs.wine, "terminal_running", lambda: True)
    with pytest.raises(SystemExit) as stop:
        autopilot.run(PROJECT, FINALISTS, PARAMS, tmp_path / "paso-26")
    assert "no se lanza" in str(stop.value) and job.calls == [] and not pool.ROOT.exists()


def test_the_job_passes_its_exit_code_and_logs(tmp_path: Path) -> None:
    """The real launcher on a harmless command: output in the log, the code returned."""
    log = tmp_path / "job.log"
    assert autopilot.job(["-c", "import sys; print('hola'); sys.exit(3)"], log) == 3
    assert log.read_text(encoding="utf-8").strip() == "hola"
