---
q: fixed native block in template with generate random param; GenerateException Identification not found; random periods via one-item group; MABarClosesAbove period; frozen params in fixed slot still permuted by SPP
tag: 🔬  date: 2026-09-26  see: authoring/holes-groups-randomcondition, sqx-drive/spp-task-type
---
# A fixed block takes frozen params only; for random periods, bind a hole to a group of ONE item
`generate="random" randomValue="default"` on a fixed native block's param → builder refuses.
Frozen, it builds — with the SAME period in every strategy (100/100 at EMA 20, USDJPY 2026-09-25).
The owner wants periods random unless he names one: `sqx.templates.build` now puts the condition in a
one-item group (`<name>Signal`) with `generate="random"` on its numeric params and points the first hole at it.
Frozen ≠ invisible: the value becomes a strategy parameter, so SPP permutes it and `variants.scale` scales it.

## Evidence
- 2026-09-26, custodian, USDJPY H1, one-item group: EMA cross period 15 distinct values in 20 strategies (7–184);
  `MABarClosesAbove` Type fixed 1 in 15/15, Period 13 distinct; Keltner period 12 and deviation 8 distinct in 15.
  Every strategy carries the condition. Same fixed-block item with `generate` → the refusal below.
`MABarClosesAbove` in the fixed slot of `market_long` with random `#Period#`:
`GenerateException: Bad configuration - Identification not found in item 'MABarClosesAbove'`.
Without `generate`: 50/50 carry it (`template_check -n 50`). Stock `highest_breakout_template_daily_filter.sqx`
fixed `BarDayOfWeekIsNot` has no `generate` either. Strategy params appear as `MABarClosesPeriod1`, `MABarClosesType1`.
🤔 Untested whether adding `#Identification#` to the Item unblocks it.
