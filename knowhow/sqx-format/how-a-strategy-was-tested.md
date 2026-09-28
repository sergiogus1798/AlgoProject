---
q: how was a strategy tested, backtest costs of a strategy, lastSettings.xml task config, settings.xml trading options ExitOnFriday FridayExitTime, MoneyManagement.UseFromStrategy, Symbol Portfolio, HHMM vs seconds, generic builder AND with attributes, logic.conditions misses AND, strategy metadata
tag: 🔬  date: 2026-09-27  see: sqx-format/sqx-zip-members, costs/per-task-costs, sqx-format/rewriting-strategy-logic
---
# A .sqx carries the task it was last tested with: `lastSettings.xml` is that task's XML
- `lastSettings.xml` = a task `<Settings>` like a `.cfx` member (Setup: window, `<Chart>` spread, slippage,
  commission, swap; sizing; Databanks). The stored numbers ran on it; the `.cfx` is today's task.
- `settings.xml` stamps flat scalars, times **HHMM** (`FridayExitTime 2100`; seconds, 75600, in lastSettings).
  `MoneyManagement.UseFromStrategy` false → the task's sizing, not the strategy's. `Symbol` may read `Portfolio`.
- ⚠️ Generic builds write `<Item key="AND" generated=…>` with bare `<Item>` terms: `sqx.structural.logic`
  reads that signal as ONE condition keyed `AND`. Reader for all this: `sqx.inspect.strategymeta`.

## Evidence
- 609 `.sqx` (≤15 per databank, all three installs, 2026-09-27): `lastSettings` output databank =
  the folder on XAUUSD/OOS; 609/609 one sizing method on; commission methods on: 421 one, 185 none,
  **3 both**; `Symbol` = `Portfolio` on 135 while `<Chart>` names the feed on all 609.
- Same strategy (XAUUSD Strategy 10.13.25): FridayExitTime 2100 ↔ 75600, EODExitTime 2304 ↔ 83040,
  DontTradeOnWeekends FridayCloseTime 38 ↔ 2300 (2300 s = 00:38 — someone typed HHMM into seconds; option off).
- `logic.conditions` vs the tree walk: 304 equal, 298 differ, every one the generic `AND` above.
- `.cfx` tasks without `Data/Setups/Setup`: AutomaticRetest keeps its setup (spread, slippage, commission,
  often no `<Swap>`) under `CustomData/Setups/Setup`; CustomAnalysis has no setup and writes Results/OOS too.
