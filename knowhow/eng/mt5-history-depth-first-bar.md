---
q: how much history does MT5 have for a symbol; first bar date on a prop firm server; copy_rates Terminal Call failed -1; Desde MT5 in Verificar; History Quality 22%; tester trades nothing for years; M1 copy_rates one row max bars; whole H1 weeks
tag: 🔬  date: 2026-09-30  see: eng/mt5-symbols-csv-only-had-one-row, eng/mt5-account-switch-unattended
---
# A server's usable history starts at its first month of whole H1 weeks — not its first monthly bar
`mt5/winside/query.py` verb `first`: the months from the first MN1 bar to now, halved until the
first whose second week holds ≥ 100 H1 bars (120 whole). Monthly bars reach further back than the
tester can trade, the terminal serves M1 only for its last «max bars» (one row for anything older),
and a freshly selected symbol answers `(-1, 'Terminal: Call failed')` until synced (retried).
«Verificar» with Desde = `MT5` (`mt5.verify.run.earliest`) starts at the latest firm's month.

## Evidence
- 🔬 2026-09-30, USDJPY: MN1 from 2000-03 (FTMO) and 2008-07 (Hantec). H1 bars per week: Hantec
  5 in 2008-2022-01, 120 from 2022-07; FTMO 120 from 2016 (1 in 2010: the terminal's cap). The
  tester on Hantec over 2008-07→2026-09: «History Quality 22 %», 30,200 H1 bars, first trade
  2022-06-08 (457 trades vs SQX 1,903). Bisection now: FTMO 2010-09-01, Hantec 2022-06-01.
