---
name: variants
description: Run the variant factory in SQX — turn one mother's SPP design brief into a batch of parameter variants, load and retest them on the custodian, and harvest the metrics panel and the per-day equity the WFC and the CSCV read. Use when the owner asks to fabricate, run or retest variants, to prepare the walk-forward correlation, or about step 16.5 of the workflow.
---

# /variants

Step 16.5 of the workflow: **from one design to a measured population of variants**. Four commands
in order, three of them without touching SQX and one that holds the custodian for hours. What comes
out of here is what the WFC (step 17) and the CSCV (step 18) read — and those two are not looked at
until step 19 is done too.

## Why it exists

**No `sqcli` verb changes a strategy's parameters.** None. The only way to score a combination is to
write a `.sqx` with that value inside and retest that file. That is the factory. → `knowhow/sqx-drive/variant-route.md`

And it is needed because the two SPPs of step 15 **cannot be paired**: they share 6 tuples out of
~11,600. To have the same combination measured in-sample and out-of-sample it has to be fabricated.

## Which project it runs in: the workflow's

Owner, 2026-09-25: the whole workflow lives in **one** custom project, the one `/template-run`
created with `--workflow`. It already carries the three legs of the retest that feeds the WFC and the
CSCV — `WFC 1 IS`, `WFC 2 OOS1`, `WFC 3 OOS2`, one per segment, each at its own spread and slippage
and with the additional markets inside — reading the three `WFC_Variants` (**no spaces**: the API
cannot name a databank that has them). The doctrine is in `wfc:` of `assets/_build.yaml`:

```bash
python3 -m sqx.projects.wfc <SYMBOL> --cfx <install>/user/projects/<PROJECT>/project.cfx \
    --timeframe <TF>
```

It finds the three by their title, switches off all their conditions (with the OOS one the donor
brings in `build`, that segment used to come back without the markets and without warning) and
leaves them **as the only active ones**. `execute` requires `--project` and refuses a stock project
(hard rule 10) or one with anything else active than those three. Manual:
`docs/manual/09-optimizacion.pdf` (cap. 37-wfc-retest).

A project made only for this (`Test_<SYM>_variantes`, cloned with `--tasks Retest`) is still valid:
`wfc` with `--tasks <three files>` in the order build, oos1, oos2.

⚠️ **Between one mother and the next, empty the four databanks** — `clear` and `synctofiles` on each,
then stop — **after** `equity` and `collect`: the curves are read from the custodian's disk.
→ `knowhow/sqx-drive/variant-chain-custom-project.md`. **The harvest now reads the three databanks**:
`execute.py` exports one panel per segment, `equity.py` joins the three segments' daily curves (and
keeps each additional market's apart) and `collect.py` leaves in C3 the metrics per segment, per
market and the unions. From there come the two WFC readings — `build` vs `oos1+oos2`, and the strict
`build+oos1` vs `oos2` — without running anything again.

## The hard floor: 50 trades

`wfc.min_trades_total` in `assets/_build.yaml` (owner, 2026-09-24). A backtest with fewer than 50
trades summing `build`+`oos1`+`oos2` **enters no statistic**: `collect.py` does not write it to
`metrics.parquet`. It is counted per variant **and per market**, the full evidence stays in
`segments.parquet` with `usable=False`, and the count is announced on screen and in `collected.json`.
When reporting, say how many fell: a batch where half does not reach the floor is not a batch with
fewer points, it is a design that fabricated variants that do not trade.

Not to be confused with `min_trades: 30` in the WFC's `config.yaml`, which looks at each side of the
partition separately and acts afterwards.

## The four commands

```bash
python3 -m sqx.variants.make --brief <design_brief_<Strategy>.json> --project <PROJECT> \
    [--out <work>] [--sample N | --limit N] [--design-only] [--no-pilot]
python3 -m sqx.variants.execute --work <work> --project <PROJECT>   # ⏰ the only one that holds the custodian
python3 -m sqx.variants.equity   --work <work>    # before collect: collect reads equity.parquet
python3 -m sqx.variants.collect  --work <work>
```

`execute` waits on the run itself (it polls `-project action=status`): launch it with
`run_in_background: true` and do nothing until it exits (rule 18) — no `wait.sh`, no polling loop.

| command | what it leaves | touches SQX |
|---|---|---|
| `make` | `plan.csv`, `design.json`, `sqx/` with the N variants, `manifest.parquet`, `pilot.json` | **the pilot, yes** (by default) |
| `execute` | `retest.csv`, `ran.json`, the databank dumped to disk | **yes** |
| `equity` | `equity.parquet` — each variant's P&L **per day** | no |
| `collect` | `metrics.parquet` — the panel joined to the manifest | no |

## The pilot, before fabricating the whole batch (OPEN.md #41, owner 2026-09-29)

Measured 2026-09-24 on `Strategy 17.9.39`: **1,002 of 2,000 rows traded fewer than 30 times
in-sample** — half the budget went on combinations that are not a point of a surface. `make` now
first fabricates and retests a few hundred sample tuples (Sobol, only the parameters that move) in
the SAME `--project`, counts their trades and drops the levels of a parameter whose pilot traded
below `pilot.min_trades` (30 by default) — never a whole parameter, and never the origin's value.
The big batch is then fabricated without those regions.

**ON by default** (`pilot.enabled` in `sqx/variants/config.yaml`). `--no-pilot` skips it for a quick
test; `--design-only` never runs it (it fabricates nothing). It is the only time `make` touches SQX:
a short retest, with the same `awake`/`load`/`run`/`synced` of `execute.py`, on the same project and
at the same per-task costs — it creates and needs no project of its own.

**It is never silent.** `pilot.json` (next to the batch) carries, per parameter and level, the
pilot's median trades, how many points support it and whether it was dropped; `design.json` carries
the same cut in `pilot_dropped`. A batch fabricated with the pilot and one without it should never be
compared as if they were the same design — look at `pilot_dropped` before reading a surface.

**The variant space** (owner, 2026-09-26): every parameter covers at least ±30 %, integers with all
their values, the *shift* ones fixed, and each mother has **at least 1,000 distinct variants**
(`--min-variants`, `minimum:` in `sqx/variants/config.yaml`) — if they do not fit in ±30 %, the
integers are widened to ±60 %. If `make` prints `⚠️ only N distinct tuples`, tell the owner before
running.

`--sample N` fabricates N rows **spread** over the whole plan (the controls and then spaced picks from
each stratum); `--limit N` takes the first N and biases the batch toward one stratum. For a smoke
test, `--sample`.

The brief comes from step 16: `studies/breakage/spp/report.py`. If its verdict is `noise`, the family
is indistinguishable from chance and fabricating variants of it is measuring noise — the command does
not prevent it, it shows it on the first line. Tell the owner before spending the afternoon.

## The three contracts, and why there are three

**design** decides and writes no file. **build** writes and decides nothing. **manifest** reads the
files back from disk and describes what **is there**, not what was meant to be there. That third
boundary is the only thing that detects a file whose content is not the tuple that named it, and
that failure is silent in any other setup.

## The batch's five controls

They are there to fail, not to be analysed: `P00000` (the origin re-fabricated), three canaries with
a known result taken at the **extremes** of the SPP grid, and an inert pair per frozen parameter. If
`collect` says all the controls returned the same number, the chain is broken and it stops there. A
canary at the extreme betrays a broken chain; one from the middle returns a plausible number.

⚠️ A canary's expectation is about the **in-sample** result and is only valid while the retest's IS
window is the one the SPP ran.

## The measured traps

- **A retested `.sqx` carries THREE equity curves** — `Portfolio`, `Main:` and one per cross
  market — and `Portfolio` comes first in the file. Reading the first gives gold plus silver.
  `equity.py` calls them by name, never by position. → `knowhow/sqx-format/daily-equity-bin.md`
- **`synctofiles` writes late**: 962 of 2,000 were on disk when the retest said it had finished.
  `execute` waits, but the cap is `sync_tries` in the config. → `knowhow/sqx-drive/variant-route.md`
- **`-project action=startOnlyTask` says yes and tests nothing** on this install. Only
  `action=start` runs the task.
- **Never leave the worker up**: a sync deletes the `.sqx` it does not hold in memory (hard rule 1).
  `execute` stops it if it was the one that started it.
- Before touching W2: `ListAgents`, `ls -lt user/projects` and the log. The `stop` kills anyone's work.

## What to look at

- `make`: `planned N of a target M` with the shortfall. A big gap is not a failure — a tuple is
  never repeated to reach the target.
- `execute`: `n_loaded` against `n_returned` against `n_on_disk` in `ran.json`. If they drop, people
  are missing.
- `collect`: the controls. If they fail, do not go on.
- `equity`: 962 variants in 1.5 s and 5.9 MB of Parquet — against ~90 minutes if their trades were
  exported. If it takes much longer, it is reading what it should not.

Manual: `docs/manual/09-optimizacion.pdf` (cap. 18-variantes) (fabricating) and
`docs/manual/09-optimizacion.pdf` (cap. 19-wfc) (running, collecting and step 17). The chainer of the
~100 mothers is `docs/manual/04-sqx-plantillas-y-proyectos.pdf` (cap. 17-pipeline).
