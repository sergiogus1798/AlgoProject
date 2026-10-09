---
q: Why does the builder refuse a project on M15 with «falta M15 en trades_per_year»?
kw: falta M15 en trades_per_year, Sin ese valor no se escribe ningún filtro de aceptación, assets/_study.yaml timeframe build, sqx.projects.builder refuses timeframe
tag: 🔬  date: 2026-10-09  see: research/is-filters-inside-the-build
---
# A timeframe with no `trades_per_year` entry in `assets/_study.yaml` cannot be a build timeframe
`sqx.projects.builder` refuses it: no value, no acceptance filter is written. Today only H1, M30 and H4
are there, so M15 appears only as a step-11 sister. The value is the owner's.

## Evidence
- 🔬 Refusal text: «falta `M15` en `trades_per_year` … Sin ese valor no se escribe ningún filtro de aceptación» (2026-10-08/09 calibration). Check: `grep -n -A6 trades_per_year assets/_study.yaml`.
