"""The health of each terminal and of the VPS they run on, from the beats, the minute history and `vps.json`."""

from typing import Any

import pandas as pd

from mt5.fleet.app import fmt

DAY = 86400
# Lines of a terminal's log that match «failed» and are no fault: MT5's own Signals (copy trading)
# service asks the broker for its signal list every half hour, and a prop firm's server (FTMO)
# offers none. 📓 2026-10-04: `Signal '541350656': failed get list of signals` filled Salud.
NOISE = ("failed get list of signals",)


def disconnections(minutes: pd.DataFrame | None, since: int) -> tuple[int, int] | None:
    """How often and for how long the terminal was disconnected since a server epoch.

    Args:
        minutes: `history.minutes()`, None until the collector has written any.
        since: Server epoch to count from (the server's midnight).

    Returns:
        (episodes, minutes disconnected); None without history. Episodes are runs of consecutive
        rows with `connected` 0.
    """
    if minutes is None:
        return None
    today = minutes[minutes["server_time"] >= since]
    off = today["connected"].to_numpy() == 0  # pyright: ignore[reportAttributeAccessIssue]  # pandas/numpy stubs lose the type through indexing
    episodes = int((off & ~pd.Series(off).shift(fill_value=False).to_numpy()).sum())
    return episodes, int(off.sum())


def terminal(
    beat: dict, minutes: pd.DataFrame | None, vps: dict | None
) -> dict[str, Any]:
    """One terminal's row.

    Args:
        beat: FleetBeacon's JSON.
        minutes: The account's minute history of today, or None.
        vps: `vps.json`, or None.

    Returns:
        `connected`, `ping_ms`, `build`, `disconnections` (`disconnections()`), `uptime_s` (the
        service's, None on a schema-1 beat) and `errors`: the last lines of this terminal's log that
        carry an error, from the VPS's own reading (empty without one), `NOISE` left out.
    """
    mine = next(
        (
            t
            for t in (vps or {"terminals": []})["terminals"]
            if t["login"] == beat["login"]
        ),
        None,
    )
    return {
        "connected": bool(beat["connected"]),
        "ping_ms": beat["ping_us"] / 1000,
        "build": beat["build"],
        "disconnections": disconnections(minutes, beat["day_start"]),
        "uptime_s": beat["server_time"] - beat["service_started"]
        if "service_started" in beat
        else None,
        "errors": [e for e in mine["errors"] if not any(n in e for n in NOISE)]
        if mine
        else [],
    }


def machine(vps: dict | None) -> list[tuple[str, str]]:
    """The VPS's readings as (name, text) pairs, with their unit; empty until the collector has written `vps.json`."""
    if vps is None:
        return []
    return [
        (
            "RAM libre",
            f"{vps['ram_free_mb'] / 1024:.1f} de {vps['ram_total_mb'] / 1024:.1f} GB",
        ),
        ("CPU", fmt.pct(vps["cpu_pct"] / 100, 0)),
        ("Disco libre", f"{vps['disk_free_gb']:.0f} GB"),
        ("En marcha desde hace", fmt.span(vps["uptime_h"] * 3600)),
    ]
