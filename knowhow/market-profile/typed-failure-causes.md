---
q: Where does a closed run's failure cause come from in the autopilot?
kw: why did a run die, cause of a closed run, typed failure, closed vocabulary, verdict.csv reason strings, memory cause, rules out, try next, infrastructure
tag: 📓  date: 2026-10-02  see: hypothesis-sheet-vs-build
---
# A closed run's cause comes from the FACT in the judge's reason, and today no real run has one
The autopilot's only per-strategy reason is `<state>: <fact>=<value>` parts joined by "; "
(`pipeline/autopilot/criteria.py`), plus two fixed strings that are not failures («fuera del sorteo
de desarrollo», «hermana escalada: solo sigue la madre»). `studies/research/memory/causes.py` maps
the fact of each `fail:` part to one cause of `studies/research/memory/config.yaml` › `causes` (data, provisional
until the owner approves it); the run takes the cause that failed most strategies at the step that
emptied it. A reason names a fact, never which rule: a two-sided rule (the trades-per-year band)
needs the mapping's `split`. `failed@` is `infrastructure` and never evidence.

## Evidence
Inventory 2026-10-02 over `AlgoData/autopilot/`: 4 `verdict.csv` (all step 8, 1,059 rows), every row
`outcome=pass`, reason "" (20) or «fuera del sorteo de desarrollo» (1,039) — development mode kept 5
at random, so no rule has ever written a `fail:` in a real run. 16 `fallo.md`: 5 «SQX rechazó
action=start», 5 «cancelado desde la ventana», 2 «el disco no llegó a igualar la memoria», 1 worker
holding the project, 3 Python errors (`'on'`, `KeyError: 'block'`, a gate that left nobody). All
technical. Rules exist only at step 8 (12 facts, all `gate.scorecard.*`); 10, 12, 14 and 16 have none,
so their causes come from the stage default until rules are written.
Test: `python3 tests/test_research_memory.py` (`test_causes`).
