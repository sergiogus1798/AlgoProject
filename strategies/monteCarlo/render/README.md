# monteCarlo/render — how is all of that read?

The presentation layer: HTML pages, inline SVG figures and Spanish sentences. It is the last layer,
so it may import any of the others — but only to *read* their tables and results. **If a figure in
this folder computes a number that did not come from `simulate/` or `verdict/`, that is a bug**, not
a convenience: a value that exists only in the renderer cannot be gated, cannot be cross-checked,
and disagrees silently with the panel.

Everything here is self-contained: no script to run in the browser, no asset to fetch. The batch
report and `explorer/` call these same functions, which is the reason the two can never disagree.

**Imports from:** every other layer  ·  **Consumed by:** `report.py`, `explorer/`
**Must not contain:** a calculation, a threshold, or a decision

| file | what it does | run it | in → out |
|---|---|---|---|
| `svg.py` | **The drawing primitives.** Canvas size, margins, colours, axis placement, number format and the legend | imported | value → pixels, chips |
| `charts.py` | The two core figures: a simulated distribution with the backtest marked on it, and the equity cone | imported | numbers → SVG |
| `barcharts.py` | The two bar figures: the sub-scores against their cutoffs, and a signed bar per group | imported | numbers → SVG |
| `timeline.py` | Family D's two time-indexed figures: equity against its windows, price against the volatility regime | imported | series → SVG |
| `overlay.py` | The IS/OOS figure: two histograms on one axis, each scope's own reference lines | imported | shapes → SVG |
| `panel.py` | The databank page and the shared table and shell helpers | imported | rows → HTML |
| `panel.html` | The shell every page is poured into: the stylesheet and the colour variables | read | — |
| `text.py` | The Spanish sentences: one per check that can fire, plus `montecarlo.md` | imported | result → words |
| `strategypage.py` | One strategy's page: verdict, what failed, then the families | imported | result → HTML |
| `families/` | The five family sections of one strategy's page, one file per family. Its own README | imported | result → HTML |

## Contracts and traps

- **No figure redefines an axis.** `W`, `H`, `PAD`, the colour variables, `xpos()`, `ypos()`,
  `num()` and `legend()` come from `svg.py` and only from there, so every figure in the report
  shares one geometry and one number format. A chart that sets its own margins will not line up
  with the one above it.
- **`svg.line` and `svg.box` are legend swatches, not SVG elements.** They return inline CSS for a
  chip. They are also easy to shadow: a local variable called `line` inside a figure silently
  breaks the legend at render time, which is how `timeline.equity_windows` once failed.
- **Every colour is a CSS variable** (`var(--null)`, `var(--real)`, `var(--vol-high)`) defined in
  `panel.html`. Nothing here hard-codes a hex value, which is what keeps the light and dark palettes
  consistent and the report readable when printed.
- **Prose is Spanish, identifiers are English.** The owner reads the report; the registry keys
  (`skip`, `cost_shock`, `iid_bootstrap`) stay in English and are translated at the last moment
  through `model.stress.TITLES` and `families/common.py` — so a model name is never typed twice.
- Reading a registry's label table from `model/` or `verdict/` is correct and intended; running one
  is not.
