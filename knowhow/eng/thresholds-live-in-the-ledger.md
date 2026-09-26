---
q: where does a study's threshold live, config.yaml or ledger/thresholds.yaml? ledger:<key> placeholder, add or change a threshold, migrate a module, --set override of a threshold, check-thresholds copia
tag: 🔬  date: 2026-09-26  see: research/cscv-always-reads-oos2
---
# A threshold's number lives in ledger/thresholds.yaml; config.yaml holds `ledger:<key>` in its place
New threshold: append a row to `ledger/thresholds.yaml` (key, value, source, set_by, set_on, why) and write
`ledger:<key>` where the number would go in the module's `config.yaml`. The module's `config()` must run
`ledger.thresholds.fill` on the parsed YAML **before** `study_config.apply(overrides)` — then `--set` is typed
against the number, not the string. Keep the placeholder **in place**; don't delete the key and inject it:
the gate prints each screen's thresholds in row order, so moving a key changes `gate.md`. A key missing
or declared twice raises on read. Changing a value is the owner's, in the register, never in config.yaml.

## Evidence
- 2026-09-26, six modules migrated (gate, snoopingScreen, profitShape, entryQuality, cloud, cscv; 14 keys).
  Goldens before/after on real data byte-identical incl. `core.study.config.fingerprint`: gate on
  `XAU_ISOOS_ejemplo` 45/120 and `USDJPY_emaCross_H1` 25/100; profitShape/entryQuality on 36 strategies of
  `raw/XAUUSD/Results/2026-09-03`; cloud on `pipeline/XAUUSD/Strategy_17-9-39`; each also with `--set`.
- `tests/test_thresholds.py` swaps every value for a sentinel; reverting one placeholder to `5.0` fails it.
- `python3 -m ledger.report --check-thresholds` column `lee_de`: `ledger` or `copia` (a copy must match).
