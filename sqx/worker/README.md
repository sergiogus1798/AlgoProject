# sqx/worker — the state of a SQX worker install

| file | what it does | run it | in → out |
|---|---|---|---|
| `guard.py` | Whether a worker is up, and the marker a launcher job leaves while the worker it started runs. | imported by the launchers (`ui/daemon/launch/run.py`, `ui/daemon/advance/run.py`), `winddown.py`, `mt5/verify/sqxside.py` | install → sign, marker |
| `preflight.py` | Whether «Continuar workflow» may touch a project's install now, and every reason it may not. | imported by `ui/daemon/advance/`, `ui/daemon/launch/`, `pipeline/autopilot/` | project, databank → `{ok, reasons, …}` |
| `session.py` | One worker session of a launcher: rule 5, wait for SQX to be ready, follow a run to «Project finished», the build's time cap. | imported by `ui/daemon/launch/{run,chain,liverun}.py`, `ui/daemon/advance/run.py`, `mt5/verify/{run,sqxside}.py`, `mt5/reconcile/sqxside.py` | project, role → run followed to its end |
| `winddown.py` | Cancelling a launcher job: let it stop the worker it started, and stop only that worker. | — | — |
