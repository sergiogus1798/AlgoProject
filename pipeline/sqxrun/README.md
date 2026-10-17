# pipeline/sqxrun — one launch of SQX tasks, start to stop

What «Lanzar en SQX» runs once the window (or the autopilot) has a preflight that passed: rule 5,
a snapshot of the project, the configurators, the chosen tasks switched on alone, one start of the
worker, the wait, the stop, the restore of what SQX's sync race deleted, the counts compared. It
imports `core`, `sqx` and `ledger` only; the window's route (`ui/daemon/launch/api.py`) queues it
as `python3 -m pipeline.sqxrun.run`.

| file | what it is | called by | in → out |
|---|---|---|---|
| `run.py` | «Lanzar en SQX»: switch on one task or one step's tasks, start the worker once, wait for SQX, stop. | `python3 -m pipeline.sqxrun.run --project P --task CONSTRUCCION` (repeatable) or `--step 13` (the window queues it); `execute` imported by `pipeline/autopilot/run.py` and the window chain | a project → its tasks run, worker stopped |

`liverun.py` (the same on a GUI session already up) stays in `ui/daemon/launch/`: it needs
`ui.daemon.loader.afterrun` (`scope`, `UNREAD_TRADES`), the export CLI that `core.worker` also starts by module name.
