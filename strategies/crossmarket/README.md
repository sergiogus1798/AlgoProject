# strategies/crossmarket — does the edge transfer to markets it never saw?

One study, one folder. Inside it, four boundaries in the order the data flows, as rule 5 of
`CODESTYLE.md` requires: **configuration → modelling → execution → inference**. Read
`POSSIBLE_IMPROVEMENTS.md` before extending any of this.

```
markets.yaml ─▶ markets ─▶ envelope ─▶ trade_models ─▶ backtest ─▶ inference ─▶ text
 what it runs on   config   the real run   how random     the numbers   the maths   the words
                              is shaped    runs are drawn
```

**`explorer/` is the only way to run this study.** There is no batch command any more: open the
panel, pick a strategy or the whole database, and its own "Generar informe" button writes the same
files the old `report.py` used to. See `explorer/README.md`.

| file | what it does | run it | in → out |
|---|---|---|---|
| `markets.py` | Reads `markets.yaml`: which additional markets each base asset is retested on | imported | asset → feeds |
| `envelope.py` | The real run's shape on the bar grid: bars held, gaps, regime blocks, and the weekday-hour groups a model may move it to | imported | trades + bars → the market dict |
| `pricing.py` | ATR, the cost SQX charged recovered per trade, and the fill convention re-derived by reconciling against SQX's own prices | imported | bars + trades → returns, cost, convention |
| `trade_models.py` | **How random trades are drawn.** Four models behind one signature, plus what each holds fixed and a goodness-of-fit check on the ones that fit distributions | imported | envelope → entries, holds |
| `backtest.py` | Runs the real run and N random ones under a chosen model, priced identically | imported | trades + bars + model → real, null, diagnostics |
| `inference.py` | **All the statistics.** p-value, effect size, admissibility, the verdict, and how many passes are luck | imported | real + null → rows, verdict |
| `text.py` | Turns the rows into `crossmarket.md`. Pure text, computes nothing | imported | rows → markdown |
| `charts.py` | Draws the figures as inline SVG: the null distribution with the real run on it, and the p-value per model | imported | a distribution → SVG |
| `panel.py` | Assembles `crossmarket.html` from `panel.html`: figures, tables and what every number means | imported | rows + distributions → HTML |
| `bootstrap.py` | Block-bootstrap resampling and percentile confidence intervals, shared by `exposure.py` and `significance.py` | imported | a sequence → resampled positions, a CI |
| `exposure.py` | Test 1c: concentration ratio E, drift-neutral excess A with its bootstrap CI, risk-normalised A, and the MFE capture ratio | imported | trades + bars → E, A, capture |
| `significance.py` | Minimum track-record length and bootstrap CIs on PF/expectancy, from the real per-trade returns. No DSR — see `POSSIBLE_IMPROVEMENTS.md` | imported | trades + bars → moments, CI |
| `breadth.py` | Breadth, worst-market floor and PF dispersion across one strategy's markets — replaces the single median | imported | per-market rows → breadth, floor, CV |
| `fingerprint.py` | Behavioural fingerprint against the base asset: holding-time KS, MAE/MFE profile normalised by ATR, return shape | imported | trades + bars, base vs. market → fingerprint |
| `stress.py` | Cost gradient, breakeven cost multiple, and decay under a bar shift or range slippage | imported | trades + bars → cost/slippage curves |
| `correlation.py` | Weekly equity curves, their correlation matrix, and PCA by SVD across a strategy's markets plus gold | imported | trades + bars per market → correlation, variance share |
| `tables.py` | Renders Test 1c, significance, fingerprint, cost and correlation into HTML tables/figures for `panel.py`'s static report and `explorer/sections.py`'s live tabs | imported | rows/record → HTML |
| `explorer/` | The interactive panel — the only entry point. See `explorer/README.md` | `python3 -m strategies.crossmarket.explorer.serve --project XAUUSD --databank RetestMarkets --asset XAUUSD --export 2026-09-08` | export → `http://127.0.0.1:8766` |

`backtest.py` never chooses a model and `inference.py` never produces a number it judges. That is what
lets the same runs be re-judged, or the same judgement re-run under another model, without editing
either — which is the only way to find out whether a conclusion depended on an assumption.

`markets.yaml` lives here rather than in `assets/` because it is this study's design, not a fact about
an instrument. **The list is fixed before results are looked at**: choosing markets after seeing where
the strategies work turns the test into a selection.

The bars and trades come from `sqx/export/export_bars.py` and `sqx/export/export_retest.py`, read with
`core/bars.py` and `core/trades.py`. Those four are shared with every future study and live outside.

## Adding a model

Write a function in `trade_models.py` with the shared signature — `(held, market, draws, rng)` in,
`(entries, holds)` out — add it to `MODELS`, and add a row to `RANDOMISES` saying **what it
randomises**. Nothing else changes: the panel's config drawer picks it up as another model to run,
and the test explorer's model dropdown gains an entry.

That row is not documentation, it is the finding. A model that randomises more than one thing cannot
attribute a low p-value to any single cause, so the report prints it next to every p-value it produced.

| model | randomises | reads as |
|---|---|---|
| `block_shift` | placement, inside the regime block and the weekday-hour slot | the verdict: **the only model that changes exactly one thing** |
| `segment_permute` | placement, order, clustering and calendar | a weaker null; passing only here means the result needed the clustering removed |
| `resampled_holds` | placement, which holds and gaps occur, and time in market | a test of the trading rhythm rather than of this realisation of it |
| `fitted_holds` | placement, and the holding times themselves | a system with this *shape* of holding time entering at random |

`fitted_holds` fits a negative binomial when the observations are overdispersed and a Poisson when
they are not — a property of the data, not a setting. `goodness()` reports the dispersion and a KS
p-value beside it: on the XAUUSD fleet the holds are almost constant (dispersion 0.05, KS p < 0.001),
so **no fitted distribution describes them** and that model's result there is a statement about the
wrong distribution. The check is in the output so nobody has to remember this.

## What the test compares, and what it cannot

The statistic is the **mean log return per trade, net of cost**, divided by one constant per market
(the median ATR as a fraction of price) so markets compare. That constant is identical for the real
run and every random run, so it cannot move a p-value — it only puts gold, the DAX and EURUSD on one
axis.

The earlier design divided each trade by the ATR **of its own entry bar**. That is wrong here and was
removed: real entries are chosen by the rule and random ones are not, so any filter that favours
compressed bars divides the real trade by a small number while the move that follows reverts to normal
volatility. It inflates the real statistic with no directional edge at all, in the direction of
passing. `atr_ratio` in every row is the diagnostic that would have caught it.

## Why block_shift is shaped the way it is

Three properties, each of which was needed, and two of which were found by measuring:

- **Blocks**, because thirteen years of gold are not one regime. A strategy whose trades sit in a
  strong trending stretch would beat a null spread over the whole sample on drift alone.
- **Whole weeks, in the block's own weekday-hour groups**, so entries land on the weekday and hour they
  really used — an eight-bar hold entered late on a Friday spans the weekend gap and one entered on a
  Tuesday does not. `calendar_kept` must read 1.00; when the shift was written in bar space it read 0.05.
- **The wrap**, because a strategy's trades span nearly the whole of every block. Placing them end to
  end left one legal position in most blocks and none in nine of twenty-four, and the null then
  reproduced the real run — measured, it returned p ≈ 0.5 for everything.

## Rules these enforce, because each one has a direction

- **A market is dropped from the vote, not corrected**, when it has fewer than 30 trades, or when fewer
  than 95% of entries land on a bar open. A pending order filled inside a bar is a price-conditional
  selection no model reproduces, and testing it anyway flatters the strategy.
- **The base asset never votes.** Measured on eight gold strategies, every one beat its null at p
  between 0.0002 and 0.007 — that says the code works, and nothing about the strategies.
- **Holds are never resampled by the verdict's model.** Under `block_shift` each random trade keeps the
  hold of the real trade it replaces.
- **A strategy whose exits are a rule gets a different sentence.** No model reproduces what set those
  holds, so for that family the result is a joint test of entry and exit. `inference.family` separates
  them and the report says so.
- **Read the luck figure before the verdict count.** For eight markets over 900 strategies it is 10.3
  assuming the markets correlate at 0.5, against 0.014 assuming they do not. The first is the one to use.
