"""The EAs an account should carry against the ones mounted and the magics that actually trade."""
import re

from mt5.fleet.app import floors, history, read

STRATEGY = re.compile(r"(\d+)[._ ](\d+)[._ ](\d+)")


def strategy_key(text: str) -> str:
    """A strategy's name as «3.23.151», whether it is written «Strategy 3.23.151», «Strategy_3_23_151» or bare."""
    m = STRATEGY.search(text)
    return ".".join(m.groups()) if m else text


def activity(trades: list[dict], positions: list[dict]) -> tuple[dict[str, int], dict[int, int]]:
    """What the account's own trades say about its magics.

    Args:
        trades: `history.trades()` of the account.
        positions: The beat's open positions.

    Returns:
        The magic each strategy name's comment appears under, and the last server epoch each
        magic traded (opening or closing).
    """
    linked, last = {}, {}
    for t in trades:
        linked[strategy_key(t["comment"])] = t["magic"]
        last[t["magic"]] = max(last.get(t["magic"], 0), t["open"], t["close"] or 0)
    for p in positions:
        linked[strategy_key(p["comment"])] = p["magic"]
        last[p["magic"]] = max(last.get(p["magic"], 0), p["time"])
    return linked, last


def compare(sheet: list[dict] | None, charts: list[dict] | None, trades: list[dict],
            positions: list[dict], register: dict[int, str], server_now: int) -> list[dict]:
    """One row per strategy the account should carry, carries, or trades, with what is wrong with it.

    Args:
        sheet: `read.sheet()` — what the owner's workbook expects; None when it has no sheet.
        charts: The beat's `charts[]` (symbol, period, expert); None on a schema-1 beat.
        trades: `history.trades()` of the account.
        positions: The beat's open positions.
        register: This firm's `{magic: strategy}` from the reconciler; empty while it has none.
        server_now: The server clock's epoch.

    Returns:
        Rows of `strategy`, `symbol`, `tf`, `expected` and `mounted` (None when unknown), `magic`,
        `last` (server epoch of its last trade, None for none) and `flags`: Spanish texts, none
        when all is well.
    """
    expected = {(strategy_key(e["strategy"]), e["tf"]): e for e in sheet or []}
    mounted = {(strategy_key(c["expert"]), c["period"]): c for c in charts or []}
    linked, last = activity(trades, positions)
    by_name = {strategy_key(s): m for m, s in register.items()}
    rows = []
    for key, tf in sorted(expected.keys() | mounted.keys()):
        src = expected.get((key, tf)) or mounted[(key, tf)]
        magic = linked.get(key, by_name.get(key))
        rows.append({"strategy": key, "symbol": src["symbol"], "tf": tf, "magic": magic,
                     "expected": None if sheet is None else (key, tf) in expected,
                     "mounted": None if charts is None else (key, tf) in mounted})
    seen = {r["magic"] for r in rows}
    rows += [{"strategy": register.get(m, f"magic {m}"), "symbol": "", "tf": "", "magic": m,
              "expected": None, "mounted": None} for m in sorted(last.keys() - seen)]
    for r in rows:
        r["last"] = last.get(r["magic"])
        r["flags"] = flags(r, register, server_now)
    return rows


def flags(row: dict, register: dict[int, str], server_now: int) -> list[str]:
    """What is wrong with one row of `compare`, in Spanish."""
    out = []
    if row["expected"] and row["mounted"] is False:
        out.append("esperada y no montada")
    if row["mounted"] and row["expected"] is False:
        out.append("montada y no esperada")
    if register and row["magic"] is not None and row["magic"] not in register:
        out.append("magic sin registrar")
    if row["last"] and (server_now - row["last"]) / 86400 > read.CFG["silent_strategy_days"]:
        out.append(f"sin operar hace {(server_now - row['last']) // 86400} d")
    return out


def account_view(row: dict, now: int) -> dict:
    """One account's deployment as the Despliegue tab shows it.

    Args:
        row: A `state.rows` row.
        now: UTC epoch seconds.

    Returns:
        `notes` (Spanish lines on what could not be read: no sheet in the workbook, a schema-1
        beacon, no history yet) and `rows` (`compare()`).
    """
    beat, stage = row["beat"], row["stage"]
    sheet_name = stage["excel"] if stage else None
    sheet = read.sheet(sheet_name) if sheet_name else None
    register = {m: s for (f, m), s in read.names().items() if stage and f == stage["firm"]}
    trades = history.trades(row["deals"]) if row["deals"] is not None else []
    notes = []
    if sheet is None:
        notes.append("sin hoja en el Excel: no se sabe qué EAs debería llevar")
    if "charts" not in beat:
        notes.append("el servicio de la VPS es de la versión 1: recárgalo para ver qué EAs hay montados")
    if row["deals"] is None:
        notes.append("falta el historial de la cuenta (lo envía el servicio de la versión 2: recárgalo en la VPS): no se ven los magics ni las últimas operaciones")
    if not read.names():
        notes.append("aún no hay registro de magics del reconciliador: no se puede comprobar el magic de cada EA")
    return {"notes": notes, "rows": compare(sheet, beat.get("charts"), trades, beat["positions"], register,
                                            now + floors.server_offset(beat))}
