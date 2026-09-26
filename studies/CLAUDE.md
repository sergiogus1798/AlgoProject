# studies — every question asked of a strategy or a population, one folder each

A study asks one question and ends in a reading. It computes through `engines/` and speaks the
contract of `core/study/`; it never imports another study. Families follow the WORKFLOW's steps
and the catalogue of the window (`docs/AgentPDFs/catalogo-para-la-ui-2026-09-25.md` §3):

| family | the question | steps | studies |
|---|---|---|---|
| `screening/` | of thousands, which deserve to go on? | 7–8 | `gate`, `isOos`, `filters`, `replication`, `decay`, `monkeyExcess`, `snoopingScreen` (+ `analysis/`, their shared maths); *to build:* `falsePositives` |
| `transfer/` | does the edge work away from where it was built? | 9–12 | `crossmarket`, `crossTF` |
| `breakage/` | had the world been slightly different, what breaks it? | 13–16 | `mcRetest`, `spp` |
| `optimisation/` | does optimising buy anything, or is choosing parameters overfitting? | 16.5–19 | `cloud`, `wfc`, `cscv`, `marketSurfaces` (18.5), `wfm` |
| `closing/` | the final call, the shape of the edge, and the stop it trades with | 20–21, 24 | `blindJoint` (20), `exposure`, `atrCalculator` (24) |
| `readings/` | what one strategy's result is made of | 8, 22, 23, 25 | `monkey`, `profitShape`, `entryQuality`, `edgeCost` (8 and 25), `conditionalMap` (22), `structure` (23) |
| `data/` | are the inputs fit to judge with? | 4, 8 | *on hold:* `feedQuality` (encargo 17, owner's consultation pending) |

The trade-level Monte Carlo is not here: the WORKFLOW keeps it out of the sequence and its
question is a portfolio's, so it lives in `portfolio/common/monteCarlo`. What each old path
became is `docs/MAPA-DE-CARPETAS.md`.

## The shape of a study module (encargo 19)

```
<study>/
  config.yaml   every knob, commented; overridden with --set section.key=value
  tooltips.py   one Spanish sentence per knob, for the window's configuration drawer
  one.py        run(strategy, inputs, cfg) -> dict      one strategy, plain data
  many.py       run(inputs, cfg) -> dict                the population, when the study judges one
  report.py     the command: prints the result, writes it, writes verdict.csv
```

- **`one.run` and `many.run` return the contract** (`core/study/CONTRACT.md`): eight block kinds,
  five state words, the config's hash, JSON-safe. The window paints that dict; the batch page and
  the `.md` are drawn from the same dict by `core/study/render`, so they cannot disagree.
- **Results land in `reports/<P>/<D>/<day>/<study>/`** — `<study>.json/.html/.md` for the
  population, `estrategias/<name>.json/.html` per strategy, `verdict.csv` with `strategy`,
  `identity` and `verdict` for `/curate`, and a manifest naming the absolute input judged.
  Studies that read a variant batch write into the batch's `estudios/` instead.
- **Progress is a `PROGRESS <0..100> <state>` line on stdout.** The window and the pipeline move
  their bars with it.
- A study with several internal layers keeps them as folders — `inputs/`, `model/`, `measure/`
  or `simulate/`, `verdict/`, `contract/` — each with its README saying what it must never hold.
  Every study folder carries a `README.md` with the one-row-per-file table, and a
  `POSSIBLE_IMPROVEMENTS.md` when its design had real alternatives: argue a change there before
  making it in code.

What is genuinely shared goes outside: the export readers in `core/`, the computing engines in
`engines/`, the contract in `core/study/`. A helper only two studies need is not shared yet — copy
it, and move it out when a third one wants it.

## Two lifecycles of data, deliberately in separate trees

**`metrics/<project>/<databank>/metrics.csv` is the current export and there is only ever one.**
Refreshing it deletes what was there first. Trade and bar exports keep `raw/<P>/<D>/<date>/`,
dated and immutable. **Reports accumulate**: the CSV is reproducible from SQX, the reasoning is not.

## Traps that have already produced wrong answers

- **Deduplicate on the exported trade list**, not on the name and not on the XML hash: 45 of 231
  strategies had byte-identical trades under different hashes.
- **A stored result covers whatever window it was last retested over.** Check before pooling.
- **Two structurally different populations can share one databank.** Split before you average.
- **Multiple testing is the default condition**, not an edge case: say what the search space was
  before claiming an edge. A correlation inside a sample selected on that metric is attenuated by
  construction — compare outcomes, never correlations, across samples.
- **MAE and MFE are in account currency, not points**, and each trade has its own size:
  `price = abs(MAE_$) / (Size * pointValue)`. Drop the last row when its close price is blank.
- **Never present a stop simulation without a slippage sensitivity**
  (`knowhow/research/research-lessons.md`). The generated XAUUSD strategies carry no stop, no
  target and no trailing — check what a strategy does before assuming the builder's settings.
- **1.2 % of XAUUSD entries do not land on a bar open**, far more on other projects: pending orders
  filled inside a bar, a price-conditional selection any study placing synthetic trades must
  measure first.
- **A translation is not done until it reconciles** against the trades SQX exported, and neither
  is a null: `engines/market/calibrate.convention()` and `crossmarket`'s `pricing.reconcile()`
  refuse to read a market they could not reproduce. The convention measured is open-to-open.
