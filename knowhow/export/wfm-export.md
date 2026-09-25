---
q: Walk-Forward Matrix WFM export cells steps; is_Fitness oos_Fitness zero; future steps past end of data; pool steps or cells; params.parquet NaN parameter drift
tag: 🔬  date: 2026-09-23  see: export/data-all-blocks, conditions/wfm-acceptance, export/fill-and-pricing, export/exits-and-m1-library
---
# WFM export: the cell is the unit; per-step fitness is zero and last steps run into the future
- ⚠️ `is_Fitness`/`oos_Fitness` per step are always 0 — fitness exists only per cell (`fitness_is`/`fitness_oos` in `cells.csv`). Read a real metric per step.
- ⚠️ Drop steps with `future=True` — their OOS stats are on non-existent history.
- Never pool steps across cells into one correlation: cells re-split the same history. Analyse per cell.
- Drop all-NaN parameter columns per strategy before step-to-step drift (`NaN != 0` is True).

## Evidence
- `raw/XAUUSD/WFM/2026-09-10/wfm/`: 2 strategies, 60 cells, 720 steps; 60 steps `future=True` (cell 6x20 of `Strategy 1.19.29`: 2025-12-31 → 2027-08-20).
- Run windows within a cell disjoint and consecutive (0 overlaps in 60 cells); optimisation windows overlap 6.5 of 8.2 years (79 %); every cell re-splits the same 10–14 years.
- `params.parquet` is wide since 2026-09-23; two strategies don't share a parameter list.
- 📓 IS optimisation doesn't predict OOS: `1.19.29` rho +0.076 (95 % over cells −0.034 to +0.193); `4.33.46` −0.505 (−0.683 to −0.339), negative in 28/30 cells, all four metrics.
  Optimiser re-decides 70–78 % of parameters every step.
- Fill convention (open at bar open, both sides) and exit repertoire → `export/fill-and-pricing`, `export/exits-and-m1-library`.
