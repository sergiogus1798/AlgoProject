---
name: analysis-crossmarket
description: Run the cross-market random-entry study for a retest databank — export the bars and the per-market trades, test every strategy against occupancy-matched nulls, read the verdict honestly, and move the rejected strategies into another databank. Use when the owner asks whether a strategy's edge transfers to other markets, whether it is timing or just being long, what a random-entry or Monte Carlo test says, or to apply a verdict inside SQX.
---

# /analysis-crossmarket

```
SQX retest  →  export_bars  →  export_retest  →  report  →  verdict.csv  →  apply_verdict
 (the owner)     bars/          trades/market/    the study    the call      moves in SQX

report = trade_models (how random runs are drawn) → backtest (the numbers) → inference (the maths)
```

It **reads data and writes reports**, and in its last step moves strategies between databanks of one
project. It never changes a project, a task or a build — hard rule 3 stands. The retest itself is the
owner's job in the GUI; this skill starts from its output.

## Step 1 — establish what you are looking at

Ask if it is not obvious from the request:

- Which **databank** holds the retest, and which **base asset** it belongs to.
- Whether `strategies/crossmarket/markets.yaml` already lists that asset, and whether its feeds are
  the same ones the retest task used. A mismatch shows up as a market with zero strategies, not as
  an error.
- Whether the export already exists in `~/Desktop/AlgoData/raw/`. Re-exporting costs SQX time and a
  duplicate copy of the same rows.

## Step 2 — run it

```bash
python3 -m core.assets XAUUSD                                             # preflight, read it out
python3 -m sqx.export.export_bars --asset XAUUSD                          # ~1 min per market
python3 -m sqx.export.export_retest --project XAUUSD --databank RetestMarkets   # ~4 min / 200
python3 -m strategies.crossmarket.report --project XAUUSD \
    --databank RetestMarkets --asset XAUUSD --export <the export's date>   # 1-2 h for 900 x 8
```

`--models` chooses how the random runs are drawn; the first one decides the verdict and defaults to
`block_shift`, the only model that randomises exactly one thing. Add others to see whether a result
survives a different assumption — never to find one that passes. `trade_models.RANDOMISES` says what
each changes, and the report prints it next to every p-value it produced.

`use: null` in the asset file does **not** block here, and this is the only place that is true. The
work reproduces a simulation SQX already ran rather than authoring anything, and the cost is
recovered per trade from the export instead of being chosen. Say that out loud rather than
silently skipping the preflight.

Every run writes **`crossmarket.html`** beside the CSVs: an illustrated report with the null
distribution of each strategy on each market, the real run marked on it, the p-value under every
model, the diagnostics table and a closing section explaining what each number means. It is a single
self-contained file — no scripts, no fonts, no network — so it can be sent to anyone. Open it with
`xdg-open`, and hand the owner that path rather than pasting numbers into the chat.

The figures are capped at the twelve strategies with the lowest p; the CSVs carry all of them. A run
over a whole databank is read from the tables and the luck figure, not from the histograms.

## Step 3 — read it, in this order

0. **Open `crossmarket.html`.** The tables and figures below are the same numbers; the page is
   the fastest way to see whether anything is wrong before reading a single p-value.
1. **`fill_error` and `calendar_kept` in `by_market.csv`, or the *Comprobaciones* table.** They must be 0 and 1.00. If they are
   not, the null and the real run are not comparable and there is nothing to interpret. Stop here.
2. **The luck figure in `crossmarket.md`**, the correlated one. Compare it against the MANTENER
   count before reading a single p-value.
3. **The per-market table.** A market with few testable strategies dropped out of the vote; say why.
4. **Only then** the individual strategies.

## Rules that keep the answer honest

- **This does not detect overfitting to the base asset.** It measures whether timing transfers to
  markets that were never fitted. Reporting it as evidence against overfitting is the single easiest
  way to mislead with it.
- **The base asset never votes.** On the market it was optimised on, a strategy beats the null by
  construction — measured, p between 0.0002 and 0.007 on the eight gold strategies used to build
  this. That number says the code works, nothing else.
- **Correlated markets are not independent evidence.** Eight markets driven by one dollar-and-risk
  factor behave like about two. Use the correlated false-pass figure, and say the vote is weaker
  than its arithmetic suggests.
- **Two families, two sentences.** Fixed-bar-cap strategies get a clean entry-timing result.
  Signal-exit strategies get a joint entry-and-exit result, because the null reuses their holds
  without being able to reproduce what set them.
- **A failed market is a finding, not a failure.** It maps where the edge lives and feeds the
  edge-driver study.
- **The alternative models are not second opinions.** `p` comes from the only model that randomises
  exactly one thing; every `p_<model>` beside it randomises more. Where they disagree, `p` is the
  answer, and the disagreement is itself the finding — it names the assumption the result needed.
- **Report the search space.** N strategies times M markets were tested, and the strategies reaching
  this stage were already selected by SQX's own search.

## Step 4 — the decision, if the owner asks for it

```bash
python3 -m sqx.curate.apply_verdict --project ... --databank ... --verdict ... --into Rejected
```

Dry by default. Before `--apply`: the destination databank must have been created **in the GUI**, and
the master's GUI must be **closed** — the command refuses otherwise, and the owner closes it himself
and signals. It snapshots the source databank outside the install first and verifies by counting the
files back. Never propose deleting instead of moving.

## Output

`crossmarket.html` and `crossmarket.md` are written for you; the page is in Spanish because the owner
and whoever he shows it to are its readers. Add your own conclusions to the report directory **in
English** like the other report files, then give the owner the same conclusions in Spanish in the
conversation, and the path to the HTML. One page: what transferred,
to which markets, how much of it is luck, and what to do about it. It is a decision memo, not a
second copy of the tables.

Found something non-obvious on the way? `knowhow/04-export.md` for export facts,
`strategies/crossmarket/POSSIBLE_IMPROVEMENTS.md` for anything about how the null is modelled — that
file exists so the same modelling arguments are not had twice.
