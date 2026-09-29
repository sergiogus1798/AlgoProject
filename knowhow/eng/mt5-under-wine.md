---
q: MetaTrader 5 on Linux, Wine, mt5linux.sh official install, MetaTrader5 python package Windows only, IPC send failed -10001, SQX EA needs Sq indicators, SqATR iCustom compile error, terminal data folder origin.txt portable.txt, built-in MCP port 22346 401, strategy tester command line
tag: 🔬  date: 2026-09-29  see: export/feed-clock-timezones, eng/metaeditor-compile-under-wine
---
# MT5 runs under WineHQ staging; SQX's EAs need SQX's Sq* indicators; the Python API is Windows-only
- Official route: MetaQuotes' `mt5linux.sh` = WineHQ `winehq-staging` (root) + prefix set to win11, WebView2, `mt5setup.exe`. Ours: `bin/mt5-wine-system.sh` + `bin/mt5-install.sh`.
- An SQX MQL5 export calls `Sq*` custom indicators: copy `<SQX>/custom_indicators/MetaTrader5/{Indicators,Include}` into `MQL5/` and compile, or the EA fails — compiling them under Wine has its own traps, `eng/metaeditor-compile-under-wine`.
- The `MetaTrader5` pip package ships only Windows wheels → a Windows Python inside the prefix (`mt5/winside/`).
- It does not drive the Strategy Tester: that is `terminal64.exe /config:<ini>` with `ShutdownTerminal=1`, report in the data folder.
- Data folder: `AppData/.../Terminal/<hash>` whose `origin.txt` (UTF-16) names the install — but if it holds `portable.txt` (as `mt5setup.exe` leaves it under Wine) the data is in the install folder itself.
- `initialize()` → `(-10001, 'IPC send failed')` until the terminal is up **and logged in**; with `path=` it launches a terminal — never pass it.
- Build 6231 runs its own MCP on 127.0.0.1:22346 (`Server: MetaTrader5-MCP`, 401 Bearer): token and AI trading permissions are set in the terminal.

## Evidence
`curl https://download.mql5.com/cdn/web/metaquotes.software.corp/mt5/mt5linux.sh` (2026-09-27): `WINE_VERSION="staging"`,
jammy → `winehq-jammy.sources`, `apt upgrade -y` of the whole system, prefix `~/.mt5` hard-coded.
`ls ~/Desktop/SQX/custom_indicators/MetaTrader5/Indicators` → 48 `Sq*.mq5`; identical in SQX_w1.
PyPI `MetaTrader5` 5.0.6231: wheels cp36–cp314, all `win_amd64`.
2026-09-29, Wine 11.18 staging, build 6231, Hantec funded account: account/symbols/symbol/bars via `mt5/live.py` answer; IPC failed while not logged in; `portable.txt` present; `curl -v 127.0.0.1:22346` → 401. Tester itself not yet run — terminal open, real funded account logged in (OPEN.md #78).
