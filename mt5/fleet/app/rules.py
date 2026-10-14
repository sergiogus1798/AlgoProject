"""The rules a funded stage forbids — holding over the weekend, trading around news — against the open positions."""

from mt5.fleet.app import fmt, read
from mt5.newsfilter import windows
from mt5.newsfilter.firms import FIRMS

HIGH = 3
# A firm with no profile in `FIRMS` is read with Hantec's (every HIGH release, 3 min), as the catalogue says.
FALLBACK = "hantec"


def profile(firm: str) -> tuple[dict, str]:
    """The firm's news profile and the note on where its prohibition comes from."""
    if firm == "ftmo":
        return FIRMS["ftmo"], ""
    if firm == "hantec":
        return FIRMS["hantec"], " (sólo calendario MT5)"
    return FIRMS[FALLBACK], " (según catálogo)"


def weekend(positions: list[dict], server_now: int) -> list[tuple[str, str]]:
    """Reasons for each position that is too close to, or past, its symbol's Friday close.

    Args:
        positions: Beat positions of schema 2 (`friday_close`, server epoch, 0 when none).
        server_now: The server clock's epoch.

    Returns:
        (level, Spanish text) pairs: yellow within `weekend_yellow_h` of the close, red within
        `weekend_red_h` or past it.
    """
    out = []
    for p in positions:
        if not p["friday_close"]:
            continue
        left = (p["friday_close"] - server_now) / 3600
        if left <= read.CFG["weekend_red_h"]:
            when = (
                "ya pasó el cierre"
                if left <= 0
                else f"cierra en {fmt.span(left * 3600)}"
            )
            out.append(("red", f"Fin de semana: {p['symbol']} sigue abierta y {when}"))
        elif left <= read.CFG["weekend_yellow_h"]:
            out.append(
                (
                    "yellow",
                    f"Fin de semana: {p['symbol']} sigue abierta, cierra en {fmt.span(left * 3600)}",
                )
            )
    return out


def moving(item: dict, firm: dict) -> list[str]:
    """The firm's currency tags a calendar release belongs to: every HIGH one, or those on its list."""
    if firm["events"] is None:
        return [item["currency"]] if item["importance"] == HIGH else []
    key = f"{item['country']}:{item['code']}"
    return [tag for tag, keys in firm["events"].items() if key in keys]


def news(
    positions: list[dict],
    releases: list[dict],
    firm: dict,
    server_now: int,
    note: str = "",
) -> list[tuple[str, str]]:
    """Reasons for each release that moves an open position's symbol and is inside or near the firm's window.

    Args:
        positions: Beat positions.
        releases: The beat's `news[]` (server epoch `time`).
        firm: A profile of `mt5.newsfilter.firms.FIRMS`.
        server_now: The server clock's epoch.
        note: Appended to the text, saying where the prohibition comes from.

    Returns:
        (level, text): red from the firm's window before the release to the same after it, yellow
        up to `news_yellow_min` minutes before.
    """
    out = []
    for r in releases:
        minutes = (r["time"] - server_now) / 60
        tags = moving(r, firm)
        if not -firm["rule_minutes"] <= minutes <= read.CFG["news_yellow_min"]:
            continue
        for p in positions:
            if not any(windows.moves(p["symbol"], t, firm) for t in tags):
                continue
            level = "red" if minutes <= firm["rule_minutes"] else "yellow"
            when = f"en {fmt.span(minutes * 60)}" if minutes > 0 else "ahora mismo"
            out.append(
                (level, f"Noticia «{r['name']}» {when} mueve {p['symbol']}{note}")
            )
    return out


def reasons(beat: dict, stage: dict, server_now: int) -> list[tuple[str, str]]:
    """The rule reasons of one account: nothing when its stage allows both, or the beat is schema 1."""
    if beat.get("schema", 1) < 2:
        return []
    out = []
    firm, note = profile(stage["firm"])
    if not stage["news_ok"]:
        out += news(beat["positions"], beat["news"], firm, server_now, note)
    if not stage["weekend_ok"]:
        out += weekend(beat["positions"], server_now)
    return out
