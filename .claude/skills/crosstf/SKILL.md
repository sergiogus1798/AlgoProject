---
name: crosstf
description: Test whether a strategy's edge survives being read on a slower timeframe — fabricate period-rescaled siblings, wire a cross-timeframe check into a custom project, run it on the custodian, and read each cell against its own timeframe's null. Use when the owner asks to test a strategy on another timeframe, to run the cross-timeframe or crossTF check, whether an H1 strategy also works on H4, or to scale a strategy's parameters to a different timeframe.
---

# /crosstf

The sibling of `/crossmarket`, one axis over. `/crossmarket` changes the market and keeps the clock;
this changes the clock and keeps the market.

## The one thing to understand before running it

**H1 and H4 are the same price series, resampled.** An H4 bar is made of the same four H1 bars, so
"it also works on H4" is far weaker evidence than "it also works on EURUSD" — you are not getting a
fresh test, you are getting a smoothed version of the same one. That is why every cell is judged
against **its own timeframe's entry-timing null** and never against "is it profitable". A profitable
H4 cell that does not beat its null is *inheriting* the H1 edge, and the verdict says so.

Consequence: this is a **score, not a gate**, and it belongs at the end of the funnel — on survivors
that already passed `/oos-gate`, never on a freshly built population.

## The two rows are two different questions

| row | what is done to the strategy | what a failure means |
|---|---|---|
| **scaled** | periods divided by the ratio (a 20-hour average stays 20 hours) | evidence against the strategy |
| **unscaled** | left alone (a 20-bar average becomes 80 hours) | **nothing about the strategy** — that asks whether the market is self-similar |

Never grade the unscaled row. Report it, say what it is, and move on.

## The control cell is shown, not read (proposal of 2026-10-02, pending the owner)

Each scaled sibling is run **on its own source timeframe too**, and that number sits beside the
reading. It was a reading of its own (`control_failed`) until 2026-10-02: it took 29 of 46 real
siblings and inverted for a negative baseline — periods ÷ 4 on the mother's bars is another
strategy, not a rounding check. What prices the sibling now is `z_new`: its z with what its
mother's result already explains taken out (a sibling re-reads the same asset over the same years).

## Run it — from the window (the usual path)

Since 2026-09-29 the window does steps 10.5 and 11 in one press: ▶ SQX of step 11 (or «Correr
workflow», or «Continuar workflow» on the Cross Market databank) runs
`sqx.projects.crosstfload` with the worker **stopped** — the Cross Market survivors on disk are
scaled to `crosstf.timeframes`, copied with the mothers into `CrossTF_Input` (emptied first), the
`CrossTF` task is rewritten with the same blocks — then starts the worker, runs `CrossTF`, stops.
Before step 13 the same module copies the mothers `CrossTF` kept (no `_Scaled*` sibling) into
`CrossTF_Mothers`, which the eight MC Retest tasks of a `--workflow` project read. The permanent
order is Cross Market → Cross TF → MC Retest (owner, 2026-09-29). By hand:

```bash
python3 -m core.assets <SYMBOL>                                            # hard rule 5
python3 -m sqx.projects.crosstfload --project <P> --role custodian          # 10.5, worker stopped
python3 -m sqx.projects.crosstfload --project <P> --role custodian --mothers  # before 13
```

`CrossTF_Input` is written by **no task** — `knowhow/sqx-drive/crosstf-input-filled-by-no-task.md`.

## Run it — step by step

**1 · Fabricate.** Owner's rule, 2026-09-23: **periods and bar-count exits, nothing else.** Since
2026-10-02 a period is what SQX types `ParamTypePeriod` on the variable (MACD's three, the
Stochastic's slowing…), a custom block's length is what `sqx/variants/lengths.yaml` rules, and the
name patterns of `sqx/variants/config.yaml` are only a fallback. A custom block the table does not
rule is left unscaled and its sibling comes back `unusable`.

```bash
python3 -m sqx.variants.scale --mothers <dir de .sqx> --project <P> --source H1   # M30 + H4 + D1
```

**The batch has a declared home** (hard rule 7 — heavy data never in the repo):
`AlgoData/crosstf/<project>/<date>/`, from `core.datapaths.crosstf_dir`. Dated and immutable,
because a verdict is only readable against the exact scaling that produced it.

**Its `sqx/` subfolder IS the databank load.** The mothers are copied in beside the siblings,
verbatim, because the study needs their baseline and control cells too — so step 3 loads one
folder and not two, and nothing has to be assembled by hand. `scaling.parquet` sits one level up
(since 2026-09-27): SQX loads every file of the folder it is given and logged an error for it.

```
AlgoData/crosstf/XAUUSD/2026-09-23/
  sqx/Strategy 10.13.25.sqx         <- mother, untouched
  sqx/Strategy 10.13.25_ScaledH4.sqx <- sibling
  ...
  scaling.parquet                   <- the only record of what was divided and how far
                                       rounding moved it; step 4 reads it
```

The two columns it prints, `clamped` and `max_rounding_shift`, are recorded and shown, and since
2026-10-02 they no longer discard a sibling (owner: «Redondea donde puedas, ya está»): each
length is rounded to the nearest integer, floor 2, and the sibling is read like any other. It also lists the int parameters the whitelist did not claim — review
them, do not assume they are wrong.

⚠️ **D1 is not reachable from H1 by scaling.** Measured: ÷24 moves parameters 140–586 % and clamps
every period at the builder's floor. The doctrine still lists D1 from H1 (owner, 2026-09-29); the
criteria calibration of 2026-10-02 runs without it (`crosstfload --targets M30 H4`). **A faster target is fine**: H1→M30 doubles the
periods, no clamp (→ `knowhow/sqx-drive/crosstf-input-filled-by-no-task.md`).

⚠️ **Short lengths hit the floor, and the sibling is read all the same** (owner, 2026-10-02). A
Stochastic's D and slowing of 3 divided by 4 are written as 2, the floor. 🔬 on 600 Simple
Strategies: 23 % of H1→H4 siblings and 53 % of M30→H4 ones carry a clamped length. Say the
`clamped` share and the rounding shift when reporting; do not drop those siblings.

**2 · Wire the task.** It lives in the workflow's own project (`/template-run --workflow`), in the
task titled `CrossTF`, which reads `CrossTF_Input` and writes `CrossTF`:

```bash
python3 -m core.assets <SYMBOL>                           # hard rule 5, blocking
python3 -m sqx.projects.crosstf <SYMBOL> --cfx <install>/user/projects/<P>/project.cfx
                                         # --timeframes H4 D1 overrides the doctrine's list
```

The timeframes, the window and the precision come from `crosstf:` in `assets/_build.yaml`
(`segment: oos1`, `precision: 1` — owner, 2026-10-02: the step reads oos1 only, at the selected
timeframe's precision). The timeframes depend on the one the strategy was built
on: **from M30, H1 and H4** (owner, 2026-09-26); **from H1, M30, H4 and D1** (owner, 2026-09-29).
H12 is a custom SQX timeframe and works as-is in a task if named (→ `knowhow/sqx-drive/custom-timeframe-h12.md`).
`sqx.variants.scale --source H1` fabricates every sibling of the list by default. The study derives the same block order itself — the siblings'
`source_tf` in `scaling.parquet`, then this list (2026-09-27; it used to be a hand-edited
`run.blocks`). D1 (or H12) siblings of short
periods come back `clamped` — they are read only as the unscaled row. `--timeframes` overrides the list for
a one-off — then, and only then, the command prints the `--set run.blocks=[…]` the study needs;
the window and the precision are not overridable on purpose.

Each `<Setup>` overrides **only** `timeframe`; the window, costs, precision and session all come from
the main test through `<MainTestValues>` — the same instrument does not get a different spread for
being resampled. Because the extra blocks inherit the main test's dates, the command **writes the
task's own window as `crosstf.segment`** — `oos1` since 2026-10-02, `build..oos1` before.

It **silences every acceptance condition** of the cross-check and forces `DeleteFailedStrategies`
to false, and says how many — `crosstf.conditions: []` (owner, 2026-09-24): with them live SQX drops
the failing strategy and Python never sees the dead ones
(`knowhow/conditions/crossmarket-crosstf-no-conditions.md`). It leaves `CrossTF` the only active
task, refuses while the install is up (hard rule 4), and ends by printing the block order.

**3 · Load, run and export.** On the custodian, stopped: `crosstfload` copies the folder into
`CrossTF_Input` (SQX loads it when it starts — never `-databank action=load` on a running
custodian), then the run half of `/template-run` — `start` and the wait — mark, `action=start`, ONE
background `wait.sh --from`, nothing until it notifies (rule 18; `-project action=status` is the only
query the custodian takes meanwhile) — always end stopped:

```bash
# with the custodian STOPPED, copy the folder into the databank; SQX loads it on start
python3 -m sqx.projects.crosstfload --project <P> --role custodian
python3 -m sqx.export.export_retest --project <P> --databank CrossTF --role custodian
```

**4 · Read.**

```bash
python3 -m studies.transfer.crossTF.report --project <P> --asset <SYMBOL> [--day <export>] [--fabricated <scale day>]
```

Six readings, on oos1 only (an agent's proposal of 2026-10-02, pending the owner — the study's
README): `survives` (beats its own timeframe's null AND adds to what its mother already showed,
`z_new`), `inherited` (made money, no more than its mother predicts), `fails` (lost money), and
three that mean the test did not happen: `unusable` (ONLY an unverified custom-block length —
owner, 2026-10-02, «Redondea donde puedas, ya está»: rounding and the floor never discard a
sibling; `rounding_shift` and `clamped` are numbers to measure with), `silent` (no trade),
`no_data` (under 30 oos1 trades). The control cell is
shown, never read. `--seed N` replays the nulls.

## The trap that is silent

The block order must match the `<Setup>` order of the task. Wrong, and every cell is priced on the
wrong bars with no error anywhere — `report.py` prints the mapping for that reason. It is derived,
so only a task written with `--timeframes` can break it. The blocks are separated by the ticket restarting at 1, **not** by
the `Symbol` column, which is identical across the timeframes of one asset.

## Say this when reporting

- **The H4 stop is physically about twice as wide in price than the H1 one.** Only periods and bar
  exits are scaled, so `StopLossCoef` and `ProfitTargetCoef` are written through unchanged while the
  range they multiply grows with aggregation. Declared property of the comparison, not a bug — but
  never describe an H4 cell as a clean "same strategy, slower clock".
- The share of siblings with a clamped length and their rounding shift, as a description: they are
  read like any other (owner, 2026-10-02), and whether they behave differently is a thing to measure.
- That the result is correlated with what the OOS gate already knew, and is worth less per CPU-hour
  than another market.

## Do not

- Grade the unscaled row, or report it as robustness evidence.
- Discard a sibling for rounding or for hitting the floor (owner, 2026-10-02) — only an unverified
  custom-block length makes one `unusable`.
- Run it with the cross-check's acceptance conditions live.
- Build D1-scaled siblings and read them as scaled.
- Run it on the master, or on a stock project.
