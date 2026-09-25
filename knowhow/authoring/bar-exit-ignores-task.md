---
q: ExitAfterBars in template; exit after bars missing from built strategies; ExitTypes minValue maxValue; #ExitAfterBars.ExitAfterBars# key; randomValue default
tag: 🔬  date: 2026-09-23  see: authoring/build-doctrine-sections
---
# A template's bar exit: the task sets its RANGE, nothing tested sets its PRESENCE (unresolved)
In a template `ExitAfterBars` is a parameter of the entry order, key `#ExitAfterBars.ExitAfterBars#`
(block-prefixed); grepping `#ExitAfterBars#` finds nothing and falsely suggests no bar exit.
The Build task's `ExitTypes` `<Block minValue maxValue>` governs the range. No task lever tested forces it to appear.
🤔 Next to try: the template param's `randomValue=` (now `"default"`) — likely a template-authoring lever.

## Evidence
- Template: `<Param key="#ExitAfterBars.ExitAfterBars#" … defaultValue="0" generate="random" randomValue="default">`.
- `minValue=4 maxValue=48` → 15, 18, 20, 34, 42, 45, 46 bars, above the template's `builderMaxValue="20"`.
- `use="true" probability="100"`, `minExitTypes=1`, `maxExitTypes=2`, `minExitConditions=0` → 13/20 without a bar exit.
- Raising template `defaultValue`/`minValue` above 0 → 15/20 without; reverted.
