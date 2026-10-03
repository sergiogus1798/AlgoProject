"""The two calls to the VPS over `ssh vps`: pull the beacon's files, run the health probe."""

import json
import subprocess
from pathlib import Path

SSH = "vps"
FLEET_FOLDER = "AppData/Roaming/MetaQuotes/Terminal/Common/Files/fleet"   # relative to the VPS user's home
PROBE = Path(__file__).parent / "vps" / "probe.ps1"
POWERSHELL = 'powershell -NoProfile -Command "$input | Out-String | Invoke-Expression"'


def pull(into: Path) -> bool:
    """Copy the beacon's `*.json` files from the VPS into `into`; False when the VPS does not answer."""
    done = subprocess.run(["scp", "-q", "-o", "ConnectTimeout=10", f"{SSH}:{FLEET_FOLDER}/*.json", str(into)],
                          capture_output=True, text=True, timeout=50)
    return done.returncode == 0


def probe() -> dict | None:
    """The VPS's RAM, CPU, disk, uptime and each terminal's process and log; None when it does not answer."""
    done = subprocess.run(["ssh", "-o", "ConnectTimeout=10", SSH, POWERSHELL], input=PROBE.read_text(),
                          capture_output=True, text=True, timeout=90)
    return json.loads(done.stdout) if done.returncode == 0 else None
