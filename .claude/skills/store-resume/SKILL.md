---
name: store-resume
description: Bring strategies back from the strategy store into StrategyQuant and carry on their workflow from step 13 (MC Retest) — recreates the retired project under its own name, loads the chosen stored .sqx into its databanks and hands it to the one workflow command. Use when the owner wants to continue a run that was cut or retired after step 12, to run the later tests (13-20) on saved strategies, or says «reanuda», «sigue con las guardadas», «pásalas por el resto del workflow», «cárgalas en SQX».
---

# /store-resume

The store keeps each gate survivor's `.sqx`; the project it came from is usually retired. This
puts the project back as the rail expects it — its own name, so its reports of steps 8-12 are
found; the strategies in the output databank of every step already done — and nothing else: the
run itself is `bin/workflow.sh run` (hard rule 19).

1. **Which strategies, which project.** `python3 -m core.store list | grep '<cell or project>'`.
   Every strategy must come from the SAME project; the owner says which ones (rule 11) — «todas»,
   a list of names, or «N al azar» (then draw with `random.Random(<seed>).sample(sorted(ids), N)`
   and report the seed).
2. **Smoke or real?** Ask if not said (rule 11): `--smoke` (Test_ only) lets every strategy
   through every step — a test of the chain; without it steps 14 and 16 cut by `criteria.yaml`.
3. **Free worker.** `.claude/skills/sqx-wait/preflight.sh`: the custodian down, no lock, nobody
   else's run in the day's log.
4. **Resume.** `python3 -m pipeline.autopilot.resume <PROJECT> <identity or name>...`
   - It runs `core.assets <SYMBOL>` (rule 5: report the overrides it prints), builds the full
     task chain from the project's registry row, fills the databanks and asks the rail.
   - `listo: bin/workflow.sh run <PROJECT>` → go on.
   - `el raíl dice que … está en el paso N, no en el 13` → stop and report; do not launch.
   - `figura vivo` → the project is still on a worker: `bin/workflow.sh run` directly.
   - `nombra 0|2 estrategias`, `no está entera`, `salió de <otro>` → report as printed.
5. **Run**, one background command (rule 18): `bin/workflow.sh run <PROJECT> [--smoke]`,
   `run_in_background`, and do nothing until it notifies. Some 75 min for 3 strategies; nothing
   CPU-heavy beside it.
6. **When it ends:** read the printed `resumen.md`; then `/store-save` (save + verify + audit).
   The project is a `Test_`: retire it once saved (`/store-save` step 5).

Only step 13 is a resume point: strategies cut earlier have no stored input for the step they
would start at. A fresh idea is `/workflow-template` or `/workflow-simple`, not this.
