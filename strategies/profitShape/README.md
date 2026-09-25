# strategies/profitShape — what few things is this result made of?

One study, one folder, three questions that all read the **same trade list and nothing else** — no
bars, no SQX, no new runs:

| | the question | the PDF's item |
|---|---|---|
| **concentración** | does the result survive losing its best trades and its best year? | 1 |
| **independencia** | may these trades be resampled as independent draws? | 2 |
| **rotura** | did the mean change somewhere inside the sample, and where? | 7 |

They are one folder because they are one argument: each says the result rests on fewer observations
than the trade count suggests, and each does it from a different angle.

| file | what it does | run it | in → out |
|---|---|---|---|
| `report.py` | **The panel — the only way to run it** | `python3 -m strategies.profitShape.report --export <trades.parquet> --strategy "Strategy 35.44.31"` | trades → three readings |
| `inputs.py` | The knobs, and one strategy's trades in time order with its daily P&L | imported | export → streams |
| `concentration.py` | Top-share, trimmed metrics, monthly and yearly concentration | imported | P&L → shares |
| `dependence.py` | Wald-Wolfowitz runs, Ljung-Box, and the losing streak against shuffling | imported | P&L → statistics |
| `breaks.py` | OLS-CUSUM, the two sides of the break, and a rolling Sharpe with a non-normal band | imported | P&L → break |
| `verdict.py` | What each of the three means, against frozen thresholds | imported | numbers → readings |
| `config.yaml` | Every tunable, grouped by the layer that reads it | edited, or `--set section.key=value` | — |

Manual page, in Spanish: `docs/manual/40-forma-del-beneficio.md`.

## Four decisions worth arguing with

**Concentration is not a failure by itself, and the module never says it is.** A trend-following
system is positively skewed by design — it is *supposed* to live off a few large winners. What the
number does is set up the comparison the PDF asks for: concentration similar to that of random
entries with the same exits means the skew belongs to the exit structure, not to the signal. That
comparison is `nulls/` and `strategies/entryQuality/`, and this module hands it the figure.

**Profit is attributed by entry time.** A trade belongs to the period in which the decision was
made, because the decision is the thing being judged.

**The Sharpe here is per trade and never annualised.** Trimming removes trades, which changes the
trade frequency; annualising through a frequency that the operation itself alters would compare two
different years and call it a sensitivity.

**The rolling Sharpe's band uses `core.significance.variance_factor`**, the same skew and kurtosis
correction the PSR and the minimum track record already use. A second copy of that formula would be
a correctness risk, not a typing one.

## The trap the CUSUM sets

🔬 Measured 2026-09-24 on `Strategy 35.44.31`, OOS1: the mean before the candidate break is **+82.5**
per trade and after it **−5.1**, and the CUSUM does **not** reject (sup 1.01 against 1.36). Both
statements are correct. The supremum is standardised by the dispersion of the trades, and with a
per-trade standard deviation of hundreds of dollars a shift of that size is inside what a constant
mean produces. Read the two-sided table with the verdict, never instead of it — and never report
the split as a break the test found, because it did not.

## What it does not tell you

- **Nothing about why.** A break's location is a position in a sequence, not an explanation, and it
  can land where the market changed rather than where the strategy did.
- **Nothing about the block length** a portfolio-stage bootstrap should use. `ljung_box` reports the
  last lag with a significant autocorrelation, which is the floor for that choice;
  Politis-White's automatic selection is not implemented.
- **It is not a gate.** With three diagnostics on one strategy, some will fail by chance on a
  genuine edge. A filter derived from these numbers is a new search and belongs in the ledger.
