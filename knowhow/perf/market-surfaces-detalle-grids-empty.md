---
q: Why is marketSurfaces_detalle.json 100+ MB and 36 s to write, and does anything read it?
kw: marketSurfaces_detalle.json, grids.tab, continuous parameter grid 1000x1000, 159 MB, step 18.5 slow, pivot_table
tag: 🔬  date: 2026-10-13  see: perf/two-study-processes-oversubscribe-blas
---
# `marketSurfaces_detalle.json` was ~1000x1000 grids 99 % empty with a continuous parameter, and nothing read it: no longer written
A continuous parameter (932-985 distinct values over 1,004 variants) makes a ~1000x1000 grid per pair and market (the grid writer, deleted 2026-10-13 by the owner's decision; `core/study/blocks.py:40`). DAX 14.16.487: 432 grids, 26.1 M cells, 0.9 % filled, 159 MB, 36 s of 50.7 s per mother; NIKKEI 20.11.454 103 MB; USATEC 1.5 MB. A grep of `ui`, `core`, `studies`, `pipeline` finds only the writer. Before the removal, the idea was: stop writing it, or bin axes above ~12 levels with `pd.qcut` before `pivot_table`. Changes only that file.

## Evidence
- 🔬 DAX timing: `grids.tab` 18.8 s + `envelope`/`plain` 15.1 s + `json.dumps` 1.9 s; file mtimes 22:50:30 (`marketSurfaces.json`) and 22:51:05 (`_detalle`).
- Source: `findings-P6.md` finding 2.
