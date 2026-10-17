# sqx/worker — the state of a SQX worker install

| file | what it does | run it | in → out |
|---|---|---|---|
| `guard.py` | Whether a worker is up, and the marker a launcher job leaves while the worker it started runs. | imported by the launchers (`ui/daemon/launch/run.py`, `ui/daemon/advance/run.py`), `ui/daemon/winddown.py`, `mt5/verify/sqxside.py` | install → sign, marker |
