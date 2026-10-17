---
name: workflow
description: Run the WHOLE workflow of a strategy project — steps 5 to 21, then 26 (MT5) — with ONE command, unattended, on the custodian. Four ways in — a Simple Strategy (no template), an authored template, an existing project from where its rail is, or the fixed functional test of the whole chain. Applies the owner's filters (criteria.yaml) unless it is a functional test. Fully mechanical, any model can run it. Use when the owner asks to run, launch, continue or test the workflow ("lanza el workflow", "estrategia simple", "con plantilla", "continúa el proyecto", "prueba el workflow entero").
---

# /workflow

One command does everything: `bin/workflow.sh` (hard rule 19). You decide nothing: you pick the
way in (§1), collect its values from the owner, launch (§4), wait, and report (§5).

**Layout of this file, for whoever changes or copies it:** §1 has one block per way in (A simple,
B template, C run, D test). Everything after §1 is common to all four. To add a way in, add a
block to §1; to make a variant skill for one way in, copy the file and keep that block only.

## 1. The way in — one of four

### A. Simple Strategy — no template, one side

```bash
bin/workflow.sh simple <PROJECT> <SYMBOL> <TF> <long|short> <FAMILY> <PALETTE> "<PURPOSE>" <STRATEGIES> <MINUTES> [OPTIONS]
```

| value | what | example |
|---|---|---|
| PROJECT | `Test_…` (thrown away) or `Trade_…` (real); letters, digits, underscores | `Trade_NIKKEI225_M30_simpleL` |
| SYMBOL | the asset, as in `assets/` | `NIKKEI225` |
| TF | `M15`, `M30`, `H1` or `H4` | `M30` |
| SIDE | `long` or `short` — never both (hard rule 13) | `long` |
| FAMILY | the idea family, one key of `_expected_sign` in `assets/_markets.yaml` (`python3 -c "from core.assetmarkets import expected_sign; print(list(expected_sign()))"`). Step 10 reads it | `breakout` |
| PALETTE | one idea family: a file name of `sqx/blocks/palettes/` without `.yaml` (hard rule 15) | `tendencia_base_v3` |
| PURPOSE | one sentence, what the project is for | `"Tendencia en Nikkei M30, largos"` |
| STRATEGIES | the databank's capacity; the build stops at MINUTES, not when this fills | `1000` |
| MINUTES | the build's time cap | `20` |

### B. Template — an authored `.sqx`

```bash
bin/workflow.sh template <PROJECT> <SYMBOL> <TF> <TEMPLATE.sqx> <PALETTE|-> "<PURPOSE>" <STRATEGIES> <MINUTES> [OPTIONS]
```

PROJECT, SYMBOL, TF, PURPOSE, STRATEGIES, MINUTES as in A. TEMPLATE is the path of the template's
`.sqx` in the library, one side only (the builder refuses a template whose long and short
entries both open trades, hard rule 13). PALETTE fills the template's random hole; `-` ONLY when the
template has none (two fixed conditions a side, hard rule 14) — ask the owner which. This skill
does not author the template: that is steps 1-4, `/workflow-start`.

### C. Run — an existing project, from where its rail is

```bash
bin/workflow.sh run <PROJECT> [--until wfm] [--smoke] [--restart] [MT5]
bin/workflow.sh plan <PROJECT>          # prints what «run» would do, runs nothing
```

The project was created by A or B (or by `sqx.projects.builder --workflow`) and lives on the
custodian. Show the owner the `plan` first when he did not say where it stands.

### D. Test — the whole chain, builder to step 26, PASA or FALLA

```bash
bin/workflow-test.sh [TAG]
```

No values to ask: it is fixed (XAUUSD H1 long breakout, 10,000 strategies, 30 minutes of Build,
`--smoke`, step 26 on FTMO and Hantec, 2021-07-01 to 2022-12-31 — inside oos1 —, `ohlc_m1`) and it prints its own
verdict. **PASA only for one whole run with no failure, no retry, step 26 run and no fallback to
the slow export.** A FALLA is fixed in code (with its test and a row in §7), and then this is run
AGAIN from scratch: a run that needed a fix or a `run` to continue never counts (owner,
2026-10-13). Work that touches `pipeline/`, the exports or `bin/workflow.sh` is not finished
until this prints PASA.

## 2. Every value comes from the owner

A missing or unclear value is a question (hard rule 11), never a default — FAMILY and PALETTE
above all. Before A or B the command itself runs `python3 -m core.assets <SYMBOL>` (hard rule 5)
and stops if it fails.

## 3. Options — filters, where it ends, step 26

| option | what | when |
|---|---|---|
| (none) | **the owner's filters judge and cut at every step**: `pipeline/autopilot/criteria.yaml`. A step that leaves nobody ends the run — a result, not a failure | the normal run, every `Trade_` and `Research_` project |
| `--smoke` | functional test, `Test_` only (refused otherwise): only the readability rules judge and at most 3 strategies go on after step 8 | only when the owner says it is a test |
| `--until STEP` | `oos` (7), `crossmarket` (10), `crosstf` (12), `mcretest` (14), `spp` (16): the project carries no task after that step. `wfm` (19): keeps every task, stops before step 20, repeated on `run` | only when the owner asks for a run that ends there |
| `--mt5-from=` `--mt5-to=` `--mt5-model=` `--mt5-firms=` | step 26, run only when ALL four are given, each one word with `=`: a date `YYYY-MM-DD` (or `MT5` = the oldest every server has), the tester's model (`every_tick`, `ohlc_m1`, `open_prices`, `real_ticks`), the firms (`ftmo,hantec`). `--mt5-real-ticks` adds a second, much slower pass | the owner gives the four each time; without them the run ends before step 26 |
| `--restart` | the old route: SQX starts and stops at every step | only in §6 |

The filters are the owner's: to change what a step keeps he edits `criteria.yaml` (window ›
Configuración). Never edit it to get a run through. Steps 22 to 25 do not exist (deleted
2026-10-11); what each step runs, reads and fills: `.claude/skills/workflow/steps.md`.

## 4. Launch — one command, in the background

1. `.claude/skills/sqx-wait/preflight.sh` — the custodian must be free; with step 26, the
   conductor too and the MT5 terminal closed. Held by someone else: say so and stop.
2. The command of §1 with `run_in_background: true`, and NOTHING until it notifies (hard rule
   18): no polling, no `sleep`, no reading SQX's log, **nothing CPU-heavy beside it** (it doubled
   SQX's task times), and **no edit to `bin/workflow.sh` or `bin/workflow-test.sh`** (bash reads
   a script while it runs it: an edit mid-run broke a run's end on 2026-10-13).
   A run of 1,000 strategies with 10 mothers of 500 variants took 160 min. A known SQX abort
   (fastutil NullPointerException) is rerun once by the autopilot itself.
3. If the owner asks how it goes, ONE line: `tail -1 ~/Desktop/AlgoData/autopilot/<PROJECT>/*/estado.txt`.

## 5. When it notifies

It printed the last status line, the failure (if any) and the path of `resumen.md`. Read
`resumen.md` (one line per step; `tiempos.md` for where the seconds went) and report in Spanish:
per step what ran, seconds, the cut (in → out), and where it stopped. A judge's numbers are in
`paso-<n>/hechos.parquet`; the keys a rule can use: `python3 -m pipeline.autopilot.facts --project P
--step N --grep <text>`. Do not read SQX's log or the run's stdout unless the owner asks.

| last line | meaning | do |
|---|---|---|
| `FIN · …` | complete to where it was asked | report; say if resumen lists «Caídas a la ruta lenta» |
| `FIN · …` and «no dejó ninguna superviviente» | a cut left nobody | report which step: a result, not a failure |
| `FALLO en el paso N: …` | failed | report N and the first lines of `fallo.md`; then §6 |
| `workflow: …` (no status line) | refused before starting | report the sentence as it is; do not work around it |
| `workflow-test: PASA / FALLA` | D's verdict, with its reasons | report it as it is |

A good run of a `Test_` project stops the custodian and retires the project by itself (rule 6).
A failed one, or one with `--until`, keeps it: retire it yourself when it has answered —
`python3 -m sqx.projects.retire <P> --role custodian --yes`, worker stopped.

## 6. After a failure — exactly this, nothing else (never for D)

1. `.claude/skills/sqx-wait/preflight.sh`. Custodian up and its lock is this session's:
   `bin/sqx-worker.sh --role custodian stop`. Someone else's: leave it, report.
2. ONE retry from where it stopped: `bin/workflow.sh run <PROJECT>` (plus `--smoke` and the MT5
   options if the first launch had them), in the background, as in §4.
3. Fails again at the same step: one last try with `bin/workflow.sh run <PROJECT> --restart`.
4. Fails too: stop. Report the step and `fallo.md`. Do not edit code, `criteria.yaml` or the
   project to get past it, and never run a step by hand.

## 7. Failures already seen — recognise them before retrying

One row per failure a real run hit (owner, 2026-10-13: every error is fixed and noted here). A
symptom in this table on code that already carries the fix is a NEW bug: report it, do not retry.

| symptom | cause | fixed in |
|---|---|---|
| step 11.5 «CrossTF_M30 no tiene export: exporta ese databank…» | the live export after step 11 only took the databanks of the tasks preflight chose; the extra-timeframe tasks are created later, by the fill | `0106b60`, `ui/daemon/launch/liverun.py` |
| `bin/workflow.sh`: «opción desconocida: --mt5-from» | the script did not pass step 26's parameters on | `5a9f30c`: the four go through, one word each with `=` |
| «el paso 26 no se lanza: el log de hoy de SQX_w1 se escribió hace N min (< 15)» | step 26's pre-check read the conductor's log, just written by the run's own exports, as someone else's | `5a9f30c`: the autopilot says the log is its own; lock, open port and live process still refuse |
| `bin/workflow.sh: line N: syntax error` right after the autopilot's `FIN`; the `Test_` project not retired | the script was edited while it ran | not a code bug: §4.2. Stop the custodian and retire the project by hand |
| refusal «los databanks no terminaron de cargar en 5 min; sesión matada por PID, ficheros intactos» | an earlier `stop` killed SQX mid-save and left a truncated `.sqx` | do not retry; report (`knowhow/sqx-drive/stop-killed-mid-save-truncated-sqx.md`) |
| resumen: «Caídas a la ruta lenta: …CrossTF_Input: una identidad no coincide» | the identity counted the `<!--variant_id:…-->` comment Python stamps on the scaled siblings and SQX drops on load | 2026-10-13, `ui/daemon/launch/liverun.py`: the filled bank is synced (SQX rewrites it) before the dump |
| step 26: «PermissionError: ledger: el paso 26 no puede mirar `oos2` de <SYMBOL>: está reservado para…» | the autopilot is an autonomous agent and step 26 is not in `reserved_for` of `assets/_policy.yaml`: a window that touches the asset's oos2 is refused | not a code bug, the owner's policy: report it, never edit the policy. The refusal now comes before the backtests (`mt5/verify/run.py`), and D's window lies in oos1 |
| resumen: «Caídas a la ruta lenta: …CrossTF_Input: …_ScaledH4: el .abk lleva 0 operaciones…, el .sqx 301» | Python fills `CrossTF_Input` and no task backtests it there: a scaled sibling's `.sqx` carries its mother's stored result, SQX's memory none; and no step reads that bank's trades | 2026-10-13, `ui/daemon/loader/afterrun.py`: `CrossTF_Input` is in `UNREAD_TRADES`, its trades are not exported |
| step 8 «OSError: List index overflow» (pyarrow) on a 10,000-strategy build | `distribuciones.parquet` written as one row group with > 2**31 list elements; `facts.from_folder` read it whole | 2026-10-15: `core/study/draws.py` writes 1,000-row groups; `pipeline/autopilot/facts.py` reads a parquet's `strategy` column first (`knowhow/pipeline/distributions-parquet-list-overflow.md`) |
| «FALLO en el arranque de la sesión GUI: [Errno 2] No such file or directory: …/log_<ayer>.log», the custodian left up half-loaded | the first start after midnight listed yesterday's SQX log as the newest and SQX deleted it while starting, before its `stat` | 2026-10-17, `sqx/projects/live.py` (`mark`, `wait`, `tail`) and `sqx/log.py` skip a log that vanished |

## Never

- Run workflow steps by hand, or call SQX directly: this command is the only way (rule 19).
- Use the master install, `pkill`, or a project that is not the one named here.
- Leave a `Test_` project behind (rule 6). A `Trade_` or `Research_` project is never retired here.
- Change `pipeline/autopilot/criteria.yaml`. Its rules are the owner's.
- Guess a missing argument. Ask (rule 11).
- Count as proof a run that was continued or fixed on the way.
