"""Send one account's package to the VPS and relaunch its terminal; or install the relaunch task. Dry-run unless --yes."""

import argparse
import tempfile
from pathlib import Path

from core import proc
from mt5.fleet import remote

VPS = Path(__file__).parent / "vps"
HOME = "fleet-packages"  # under the VPS user's home


def ps(script: Path, variables: dict[str, str]) -> str:
    """Run a VPS PowerShell script with its variables set first; returns stdout, raises on failure."""
    head = "".join(f"${k} = {v}\n" for k, v in variables.items())
    done = proc.run(
        ["ssh", "-o", "ConnectTimeout=10", remote.SSH, remote.POWERSHELL],
        input=head + script.read_text(),
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    if done.returncode:
        raise SystemExit(
            f"la VPS devolvió {done.returncode}: {done.stderr.strip()[:300]}"
        )
    return done.stdout.strip()


def quote(text: str) -> str:
    """A PowerShell single-quoted string."""
    return "'" + text.replace("'", "''") + "'"


def push(package: Path, install: str, restart: bool) -> str:
    """Copy the package to the VPS, then lay it into the terminal at `install` (its data folder is found by origin.txt)."""
    name = package.name
    proc.run(
        ["ssh", remote.SSH, f"mkdir {HOME}"],
        capture_output=True,
        timeout=30,
        check=False,
    )  # exists already: harmless
    proc.run(
        ["scp", "-qr", str(package), f"{remote.SSH}:{HOME}/"], check=True, timeout=300
    )
    return ps(
        VPS / "deploy.ps1",
        {
            "Install": quote(install),
            "Profile": quote(name),
            "Restart": "$true" if restart else "$false",
        },
    )


def install_watchdog(installs: list[str]) -> str:
    """Copy the watchdog and its list of installs to the VPS and register the scheduled task that runs it every 5 minutes."""
    tmp = Path(tempfile.gettempdir()) / "installs.txt"
    tmp.write_text("\n".join(installs) + "\n", encoding="utf-8")
    proc.run(
        ["ssh", remote.SSH, f"mkdir {HOME}"],
        capture_output=True,
        timeout=30,
        check=False,
    )  # exists already: harmless
    proc.run(
        ["scp", "-q", str(VPS / "watchdog.ps1"), str(tmp), f"{remote.SSH}:{HOME}/"],
        check=True,
        timeout=60,
    )
    return ps(VPS / "register.ps1", {})


def main() -> None:
    """Deploy a package, or install the watchdog; says what it would do unless --yes."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--package", type=Path, help="carpeta que dejó mt5.fleet.package")
    ap.add_argument(
        "--install",
        action="append",
        help="carpeta de instalación del terminal en la VPS (con --watchdog, una por terminal)",
    )
    ap.add_argument(
        "--restart",
        action="store_true",
        help="relanzar el terminal con el perfil (el play sigue siendo del dueño)",
    )
    ap.add_argument("--install-watchdog", action="store_true")
    ap.add_argument("--yes", action="store_true")
    a = ap.parse_args()
    if not a.install:
        raise SystemExit("falta --install <carpeta del terminal en la VPS>")
    what = (
        "tarea AlgoFleetWatchdog para " + ", ".join(a.install)
        if a.install_watchdog
        else f"paquete {a.package} → {a.install[0]}"
        + (" y reiniciar" if a.restart else "")
    )
    if not a.yes:
        raise SystemExit(
            f"simulacro: haría {what}. Repite con --yes cuando el dueño lo haya visto."
        )
    print(
        install_watchdog(a.install)
        if a.install_watchdog
        else push(a.package, a.install[0], a.restart)
    )


if __name__ == "__main__":
    main()
