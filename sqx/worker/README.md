# sqx/worker — the state of a SQX worker install

| file | what it does | run it | in → out |
|---|---|---|---|
| `guard.py` | Whether a worker is up, and the marker a launcher job leaves while the worker it started runs. | imported by the launchers (`ui/daemon/launch/run.py`, `ui/daemon/advance/run.py`), `winddown.py`, `mt5/verify/sqxside.py` | install → sign, marker |
| `preflight.py` | Whether «Continuar workflow» may touch a project's install now, and every reason it may not. | imported by `ui/daemon/advance/`, `ui/daemon/launch/`, `pipeline/autopilot/` | project, databank → `{ok, reasons, …}` |
| `winddown.py` | Cancelling a launcher job: let it stop the worker it started, and stop only that worker. | — | — |
