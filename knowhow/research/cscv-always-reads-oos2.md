---
q: can I run the CSCV on a real variant batch to test a change, golden, regression? split_mode oos1_oos2 oos2_only, spends oos2, old batch KeyError NetProfit (build+oos1)
tag: 📓  date: 2026-09-26  see: eng/thresholds-live-in-the-ledger
---
# Every CSCV run on a real batch reads oos2 — never use one as a regression test
Both `engines/variants/panel.MODES` (`oos1_oos2`, `oos2_only`) put oos2 on the out-of-sample side, and the
PBO cuts the whole equity history. `_policy.yaml` says every look spends oos2. To prove a change to the
CSCV keeps its output, compare the config dict (`inputs.config.load`) and use `tests/test_cscv.py`'s
synthetic panels, not a real batch.

## Evidence
- `engines/variants/panel.py:15`, `engines/variants/config.yaml` `split_mode: oos2_only`.
- `pipeline/XAUUSD/Strategy_17-9-39` predates the per-segment columns: its metrics hold
  `Net profit (IS)/(OOS)`, and `cscv.report` fails with `KeyError: ['NetProfit (build+oos1)', 'NetProfit (oos2)']`.
- The only current-format real batches found (`profiling/variantes-2026-09-25/real/*`) carry oos2 too.
