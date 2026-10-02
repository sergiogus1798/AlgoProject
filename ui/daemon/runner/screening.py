"""The command lines of the screening and data families (steps 4-8), or why the window cannot start one."""

from core.paths import DATA, databank_dir, metrics_export
from ui.daemon.loader import find
from ui.daemon.runner import where
from ui.daemon.workflow import sources

NO_HARVEST = "necesita la cosecha de este databank (studies.screening.gate.harvest, skill /oos-gate)"
NO_METRICS = "necesita el export de métricas de este databank (skill /export, metrics/)"


def gate(c: dict, strategy: str) -> list[str] | str:
    """Step 8: the whole cosecha through every screen."""
    if not c["harvest"]:
        return NO_HARVEST
    frame = where.harvest_timeframe(c["harvest_dir"])
    # The monkey screen's bar grid is the cosecha's own timeframe, not config.yaml's M30.
    return (["-m", "studies.screening.gate.report", "--project", c["project"], "--databank",
             c["databank"], "--feed", c["feed"]]
            + (["--set", f"monkey.timeframe={frame}"] if frame else []))


def is_oos(c: dict, strategy: str) -> list[str] | str:
    """In sample against out of sample: the population half over the metrics export, the
    per-trade half over the newest cosecha; either input is enough. It has no --strategy, so
    one strategy runs the whole databank once (`table.jobs` folds identical commands)."""
    if not ((metrics_export(c["project"], c["databank"]) / "metrics.csv").exists()
            or c["harvest"]):
        return f"{NO_METRICS}, o su cosecha (skill /oos-gate)"
    return ["-m", "studies.screening.isOos.report", "--project", c["project"], "--databank",
            c["databank"]]


def filters(c: dict, strategy: str) -> list[str] | str:
    """What an in-sample filter buys out of sample, over the metrics export."""
    if not (metrics_export(c["project"], c["databank"]) / "metrics.csv").exists():
        return NO_METRICS
    return ["-m", "studies.screening.filters.report", "--project", c["project"], "--databank",
            c["databank"]]


def decay(c: dict, strategy: str) -> list[str] | str:
    """IS to OOS decay read from the databank's .sqx files, split at the asset's oos1. Reads
    whichever install actually holds the project (owner, 2026-09-29: it read the master's
    always, empty for a project the workers hold — 📓 knowhow/sqx-drive)."""
    found = sources.install(c["project"])
    if found is None:
        return "no encuentra el proyecto en ningún install (master, conductor o custodio)"
    role, install = found
    if not any(databank_dir(c["project"], c["databank"], install).glob("*.sqx")):
        return f"lee los .sqx del databank en {role}, y ese databank no tiene ninguno ahí"
    built = find.built_from(c["project"], c["databank"])   # IS lives in the build, OOS here
    return (["-m", "studies.screening.decay.report", "--project", c["project"], "--databank",
             c["databank"], "--split", c["split"], "--end", c["end"]]
            + (["--role", role] if role != "master" else [])
            + (["--is-databank", built] if built else [])
            + (["--strategy", strategy] if strategy else []))


def monkey_excess(c: dict, strategy: str) -> list[str] | str:
    """How many beat the monkey against how many should by chance; needs a monkey panel."""
    if not where.newest(DATA / "reports" / c["project"] / c["databank"], "*/monkey/nulls.csv"):
        return "necesita el panel del mono de toda la población (monkey, ▶▶ toda la población)"
    return ["-m", "studies.screening.monkeyExcess.report", "--project", c["project"],
            "--databank", c["databank"]]


def feed_quality(c: dict, strategy: str) -> list[str] | str:
    """Each strategy's trades against its feed's anomalies; reads the .sqx on disk, read-only."""
    if not c["harvest"]:
        return NO_HARVEST
    return (["-m", "studies.data.feedQuality.report", "--project", c["project"], "--databank",
             c["databank"], "--feed", c["feed"]] + (["--strategy", strategy] if strategy else []))


def spread(c: dict, strategy: str) -> list[str] | str:
    """Each strategy repriced at Darwinex's real spread; needs the asset's step-4 scan."""
    if not c["harvest"]:
        return NO_HARVEST
    return (["-m", "studies.data.spread.report", "--project", c["project"], "--databank",
             c["databank"], "--feed", c["feed"]] + (["--strategy", strategy] if strategy else []))


def snooping_screen(c: dict, strategy: str) -> list[str] | str:
    """SPA and StepM of the gate's survivors against buy and hold, signed under the family."""
    row, family = where.enrolled(c["project"]), where.family(c["project"])
    if family is None:
        return where.no_family(c["project"])
    if not c["harvest"]:
        return NO_HARVEST
    return ["-m", "studies.screening.snoopingScreen.report", "--project", c["project"],
            "--databank", c["databank"], "--feed", c["feed"], "--symbol", c["asset"],
            "--timeframe", row["timeframe"], "--family", family]


# key -> {"plan", "one", "many", "sets"}; `sets` says whether the command takes --set. A
# study the window never starts carries only "why".
STUDIES = {
    "gate": {"plan": gate, "one": False, "many": True, "sets": True},
    "isOos": {"plan": is_oos, "one": True, "many": True, "sets": True},
    "filters": {"plan": filters, "one": False, "many": True, "sets": False},
    "decay": {"plan": decay, "one": True, "many": True, "sets": False},
    "monkeyExcess": {"plan": monkey_excess, "one": False, "many": True, "sets": False},
    "feedQuality": {"plan": feed_quality, "one": True, "many": True, "sets": True},
    "spread": {"plan": spread, "one": True, "many": True, "sets": True},
    "replication": {"why": "compara varios databanks contra uno de referencia y la ventana "
                           "corre uno: desde la terminal con --reference y --databank"},
    "snoopingScreen": {"plan": snooping_screen, "one": False, "many": True, "sets": True},
    "falsePositives": {"why": "aún no existe: sólo su README"},
    "analysis": {"why": "no es un estudio: son las matemáticas que comparten los del cribado"},
}
