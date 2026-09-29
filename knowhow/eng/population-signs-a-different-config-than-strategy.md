---
q: config_hash mismatch crossmarket stale window always stale population result identity resolved but stale, knobs.py current_hash differs from stored, nulls.draws vs batch_draws, LOADERS_POPULATION
tag: 🔬  date: 2026-09-29  see: eng/thresholds-live-in-the-ledger
---
# A study whose population run substitutes a knob before fingerprinting reads stale forever unless the window's loader repeats the substitution
`crossmarket.many.run` never draws `nulls.draws` — the population's null is always
`nulls.batch_draws`, and it signs the config it actually used, `nulls.draws` overwritten
(`inputs/config.py::batch`). `one.run` (one strategy) signs the raw config. `knobs.py`'s `LOADERS`
only had the raw loader, so a crossmarket **population** result's `current_hash` never matched —
every one read stale even freshly written (OPEN #52). Fixed: `LOADERS_POPULATION` holds a second
loader for a study whose population signs differently; `knobs.signed(key, overrides,
population=bool)` picks it, `runs.result`/`.history` pass `population=not strategy`.

## Evidence
- 🔬 stored `crossmarket.json` of `Test_USDJPY_donchianUpperCrossUp_M30/Retest_Markets_-_Family/
  2026-09-28`: `config_hash 577dd78006050324`. `studies.transfer.crossmarket.inputs.config.load([])`
  fingerprints to `eb58c827c7631084` (raw). `batch(load([]))` (`nulls.draws` -> `nulls.batch_draws`,
  10000 replacing 25000) fingerprints to `577dd78006050324` — the match.
- After the fix: `ui.daemon.results.runs.result(..., "crossmarket", "", "", "2026-09-28")["meta"]`
  gives `config_hash == current_hash`, `stale: False`, on both surviving contract-format exports
  (`Test_USDJPY_donchianUpperCrossUp_M30` 2026-09-27/28). The two 2026-09-09/14 `XAUUSD` folders
  still read `config_hash: None` — pre-contract JSON, a different and older gap (`store._read`).
