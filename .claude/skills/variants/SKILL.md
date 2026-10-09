---
name: variants
description: Run the variant factory in SQX — turn one mother's SPP design brief into a batch of parameter variants, load and retest them on the custodian, and harvest the metrics panel, the per-day equity and every variant's trades that the WFC, the parameter cloud and the CSCV read. Use when the owner asks to fabricate, run or retest variants, to prepare the walk-forward correlation, or about step 16.5 of the workflow.
---

# /variants

Step 16.5 of the workflow: **from one design to a measured population of variants**. The autopilot
(`pipeline/autopilot/variants.py`) runs it per mother: `make` → `execute` → `equity` → `collect` →
`export_retest --batch variants` → `varianttrades` → `execute --clear`, then the mothers' trades
(`mothertrades`) and, with SQX idle, **the parameter cloud** (`studies.optimisation.cloud.report`)
for every batch. What comes out is what the WFC (step 17), the cloud and the CSCV (step 18) read.
Step 16.5 **cuts nothing** (`criteria.yaml` `"16.5"`: `cut: null`, `rules: []`).

**The batch is a Latin hypercube** (encargo 48 F, owner 2026-10-07): one hypercube over the live
parameters inside the SPP IS plateau (`from`..`to`; frozen and shifted ones stay at the mother's value in
every variant), `n = min(n_max, max(n_min, 8 × p))` with `p = 1 + 2k + k(k-1)/2` (ledger rows
`variants.*`; 1,000..5,000). `stratum` is `lhs`, `origin`, `canary` or `inert`. The old three strata
and `n_target`/`strata`/`minimum` no longer exist for the factory. → `sqx/variants/design/README.md`

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
market and the unions. From there come the WFC's three compositions (`c1` build+oos1 → oos2, `c2`
build → oos1+oos2, `c3` build → oos2) without running anything again.

**Every variant's trades are exported too** (`variant_trades.parquet`, schema T plus `variant_id`,
`leg`, `market`): the WFC and the cloud price each variant's own trades as step 14's excess
(`engines/variants/excess.py`). It reverts the old «only the mother's trades» choice and costs about
90 min per batch (reference run); `mothertrades.py` still serves step 20's curve of the mother.

## No floor at harvest

`collect.py` **drops no variant for trading little** (encargo 48 F; `usable` stays all true except
without data, so `marketSurfaces` is not broken). Each study applies its own floors, counted per
filter in its report: the WFC and the cloud take `15 × k` trades inside and, the WFC, `10` per year
outside (`engines/variants/filters.py`; a mother under a floor warns and the floor is skipped).
When reporting, say how many fell at each filter.

## The commands

```bash
python3 -m sqx.variants.make --brief <design_brief_<Strategy>.json> --project <PROJECT> \
    [--out <work>] [--sample N | --limit N] [--design-only] [--no-pilot]
python3 -m sqx.variants.execute --work <work> --project <PROJECT>   # ⏰ the only one that holds the custodian
python3 -m sqx.variants.equity   --work <work>    # before collect: collect reads equity.parquet
python3 -m sqx.variants.collect  --work <work>
python3 -m sqx.export.export_retest --project <P> --role custodian --batch variants --databank <leg 1> --databank <leg 2> --databank <leg 3>   # SQX up
python3 -m sqx.variants.varianttrades --work <work> --project <P>   # exports -> variant_trades.parquet
python3 -m studies.optimisation.cloud.report --work <work>          # the map; reads build and oos1 only
```

`execute` waits on the run itself (it polls `-project action=status`): launch it with
`run_in_background: true` and do nothing until it exits (rule 18) — no `wait.sh`, no polling loop.

| command | what it leaves | touches SQX |
|---|---|---|
| `make` | `plan.csv`, `design.json`, `sqx/` with the N variants, `manifest.parquet`, `pilot.json` | **the pilot, yes** (by default) |
| `execute` | `retest.csv`, `ran.json`, the databank dumped to disk | **yes** |
| `equity` | `equity.parquet` — each variant's P&L **per day** | no |
| `collect` | `metrics.parquet` — the panel joined to the manifest | no |
| `export_retest` + `varianttrades` | `variant_trades.parquet`, the three legs' exports deleted | **the export, yes** |
| `cloud.report` | `estudios/cloud.{json,html,md}`: adjusted R², its shuffled reference, Sobol indices | no |

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

**The variant space**: the live parameters inside the SPP IS plateau (never outside it), the shifted
ones fixed. If the hypercube cannot give `n` distinct tuples after rounding, `make` prints the
shortfall and `design.json` carries `capped`/`shortfall`: tell the owner before running.

`--sample N` fabricates N rows **spread** over the whole plan (the controls and then spaced picks);
`--limit N` takes the first N. For a smoke test, `--sample`.

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
- `equity`: 962 variants in 1.5 s and 5.9 MB of Parquet (the curves; the trades export is the ~90
  minutes). If `equity` takes much longer, it is reading what it should not.
- `cloud.report`: the line «Sin estructura distinguible del ruido» means the Sobol ranking must not
  be read (adjusted R² under its shuffled reference). It is a map, not a verdict.

## Step 17, which reads this batch (the WFC)

`python3 -m studies.optimisation.wfc.report --work <work> --family <F>`: three compositions, one
`estudios/wfc.*`; `facts.c1.estado` ∈ `pasa` / `limbo` / `no_pasa`, judged by the pilot with **no
cut** (`cut: null`: it notes, never deletes). **oos2 is sealed**: `ledger.gate.seal` refuses it until
`python3 -m studies.optimisation.wfc.calibrate` has written `AlgoData/ledger/wfc_calibration.json`
with `abre: true` for the current `criteria.yaml` entry. Today it says `abre: false` (the owner
chooses the level's null, `AlgoData/ledger/wfc_calibration.md`), so step 17 stops at the seal: say so,
do not edit the criteria or the record. Step 20 translates the state (PASA = no failure, NO PASA =
failure, LIMBO = undecided). → `studies/optimisation/wfc/README.md`

Manual: `docs/manual/09-optimizacion.pdf` (cap. 18-variantes) (fabricating), (cap. 19-wfc) (running,
collecting and step 17), (cap. 39-nube-de-parametros) and (cap. 107, the calibration). The chainer of the
~100 mothers is `docs/manual/04-sqx-plantillas-y-proyectos.pdf` (cap. 17-pipeline).
