---
q: What does `<BuildingBlocks>` in the Build task gate: free holes only, or fixed blocks too?
kw: which blocks can the builder sample; stop/limit entry blocks with market orders; clock calendar blocks never on; union of two palettes; BuildingBlocks in Build task use weight category; signals indicators stopLimitBlocks; use=false ignored by group-bound hole; fixed block outside switches; frozen donor BuildingBlocks stale; talib unreachable
tag: 🔬  date: 2026-10-11  see: authoring/block-vocabulary, authoring/holes-groups-randomcondition, authoring/simple-strategy-build-xml
---
# `<BuildingBlocks>` in the Build task gates only FREE holes and generic generation
Per-task `<Blocks><BuildingBlocks>`: 844 `<Block key= weight= use= category=>`. A `RandomCondition`
bound to a group samples the group regardless of `use="false"`; a template's fixed block ignores the list entirely. To narrow a group-bound template, choose/author the group — switches silently do nothing there.
A frozen donor's list lacks blocks authored after the freeze; SQX builds with them anyway (`sqx/blocks/taxonomy.py` adds them back).
`sqx/projects/buildingblocks.py` writes it from a palette (2026-10-01; `--palette a,b` = their union), prefix stripped to the taxonomy key.
🔬 2026-10-02: a palette with `unlabelled: off` + `overrides` is a SHORTLIST — `palette.resolve` switches off every block not listed. Before that fix the full labelling of 2026-10-01 (752 blocks got a neutral 1) made every curated palette resolve to ~575 conditions, clock blocks and stop/limit levels included; anything applied between 2026-10-01 22:41 and the fix was built wide. Guard: `tests/test_palettes_families.py`.
Rule 15 is in `rewrite` (2026-10-02): a `category="stopLimitBlocks"` entry and a clock/calendar block (`buildcensus.CLOCK`) are never switched on, whatever the palette says — a dual-role value (Close, SessionHigh, ATR…) comes on as indicator only; the refusals are printed. A stop/limit level is only the PRICE of a pending entry: whether one can be placed is `<OrderTypes>` (`EnterAtStop`, `EnterAtLimit`), which the doctrine keeps off (`order_types: [EnterAtMarket]`). With no palette applied a project keeps the donor's list (400 conditions, 26 values, 10 levels on): count with `buildingblocks --count`.
🔬 SQX ignores palette weights for generic comparators / value blocks (69 % of conditions, 2.4 % of weight); v3 palettes carry named signal blocks only (Evidence).

## Evidence
- 🔬 2026-10-02 pilot: SQX does **not** honour palette weights for the generic comparison operators / value blocks — 69 % of entry conditions were a comparator on one of two values, though they were 2.4 % of the weight. Among **named signal blocks** weights are honoured (77.5 : 10.8 : 11.7 used vs 78.0 : 13.0 : 8.9 by weight), so the v3 family palettes (`*_base_v3`, 99-127 blocks) carry named signal blocks only.
- Pilot: `AlgoData/scratch/calib2/` (deleted 2026-10-04) (`PILOT_READY`; `synth_final/synthesis.md` §0b repeats the test on the final populations).
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
- 🔬 2026-10-02, read in the snippets' Java and `customBlocks.xml`: `TTMSqueeze.Squeeze` = 1 when Bollinger sits inside
  Keltner, so `CBlock_SqueezeOn` (> 0.5) is compression; the four native `TTMSqueezeMomentum*` fire only while the
  squeeze is ON (breakout, not momentum); CSSA high = range; `CBlock_BullishMarubozu(_2)` compares a body in price
  units and Close/High > 0.9 — not a marubozu, kept out of the five `_v3` palettes (90-150 blocks, same test).
🔬 2026-10-11 (owner): `buildcensus.CLOCK_NAMES` adds `CBlock_TimeBreakoutLong`, `CBlock_TimeBreakoutLong_2`, `SessionHigh`, `SessionLow`, `SessionOpen`, and (owner, 2026-10-13) `SessionClose`, `VolumeProfileCustomHours`, `VolumeProfileCustomHoursMultiSession` — the regex alone cannot see custom blocks. The builder also refuses a template whose FIXED blocks are clock (`buildrules.clock_fixed`).
