# sqx/databank — reading what a databank holds

| file | what it does | run it | in → out |
|---|---|---|---|
| `discards.py` | The discard log of one databank: what the filter in force and the manual deletions set aside. | imported by the filter routes, `sqx/worker/preflight.py` | log ↔ hidden identities, funnel steps |
| `find.py` | Where a databank's files live, which retest pairs with it, and whether SQX is writing it now. | imported by the loader routes, `pipeline/autopilot/judge.py` | project, databank → paths, facts |
| `fingerprint.py` | A databank's strategies reduced to one signature, so an export can tell a resave from a change. | imported by `sqx/databank/state.py`, `pipeline/autopilot/judge.py` | .sqx files → hex digest |
| `state.py` | What of a databank is loaded, what is stale, and the commands that bring it up to date. | imported by the loader routes, `pipeline/autopilot/` | project, databank → status, jobs |
