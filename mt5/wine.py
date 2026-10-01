"""Where MetaTrader 5 lives inside its Wine prefix, and how to run a Windows program there."""
import os
import shutil
import subprocess
import time
from pathlib import Path, PureWindowsPath

from core.paths import MASTER, MT5_PREFIX

INSTALL = MT5_PREFIX / "drive_c" / "Program Files" / "MetaTrader 5"
TERMINAL = INSTALL / "terminal64.exe"
METAEDITOR = INSTALL / "MetaEditor64.exe"   # Linux is case-sensitive: the installer writes this case
# The Windows Python bin/mt5-install.sh puts in the prefix, for the MetaTrader5 package.
PYTHON = MT5_PREFIX / "drive_c" / "Python" / "python.exe"
# What SQX's generated EAs call: its Sq* indicators and their include.
SQX_MQL5 = MASTER / "custom_indicators" / "MetaTrader5"
# The project's own set, laid over SQX's: the add-on indicators SQX does not ship, and the
# owner's versions of some it does. Same Indicators/ and Include/ layout as MQL5/.
PROJECT_MQL5 = Path(__file__).parent / "indicators"
# Our EAs go in a folder of their own under MQL5/Experts, never mixed with the stock ones.
EXPERTS_SUB = "AlgoProject"
# The virtual X display the terminal and MetaEditor draw on, so no window opens on the desktop.
# Xvfb is unpacked into ~/.local/bin (no sudo here). MT5_VISIBLE=1 shows the windows again.
HEADLESS_DISPLAY = ":77"


def _headless_display() -> str | None:
    """HEADLESS_DISPLAY, starting Xvfb on it if it is not up; None when Xvfb is not installed."""
    socket = Path("/tmp/.X11-unix") / f"X{HEADLESS_DISPLAY[1:]}"
    if socket.exists():
        return HEADLESS_DISPLAY
    xvfb = shutil.which("Xvfb")
    if xvfb is None:
        return None
    subprocess.Popen([xvfb, HEADLESS_DISPLAY, "-screen", "0", "1280x1024x24", "-nolisten", "tcp"],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    for _ in range(50):
        if socket.exists():
            return HEADLESS_DISPLAY
        time.sleep(0.1)
    return None


def env() -> dict:
    """The process environment: WINEPREFIX at the MT5 prefix, Wine's chatter off, and the
    virtual display unless MT5_VISIBLE=1 or Xvfb is missing (then the desktop's, windows show)."""
    out = {**os.environ, "WINEPREFIX": str(MT5_PREFIX), "WINEDEBUG": "-all"}
    display = None if os.environ.get("MT5_VISIBLE") == "1" else _headless_display()
    if display:
        out["DISPLAY"] = display
        out.pop("WAYLAND_DISPLAY", None)
    return out


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


def open_terminal(wait_s: float = 60) -> bool:
    """Start this prefix's terminal detached, when it is not up, and wait until it runs.

    Started here and not by the MetaTrader5 package's `initialize(path=…)`: a terminal that
    package starts is the Windows Python's child, holds its stdout, and `run()` — which waits
    for the pipe to close — then waits for as long as the terminal lives (🔬 2026-09-29, a
    ten-minute hang on the first account read).

    Returns:
        True when a terminal is running.
    """
    if terminal_running():
        return True
    subprocess.Popen(["wine", str(TERMINAL)], env=env(), stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL, start_new_session=True)
    for _ in range(int(wait_s)):
        time.sleep(1)
        if terminal_running():
            time.sleep(5)            # the process is listed before its IPC answers
            return True
    return False


def close_terminal(wait_s: float = 90) -> bool:
    """Close this prefix's terminal the way its window's X does, so it saves and exits.

    The tester and MetaEditor need it closed, and the MetaTrader5 package can open it but has
    no call to close it. `taskkill` without /F posts WM_CLOSE; only a terminal still up after
    `wait_s` is killed.

    Returns:
        True when no terminal is left.
    """
    if not terminal_running():
        return True
    run(INSTALL.parent.parent / "windows" / "system32" / "taskkill.exe",
        ["/IM", "terminal64.exe"], timeout=60)
    for _ in range(int(wait_s)):
        if not terminal_running():
            return True
        time.sleep(1)
    subprocess.run(["pkill", "-TERM", "-f", r"^C:\\.*terminal64\.exe"], check=False)
    time.sleep(5)
    return not terminal_running()


def kill_terminal() -> bool:
    """Kill this prefix's terminal outright, no save — for one `close_terminal` gave up on.

    The owner's last resort for a terminal wedged open that neither its own window controls
    nor `close_terminal`'s WM_CLOSE/SIGTERM reach (🔬 2026-10-01). Throws away unsaved state.

    Returns:
        True when no terminal is left.
    """
    if not terminal_running():
        return True
    subprocess.run(["pkill", "-KILL", "-f", r"^C:\\.*terminal64\.exe"], check=False)
    time.sleep(2)
    return not terminal_running()


def run(exe: Path, args: list[str], timeout: float, cwd: Path | None = None) -> subprocess.CompletedProcess:
    """Run a Windows program under Wine and wait for it.

    Args:
        exe: The .exe inside the prefix.
        args: Its Windows-style arguments. Wine builds the child's command line by joining
            these with spaces and does NOT requote one that itself contains a space (every
            path under the prefix does: "Program Files", "MetaTrader 5") — the argument
            silently splits in two and the program sees a truncated path. Pass `cwd` and a
            path relative to it instead of an absolute one, wherever the callee allows it.
        timeout: Seconds before it is killed.
        cwd: Working directory (Linux path) the child starts in, so a Windows-relative
            argument resolves against it.

    Returns:
        The finished process, output captured as text.
    """
    return subprocess.run(["wine", str(exe), *args], env=env(), capture_output=True,
                          text=True, errors="replace", timeout=timeout,
                          cwd=str(cwd) if cwd else None)
