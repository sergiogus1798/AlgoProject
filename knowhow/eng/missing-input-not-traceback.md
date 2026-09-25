---
q: analysis fails with traceback instead of saying what is missing, empty report exit 0, studies.readings.monkey.report --sample OOS1 zero strategies, is_oos StopIteration, exposure.report IndexError trades.parquet, sorted(glob)[-1] next(iter)
tag: 🔬  date: 2026-09-24  see: eng/pipeline-run-guards
---
# Say what input is missing; never let an empty selection become a traceback or a silent zero
Pattern to fix: `sorted(glob(...))[-1]` or `next(iter(...))` over something that can be empty. One line naming the missing
file/partition saves half an hour — and stops an empty report (exit 0) being read as an answer.

## Evidence
Five untested analyses run by hand; four failed, none from maths. By danger:
1. Silent zero: `studies.readings.monkey.report` defaults `--sample OOS1`; a crossmarket export has only `Sample type = IST` → 0 rows, "0 estrategias", exit 0.
2. Wrong-shaped input: `studies.screening.isOos.report` on a databank without OOS partition → `StopIteration` in `summary.render`; right databank: 17 strategies in 0.57 s.
3. Undeclared prerequisite: `exposure.report` needs the databank's `trades.parquet` → `IndexError: list index out of range` in `sorted(...)[-1]`;
   `studies.screening.monkeyExcess.report` likewise with `studies.readings.monkey.report` output.
4. Empty population: a strategy with no trades in any foreign market killed the crossmarket batch with `KeyError: 'bar_cap'` (fixed).
