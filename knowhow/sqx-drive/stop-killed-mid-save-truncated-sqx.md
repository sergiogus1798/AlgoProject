---
q: Why does the custodian refuse to start with «los databanks no terminaron de cargarse en 5 min»?
kw: los databanks no terminaron de cargarse en 5 min; no se toca nada; Cannot load strategy from file; truncated .sqx not a zip; custodian silent for 60 s and not leaving; stop killed SQX mid-save; memory 9,999 vs disk 10,000; live.records live._files
tag: 🔬  date: 2026-10-09  see: sqx-drive/worker-process-lifecycle, databanks/sync-deletes-unloaded-files
---
# A `stop` that kills SQX while it rewrites a big databank leaves a truncated `.sqx`, and the next start refuses
Trap: SQX rewrites every loaded project's databanks on shutdown; 10,000 strategies take over 2 min with no
log line. `bin/sqx-worker.sh stop` used to kill by PID after 60 s of log silence, mid-save. The cut file is
not a zip, SQX logs «Cannot load strategy from file …», memory is one short of disk, and
`sqx.projects.live.start` refuses (correct, hard rule 1). The next stop's sync then DELETES that file.
Fix (code): the stop also counts as moving any file under `<install>/user/projects` written in the last
minute (`find … -type f -mmin -1`), up to the same 15 min. Recovery: worker stopped, restore the file from
`AlgoData/projects/snapshots/<P>/<stamp>/…`.

## Evidence
- 📓 2026-10-09 12:13 UTC, another session's `bin/workflow.sh run … --smoke` on the custodian: «custodian silent for 60 s and not leaving: killing by PID 1864137». `SQX_w2/user/projects/Trade_NIKKEI225_M30_volatilidadL/databanks/Results/Strategy 1.11.378.sqx` was 27 KB, not a zip. Restored from `snapshots/Trade_NIKKEI225_M30_volatilidadL/20261004-210011/`.
- Diagnose: compare `live.records(role, p)` with `live._files(p, role, b)` per project/databank; `grep -h <project> <install>/user/log/*.log` finds the «Cannot load strategy» ERROR lines.
