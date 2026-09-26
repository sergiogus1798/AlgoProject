---
q: exposure.report KeyError strategy identity verdict empty table; Sample type OOS1 required; edgeCost report --strategy IndexError out of bounds; stopgrid variant names S00Vxxx not original strategy name
tag: 🔬  date: 2026-09-26  see: databanks/curate-verdict-identity-per-databank
---
# Two Python readers of `sqx.export.export_retest` output need a SPECIFIC databank/name, not just any export
`studies.closing.exposure.report` and `studies.readings.edgeCost.report --strategy` both look like
generic "point at an export" tools, and both fail confusingly when pointed at the wrong one.

## `exposure.report` needs an OOS-sample-type export, not the build one
`load.py` hard-filters `frame[frame["Sample type"] == cfg["study"]["sample"]]`, default `"OOS1"`.
Pointing `--databank Results` (the build/IS databank) at it gives an export whose `Sample type`
column is `"IST"` everywhere, so the filtered frame is empty, `inputs["strategies"]` is `[]`, and the
crash surfaces three calls deep as `KeyError: "None of [Index(['strategy', 'identity', 'verdict'])]
are in the [columns]"` — nothing in the message points at "wrong databank". Fix: export and pass the
**OOS** databank (`sqx.export.export_retest --databank OOS`), matching `segment: oos1` in
`studies/closing/exposure/config.yaml`.

## `edgeCost.report --strategy <name>` needs the export's OWN names, not the mother's
Run against a `stopgrid`/`variants` batch export (e.g. `WFC_Build` after `sqx.variants.stopgrid` +
`sqx.variants.execute`), the strategies are renamed to the batch's variant IDs (`S00V000`,
`S00V001`, ... — stopgrid's own scheme; `sqx.variants.make`'s general fabricator uses a different
one). Passing the ORIGINAL mother name (`--strategy "Strategy 1.29.55"`) crashes with
`IndexError: index 0 is out of bounds for axis 0 with size 0` inside `names[names ==
a.strategy].index[0]` — the name simply isn't in that export. Fix: omit `--strategy` to run the
whole population (it does, produces one report per name), or look up the batch's own name from its
`manifest.parquet`/`plan.csv` first.

## Evidence
- 2026-09-26, `USDJPY_workflow_profiling_v1`: `exposure.report --databank Results` → the `KeyError`
  above in 0.51 s; re-run with `--databank OOS` (same project, freshly exported) → clean, 3/3
  `worth_it`, 0.59 s.
- Same day, ATR pass2 batch (22 files: 20-point grid + probe + reference around 4 percentiles):
  `edgeCost.report --databank WFC_Build --strategy "Strategy 1.29.55"` → `IndexError` in 0.44 s;
  `pd.read_parquet(trades.parquet)['strategy'].unique()` showed `['S00V000', ..., 'S00V021']`, no
  `Strategy 1.29.55` anywhere; re-run without `--strategy` → clean, 22 strategies read, spread
  reconciliation corr 1.000000 on 29,850 rows.
- 🤔 Neither failure mode is caught before the traceback — a bit of pre-flight validation (does
  `Sample type` contain the requested value at all? does `--strategy` exist in the export's own
  `strategy` column?) would turn both into a one-line, actionable error instead of a stack trace
  pointing at pandas internals.
