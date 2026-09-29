"""Where MetaTrader 5 lives inside its Wine prefix, and how to run a Windows program there."""
import os
import subprocess
from pathlib import Path, PureWindowsPath

from core.paths import MASTER, MT5_PREFIX

INSTALL = MT5_PREFIX / "drive_c" / "Program Files" / "MetaTrader 5"
TERMINAL = INSTALL / "terminal64.exe"
METAEDITOR = INSTALL / "metaeditor64.exe"
# The Windows Python bin/mt5-install.sh puts in the prefix, for the MetaTrader5 package.
PYTHON = MT5_PREFIX / "drive_c" / "Python" / "python.exe"
# What SQX's generated EAs call: its Sq* indicators and their include.
SQX_MQL5 = MASTER / "custom_indicators" / "MetaTrader5"
# Our EAs go in a folder of their own under MQL5/Experts, never mixed with the stock ones.
EXPERTS_SUB = "AlgoProject"


def env() -> dict:
    """The process environment with WINEPREFIX pointing at the MT5 prefix and Wine's chatter off."""
    return {**os.environ, "WINEPREFIX": str(MT5_PREFIX), "WINEDEBUG": "-all"}


def windows(path: Path) -> str:
    """A Linux path as Wine sees it: the prefix's own drive when inside it, else Z:.

    Args:
        path: Absolute Linux path.

    Returns:
        A Windows path, e.g. C:\\Program Files\\MetaTrader 5\\MQL5.
    """
    drive_c = MT5_PREFIX / "drive_c"
    if path.is_relative_to(drive_c):
        return str(PureWindowsPath("C:/", *path.relative_to(drive_c).parts))
    return str(PureWindowsPath("Z:/", *path.parts[1:]))


def data_dir() -> Path:
    """The terminal's data folder: AppData/.../Terminal/<hash> whose origin.txt names INSTALL.

    Unless that folder holds a portable.txt: then the terminal keeps MQL5/, logs/ and the
    accounts in INSTALL itself — which is how mt5setup.exe left it under Wine (2026-09-29).
    """
    root = MT5_PREFIX / "drive_c" / "users"
    for origin in root.glob("*/AppData/Roaming/MetaQuotes/Terminal/*/origin.txt"):
        if origin.read_text(encoding="utf-16").strip().lower() == windows(INSTALL).lower():
            return INSTALL if (origin.parent / "portable.txt").exists() else origin.parent
    raise SystemExit(f"no data folder for {INSTALL}: start the terminal once (bin/mt5-install.sh)")


def terminal_running() -> bool:
    """Whether a terminal64.exe of this prefix is up. MT5 refuses a second one on the same data."""
    # Wine shows the process as its Windows command line; matching only that keeps a shell
    # whose command merely mentions terminal64.exe from reading as a running terminal.
    out = subprocess.run(["pgrep", "-af", r"^C:\\.*terminal64\.exe"], capture_output=True,
                         text=True).stdout
    return bool(out.strip())


def run(exe: Path, args: list[str], timeout: float) -> subprocess.CompletedProcess:
    """Run a Windows program under Wine and wait for it.

    Args:
        exe: The .exe inside the prefix.
        args: Its Windows-style arguments.
        timeout: Seconds before it is killed.

    Returns:
        The finished process, output captured as text.
    """
    return subprocess.run(["wine", str(exe), *args], env=env(), capture_output=True,
                          text=True, errors="replace", timeout=timeout)
