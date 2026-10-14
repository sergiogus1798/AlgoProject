"""The day's equity curve of one account: minute rows, the service's hourly extremes, the two floors."""

from mt5.fleet.app import floors, history


def data(beat: dict, floor: dict) -> dict | None:
    """What the chart draws, on the server's clock.

    Args:
        beat: FleetBeacon's JSON.
        floor: `floors.reading()`; its `day_start` is the firm's day, which can begin before the
            server's midnight, so up to two parquet days are read.

    Returns:
        `times` and `equity` (the collector's minutes since the firm's day began), `hours`
        (`start`, `low`, `high` of the beat's `hours[]` since then), `daily_floor`, `max_floor`,
        `start` (the firm's day start) and `now` (the beat's server time); None when neither the
        minute history nor `hours[]` has anything.
    """
    start = floor["day_start"] + floors.server_offset(beat)
    frame = history.minutes(beat["login"], [start, beat["server_time"]])
    mins = frame[frame["server_time"] >= start] if frame is not None else None
    hours = [h for h in beat.get("hours", []) if h["start"] >= start]
    if (mins is None or mins.empty) and not hours:
        return None
    return {
        "times": [] if mins is None else mins["server_time"].tolist(),
        "equity": [] if mins is None else mins["equity"].tolist(),
        "hours": hours,
        "daily_floor": floor["daily_floor"],
        "max_floor": floor["max_floor"],
        "start": start,
        "now": beat["server_time"],
    }
