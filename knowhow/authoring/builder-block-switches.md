---
q: which blocks can the builder sample; BuildingBlocks in Build task use weight category; signals indicators stopLimitBlocks; use=false ignored by group-bound hole; fixed block outside switches; frozen donor BuildingBlocks stale; talib unreachable
tag: 🔬  date: 2026-09-24  see: authoring/block-vocabulary, authoring/holes-groups-randomcondition
---
# `<BuildingBlocks>` in the Build task gates only FREE holes and generic generation
Per-task `<Blocks><BuildingBlocks>`: 844 `<Block key= weight= use= category=>`. A `RandomCondition`
bound to a group samples the group regardless of `use="false"`; a template's fixed block ignores the list entirely.
To narrow a group-bound template, choose/author the group — switches silently do nothing there.
A frozen donor's list lacks blocks authored after the freeze; SQX builds with them anyway (`sqx/blocks/taxonomy.py` adds them back).
Nothing in this repo reads or writes `<BuildingBlocks>` (as of 2026-09-24).

## Evidence
Donor `AlgoData/projectsBackup/XAUUSD_base_2026-09-21`; `Build-Task3.xml` 2.9 MB vs Retest 40 KB.
| `category` | entries | keys | gates | on in donor |
|---|---|---|---|---|
| `signals` | 588 | `ADXCrossUp`, `CBlock_BBBreakoutUp` | entry/exit condition | 400 |
| `indicators` | 171 | `Indicators.ADX`, + 23 comparators bare | value to compare | 26 |
| `stopLimitBlocks` | 85 | `Stop/Limit Price Levels.EMA`, `…Ranges.ATR` | stop/limit price | 10 |
- Prefixes are a namespace: `Indicators.ATR`, `Stop/Limit Price Ranges.ATR` → one `ATR`. All 844 resolve into
  the 1,020 catalogue; all 171 own blocks present. 253 natives in no category (Actions, Functions,
  Bar/Time values, Strategy Control values, all 158 `talib_*`) — unreachable from generation.
- `weight` = 1 on all 844 (soft knob never used).
- Test `blocktest_grupoA` (custodian, donor untouched, template `TrendRegimeFilters_EntryOnly.sqx` =
  `AND(RandomCondition(group=TrendRegimeFilters), RandomCondition(free))`, all 6 group members `use="false"`, 30 strategies, 21 s):
  | hole | bound | result |
  |---|---|---|
  | `RandomConditionFilter1` | `TrendRegimeFilters` | 30/30 `CBlock_CSSARegimeAbove50` (`use="false"`) |
  | `RandomCondition2` | none | 98 fills, 28 blocks, 97/98 `use="true"` |
  The one off-block in the free hole was the one the bound hole forced in (evolution copying across slots).
- Fixed block: `CBlock_CloseCrossesAboveKCUpper` absent from donor list (authored 2026-09-22) → in 29/29 of `smoke_keltnerUpperCrossUp`.
- 85 `indicators` entries carry `indicatorMin/Max/Step`; `<Calibration calibrateBeforeStart="true" maxSteps="50"/>`
  recalibrates before each run, so cloned ranges aren't stale on a new asset.
