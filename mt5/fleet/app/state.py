"""The fleet as rows: each account's beat, its floors and the light the window paints."""

from collections.abc import Sequence

from mt5.fleet.app import floors, history, progress, read, risk, rules

SILENT, RED, YELLOW, GREEN, UNKNOWN = "silent", "red", "yellow", "green", "unknown"
ORDER = [SILENT, RED, YELLOW]
_SWITCHES = [
    ("connected", "Desconectado"),
    ("autotrading", "AutoTrading apagado"),
    ("account_trade_allowed", "Cuenta sin permiso de operar"),
    ("account_trade_expert", "Cuenta sin permiso para EAs"),
]


def reasons(
    beat: dict, floor: dict | None, now: int, extra: Sequence[tuple[str, str]] = ()
) -> list[tuple[str, str]]:
    """Every reason an account is not green, worst first, as (level, Spanish text).

    Args:
        beat: FleetBeacon's JSON.
        floor: `floors.reading()`, or None for an account with no plan in machine.yaml.
        now: UTC epoch seconds.
        extra: Reasons from `risk.reasons` and `rules.reasons`, which the caller has computed.

    Returns:
        Silence first, then the red ones (a floor close, then `extra`'s reds in the order given),
        then the yellow ones; empty when there is nothing to say.
    """
    out = []
    age = now - beat["written_gmt"]
    if age > read.CFG["silence_s"]:
        out.append((SILENT, f"Calla {_age(age)}"))
    near = [
        name
        for name, key in (("diario", "daily_left"), ("total", "max_left"))
        if floor and floor[key] < read.CFG["red_margin_left"]
    ]
    if near:
        out.append((RED, "Cerca del suelo " + " y del ".join(near)))
    out += list(extra)
    out += [(YELLOW, text) for key, text in _SWITCHES if not beat[key]]
    return sorted(out, key=lambda r: ORDER.index(r[0]))


def light(
    beat: dict, floor: dict | None, now: int, extra: Sequence[tuple[str, str]] = ()
) -> tuple[str, str]:
    """An account's light and the Spanish words beside it: its worst reason, or green when it has none."""
    found = reasons(beat, floor, now, extra)
    if found:
        return found[0]
    return (GREEN, "Operando") if floor else (UNKNOWN, "Sin plan en machine.yaml")


def _age(seconds: int) -> str:
    """A span in the largest unit that reads well: 40 s, 12 min, 3 h, 2 d."""
    for size, unit in ((86400, "d"), (3600, "h"), (60, "min")):
        if seconds >= size:
            return f"{seconds // size} {unit}"
    return f"{seconds} s"


def rows(now: int) -> list[dict]:
    """One row per account that has a beat on disk.

    Args:
        now: UTC epoch seconds, against which a beat's silence is measured.

    Returns:
        Dicts of `beat`, `stage` (or None), `floor` (or None), `risk` (`risk.reading`), `deals`
        (`history.deals`, None until the collector writes them), `progress` (`progress.reading`,
        None without a plan or deals), `reasons` (every one, worst first), `light`, `text` (the
        worst reason), `age` (Spanish), `doubts`: the Spanish lines saying which of its figures
        rest on an unconfirmed rule.
    """
    zones, unconfirmed = read.clocks()
    out = []
    for beat in read.beats():
        stage = read.stage(beat["login"])
        floor, doubts, extra, prog = None, [], [], None
        deals = history.deals(beat["login"])
        if stage:
            zone = zones.get(stage["firm"])
            floor = floors.reading(beat, stage, zone)
            if zone is None:
                doubts.append(
                    "El catálogo no trae el reloj ni la base de la pérdida diaria de esta "
                    "firma: se lee el día del servidor y la base de Hantec."
                )
            elif stage["firm"] in unconfirmed or "daily_loss_basis" in stage["flags"]:
                doubts.append(
                    "El reloj y la base de la pérdida diaria de esta firma están sin "
                    "confirmar en el catálogo."
                )
            extra = rules.reasons(beat, stage, now + floors.server_offset(beat))
            if deals is not None:
                prog = progress.reading(
                    beat,
                    stage,
                    read.terms(stage["plan_key"], stage["phase"]),
                    deals,
                    zone,
                )
        stops = risk.reading(beat, floor)
        extra = risk.reasons(stops) + extra
        found = reasons(beat, floor, now, extra)
        code, text = light(beat, floor, now, extra)
        out.append(
            {
                "beat": beat,
                "stage": stage,
                "floor": floor,
                "risk": stops,
                "deals": deals,
                "progress": prog,
                "reasons": found,
                "light": code,
                "text": text,
                "age": _age(max(now - beat["written_gmt"], 0)),
                "doubts": doubts,
            }
        )
    return out
