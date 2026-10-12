# What the literature scout extracts, and how — the rules both the headless calls and the agent follow

## The one rule: nothing is inferred

Every field of an entry is what the source says, with the sentence that says it and where
(`abstract` or `p. N`). A field the paper does not state is the literal `not stated in source` —
in the value **and** in its anchor — never filled from memory, from the title, or from what such
papers usually do. You know many of these papers; that knowledge is not a source. A paper whose
full text could not be fetched is read from its abstract only, every quote comes from the
abstract, and the entry says so (Python stamps it). The validator refuses a quote that is not
verbatim in the stored text.

## The hard filters — applied before extraction

| filter | reject when |
|---|---|
| `no_rule` | no trading rule with an entry: theory, an optimal-control model, a forecast, a learned network, a survey |
| `cross_sectional` | it ranks or holds several assets at once, or needs a universe of stocks. A rule tested asset by asset on index, FX, metal or oil series passes; a rule tested only on single stocks passes only if it is a one-series rule |
| `fundamentals` | it needs anything but the asset's own price and volume: earnings, flows, sentiment, macro, text, another asset |
| `clock` | the entry or the exit reads the hour, a session, the weekday, the month or the calendar (hard rule 15). «Hold N bars» is not a clock; «exit at the close» is |
| `not_sqx_at_market` | not expressible with SQX building blocks entering at market: needs stop or limit entry orders, tick data, an order book, a fitted model. Apply it narrowly (owner, 2026-10-02): AlgoWizard has about 500 conditions and 190 indicators, compares and combines any two values, reads another timeframe's chart from the same strategy (a daily return is ROC or Momentum on D1) and takes custom blocks — returns, their averages, percent ranks, channels and bands are all buildable |
| `conditions` | the entry needs more than two conditions (hard rule 14) |
| `two_legs` | long and short are held together (a spread, a pair, a hedge). A symmetric rule — long on X, short on its mirror — passes: write `direction: both (…)`, the profile measures each side apart (hard rule 13) |
| `no_backtest` | an item of a code repository (key `gh-…`) whose description and code report no backtest result of their own: a rule nobody says they tested is not an entry |
| `unreadable` | neither the full text nor an abstract that states the rule could be read (no quote needed) |

## Futures papers are wanted (owner, 2026-10-02: «si dan una estrategia, merece la pena probarla»)

Never turn a paper away because it trades futures: the rule of a gold, crude, index or currency
future is a rule for our CFD of the same underlying, and one shown on other futures (grains,
bonds) is still a one-series rule worth an entry — say in `note` what the paper traded.
- A paper that runs a **portfolio** of futures passes when its signal is computed contract by
  contract from that contract's own prices (time-series momentum, a channel, a moving average):
  extract that per-contract rule. `cross_sectional` is only for a signal that ranks contracts
  against each other, and `fundamentals` only for one that needs the curve, the basis, positions
  or another series.
- A paper whose own contribution is a model (a network, an optimiser) but that **states the
  classical rules it is compared with** — with their parameters and results — gives those rules
  as entries; it is `no_rule` only when it states none.
- In triage, a futures paper whose abstract names a rule family without its parameters is
  **kept**: the parameters are in the full text.

## The draft

```yaml
paper: <key>
slug: <short-kebab-name-of-the-rule>
asset_class: <indices | forex | metals | oils, comma-separated; the classes the paper tests>
assets: <what the paper tested, in its words>
family: <tendencia | ruptura | reversion | momentum | volatilidad | patron>
direction: <long … | short … | both …>
horizon: {lookback: <…>, holding: <…>, source_bar: <daily, 5-minute…>}
condition: <the regime the paper says it needs, or: none stated — then anchor `not stated in source`>
size: <the effect as the paper reports it: return, Sharpe, t — gross or net, as it says>
sample: <the paper's sample, as written>
grade: <peer-reviewed | working paper | quantified practitioner test> (<journal or series>)
needs_clock: 'no'
decay: <what the paper ITSELF reports out of sample or after publication>
selection:
  variants_tried: <how many rules / parameter sets the authors say they tried, and how they chose>
  sample_from: <first year, integer, or null>
  sample_to: <last year, integer, or null>
translation:
  entry: <the rule on closed bars of M15-H4 or D1 context, one direction written out>
  hold: <the exit the paper uses>
  context: <D1, or none>
  params: <every number, and which the paper fixed>
  note: <what the translation changes from the paper: the bar, the instrument>
  conditions: <1 or 2>
  measures:           # only when they can be written with existing conditions
    - name: <snake_case, new>
      args: {enter: <key>, when: [<key>], leave: <key>, cap: 0, days: 0}
anchors:
  rule: {quote: "<verbatim sentence stating the rule>", where: "p. 7"}
  assets: {quote: "…", where: "p. 3"}
  direction: {quote: "…", where: "…"}
  lookback: {quote: "…", where: "…"}
  holding: {quote: "…", where: "…"}
  condition: not stated in source
  size: {quote: "…", where: "…"}
  sample: {quote: "…", where: "…"}
  variants_tried: {quote: "…", where: "…"}
  out_of_sample: {quote: "…", where: "…"}
```

- `rule` must be quoted; every other anchor is a quote or `not stated in source`, and then the
  field it anchors (`horizon.lookback`, `horizon.holding`, `condition`, `size`, `sample`,
  `assets`, `direction`, `selection.variants_tried`, `decay`) is that same literal.
- A quote is one sentence or a table row copied from the stored text, at least 20 characters.
  Copy it; do not tidy it.
- **The measures** are how the market profile will test the rule on `build`: one per parameter
  value the paper itself tested (three channel lengths → three measures; each is a look the
  ledger counts, so never add a value the paper did not test). `enter`, `when` (at most one) and
  `leave` are keys of `CONDITIONS` in `studies/research/marketProfile/measure/rules.py`
  (`not:<key>` negates one); `cap` is in bars of the cell, `days` in days. Written for longs —
  the short side is the mirror. If the rule needs a condition that is not there, write no
  `measures` and say in `note` exactly which condition is missing: you never edit `rules.py`.
- A paper with another rule that a filter excludes (it needs the T-bill rate, the clock): say so
  in `note`, naming the filter.
- You never set `id`, `source`, `verified`, `overlaps_is`, `overlaps_oos1`, `overlaps_oos2` or `read`: Python stamps them.

## An item of a code repository (key `gh-…`)

Its `abstract` is the strategy's description, its `p. 1…` the code. The rule is what the **code**
does — quote the code lines; where the description and the code disagree, that is a question for
the owner. `size` is the description's own claim, verbatim («Testing indicates…»), and `sample`,
`selection.variants_tried` and `decay` are almost always `not stated in source`: say so. Default
parameter values in the code are the parameters. Python stamps the grade `code repository`.

## An article of a practitioner site (key `web-…`)

A page of a research site or a gestora, cut into `p. N` of its running text; its `abstract` is
the start of the page. `grade` is `quantified practitioner test (<site>)`. A page that states a
rule and says it tested it — its portfolio, its years — is an entry even when its results are
only in figures the text does not carry: then `size` is `not stated in source` (say in `note`
that the results are in the page's charts). `no_backtest` is for code repositories only; a page
with no rule is `no_rule`. A catalogue page
that only summarises a paper (Quantpedia) is an entry of that paper's rule as the page states
it — say in `note` that the source is the summary, not the paper.

## Ambiguity is a stop (hard rule 11)

When the source's rule admits two readings — which band, on the close or intrabar, which bar,
a period the text gives two values for — you do not choose. Write the entry with

```yaml
question:
  text: <what is ambiguous, quoting the phrase>
  readings: [<reading 1, complete>, <reading 2, complete>]
  answer: ''
```

put reading 1 in `translation.entry` marked «(reading 1 of 2, unresolved)», and write **no**
`measures`. Two independent ambiguities in one rule are one question whose readings are the
combinations. The entry waits for the owner; it is not measured before he answers.
