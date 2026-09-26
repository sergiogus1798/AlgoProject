---
q: sqx.variants.execute hangs after Project finished; WFC_OOS1 WFC_OOS2 databank 0 files on disk; execute.py waiting forever; who stops the custodian after variants execute
tag: 🔬  date: 2026-09-26  see: sqx-drive/mcr-nullpointer-fastutil-transient
---
# `sqx.variants.execute` only stops the worker if IT started it — pre-starting the custodian yourself makes it hang after SQX says "Project finished"
The skill's own warning ("Nunca dejar el worker arriba... `execute` lo para si fue él quien lo
levantó") is precise and easy to misread as "it always stops it when done". It doesn't: if the
custodian was already running when `execute.py` was invoked (because the operator started it by
hand, e.g. following `/template-run`'s own stop-then-start pattern before calling `execute`), the
script correctly leaves that worker alone on exit — **but its own export step needs the databanks
synced to files, which only happens on worker STOP.** Nobody stops it, so `execute.py` sits
polling forever with the SQX side fully done.

## Evidence
- 2026-09-26, `USDJPY_workflow_profiling_v1`, `sqx.variants.execute --work
  .../Strategy_1.29.55 --project USDJPY_workflow_profiling_v1`, custodian started by hand first.
  SQX log: `WFC 1 IS` (350s) → `WFC 2 OOS1` (177s) → `WFC 3 OOS2` (129s) → `Project finished` at
  11:22:14. `-project action=status` confirmed `Strategies generated 1093`, `Passed 1092`, `Failed 1`.
- `execute.py` kept running at ~0.9% CPU (idling, not crashed) for **13+ minutes** after that with
  zero new output. `find .../databanks/WFC_Build -iname '*.sqx' | wc -l` → 937 of 1093 (a stale
  partial autosync); `WFC_OOS1` and `WFC_OOS2` → **0** — proof the sync never ran for those two.
- Fix: `bin/sqx-worker.sh --role custodian stop` (manual, since I had started it manually too).
  Within seconds `execute.py` printed its remaining progress (`3279 de 3279 reteseadas`,
  `exportando WFC_Build/OOS1/OOS2`) and exited 0 with `1093 en disco` for all three segments.
- Consequence for the operator: **let `execute.py` manage its own worker lifecycle** — do not
  pre-start the custodian before calling it, unlike the `/template-run`/`/mcretest`/`/spp` pattern
  which explicitly does start-then-stop-then-start around the skill's own command. If the custodian
  is already up for another reason, be ready to stop it by hand the moment `Project finished`
  appears in the SQX log, or `execute.py` will look hung indefinitely with no error to explain why.
