---
q: five-member sqx minimal shape loads, databank de-duplication fingerprint, load same folder twice duplicates, DismissTooSimilarStrategies, fabricated variant exports parent's metrics, inherited results detector
tag: 🔬  date: 2026-09-22  see: sqx-format/writing-a-variant, sqx-format/retest-rewrites-sqstats, databanks/databank-verbs, databanks/autosync-nothing-on-disk
---
# SQX loads and retests a five-member .sqx — but it still carries the parent's results until retested
Members `META-INF/MANIFEST.MF`, `settings.xml`, `strategy_Portfolio.xml`, `lastSettings.xml`,
`version.txt`; the 70 MB-per-5,000 shape to build. ⚠️ `settings.xml` keeps 36 `SQStats` blobs, so an
unretested variant exports the **parent's** row — the minimal shape is no defence; only canaries or a
distinct-results check detect a dead chain. Databanks do **no** de-duplication on `load`/`copy`.

## Evidence
- Probe (W1, 5060): 3 hand-made variants of `XAUUSD/SPP IS/Strategy 17.9.39` (`DICrossPeriod1` 55/60/70,
  parent `<Fingerprint>` left in), 15.0 KB each, `-databank action=load folder=…` into `Retester/ProbeA`:
  `Records: 3`, own names, full export rows. Dropping `optimizationProfile.bin`, `orders.bin`,
  `dailyEquity.bin` costs nothing at load. Retest works too (retest-rewrites-sqstats).
- Controls: load 3 → 3; load same folder again → **6**; copy those 6 → 6; copy same 6 again → **12**.
  No fingerprint, name or similarity check. Removing `<Fingerprint>` is prudence (wrong data), not required.
- 📓 Only similarity filter lives in the builder: `DismissTooSimilarStrategies`, `FreshBloodReplaceSimilar`
  in `Build-Task*.xml`; none in `Retest-Task*.xml` or `config.xml` databank registrations.
- Real factory output (W2, `python3 -m sqx.variants.make --limit 3`, `shape: minimal`) into
  `Retester/VerifA`: tuples differ (`DICrossPeriod1` 67/43/94 + 7 more), fingerprint removed, yet all three
  export net profit `22650.2`, 755 trades, PF `1.15`, Sharpe `0.38`, DD `8449.28`, `Filters result: FAILED`
  — parent's. Right: own names `P00000/1/2`, `Symbol`/`TimeFrame` (`XAUUSD_DukasM1_Infinox`, M30), 3 in 3 out.
- 🤔 Cheap second detector: refuse a batch whose rows are identical across distinct `tuple_hash`.
  `sqx/variants/collect.py` counts distinct results among controls and aborts when all are identical.
- A databank made with `-databank action=create` does not appear on disk even after `synctofiles`
  (`user/projects/Retester/databanks/ProbeA/` never existed); read it via `action=export`.
- `action=count` after `action=load` destroys the load (see databanks/databank-verbs).
