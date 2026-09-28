---
q: can I run the CSCV or the WFC on a real variant batch to test a change, golden, regression? split_mode oos1_oos2 oos2_only, composition, spends oos2, ledger row, old batch KeyError NetProfit (build+oos1)
tag: 📓  date: 2026-09-27  see: eng/thresholds-live-in-the-ledger
---
# Every CSCV run on a real batch reads oos2, and now writes it in the ledger — never use one as a regression test
The CSCV's partitions cut the whole joined curve (build+oos1+oos2) whatever the composition, and
since 2026-09-27 each run appends three permanent ledger rows (step 18) — the ledger is append-only.
A WFC composition with `oos2` does the same on step 17. `_policy.yaml` says every look spends oos2.
To prove a change keeps the output, compare the config dict (`inputs.config.load`) and use
`tests/test_cscv.py` / `tests/test_wfc.py`, not a real batch. A WFC `--inside build --outside oos1`
reads no oos2 and is the only real-batch run that spends nothing reserved.

## Evidence
- `engines/variants/panel.py` `COMPOSITIONS`, `SHORTCUTS`; `studies/optimisation/cscv/report.py` `READS`.
- `pipeline/XAUUSD/Strategy_17-9-39` predates the per-segment columns and `segments.parquet`: its
  metrics hold `Net profit (IS)/(OOS)`, so both reports fail on it (`KeyError`, or no segments file).
- The only current-format real batch on disk on 2026-09-27 is
  `strategyPermutations/Test_USDJPY_donchianUpperCrossUp_M30/Strategy_9.27.83`.
