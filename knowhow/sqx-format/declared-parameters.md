---
q: strategy tunable parameters list, variable paramType, SPP permutation ranges per class, ParamTypeShift 0..6, percentage range collapses small integers, inert parameter detection, engine deterministic
tag: 🔬  date: 2026-09-21  see: sqx-format/writing-a-variant, sqx-format/optimization-profile-bin, columns/param-count
---
# A strategy's tunable parameters = its `<variable>`s with a non-empty `<paramType>`
That list in `strategy_Portfolio.xml` is authoritative — it matches what SPP permutes one for one; no
block-catalog lookup. SQX ranges are per class: Period/Constant/ExitUsed get ±% of the original; every
`ParamTypeShift` gets flat **0..6**. ⚠️ A percentage range collapses on small integers — a
percentage-only generator makes a far coarser grid than it thinks. Inert parameters are detectable
cheaply from the permutation table; drop them.

## Evidence
- Each `<variable>`: `id`, `name`, `type` (`int`|`double`), `value`, `paramType`. Values seen:
  `ParamTypePeriod`, `ParamTypeShift`, `ParamTypeConstant`, `ParamTypeOtherParam`, `ParamTypeExitUsed`
  — exactly the classes a task's `<WhatToParametrize>` switches on. Checked on all 5 XAUUSD SPP
  strategies: 8/8, 11/11.
- Non-tunables (`MagicNumber`, the four direction booleans) have a UUID `<id>` and empty `<paramType />`;
  tunables have their own name as id. `Strategy 17.9.39`: 8 tunables of 13; USDCHF fixture 7 of 9.
- Ranges (settings ±30 %, 20 steps), off stored permutation domains: `DICrossPeriod1` 67 → 46..88,
  `ATRPrcRnkCrsDwnLvl1` 48.76 → 34.13..63.20 (2 decimals). `MomentumPeriod1` = 14 → only 10 distinct
  values of 20 steps; `IsBars1` = 3 → 5.
- Inert test: group permutations by all params but one; groups of >1 differ only in that one.
  `CBlock_SqzMmnInt21` on `Strategy 17.9.39`: **757/757** groups byte-identical `NetProfit` and trade
  count; `Strategy 23.16.37` 338/338; `Strategy 41.5.25` 287/302 (nearly inert). Dropping it shrinks
  grids 13×. Also proves the engine is deterministic to the last decimal.
