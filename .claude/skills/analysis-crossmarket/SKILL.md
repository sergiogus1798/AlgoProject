---
name: analysis-crossmarket
description: Run the cross-market study for a retest databank — export the bars and the per-market trades, measure every strategy against occupancy-matched nulls, against its own blind window, and against the market's own average bar, and report every number with the reasons to distrust it. Use when the owner asks whether a strategy's edge transfers to other markets, whether it is timing or just being long, what a random-entry test says, or asks to analyse a cross-market retest.
---

# /analysis-crossmarket

```
SQX retest  →  export_bars  →  export_retest  →  explorer panel, one strategy at a time
 (the owner)     bars/          trades/market/    read it on screen; nothing is written

panel = trade_models (how random runs are drawn) → backtest (prices them in dollars)
        → metrics (what each run is worth) + equity (the cone) → the tabs
      + paired (1b) / exposure (1c) / significance / breadth / fingerprint
      / drivers / stress / correlation
```

It **reads data and writes reports**. It never changes a project, a task or a build — hard rule 3
stands. The retest itself is the owner's job in the GUI; this skill starts from its output.

**There is no verdict, and there is no `apply_verdict` step in this skill any more.** The owner asked
for a measuring instrument, not a decision procedure. Do not reintroduce a MANTENER/DESCARTAR call,
a composite score, or a gate that removes a market from the analysis — each of those was deliberately
removed on 2026-09-14 and the reasons are in `strategies/crossmarket/POSSIBLE_IMPROVEMENTS.md` and
`knowhow/07-practices.md`. If the owner asks to act on a result, that is
`python3 -m sqx.curate.apply_verdict` run on a CSV he decided, not on one this study wrote.

`strategies/crossmarket/explorer/serve.py` is the only entry point, a local Flask panel, and it runs
**one strategy at a time**. There is no batch command, no report file and no cache — removed on
2026-09-15 at the owner's request. Every number on screen comes from the run he just started; the
panel deletes any result an earlier build left on disk when it starts. Do not add caching back, and
do not offer to write a report file unless he asks for one.

## Step 1 — establish what you are looking at

Ask if it is not obvious from the request:

- Which **databank** holds the retest, and which **base asset** it belongs to.
- Whether the export already exists in `~/Desktop/AlgoData/raw/`. Re-exporting costs SQX time and a
  duplicate copy of the same rows.

You do **not** need to check `markets.yaml` first. The study discovers the markets from the export
itself and classifies them against that file; a feed missing from it is analysed anyway and marked
`sin clasificar`, and a declared feed the export has no trades for is printed as absent at start-up.

## Step 2 — run it

```bash
python3 -m core.assets XAUUSD                                   # preflight, read it out
python3 -m sqx.export.export_bars --asset XAUUSD                # ~1 min per market
python3 -m sqx.export.export_retest --project XAUUSD \
    --databank "Retest Markets - Family" [--limit 30]           # ~4 min / 200 strategies
python3 -m strategies.crossmarket.explorer.serve --project XAUUSD \
    --databank "Retest Markets - Family" --asset XAUUSD --export <the export's date>
```

`--limit N` stages a reproducible random sample instead of the whole databank — use it when the
point is to check the pipeline rather than to analyse everything.

The panel opens at `http://127.0.0.1:8766`. Pick a strategy and the markets SQX retested it on appear
below. **Run analysis** does the whole strategy (~30 s at the default 25,000 draws over two markets, so
roughly a minute over four); the **run** button beside one market does that market alone and merges
into what is already there, which is how to raise the draws on a single market without paying for
the rest. The config drawer (▸) holds all 35 knobs of `config.yaml`, in columns, each with its own
sentence on hover; the same overrides work at launch as `--set nulls.draws=50000`.

Inside **Entrada aleatoria** there are three selectors: a sub-tab per market, a sub-tab per null
model under it, and a dropdown for which statistic the histogram draws. Switching any of them
recomputes nothing — every model's whole result is already in memory.

`use: null` in the asset file does **not** block here, and this is the only place that is true. The
work reproduces a simulation SQX already ran rather than authoring anything, and the cost is
recovered per trade from the export instead of being chosen. Say that out loud rather than silently
skipping the preflight.

## Step 3 — read it, in this order

1. **`fill_error` and `calendar_kept`**, in the *Comprobaciones* table of the Resumen tab. They must
   be 0 and 1.00 under `block_shift`. If they are not, the null and the real run are not comparable
   and there is nothing to interpret. Stop here.
2. **The Avisos tab**, before any number. It names what to distrust on each market.
3. **The per-market table**, then the cone, then the histograms.
4. **The search space, out loud.** This panel shows one strategy of the 757 in the databank, and
   those were already selected by SQX's own search. At alpha 0.05, roughly 38 of 757 clear it on a
   market by chance. Never report a single strategy's p-value without saying that.

## Reading the two simulation tabs

**Entrada aleatoria (1a)** and **Coste y ejecución** both show, per market, an equity cone and a
histogram per statistic. They answer different questions — the first is what random *timing* could
have done with the same trading rhythm, the second what a worse *broker* could do to the same trades
— and must never be described as two views of one thing.

- Every random run is priced **in dollars with the real trades' own sizes and charged costs**, so
  `net` on the page is directly SQX's own: the reconstruction correlates 0.9996 with its reported
  P/L. Say that when the owner asks whether the number is real.
- **Direction matters.** For `dd` and `losing_run` a small p means the real backtest suffered *less*
  than chance. Reading it as "significant, therefore bad" is the easiest mistake on the page.
- The cone's x axis is **calendar time**, not trade number. Read it for its width and for where the
  real curve leaves it, never for a single line inside it.
- A typical honest result on this data: on silver, a real net of +26,428 $ against a null median of
  −47,291 $ — the random runs lose roughly what they pay in costs. The strategy earning its costs
  back is most of what a low `p_net` is saying.

## What each test is for, and which one to trust when they disagree

- **Test 1a** (`p`) — the real run against occupancy-matched random runs, 25,000 of them **per
  market and per model**. Four models in **two families**: `segment_permute` / `resampled_holds` /
  `fitted_holds` re-lay the whole run anywhere in the sample (changing when, order, calendar and
  regime at once), and `block_shift` moves each trade inside its own semester and weekday-hour slot,
  changing only *when*. `nulls.headline` names `block_shift` and the summary reports its p, because
  it is the only one whose low p is attributable to entry timing.
  🔬 **Measured with the window bounded, it returns the lowest p in 7 of 8 (strategy, market) pairs
  and the narrowest null in 5 of 8** — usually the most flattering, never the reason to trust a
  result. So a strategy that survives all four says more than one that survives only `block_shift`,
  and reporting a lone `block_shift` pass as strong evidence is wrong.
  🔬 **Everything runs on the backtest's own window**, not the bar file: `envelope.window()` slices
  to first entry / last exit before anything is computed. The bar file is about a third wider than
  the retest on this data, and letting nulls trade outside the backtest's span distorts every
  statistic. Never remove that slice.
  🔬 `renewal` was retired the same day: over 8 (strategy, market) pairs it matched
  `resampled_holds` to within 2% on null width and 0.004 on p. Do not propose adding it back
  without a measurement that says it separates.
- **Test 1b** (`paired_p`) — each trade against the exact mean of every window of its own length in
  its own regime block. **Needs no null model and no cost assumption.** When 1a and 1b agree, the
  result does not rest on a modelling choice. When only 1a passes, say that the result depends on
  how the null was built.
- **Test 1c** (`a`, `e`) — beating the market's own average bar rather than beating chance. Read
  **A**, not E: E divides by the market's drift and is withheld where that drift is not
  distinguishable from zero, which on this data is both non-gold markets.

## Rules that keep the answer honest

- **Never present this as evidence against overfitting.** It measures whether timing transfers to
  markets that were never fitted. Saying it the other way is the single easiest way to mislead.
- **The base asset is the reference case, never evidence.** On the market it was optimised on, a
  strategy beats its null and its blind window by construction. That says the code works.
- **Correlated markets are not independent evidence.** Read the PCA before treating a count of
  markets as a count of confirmations.
- **Two families, two sentences.** Fixed-bar-cap strategies get a clean entry-timing result;
  signal-exit strategies get a joint entry-and-exit result, because the null reuses their holds
  without reproducing what set them. The Friday close is the one exit rule the nulls do replicate.
- **A failed market is a finding, not a failure.** It maps where the edge lives.
- **Report the search space.** N strategies times M markets were measured, and the strategies
  reaching this stage were already selected by SQX's own search.
- **Never drop a market, never rank strategies into keep and discard.** Report and explain.

## Output

Nothing is written. The panel is the output, and it is in Spanish because the owner is its reader.
Report back to him in Spanish, in the conversation: what transferred, to which markets, what the
warnings say, and what he might want to look at next. It is a memo, not a second copy of the tables
— and it recommends, it does not decide.

Found something non-obvious on the way? `knowhow/04-export.md` for export facts,
`strategies/crossmarket/POSSIBLE_IMPROVEMENTS.md` for anything about how the null is modelled — that
file exists so the same modelling arguments are not had twice.
