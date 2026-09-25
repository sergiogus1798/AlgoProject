---
q: sqx-strategy-project skill donor task chain; keep_tasks strip; StrategyType simple ignores templateFile; template not applied OPEN issue 9; templateFile absolute path; uSymbol vs symbol
tag: 🔬  date: 2026-09-22  see: authoring/headless-authoring-chain, sqx-format/project-cfx
---
# With `<StrategyType type="simple">` the `templateFile` is ignored; only `type="template"` applies it
The `sqx-strategy-project` skill carries the donor's whole task chain; for builder-only strip it with
`python3 -m sqx.inspect.keep_tasks in.cfx out.cfx --types Build` (also drops unreferenced databanks, keeps the 5 system ones).
`templateFile` paths are absolute and resolve on the target install: copy templates into
`<install>/user/settings/StrategyTemplates/<set>/` first. SQX binds `uSymbol`, not `symbol` (heals it on load).
The owner's nine `type="simple"` projects stay as they are (owner, 2026-09-04): their populations are generic.

## Evidence
- Cloning XAUUSD's build task ×5 → 18 tasks: 5 builds + 13 donor retest/MC/SPP/WFM/Clear/GoTo, incl. a
  dangling `GoToTask` to a vanished task name.
- `sqx/inspect/template_check.py`: fixed blocks = `Rules` Items with `categoryType` `indicator`,
  `simpleRules`, `priceValue`, `priceRange`, `Custom blocks`, skipping any `randomBlock` subtree; then check built strategies.
  ⚠️ Until 2026-09-22 it lacked `Custom blocks` and signed custom-block templates as `MarketPositionIsLong`
  (every long strategy has it) → false `25/25 carry it ok`. Fixed.
- 8 projects, 33 databanks, 25 per databank, seed 0: 0 of 642 carry their template block. XAUUSD's
  `DoubleVortexLong_Template.sqx` fixes `Vortex`; none of 10,231 strategies has one. Same for
  `ROCAboveLevel` (AUDJPY, EURUSD, USDJPY), `AroonCrossesAbove` (GBPJPY_H1), `CCI` (USDCHF),
  `HurstExponent` (SP500_H1), `BBWidthRatio` (EURJPY_H1). Positive control: 2 of 53 from imported
  `Existing portfolio` databanks carry it (SP500_H1, EURJPY_H1). Unaffected by the checker fix (native blocks).
- ⚠️ Unsettleable: CADJPY_H1 `AcceleratorEMALong_Template.sqx` is only `RandomCondition`s (no fixed
  block); `XAUUSD_Breakout_H1` (`type="template"`) had no strategies on disk.
- 📓 Count: 10 `type: simple` hits; 10th is `Builder` with stock relative `SQ3StrategyTemplateExample.sq4` (absent here).
- Positive control that `type="template"` works: `authoring/headless-authoring-chain` (30/30).
- `OPEN.md` issue 9. Flipping them changes what they generate — owner's call (hard rule 3).
- `uSymbol`: engine blanks it; SQX filled `XAUUSD` for all 5 tasks on load.
