---
q: which log line names the project of a run; Starting project; ProgressEngine task title; SKIPPED inactive task; percent in thread name; how the window knows what SQX is running
tag: 📓  date: 2026-09-25  see: locations/report-csv-conventions, sqx-drive/running-a-task-headless
---
# The only log line naming a run's project is the CLI's `Starting project '<name>'`
`ProgressEngine` lines carry the task **title**, never the project. Two lines tie a run to a project:
`CLILogger - Starting project '<name>'` (a start via the HTTP API; a GUI start writes none) and
`Databank '<project>/<bank>' saved` at the end. The fine percentage travels in the compute thread's
name: `[Blocking computeThread common #55 - WF: 16 runs : 40 % OOS WFO 2]`. Every `start` is one
workflow step (`stage`), so a task done in an earlier start reads `SKIPPED, inactive task` now;
`ui/daemon/progress.py` keys on the last `Starting project` and calls such a task «hecha antes».

## Evidence
- `SQX_w2/user/log/StrategyQuant/log_2026_09_25.log`, run of `USDJPY_emaCross_H1` on 2026-09-25
  21:07–21:12: `Starting project 'USDJPY_emaCross_H1'` (CLILogger), then per-task `ProgressEngine`
  lines, `CrossTF : Task finished in 19.31 s.`, 17 × `SKIPPED, inactive task`, `Project finished`,
  then three `Databank '…' saved` lines.
- Read from disk only; the custodian was mid-job and received no command.
