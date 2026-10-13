---
q: Does a retest status of «Failed 30, Passed 0» mean the strategies are missing from the output databank?
kw: Failed 30 Passed 0, Rejected 100 %, retest zero trades, silenced acceptance, 0-trade strategy in OOS, status Failed Passed not presence
tag: 🔬  date: 2026-10-13  see: databanks/databank-verbs
---
# A retest with zero trades still lands in the output databank while its status says «Failed 30 / Passed 0»
Trap: reading the task status as presence. With the acceptance conditions silenced, every retested strategy
is written to the output databank, 0-trade ones included. Count `.sqx` files (or `-databank action=export`), never `Passed`.

## Evidence
- 🔬 conductor, 2026-10-13, encargo 66 session 1: OOS task window 2018.01.02-04 on 30 strategies: 30 in `Results` → 30 `.sqx` in `OOS`,
  10 with 0 trades (orderstocsv CSV = header only); status «Rejected 100 %, Failed 30, Passed 0».
