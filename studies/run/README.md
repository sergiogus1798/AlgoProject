# studies/run — where a study's input lives

Not a study: the lookups the window and the autopilot make before offering or starting one.

**Imports from:** `core.datapaths`, `core.paths`, `pipeline.ledger.state`, `sqx.projects.registry` · **Consumed by:** `ui/daemon/` (`runs.py`, `runner/`, `workflow/`, `batch/`, `filters/`, `strategy/`), `pipeline/autopilot/survivors.py` · **Must not contain:** an SQX command, a study's maths, or a write.

| file | what it does | run it | in → out |
|---|---|---|---|
| `where.py` | Where a study's input lives on the data root, found before a run is offered — never computed. | imported | data root → paths |
