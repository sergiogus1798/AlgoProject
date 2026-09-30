"""A study's knobs as the window will run them for one project: the runner's substitutions, and the ones it does not make."""

from core.assetdata import load
from sqx.projects import registry

# The knobs `ui/daemon/runner/` replaces at run time with the project's own, by `--set`
# (`readings.entry_quality`, `readings.conditional_map`, `readings.exposure`,
# `optimisation.cloud`, `screening.gate`): the config.yaml's value (the donor's, XAUUSD, M30)
# never runs for another asset. Kept in step with the runner by hand; the test
# `tests/test_ui_workflow.py` reads the runner's argv against it.
SET = {"entryQuality": {"run.feed": "feed", "run.timeframe": "timeframe"},
       "conditionalMap": {"run.symbol": "symbol", "run.feed": "feed",
                          "run.timeframe": "timeframe"},
       "cloud": {"run.symbol": "symbol"}, "exposure": {"study.timeframe": "timeframe"},
       "gate": {"monkey.timeframe": "timeframe"}}
# Knobs naming an asset or a grid that the runner does NOT replace: the file's value runs,
# whatever the project trades. Empty since 2026-09-28 (cloud, exposure and gate now get theirs).
KEPT: dict[str, dict[str, str]] = {}
WORDS = {"symbol": "activo", "feed": "feed", "timeframe": "timeframe"}


def facts(project: str) -> dict[str, str] | None:
    """The project's symbol, timeframe and feed, from its newest row of `registry.csv`.

    Args:
        project: Project name.

    Returns:
        `symbol`, `timeframe`, `feed` (the asset's SQX symbol, as `ui.daemon.runs.context`
        takes it), or None when the builder never recorded the project.
    """
    row = next((r for r in reversed(registry.rows()) if r["name"] == project), None)
    if row is None:
        return None
    return {"symbol": row["symbol"], "timeframe": row["timeframe"],
            "feed": load(row["symbol"])["sqx_symbol"]}


def apply(key: str, sections: list[dict], project: str) -> list[dict]:
    """The drawer's sections with this project's values where the run will use them.

    Args:
        key: Study key.
        sections: `knobs.sections(key)["sections"]`, not modified.
        project: Project name.

    Returns:
        The sections, each substituted knob with `value` the project's, `default` the file's
        and `note` saying so; each kept knob that differs from the project's with `warn`.
    """
    mine = facts(project)
    if mine is None or key not in SET | KEPT:
        return sections
    out = []
    for s in sections:
        knobs = []
        for k in s["knobs"]:
            what = SET.get(key, {}).get(k["key"])
            kept = KEPT.get(key, {}).get(k["key"])
            if what:
                k = k | {"value": mine[what],
                         "note": f"lo pone el proyecto al correr (en el config.yaml: "
                                 f"{k['value']})"}
            elif kept and str(k["value"]) != mine[kept]:
                k = k | {"warn": f"corre con {k['value']} aunque el {WORDS[kept]} del proyecto "
                                 f"sea {mine[kept]}: la ventana no lo cambia al lanzarlo"}
            knobs.append(k)
        out.append(s | {"knobs": knobs})
    return out
