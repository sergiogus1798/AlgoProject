# sqx/databank — reading what a databank holds

| file | what it does | run it | in → out |
|---|---|---|---|
| `fingerprint.py` | A databank's strategies reduced to one signature, so an export can tell a resave from a change. | imported by `ui/daemon/loader/state.py`, `pipeline/autopilot/judge.py` | .sqx files → hex digest |
