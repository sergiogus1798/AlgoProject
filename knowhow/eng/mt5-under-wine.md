---
q: MetaTrader 5 on Linux, Wine, mt5linux.sh official install, MetaTrader5 python package Windows only, SQX EA needs Sq indicators, SqATR iCustom compile error, terminal data folder origin.txt, strategy tester command line
tag: 📓  date: 2026-09-27  see: export/feed-clock-timezones
---
# MT5 runs under WineHQ staging; SQX's EAs need SQX's Sq* indicators; the Python API is Windows-only
- Official route: MetaQuotes' `mt5linux.sh` = WineHQ `winehq-staging` (root) + prefix set to win11, WebView2, `mt5setup.exe`. Ours: `bin/mt5-wine-system.sh` + `bin/mt5-install.sh`.
- An SQX MQL5 export calls `Sq*` custom indicators: copy `<SQX>/custom_indicators/MetaTrader5/{Indicators,Include}` into `MQL5/` and compile, or the EA fails.
- The `MetaTrader5` pip package ships only Windows wheels → a Windows Python inside the prefix (`mt5/winside/`).
- It does not drive the Strategy Tester: that is `terminal64.exe /config:<ini>` with `ShutdownTerminal=1`, report in the data folder.
- The data folder is `AppData/Roaming/MetaQuotes/Terminal/<hash>`, the one whose `origin.txt` (UTF-16) names the install — not Program Files, unless `/portable`.

## Evidence
`curl https://download.mql5.com/cdn/web/metaquotes.software.corp/mt5/mt5linux.sh` (2026-09-27): `WINE_VERSION="staging"`,
jammy → `winehq-jammy.sources`, `apt upgrade -y` of the whole system, prefix `~/.mt5` hard-coded.
`ls ~/Desktop/SQX/custom_indicators/MetaTrader5/Indicators` → 48 `Sq*.mq5`; identical in SQX_w1.
PyPI `MetaTrader5` 5.0.6231: wheels cp36–cp314, all `win_amd64`.
Not yet tested against a running terminal (OPEN.md #78) — the tester and origin.txt points come from MT5's docs.
