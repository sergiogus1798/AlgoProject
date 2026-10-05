---
name: workflow-simple
description: Run the WHOLE workflow (steps 5 to 25) for a Simple Strategy — no template, one side — with one command that creates the project, applies the palette and runs every SQX task and study unattended. Fully mechanical, any model can run it. Use when the owner asks to run, launch or test the workflow on an asset without a template ("estrategia simple", "sin plantilla").
---

# /workflow-simple

One command does everything: `bin/workflow.sh simple`. You decide nothing; you collect eight
values, launch, wait, and report.

## 1. The eight values — every one from the owner, none guessed

| value | what | example |
|---|---|---|
| PROJECT | `Test_…` (a test, thrown away) or `Trade_…` (real); letters, digits, underscores | `Test_NIKKEI225_M30_simpleL_x` |
| SYMBOL | the asset, as in `assets/` | `NIKKEI225` |
| TF | `M15`, `M30`, `H1` or `H4` | `M30` |
| SIDE | `long` or `short` — never both (hard rule 13) | `long` |
| PALETTE | one idea family: a file name of `sqx/blocks/palettes/` without `.yaml` (hard rule 15) | `tendencia_base_v3` |
| PURPOSE | one sentence, what the project is for | `"Tendencia en Nikkei M30, largos"` |
| STRATEGIES | how many the build stops at | `1000` |
| MINUTES | the build's time cap | `20` |

If the owner did not give one of them, ask for it. `--smoke` only when he says it is a functional
test (a `Test_` project): then only the readability rules judge.

Before launching: `.claude/skills/sqx-wait/preflight.sh` — the custodian must be free. If someone
else holds it, say so and stop.

## 2. Launch — one command, in the background

```bash
bin/workflow.sh simple <PROJECT> <SYMBOL> <TF> <SIDE> <PALETTE> "<PURPOSE>" <STRATEGIES> <MINUTES> [--smoke]
```

Run it with `run_in_background: true` and do NOTHING until it notifies (hard rule 18): no polling, no
`sleep`, no reading SQX's log, and **nothing CPU-heavy on the machine while it runs** (a parallel
test run or a study slowed SQX's tasks by 2x on 2026-10-05). A full run of 1,000 strategies with
10 mothers of 500 variants took 160 min. If the owner asks how it goes, read ONE line:
`cat ~/Desktop/AlgoData/autopilot/<PROJECT>/*/estado.txt | tail -1`.

The command does, in this order, and stops at the first failure:
1. `python3 -m core.assets <SYMBOL>` (hard rule 5).
2. `sqx.projects.builder … --workflow` — the project, with every step's task, on the custodian.
3. `sqx.projects.buildingblocks --palette …` — the blocks the build may draw.
4. `pipeline.autopilot.run` — steps 6 to 25 in ONE SQX session, judging and cutting by
   `pipeline/autopilot/criteria.yaml`. What each step runs and which databank it reads and
   fills: `.claude/skills/workflow-simple/steps.md`.

## 3. When it notifies

The command printed three things: the last status line, the failure (if any) and the path of
`resumen.md`. Read `resumen.md` (one line per step) and report to the owner in Spanish: per step
what ran, seconds, the cut (in → out), and where it stopped. Then, by the last status line:

| last line | meaning | do |
|---|---|---|
| `FIN · …` and resumen says «Se para antes del paso 26» | complete | report; step 26 (MT5) is another task |
| `FIN · …` and resumen says «no dejó ninguna superviviente» | complete: a cut left nobody | report which step; this is a result, not a failure |
| `FALLO en el paso N: …` | failed | report N and the first lines of `fallo.md`; then §4 |
| `workflow: …` (no status line) | refused before starting | report the sentence as it is; do not work around it |

## 4. After a failure — exactly this, nothing else

1. `bin/sqx-worker.sh --role custodian status`. If it is up and its owner is this session:
   `bin/sqx-worker.sh --role custodian stop`. If the owner is someone else: leave it, report.
2. ONE retry, of the same project from where it stopped: `bin/workflow.sh run <PROJECT>` (add
   `--smoke` if the first launch had it), in the background, as in §2.
3. If it fails again at the same step: one last try with `bin/workflow.sh run <PROJECT> --restart`.
4. If that fails too: stop. Report the step and `fallo.md` to the owner. Do not edit code,
   `criteria.yaml` or the project to get past it.

## Never

- Run workflow steps by hand, one by one, or call SQX directly: this command is the only way
  (CLAUDE.md hard rule 19).
- Use the master install, `pkill`, or a project that is not the one named here.
- Delete or retire the project when it ends unless the owner says so (a `Test_` project is
  retired with `python3 -m sqx.projects.retire <P> --role custodian --yes`, worker stopped).
- Change `pipeline/autopilot/criteria.yaml`. Its rules are the owner's.
- Guess a missing argument. Ask (hard rule 11).
