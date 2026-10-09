---
q: Why does a batch study's fact not reach the pilot, or its YAML `null:` key come back as None?
kw: facts.gather estudios json batch study path file_rows yaml null key parses None quoted "null" filters.screen NetProfit oos2 duplicates composition
tag: 🔬  date: 2026-10-07  see: wfc-top-persistence-sign-flip-null
---
# Three traps of the batch studies' plumbing
1. `facts.gather` reads a batch study only from `<batch>/estudios/<study>.json` (newest per mother):
   any other name (the old `wfc_<comp>.json`) is invisible to the judge.
2. A YAML key `null:` parses as `None`: quote it, `"null":` (`wfc/config.yaml`).
3. `filters.screen` signs duplicates with `NetProfit` of all three legs in every composition, so even
   `c3` reads oos2 there; it runs after `gate.seal`, and the rehearsal fills that column with zeros.

## Evidence
`pipeline/autopilot/facts.py` (`gather`, `file_rows`); `engines/variants/filters.py:70`;
`studies/optimisation/wfc/calibrate/rehearsal.py:28-33`; `tests/test_autopilot_facts_batch.py`.
