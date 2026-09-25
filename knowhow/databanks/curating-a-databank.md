---
q: remove strategies from a databank, curate databank apply verdict, strategies= selector not working, action=move moves whole databank, delete rejected strategies, create destination databank, rejected record csv
tag: 🔬  date: 2026-09-23  see: databanks/databank-verbs, databanks/no-spaces-in-names, sqx-format/strategy-identity
---
# Curate by moving/deleting .sqx files with the install stopped; the CLI `strategies=` selector never works
SQX syncs a databank from files on next access, so the curated directory becomes memory.
`sqx/curate/apply_verdict.py` does it: writes `before-<stamp>.csv` and `rejected-<stamp>.csv` under
`reports/<P>/<bank>/<day>/curate/`, then **unlinks** rejects (no `Rejected` databank, no copy). Verdict
carries `identity`; a file swapped under a judged name is caught in the dry run. ⚠️ `action=move` with a
selector that does not arrive moves the **whole** databank, no error.

## Evidence
- HTTP API cuts the name at the first space (every name is `Strategy 11.3.25`): `%20`, `+`, `%2520`,
  `"quotes"` tried, count never moved; `action=delete` answered `Reports removed.`
- One-shot `sqcli -databank …` never loads records: `action=save` with no selector wrote **0 of 30** files,
  answering `Reports saved.` A running worker does load (`list` → `Loaded 30 strategies`).
- `move` naming two strategies moved all thirty.
- File route: `mv "<install>/user/projects/<P>/databanks/Results/Strategy 11.3.36.sqx" …` while stopped;
  start; `-databank action=list` → `Loaded 27 strategies to databank Results`. 30 → 28 → 27 → 24 over four
  rounds (custodian).
- A destination databank can be made by `-databank action=create` or by `mkdir`; a restart picks both up
  (not: "must be made in the GUI").
- Deletion (owner's decision; conductor `Retester/Results` 66 → 34 → 33): ~5 MB per `.sqx` (32 → 158 MB);
  keeping 8k of 10k rejects = 40 GB per cut, and a `Rejected` databank also costs RAM (SQX loads every
  databank of a project on start). `before` = name, identity, bytes, verdict, reason of all on disk;
  `rejected` = dropped rows of the metrics export; ~56 KB per cut. Export had 5 `(1)` collisions in 66
  (`Strategy 11.10.85(1)` replaced by another strategy).
- `synctofiles` exists (memory → disk; opposite of what curation needs). Not: "no verb forces a write".
