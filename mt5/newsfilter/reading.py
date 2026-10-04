"""What a firm's news rule costs one strategy: its EA in the Strategy Tester with the filter and without, trade by trade."""
import argparse
import json
import time

import pandas as pd

from core.paths import MT5_ACCOUNTS, MT5_DATA
from mt5.newsfilter import gaps, testerfile, windows
from mt5.newsfilter.firms import FIRMS
from mt5.verify import firms as verify_firms

OUT = MT5_DATA / "newsfilter-readings"
KEY = ["Type", "Open time"]
FATES = ["igual", "cerrada antes", "no abierta", "cambia por arrastre", "nueva por arrastre"]


def worst_day(trades: pd.DataFrame) -> dict:
    """The server day with the lowest closed P&L."""
    daily = trades.groupby(trades["Close time"].dt.normalize())["Profit/Loss"].sum()
    return {"day": str(daily.idxmin().date()), "pl": round(float(daily.min()), 2)}


def compare(plain: pd.DataFrame, filtered: pd.DataFrame, releases: pd.DataFrame, firm: dict) -> dict:
    """Pair the two runs by entry (side and open time) and name what the filter did to each trade.

    Args:
        plain, filtered: Trades of the EA without and with the filter (mt5.report.trades' shape).
        releases: The symbol's rows of the firm's tester file (windows.for_symbol).
        firm: One entry of firms.FIRMS.

    Returns:
        {"table": one row per trade of either run — its `fate` (FATES), the release responsible,
        both closes and both P&Ls; "summary": trades per fate and what each fate moved, the net
        result and the worst day of each run; "violations": windows.violations of the filtered
        run}. "cerrada antes" and "no abierta" are the filter acting on that very trade; the two
        "arrastre" fates are trades that differ only because an earlier one did.
    """
    told = windows.expected(plain, releases, firm)
    both = told.merge(filtered[KEY + ["Close time", "Profit/Loss"]], on=KEY, how="outer",
                      suffixes=("", " (filtro)"), indicator=True)
    paired, alone, new = both["_merge"] == "both", both["_merge"] == "left_only", both["_merge"] == "right_only"
    fate = pd.Series("cambia por arrastre", index=both.index)
    fate[paired & (both["Close time"] == both["Close time (filtro)"])] = "igual"
    fate[paired & (both["Close time (filtro)"] < both["Close time"]) & (both["fate"] == "cut")] = "cerrada antes"
    fate[alone & (both["fate"] == "blocked")] = "no abierta"
    fate[new] = "nueva por arrastre"
    table = both.drop(columns=["fate", "cut_at", "_merge"]).assign(fate=fate).sort_values("Open time", ignore_index=True)
    moved = table["Profit/Loss (filtro)"].fillna(0) - table["Profit/Loss"].fillna(0)
    by_fate = {f: {"trades": int((table["fate"] == f).sum()), "pl_change": round(float(moved[table["fate"] == f].sum()), 2)}
               for f in FATES}
    net = [round(float(t["Profit/Loss"].sum()), 2) for t in (plain, filtered)]
    summary = {"trades": [len(plain), len(filtered)], "net": net, "net_change": round(net[1] - net[0], 2),
               "worst_day": [worst_day(plain), worst_day(filtered)], "by_fate": by_fate,
               "releases_in_span": int(releases["time"].between(plain["Open time"].min(), plain["Close time"].max()).sum())}
    return {"table": table, "summary": summary, "violations": windows.violations(filtered, releases, firm)}


def model_for(a: argparse.Namespace) -> tuple[str, str]:
    """The tester model when none was named: real ticks if the firm's server has them, else M1 bars.

    Asks the server (terminal opened on the firm's account) for the ticks of each of the
    window's first seven days until one answers; tick history, once it starts, runs to today.

    Returns:
        (a key of mt5.tester.MODELS, the reason in Spanish).
    """
    from mt5 import live, wine
    OUT.mkdir(parents=True, exist_ok=True)
    probe = OUT / "ticks_probe.csv"
    for n in range(7):
        day = pd.Timestamp(a.start) + pd.Timedelta(days=n)
        got = live.ask("ticks", {"symbol": a.symbol, "start": f"{day:%Y-%m-%d}", "out": wine.windows(probe),
                                 "end": f"{day + pd.Timedelta(days=1):%Y-%m-%d}"}, MT5_ACCOUNTS.get(a.firm))
        probe.unlink(missing_ok=True)
        if got["rows"]:
            return "real_ticks", f"el servidor tiene ticks de {a.symbol} el {day:%Y-%m-%d} ({got['rows']})"
    return "ohlc_m1", f"el servidor no tiene ticks de {a.symbol} en la primera semana del tramo"


def backtest(expert: str, a: argparse.Namespace, tag: str) -> pd.DataFrame:
    """One tester pass, waited for. Closes the terminal first, as mt5.verify does: the tester needs it closed."""
    from mt5 import tester, wine
    if not wine.close_terminal():
        raise SystemExit("el terminal de MT5 sigue abierto y el tester no arranca con él")
    started = tester.start(expert, a.symbol, a.timeframe, a.start, a.end, a.model, a.deposit,
                           a.leverage, MT5_ACCOUNTS.get(a.firm), tag)
    cfg = verify_firms.config()["mt5"]  # as mt5.verify: ticks models are far slower, past the limit the run is given up
    minutes = cfg["ticks_max_minutes" if a.model in ("real_ticks", "every_tick") else "max_minutes"]
    deadline = time.monotonic() + minutes * 60
    while True:
        time.sleep(10)
        got = tester.collect(started["run"])
        if got["state"] == "done":
            h = got["summary"]
            print(f"{expert}: calidad del histórico {h['history_quality_pct']} %, empezó el "
                  f"{h['start_actual']}" + (f" (se pidió {h['start_asked']})" if h["start_changed"] else ""))
            return pd.read_parquet(got["trades_file"])
        if got["state"] == "no_report":
            raise SystemExit(f"{expert}: {got['hint']}")
        if time.monotonic() > deadline:
            wine.close_terminal()
            raise SystemExit(f"{expert}: el tester no acabó en {minutes} min")


def show(summary: dict, violations: pd.DataFrame, label: str) -> None:
    """The reading, in the owner's language."""
    n, net, worst = summary["trades"], summary["net"], summary["worst_day"]
    for g in summary.get("excluded", []):
        print(f"excluido {g['start']} -> {g['end']} ({g['days']} días sin velas M1 en el servidor): "
              f"{g['trades'][0]} operaciones sin filtro, {g['trades'][1]} con filtro")
    print(f"\n{'':<24}{'sin filtro':>14}{'con filtro ' + label:>22}")
    print(f"{'operaciones':<24}{n[0]:>14}{n[1]:>22}")
    print(f"{'resultado neto':<24}{net[0]:>14.2f}{net[1]:>22.2f}   diferencia {summary['net_change']:+.2f}")
    print(f"{'peor día':<24}{worst[0]['pl']:>14.2f}{worst[1]['pl']:>22.2f}   ({worst[0]['day']} / {worst[1]['day']})")
    print(f"\npublicaciones restringidas dentro del tramo: {summary['releases_in_span']}")
    for f in FATES:
        print(f"  {f:<22}{summary['by_fate'][f]['trades']:>5} operaciones   {summary['by_fate'][f]['pl_change']:>+10.2f}")
    print(f"\nincumplimientos del run con filtro: {len(violations)}" + ("" if violations.empty else "\n" + violations.to_string()))


def main() -> None:
    """CLI: python3 -m mt5.newsfilter.reading <firm> <name> --symbol S --timeframe TF --from D --to D --deposit N --leverage L [--model M]."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("firm", choices=sorted(FIRMS))
    ap.add_argument("name", help="la estrategia tal como la dejó mt5.newsfilter.run, p. ej. Strategy_3_48_75")
    ap.add_argument("--symbol", required=True, help="el símbolo de la firma en MT5")
    ap.add_argument("--timeframe", required=True)
    ap.add_argument("--from", dest="start", required=True, help="YYYY-MM-DD")
    ap.add_argument("--to", dest="end", required=True, help="YYYY-MM-DD")
    ap.add_argument("--model", choices=["every_tick", "ohlc_m1", "real_ticks"],
                    help="por defecto real_ticks si el servidor de la firma tiene ticks en el tramo, ohlc_m1 si no")
    ap.add_argument("--deposit", required=True, type=float)
    ap.add_argument("--leverage", required=True, type=int)
    a = ap.parse_args()
    firm = FIRMS[a.firm]
    target = testerfile.common_files() / testerfile.name(firm)
    assert target.exists(), f"falta {target}: python3 -m mt5.newsfilter.testerfile {a.firm}"
    if a.model:
        print(f"modelo del probador: {a.model} (pedido con --model)")
    else:
        a.model, why = model_for(a)
        print(f"modelo del probador: {a.model} — {why}")
    folder = f"AlgoProject\\{firm['label']}\\{a.name}"
    plain = backtest(f"{folder}_NoNews.ex5", a, a.firm)
    filtered = backtest(f"{folder}_{firm['label']}.ex5", a, a.firm)
    thin = gaps.stretches(gaps.thin_days(gaps.agent_log().read_bytes().decode("utf-16"),
                                         f"{a.name}_{firm['label']}"))
    (plain, cut_plain), (filtered, cut_filtered) = gaps.outside(plain, thin), gaps.outside(filtered, thin)
    got = compare(plain, filtered, windows.for_symbol(testerfile.read(target), a.symbol, firm), firm)
    got["summary"]["excluded"] = [{"start": str(g.start.date()), "end": str(g.end.date()), "days": g.days,
                                   "trades": [cut_plain[i], cut_filtered[i]]} for i, g in enumerate(thin.itertuples())]
    out = OUT / f"{a.name}_{a.firm}_{a.symbol}_{a.timeframe}_{a.start}_{a.end}_{a.model}"
    out.mkdir(parents=True, exist_ok=True)
    got["table"].to_parquet(out / "trades.parquet")
    got["violations"].to_parquet(out / "violations.parquet")
    (out / "summary.json").write_text(json.dumps(got["summary"], indent=1, ensure_ascii=False))
    show(got["summary"], got["violations"], firm["label"])
    print(f"\n-> {out}")


if __name__ == "__main__":
    main()
