#!/usr/bin/env python3
"""The interactive panel: run every cross-market test on any strategy, or on the whole
database, and write the report. The only way to run this study — report.py is retired."""

import argparse
import webbrowser
from pathlib import Path

from flask import Flask, jsonify, request

from core import bars as barsio
from core.paths import bars_file, export_dir
from strategies.crossmarket import charts, markets
from strategies.crossmarket.explorer import cache, jobs, sections, work

APP = Flask(__name__)
PAGE = Path(__file__).with_name("page.html")
SETUP: dict = {}
CFG: dict = {}


@APP.get("/")
def index() -> str:
    """The panel itself."""
    return PAGE.read_text(encoding="utf-8").replace(
        "__TITLE__", f"{SETUP['project']} / {SETUP['databank']}")


@APP.get("/api/state")
def state() -> object:
    """What the panel needs to draw its dropdown and headline strip.

    Returns:
        The strategies, which already have a stored result, and the database summary from
        the last "Analizar toda la base de datos" — empty until that has run once.
    """
    have = cache.stored(SETUP["project"], SETUP["databank"])
    return jsonify({"project": SETUP["project"], "databank": SETUP["databank"],
                    "export": SETUP["export"],
                    "strategies": [{"name": n, "saved": have.get(n, "")}
                                   for n in SETUP["strategies"]],
                    "database": work.DATABASE})


@APP.get("/api/config")
def config_defaults() -> object:
    """The factory defaults the config drawer builds its form from."""
    return jsonify(CFG)


def _scoped(payload: dict) -> dict:
    """This request's configuration, with the drawer's overrides applied.

    Args:
        payload: The request JSON. Its optional "cfg" is {key: value}, only the keys the
            reader actually changed.

    Returns:
        A copy of CFG with those keys replaced — never mutated in place, so a run made with
        the drawer open does not change what any other strategy sees.
    """
    return {**CFG, **payload.get("cfg", {})}


@APP.post("/api/analyse")
def analyse() -> object:
    """Start "Analizar esta estrategia"."""
    cfg, name = _scoped(request.json), request.json["strategy"]
    steps = len(SETUP["spec"]["additional"])
    return jsonify({"started": jobs.start(lambda: work.analyse(SETUP, cfg, name),
                                          f"Analizando {name}", steps)})


@APP.post("/api/analyse_all")
def analyse_all() -> object:
    """Start "Analizar toda la base de datos"."""
    cfg = _scoped(request.json)
    return jsonify({"started": jobs.start(lambda: work.analyse_all(SETUP, cfg),
                                          "Analizando toda la base de datos",
                                          len(SETUP["strategies"]))})


@APP.post("/api/report")
def report() -> object:
    """Start "Generar informe"."""
    cfg = _scoped(request.json)
    return jsonify({"started": jobs.start(lambda: work.report(SETUP, cfg), "Informe", 0)})


@APP.post("/api/run")
def run_one() -> object:
    """Re-run one (market, model) pair on its own, with its own draw count."""
    cfg = _scoped(request.json)
    name, market, model = (request.json["strategy"], request.json["market"],
                           request.json["model"])
    draws = int(request.json.get("draws", cfg["draws"]))
    return jsonify({"started": jobs.start(
        lambda: work.rerun(SETUP, name, market, model, draws),
        f"Re-ejecutando {market} · {model}", 0)})


@APP.get("/api/status")
def status() -> object:
    """Where the running job has got to."""
    return jsonify({**jobs.status(), "result": jobs.take()})


@APP.get("/api/runs")
def runs() -> object:
    """Every market whose null distribution can be drawn for one strategy."""
    record = cache.load(SETUP["project"], SETUP["databank"], request.args["strategy"], CFG)
    if record is None:
        return jsonify({"markets": [], "saved": "", "stale": False})
    return jsonify({"markets": sections.runs(record["body"]), "saved": record["saved"],
                    "stale": record["stale"],
                    "adhoc": list(work.ADHOC.get(request.args["strategy"], {}))})


@APP.get("/api/section")
def section() -> object:
    """One tab's HTML, for the strategy the panel is showing."""
    name, which = request.args["strategy"], request.args["name"]
    record = cache.load(SETUP["project"], SETUP["databank"], name, CFG)
    if record is None:
        return jsonify({"html": '<div class="note">Esta estrategia todavía no se ha '
                                'analizado. Pulsa «Analizar esta estrategia».</div>'})
    warn = ('<div class="fail"><b>Resultado de otra configuración.</b> Se calculó con un '
            'ajuste distinto del actual. Vuelve a analizar antes de decidir nada con estos '
            'números.</div>' if record["stale"] else "")
    return jsonify({"html": warn + sections.section(which, record["body"])})


@APP.get("/api/figure")
def figure() -> object:
    """One market/model pair's null distribution."""
    name, market, model = (request.args["strategy"], request.args["market"],
                           request.args["model"])
    if request.args.get("source") == "adhoc":
        got = work.ADHOC[name][f"{market}|{model}"]
        return jsonify({"html": charts.distribution(
            got["shape"], market, f"modelo {model} (re-ejecutada) — p = {got['p']:.4f}")})
    record = cache.load(SETUP["project"], SETUP["databank"], name, CFG)
    return jsonify({"html": sections.figure(record["body"], market, model)})


def main() -> None:
    """Start the panel and open it in a browser."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--databank", required=True, help="the databank export_retest exported")
    ap.add_argument("--asset", required=True, help="base asset, e.g. XAUUSD")
    ap.add_argument("--export", required=True, help="export date, YYYY-MM-DD")
    ap.add_argument("--port", type=int, default=8766)
    a = ap.parse_args()

    cache.clear(a.project, a.databank)
    spec = markets.load(a.asset)
    trades = export_dir(a.project, a.databank, a.export) / "trades"
    names = [f.stem for f in sorted((trades / spec["main"]).glob("*.csv"))]
    feed_bars = {feed: barsio.read(bars_file(feed, spec["timeframe"]))
                for feed in markets.feeds(a.asset)}
    SETUP.update({"project": a.project, "databank": a.databank, "export": a.export,
                  "spec": spec, "bars": feed_bars, "trades": trades, "strategies": names,
                  "args": a})
    CFG.update(work.default_cfg())
    url = f"http://127.0.0.1:{a.port}/"
    print(f"{len(names)} estrategias · panel en {url}  (Ctrl+C para parar)")
    webbrowser.open(url)
    APP.run(host="127.0.0.1", port=a.port, threaded=True)


if __name__ == "__main__":
    main()
