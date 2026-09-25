---
q: startOnlyTask does nothing Total tested 0; action=start runs whole chain; second start does nothing needs stop; retestSelected missing retests nothing; DeleteFailedStrategies in harness
tag: 🔬  date: 2026-09-22  see: sqx-drive/project-verb, sqx-drive/spp-task-type
---
# Run a task with `stop` then `start` on a single-task project; never `startOnlyTask`
`-project action=startOnlyTask` logs success and tests nothing. `action=start` works but runs the
WHOLE chain (with a Build + `GoToTask` it generates forever) — use single-task projects.
A second `start` without `stop` first silently does nothing. Always `stop` before `start`.
Retest task needs `<Databanks retestSelected="false">` + `<SelectedStrategies />` or it retests nothing.
Set `<DeleteFailedStrategies>false` and all conditions `use="false"` for parameter studies.

## Evidence
- `startOnlyTask name=X task=1`: logs `Starting project 'X' task 1 only`, `Project started`; status
  `Total tested 0 · Running time so far 0 ms` forever, no error, no `Project finished`.
  `action=start` same project/instant: `Total tested 11 · Time per strategy 67 ms`.
- Restart: 0 before the `stop`, `tested=2` ten seconds after. `status` shows zeros for finished,
  never-started and refusing-to-restart alike — it cannot distinguish them.
- Stock `Retester`/hand-built tasks have `<Databanks>` with no attribute → SQX retests the empty
  selection, reports 0. Build a task by copying one that has run. Donor also carries `Broker`, `Swap`,
  `Session`, `SequentialOptimization`, `CustomAnalysis`, `ForceRunCrossChecks`,
  `DeleteFailedStrategies`, absent from the stock harness.
- ⚠️ Donor `<DeleteFailedStrategies>true` deletes variants failing acceptance → a missing variant and
  a losing one become indistinguishable. Harness sets it `false`, all 30 conditions `use="false"`.
