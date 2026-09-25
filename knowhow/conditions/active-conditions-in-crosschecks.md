---
q: where active acceptance conditions live in a task; silence acceptance of a study; crosschecks.py silenced count zero; WalkForwardMatrix element vs WalkForwardOptimization; matrix cells Param1 Param2
tag: 🔬  date: 2026-09-23  see: conditions/wf-type, conditions/wfm-acceptance, conditions/mc-retest-task
---
# Every active condition of a donor task sits inside `<CrossChecks>`
- To silence a study's acceptance, turn off every `<Condition use="true">` across the whole task, not only in the enabled cross-check.
  `sqx/projects/crosschecks.py` does it and reports the count.
- `0` silenced on a freshly cloned project is a tell: not cloned from the donor, or already edited (or the doctrine regex already did it → `conditions/mc-retest-task`).
- A matrix is the `<WalkForwardMatrix>` ELEMENT, not its `type` attribute.

## Evidence
- Frozen donor, `ElementTree` per task: 13 active in WFM task, 19 in each SPP task, 20 in an MC Retest task — all inside `<CrossChecks>`; task top level none.
- Some belong to cross-checks the task doesn't run (a `WalkForwardMatrix` condition inside `use="false"` `WalkForwardOptimization`); unknown whether SQX evaluates them.
- `<WalkForwardMatrix>` writes `value="undefined"` + `start/stop/step` on `Param1` and `Param2`; cells = product of ranges (5 × 6 = 30 on the owner's task).
  `<WalkForwardOptimization>` carries a single `value` each.
