"""Fleet guard: a critical desktop notification when an account crosses into red on a floor or on silence, window closed or open."""

import json
import os
import subprocess
import time
from collections.abc import Callable

from core import fleetpaths
from mt5.fleet.app import floors, read, state

REDS = (state.RED, state.SILENT)


def send(title: str, body: str) -> None:
    """Show a critical desktop notification; cron has no session bus, so the owner's is named."""
    env = {**os.environ}
    env.setdefault("DBUS_SESSION_BUS_ADDRESS", f"unix:path=/run/user/{os.getuid()}/bus")
    subprocess.run(
        ["notify-send", "--app-name=AlgoProject", "--urgency=critical", title, body],
        check=True,
        env=env,
    )


def red_reasons(beat: dict, now: int) -> list[str]:
    """The Spanish reasons an account is in red now: a floor under `red_margin_left`, or silence over `silence_s`."""
    stage = read.stage(beat["login"])
    floor = None
    if stage:
        zone = read.clocks()[0].get(stage["firm"])
        floor = floors.reading(beat, stage, zone)
    return [text for level, text in state.reasons(beat, floor, now) if level in REDS]


def crossings(
    before: dict[str, bool], reds: dict[str, list[str]]
) -> dict[str, list[str]]:
    """The accounts in red now that were not in red at the last pass; a login unseen before counts as green."""
    return {login: why for login, why in reds.items() if why and not before.get(login)}


def run(notify: Callable[[str, str], None] = send, now: int | None = None) -> list[str]:
    """One pass over `live/`: notify each account that crossed into red, keep the colours in `guard.json`.

    Read-only on the accounts: it reads the collector's copies and never touches an order.

    Args:
        notify: Called with a title and a body once per crossing.
        now: UTC epoch seconds; the clock when None.

    Returns:
        The logins notified.
    """
    now = int(time.time()) if now is None else now
    path = fleetpaths.FLEET / "guard.json"
    try:
        before = json.loads(path.read_text(encoding="utf-8"))
    except (
        json.JSONDecodeError,
        OSError,
    ):  # missing or corrupt: every login counts as green
        before = {}
    reds = {str(b["login"]): red_reasons(b, now) for b in read.beats()}
    fired = crossings(before, reds)
    sent: list[str] = []
    # A failed notification leaves the account green in the file, so the next minute retries it.
    after = {login: bool(why) and login not in fired for login, why in reds.items()}
    for login, why in fired.items():  # one failing notifier must not silence the others
        try:
            notify(f"Flota: cuenta {login} en rojo", "\n".join(why))
        except (FileNotFoundError, subprocess.CalledProcessError, OSError):
            continue  # stays not-red in the file: retried next minute
        after[login] = True
        sent.append(login)
    tmp = path.with_name(
        path.name + ".tmp"
    )  # atomic, as mt5.fleet.collect.write_json (which imports this module)
    tmp.write_text(json.dumps(after), encoding="utf-8")
    os.replace(tmp, path)
    return sent
