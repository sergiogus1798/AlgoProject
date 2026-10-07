---
q: Which keys in strategy_Portfolio.xml mark a fixed pips distance (stop, target, trailing, break-even, filter)?
kw: fixed pips, FixedValue, SLPT.FixedValue, RangeLevel.FixedValue, Range.FixedValue, PriceRange, FixedPips, SL2BEAddPips, TrailingActivation, fixed_distances
tag: 🔬  date: 2026-10-06  see: sqx-format/five-member-sqx, sqx-format/writing-a-variant
---
# A fixed distance is a `<Formula key="SQ.Formulas.<ctl>.FixedValue">` in an exit-method Param, or a `FixedPips` block
`sqx.inspect.strategymeta.fixed_distance.fixed_distances(sqx | xml | root)` lists them. Unit is **pips**
(SQX has no points unit; its config labels these «Fixed value (in pips)»). ATRBasedValue, PctValue,
PriceLevel and None are not fixed. Exit-method params sit on the `Enter…` Item; the formula class follows the
param's `controlType` (table under Evidence; 🔬 tested on real files, 🤔 config only).

Not covered: WAE `DeadZonePip`, `#StopLossInPips#`, `SLPT.ValueFromFormula` (details under Evidence).

## Evidence
| param key | controlType | fixed formula | status |
|---|---|---|---|
| `#StopLoss.StopLoss#`, `#ProfitTarget.ProfitTarget#` | SLPT | `SLPT.FixedValue` | 🔬 |
| `#TrailingStop.TrailingStop#`, `#MoveSL2BE.MoveSL2BE#` | RangeLevel | `RangeLevel.FixedValue` | 🔬 |
| `#TrailingStop.TrailingActivation#`, `#MoveSL2BE.SL2BEAddPips#` | Range | `Range.FixedValue` | 🔬 |
| any of the above | RangeLevel / Range | `…PriceRange` («Range in pips», `ignoreInBuilder`) | 🤔 config only, never seen |
| condition operand | — | Item `FixedPips`, pips in `#Value#` | 🔬 |
| condition operand | — | `OpenPLInPips`/`ClosedPLInPips`/`SpreadInPips` vs a `Number` | 🤔 config only |

- 6,000 random `.sqx` of the three installs + AlgoData: 28 flagged — break_even 11, trailing_stop 11,
  trailing_activation 5, break_even_add 4, FixedPips 3, profit_target 1, stop_loss 1. Seen in:
  `snapshots/weekly-data-update-2026-10-03/projects/GBPJPY_H1/databanks/RetestPairs/Strategy 5.17.290.sqx`
  (trailing `RangeLevel.FixedValue` 93), `…/MC Jitter - IS/Strategy 5.21.162.sqx` (trailing 53 + activation
  `Range.FixedValue` 60), `…/MC Random - IS/Strategy 9.2.223.sqx` (BE 213 + add 24),
  `…/Retester/databanks/XAU Incomplete/Strategy 1.3.52.sqx` (`FixedPips` 160, via `variable="true"` →
  `FixedPipsValue1`). SL/PT fixed: only `AlgoData/templates/library/doubleROCLong_withExit/template.sqx`
  (SL 50, PT 50, trailing 50) — authored, not a builder output, but SQX's own format.
- Not covered: WAE's `DeadZonePip` (indicator-internal pips param; 350 of 6,000 sampled strategies hold it,
  key renamed `#Double2#` inside the custom-block wrapper), `#StopLossInPips#` (money-management fallback),
  `SLPT.ValueFromFormula`. `value` resolves `variable="true"` refs through `<variables>`.
- Builder output in these samples draws SL/PT as `SLPT.ATRBasedValue` (98 hits) and no fixed SL/PT.
- Definitions: `SQX_w1/internal/web/SQWIZARD/branding/global/config.xml` lines 330-430 (formula classes),
  10901 (`FixedPips`).
