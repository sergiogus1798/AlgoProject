"""Every path and port in the project. The only module allowed to know where things live."""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
_CFG = yaml.safe_load((ROOT / "config" / "machine.yaml").read_text())

MASTER = Path(_CFG["sqx_master"]).expanduser()
WORKER = Path(_CFG["sqx_worker"]).expanduser()
DATA = Path(_CFG["data_root"]).expanduser()
ARCHIVE = Path(_CFG["archive"]).expanduser()
BROWSER = Path(_CFG["browser"]).expanduser()
WORKER_PORT = _CFG["worker_port"]
STRATEGY_POOLS = {name: Path(p).expanduser() for name, p in _CFG["strategy_pools"].items()}

WORKER_SH = ROOT / "bin" / "sqx-worker.sh"
ASSETS = ROOT / "assets"
MANUAL = ROOT / "docs" / "manual"
VIEWS_REL = "user/settings/views/databanks"
STAGING = WORKER / "user/projects/Retester/databanks/Results"


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
        records in memory — see knowhow/02-databanks.md.
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


def bars_file(symbol: str, timeframe: str) -> Path:
    """Where exported OHLC bars for one symbol and timeframe live.

    Args:
        symbol: SQX symbol without the timeframe suffix, e.g. "XAUUSD_DukasM1_Infinox".
        timeframe: SQX timeframe code, e.g. "M30".

    Returns:
        Path under the data root.
    """
    return DATA / "bars" / symbol / f"{timeframe}.csv"
