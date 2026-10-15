"""The fleet guard on a planted beat: one notification on the crossing into red, none while it stays red, re-armed by green."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from core import fleetpaths
from mt5.fleet import guard
from mt5.fleet.app import read

GMT = 1790979700
OFFSET = 10800
STAGE = {
    "size": 10000.0,
    "daily_loss": 0.05,
    "max_loss": 0.10,
    "max_loss_mode": "static",
    "daily_basis": "balance",
    "firm": "FTMO",
}


def plant(root: Path, equity: float, written: int = GMT) -> None:
    """Write a schema-1 beat for login 5 whose balance is 10000."""
    beat = {
        "login": 5,
        "written_gmt": written,
        "server_time": written + OFFSET,
        "day_start": GMT - 4900 + OFFSET,
        "balance": 10000.0,
        "equity": equity,
        "positions": [],
        "deals_today": [],
        "connected": 1,
        "autotrading": 1,
        "account_trade_allowed": 1,
        "account_trade_expert": 1,
    }
    (root / "live").mkdir(exist_ok=True)
    (root / "live" / "5.json").write_text(json.dumps(beat), encoding="utf-8")


@pytest.fixture
def fleet(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A scratch fleet root with login 5 on a 10k FTMO stage; the real catalogue is not read."""
    monkeypatch.setattr(fleetpaths, "FLEET", tmp_path)
    monkeypatch.setattr(read, "stage", lambda login: STAGE)
    return tmp_path


def test_cross_stay_rearm(fleet: Path) -> None:
    """Red notifies once, stays quiet while red, and notifies again after a green pass."""
    sent = []
    notify = lambda title, body: sent.append((title, body))
    plant(fleet, 9900.0)  # 80 % of the daily allowance left: green
    assert guard.run(notify, GMT) == [] and sent == []
    plant(fleet, 9300.0)  # 14 % left of the daily floor: red
    assert guard.run(notify, GMT) == ["5"] and len(sent) == 1
    assert "diario" in sent[0][1]
    assert guard.run(notify, GMT + 60) == [] and len(sent) == 1  # still red
    plant(fleet, 9900.0)
    assert guard.run(notify, GMT + 120) == [] and len(sent) == 1  # green: re-armed
    plant(fleet, 9300.0)
    assert guard.run(notify, GMT + 180) == ["5"] and len(sent) == 2


def test_silence_fires_once(fleet: Path) -> None:
    """An account silent over 300 s notifies once."""
    sent = []
    plant(fleet, 9900.0)
    assert guard.run(lambda t, b: sent.append(b), GMT + 301) == ["5"]
    assert "Calla" in sent[0]
    assert guard.run(lambda t, b: sent.append(b), GMT + 400) == [] and len(sent) == 1


def plant2(root: Path) -> None:
    """Login 6 in red beside login 5."""
    beat = json.loads((root / "live" / "5.json").read_text())
    (root / "live" / "6.json").write_text(json.dumps({**beat, "login": 6}))


def test_failed_notification_retries(fleet: Path) -> None:
    """A notification that fails leaves the account armed for the next pass."""
    plant(fleet, 9300.0)

    def boom(title: str, body: str) -> None:
        """A notifier that cannot reach the bus."""
        raise OSError("no bus")

    assert guard.run(boom, GMT) == []
    assert guard.run(lambda t, b: None, GMT + 60) == ["5"]


def test_one_failing_login_does_not_stop_the_others(fleet: Path) -> None:
    """The notifier raises for login 5; login 6 is still notified and 5 retries next pass."""
    plant(fleet, 9300.0)
    plant2(fleet)
    sent = []

    def only_six(title: str, body: str) -> None:
        """Fails for login 5."""
        if "5" in title:
            raise FileNotFoundError("notify-send")
        sent.append(title)

    assert guard.run(only_six, GMT) == ["6"] and len(sent) == 1
    assert guard.run(lambda t, b: None, GMT + 60) == ["5"]
