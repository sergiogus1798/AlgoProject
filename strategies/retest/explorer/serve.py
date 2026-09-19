#!/usr/bin/env python3
"""The interactive panel: one strategy at a time, every figure on demand, and the report."""

import argparse
import webbrowser
from datetime import date
from pathlib import Path

from flask import Flask, jsonify, request

from core.paths import report_dir
from strategies.retest.explorer import jobs, scope, sections, tooltips, work
from strategies.retest.inputs import config
from strategies.retest.measure import store
from strategies.retest.render import panel

APP = Flask(__name__)
PAGE = Path(__file__).with_name("page.html")
SETUP: dict = {}


@APP.get("/")
def index() -> str:
    """The panel itself.

    Returns:
        The page, with this run's project and ingest in its title.
    """
    return (PAGE.read_text(encoding="utf-8")
            .replace("__TITLE__", f"{SETUP['project']} / {SETUP['databank']} / {SETUP['day']}"))


@APP.get("/api/state")
def state() -> object:
    """What the panel needs to draw its controls.

    Returns:
        The strategies of this ingest, which of them the session has already run, and the
        tabs available.
    """
    return jsonify({"project": SETUP["project"], "databank": SETUP["databank"],
                    "day": SETUP["day"], "strategies": SETUP["strategies"],
                    "done": sorted(work.RESULTS), "tabs": sections.TABS})


@APP.get("/api/config")
def config_defaults() -> object:
    """The configuration this panel started with.

    Returns:
        The whole cfg plus one sentence per knob. The drawer builds its form from this and
        sends back only the fields the reader changed, so a run nobody touched the drawer
        for uses exactly what config.yaml says.
    """
    return jsonify({"cfg": SETUP["cfg"], "tips": tooltips.TIPS})


@APP.post("/api/analyse")
def analyse() -> object:
    """Run the four questions on one strategy.

    Returns:
        Whether the job started; False means another one is running.
    """
    setup, name = scope.scoped(SETUP, request.json), request.json["strategy"]
    return jsonify({"started": jobs.start(lambda: work.analyse(setup, name), f"Analizando {name}")})


@APP.post("/api/all")
def analyse_all() -> object:
    """Run every strategy of the ingest.

    Returns:
        Whether the job started.
    """
    setup = scope.scoped(SETUP, request.json)
    return jsonify({"started": jobs.start(lambda: work.whole(setup), "Analizando la batería")})


@APP.get("/api/progress")
def progress() -> object:
    """What the panel polls while a job runs.

    Returns:
        The job state without its payload.
    """
    return jsonify(jobs.snapshot())


@APP.get("/api/section/<name>/<strategy>")
def section(name: str, strategy: str) -> str:
    """One tab of one strategy, already rendered.

    Args:
        name: One of sections.TABS' keys.
        strategy: One strategy id.

    Returns:
        HTML, or a prompt to run the strategy first. The panel owns no calculation: this
        calls the same renderers the batch report calls.
    """
    got = work.RESULTS.get(strategy)
    if not got:
        return '<p class="lede">Dale a <b>Analizar</b> para esta estrategia.</p>'
    return sections.section(name, got, scope.from_query(SETUP, request.args)["cfg"])


@APP.post("/api/report")
def write_report() -> object:
    """Write the batch report from what the session has run.

    Returns:
        Where it landed. It is the same page the batch command writes, from the same
        functions: if the panel and the report ever disagreed, one of them would be lying.
    """
    setup = scope.scoped(SETUP, request.json)
    result = work.whole(setup)
    out = report_dir(setup["project"], setup["databank"], setup["day"]) / "retest"
    out.mkdir(parents=True, exist_ok=True)
    title = f"Monte Carlo Retest — {setup['project']} / {setup['databank']} / {setup['day']}"
    (out / "retest.html").write_text(
        panel.page(result, title, "Escrito desde el panel."), encoding="utf-8")
    return jsonify({"path": str(out / "retest.html")})


def main() -> None:
    """Serve the panel for one ingest."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True)
    parser.add_argument("--databank", default="MCR_All")
    parser.add_argument("--day", default=date.today().isoformat())
    parser.add_argument("--port", type=int, default=8767)
    parser.add_argument("--set", action="append", dest="overrides", default=[],
                        metavar="KEY=VALUE")
    args = parser.parse_args()

    keys = {"project": args.project, "databank": args.databank, "day": args.day}
    sims = store.load_sims(**keys)
    SETUP.update(**keys, base_set=args.overrides, cfg=config.load(args.overrides),
                 strategies=sorted(sims["strategy"].unique()),
                 provenance=work.load_provenance(keys))

    url = f"http://127.0.0.1:{args.port}/"
    print(f"panel: {len(SETUP['strategies'])} estrategias de {args.databank} -> {url}")
    webbrowser.open(url)
    APP.run(host="127.0.0.1", port=args.port, debug=False)


if __name__ == "__main__":
    main()
