---
q: How does the validated pool register store verdicts, and which verdict per identity wins?
kw: validated pool register step 26; AlgoData/pool/pool.sqlite; which strategies are validated for FTMO Hantec; mt5.verify.pool read record rebuild; thresholds a past Verificar run was judged under; step 26 from the autopilot; refused firm no row
tag: 🔬  date: 2026-10-02  see: mt5-verify-clock-zones, thresholds-live-in-the-ledger
---
# The validated pool is one append-only SQLite table; the FIRST verdict per check wins
- Only through `mt5.verify.pool`: `record(rows)` appends to `AlgoData/pool/pool.sqlite`; `read(firm)` = the
  FIRST verdict per (identity, window, model), by `verified_on`, being `pass`; `history(firm)` = every row;
  `validated()` = identity -> firms (the archive list's MT5 column).
- A firm the check REFUSED, or a crashed check, is not a verdict: no row, an earlier `pass` stands.
- A past check's thresholds are only in its ledger row (`<ASSET>_<TF>_mt5verify.jsonl`: `note` ends
  with the run, `criterion` names the firm) — `thresholds_hash` comes from there; `result.json`
  has only `config_hash`, of the whole config.

## Evidence
- 🔬 2026-10-02, `pool.rebuild()` over the 21 folders of `AlgoData/mt5/verify/`: 13 finished
  checks → 24 rows (13 FTMO, 11 Hantec; gold's two checks refused Hantec), 8 crashed → none.
  `read("ftmo")` = Strategy 16.9.76 and 10.9.72 (USDJPY H1), `read("hantec")` empty.
- 🔬 same rows: `thresholds_hash` 5132c9efee9f2550 on all 24, while `config_hash` changes
  f1fbef9cb8eb93d1 → a3597d820eae2ca4 at 14:09 on 2026-09-30 (config.yaml edited, thresholds not).
- `tests/test_mt5_pool.py`, `tests/test_mt5_autopilot.py`.
- 🤔 `mt5.verify.autopilot.check` reuses `mt5bridge.runs.check`, which calls
  `advance.busy("conductor", "")` with no `own_log`: an autopilot that itself ran SQX on the
  conductor would be refused until that log is 15 min old (`QUIET_MIN`). Read in the code, not
  run; a real autopilot run on a conductor project confirms it.
- 🔬 2026-10-14: owner chose SQLite (table `verdicts`, all text); the old per-firm CSVs moved to `pool/csv-retirados/`, 22 rows migrated.
