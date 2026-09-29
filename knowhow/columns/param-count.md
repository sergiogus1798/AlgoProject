---
q: Param Count column meaning, ParameterCount snippet counts, ParamTypeShift noise, MagicNumber counted, ParametrizationTypes list, transformToVariables, hardcoded strategies no variables, Python mirror of Param Count, param_count core.sqxfile, old frozen strategies stale count
tag: 🔬  date: 2026-09-29  see: columns/custom-columns-stored, sqx-format/declared-parameters
---
# "Param Count" counts only Period, Constant, EntryLevel, OtherParam and ExitUsed (since 2026-09-06)
The old count included ~8 noise items of every 14 (5 signal/magic variables + Shift, always 1). The fix
filters the **result** of `StrategyBase.transformToVariables(symmetry, paramTypes)` by
`Variable.getParamType()` — a filter on the input map is not enough. Keep the transform: counting
`<Variables>` alone scores hardcoded strategies 0.

## Evidence
600 `.sqx` sampled from every project's databanks:

| in the count | per strategy | searched parameter? |
|---|---|---|
| `MagicNumber` + `Long/ShortEntrySignal` + `Long/ShortExitSignal` | exactly 5 | no — no `paramType` |
| `ParamTypeShift` | 3.25 | no — 1286 of 1286 have value 1 |
| `ParamTypePeriod`, `Constant`, `OtherParam`, `EntryLevel` | ~4.6 | yes — periods, levels, deviations, session hours |
| `ParamTypeExitUsed` | ~1 | yes — `ExitAfterBars` (10 distinct), SL/PT/TS coefficients (~27) |

- A variable already in the XML survives the transform whatever `paramTypes` says
  (`VariablesTransformer.tryFixVariableAttributes` returns early).
- Vocabulary (`ParametrizationTypes`, `internal/libs/SQTradingLib.jar`): `ParamTypeRecommended`, `Boolean`,
  `Constant`, `EntryLevel`, `EntryLogic`, `ExitUnused`, `ExitUsed`, `OtherParam`, `Period`, `Shift`,
  `TradingOptions` — same strings as `<variable><paramType>` in `strategy_Portfolio.xml`.
- 26 % of strategies on disk (103 of 400 sampled, all `GBPJPY_H1`) store no typed variable.
- Stored value is frozen: the new logic applies only to results computed after the change.
- **Fixed in Python 2026-09-29 (OPEN #17), no SQX GUI involved.** `core.sqxfile.param_count(path)`
  mirrors the same rule off `strategy_Portfolio.xml` directly — count `<variable><paramType>`
  in `COUNTED_PARAM_TYPES` (Period, Constant, EntryLevel, OtherParam, ExitUsed) — and is right
  for a strategy of any age, since it never reads SQX's frozen `ParameterCount`. `core.sqxview.
  frame()` overwrites `Param Count (IS)` with it and adds `Param Count source` so the column
  never passes for SQX's own number. Known-answer test: `tests/test_param_count.py` against
  `tests/fixtures/strategy.sqx` (4 `ParamTypePeriod` + 3 `ParamTypeExitUsed` = 7).
