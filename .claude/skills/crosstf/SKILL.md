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

## Why there is a control cell, and why it is not optional

Each scaled sibling is run **on its own source timeframe too**. Without that cell, "it died on H4"
and "it died when its Tenkan went from 9 to 2" are the same observation. `control_failed` is that
separation; if you drop the control, every verdict becomes unattributable.

## Run it

**1 · Fabricate.** Owner's rule, 2026-09-23: **periods and bar-count exits, nothing else.** The
whitelist in `sqx/variants/config.yaml` (`crosstf:`) is positive — an unrecognised parameter is
written through untouched, never reinterpreted.

```bash
python3 -m sqx.variants.scale --mothers <dir de .sqx> --project <P> --source H1   # H4 + H12
```

**The batch has a declared home** (hard rule 7 — heavy data never in the repo):
`AlgoData/crosstf/<project>/<date>/`, from `core.datapaths.crosstf_dir`. Dated and immutable,
because a verdict is only readable against the exact scaling that produced it.

**That folder IS the databank load.** The mothers are copied in beside the siblings, verbatim,
because the study needs their baseline and control cells too — so step 3 loads one folder and
not two, and nothing has to be assembled by hand:

```
AlgoData/crosstf/XAUUSD/2026-09-23/
  Strategy 10.13.25.sqx             <- mother, untouched
  Strategy 10.13.25_ScaledH4.sqx    <- sibling
  ...
  scaling.parquet                   <- the only record of what was divided and how far
                                       rounding moved it; step 4 reads it
```

Read the two columns it prints before going on. `clamped=True` or `max_rounding_shift` above 0.15
means the cell cannot be attributed to the timeframe, because the rounding moved the parameters as
much as the resampling did. It also lists the int parameters the whitelist did not claim — review
them, do not assume they are wrong.

⚠️ **D1 is not reachable from H1 by scaling.** Measured: ÷24 moves parameters 140–586 % and clamps
every period at the builder's floor. Fabricate D1 only for the *unscaled* row.

⚠️ **And M30 is barely usable as a source at all.** 🔬 2026-09-23: from M30, **÷2 already clamps**
— 5 of 6 siblings came back `clamped`, with rounding shifts of 1.0 (H1) and 7.0 (H4) against a
tolerance of 0.15. The cause is structural, not bad luck: the build doctrine pins the lookback at
one bar and the builder's period floor is 2, so a population built on M30 sits on the floor already
and has nowhere to be divided to. **Check the clamped column before spending a run**: if most of
the batch is clamped, the answer is "this population cannot be rescaled", and no amount of CPU
changes it.

**2 · Wire the task.** It lives in the workflow's own project (`/template-run --workflow`), in the
task titled `CrossTF`, which reads `CrossTF_Input` and writes `CrossTF`:

```bash
python3 -m core.assets <SYMBOL>                           # hard rule 5, blocking
python3 -m sqx.projects.crosstf <SYMBOL> --cfx <install>/user/projects/<P>/project.cfx
                                         # --timeframes H4 D1 overrides the doctrine's list
```

The timeframes, the window and the precision come from `crosstf:` in `assets/_build.yaml`
(`segment: build..oos1`, `precision: 2`). The timeframes depend on the one the strategy was built
on (owner, 2026-09-26): **from M30, H1 and H4; from H1, H4 and H12** — H12 is a custom SQX
timeframe and works as-is in the task (🔬 2026-09-26). `sqx.variants.scale --source H1` fabricates
both siblings by default. `run.blocks` in `studies/transfer/crossTF/config.yaml` must match:
`[H1, H4, H12]` for an H1 population, `[M30, H1, H4]` for an M30 one. H12 siblings of short
periods come back `clamped` (÷12 moves them too far) — they are read only as the unscaled row. `--timeframes` overrides the list for
a one-off; the window and the precision are not overridable on purpose.

Each `<Setup>` overrides **only** `timeframe`; the window, costs, precision and session all come from
the main test through `<MainTestValues>` — the same instrument does not get a different spread for
being resampled. Because the extra blocks inherit the main test's dates, the command **writes the
task's own window as `build..oos1`** (since 2026-09-25; it used to only warn).

It **silences every acceptance condition** of the cross-check and forces `DeleteFailedStrategies`
to false, and says how many — `crosstf.conditions: []` (owner, 2026-09-24): with them live SQX drops
the failing strategy and Python never sees the dead ones
(`knowhow/conditions/crossmarket-crosstf-no-conditions.md`). It leaves `CrossTF` the only active
task, refuses while the install is up (hard rule 4), and ends by printing the `run.blocks` line.
**Paste it into `studies/transfer/crossTF/config.yaml`.**

**3 · Run and export.** On the custodian, stopped at first. Start it, load the folder into the
task's input, then the run half of `/template-run` — `stop` then `start`, only `status` while it
runs, always end stopped:

```bash
python3 -c "from core import worker; print(worker.call('-databank action=load project=<P> name=CrossTF_Input folder=<the crosstf dir>','custodian'))"
python3 -m sqx.export.export_retest --project <P> --databank CrossTF --role custodian
```

**4 · Read.**

```bash
python3 -m studies.transfer.crossTF.report --project <P> --asset <SYMBOL> [--day <export>] [--fabricated <scale day>]
```

Five readings: `survives` (beats its own timeframe's null — the edge is its own), `inherited`
(profitable there but indistinguishable from random entry), `fails`, `control_failed` (the parameter
change broke it, not the timeframe), `unusable` (rounding or clamping moved the parameters too far).

## The trap that is silent

`run.blocks` must match the `<Setup>` order of the task. Wrong, and every cell is priced on the wrong
bars with no error anywhere — `report.py` prints the mapping as its first line for that reason, and
step 2 hands you the correct line. The blocks are separated by the ticket restarting at 1, **not** by
the `Symbol` column, which is identical across the timeframes of one asset.

## Say this when reporting

- **The H4 stop is physically about twice as wide in price than the H1 one.** Only periods and bar
  exits are scaled, so `StopLossCoef` and `ProfitTargetCoef` are written through unchanged while the
  range they multiply grows with aggregation. Declared property of the comparison, not a bug — but
  never describe an H4 cell as a clean "same strategy, slower clock".
- Which readings were `unusable`, and their rounding shift. A population that is mostly unusable is a
  result about short periods, not a reason to raise the tolerance.
- That the result is correlated with what the OOS gate already knew, and is worth less per CPU-hour
  than another market.

## Do not

- Grade the unscaled row, or report it as robustness evidence.
- Read a scaled cell whose `clamped` is True, or whose rounding shift is over tolerance.
- Run it with the cross-check's acceptance conditions live.
- Build D1-scaled siblings and read them as scaled.
- Run it on the master, or on a stock project.
