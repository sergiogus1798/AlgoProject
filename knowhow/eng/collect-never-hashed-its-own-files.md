---
q: pipeline.cleanup KeyError sha256, el export ya no coincide con su hash metrics.parquet, collected.json files no bytes no sha256, removable bare name not DATA-relative, sqx.variants.collect fingerprint, which stage rewrites metrics.parquet after its hash
tag: 🔬  date: 2026-09-29  see: research/cscv-always-reads-oos2
---
# Nothing rewrote metrics.parquet after collect hashed it -- collect never hashed it
Issue 33 read as "a later stage rewrites the file collect already hashed". It does not: since
`sqx.variants.collect` was written, its `files` entries carried only `{"path": "metrics.parquet"}`
-- no `bytes`, no `sha256` -- while `pipeline/cleanup.py` has always read `entry["sha256"]` and
resolved `DATA / entry["path"]`. Two gaps, not a race: no hash was ever recorded, and `path`/
`removable` were never DATA-relative (`str((a.work / "sqx").name)` keeps only the last component).
Fixed 2026-09-29: `collect.fingerprint(path)` hashes both files the moment `main()` writes them and
records `path.relative_to(DATA)`.

## Evidence
- `git log -p -- sqx/variants/collect.py` and `-- pipeline/cleanup.py`: `cleanup.py`'s `sha256`
  read and `collect.py`'s hash-less `files` list are both original, from their first commits --
  the mismatch was never closed, not introduced by a later change.
- 🔬 verified on `pipeline/XAUUSD/Strategy_17-9-39/state.json` (2026-09-29): `stages.collected.files
  == [{"path": "metrics.parquet"}]`, no `bytes`, no `sha256`; calling
  `pipeline.cleanup.unchanged()` on that entry raises `KeyError: 'sha256'` directly, before ever
  reaching the "no coincide" message the issue quotes -- the ledger on disk today is even older
  than the one behind the issue's own report.
- Fix verified on a copy of `metrics.parquet` under `scratch/` (never on the real batch):
  `fingerprint()` gives a `DATA`-relative path plus a hash `pipeline.cleanup.unchanged()` accepts
  as unchanged, and rejects once the recorded `sha256` is tampered with.
