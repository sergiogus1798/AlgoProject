# ui/daemon/workflow — the rail's route: every step of one project, read from disk

`GET /api/workflow?project=<P>` → `{project, asset, steps[], oos2, blind}` (SPEC §2 of the
unified UI). One row per line of `docs/AgentPDFs/WORKFLOW.md`'s table — the half steps included,
28 today — each with `state` (`done|running|pending|blocked|sealed|missing`), a Spanish `why`,
the funnel `in`/`out` and the `day`. Read only: files under the data root, the install's
`project.cfx`, logs and databank folders, and the ledger. **No command to any install**, not
even `-project action=status` (`progress.state` sends that one; the rail does not call it).

**Imports from:** `core/`, `ledger/`, `sqx/projects/stage`, `ui/daemon/{progress,tasklog,jobs,runs}` ·
**Consumed by:** `ui/daemon/app.py` (includes `ROUTER`), `ui/desktop/workflow/`

| file | what it does | run it | in → out |
|---|---|---|---|
| `api.py` | `ROUTER` and the route; gathers the context once and runs every step's reader | imported | project → JSON |
| `steps.py` | The step table: number, title, kind, study keys and which evidence proves it | imported | — |
| `derive.py` | One reader per kind of evidence: state, why, funnel; and the seal on 17-19 | imported | context → step |
| `sources.py` | What the disk holds: the install, its tasks and runs, a study's results, the template link | imported | disk → dicts |
| `ledgerview.py` | The project's ledger studies, the oos2 budget and the blind door — asked of `ledger.gate`/`spend` | imported | ledger → dicts |

## How each state is derived

- **1-3** `done` when a template is tied to the project: `runs.csv`, `projects/registry.csv`,
  else a ledger study whose family is a folder of the template library; `missing` otherwise.
- **4** `core.assetcheck` today: `blocked` when a cost is undecided or the schema breaks.
- **5** the project folder in an install (custodian, conductor, master, in that order).
- **SQX steps** (6, 7, 9, 11, 13, 15, 19) — the tasks `sqx.projects.stage.titles` names:
  `running` when the install log's last start is this project and its current task is one of
  them; `done` when their output databank holds `.sqx` or today's project log shows a finished
  run; the funnel from that run's tested/passed, else the databank counts on disk.
- **Python steps** — the newest contract result of the step's studies under
  `reports/<P>/<databank>/<day>/<key>/` or `{strategyPermutations,structural,atrCalculator}/<P>/<batch>/estudios/`;
  `running` when a daemon job runs one of them on this project. Funnel: the gate manifest's
  `entered/survives`, else `verdict.csv` rows with `out` = verdicts not in `steps.DROP`, else
  the per-strategy JSONs; a batch study counts batches.
- **10.5** the `CrossTF_Input` databank; **16.5** the mothers' batches with `collected.json`.
- **17, 18, 19** while `ledger.gate.allow_read` refuses: a finished one is `sealed` with no
  numbers and no verdict in `why`. **20** is `blocked` with the gate's own sentence until then.
- **oos2** `looks` = this project's ledger rows on `oos2` (`ledger.spend.virgin`), `allowed` is
  always None — `_policy.yaml` says who may look, never how many times.

## Traps

- **The ledger is keyed by study (asset, timeframe, family), not by project.** A study belongs
  to a project when its id ends with the project name or a row names it; a study that never
  names its project is invisible here.
- **`tasklog.task_runs` reads today's project log only**; on another day an SQX step falls back
  to the databank counts, which `/curate` has already thinned (the `why` says so).
