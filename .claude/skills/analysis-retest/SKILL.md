---
name: analysis-retest
description: Run the Monte Carlo Retest study on a project's eight MCR databanks — eight isolated perturbations, each re-running the whole backtest a thousand times, to say which single thing breaks a strategy: the cost of entering, the fill received, its own parameters, or the exact history it saw. Use when the owner asks what a strategy depends on, which perturbation breaks it, whether its edge survives a re-run of the backtest rather than a reshuffle of its trades, what drawdown to size against, or asks to analyse an MC Retest.
---

# /analysis-retest

```
MCR 1..8 databanks  →  ingest  →  parquet  →  report  →  retest.md + verdict.csv
   (ya corridos            lee y            la tabla     el veredicto
    en SQX)                reconcilia       principal    con sus vetos
```

It **reads `.sqx` files from disk and writes reports**. It touches no project, task or build —
hard rule 3 stands — and it never moves a strategy between databanks. Safe with the master GUI open.

Not to be confused with `/analysis-crossmarket`: that is the *cross-market* retest. This is
**Monte Carlo Retest**, where SQX re-runs the entire backtest against a perturbed input.

## Step 1 — check the eight databanks exist

The study needs eight databanks in the project, each with **one** perturbation method active:
`MCR 1 Bar`, `MCR 2 Spread`, `MCR 3 Slippage`, `MCR 4 MinDist`, `MCR 5 Params`, `MCR 6 Exits`,
`MCR 7 OHLC`, `MCR 8 Stress`. The names are fixed in `strategies/retest/inputs/tasks.py`.

If they are not there, stop and say so. **Never start a build and never change what a project
builds** — the owner runs the eight tasks in SQX himself.

## Step 2 — preflight, then ingest

```bash
python3 -m core.assets <SYMBOL>
python3 -m strategies.retest.ingest --project <PROJECT>
```

Use `--limit 1` first on a project you have not ingested before: one strategy per task, a couple of
seconds, and it proves the eight databanks are wired correctly before committing to the full run.

The ingest **refuses to write** when a task ran two methods, when the production task did not run
on the full sample, when a reconstructed metric no longer reproduces what SQX computed, or when an
export already exists for that day. Each refusal names what is wrong. Do not work around one.

## Step 3 — report

```bash
python3 -m strategies.retest.report --project <PROJECT>
```

Writes `retest.md`, `verdict.csv` and a manifest under
`<data root>/reports/<PROJECT>/<databank>/<day>/retest/`.

## Step 4 — read it honestly

Report the verdict table, then the three things a reader will otherwise get wrong:

- **A task that did not perturb anything is not a pass.** On the XAUUSD battery the minimum-distance
  task moved five of five strategies by exactly nothing, and the exit task produced 2 to 6 distinct
  outcomes from a thousand runs — that fleet carries no stop, target or trailing, so there was
  nothing to jitter. Those axes were not tested; say so rather than counting them as survived.
- **The thresholds are unvalidated defaults.** If every strategy fails, check the cut before
  concluding anything about the strategies. They move with `--set gates.survival_dd_pct=0.35`.
- **A confidence level is not a scenario.** Level 95 of net profit and level 95 of drawdown come
  from different simulations.

Quote the `binding` column: it says *where* a strategy breaks, not just that it does. And name the
`blocked_by` vetoes separately from the gating ones — `INCONCLUSIVE` means the battery could not
judge, which is a different statement from `FAIL`.

Full detail: `docs/manual/11-retest-mc.md`. The design arguments, and the nine tests deliberately
left out: `strategies/retest/POSSIBLE_IMPROVEMENTS.md`.
