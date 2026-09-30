---
q: auto export after SQX run; export when task finishes; crossmarket needs export of the retest; afterrun; ALGO_NO_EXPORT; worker.stop export; owner lock OWNER file; puede ser de otra sesión; headless claude authoring template from window; MCR_All ingest stale; step 14 reads old ingest; export_spp export_wfm after run; 15 min quiet guard own runs; every stop re-exports everything; SQX resave changes mtime; zip CRC fingerprint sources.sig
tag: 🔬  date: 2026-09-29  see: sqx-drive/window-advances-workflow, sqx-drive/owner-lock, databanks/sync-deletes-unloaded-files
---
# Every worker stop exports the install's stale databanks; the 24 h guard is gone, the lock decides busy now
`bin/sqx-worker.sh stop` runs `ui.daemon.loader.afterrun --role R`: per Test_/Trade_ databank the
loader's pieces (metrics → trades → harvest), then `afterrun.EXTRA` — MC ingest `MCR_All` (new
`<day>-N`: immutable), `export_spp`, `export_wfm`. Stale is by content (`state.age` checks
`<marker>.sources.sig`, SQX's sync rewrites dates not CRCs); `ALGO_NO_EXPORT=1` skips it. 2026-09-29,
owner: the 24 h "another project touched" refusal is gone (§83) — `advance.busy` now refuses only
the owner lock, the port or a live PID; `sqx-drive/owner-lock` says why that lock does not replace
the 15-min quiet rule's `released.json`, unchanged here.

## Evidence
- 🔬 `python3 -m ui.daemon.loader.afterrun --role custodian` on 2026-09-28: exported metrics
  and trades of `Test_USDJPY_donchianUpperCrossUp_M30/OOS` (stale), left the rest (fresh).
- 📓 The owner's «crossmarket: necesita el export del retest cross-market» came from
  `ui/daemon/runs.py` `context()`: `raw/<P>/Retest_Markets_-_Family/*/trades.parquet` absent
  until the databank was chosen in the window (the loader loaded it at 22:04, after the error).
- 🔬 2026-09-28, before the fix: `advance.busy('custodian', 'Test_XAUUSD_donchianUpperCrossUp_H1')`
  right after creating it read `Test_USDJPY_donchianUpperCrossUp_M30 se modificó en SQX_w2 hace
  1.0 h` (the owner's own crossmarket run at 21:39) — `RECENT_H = 24` in
  `ui/daemon/advance/preflight.py`, removed 2026-09-29 (OPEN.md §83, §32's real lock in its place).
- 🔬 `ui.daemon.create.author` (`CLAUDE_BIN -p … --permission-mode auto`) on the chat's draft
  `donchianUpperBreakUp`: ~3 min, answered `YA EXISTE: donchianUpperCrossUp` and deleted the
  draft. Headless it warns «workspace has not been trusted» and ignores the 42 allow rules of
  `.claude/settings.json`; auto mode ran the skill anyway.

2026-09-29: step 13 (7 MCR over 21) from «▶ SQX»: the stop exported metrics and trades of all 7,
but `raw/<P>/MCR_All/` stayed at 2026-09-27. `afterrun` with EXTRA ingested 539 runs in 17 s.
2026-09-29 SPP run: the stop spent 8 min re-exporting all 12 databanks, none changed. Entry
CRCs of Results matched between 06:47 and 10:52; fingerprinting 2.6 GB of .sqx costs 2 s cold.
2026-09-29 15:30: the WFM (918k trades) was re-exported at a variants stop although unchanged:
the EXTRA markers were folders (`<day>/wfm`), whose date an overwriting export does not move, so
the export never read fresh and was never signed. Markers are now each export's `manifest.json`.
17:24: still re-exported at each stop — a WFM result's attributes carry Java object addresses
(`stats="…SQStats@4f573d92"`), new on every save; `state._canonical` now keeps only the class.

