# 1_sqx/inspect — read what SQX has, change nothing

Every tool here is read-only. Opening a `project.cfx` or a `.sqx` touches no SQX state and needs no
running instance, so these are safe at any time, including while the owner's GUI is busy.

| file | what it does | run it |
|---|---|---|
| `dump_project.py` | Render one project as a Markdown pipeline map | `python3 1_sqx/inspect/dump_project.py <PROJECT> -o /tmp/<PROJECT>.md` |
| `project_map.py` | Builds each section of that map: databanks, TL;DR, flow, task order, task detail | imported |
| `project_parts.py` | Reads one task's XML: databanks, conditions, rankings, cross-checks | imported |
| `index_sqx.py` | Index every `.sqx` in the configured pools by inner-XML hash | `python3 1_sqx/inspect/index_sqx.py out.json` |
| `keep_tasks.py` | Emit a variant of a `.cfx` keeping only the chosen task types | `python3 1_sqx/inspect/keep_tasks.py in.cfx out.cfx --types Build` |
| `instruments.py` | List the spread, commission, point value and swap every project has configured | `python3 1_sqx/inspect/instruments.py [--json]` |
| `project_health.py` | Every project's broken task references, version drift and mangled text fields | `python3 1_sqx/inspect/project_health.py [--json]` |
| `template_check.py` | Whether the strategies a project built really carry the blocks its template fixes | `python3 1_sqx/inspect/template_check.py [PROJECT ...]` |

`instruments.py` is what keeps `assets/*.yaml` honest: it reports what SQX carries today, which is
the `sqx_default` side of every override.

A project whose `config.xml` references a task file its archive lacks makes `dump_project.py` raise
`KeyError`. That is not a bug here — it is how a project corrupted in the way `OPEN.md` issue 3
describes announces itself, and the GUI hides it. `project_health.py` reports the same thing across
every project at once, without the traceback; `1_sqx/repair/graft_tasks.py` is the cure.

`template_check.py` ignores what a template's random blocks will contain — the builder chooses those
— and compares only the blocks the template fixes. A template made entirely of random groups fixes
nothing, and the tool says so rather than passing it.
