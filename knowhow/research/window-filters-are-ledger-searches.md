---
q: window filter ledger row, manual deletion ledger, filter step segment, discards.jsonl, filters refused no template, ledger.report "de 150 entraron a 183" summary wrong order, # of trades (OOS) missing from cosecha, Trades OOS column
tag: 🔬  date: 2026-09-28  see: authoring/template-family-is-the-folder
---
# A filter in the window is a search: one ledger row each, logged before anything is hidden
`/api/filters/apply` and `/discard` write ONE `record.log` row (launched_by `ventana`; step = the
Python step reading the stage that writes the databank, `Results` → 8; segment `build` if only IS
was read, else `oos1`), then append to `AlgoData/filters/<P>/<D>/discards.jsonl`. No template →
refused. No value for a metric → stays visible, counted «sin valor». The cosecha has no `# of trades (OOS)` (use `spread.operaciones [OOS]`); `ledger.report`'s
summary line is first-row n_in → last-row n_out by time («de 150 entraron a 183»): read the table.

## Evidence
- 2026-09-28, `Test_USDJPY_donchianUpperCrossUp_M30`/`Results`: «Net profit (OOS) > 0 AND
  spread.operaciones [OOS] ≥ 30» → 200 → 183, row in `USDJPY_M30_donchianUpperCrossUp.jsonl`
  (step 8, oos1); «Trades (OOS)» answered «no es una columna de este databank».
- `table.table(...)["columns"]`: 21 IS metrics, 13 OOS metrics, no trade count on OOS.
- mcRetest «Parámetros fuera 90 AND PF(IS) entre 1.1 y 3» → 200 → 198, blank 191 (visible).
- Daemon restarted: `/api/filters/state` still gave hidden 17, remaining 183.
