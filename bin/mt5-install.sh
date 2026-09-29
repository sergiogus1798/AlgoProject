#!/bin/bash
# mt5-install — the user half of MetaQuotes' official mt5linux.sh: a Wine prefix set to
# Windows 11, the WebView2 runtime, and the generic MetaQuotes MetaTrader 5 terminal. Then,
# ours: a Windows Python in the same prefix with the MetaTrader5 package, which only exists
# for Windows and is how mt5/live.py reads the terminal. Each step is skipped when done.
#
# Same steps and URLs as the official script (fetched 2026-09-27); the one change is the
# prefix, which comes from mt5_prefix in config/machine.yaml (asked to core/paths.py)
# instead of the hard-coded ~/.mt5. Needs Wine: bin/mt5-wine-system.sh first.
#
# mt5setup.exe opens its own window: accept the licence and the default folder. When the
# terminal starts, it offers MetaQuotes' demo server — the account is opened there, by hand.
#
# Usage:  bin/mt5-install.sh
set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
URL_MT5="https://download.mql5.com/cdn/web/metaquotes.software.corp/mt5/mt5setup.exe"
URL_PYTHON="https://www.python.org/ftp/python/3.12.10/python-3.12.10-amd64.exe"
MT5_PACKAGE="MetaTrader5==5.0.6231"
URL_WEBVIEW="https://msedge.sf.dl.delivery.mp.microsoft.com/filestreamingservice/files/f2910a1e-e5a6-4f17-b52d-7faf525d17f8/MicrosoftEdgeWebview2Setup.exe"

command -v wine >/dev/null || { echo "wine not found: run bin/mt5-wine-system.sh first"; exit 1; }

# core/paths.py is the only place that knows where things live.
mapfile -t _WHERE < <(cd "$ROOT" && python3 -c '
from core.paths import MT5_PREFIX, MT5_DATA
print(MT5_PREFIX); print(MT5_DATA)')
export WINEPREFIX="${_WHERE[0]}"
MT5_DATA="${_WHERE[1]}"
TERMINAL="$WINEPREFIX/drive_c/Program Files/MetaTrader 5/terminal64.exe"
PYTHON="$WINEPREFIX/drive_c/Python/python.exe"
DL="$MT5_DATA/installers"
mkdir -p "$DL"

install_python() {
  if [ ! -f "$PYTHON" ]; then
    echo "Install Windows Python 3.12 in C:\\Python"
    curl -fL "$URL_PYTHON" --output "$DL/python-amd64.exe"
    wine "$DL/python-amd64.exe" /quiet InstallAllUsers=0 'TargetDir=C:\Python' \
      PrependPath=0 Include_test=0 Include_launcher=0 Include_tcltk=0
  fi
  echo "Install $MT5_PACKAGE in the Windows Python"
  wine "$PYTHON" -m pip install --disable-pip-version-check -q "$MT5_PACKAGE"
}

if [ -f "$TERMINAL" ]; then
  echo "MetaTrader 5 already installed in $WINEPREFIX"
  install_python
  exit 0
fi

echo "Download MetaTrader and WebView2 Runtime -> $DL"
curl -fL "$URL_MT5" --output "$DL/mt5setup.exe"
curl -fL "$URL_WEBVIEW" --output "$DL/webview2.exe"

echo "Set environment to Windows 11 in $WINEPREFIX"
winecfg -v=win11

echo "Install WebView2 Runtime"
wine "$DL/webview2.exe" /silent /install

echo "Install MetaTrader 5 (its installer opens a window)"
wine "$DL/mt5setup.exe" || true   # it exits non-zero even when it installed; the check below decides

[ -f "$TERMINAL" ] || { echo "installer closed without $TERMINAL"; exit 1; }
echo "installed: $TERMINAL"
install_python
