---
name: mcretest
description: Configure the eight MC Retest tasks of a custom SQX project — one perturbation each, the asset's own ranges, acceptance silenced, and the MinDistance task only when the population trades with stop or limit orders. Use when the owner asks to set up, configure or prepare the MC Retest in SQX, the MCR tasks, or the step 13 of the workflow.
---

# /mcretest

Step 13 of the workflow, the SQX half. It leaves the eight MC Retest tasks of a custom project
configured and ready to run. Reading what they produce is `studies/breakage/mcRetest/`
(step 14), and the Monte Carlo that reorders trades is OUT of the workflow on purpose.

> **Owner, 2026-10-07: the workflow's stage runs only `MCR 1 Bar`, `MCR 4 MinDist` and `MCR 7 OHLC`** (after
> step 14's T1 neighbour batch, `sqx.variants.neighbourbatch`). `MCR 2, 3, 5, 6, 8` are out of the stage
> (`sqx/projects/stages.yaml`); their definitions stay in `assets/_build.yaml` and the text below about
> «the eight» describes the catalogue, not what the autopilot starts. Not live-tested: this configurator
> on a project without the five tasks. Step 14 cuts on `MCR 7 OHLC`, which `SPP IS` reads.

## The one thing to understand first

The eight tasks exist to **attribute**, not to filter. Each one perturbs a single thing, so when a
strategy falls it is known what it depended on: the cost of entering, the fill, its own parameters or
the exact history it happened to see.

That imposes two things, and the command writes both:

- **A single active method per task** (six in the stress one). A task that moves two things cannot
  attribute the damage to either, and `studies/breakage/mcRetest/` refuses to ingest its databank.
- **Acceptance conditions off.** With them live SQX deletes what fails and each task chains into the
  next: in the end you only know how many survived. The verdict is taken in Python and applied with
  `/curate`.

That is why **all eight read the same databank**: they are eight readings of one population, not a
funnel.

## The Exits rule — 🔬 2026-10-06

`RandomizeExitParameters` («MCR 6 Exits», and one of «MCR 8 Stress»'s methods) is written **only** if
some strategy of the input population has an exit method set — stop loss, profit target, trailing,
move to BE or exit after bars (`sqx.projects.orders.with_exits`: a Param `exitMethod="true"` whose
Formula is not `.None` or whose value is not 0). Over condition-only exits SQX's MC sub-jobs never
return and the task sits for ever with nothing in the log. → `knowhow/sqx-drive/retest-task-hangs-silently-deadline.md`

## The MinDist rule — the owner's, 2026-09-23

`MCR 4 MinDist` is configured **only** if the population carries **stop or limit** orders. The minimum
distance is how close to the price the broker lets a pending order be placed; with market entries
there is none, and the task would draw a thousand times a number nobody reads.

The command resolves it by itself and says where the answer comes from:

| source | when | what it is worth |
|---|---|---|
| `population` | the databank already exists | opens the `.sqx` and looks at which orders they use. It is the good answer |
| `generator` → `no` | there is no population and the builder cannot emit pending orders | safe: what cannot be generated is not there |
| `generator` → `SIN RESOLVER` | there is no population and the builder **can** | not invented: the task is left unconfigured and must be reviewed after the build |

Inside `MCR 8 Stress` the same happens with its minimum-distance method: that method is dropped and
the task is written with the other five. The condition belongs to the method, not to the task.

## Run it

```bash
python3 -m core.assets <SYMBOL>                        # preflight, BLOCKING
python3 -m sqx.projects.mcretest <SYMBOL> \
    --cfx <install>/user/projects/<PROJECT>/project.cfx --input <databank>
```

`--input` is the population that is perturbed and has no default: ask the owner which one if the
previous step does not make it clear. In a workflow project the order is permanent — Cross Market →
Cross TF → MC Retest (owner, 2026-09-29) — and the input is `CrossTF_Mothers`: the mothers `CrossTF`
left, without their scaled siblings, which `sqx.projects.crosstfload --mothers` copies with the worker
stopped (the window does it by itself when launching step 13); `builder --workflow` already wires the
eight tasks to that databank.

Before writing: **the `.cfx` cannot be open in an instance** — SQX rewrites it on exit (hard rule 4).
The command refuses and says what to stop.

`<PROJECT>` is the workflow's (`/template-run --workflow`): it already carries the eight tasks. The
command leaves them as **the only active ones**, except those it could not configure (`⊘`), which stay
off. Run it on the custodian and one thing at a time (first, `ListAgents`,
`ls -lt <install>/user/projects` and the log: the `stop` kills any session's work):

```bash
bin/sqx-worker.sh --role custodian start
python3 -c "from core import worker; worker.call('-project action=stop name=<PROJECT>','custodian')"
N=$(.claude/skills/sqx-wait/wait.sh --role custodian mark)
python3 -c "from core import worker; worker.call('-project action=start name=<PROJECT>','custodian')"
.claude/skills/sqx-wait/wait.sh --role custodian --from "$N"   # run_in_background; nothing more until it notifies (rule 18)
bin/sqx-worker.sh --role custodian stop || exit 1   # exits 1 if the worker is still alive: go no further
```

## What to look at in the output

- The `ordenes` line: where the pending-orders verdict came from, and how many strategies were read.
- One `⊘` per unconfigured task, **with the reason**. The two legitimate reasons are "no hay órdenes
  pendientes" and "rango sin decidir en `assets/symbols/`". Anything else is a badly cloned project.
- `condicion(es) apagada(s)` different from zero in each task written: if it shows 0 in all, the donor
  already brought them off and it is worth checking.

## Where each thing is changed

| what | where |
|---|---|
| what each task perturbs, and its own `simulations`, `precision` and `segment` | `assets/_build.yaml`, `mc_retest:` block. Each task carries its own |
| `precision` | `1` = chosen timeframe, fast and coarse · `2` = one minute, slow and fine. It goes the opposite way to what the word suggests, and 2 costs double (measured) |
| `segment` | `build` one segment · `build..oos1` **two dots**, one continuous window spanning both, charged at the last one's cost. `oos2` is forbidden and the command refuses |
| between which two values spread, slippage and minimum distance are drawn | `assets/symbols/<SYMBOL>.yaml`, `mc_retest:` block |
| the titles of the eight tasks | **contract** with `studies/breakage/mcRetest/inputs/tasks.py`. Changing them breaks step 14 silently |

Manual: `docs/manual/08-montecarlo.pdf` (cap. 32-mcretest). Reading results: `docs/manual/08-montecarlo.pdf` (cap. 11-retest-mc).
