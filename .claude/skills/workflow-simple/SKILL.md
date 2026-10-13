---
name: workflow-simple
description: Run the WHOLE workflow (steps 5 to 21, then 26) for a Simple Strategy — no template, one side — with one command that creates the project, applies the palette and runs every SQX task and study unattended. Fully mechanical, any model can run it. Use when the owner asks to run, launch or test the workflow on an asset without a template ("estrategia simple", "sin plantilla").
---

# /workflow-simple

One command does everything: `bin/workflow.sh simple`. You decide nothing; you collect nine
values, launch, wait, and report.

## 1. The nine values — every one from the owner, none guessed

| value | what | example |
|---|---|---|
| PROJECT | `Test_…` (a test, thrown away) or `Trade_…` (real); letters, digits, underscores | `Test_NIKKEI225_M30_simpleL_x` |
| SYMBOL | the asset, as in `assets/` | `NIKKEI225` |
| TF | `M15`, `M30`, `H1` or `H4` | `M30` |
| SIDE | `long` or `short` — never both (hard rule 13) | `long` |
| FAMILY | the idea family of the strategy, one key of `_expected_sign` in `assets/_markets.yaml` (`python3 -c "from core.assetdata import expected_sign; print(list(expected_sign()))"`): `breakout`, `trendFollowing`, `meanReversion`, `momentum`, `volatility`, `pattern`, `session`. Recorded in `projects/registry.csv`; step 10 reads it. **Missing or unclear: ask the owner (rule 11), never default** | `breakout` |
| PALETTE | one idea family: a file name of `sqx/blocks/palettes/` without `.yaml` (hard rule 15) | `tendencia_base_v3` |
| PURPOSE | one sentence, what the project is for | `"Tendencia en Nikkei M30, largos"` |
| STRATEGIES | the databank's capacity; the build stops at its time limit (MINUTES), not when this fills (5/5 runs of 2026-10-10/11 stopped at exactly 1,800 s; `assets/_build.yaml:75-80`) | `1000` |
| MINUTES | the build's time cap | `20` |

If the owner did not give one of them, ask for it. `--smoke` only when he says it is a functional
test (a `Test_` project): then only the readability rules judge and at most
3 strategies go on after step 8.

`--until <step>` (`oos`, `crossmarket`, `crosstf`, `mcretest`, `spp`, `wfm` — `wfm` keeps every task, stops before step 20 and is repeated on `run`) only when the owner asks for a
run that ends at that step: the project is created without the later steps' tasks and the run
ends at that step's judge («Se para antes del paso N: el proyecto no lleva sus tareas»).

Before launching: `.claude/skills/sqx-wait/preflight.sh` — the custodian must be free. If someone
else holds it, say so and stop.

## 2. Launch — one command, in the background

```bash
bin/workflow.sh simple <PROJECT> <SYMBOL> <TF> <SIDE> <FAMILY> <PALETTE> "<PURPOSE>" <STRATEGIES> <MINUTES> [--until STEP] [--smoke]
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
4. `pipeline.autopilot.run` — steps 6 to 21 (then 26, when its parameters are given) in ONE SQX session, judging and cutting by
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

Refusal «custodian: los databanks no terminaron de cargaron en 5 min; sesión matada por PID, ficheros intactos»: an earlier `stop` killed SQX mid-save and left a truncated `.sqx`. Do not retry; report it (`knowhow/sqx-drive/stop-killed-mid-save-truncated-sqx.md`).

## 4. After a failure — exactly this, nothing else

1. `bin/sqx-worker.sh --role custodian status`. If it is up and its owner is this session:
   `bin/sqx-worker.sh --role custodian stop`. If the owner is someone else: leave it, report.
2. ONE retry, of the same project from where it stopped: `bin/workflow.sh run <PROJECT>` (add
   `--smoke` if the first launch had it), in the background, as in §2.
3. If it fails again at the same step: one last try with `bin/workflow.sh run <PROJECT> --restart`.
4. If that fails too: stop. Report the step and `fallo.md` to the owner. Do not edit code,
   `criteria.yaml` or the project to get past it.

## 5. Failures already seen — recognise them before retrying

One row per failure a real run hit (owner, 2026-10-13: every error is fixed and noted here). A
symptom in this table on code that already carries the fix is a NEW bug: report it, do not retry.

| symptom in `fallo.md` | cause | fixed in |
|---|---|---|
| step 11.5 «CrossTF_M30 no tiene export: exporta ese databank…» | the live export after step 11 only took the databanks of the tasks preflight chose; the extra-timeframe tasks (`CrossTF M30`, `CrossTF H4`) are created later, by the fill | `0106b60` (2026-10-13), `ui/daemon/launch/liverun.py`: their banks are added to the step's outputs. A project that failed here before the fix continues with `bin/workflow.sh run <PROJECT>`: the stop exported them |
| `bin/workflow.sh`: «opción desconocida: --mt5-from» | the script did not pass step 26's parameters on, so step 26 could not run through the one command | 2026-10-13: `--mt5-from=`, `--mt5-to=`, `--mt5-model=`, `--mt5-firms=` (one word each, with `=`) go through to the autopilot |
| resumen: «el paso 26 no se lanza: el log de hoy de SQX_w1 se escribió hace N min (< 15)» | step 26's pre-check read the conductor's log, which the autopilot's own exports (steps 11, 16.5) had just written, as someone else's | 2026-10-13, `mt5/verify/autopilot.py`, `pipeline/autopilot/finalists.py`: the autopilot says the log is its own (`own_log`); lock, open port and live process still refuse |

## Never

- Run workflow steps by hand, one by one, or call SQX directly: this command is the only way
  (CLAUDE.md hard rule 19).
- Use the master install, `pkill`, or a project that is not the one named here.
- Leave a `Test_` project behind: whoever creates it retires it when the run has answered
  (CLAUDE.md rule 6; owner, 2026-10-13) — `python3 -m sqx.projects.retire <P> --role custodian
  --yes`, worker stopped. A `Trade_` or `Research_` project is never retired here.
- Change `pipeline/autopilot/criteria.yaml`. Its rules are the owner's.
- Guess a missing argument. Ask (hard rule 11).
