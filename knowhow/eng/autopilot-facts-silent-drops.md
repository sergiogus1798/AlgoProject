---
q: autopilot facts missing, gate.scorecard rule always limbo sin dato, identity empty in hechos.parquet, parquet index identity, object dtype passed column dropped, verdict.csv numbers not facts, which step 8 keys exist
tag: 🔬  date: 2026-10-01  see: thresholds-live-in-the-ledger
---
# A fact the study wrote can silently miss the judge: index, dtype and CSV
`pipeline.autopilot.facts` joins facts to the cut databank by identity. Check when adding a study:
1. A parquet with identity as its **index** (gate scorecard) read back with identity "" → its
   rules read «sin dato» = limbo. Now reset when the index is named `identity`.
2. A cascade column filled only where reached (`mono_passed`: True/False/None) is **object**
   dtype; `select_dtypes` dropped it. Now any column holding a number is read.
3. `verdict.csv` gave only `drop`; now every numeric column is `<study>.verdict_csv.<col>`.

## Evidence
Test_USDJPY_donchianUpperCrossUp_H1, `python3 -m pipeline.autopilot.facts --project … --step 8`:
before, 0 `edgeCost/feedQuality/spread` numbers and `gate.scorecard.*` with identity "" (300 rows);
after, `edgeCost.verdict_csv.edge_mean` 60, `spread.verdict_csv.*` 300, `monkey.nulls_csv.*` 300,
`gate.scorecard.mono_passed` 190, all with identity. `tests/test_autopilot_facts.py` holds each case.
