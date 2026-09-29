---
q: MetaEditor64.exe compile silently does nothing under Wine, wine argument space splitting, NtQueryAttributesFile Program not found, MetaEditor shares terminal data folder lock, compile with terminal open, sqx_indicators ok false errors 0
tag: 🔬  date: 2026-09-29  see: eng/mt5-under-wine
---
# Two silent-success traps in MetaEditor64.exe under Wine — both exit 0 and compile nothing
- Wine does not requote a `wine <exe> arg…` argument with a space in it, and every prefix path has one (`Program Files`, `MetaTrader 5`): `/compile:C:\Program Files\...` truncates to `C:\Program`, exits 0, no log; quoting doesn't fix it. Fix: `wine.run(cwd=MQL5/)` + a relative argument (`/compile:Indicators\Foo.mq5`), no space up to that point (`mt5/wine.py::run()`'s `cwd`).
- MetaEditor also shares `terminal64.exe`'s data-folder lock: terminal up → exits 0, only the log's BOM, nothing compiled. `compile_path()` now checks `wine.terminal_running()` first and raises, instead of `{"ok": false, "errors": 0, "messages": []}`. SQX's 48 `Sq*` then compiled clean, 0 errors, 5 harmless warnings.

## Evidence
2026-09-29, Wine 11.18 staging, prefix `~/Desktop/MT5`: `wine MetaEditor64.exe /compile:"$(winepath
-w ~/.../MQL5/Indicators)"` with `WINEDEBUG=warn+all` → `NtQueryAttributesFile L"\??\C:\Program"
not found (c0000034)`, rc 0, no log. `cwd=.../MQL5`, args `/compile:Indicators /log:Indicators\
compile.log` → `MQL5/Indicators/compile.log` (UTF-16) with 48 `Result: 0 errors, …` lines,
timestamped 14:52-14:53. `logs/20260929.log`: `terminal64.exe` authorized on FTMO-Server4 at
08:45, still running through the afternoon (`ps -ef` PID confirmed); every `compile_path()` call
issued after that point produced only a 2-byte log, until the `wine.terminal_running()` guard
was added (verified: raises `SystemExit` while the terminal is up).
