# studies — every question asked of a strategy or a population, one folder each

A study asks one question and ends in a reading. It computes through `engines/` and speaks the
contract of `core/study/`; it never imports another study. Families follow the WORKFLOW's steps
and the catalogue of the window (`docs/AgentPDFs/catalogo-para-la-ui-2026-09-25.md` §3):

| family | the question | steps | studies |
|---|---|---|---|
| `screening/` | of thousands, which deserve to go on? | 7–8 (step 8 judges `gate` alone) | `gate`, `isOos`, `filters`, `replication`, `decay`, `monkeyExcess`, `maeDepth`, `falsePositives` (the chain's negative control) (+ `analysis/`, their shared maths) |
| `transfer/` | does the edge work away from where it was built? | 9–12 | `crossmarket`, `crossTF` |
| `breakage/` | had the world been slightly different, what breaks it? | 13–16 | `mcRetest`, `spp` |
| `optimisation/` | does optimising buy anything, or is choosing parameters overfitting? | 16.5–19 | `cloud`, `wfc`, `cscv`, `marketSurfaces` (18.5), `wfm` |
| `closing/` | the final call, the shape of the edge, and the stop it trades with | 20–21, 24 | `blindJoint` (20), `exposure`, `atrCalculator` (24) |
| `readings/` | what one strategy's result is made of | 8, 22, 23, 25 | `monkey`, `entryQuality`, `edgeCost` (8 and 25), `conditionalMap` (22), `structure` (23) |
| `data/` | are the inputs fit to judge with? | 4, 8 | `feedQuality` (encargo 17), `spread` (step 4 only: its step-8 reading is gone) |
| `research/` | where to look next, before any idea exists: what behaviour each asset × timeframe × direction shows against chance, how small an edge that profile can see, what was already tried, the literature | step 1 | `marketProfile`, `profilePower`, `pooledProfile`, `board`, `memory`, `literature` |

`research/` is a subsystem, not a set of independent studies: its modules import each other
(`profilePower` and `pooledProfile` → `marketProfile`, `board` → `memory`), so the "never imports
another study" rule does not apply inside it (see `research/README.md`).

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

Each trap lives as a card; read it before building the study that touches it.

- **Duplicates, stale windows, mixed populations, multiple testing, slippage on stop
  simulations** → `knowhow/research/research-lessons.md`; dedup on the exported trade list →
  `knowhow/export/what-a-project-stores.md`.
- **MAE/MFE units and per-trade size** → `knowhow/export/mae-mfe-from-m1.md`,
  `knowhow/export/orderstocsv-schema.md`.
- **Entries off the bar open, open-to-open convention, reconcile before trusting a translation
  or a null** → `knowhow/export/fill-and-pricing.md`,
  `knowhow/research/crossmarket-returns-miss-entry-offset.md`.
