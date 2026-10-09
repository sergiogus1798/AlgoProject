---
q: Why does the builder refuse a project on M15 with «falta M15 en trades_per_year»?
kw: crosstf.timeframes no dice en qué timeframes se reprueba una madre, KeyError 'M15' workflow.py finish, crosstfsolo.planned refuses; falta M15 en trades_per_year, Sin ese valor no se escribe ningún filtro de aceptación, assets/_study.yaml timeframe build, sqx.projects.builder refuses timeframe
tag: 🔬  date: 2026-10-09  see: research/is-filters-inside-the-build
---
# A timeframe with no `trades_per_year` entry in `assets/_study.yaml` cannot be a build timeframe
`sqx.projects.builder` refuses it: no value, no acceptance filter is written. Today M15, M30, H1 and H4
are there (M15 added by the owner on 2026-10-09). The value is the owner's. A build timeframe needs a second entry: `crosstf.timeframes.<TF>` in `assets/_build.yaml` (its sisters). Without it `sqx.projects.crosstfsolo.planned` refuses: «assets/_build.yaml: `crosstf.timeframes` no dice en qué timeframes se reprueba una madre <TF> — decídelo antes de construir.» Before 2026-10-09 it was a `KeyError: 'M15'` traceback from `sqx/projects/workflow.py::finish`, after the build.

## Evidence
- 🔬 Refusal text: «falta `M15` en `trades_per_year` … Sin ese valor no se escribe ningún filtro de aceptación» (2026-10-08/09 calibration). Check: `grep -n -A6 trades_per_year assets/_study.yaml`.
