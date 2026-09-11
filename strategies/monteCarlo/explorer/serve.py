#!/usr/bin/env python3
"""The interactive panel: run any test on any strategy, look at everything, write the report."""

import argparse
import webbrowser
from pathlib import Path

from flask import Flask, jsonify, request

from core import assets, bars
from core.paths import bars_file, export_dir
from strategies.monteCarlo import config, costs, regime, run, stream, stress, sweeps
from strategies.monteCarlo.explorer import cache, jobs, sections, work

APP = Flask(__name__)
PAGE = Path(__file__).with_name("page.html")
SETUP: dict = {}
ADHOC: dict = {}      # sub-tests run on their own; deliberately not written to the cache


@APP.get("/")
def index() -> str:
    """The panel itself.

    Returns:
        The page, with this run's project and databank in its title.
    """
    return (PAGE.read_text(encoding="utf-8")
            .replace("__TITLE__", f"{SETUP['project']} / {SETUP['databank']}"))


@APP.get("/api/state")
def state() -> object:
    """What the panel needs to draw its controls.

    Returns:
        The strategies, which of them already have a stored result, and the configuration
        in force.
    """
    have = cache.stored(SETUP["project"], SETUP["databank"])
    return jsonify({"project": SETUP["project"], "databank": SETUP["databank"],
                    "export": SETUP["export"], "n_sims": SETUP["cfg"]["global"]["n_sims"],
                    "strategies": [{"name": n, "saved": have.get(n, "")}
                                   for n in SETUP["strategies"]]})


@APP.post("/api/analyse")
def analyse() -> object:
    """Start the whole analysis of one strategy.

    Returns:
        Whether the job started; False means another one is running.
    """
    name = request.json["strategy"]
    steps = len(sweeps.plan(len(work.stream_of(SETUP, name)["pnl"]), SETUP["cfg"])) + len(stress.STRESS)
    return jsonify({"started": jobs.start(lambda: work.analyse(SETUP, name),
                                          f"Análisis completo — {name}", steps)})


@APP.post("/api/run")
def run_one() -> object:
    """Start a single sub-test, on its own.

    Returns:
        Whether the job started.
    """
    name, label = request.json["strategy"], request.json["label"]
    source = work.stream_of(SETUP, name)
    steps = {s["label"]: s for s in sweeps.plan(len(source["pnl"]), SETUP["cfg"])}
    step = steps.get(label, {"label": label, "model": label, "block": 0,
                             "title": stress.TITLES.get(label, label)})

    def again() -> dict:
        """Run it and keep it aside from the stored analysis."""
        ADHOC.setdefault(name, {})[label] = run.one(source, step, SETUP["cfg"])
        return {"strategy": name, "label": label}

    return jsonify({"started": jobs.start(again, step["title"], 0)})


@APP.post("/api/report")
def report() -> object:
    """Write one strategy's report file.

    Returns:
        Whether the job started.
    """
    name = request.json["strategy"]
    return jsonify({"started": jobs.start(lambda: work.report(SETUP, name),
                                          f"Informe — {name}", 0)})


@APP.get("/api/status")
def status() -> object:
    """Where the running job has got to.

    Returns:
        The progress, plus whatever the last finished job returned.
    """
    return jsonify({**jobs.status(), "result": jobs.take()})


@APP.get("/api/runs")
def runs() -> object:
    """Every sub-test whose distribution can be drawn for one strategy.

    Returns:
        The list, empty when that strategy has not been analysed yet.
    """
    record = cache.load(SETUP["project"], SETUP["databank"],
                        request.args["strategy"], SETUP["cfg"])
    if record is None:
        return jsonify({"runs": [], "saved": "", "stale": False})
    return jsonify({"runs": sections.runs(record["body"]["result"]),
                    "saved": record["saved"], "stale": record["stale"],
                    "adhoc": sorted(ADHOC.get(request.args["strategy"], {}))})


@APP.get("/api/section")
def section() -> object:
    """One rendered part of the report, for the strategy the panel is showing.

    Returns:
        HTML, or a note saying the strategy has not been analysed yet.
    """
    name, which = request.args["strategy"], request.args["name"]
    record = cache.load(SETUP["project"], SETUP["databank"], name, SETUP["cfg"])
    if record is None:
        return jsonify({"html": '<div class="note">Esta estrategia todavía no se ha '
                                'analizado. Pulsa «Analizar todo».</div>'})
    body, cfg = record["body"], SETUP["cfg"]
    warn = ('<div class="fail"><b>Resultado de otra configuración.</b> Se calculó con un '
            '<code>config.yaml</code> distinto del actual. Vuelve a analizar antes de '
            'decidir nada con estos números.</div>' if record["stale"] else "")
    if which == "verdict":
        return jsonify({"html": warn + sections.verdict_block(body["result"],
                                                              body["verdict"], cfg)})
    return jsonify({"html": warn + sections.family(which, body["result"], body["verdict"],
                                                   body["band"], cfg)})


@APP.get("/api/figure")
def figure() -> object:
    """One sub-test's distribution of one statistic.

    Returns:
        HTML. `adhoc` reads the sub-test run on its own instead of the stored analysis, so
        a re-run can be compared against what the full analysis had found.
    """
    name, label = request.args["strategy"], request.args["label"]
    metric, source = request.args["metric"], request.args.get("source", "cache")
    if source == "adhoc":
        got = ADHOC[name][label]
        return jsonify({"html": sections.figure(
            {"A": {"shapes": {label: got["shapes"]}, "runs": {label: got["table"]}},
             "B": {"shapes": {}, "runs": {}}, "C": {}}, label, metric,
            f"{got['title']} (re-ejecutada)")})
    record = cache.load(SETUP["project"], SETUP["databank"], name, SETUP["cfg"])
    result = record["body"]["result"]
    title = next(r["title"] for r in sections.runs(result) if r["label"] == label)
    return jsonify({"html": sections.figure(result, label, metric, title)})


def main() -> None:
    """Start the panel and open it in a browser."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--databank", required=True)
    ap.add_argument("--asset", required=True, help="asset name in assets/, e.g. XAUUSD")
    ap.add_argument("--export", required=True, help="export date, YYYY-MM-DD")
    ap.add_argument("--bars-timeframe", default="M30")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--set", nargs="*", default=[], metavar="KEY=VALUE")
    a = ap.parse_args()

    print(assets.report(a.asset))
    cfg = config.load(a.set)
    asset = costs.load(a.asset)
    trades = export_dir(a.project, a.databank, a.export) / "trades"
    names = [f.stem for f in sorted(trades.glob("*.csv"))]
    first = stream.build(trades / f"{names[0]}.csv", asset, cfg["global"]["risk_per_trade"])
    feed = str(first["frame"]["Symbol"].iloc[0])
    SETUP.update({"project": a.project, "databank": a.databank, "export": a.export,
                  "cfg": cfg, "asset": asset, "trades": trades, "strategies": names,
                  "day": regime.daily(bars.read(bars_file(feed, a.bars_timeframe))),
                  "shared": {"args": a, "export": trades,
                             "bars": bars_file(feed, a.bars_timeframe),
                             "cost": costs.crosscheck(first["frame"], asset),
                             "vol_model": cfg["family_d"]["vol_model"]}})
    url = f"http://127.0.0.1:{a.port}/"
    print(f"{len(names)} estrategias · panel en {url}  (Ctrl+C para parar)")
    webbrowser.open(url)
    APP.run(host="127.0.0.1", port=a.port, threaded=True)


if __name__ == "__main__":
    main()
