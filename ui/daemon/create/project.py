#!/usr/bin/env python3
"""«+ Nuevo proyecto»: hard rule 5, then `sqx.projects.builder --workflow` on the custodian.

    python3 -m ui.daemon.create.project Test_XAUUSD_x_H1 --template T --symbol XAUUSD \
        --timeframe H1 --max-strategies 500 --minutes 180 --purpose "..."
"""

import argparse
import subprocess
import sys

from core.datapaths import template_dir
from core.paths import ROOT


def main() -> None:
    """Check the asset (rule 5), then build and install every workflow task."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("name")
    ap.add_argument("--template", required=True, help="la plantilla de la librería, por nombre")
    ap.add_argument("--symbol", required=True)
    ap.add_argument("--timeframe", required=True)
    ap.add_argument("--max-strategies", required=True)
    ap.add_argument("--minutes", required=True)
    ap.add_argument("--purpose", required=True)
    a = ap.parse_args()
    got = subprocess.run([sys.executable, "-m", "core.assets", a.symbol], cwd=ROOT)
    if got.returncode:
        sys.exit(f"core.assets {a.symbol} salió con {got.returncode}: no se crea nada (regla 5)")
    sys.exit(subprocess.run(
        [sys.executable, "-m", "sqx.projects.builder", a.name, "--purpose", a.purpose,
         "--template", str(template_dir(a.template) / "template.sqx"), "--symbol", a.symbol,
         "--timeframe", a.timeframe, "--max-strategies", a.max_strategies,
         "--minutes", a.minutes, "--role", "custodian", "--workflow"], cwd=ROOT).returncode)


if __name__ == "__main__":
    main()
