---
q: how much history does MT5 have for a symbol; first bar date on a prop firm server; copy_rates Terminal Call failed -1; Desde MT5 in Verificar; symbol_select sync wait; FTMO Hantec USDJPY history start
tag: 🔬  date: 2026-09-30  see: eng/mt5-symbols-csv-only-had-one-row, eng/mt5-account-switch-unattended
---
# A server's history depth is its first MN1 bar — after `symbol_select` and a wait, or the call fails
`mt5/winside/query.py` verb `first`: `symbol_select`, then `copy_rates_from_pos(sym, MN1, 0, 1000)`
retried once a second up to 20 s; the first bar's day is how far back that server goes. Right after
the terminal logs into an account, every `copy_rates_*` on a symbol answers `(-1, 'Terminal: Call
failed')` until it has synced — a range call from 1990 fails the same way. «Verificar» with Desde =
`MT5` (`mt5.verify.run.earliest`) starts at the latest of the firms' first bars and SQX's `data.from`.

## Evidence
- 🔬 2026-09-30: without the wait, both firms answered `Call failed`; with it, USDJPY on FTMO
  (FTMO-Server4) from 2000-03-01, `USDJPY.h` on Hantec (HantecMarketsMU-MT5) from 2008-07-01.
