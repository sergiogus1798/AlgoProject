---
name: spp
description: Configure and run the two SPP tasks of a custom SQX project — the System Parameter Permutation grid over the in-sample and the out-of-sample window, at the owner's spread and steps, with every acceptance silenced so the profile is a map and not a filter. Use when the owner asks to set up, configure or run the SPP in SQX, the permutation profile, or step 15 of the workflow.
---

# /spp

The workflow runs through `bin/workflow.sh` (CLAUDE.md rule 19); this skill is the manual route for testing one step's code, never for a real run.

Step 15 of the workflow, the SQX half. It leaves the `SPP IS` and `SPP OOS` tasks of a custom
project configured, and optionally runs them on the custodian. Reading what they produce is
`studies/breakage/spp/` (step 16), which comes out of it with the variants' `design_brief.json`.

## The one thing to understand first

**The SPP is `OptProfileSysParamPermutation`.** `SequentialOptimization` lives next to it, in the same
`<CrossChecks>` block, also talks about permuting parameters and **writes no profile at all**.
Switching on the wrong one cost 47 cores for 91 minutes and produced nothing (2026-09-22). The
command switches on the right one; there is no flag to get it wrong.

**The two tasks are not compared with each other.** Measured 2026-09-19: the IS and the OOS SPP of the
same strategy with identical settings share **6 tuples out of ~11,600**. SQX does not walk the same
grid twice. They are two readings of the same environment, and that is the reason the variant
factory of step 16.5 exists — to compare, you have to fabricate the tuples yourself.

**Acceptance is off, both of them.** The task's conditions (19 in a donor clone) and the four
`Eval*Check` of the crosscheck itself. With them live SQX deletes the strategies whose map it does
not like and `sppUltra` reads the surface of an already selected population without knowing it.

## Run it

```bash
python3 -m core.assets <SYMBOL>                        # preflight, BLOCKING
python3 -m sqx.projects.spp <SYMBOL> \
    --cfx <install>/user/projects/<PROJECT>/project.cfx --input <databank>
```

`--input` is the population that is permuted and has no default: normally the MC Retest survivors
(step 13-14). Ask the owner if it is not clear. The second task reads what the first wrote, and with
acceptance off that is the whole population.

Before writing: **the `.cfx` cannot be open in an instance** — SQX rewrites it on exit (hard rule 4).
The command refuses and says what to stop.

Run it afterwards, on the custodian and one thing at a time:

`<PROJECT>` is the workflow's (`/template-run --workflow`): the command above leaves its step as
**the only active one**, because `action=start` runs all the active tasks. The `stop` before the
`start` is not superfluous: in a project that already ran, a second `start` without it does nothing,
silently.

```bash
bin/sqx-worker.sh --role custodian start
python3 -c "from core import worker; worker.call('-project action=stop name=<PROJECT>','custodian')"
N=$(.claude/skills/sqx-wait/wait.sh --role custodian mark)
python3 -c "from core import worker; worker.call('-project action=start name=<PROJECT>','custodian')"
.claude/skills/sqx-wait/wait.sh --role custodian --from "$N"   # run_in_background; nothing more until it notifies (rule 18)
bin/sqx-worker.sh --role custodian stop || exit 1   # exits 1 if the worker is still alive: go no further
```

⚠️ Before touching W2: `ListAgents`, `ls -lt <install>/user/projects` and the log. The `stop` kills
any session's work.

## What to look at in the output

- **`tope 15,000 permutaciones`** — the line that matters most. The donor brings `1000000001`, SQX's
  sentinel for **exhaustive**; that is not a long task, it is a task with no end. It is always
  written, never inherited.
- **`±35 % en 18 pasos`** — ~4 % per step, the owner's default. The donor's 12 steps over ±30 are
  coarse.
- **`19 condicion(es) y 2 chequeo(s) del SPP apagados`** — if `0` shows up in both tasks, check the
  clone.
- A **`⊘`** means the project does not carry that task; a **`⚠️ esta tarea corre ademas: …`**, that
  that `.cfx` did not go through the doctrine and would run other crosschecks at the same time.

## What it costs, and why the silence is not a hang

Measured 2026-09-22 on the custodian, a real XAUUSD mother with 22 parameters: **a good half hour**
(🤔 stale: the SQX part of the whole step measured 47-121 s for 1-3 mothers in five runs of
2026-10-10/11, 📓 `fases.csv` of `AlgoData/autopilot/<P>/<stamp>/`), and the log writes one line per parameter in the first three seconds and **nothing else** until the
end. `-project action=status` says `Total tested 0` the whole time. The honest sign that it is
working is the JVM's memory going up (23.6 → 36.9 GB). Flat RSS and no log is a hang; rising RSS is
work.

⚠️ **One SPP at a time per install.** The profile is tens of GB while it is built on a 48 heap.

## Where each thing is changed

| what | where |
|---|---|
| permutation cap, ±%, step fineness | `assets/_build.yaml`, `spp:` block |
| which window each task runs and at what precision | the same block, `tasks:` |
| the `SPP IS` / `SPP OOS` titles | **contract** with the donor and with `export_spp`. Changing them leaves the task unfound |

⚠️ Two declared divergences, noted in `OPEN.md` §38 and pending the owner: the precision is `1` and
not the doctrine's `2` (at 1 minute it does not finish), and `SPP IS` runs on `build`, which is what
"in sample" means and what the master's tasks do.

Manual: `docs/manual/09-optimizacion.pdf` (cap. 33-spp). Exporting the profile:
`docs/manual/09-optimizacion.pdf` (cap. 08-spp). Reading it: `docs/manual/09-optimizacion.pdf`
(cap. 15-sppultra).
