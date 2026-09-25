---
q: fixed native block in template with generate random param; GenerateException Identification not found; MABarClosesAbove period; frozen params in fixed slot still permuted by SPP
tag: 🔬  date: 2026-09-24  see: authoring/holes-groups-randomcondition, sqx-drive/spp-task-type
---
# A fixed native block in a template takes frozen params only — no `generate="random"`
`generate="random" randomValue="default"` on a fixed native block's param → builder refuses.
Frozen, it builds and the block appears in every strategy. Variation comes from the random hole and exits.
Frozen ≠ invisible: the value becomes a strategy parameter, so SPP permutes it and `variants.scale` scales it.

## Evidence
`MABarClosesAbove` in the fixed slot of `market_long` with random `#Period#`:
`GenerateException: Bad configuration - Identification not found in item 'MABarClosesAbove'`.
Without `generate`: 50/50 carry it (`template_check -n 50`). Stock `highest_breakout_template_daily_filter.sqx`
fixed `BarDayOfWeekIsNot` has no `generate` either. Strategy params appear as `MABarClosesPeriod1`, `MABarClosesType1`.
🤔 Untested whether adding `#Identification#` to the Item unblocks it.
