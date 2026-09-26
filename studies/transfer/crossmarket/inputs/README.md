# crossmarket/inputs — what is this study being run on?

The three declarations, and nothing computed from them: every tunable of the study, which markets
exist and what they are called, and what a worse broker would charge on each. A module here reads a
`.yaml`, validates it against what the export really carries, and hands back a plain dict.

**Imports from:** `core/` only
**Consumed by:** `simulate/`, `render/`, `explorer/`, and the three `.yaml` files in the module root
**Must not contain:** a statistic, a p-value, a threshold's *consequence* (that is `verdict/`), or
anything that reads bars

| file | what it does | run it | in → out |
|---|---|---|---|
| `config.py` | Reads `config.yaml`: every tunable of the study, in one place | imported | overrides → config |
| `markets.py` | Reconciles what the export really carries against what `assets/_markets.yaml` declares, and reads the main backtest's declared out-of-sample stretch | imported | asset + export → universe, OOS span |
| `execution.py` | What a worse broker would charge, per feed, from `execution.yaml`; and that file against what SQX really charged | imported | feed + trades → shock, depth, gap |

## Where a threshold is changed

**Every tunable of this study is a key of `config.yaml`, and `config.py` is the only module that
reads it.** Nothing else opens the file, and no module holds a number the owner might want to move.
To change one: edit `config.yaml`, or pass `--set section.key=value` on the command line, or move it
in the panel's config drawer — the drawer is built from `config.flatten()` plus one sentence per knob
in `explorer/tooltips.py`, so a new knob needs a row there too or it appears without its hover text.

What the knob then *does* lives one layer away: `verdict/inference.py` turns
`diagnostics.min_trades`, `diagnostics.alpha` and the rest into named warnings, and
`verdict/breadth.py` into breadth. A limit hard-coded in `simulate/` or `render/` would be a rule
nobody can find; it belongs in `config.yaml` and is read where the judgement is made.

## The `.yaml` files stay in the module root

`config.yaml`, `assets/_markets.yaml` and `execution.yaml` sit **one level up**, beside `README.md`, because
`docs/manual/07-otros-mercados-y-timeframes.pdf` (cap. 05-retest-mercados) names them by that path. Each of the three modules resolves its
own file as `Path(__file__).parents[1] / "<name>.yaml"` — `with_name()` would look inside `inputs/`
and the file would silently not be found. Moving a module here without changing that line is the
failure this layer is most likely to suffer.

## Contracts and traps

- **The markets are discovered; `assets/_markets.yaml` only classifies them.** It groups each base asset's
  markets into categories — `family`, `structure`, whatever comes next — and **does not decide what
  exists**. What a strategy was really retested on is read from the export, whose `trades/<feed>/`
  folders are built from the trades' own `Symbol` column. A feed the declaration does not name is
  kept and marked `sin clasificar`; a declared feed the export has no trades for is printed as absent
  at start-up. Before this, a mismatch showed up as a market with zero strategies rather than as an
  error.
- **The market list is still fixed before results are looked at.** Choosing markets after seeing
  where the strategies work turns the test into a selection.
- **The cost stress does not use round numbers.** `execution.yaml` holds, per feed, a typical and a
  stressed spread in points, a commission in USD per lot per side, a typical slippage and the tick
  size. `stress.cost_shock` is `spread_stress / spread_typical` and `stress.fill_depth` is two sides
  of that slippage as a fraction of the median MAE, both per market, instead of `[1.0, 2.0]` and
  `0.25` — numbers nobody had chosen. `p_skip` is **not** calibrated and is labelled as the
  assumption it is: nothing in the export says how often an order would have been missed.
- ⚠️ **The values in `execution.yaml` are placeholders**, written as a typical CFD broker's so the
  owner has something concrete to correct. Each block carries `source: placeholder` and
  `reviewed_by_owner: false`, and the panel prints both. They are deliberately **not** in
  `assets/*.yaml`: those files gate every project in this repo through `core.assets`, and
  `assets/RULES.md` says a file with invented values is worse than no file, because it looks decided.
  A feed that does have an asset file reads its decided spread from there instead.
- **`execution.compare()` is the check on this layer's own honesty.** It prints, per market, the cost
  SQX **really charged** — recovered per trade from its own P/L, and the truth — against what
  `execution.yaml` implies, and flags a gap past 25%. Measured on Brent: 25.85 charged against 37.46
  modelled, +45%, which is the placeholder being wrong and the table doing its job.
