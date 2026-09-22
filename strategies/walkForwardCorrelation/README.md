# walkForwardCorrelation

Does in-sample performance predict out-of-sample performance across a strategy's parameter grid?

One point per parameter combination, in-sample net profit against out-of-sample net profit. A cloud
that fills all four quadrants means optimising in-sample buys nothing out of sample; a cloud on the
rising diagonal means the surface carries information and the in-sample ranking is worth trusting.

Reads contract **C3** (`metrics.parquet`, written by `sqx.variants.collect`) and writes `wfc.html`
and `wfc.json` beside it.

| file | what it decides |
|---|---|
| `config.yaml` | the trade floor and the rho below which the ranking is not worth trusting |
| `measure.py` | which points are usable, Spearman's rho, its 95 % interval, and the call |
| `render.py` | the scatter, as inline SVG |
| `report.py` | the entry point: `python3 -m strategies.walkForwardCorrelation.report --work <dir>` |

**The interval is the point, not the coefficient.** With a dozen tuples the sampling error on a
correlation is enormous, so the study reports a band and will say `indeciso` rather than pretend.
`indeciso` means fabricate more points, not lower the threshold.
