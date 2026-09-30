---
q: switch MT5 account without clicking, log into saved account python MetaTrader5 initialize login server no password, tester ini [Common] Login Server, several prop firm accounts one terminal, initialize hangs, wine.run never returns, terminal started by initialize holds stdout, close terminal WM_CLOSE taskkill
tag: 🔬  date: 2026-09-29  see: eng/mt5-tester-unattended, eng/mt5-under-wine
---
# One MT5 terminal logs into each saved account by itself — but start it detached first
- The terminal keeps each account's password in `Config/accounts.dat`. `mt5.initialize(login=N, server=S)` with no password logs the running terminal into that account; `account_info().login` confirms it. FTMO `FTMO-Server4` and Hantec `HantecMarketsMU-MT5` switched back to back, no click.
- ⚠️ **Never let `initialize(path=…)` start the terminal from `wine.run`.** The terminal becomes the Windows Python's child, inherits its stdout pipe, and `subprocess.run(capture_output=True)` waits for EOF as long as the terminal lives: a silent hang, 10 min until killed. `mt5.wine.open_terminal()` starts it detached (`start_new_session`, stdio to /dev/null) and waits ~5 s after it is listed; `initialize` then only attaches.
- The tester switches the same way: a `[Common]` section with `Login=` and `Server=` (no password) before `[Tester]` in the `/config:` ini (`mt5.tester.start(account=…)`). The terminal stays on that account afterwards.
- Closing it: `taskkill.exe /IM terminal64.exe` without `/F` posts WM_CLOSE and the terminal exits cleanly within seconds (`mt5.wine.close_terminal()`); SIGTERM only as a fallback.
- Both accounts on 2026-09-29: USD, leverage 1:50, gold `XAUUSD` (FTMO) and `XAUUSD.h` (Hantec), swap in points (mode 1), triple on Wednesday.

## Evidence
2026-09-29 19:31, first try with `initialize(path=terminal64.exe, login, server)` from `wine.run`: the terminal's log shows `'541350656': authorized on FTMO-Server4` at 19:31:07, the Python call never returned; `timeout 600` killed it with no output. After `open_terminal()`: `conditions.read("XAUUSD", ftmo)` → spread 41, point 0.01, swap -90.35/-4.2 mode 1, `account` → 541350656 FTMO-Server4 USD 50; then `read("XAUUSD.h", hantec)` → spread 26, swap -82/-8, `account` → 8063673 HantecMarketsMU-MT5 USD 50; `close_terminal()` → True. Whole run under 2 min.
