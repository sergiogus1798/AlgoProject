---
q: build doctrine where in task XML; Param className after key; set_params returns substitutions zero; task sessions differ per task; ExitAfterBars in bars per timeframe; which sections a Retest task has; high precision crosscheck spread 0; YAML on: key True
tag: 🔬  date: 2026-09-23  see: authoring/bar-exit-ignores-task, costs/sessions-per-asset, costs/per-task-costs
---
# Build doctrine lives in `<Setup>` plus four sections; patterns must match `<Param key= className=>`
Trading-option params are `<Param key="ExitOnFriday" className="ExitOnFriday">true</Param>`; a pattern
for `<Param key="X">` silently matches nothing. `sqx/projects/doctrine.py` `set_params()` returns the
substitution count — 0 is the alarm.
A task naming a session its own `<Resources><Sessions>` lacks loads silently on another schedule: copy the definition, not just `MarketOpenSession`.
Retest tasks must match the build on `<MoneyManagement>`, `<BuildTradingOptions>`, `<CrossChecks>`, `<StopCondition>`.

## Evidence
Measured on donor `XAUUSD_base_2026-09-21` and owner's model `XAUUSD_Breakout_H1`, verified on 20
strategies from `algo_XAU_doctrina_smoke`.
- The `className` miss went unseen because the donor already had good values; found by diffing two tasks.
- Donor: `Build` defines `XAUUSD_the5ers`, `Retest-Task6` defines `XAUUSD_ftmo`.
- `ExitAfterBars` is in bars: 24 = one day on H1, 12 h on M30. Range declared in hours in `_build.yaml`, converted per task.
- Only `Build` has `<Blocks>`, `<SLPTOptions>`, `<BuildMode>`, `<Chart name="Main chart">`.
- High-precision crosscheck has its own `<Spread>` under `CustomSpread=true`; donor ships `0` → reruns the strategy free and calls it robustness.
- 🤔 YAML 1.1: `crosschecks: on: [...]` parses as `{True: [...]}`; key is named `enabled`.
