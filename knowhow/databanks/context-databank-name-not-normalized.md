---
q: Cross Market necesita el export del retest cross-market entrando desde el propio databank Cross Market; ui.daemon.runs.context databank with spaces finds no export; multimarket False when it should be True; databank name Retest Markets - Family
tag: 🔬  date: 2026-09-29  see: databanks/, eng/feed-in-config-yaml
---
# `ui.daemon.runs.context` globbed the databank name raw; a space-spelled one found nothing
Every export lands on disk under `databank.replace(" ", "_")` (`core.paths.report_dir` et al.).
`ui/daemon/runs.py`'s `context()` — the function almost every study's run button goes through
— globbed `DATA / "raw" / project / databank` with the databank exactly as the window hands it
over: SQX's own spelling, spaces and all ("Retest Markets - Family"). Not underscore-safe, it
found no `trades.parquet`, so `export` came back None and `multimarket` False however much the
export held. `crossmarket()` then answered "necesita el export del retest cross-market" about
the Cross Market tab's *own* databank (feedback 2026-09-29 §1.4).

## Evidence
```python
>>> runs.context(P, "Retest Markets - Family", "", "USDJPY")["multimarket"]   # before
False
>>> runs.context(P, "Retest_Markets_-_Family", "", "USDJPY")["multimarket"]   # underscored, worked
True
```
Fix: `context()` normalizes once (`folder = databank.replace(" ", "_")`) before both globs;
`atr_calculator()` in the same file built a path from `c["databank"]` directly and got the
same fix. The `--databank` argument passed on to the study script itself is left as SQX
spells it — `core.paths` normalizes it again downstream, so scripts were never the problem.
Every study `context()` serves (crossTF, mcRetest, spp, decay, wfm, monkey, exposure,
atrCalculator, monteCarlo, profitShape, entryQuality) carried the same risk on any databank
whose SQX name held a space, not only Cross Market.
