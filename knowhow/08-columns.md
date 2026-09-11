# Custom databank columns (snippets)

What a metric column of your own really is, and the one property that decides how you use it: **its
value is frozen into the `.sqx` when the strategy's result is computed.**

## Where they live

- `…/user/extend/Snippets/SQ/Columns/Databanks/<Name>.java` — one class per column, extending
  `DatabankColumn`. 13 on this install (`ParameterCount`, `DoFRatio`, `PSR`, `TRLRatio`, …).
- 🔬 SQX compiles them **at startup**, into `internal/tmp/compiled/SQ/Columns/Databanks/<Name>.class`.
  Editing the `.java` while an instance runs is safe — nothing reads it until the next start — and
  both installs need their own copy: `SQX/user/extend` and `SQX_w1/user/extend` are separate trees.
- 🔬 They cannot be compiled outside SQX. `com.strategyquant.lib` (`ValuesMap`, `SettingsMap`) is in
  **no jar** under `internal/libs`, so `javac -cp 'internal/libs/*'` fails on the imports; the only
  compile check is starting an instance and looking for the `.class` timestamp.
- A view refers to a column by its **class name**: `<Column class="ParameterCount" name="Param Count" …/>`
  in `user/settings/views/databanks/*.vw`. `name=` is only the header text.

## 🔬 The value is stored, not computed on demand

Measured 2026-09-06 on `XAUUSD/SPP OOS` (165 strategies), by exporting the same databank three times
through the worker while changing the snippet in between:

| what was changed | exported values |
|---|---|
| the original `ParameterCount` | 16.80 mean, median 16 |
| a rewritten `ParameterCount` with different logic | **identical, strategy by strategy** |
| `compute()` replaced by `return 99.0` | **still identical** |
| a brand-new column class added to the view | **0 for all 165** |

- `compute()` is **not called** by `-databank action=export`, nor by loading a databank. The number
  comes from the strategy's own `settings.xml`, inside the base64 `SQStats` blob, keyed by the
  **class name** — `ParameterCount` is in there as an IEEE float next to `DoFRatio` and `PSR`.
- Consequences, and they are the whole point:
  - **Rewriting a column changes nothing for strategies that already exist.** It applies to results
    computed from then on — a new build, a retest, an optimisation.
  - **A column added later reads 0 on every older strategy**, with no warning and no blank cell.
  - Two exports of the same databank taken months apart can carry values from two different versions
    of the same snippet. The metrics CSV cannot tell you which.
- 🔬 There is **no recompute verb**: `-databank action=` offers list, count, save, load, delete,
  clear, create, remove, synctofiles, syncfromfiles, copy, move, export. Nothing recalculates stats.
  The only route for existing strategies is to run them through a task that recomputes results —
  or to compute the metric outside SQX, from `strategy_Portfolio.xml`.

## 🔬 What "Param Count" was counting, and what it counts now

`StrategyBase.transformToVariables(symmetry, paramTypes)` turns every parameter of the enabled types
into a variable and then `variables().size()` counts them — but the variable list **also holds
what was already there**, which is where the noise came from. Measured over 600 `.sqx` sampled from
every project's databanks:

| in the count | per strategy | is it a searched parameter? |
|---|---|---|
| `MagicNumber` + `Long/ShortEntrySignal` + `Long/ShortExitSignal` | exactly 5, always | no — they carry **no `paramType`** at all |
| `ParamTypeShift` | 3.25 | no — **1286 of 1286 occurrences have the value 1** |
| `ParamTypePeriod`, `ParamTypeConstant`, `ParamTypeOtherParam`, `ParamTypeEntryLevel` | ~4.6 | yes — periods, levels, deviations, session hours |
| `ParamTypeExitUsed` | ~1 | yes — `ExitAfterBars` (10 distinct values), SL/PT/TS coefficients (~27) |

So roughly **8 of every 14 counted "parameters" were noise**. Since 2026-09-06 the column counts only
Period, Constant, EntryLevel, OtherParam and ExitUsed, filtering the transformed list by
`Variable.getParamType()` — a filter on the **result** is required, because a variable already present
in the XML survives the transform whatever the `paramTypes` map says (`VariablesTransformer
.tryFixVariableAttributes` returns early for it).

- The full type vocabulary is in the `ParametrizationTypes` class of `internal/libs/SQTradingLib.jar`:
  `ParamTypeRecommended`, `Boolean`, `Constant`, `EntryLevel`, `EntryLogic`, `ExitUnused`, `ExitUsed`,
  `OtherParam`, `Period`, `Shift`, `TradingOptions`. The constants' values are the same strings that
  appear in `strategy_Portfolio.xml` under `<variable><paramType>`, so a whitelist can be checked
  against either side.
- 🔬 The transform is still needed: **26% of the strategies on disk (103 of 400 sampled, all from
  `GBPJPY_H1`) store no typed variable at all** — their numbers are hardcoded in the XML. Counting
  `<Variables>` alone would score them 0.

## 🔬 `EdgeDecayRatio` / `EdgeDecayFilter` — measured, and retired

Reconstructed on 2026-09-06 over the 10,000 rows of `metrics/XAUUSD/OOS/metrics.csv` (the snippet's
own formula, with `avgTrade` held neutral because that column is not exported). Four independent
defects, any one of which is disqualifying:

- **Net-profit decay is a calendar artifact.** `npDecay = (1 − NP_oos/NP_is)·100` compares a 10-year
  IS (2008-01-02…2017-12-29) with a 5-year OOS (2018-01-02…2022-12-30). A strategy with **zero**
  decay scores `npDecay = 50` → **14.3/100** on that item. Measured on the 177 strategies whose PF
  is flat across the split (PF 1.150 IS → 1.160 OOS), median `npDecay` is **56.1%**. Net profit must
  never enter a decay ratio; only length-robust quantities (PF, Sharpe, Sortino, Calmar, Win %) may.
- **The ratio inverts near zero.** `1 − X_oos/X_is` explodes when `X_is` ≈ 0, so the score rewards a
  weak in-sample Sharpe. Of the 144 rows scoring ≥65 with NP(OOS)>0, median `sharpeDecay` is
  **−136%** at a median Sharpe (IS) of only 0.24. ρ(PF_IS, pfDecay) = **+0.62**: what it calls decay
  is largely regression to the mean of the IS value.
- **It is not a decay score.** Only 20% of the weight (pillar 4) plus 9% of pillar 2 compares the two
  samples at all; 71% reads the OOS in absolute terms. Spearman of the total against Net profit (OOS)
  is **+0.78** and against Sharpe (OOS) **+0.75** — higher than against its own pillar 4 (+0.53).
- **Three implementations, three answers.** `compute()` (what sorts and filters) weights pillar 4
  40/30/30 including a `medianXS` MFE/MAE term and reads `Stability`/`PctDrawdown`/`ReturnDDRatio`
  from the **full sample**; `getValue()` (what you see) weights 50/50, drops `medianXS`, and reads
  them from the **OOS only**. `compute()` also builds a **per-trade** Sharpe and scores it against
  thresholds meant for the annualised one. With no IS present, `compute()` defaults `pfDecay` to 0
  (best) and `getValue()` to 100 (worst).

Combined with the frozen-value rule above — the column is not in `Export Data View`, so no metrics
export has ever carried it — the decision on 2026-09-06 was to **retire both the column and the
`EdgeDecayFilter` custom analysis** and do decay work in Python over the exported CSVs.
`EdgeDecayFilter` is wired into four projects (`AUDJPY`, `EURUSD`, `USDJPY`, `XAUUSD`); removing the
`.java` before it is unwired in the GUI would leave those tasks pointing at a missing method.


## 🔬 The `SQStats` blob is decodable, and the key mapping is now known

`settings.xml` inside a `.sqx` carries one `<SQStats version="2" e="b64">` blob per
`stats_LQ1_direction_DD_<dir>_L1_pl_DD_10_L1_sample_DD_<sample>_L1__RQ1_` element — so **every metric
SQX shows in a databank is readable off disk, at every sample type, with no instance running**.

The decoded blob is a flat record stream: a 1-byte type, a 1-byte key, then the value.
**Type 1 = 4-byte int, 3 = 4-byte float, 2 = 8-byte long**, all big-endian. Decoding stops at the
first unrecognised type byte (~116 of the records parse before one appears), which is why only
calibrated keys are trusted.

The mapping was solved on 2026-09-06 by matching decoded values against a databank export of
`XAUUSD/SPP OOS` — 14 metrics reproduced **exactly on all 165 strategies**:

| key | metric | key | metric |
|---|---|---|---|
| `(f,1)` | Sharpe | `(f,25)` | Ret/DD |
| `(f,5)` | ZScore | `(f,27)` | Profit factor |
| `(f,8)` | Calmar / CAGR-MaxDD | `(f,29)` | SQN |
| `(f,9)` | Drawdown | `(f,34)` | R Expectancy |
| `(f,10)` | Net profit | `(f,43)` | Winning % |
| `(i,10)` | # of trades | `(f,56)` | RSquared |
| `(f,11)` | Stability | `(f,21)` | Max DD % |

- **The key mapping does not depend on the sample type** — the same key is the same metric in the
  IS, OOS and full blocks. Sortino, PSR, DoF Ratio, TRL Ratio, Ulcer and Param Count were not
  resolved: `SPP OOS` leaves them constant or unexported, so nothing pinned them.
- 🔬 **`SPP OOS` strategies carry an all-zero sample-20 block.** Their OOS columns exported as 0 and
  every key matched them, which is what makes them useless as calibration for the OOS side and
  matches the `04-export.md` note that their trades are all `IST`.
- The values are the same frozen numbers described above, so this reads what SQX stored, not a
  recomputation. For anything needing a **recomputation over a different window**, use
  `dailyEquity.bin` (`01-file-formats.md`) instead.
- Tool: `core/sqxstats.py` (`stats()` and `equity()`). Together they made
  `tasks/reports/decay.py` possible with the master's GUI up and the worker never started.
