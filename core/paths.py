"""Every path and port in the project. The only module allowed to know where things live."""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
_FILE = ROOT / "config" / "machine.yaml"
if not _FILE.exists():
    raise SystemExit(f"{_FILE} is missing. Copy config/machine.example.yaml to it and edit "
                     "the paths for this machine — it is the only file not in git.")
_CFG = yaml.safe_load(_FILE.read_text(encoding="utf-8"))

MASTER = Path(_CFG["sqx_master"]).expanduser()
WORKER = Path(_CFG["sqx_worker"]).expanduser()
DATA = Path(_CFG["data_root"]).expanduser()
# Optional: no browser is needed unless the manual is rendered to PDF.
BROWSER = Path(_CFG.get("browser", "")).expanduser()
WORKER_PORT = _CFG["worker_port"]
# The desktop app's local daemon. Loopback only, never exposed; a machine that never
# opens the app never sets it, so it carries a default rather than being required.
UI_PORT = _CFG.get("ui_port", 8765)
STRATEGY_POOLS = {name: Path(p).expanduser()
                  for name, p in (_CFG.get("strategy_pools") or {}).items()}

# Headless installs by role. The conductor is sqx_worker / worker_port themselves rather
# than an entry of its own: two places holding the same port is how one of them goes stale.
# Any other role — the custodian, and it is optional — comes from sqx_workers.
WORKERS = {"conductor": {"path": WORKER, "port": WORKER_PORT}}
WORKERS.update({role: {"path": Path(w["path"]).expanduser(), "port": w["port"]}
                for role, w in (_CFG.get("sqx_workers") or {}).items()})

WORKER_SH = ROOT / "bin" / "sqx-worker.sh"
ASSETS = ROOT / "assets"
# La taxonomía de bloques: configuración a mano, versionada, no un derivado del install.
TAXONOMY = ROOT / "sqx" / "blocks" / "taxonomy.yaml"
# Las paletas: una por arquetipo, lo único que la ventana escribe de este lado.
PALETTES = ROOT / "sqx" / "blocks" / "palettes"
MANUAL = ROOT / "docs" / "manual"
VIEWS_REL = "user/settings/views/databanks"
STAGING_REL = "user/projects/Retester/databanks/Results"
STAGING = WORKER / STAGING_REL


def worker_dir(role: str = "conductor") -> Path:
    """Top-level folder of one headless install.

    Args:
        role: "conductor" for the always-awake worker that takes short jobs, "custodian"
            for the one that holds a long job and receives no other command while it runs.

    Returns:
        Path to the install. Raises KeyError when the role is not in machine.yaml, which
        is the honest answer on a machine where the custodian was never cloned.
    """
    return WORKERS[role]["path"]


def worker_staging(role: str = "conductor") -> Path:
    """The Retester/Results databank one install exports through.

    Args:
        role: Worker role, as in worker_dir.

    Returns:
        Path inside that install. Exports stage a copy of the strategies here because a
        databank's folder can be empty while SQX holds its records in memory.
    """
    return WORKERS[role]["path"] / STAGING_REL


def project_dir(name: str, install: Path = MASTER) -> Path:
    """Folder of one SQX project.

    Args:
        name: Project name as SQX shows it, underscores only.
        install: Which install to look in; the master by default.

    Returns:
        Path to <install>/user/projects/<name>, which holds project.cfx and databanks/.
    """
    return install / "user/projects" / name


def databank_dir(project: str, databank: str, install: Path = MASTER) -> Path:
    """Folder holding one databank's .sqx files.

    Args:
        project: Project name.
        databank: Databank name as SQX shows it, e.g. "SPP OOS".
        install: Which install to look in; the master by default.

    Returns:
        Path to the databank directory. It can be empty while the databank holds
        records in memory — see knowhow/databanks/sync-deletes-unloaded-files.md.
    """
    return project_dir(project, install) / "databanks" / databank


def view_file(name: str, install: Path = MASTER) -> Path:
    """Path of a databank view definition.

    Args:
        name: View name without the .vw extension.
        install: Which install the view belongs to.

    Returns:
        Path to <install>/user/settings/views/databanks/<name>.vw.
    """
    return install / VIEWS_REL / f"{name}.vw"


def export_dir(project: str, databank: str, day: str) -> Path:
    """Where one export of one databank lands.

    Args:
        project: Project name.
        databank: Databank name.
        day: Export date as YYYY-MM-DD.

    Returns:
        Path under the data root. Created by the caller, never by this module.
    """
    return DATA / "raw" / project / databank.replace(" ", "_") / day


def metrics_export(project: str, databank: str) -> Path:
    """Directory holding the CURRENT metrics export of one databank.

    Args:
        project: Project name.
        databank: Databank name as SQX shows it, e.g. "SPP OOS".

    Returns:
        Path under the data root. There is exactly one metrics export per databank and
        refreshing it replaces what is there, so "which CSV is the real one" cannot arise.
        It is deliberately outside raw/, where exports are dated and immutable.
    """
    return DATA / "metrics" / project / databank.replace(" ", "_")


def harvest_dir(project: str, databank: str, day: str) -> Path:
    """Where one cosecha of a databank lands: its metrics, trades and equity together.

    Args:
        project: Project name.
        databank: Databank name as SQX shows it.
        day: Harvest date as YYYY-MM-DD.

    Returns:
        Path under the data root. Dated and immutable, like raw/, and separate from it
        because the three files here were taken in one pass from one state of the
        databank: a gate verdict is only reproducible against the set it was judged on.
    """
    return DATA / "harvest" / project / databank.replace(" ", "_") / day


def report_dir(project: str, databank: str, day: str) -> Path:
    """Where one day's rendered analysis of a databank lands.

    Args:
        project: Project name.
        databank: Databank name.
        day: Report date as YYYY-MM-DD.

    Returns:
        Path under the data root. Reports accumulate so the history of what was concluded
        survives; the CSV they were built from does not.
    """
    return DATA / "reports" / project / databank.replace(" ", "_") / day


def bar_source(feed: str) -> Path:
    """The M1 bars of one feed: the only bar data the project stores.

    Args:
        feed: SQX symbol without the timeframe suffix, e.g. "XAUUSD_DukasM1_Infinox".

    Returns:
        Path under the data root. Every other timeframe is resampled from this file and
        reproduces SQX's own export of it exactly, so nothing else is worth keeping.
    """
    return DATA / "bars" / feed / "M1.parquet"


def bar_cache(feed: str, timeframe: str, version: str) -> Path:
    """Where a timeframe resampled from M1 is kept.

    Args:
        feed: SQX symbol without the timeframe suffix.
        timeframe: SQX timeframe code, e.g. "M30".
        version: Fingerprint of the M1 data it was built from.

    Returns:
        Path under the data root. The version is in the name rather than in a field, so a
        refreshed M1 orphans its caches instead of quietly answering with stale bars.
    """
    return DATA / "barsDerived" / feed / f"{timeframe}-{version}.parquet"


def perf_dir() -> Path:
    """Where the performance catalogue keeps its history.

    Returns:
        Path under the data root. It holds one row per measurement, appended forever: the
        point of the catalogue is the comparison between dates, so nothing here is ever
        overwritten.
    """
    return DATA / "profiling"


def ledger_file(study: str) -> Path:
    """The global search ledger of one study.

    Args:
        study: Study id, e.g. "XAUUSD_M30_DirectionalMomentum".

    Returns:
        A `.jsonl` under the data root, one line per search, appended and never rewritten.
        It lives with the data and not in the repository because it grows with every run
        and because it is a record of what happened on this machine, not source.
    """
    return DATA / "ledger" / f"{study}.jsonl"
