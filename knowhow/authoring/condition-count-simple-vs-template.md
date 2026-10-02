---
q: how many entry or exit conditions does a built strategy get; What to build minConditions maxConditions with a template; RandomCondition filled with 1 to 2 conditions; template plus random hole gives 3 conditions; simple strategy vs template; two RandomCondition holes give 4 conditions; nested AND in a hole; max 2 conditions rule
tag: 📓  date: 2026-10-02  see: authoring/holes-groups-randomcondition, authoring/builder-block-switches, sqx-drive/unselected-build-population
---
# «What to build» counts conditions PER RANDOM HOLE in a template, and per strategy only in a Simple Strategy
Owner, 2026-10-02, «fundamental»: **at most 2 entry and 2 exit conditions per strategy, never 3**.
- **Simple Strategy (no template):** «What to build» is per strategy — set entry and exit to **1..2**.
- **Template:** each `RandomCondition` is filled with `min..max` conditions ON TOP of the fixed ones.
  **1 fixed + 1 hole** on a side → **0..1**; **2 fixed** → **no hole**; never two holes on a side (0..4):
  a template of only random holes IS a Simple Strategy — build that, author no template.
- Same arithmetic for exits. What the builder writes must be `2 − fixed`, not `_build.yaml`'s cap of 2.

## Evidence
- 📓 Owner's explanation of the GUI's behaviour, 2026-10-02, after opening `Test_Calib_USDJPY_H1_freeL_ver`.
- 🔬 It matches what the calibration measured without understanding it: the «free shell» template
  (`freeShellLong`, two `RandomCondition` per side, «What to build» 1..2) produced a nested AND — three or
  more entry conditions — in 69 % of USDJPY H1 freeL; on the Donchian template (1 fixed + 1 hole, 1..2)
  1,962 of 5,026 strategies carried a nested AND as their second condition
  (`sqx-drive/unselected-build-population`).
- 🔬 `sqx/projects/buildrules.py` writes `maxConditions = complexity.max_entry_conditions` (2) whatever the
  template holds — the source of the excess. Open: make the builder count the template's fixed
  conditions and holes per side, write `2 − fixed`, and refuse two holes on one side (OPEN.md #93).
- ⚠️ The 28 calibration populations of 2026-10-01/02 therefore hold strategies above the cap; their
  criteria (`docs/AgentPDFs/criterios-pasos-6-y-8-2026-10-02.md`) were calibrated on them.
