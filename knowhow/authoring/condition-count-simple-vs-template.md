---
q: How many conditions may a template's random hole add per side, versus a Simple Strategy?
kw: how many entry or exit conditions does a built strategy get; What to build minConditions maxConditions with a template; RandomCondition filled with 1 to 2 conditions; template plus random hole gives 3 conditions; simple strategy vs template; two RandomCondition holes give 4 conditions; nested AND in a hole; max 2 conditions rule; bound hole one-item group counts as fixed; exit conditions mandatory only in simple strategy
tag: 📓  date: 2026-10-02  see: authoring/simple-strategy-build-xml, authoring/holes-groups-randomcondition, authoring/one-item-group-can-drift
---
# «What to build» counts conditions PER RANDOM HOLE in a template, and per strategy only in a Simple Strategy
Owner, 2026-10-02, «fundamental»: **at most 2 entry and 2 exit conditions per strategy, never 3**. `buildrules.what_to_build` writes it on every Build (`minConditions`…`maxExitConditions` of `<Chart name="Main chart">`):
- **Simple Strategy:** `complexity.simple` of `assets/_build.yaml` as written — entry **1..2**, exit **1..2** (the exit condition is mandatory ONLY here; owner, same day).
- **Template:** per side `0..(2 − fixed)`; a side with nothing fixed keeps its floor (entry 1, exit 0 — a template's exit stays optional, 0..2). `builder` refuses two free holes on a side, and fixed + hole > 2. The same condition written twice on a side — same blocks, different periods (double ROC, double Vortex) — counts as ONE fixed (owner, 2026-10-05; `holes._count`), so those templates carry 3 entry conditions. 🔬 on the library's `doubleROC*`/`doubleVortex*`.
- ⚠️ SQX has ONE range for every hole of a side, and this project's "fixed" condition is itself a hole bound to a one-item group (`sqx/templates/build.py`), filled by that same range: such a side is written **1..1** (idea + exactly one random), never 0..1, which could leave the idea out. 🤔 untested in SQX either way.
- Count it on the project, never assume: `python3 -m sqx.projects.buildingblocks --project P --count`.

## Evidence
- 📓 Owner's explanation of the GUI's behaviour, 2026-10-02, after opening `Test_Calib_USDJPY_H1_freeL_ver`;
  his hand-set Build there: `type="simple"`, `minConditions="1" maxConditions="2" minExitConditions="1"
  maxExitConditions="2"`, `_ExitRule_` use true probability 50 (archived under `projects/retired/SQX_w2/`).
- 🔬 It matches what the calibration measured: `freeShellLong` (two free holes, 1..2) gave a nested AND —
  three or more entry conditions — in 69 % of USDJPY H1 freeL; Donchian (1 bound + 1 free, 1..2) carried a
  nested AND as second condition in 1,962 of 5,026.
- 🔬 `sqx.templates.holes.conditions` on the library, 2026-10-02: every authored template is
  `{bound 1, free 1}` on entry and nothing on exit; `timeRangeBreakout` is `{fixed 1, free 1}` → 0..1;
  `freeShellLong/Short` `{free 2}` → refused. `tests/test_condition_count.py` holds the arithmetic.
- ⚠️ Until this fix `buildrules.py` wrote `maxConditions = 2` whatever the template held: the 28
  calibration populations of 2026-10-01/02 exceed the cap, and their criteria
  (`docs/AgentPDFs/criterios-implementados-2026-10-12.md`) were calibrated on them.
