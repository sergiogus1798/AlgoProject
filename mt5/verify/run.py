#!/usr/bin/env python3
"""Step 26: one strategy in SQX at each prop firm's conditions against its MT5 backtest on that firm's account."""
import argparse
import json
import re
import signal
import time
import zipfile
from datetime import date, datetime
from pathlib import Path

from core import assetdata, sqxfile
from core.paths import MT5_DATA
from core.study import result as study_result
from ledger import record, study as ledger_study
from mt5 import compare, tester, wine
from mt5.verify import conditions, firms, judge, mt5side, report, sidebyside, sqxside
from sqx.projects import mt5verify
from ui.daemon.launch.run import assets as rule_five, graceful

RUNS = MT5_DATA / "verify"
FALLBACK = 4        # years before Hasta when no server says how deep its history goes


def say(pct: int, line: str) -> None:
    """One progress line for the window's job strip."""
    study_result.progress(pct, line)


def identify(strategy: Path) -> tuple[str, str]:
    """The asset and timeframe a strategy trades, from its own file.

    Returns:
        (asset, timeframe). The asset is the file's symbol as `assets/symbols/` names it —
        the check prices and retests on that asset's feed, whatever feed the file was built
        on; a symbol no asset file declares stops here.
    """
    name, rest = sqxfile.symbol(strategy)
    timeframe = rest.rsplit("_", 1)[-1]
    if name not in assetdata.symbols():
        raise SystemExit(f"{strategy.name} opera {name}, que no tiene ficha en assets/symbols/")
    if timeframe not in judge.MINUTES:
        raise SystemExit(f"{strategy.name}: timeframe «{timeframe}» no reconocido")
    return name, timeframe


def segments(data: dict, window: tuple[str, str]) -> str:
    """Which of the asset's segments the window reads, for the ledger row: «oos1+oos2»."""
    got = []
    for seg in ("build", "oos1", "oos2"):
        try:
            a, b = assetdata.window(data, seg)
        except (ValueError, KeyError):
            continue
        if mt5verify._ms(window[0], False) < b and mt5verify._ms(window[1], True) > a:
            got.append(seg)
    return "+".join(got) or "fuera"


def capital(cfx: Path, member: str) -> float:
    """The initial capital the SQX retest starts from, which the MT5 tester is given too."""
    with zipfile.ZipFile(cfx) as z:
        found = re.search(r"<InitialCapital>([\d.]+)</InitialCapital>", z.read(member).decode())
    return float(found.group(1)) if found else 100000.0


def earliest(start: str, end: str, depth: dict, data: dict) -> str:
    """The window's first day: as typed, or with «mt5» the deepest history all firms share.

    Args:
        start: YYYY-MM-DD, or "mt5".
        end: YYYY-MM-DD, the last day.
        depth: Firm → the day of its server's first monthly bar (`conditions.read`), or None.
        data: The asset, whose `data.from` is where SQX's own feed begins.

    Returns:
        The latest of the firms' first bars and SQX's first day, so every side has bars;
        `runs.HISTORY_FALLBACK_YEARS` before `end` when no firm answered. Printed either way.
    """
    if start != "mt5":
        return start
    found = [d for d in depth.values() if d]
    if not found:
        got = date.fromisoformat(end).replace(year=date.fromisoformat(end).year - FALLBACK)
        print(f"Desde: ningún servidor dijo su histórico; {FALLBACK} años antes de Hasta, "
              f"{got}", flush=True)
        return got.isoformat()
    got = max(found + [str(data["data"]["from"])[:10]])
    print("Desde: " + ", ".join(f"{firms.label(f)} tiene barras desde {d}" for f, d in
                                depth.items()) + f"; SQX desde {str(data['data']['from'])[:10]}"
          f" -> {got}", flush=True)
    if date.fromisoformat(got) >= date.fromisoformat(end):
        raise SystemExit(f"la historia común empieza el {got}, después de Hasta")
    return got


def main() -> None:
    """Price each firm, retest in SQX, backtest in MT5, compare, and write the result."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--strategy", type=Path, required=True, help="the .sqx to verify")
    ap.add_argument("--from", dest="start", required=True,
                    help="YYYY-MM-DD, the first day; «mt5»: the deepest history every firm's "
                         "server holds (owner, 2026-09-29 §3.2)")
    ap.add_argument("--to", dest="end", required=True, help="YYYY-MM-DD, the last day")
    ap.add_argument("--model", required=True, choices=sorted(tester.MODELS),
                    help="the MT5 tester's model — chosen each time, never a default")
    ap.add_argument("--firms", default="", help="comma-separated firm keys; all saved if empty")
    ap.add_argument("--set", action="append", default=[], help="section.key=value")
    a = ap.parse_args()
    started = time.time()
    cfg = firms.config(a.set)
    if a.start != "mt5" and date.fromisoformat(a.start) >= date.fromisoformat(a.end):
        raise SystemExit("la ventana acaba antes de empezar")
    strategy = a.strategy.resolve()
    asset, timeframe = identify(strategy)
    sizing = mt5verify.own_sizing(strategy)      # both sides trade it (owner, 2026-09-29)
    data = assetdata.load(asset)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    run_id = f"{stamp}_{re.sub(r'[^A-Za-z0-9]+', '_', strategy.stem)}"
    work = RUNS / run_id
    work.mkdir(parents=True, exist_ok=True)
    meta = {"run": run_id, "strategy": strategy.stem, "file": str(strategy),
            "identity": sqxfile.identity(strategy), "asset": asset, "timeframe": timeframe,
            "from": a.start, "to": a.end, "model": a.model, "state": "running",
            "started": datetime.now().isoformat(timespec="seconds")}
    (work / "run.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")

    say(2, f"comprobando {asset} (regla 5)")
    rule_five(asset)

    wanted = [f for f in a.firms.split(",") if f]
    refused, costs, notes, leverage, depth = {}, {}, {}, {}, {}
    for firm, row in firms.usable(asset).items():
        if wanted and firm not in wanted:
            continue
        if row["why"]:
            refused[firm] = row["why"]
            continue
        say(5, f"leyendo {row['symbol']} en la cuenta de {firm} ({row['account']['server']})")
        try:
            info = conditions.read(row["symbol"], row["account"])
            costs[firm], notes[firm] = conditions.for_sqx(data, firm, info, cfg["sqx"]["slippage"])
            leverage[firm], depth[firm] = info["account_leverage"], info["first_bar"]
        except conditions.Refused as why:
            refused[firm] = str(why)
    wine.close_terminal()
    for firm, why in refused.items():
        print(f"⚠️ {firm}: {why}", flush=True)
    if not costs:
        report.finish(work, meta, cfg, started, {}, refused, "ninguna empresa se pudo preparar")
        raise SystemExit("ninguna empresa se pudo preparar: " + " | ".join(refused.values()))

    window = (earliest(a.start, a.end, depth, data), a.end)
    meta["from"] = window[0]
    project = f"Test_MT5Verify_{asset}_{timeframe}_{stamp[9:]}"
    role = cfg["role"]
    say(10, f"creando {project} en el {role}")
    built = sqxside.build(project, strategy, asset, timeframe, role, cfg["sqx"]["donor_members"])
    cfx = Path(built["cfx"])
    mq5_dir = work / "mq5"
    mq5_dir.mkdir(exist_ok=True)
    done = mt5verify.configure(cfx, data["sqx_symbol"], window, costs, mq5_dir, cfg["sqx"],
                               sizing)
    deposit = capital(cfx, done["tasks"][0]["member"])
    outputs = {t["firm"]: t["output"] for t in done["tasks"]}
    try:
        folders = sqxside.run(project, role, strategy, work, outputs, cfg["sqx"])
        say(55, "exportando las operaciones de SQX")
        sqx_trades = sqxside.firm_trades(folders, work)
    finally:
        print(sqxside.retire(project, role), flush=True)

    found = sorted(mq5_dir.glob("*.mq5"))
    if not found:
        raise SystemExit(f"SQX no escribió el .mq5 en {mq5_dir}: la tarea «{done['export']}» "
                         f"no exportó (generador «{cfg['sqx']['generator']}»)")
    say(60, f"compilando {found[0].name}")
    ea = mt5side.compile_ea(found[0], f"V{stamp[9:]}_{strategy.stem}", sizing["params"]["Size"])

    mt5_trades, reports = {}, {}
    usable = firms.usable(asset)
    for i, firm in enumerate(costs):
        say(65 + 25 * i // len(costs), f"backtest en MT5 en la cuenta de {firm}")
        got = mt5side.backtest(ea["expert"], usable[firm]["symbol"], timeframe, window, a.model,
                               deposit, leverage[firm], usable[firm]["account"], firm,
                               cfg["mt5"])
        mt5_trades[firm], reports[firm] = got["trades"], {"dir": got["dir"],
                                                           "summary": got["summary"]}

    say(92, "comparando")
    pieces, summaries = {}, {}
    for firm in costs:
        sqx_in = compare.window(sqx_trades[firm], *window)
        mt5_in = compare.window(mt5_trades[firm], *window)
        piece = judge.firm_result(firm, sqx_in, mt5_in, timeframe, deposit, cfg,
                                  usable[firm]["symbol"])
        pieces[firm] = piece
        summaries[firm] = {**piece["summary"], "report": reports[firm]["dir"]}
        record.log(ledger_study.study_id(asset, timeframe, "mt5verify"), {
            "step": 26, "launched_by": "mt5.verify", "symbol": asset, "timeframe": timeframe,
            "segment": segments(data, window), "window_from": window[0], "window_to": a.end,
            "n_in": 1, "n_out": int(piece["summary"]["state"] == "pass"),
            "criterion": f"SQX ↔ MT5 en {firm} ({a.model})",
            "thresholds": cfg["thresholds"], "note": f"{strategy.stem} · {run_id}"})
    tabs = []
    if pieces:
        baseline = assetdata.sqx_settings(data, "build")
        tab_blocks = [judge.params_table(baseline, costs), judge.combined_chart(pieces),
                      sidebyside.table(pieces)]
        for piece in pieces.values():
            tab_blocks += [piece["verdict"], piece["lonely"]]
        tabs = [{"name": "verificacion", "title": "Verificación",
                "note": "Criterios de aceptación (verde: superado, rojo: fallido) y P&L por "
                        "empresa; la lucecita de cada empresa en la ventana enciende o apaga "
                        "su curva y sus criterios.",
                "blocks": tab_blocks}]
    meta.update({"project": project, "deposit": deposit, "ea": ea["expert"],
                 "lots": sizing["params"]["Size"]})
    report.finish(work, meta, cfg, started, summaries, refused, "", tabs)
    say(100, " · ".join(f"{firms.label(f)}: {'Validada' if s['state'] == 'pass' else 'No validada'}"
                        for f, s in summaries.items()) or "sin empresas")


if __name__ == "__main__":
    # A cancel from the window is SIGTERM: raised as SystemExit, every `finally` stops the
    # conductor it started and `report.failed` marks the run, as «Lanzar en SQX» does.
    signal.signal(signal.SIGTERM, graceful)
    try:
        main()
    except SystemExit as stop:
        if stop.code not in (None, 0):
            report.failed(RUNS, str(stop.code))
        raise
    except Exception as crash:
        report.failed(RUNS, f"{type(crash).__name__}: {crash}")
        raise
