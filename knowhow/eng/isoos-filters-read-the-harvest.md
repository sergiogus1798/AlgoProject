---
q: Panel IS/OOS only Param Count IS metric; Filtros candidatos no IS metrics; metrics export of OOS databank IS columns zero; population IS OOS from harvest; metrics.source; oos_databank manifest
tag: 🔬  date: 2026-09-30  see: eng/decay-needs-build-and-retest, databanks/
---
# A workflow retest's metrics export has no IS: the IS/OOS population studies read the harvest
`OOS` (the retest) fills only its OOS block; its `metrics.csv` IS columns are constant, so
`metrics.measured` kept one IS metric (`Param Count`) and «Panel IS/OOS» / «Filtros candidatos» had
nothing to correlate. `studies.screening.analysis.metrics.source` reads the newest harvest whose
manifest names this databank as `oos_databank` (IS from the build, OOS from the retest, joined by
identity) and falls back to the metrics export only when no harvest pairs it.

## Evidence
- 🔬 2026-09-30, `Test_USDJPY_donchianUpperCrossUp_H1/OOS`: before, 1 IS metric over 296 rows;
  after, 21 IS and 13 OOS metrics over the 60 harvested pairs. ⚠️ The harvest is rewritten after a
  cut (post-stop export), so it then holds only the survivors: step 8's 300 are gone from it.
