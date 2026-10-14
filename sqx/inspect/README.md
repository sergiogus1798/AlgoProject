# sqx/inspect — read what SQX has, change nothing

Every tool here is read-only. Opening a `project.cfx` or a `.sqx` touches no SQX state and needs no
running instance, so these are safe at any time, including while the owner's GUI is busy.

| file | what it does | run it |
|---|---|---|
| `dump_project.py` | Render a project.cfx as a readable Markdown pipeline map. Reading never touches SQX state. | `python3 -m sqx.inspect.dump_project <PROJECT> -o /tmp/<PROJECT>.md` |
| `feeds.py` | The clock a feed's bars and trades are stamped in, as SQX's own data registry declares it. | imported (`sqx.inspect.feeds.timezone(feed)`) |
| `index_sqx.py` | Index every .sqx on this machine by the hash of its inner strategy XML. | `python3 -m sqx.inspect.index_sqx out.json` |
| `instruments.py` | List the trading costs every project has configured, per instrument. | `python3 -m sqx.inspect.instruments [--json]` |
| `keep_tasks.py` | Produce a variant of a project.cfx keeping only tasks of the given types. | imported by `sqx.projects.builder` (`keep`) |
| `project_health.py` | Report what is wrong with every project on an install: broken archives, drift, mojibake. | `python3 -m sqx.inspect.project_health [--json]` |
| `project_map.py` | Turn a parsed project.cfx into the sections of its Markdown pipeline map. | imported |
| `project_parts.py` | Read the pieces of one task's XML: databanks, conditions, rankings, cross-checks. | imported |
| `template_check.py` | Check whether the strategies a project built really use the blocks its template declares. | `python3 -m sqx.inspect.template_check [PROJECT ...]` |
| `vocabulary.py` | What one SQX install can express: its blocks, its random groups, and what each pools. | `python3 -m sqx.inspect.vocabulary [TERM] [--role ROLE] [--diff ROLE] [--snapshot]` |
| `strategymeta/` | One strategy's metadata as fields — direction, entry/exit conditions with values, orders and stops, money management, Friday close, the last test's and the task's costs, today's asset card hash | `python3 -m sqx.inspect.strategymeta <file.sqx> [--cfx <project.cfx>]` |

`instruments.py` is what keeps `assets/symbols/*.yaml` honest: it reports what SQX carries today,
which is the `sqx_default` side of every override.

A project whose `config.xml` references a task file its archive lacks makes `dump_project.py` raise
`KeyError`. That is not a bug here — it is how a project corrupted in the way `OPEN.md` issue 3
describes announces itself, and the GUI hides it. `project_health.py` reports the same thing across
every project at once, without the traceback. The one project on this install broken that way,
`Infinox_SP500ft_H4_HighPrecision`, has a written repair that the owner withdrew (issue 3) — the
tool is not kept around unused.

`template_check.py` ignores what a template's random blocks will contain — the builder chooses those
— and compares only the blocks the template fixes. A template made entirely of random groups fixes
nothing, and the tool says so rather than passing it.

`vocabulary.py` answers the question that has to be settled before a template is designed: does this
install know the thing the idea names, and can a template *reach* it. Those are two questions. A
template references **groups**, never blocks, so a block no group pools is unusable however native
it is — the tool says `NO GROUP POOLS IT` rather than reporting a hit and letting the design fail
later. It also calls out **empty groups**: a group with no items is structurally valid, a template
pointing a hole at it builds without error, and nothing is ever sampled.
