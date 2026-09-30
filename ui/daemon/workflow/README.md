# ui/daemon/workflow — the rail's routes: every step of one project, read from disk, and its run buttons

`GET /api/workflow?project=<P>` → `{project, asset, family, steps[], tabs, oos2, blind, backfill}`.
One row per line of `docs/AgentPDFs/WORKFLOW.md`'s table — the half steps included, 28 today —
each with `state` (`done|running|pending|blocked|sealed|missing`), a Spanish `why`, the funnel
`in`/`out`, the `day`, the databank panel's `tab`/`sub` where its result is read, and `tests`:
every study that belongs to the step (its evidence, the catalogue's studies filed under its
number, and step 8's off-sequence readings), each with its own state, a one-line `config` from
`results/knobs` with the project's feed, symbol and timeframe where the runner puts them
(`results/forproject`; a knob it leaves at the donor's is marked ⚠), `runnable` and the `databank` of its newest result. `backfill` says whether to
offer «rehacer las filas de 17-19» and the command.

Each step also carries `stage`, `panel` (its tests read the databank the panel shows: 21-25) and
`needs` (the steps to run before it, `needs.of`; the drawer paints the missing ones in red), and
the payload `chain`: what «Correr workflow» would run now and where it would stop
(`ui/daemon/launch/chainplan.plan`, painted beside its button).

`POST /api/workflow/run {project, tests: [{n, key}], databank, strategies}` queues the ticked
tests in `ui/daemon/jobs.py` → `{jobs, refused: [{n, key, why}]}`. `POST /api/workflow/backfill
{project}` queues `python3 -m ledger.backfill --blind <P> … --write` when offered.

Reading is files only: the data root, the install's `project.cfx`, logs and databank folders, and
the ledger, and `/proc` for whether an SQX process lives in the install. **No command to any
install**, not even `-project action=status`. The run routes start Python studies and nothing
else: an SQX step's own task is never a test — the rail's ▶ SQX goes to `ui/daemon/launch/`.

**Imports from:** `core/`, `ledger/`, `sqx/projects/{stage,registry}`,
`ui/daemon/{progress,tasklog,jobs,runs,results,runner}`, `ui/daemon/launch/chainplan` ·
**Consumed by:** `ui/daemon/routers.py` (includes `ROUTER`), `ui/desktop/workspace/rail.py`,
`ui/daemon/launch/chain.py` (the plan, the context, the tests' commands) ·
**Checked by:** `tools/checks.py` («workflow table»):
the numbers and the `doc` titles of `steps.py` must equal WORKFLOW.md's table, word for word.

| file | what it does | run it | in → out |
|---|---|---|---|
| `api.py` | `ROUTER` and the three routes; gathers the context once and runs every step's reader | imported | project → JSON |
| `steps.py` | The step table: number, short title, WORKFLOW.md title, kind, evidence, study keys, tab and sub-panel, the stages its tests read | imported | — |
| `derive.py` | One reader per kind of evidence: state, why, funnel; and the seal on 17-19 | imported | context → step |
| `needs.py` | `of(spec, ctx)`: the steps a step needs done first — for an SQX task step the steps filling its tasks' inputs (from the project's own tasks) and the Python step judging each, for a Python step the SQX step it reads, the variant batch (17-18.5), 17-19 for 20, 20 for 21-25 — and always the row before it | imported | step, context → step numbers |
| `tests.py` | The tests of each step, generated from the catalogue: state, one-line configuration, whether the window may start it | imported | step → tests |
| `run.py` | Ticked tests into the runner's jobs — the databank each reads and the strategies — and the backfill offer | imported | request → jobs |
| `sources.py` | What the disk holds: the install, its tasks and runs, a study's results, the template link | imported | disk → dicts |
| `ledgerview.py` | The project's ledger studies, the oos2 budget, and the blind door over the one Q9 study — asked of `ledger.gate`/`spend` | imported | ledger → dicts |

## Where a test runs

- **The databank.** From the panel, the one it shows. From the rail, the databank of the study's
  newest result on this project, then the output databanks of the SQX stages the step `feeds`
  on (8: oos, build · 10: crossmarket · 12: crosstf · 14: mcretest · 16: spp · 19-20: wfm), as
  the data root spells them (spaces become `_`); the first where the study finds its input wins.
  Steps 21-25 read survivors whose databank the rail cannot know: they run from the panel.
- **The strategies.** A study with a population command runs once; a one-strategy study runs
  once per strategy of the databank's newest export (else its cosecha), all queued at once;
  17, 18, 18.5 and the cloud run once per mother batch in `strategyPermutations/<P>/`.
- **What the run route refuses first** (`run.refusal`): an unknown step, any test of an SQX
  step — its task is SQX's, and the analysis hanging from it (the WFM study of 19, the cloud of
  16.5) is read after the task, from the databank panel, never from the rail — a study that is
  not a test of that step, and a test `tests.one` does not mark runnable.
- **What costs more than CPU** (`tests.SPENDS`: wfc, cscv, marketSurfaces, wfm, blindJoint read
  oos2; snoopingScreen writes a ledger row) carries `spends`; with steps 21-25 it has
  `auto` false: never ticked by default, never in «correr todo», and the window asks before
  each run.
- **Step 20** is refused while `ledger.gate.allow_read` refuses, before the runner is asked.
- **The family** the studies of 8 (snooping), 17, 18, 18.5 and 20 sign the ledger under is the
  template's name in `projects/registry.csv` (`runner/where.family`); no template, no run.

## How each state is derived

- **1-3** `done` when a template is tied to the project: `runs.csv`, `projects/registry.csv`,
  else a ledger study whose family is a folder of the template library; `missing` otherwise.
- **4** `core.assetcheck` today: `blocked` when a cost is undecided or the schema breaks.
- **5** the project folder in an install (custodian, conductor, master, in that order).
- **SQX steps** (6, 7, 9, 11, 13, 15, 19) — the tasks `sqx.projects.stage.titles` names:
  `running` when the install log's last start is this project, its current task is one of
  them and an SQX process lives in the install (`core.worker.holding`) — a run killed before
  «Project finished» reads pending/done with «se cortó» in `why`; `done` when their output databank holds `.sqx` or today's project log shows a finished
  run; the funnel from that run's tested/passed, else the databank counts on disk.
- **Tests** `running` when a daemon job of this project runs that study, `blocked` when the
  runner never starts it (`why`) or it signs the ledger and the project has no template, `done`
  when a result exists, else `pending`.
- **Python steps** — the newest contract result of the step's studies under
  `reports/<P>/<databank>/<day>/<key>/` or `{strategyPermutations,structural,atrCalculator}/<P>/<batch>/estudios/`;
  `running` when a daemon job runs one of them on this project. Funnel: the gate manifest's
  `entered/survives`, else `verdict.csv` rows with `out` = verdicts not in `steps.DROP`, else
  the per-strategy JSONs; a batch study counts batches.
- **10.5** the `CrossTF_Input` databank; **16.5** the mothers' batches with `collected.json`.
- **The blind door** — only under `ALGO_AUTONOMOUS=1` (`core.assetdata.enforced`); for a human it is always open (owner, 2026-09-28) — (`ledgerview.door`) asks `ledger.gate` over exactly one study, the one
  blindJoint signs and reads: `<symbol>_<timeframe>_<template folder>` from the registry row
  (Q9). Rows signed under the project's own name (E1's tests) never open it; no template, it
  stays shut. Its sentence names the study. `ledgerview.blind(rows)` remains for older callers.
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
