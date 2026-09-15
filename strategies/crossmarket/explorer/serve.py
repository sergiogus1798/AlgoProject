#!/usr/bin/env python3
"""The panel: pick a strategy, see its markets, set every knob, and run the study on it."""

import argparse
import webbrowser
from pathlib import Path

from flask import Flask, jsonify, request

from core import bars as barsio
from core.paths import DATA, bars_file, export_dir
from strategies.crossmarket import config, markets, metrics, panel
from strategies.crossmarket.explorer import jobs, scope, sections, simulations, tooltips, work

APP = Flask(__name__)
PAGE = Path(__file__).with_name("page.html")
SETUP: dict = {}


@APP.get("/")
def index() -> str:
    """The panel itself.

    Returns:
        The page, with this run's project and databank in its title.
    """
    return PAGE.read_text(encoding="utf-8").replace(
        "__TITLE__", f"{SETUP['project']} / {SETUP['databank']}")


@APP.get("/api/state")
def state() -> object:
    """What the panel needs to draw its dropdown.

    Returns:
        The strategies of the databank, and which of them have been run in this session.
    """
    return jsonify({"project": SETUP["project"], "databank": SETUP["databank"],
                    "export": SETUP["export"], "strategies": SETUP["strategies"],
                    "done": sorted(work.RESULTS), "tabs": sections.TABS})


@APP.get("/api/markets")
def market_list() -> object:
    """The additional markets one strategy was retested on in SQX.

    Returns:
        One row per market of the universe with its category and whether this strategy
        actually traded there, plus whether it has a result in this session.
    """
    name = request.args["strategy"]
    return jsonify({"markets": work.available(SETUP, name),
                    "analysed": sorted(work.RESULTS.get(name, {}).get("runs", {}))})


@APP.get("/api/config")
def config_defaults() -> object:
    """The factory defaults the config drawer builds its form from.

    Returns:
        Every knob of config.yaml flattened to dotted keys, one sentence per knob, and the
        group each belongs to. The drawer sends back only the fields actually changed.
    """
    return jsonify({"cfg": config.flatten(SETUP["cfg"]), "tips": tooltips.TIPS,
                    "groups": tooltips.GROUPS})


@APP.post("/api/analyse")
def analyse() -> object:
    """Run the analysis: the whole strategy, or one of its markets."""
    cfg, name = scope.scoped(SETUP, request.json), request.json["strategy"]
    only = request.json.get("market") or None
    what = f"{name} — {only}" if only else name
    return jsonify({"started": jobs.start(lambda: work.analyse(SETUP, cfg, name, only),
                                          f"Analizando {what}", 0)})


@APP.get("/api/status")
def status() -> object:
    """Where the running job has got to."""
    return jsonify({**jobs.status(), "result": jobs.take()})


@APP.get("/api/random")
def random_axes() -> object:
    """The three selectors of the random-entry tab, for the strategy on screen.

    Returns:
        The markets that have a result, the null models that were run with their reader's
        names, and the statistics the histogram can draw. Everything was computed by the run
        and is held in memory, so switching any of the three recomputes nothing.
    """
    record = work.RESULTS.get(request.args["strategy"])
    if record is None:
        return jsonify({"markets": [], "models": [], "metrics": []})
    models = record["cfg"]["nulls"]["models"]
    return jsonify({"markets": list(record["runs"]),
                    "models": [{"key": m, "name": panel.NAMES[m]} for m in models],
                    "metrics": [{"key": k, "label": metrics.LABELS[k]}
                                for k in simulations.DRAWN]})


@APP.get("/api/random/view")
def random_view() -> object:
    """One market, one null model, one statistic: the cone, the histogram and the table."""
    a = request.args
    record = work.RESULTS[a["strategy"]]
    return jsonify({"html": simulations.random_view(record, record["cfg"], a["market"],
                                                    a["model"], a["metric"])})


@APP.get("/api/models/view")
def models_view() -> object:
    """The model comparison for one statistic, when the Modelos tab's dropdown changes."""
    a = request.args
    record = work.RESULTS[a["strategy"]]
    return jsonify({"html": simulations.models_view(record, record["cfg"], a["metric"])})


@APP.get("/api/section")
def section() -> object:
    """One tab's HTML, for the strategy the panel is showing."""
    name, which = request.args["strategy"], request.args["name"]
    record = work.RESULTS.get(name)
    if record is None:
        return jsonify({"html": '<div class="note">Esta estrategia todavía no se ha '
                                'analizado en esta sesión. Pulsa <b>Run analysis</b>.</div>'})
    return jsonify({"html": sections.section(which, record, record["cfg"])})


def main() -> None:
    """Start the panel and open it in a browser."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--databank", required=True, help="the databank export_retest exported")
    ap.add_argument("--asset", required=True, help="base asset, e.g. XAUUSD")
    ap.add_argument("--export", required=True, help="export date, YYYY-MM-DD")
    ap.add_argument("--set", action="append", default=[], metavar="KEY=VALUE",
                    help="config.yaml override, e.g. --set nulls.draws=20000")
    ap.add_argument("--port", type=int, default=8766)
    a = ap.parse_args()

    trades = export_dir(a.project, a.databank, a.export) / "trades"
    universe = markets.universe(a.asset, trades)
    names = [f.stem for f in sorted((trades / universe["main"]).glob("*.csv"))]
    SETUP.update({"project": a.project, "databank": a.databank, "export": a.export,
                  "universe": universe, "trades": trades, "strategies": names, "args": a,
                  "base_set": a.set, "cfg": config.load(a.set),
                  "bars": {feed: barsio.read(bars_file(feed, universe["timeframe"]))
                           for feed in markets.feeds(universe)}})
    wiped = work.clear(DATA)
    url = f"http://127.0.0.1:{a.port}/"
    print(f"{len(names)} estrategias · {len(universe['markets'])} mercados · panel en {url}")
    for m in universe["markets"]:
        print(f"  {m['feed']:30} {m['category']}")
    for feed in universe["absent"]:
        print(f"  {feed:30} DECLARADO PERO SIN OPERACIONES EN EL EXPORT")
    if wiped:
        print(f"  {wiped} resultados de análisis anteriores borrados del disco")
    print("  nada se guarda: cada número de esta sesión sale del botón que acabas de pulsar")
    webbrowser.open(url)
    APP.run(host="127.0.0.1", port=a.port, threaded=True)


if __name__ == "__main__":
    main()
