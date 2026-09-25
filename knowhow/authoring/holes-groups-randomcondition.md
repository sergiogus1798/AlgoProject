---
q: does a RandomCondition need a group; empty #Group# samples all conditions; AND RandomCondition plus fixed block; block not in any group unreachable from hole; Keltner condition not in group; empty group RandConditions silent; vocabulary.py diff installs
tag: 🔬  date: 2026-09-22  see: authoring/builder-block-switches, authoring/block-vocabulary
---
# A hole references a group, never a block; an ungrouped block works only as a fixed block
`RandomCondition` with empty `#Group#` builds and samples all 500 Conditions; a group only narrows it.
`AND(RandomCondition, <concrete block>)` is build-confirmed — one fixed idea + one random needs no new skeleton.
A block no group pools cannot fill a hole. An empty group builds and samples nothing, silently.
Diff installs (`sqx/inspect/vocabulary.py --diff`) before building on one what was authored on another.

## Evidence
- Stock `highest_breakout_template_daily_filter.sqx` (source of the `session_market` shape):
```xml
<Item key="AND">
  <Block><Item key="RandomCondition" ...>
           <Param key="#Group#" name="Random group" randomGroupType="Conditions" />   <!-- empty -->
  <Block><Item key="BarDayOfWeekIsNot" ...>                                           <!-- concrete -->
```
- Keltner: native category `Conditions/Keltner Channel`, 16 conditions (`KCBarClosesAboveUpper` = bar
  closes above upper band), none in any group. Reachable only as a value via Value group
  `BollingerBands_Lower` (11 band indicators incl. `KeltnerChannel`, `MTKeltnerChannel`). So Keltner
  price level yes, Keltner entry-condition hole no, until a group is authored.
- ⚠️ `RandConditions` has 0 items but `sqx-strategy-template`'s `catalog.json` lists it as clean;
  `vocabulary.py` prints such groups on an `EMPTY, unusable` line.
- 🔬 Today master, `SQX_w1`, `SQX_w2` identical: 849 native + 171 own blocks, 20 groups (`--diff` no gap).
