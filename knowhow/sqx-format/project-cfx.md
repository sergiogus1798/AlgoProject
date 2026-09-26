---
q: project.cfx format, cfx zip config.xml task xml, edit project.cfx while running, task output databank, Databank value null, cfx only config.xml rejected, missing task files project dropped, templateFile Project vs StrategyType
tag: 🔬  date: 2026-09-02  see: sqx-drive/project-verb, sqx-format/retest-rewrites-sqstats
---
# project.cfx is a ZIP (`config.xml` + `<TaskType>-Task<N>.xml`); SQX rewrites it on save and exit
Reading is always safe (no SQX needed); `sqx/inspect/dump_project.py` renders one. **Never edit a cfx a
running instance holds** — silently discarded; use the `-project` API (`knowhow/sqx-drive/`). A task's
real output databank is `<Databank name="Output" value=>` in the task XML, not `<Task title=>`.
The strategy template is `<StrategyType templateFile=>` in the Build task; `<Project templateFile=>` is dead.

## Evidence
- All 14 project files restamped within the same second (`14:33:43`, 2026-09-02). No error on loss.
- Cloning a task without changing `Output` makes every clone write to the same databank.
- `<Databank … value="null">` = SQX literal for "task type's default databank"; Build tasks ship so.
- A `.cfx` with **only** `config.xml` is not a loadable template (`~/Desktop/Benchmark.cfx`, anything
  from `saveconfig`) — rejected.
- `config.xml` declaring task files the archive lacks → GUI drops the project, no error. Scan:
  `sqx/inspect/project_health.py`. The one instance found (`OPEN.md` issue 3) has a written repair
  the owner withdrew; the tool was removed rather than kept unused.
- `<Project templateFile=>` records the `.cfx` it was imported from; on Windows imports it is
  UTF-8-as-CP1252 re-encoded **seven times**, decoding to
  `C:\Users\Rubén Martínez\OneDrive\Escritorio\FILTROS\Build strategies.cfx`, on 11 of 16 projects,
  always the same string. Nothing resolves it — it is a Windows path on a Linux box, and it is not a
  strategy template (that is `<StrategyType templateFile=>`, above). Not worth repairing: it would
  mean rewriting eleven archives offline for a field nothing reads. `project_health.py` decodes it.
- Rewrite-on-exit is also how `-project action=loadconfig` becomes permanent (see retest-rewrites-sqstats).
