---
name: wfm
description: Configure and run the Walk Forward Matrix task of a custom SQX project — the 30-cell grid over a window that ends in oos2, and the ten per-cell conditions and the area rule that decide whether a strategy survives. Use when the owner asks to set up, configure or run the WFM or walk-forward matrix in SQX, or step 19 of the workflow.
---

# /wfm

Step 19 of the workflow, and **the last step that looks at data**. It leaves the `WFM` task of a
custom project configured and ready to run. Reading it is `studies/optimisation/wfm/`, when wanted.

## It ends in `oos2`

The window is `build..oos2` — the walk-forward needs history in front to optimise. On 2026-09-28 the
owner repealed the «do not burn oos2» rule for humans: it is run and read whenever he wants, without
waiting for 17 and 18 to be done. Only an autonomous agent (`ALGO_AUTONOMOUS=1`) is still bound to the
reserve in `assets/_policy.yaml` and to step 20's blind door (`ledger/gate.py`).

## What it writes

30 cells: 5 out-of-sample percentages (20→40 in steps of 5) × 6 numbers of runs (6→16 in steps of 2),
`MaxTests` 5,000 per step, ±35 % in steps of 4 % (`maxSteps=18`), only the parameters **recommended**
by SQX, precision 2, fidelity `exact_is_exact_oos` — the GUI's "Walk-Forward type": each step does
its own real optimisation over its window, not a cut — and the window `build..oos2` both in the
`<Setup>` and in `<Resources><Symbol>`.

The split between the two knobs is deliberate (owner, 2026-09-24): `MaxTests` went down from 15,000 to
5,000 because it buys a better choice per step and nothing readable afterwards, whereas `wf_type`
changes what the number that is stored means.

⚠️ **It is charged at `oos1`'s costs, not the last segment's** (`wfm.costs_segment`, owner's decision
2026-09-24): it is 18.7 years of which `oos2` is the 3.7 tail. It is the exception to the spans'
convention, and the command announces it in its output. Today `oos1` and `oos2` share spread, so the
number does not change.

And the criterion, which is what the master's task lacked: **ten conditions per cell**, a cell passes
with 80 % of them met, and the strategy passes if there is a 4x4-cell rectangle with 12 passing. They
are in `assets/_build.yaml`, `wfm.conditions`, with the % of the master's 150 real cells that meets
each threshold next to them; the dissection of SQX's formulas is in
`knowhow/conditions/wfm-acceptance.md`.

**The criterion flags, it does not delete** (🔬 2026-09-26, owner). With `DeleteFailedStrategies=false`
— the command forces it — a strategy that does not find the 12-cell area stays in the databank with
`FiltersResultFailedReason = "Cross Check filter in 'Walk-Forward Matrix': Robustness score
didn't pass."`. `export_wfm` saves it in `status.parquet` and in the manifest (`failed_in_sqx`), and
the analysis puts it as a `failed_en_sqx` warning on the strategy's sheet. The verdict stays Python's.
Do not use map mode (`min_squares: 0`) unless the owner asks.

Count the bill before launching: 5,000 backtests per step × 6–16 steps per cell × 30 cells × strategy,
at precision 2. The master's WFM finished with 500 over five years.

## Run it

```bash
python3 -m core.assets <SYMBOL>                        # preflight, BLOCKING
python3 -m sqx.projects.wfm <SYMBOL> \
    --cfx <install>/user/projects/<PROJECT>/project.cfx --input <databank>
```

`--input` is the survivors that reached step 19 and has no default.

The project must carry the task titled `WFM`, which comes from the frozen donor: if it does not, the
command refuses instead of fabricating it — the block and its conditions come from a task that SQX
wrote. And the `.cfx` cannot be open in an instance (hard rule 4).

Then, on the custodian, one thing at a time, and warning before touching W2 (`ListAgents`,
`ls -lt user/projects`, the log — the `stop` kills any session's work):

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

## What to look at in the output

- **The dates.** They must be `oos2`'s (in XAUUSD, 2023.01.01 → the `to` of `oos2` in `_policy.yaml`,
  which advances by itself every first Saturday of the month). If 2018–2022 appears, the task is
  re-reading the spent sample and is out-of-sample of nothing.
- **`30 celdas`.** Any other number means someone touched the axes in `_build.yaml`: not an error, a
  different study.
- **`13 del donante apagadas y 10 propias escritas`** — the 13 is normal in a clone of the donor and a
  0 warns that the `.cfx` does not come from it. If the second number is not that of
  `wfm.conditions`, the matrix judges with something else.
- **`queda marcada FAILED en SQX, NO se borra`** — normal. If a strategy is ever missing from the
  output databank, `DeleteFailedStrategies` was not `false`.
- **`⚠️ esta tarea corre ademas: …`** — that `.cfx` did not go through the doctrine and would run other
  crosschecks at the same time, each with its bill.

⚠️ The whole window is 18.7 years in XAUUSD, of which `oos2` is the 3.7 tail. With 16 runs each
out-of-sample segment is about a year; with 6, three and a half years. Look at it before reading a
per-cell correlation. On an asset with `oos2: {from: null}` there is no window and the command blows
up, which is correct.

## Where each thing is changed

| what | where |
|---|---|
| the two axes, `MaxTests`, ±% and the step, precision, the window | `assets/_build.yaml`, `wfm:` block |
| the walk-forward's fidelity (`type`) | `assets/_build.yaml`, `wfm.wf_type` |
| the per-cell criterion and the area it must find | `assets/_build.yaml`, `wfm.conditions`, `threshold_pct`, `grid_passing_size`, `min_squares` |
| which segment is `oos2` on each asset | `assets/_policy.yaml`, `segments:` |
| the `WFM` title | **contract** with the donor and with `export_wfm` |

Export from a worker: `python3 -m sqx.export.export_wfm --project <P> --databank WFM --role custodian`.

Measured 2026-09-25 on 3 USDJPY H1 mothers (`knowhow/sqx-drive/wfm-end-to-end.md`): the matrix, ~4-5
min per mother and a 45 GB JVM; export 20 s; analysis 2 s. **SQX gives no progress signal** while it
runs: `Running time 0 ms` and the databank still until each mother finishes.

Manual: `docs/manual/09-optimizacion.pdf` (cap. 34-wfm). Exporting: `docs/manual/09-optimizacion.pdf`
(cap. 09-wfm). Reading it: `docs/manual/09-optimizacion.pdf` (cap. 14-walkforwardmatrix).
