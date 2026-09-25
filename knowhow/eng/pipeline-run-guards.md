---
q: gate vs threshold, canary failure stops the run, brief_hash fingerprint design, gates.unchanged, provisional costs block pipeline?, core.assets.pending, costs_provisional
tag: 🔬  date: 2026-09-21  see: eng/resumable-jobs, eng/missing-input-not-traceback
---
# Separate "measurement invalid" gates from "not good enough" thresholds; hash the design; stamp provisional costs
- Gate (stops the run, on the recipe row): the measurement is invalid — e.g. failed canaries (SQX returned variants other than those written).
  Threshold (user's, `config.yaml`, changeable without reprocessing): the strategy isn't good enough. In `pipeline/` canaries are a gate, absent from `verdict.rules`.
- `gates.unchanged` compares the recorded `brief_hash` (C5 ledger) with the brief before every stage and refuses on change.
- Provisional cost = run and stamp `costs_provisional: true` in every ledger; missing cost (`use` null) = blocker.

## Evidence
- Brief read once → 5,000 variants; a regenerated brief (sppUltra rerun, threshold change, other export day) errors nowhere and judges one design against another's numbers. A hash nobody reads is decoration.
- `core.assets.pending()` returns only fields whose `use` is null, not PROVISIONAL ones. XAUUSD spread and commission are SQX defaults the owner hasn't replaced.
