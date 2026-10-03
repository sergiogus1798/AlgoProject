"""One account's distance to its daily and total floors, from one beat and its stage's rules."""
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from portfolio.funded.rules import floors

UTC = timezone.utc


def day_start(now: int, zone: str) -> int:
    """The UTC epoch at which a firm's daily-loss day containing `now` began.

    Args:
        now: UTC epoch seconds.
        zone: An IANA name, or "EETUS" for New York + 7 h (the NY-close server day).
    """
    shift = timedelta(hours=7) if zone == "EETUS" else timedelta(0)
    tz = ZoneInfo("America/New_York" if zone == "EETUS" else zone)
    local = datetime.fromtimestamp(now, tz).replace(tzinfo=None) + shift
    midnight = local.replace(hour=0, minute=0, second=0, microsecond=0) - shift
    return int(midnight.replace(tzinfo=tz).timestamp())


def server_offset(beat: dict) -> int:
    """Seconds the beat's server clock is ahead of UTC, to the half hour."""
    return round((beat["server_time"] - beat["written_gmt"]) / 1800) * 1800


def reading(beat: dict, stage: dict, zone: str | None) -> dict:
    """Where an account stands against its two floors at the moment of its beat.

    The day's starting balance is today's balance minus every deal booked since the firm's day
    began (balance operations included). A "max_be" floor needs the equity at that instant, which
    a schema-1 beat does not carry: it is exact only when no open position was carried over
    midnight. A schema-2 beat's `hours[]` has the balance and equity at the first sample of the
    firm's day-start hour, which makes both exact.

    Args:
        beat: FleetBeacon's JSON. Its deal and position times are on the server's clock.
        stage: `read.stage()` — `size`, `daily_loss`, `max_loss`, `max_loss_mode`, `daily_basis`.
        zone: The firm's daily-loss clock; None reads the day as the server's own midnight.

    Returns:
        `day_start` (UTC epoch), `start_balance`, `today` (equity minus the day's starting
        balance), `worst_today` (the day's lowest equity from `hours[]`, None without it),
        `daily_floor`, `daily_room` (account currency to the floor), `daily_left` (share of the
        allowance left), `max_floor`, `max_room`, `max_left`, and `approx`: the reasons, in
        Spanish, the daily figures are not exact — empty when they are.
    """
    offset = server_offset(beat)
    served = beat["day_start"] - offset
    start = day_start(beat["written_gmt"], zone) if zone else served
    since = [h for h in beat.get("hours", []) if h["start"] >= start + offset]
    first = next((h for h in since if h["start"] == start + offset), None)
    approx = []
    if first:
        b0, e0 = first["balance0"], first["equity0"]
        if beat["service_started"] > start + offset:
            approx.append("el servicio de la VPS arrancó después del inicio del día de la firma: "
                          "el equity de inicio es el de su primera lectura")
    else:
        closed = sum(d["profit"] + d["swap"] + d["commission"] + d["fee"]
                     for d in beat["deals_today"] if d["time"] - offset >= start)
        b0 = e0 = beat["balance"] - closed
        if start < served:
            approx.append("el latido sólo trae las operaciones desde la medianoche del servidor y el día "
                          "de la firma empezó antes: falta lo cerrado en ese tramo")
        if stage["daily_basis"] == "max_be" and any(p["time"] - offset < start for p in beat["positions"]):
            approx.append("el suelo diario parte del mayor entre balance y equity a medianoche, y hay "
                          "posiciones abiertas desde antes: el equity de medianoche no viene en el latido "
                          "(el servicio de la VPS de la versión 2 lo trae), se usa sólo el balance")
    size, equity = stage["size"], beat["equity"]
    if stage["max_loss_mode"] != "static":
        approx.append("el suelo total es móvil y su máximo histórico no viene en el latido")

    dfloor = floors.daily_floor(b0, e0, size, stage["daily_loss"], stage["daily_basis"])
    mfloor = floors.max_floor(stage["max_loss_mode"], size, stage["max_loss"], equity, beat["balance"])
    return {"day_start": start, "start_balance": b0, "today": equity - b0,
            "worst_today": min(h["low"] for h in since) if since else None,
            "daily_floor": dfloor, "daily_room": equity - dfloor,
            "daily_left": (equity - dfloor) / (b0 - dfloor),
            "max_floor": mfloor, "max_room": equity - mfloor,
            "max_left": (equity - mfloor) / (stage["max_loss"] * size),
            "approx": approx}
