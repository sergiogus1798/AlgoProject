"""One press of a run button into the commands to start, or the Spanish sentence why none can start."""

from pathlib import Path

from ui.daemon import runs
from ui.daemon.runner import optimisation, readings, screening, transfer, where

STUDIES = {**screening.STUDIES, **transfer.STUDIES, **optimisation.STUDIES, **readings.STUDIES}
# The one study whose command runs a sub-test alone (CONTRACT §1): `--only <feed>` with
# `--strategy`. monteCarlo's one.run() can too, but its report.py exposes neither flag.
ONLY = {"crossmarket": transfer.only_options}
# Studies that read the export's `OOS1` sample unless told otherwise: on a build-only export
# they found no trade and died in a traceback (2026-09-27, Results holds IST alone).
SAMPLED = {"monkey", "profitShape", "entryQuality"}


def why_not(study: str) -> str | None:
    """Why a study can never start from the window, whatever the data holds.

    Args:
        study: A study folder name.

    Returns:
        The sentence, or None when it may start once its inputs exist.
    """
    return STUDIES[study].get("why") if study in STUDIES else "estudio desconocido"


def jobs(req: dict) -> list[dict] | str:
    """The commands one run request starts.

    Args:
        req: `study`, `scope` ("one" | "many"), `project`, `databank`, `strategies`, `asset`,
            `overrides` ("section.key=value"), `only` — the body of POST /api/study/run.

    Returns:
        One `{label, argv, about}` per job — one per strategy for `one`, a single one for
        `many` — or the sentence the window shows instead.
    """
    study, scope = req["study"], req["scope"]
    if why_not(study):
        return f"{study}: {why_not(study)}"
    entry = STUDIES[study]
    if not entry[scope]:
        return (f"{study} no se corre sobre toda la población: elige la estrategia"
                if scope == "many" else
                f"{study} lee la población entera: córrelo sobre toda la población")
    if scope == "one" and not req["strategies"]:
        return "elige al menos una estrategia"
    if req["only"] and (study not in ONLY or scope != "one"):
        return f"{study} no sabe correr una sola subprueba: córrelo entero"
    if req["overrides"] and not entry["sets"]:
        return f"{study} no tiene configuración que cambiar: su comando no acepta --set"
    if not req["asset"]:
        return "elige el activo del proyecto: de él salen el feed y las ventanas"
    c = runs.context(req["project"], req["databank"], "", req["asset"])
    if (study in SAMPLED and c["export"] and not any("sample" in o for o in req["overrides"])
            and "OOS1" not in where.distinct(Path(c["trades"]), "Sample type")):
        return (f"{study} lee la muestra OOS1 y el export de {req['databank']} sólo trae "
                f"{', '.join(where.distinct(Path(c['trades']), 'Sample type'))}: elige el "
                f"databank del retest fuera de muestra")
    out = []
    for strategy in req["strategies"] if scope == "one" else [""]:
        argv = entry["plan"](c, strategy)
        if isinstance(argv, str):
            return f"{study}: {argv}"
        argv += ["--only", req["only"]] if req["only"] else []
        argv += ["--set", *req["overrides"]] if req["overrides"] else []
        out.append({"label": study, "argv": argv,
                    "about": {"project": req["project"], "databank": req["databank"],
                              "strategy": strategy, "study": study, "scope": scope}})
    return out


def options(study: str, project: str, databank: str, asset: str) -> list[dict]:
    """The sub-tests of a study that run alone, for the `↻ solo …` button.

    Args:
        study: A study folder name.
        project, databank, asset: Where; the options of crossmarket are the export's markets.
            Empty strings when the window has not chosen yet.

    Returns:
        `[{"key", "label"}]`, empty when the study has none or nothing is chosen.
    """
    if study not in ONLY or not (project and databank and asset):
        return []
    return ONLY[study](runs.context(project, databank, "", asset))
