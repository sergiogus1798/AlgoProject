"""Compare each firm's SQX retest with its MT5 backtest on the five rows of encargo 34, and judge.

One merged tab reads better than one per firm (owner, 2026-09-29 §3.7): a shared parameter
table, one P&L chart with every firm's pair of curves, and one verdict block per firm — tagged
`"firm"` so the window can show or hide a firm's own blocks and chart series when its light is
toggled, without asking the study to run again.
"""
from collections.abc import Callable

import pandas as pd

from core.study import blocks
from mt5 import compare
from mt5.verify import firms

MINUTES = {"M1": 1, "M5": 5, "M15": 15, "M30": 30, "H1": 60, "H4": 240, "D1": 1440}


def shifted(frame: pd.DataFrame, hours: int) -> pd.DataFrame:
    """The same trades with both times moved by whole hours."""
    out = frame.copy()
    for c in ("Open time", "Close time"):
        out[c] = pd.to_datetime(out[c]) + pd.Timedelta(hours=hours)
    return out


def clock(sqx: pd.DataFrame, mt5: pd.DataFrame, tolerance_min: float, max_h: int) -> int:
    """The whole-hour shift from SQX's feed clock to the firm's server clock that pairs most.

    SQX stamps its feed's zone (`knowhow/export/feed-clock-timezones.md`), MT5 its server's,
    and the two need not be the same zone nor change hour on the same day. The shift is read
    off the trades rather than assumed: most pairs within half the tolerance first — with a
    tolerance of one H1 bar a one-hour error still pairs everything, and greedy pairing can
    even find one pair more (🔬 2026-09-30: 376 pairs all 1 h off beat 375 exact ones) —
    then most pairs, then the smallest total entry gap, then the smaller shift.
    """
    if sqx.empty or mt5.empty:
        return 0
    scored = []
    for h in range(-max_h, max_h + 1):
        pairs = compare.pair(shifted(sqx, h), mt5, tolerance_min)
        hit = pairs.dropna(subset=["Open time_mt5"])
        gaps = (hit["Open time_mt5"] - hit["Open time"]).abs()
        close = int((gaps <= pd.Timedelta(minutes=tolerance_min / 2)).sum())
        scored.append((close, len(hit), -float(gaps.dt.total_seconds().sum()), -abs(h), h))
    return max(scored)[4]


def daily(frame: pd.DataFrame, deposit: float) -> pd.Series:
    """P&L per server day in % of the account, by the day a trade closed."""
    if frame.empty:
        return pd.Series(dtype=float)
    days = pd.to_datetime(frame["Close time"]).dt.normalize()
    return frame.groupby(days)["Profit/Loss"].sum() / deposit * 100


def max_dd(frame: pd.DataFrame, deposit: float) -> float:
    """Largest fall of the closed-trade balance from its high, in % of the account."""
    if frame.empty:
        return 0.0
    equity = deposit + frame.sort_values("Close time")["Profit/Loss"].cumsum()
    peak = equity.cummax().clip(lower=deposit)
    return float(((peak - equity) / peak).max() * 100)


def rows(sqx: pd.DataFrame, mt5: pd.DataFrame, pairs: pd.DataFrame, deposit: float,
         th: dict) -> list[dict]:
    """The five figures, each with its threshold and whether it passes.

    Returns:
        [{"row", "label", "value", "limit", "state", "note"}]. A figure that cannot be
        computed (no trades on one side, a constant series) fails: a check that could not
        be made has not been passed.
    """
    hit = pairs.dropna(subset=["Open time_mt5"])
    matched = len(hit) / len(pairs) if len(pairs) else None
    matched_mt5 = len(hit) / len(mt5) if len(mt5) else None
    losses = sqx.loc[sqx["Profit/Loss"] < 0, "Profit/Loss"].abs()
    r = float(losses.mean()) if len(losses) else None
    diff = hit["Profit/Loss_mt5"] - hit["Profit/Loss"]
    gap_r = float(diff.abs().mean()) / r if r and len(hit) else None
    a, b = daily(sqx, deposit), daily(mt5, deposit)
    days = a.index.union(b.index)
    a, b = a.reindex(days, fill_value=0.0), b.reindex(days, fill_value=0.0)
    corr = float(a.corr(b)) if len(days) > 2 and a.std() > 0 and b.std() > 0 else None
    mad = float((a - b).abs().mean()) if len(days) else None
    worst = (float(a.min()), float(b.min())) if len(days) else (None, None)
    worst_gap = abs(worst[0] - worst[1]) if len(days) else None
    dd = (max_dd(sqx, deposit), max_dd(mt5, deposit))
    dd_gap = abs(dd[0] - dd[1]) / max(dd) if max(dd) > 0 else (0.0 if len(days) else None)

    def one(row: str, label: str, value: float | None, limit: float, above: bool,
            note: str) -> dict:
        """One criterion: pass when the value sits on the right side of its limit."""
        ok = value is not None and (value >= limit if above else value <= limit)
        return {"row": row, "label": label, "value": value, "limit": limit,
                "state": "pass" if ok else "fail", "note": note}

    return [
        one("1", "operaciones de SQX emparejadas en MT5", matched, th["matched_min"], True,
            f"{len(hit)} de {len(pairs)} de SQX; de las {len(mt5)} de MT5, "
            f"{'—' if matched_mt5 is None else f'{matched_mt5:.0%}'} tienen pareja"),
        one("2", "diferencia media por operación emparejada, en R", gap_r,
            th["trade_gap_max_r"], False,
            "media de |P&L MT5 − P&L SQX| del movimiento de precio, al valor de punto fijo "
            f"del activo; R = la pérdida media de SQX ({'—' if r is None else f'{r:.2f}'} "
            f"USD): sin stop; sesgo {'—' if not len(hit) else f'{diff.mean():+.2f}'} USD"),
        one("3a", "correlación del P&L diario", corr, th["daily_corr_min"], True,
            f"{len(days)} días del servidor con alguna operación cerrada en un lado u otro"),
        one("3b", "diferencia media absoluta del P&L diario, % de la cuenta", mad,
            th["daily_mad_max_pct"], False, f"cuenta de {deposit:,.0f} USD"),
        one("4", "peor día: diferencia en puntos de %", worst_gap, th["worst_day_gap_max_pp"],
            False, "SQX {:.3f} %, MT5 {:.3f} %".format(*worst) if worst[0] is not None else
            "sin días"),
        one("5", "drawdown máximo: diferencia relativa", dd_gap, th["dd_rel_gap_max"], False,
            f"SQX {dd[0]:.3f} %, MT5 {dd[1]:.3f} % — sobre el balance al cerrar cada "
            "operación; el flotante intradía con M1 está pendiente"),
    ]


def firm_result(firm: str, sqx: pd.DataFrame, mt5: pd.DataFrame, timeframe: str, deposit: float,
                cfg: dict, symbol: str, instrument: dict, zones: tuple[str, str]) -> dict:
    """One firm's clock-aligned comparison: its verdict, its unpaired-trades table, its curves.

    Args:
        firm: Firm key, e.g. "ftmo".
        sqx, mt5: Every trade of each side, already inside the window.
        timeframe: For the entry tolerance, which is counted in bars.
        deposit: The account both sides start from.
        cfg: The whole config: `thresholds` and `clock`.
        symbol: The firm's symbol, for the verdict's note.
        instrument: The asset's tick size and point value: every row compares price moves at
            one point value (`compare.in_points`); USD is only shown.
        zones: (SQX feed's zone, the firm server's): SQX's times are moved trade by trade
            (`compare.to_zone`) before `clock` looks for any whole-hour shift left.

    Returns:
        {"verdict", "lonely", "summary", "pairs", "hours", "daily_sqx", "daily_mt5", "label"}
        — `pairs` and `hours` feed `sidebyside.table`, the daily pair the merged chart in
        `combined_chart`; `verdict` and `lonely` both carry
        `"firm": firm`, so the window can hide a firm's own blocks by its light.
    """
    th = cfg["thresholds"]
    sqx = compare.in_points(compare.to_zone(sqx, *zones), instrument)
    mt5 = compare.in_points(mt5, instrument)
    tolerance = th["entry_tolerance_bars"] * MINUTES[timeframe]
    hours = clock(sqx, mt5, tolerance, cfg["clock"]["max_offset_h"])
    moved = shifted(sqx, hours)
    pairs = compare.pair(moved, mt5, tolerance)
    got = rows(moved, mt5, pairs, deposit, th)
    ok = all(r["state"] == "pass" for r in got)
    failed = [r["row"] for r in got if r["state"] == "fail"]
    label = firms.label(firm)
    meaning = (f"{label} — SQX reproduce lo que el EA hace en su cuenta: el histórico largo de "
               "SQX vale para ella." if ok else
               f"{label} — falla{'n' if len(failed) > 1 else ''} la{'s' if len(failed) > 1 else ''} "
               f"fila{'s' if len(failed) > 1 else ''} {', '.join(failed)} de los criterios de "
               "aceptación: casi siempre es el reloj o un coste; se corrige y se compara una vez "
               "más, y si sigue fallando la estrategia no entra en el pool de esta empresa.")
    verdict = blocks.verdict("Validada" if ok else "No validada", "pass" if ok else "fail",
                             meaning, parts=[{"label": f"{r['row']} · {r['label']}",
                                              "state": r["state"], "value": r["value"],
                                              "note": f"límite {r['limit']} · {r['note']}"}
                                             for r in got])
    verdict = {**verdict, "firm": firm}
    lonely = pairs[pairs["Open time_mt5"].isna()][["Type", "Open time", "Close time",
                                                   "Profit/Loss USD"]].head(50)
    lonely = lonely.rename(columns={"Type": "tipo", "Open time": "apertura",
                                    "Close time": "cierre", "Profit/Loss USD": "P&L (USD)"})
    lonely_block = {**blocks.table(f"{label}: operaciones de SQX sin pareja en MT5 (hasta 50)",
                                   lonely.astype(str),
                                   f"{symbol}, {len(pairs) - len(pairs.dropna(subset=['Open time_mt5']))} "
                                   "sin pareja de " + str(len(pairs)) + "; si hay muchas y "
                                   "seguidas, mira el reloj o el historial de la empresa en "
                                   "esas fechas"), "firm": firm}
    summary = {"firm": firm, "state": "pass" if ok else "fail", "clock_h": hours,
               "sqx_trades": len(sqx), "mt5_trades": len(mt5),
               **{f"row_{r['row']}": r["value"] for r in got}}
    return {"verdict": verdict, "lonely": lonely_block, "summary": summary, "pairs": pairs,
            "hours": hours, "daily_sqx": daily(moved, deposit), "daily_mt5": daily(mt5, deposit),
            "label": label}


def combined_chart(pieces: dict[str, dict]) -> dict:
    """One P&L chart: every firm's SQX and MT5 daily curve, cumulative, on a shared day axis.

    Each firm's SQX leg is its own retest, priced at that firm's own conditions — not one
    shared SQX curve — so a firm's pair of series is labelled with its name on both legs.
    Every series carries `"firm"`, so the window can show or hide a firm's pair by its light.
    """
    days = sorted(set().union(*(set(p["daily_sqx"].index) | set(p["daily_mt5"].index)
                                for p in pieces.values()))) if pieces else []
    series = []
    for firm, p in pieces.items():
        a = p["daily_sqx"].reindex(days, fill_value=0.0).cumsum()
        b = p["daily_mt5"].reindex(days, fill_value=0.0).cumsum()
        series.append({"label": f"SQX · {p['label']}", "role": "real",
                       "values": [float(v) for v in a], "firm": firm})
        series.append({"label": f"MT5 · {p['label']}", "role": "sim",
                       "values": [float(v) for v in b], "firm": firm})
    return {"kind": "lines",
            "title": "P&L acumulado por día (hora del servidor), % de la cuenta, puntos a valor fijo",
            "unit": "%", "x": [d.strftime("%Y-%m-%d") for d in days], "series": series}


def params_table(baseline: dict, costs: dict[str, dict]) -> dict:
    """SQX's own default costs against what was actually read off each firm's account.

    Args:
        baseline: The asset's own default settings, `core.assetdata.sqx_settings(data, "build")`
            — the same shape as `costs`' values, whatever the asset's class (forex's one
            `spread` or a no_forex asset's per-segment `spread_is`/`spread_oos`/`spread_oos2`
            are already resolved by `sqx_settings`).
        costs: {firm: `conditions.for_sqx`'s settings dict}, only the firms that were priced.

    Returns:
        A "table" block, columns fixed to SQX | FTMO | Hantec — a firm not priced this run
        shows a dash, never a guess.
    """
    def col(get: Callable[[dict], str], firm: str) -> str:
        """One firm's formatted figure, or a dash when it was not priced this run."""
        return "—" if firm not in costs else get(costs[firm])

    rows_ = [
        ["spread (puntos SQX)", f"{baseline['defaultSpread']:g}",
         *[col(lambda c: f"{c['defaultSpread']:g}", f) for f in ("ftmo", "hantec")]],
        ["comisión", f"{baseline['commission']['method']} {baseline['commission']['value']:g}",
         *[col(lambda c: f"{c['commission']['method']} {c['commission']['value']:g}", f)
           for f in ("ftmo", "hantec")]],
        ["swap largo (puntos/noche)", f"{baseline['swap']['long']:g}",
         *[col(lambda c: f"{c['swap']['long']:g}", f) for f in ("ftmo", "hantec")]],
        ["swap corto (puntos/noche)", f"{baseline['swap']['short']:g}",
         *[col(lambda c: f"{c['swap']['short']:g}", f) for f in ("ftmo", "hantec")]],
        ["triple swap el", baseline["swap"]["triple_swap_on"].capitalize(),
         *[col(lambda c: c["swap"]["triple_swap_on"].capitalize(), f) for f in ("ftmo", "hantec")]],
        ["deslizamiento", f"{baseline['defaultSlippage']:g}",
         *[col(lambda c: f"{c['defaultSlippage']:g}", f) for f in ("ftmo", "hantec")]],
    ]
    frame = pd.DataFrame(rows_, columns=["parámetro", "SQX", "FTMO", "Hantec"])
    table = blocks.table("Parámetros de la comparación", frame,
                         "SQX: el default del activo (tramo build) en assets/. FTMO y Hantec: "
                         "leído en su cuenta en el momento de la verificación.")
    # Which column index is which firm's — the window drops a firm's column when its light is
    # off (§3.7 "su columna"); "SQX" and "parámetro" never toggle.
    table["firm_columns"] = {"ftmo": 2, "hantec": 3}
    return table
