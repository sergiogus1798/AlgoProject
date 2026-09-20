# crossmarket/render — how is all of that read?

Everything that turns numbers into something on a screen: inline SVG, HTML tables, and the Spanish
wording the owner reads. It is the last layer and the only one allowed to import every layer above
it. It **computes nothing that a reader could disagree with** — no threshold, no p-value, no
resampling — and nothing here writes a file: the panel assembles these strings per request.

**Imports from:** `inputs/`, `mechanics/`, `model/`, `simulate/`, `verdict/`, and itself
**Consumed by:** `explorer/`
**Must not contain:** a statistic, a threshold, a decision, or any `<script>` — every figure is
static markup so it renders the same anywhere

| file | what it does | run it | in → out |
|---|---|---|---|
| `svg.py` | **The drawing primitives every figure shares:** the canvas constants, the axis positions, the axis number, the market palette and the legend | imported | value + extent → pixels, markup |
| `charts.py` | The study's two figures: a statistic's distribution with the real run on it, and the equity cone | imported | numbers → SVG |
| `figures.py` | The per-market comparison figures: one bar or one cell per market, and the window sweep's p curves — every swept model on one axis | imported | rows → SVG |
| `overlays.py` | The two figures that lay several series over one axis: market equity curves, and two distributions through each other | imported | curves, bins → SVG |
| `overview.py` | The main tab's tables: every market's real backtest, the same at equal risk, and what its sample size holds up | imported | rows → HTML |
| `tables.py` | Renders Tests 1b and 1c, the fingerprint, the cost stress and the correlation into HTML tables | imported | rows → HTML |
| `panel.py` | The market table, the diagnostics table, the glossary and the Spanish wording | imported | rows → HTML |

## The primitives are a declared API, not private names

`svg.py` was split out of `charts.py` on 2026-09-18 for one reason: `figures.py` imported `_x` from it
and `overlays.py` imported `_ticks`. **A private name imported from another module is not private —
it is an API nobody declared.** The two are now `svg.xpos()` and `svg.tickvals()`, alongside the
constants, `num()`, `palette()` and `legend()` every figure already shared.

⚠️ **`tickvals`, and not `ticks`, on purpose.** `ticks` is already a local variable holding rendered
markup in both `charts.cone()` and `overlays.py`. A public name that collides with a local in the
module that imports it fails **at render time, not at import time** — the local shadows the import and
nothing complains until someone opens that tab. Grep for local assignments before choosing a name
here.

## The panel opens on the backtest, not on a test

Rebuilt 2026-09-16 at the owner's request. `Resumen`, `Significancia` and `Correlación` were three
tabs answering one question between them, and nobody reads a strategy's drawdown on one page and its
confidence interval on another: they are one tab, **`Backtest`**, which the panel opens on.

`overview.py` builds it, in this order: the strategy's tiles; every market's **real** backtest (net,
return, drawdown in dollars and per cent, Ret/DD, Sharpe, PF, losing run) with the base asset last
and marked *reference, not evidence*; the same comparison **at equal risk**, every market rescaled
until its worst drawdown is `equity.risk_target_dd` of the account; the **overlaid equity curves**,
each market on its own independent account, in per cent, on real calendar dates so a market whose
backtest starts later starts later on the chart; the correlation matrix; what each test said; what
holds those numbers up; the warnings; the mechanical checks; and a paragraph per statistic.

**What was removed, and why.** `drivers.py` and the `El mercado` tab: the edge-driver regression it
was built for needs six or more markets on the right-hand side and the owner will have four, so with
two it described markets rather than saying anything. `correlation.pca()` and the `Correlación` tab:
with two or three streams PC1 is close to a function of the mean pairwise correlation. Both are
recorded as **discarded with a reason** in `POSSIBLE_IMPROVEMENTS.md` rather than deleted from it, so
neither is proposed again from scratch.

## Contracts and traps

- **The Spanish wording is a mirror with a contract.** `panel.NAMES` is the only place a reader's name
  for a null model lives; `panel.RANDOMISES` mirrors `model/trade_models.RANDOMISES`; and
  `panel.WARNINGS_ES` mirrors `verdict/inference.WARNINGS`. Code and registry keys stay English. A
  key added upstream without a row here renders as a missing entry, not as a fallback.
- **Direction is never assumed.** Anything that colours a cell reads
  `simulate/metrics.HIGHER_IS_BETTER`: for `dd` and `losing_run`, a real run high in its null drew
  down *worse* than chance, which reads the opposite way from `net`.
- **A figure carries its own legend.** `svg.legend()` takes the swatch style the figure actually drew
  — a filled box for a bar or band, a border style for a line — so the chips cannot drift from the
  picture. No caption sentence is asked to do that job.
- **The distribution figure labels only the real value inside the plot.** The median and the two
  percentiles live in the table beside it: at some values their labels collided on top of the plot.
- **One colour per market, fixed for the whole panel.** `svg.palette()` gives the base asset `--real`
  — the colour that means "the reference" everywhere else — and the rest take `MARKETS` in the order
  the universe lists them, so a market does not change colour when another one is re-run alone. Every
  tab that needs colours goes through it; `explorer/portfolio_tab.overview_palette()` deliberately
  routes through the main tab for the same reason.
- **Nothing here reads `config.yaml` to decide anything.** It prints knobs — including, on the cost
  tab, `source: placeholder` and `reviewed_by_owner: false` from `execution.yaml` — and applies none.
