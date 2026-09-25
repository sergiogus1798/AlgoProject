---
q: custom databank column snippet, DatabankColumn java where, compile snippet, column value frozen stored, rewrite column no effect old strategies, new column reads 0, recompute stats verb
tag: 🔬  date: 2026-09-06  see: sqx-format/sqstats-blob, columns/param-count, columns/edge-decay-retired
---
# A custom column's value is frozen into the .sqx when the result is computed
`compute()` is not called by `-databank action=export` nor by loading; the number comes from the
`SQStats` blob in `settings.xml`, keyed by class name. Rewriting a column changes nothing for existing
strategies; a column added later reads **0** on every older one, no warning. No recompute verb — rerun a
task that recomputes results, or compute the metric outside SQX from `strategy_Portfolio.xml`.

## Evidence
- Location: `…/user/extend/Snippets/SQ/Columns/Databanks/<Name>.java`, one class extending `DatabankColumn`;
  13 on this install (`ParameterCount`, `DoFRatio`, `PSR`, `TRLRatio`, …).
- Compiled at startup into `internal/tmp/compiled/SQ/Columns/Databanks/<Name>.class`. Editing the `.java`
  while running is safe. Each install needs its own copy (`SQX/user/extend`, `SQX_w1/user/extend` separate).
- Cannot compile outside SQX: `com.strategyquant.lib` (`ValuesMap`, `SettingsMap`) is in no jar under
  `internal/libs`; `javac -cp 'internal/libs/*'` fails. Only check: start an instance, look at the
  `.class` timestamp.
- Views reference by class name: `<Column class="ParameterCount" name="Param Count" …/>` in
  `user/settings/views/databanks/*.vw`; `name=` is header text only.
- `XAUUSD/SPP OOS` (165 strategies), exported thrice via the worker: original `ParameterCount` 16.80 mean,
  median 16; rewritten logic → identical per strategy; `compute()` = `return 99.0` → still identical;
  new column class → 0 for all 165. `ParameterCount` sits in the blob as an IEEE float next to `DoFRatio`, `PSR`.
- ⚠️ Two exports months apart may carry values from two snippet versions; the CSV can't tell which.
- Verbs: list, count, save, load, delete, clear, create, remove, synctofiles, syncfromfiles, copy, move, export.
