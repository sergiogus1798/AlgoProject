# core/study — the contract every study module speaks

A study (`studies/…`, `portfolio/common/monteCarlo`) computes; this folder only says **what shape
its answer takes** so the desktop window and the batch report read one structure and cannot
disagree. It analyses nothing. The contract itself is `CONTRACT.md`
(it was encargo 19); `studies/CLAUDE.md` says how a module is laid out around it.

| file | what it does | run it | in → out |
|---|---|---|---|
| `__init__.py` | The contract every study module speaks: its config, its blocks, its result and its page. | — | — |
| `bands.py` | N curves drawn as percentile bands (5-95, 25-75), the median and the original — a `cone` block. | imported | curves → block |
| `blockcheck.py` | The optional keys of a block: a distribution's series and shift, a grid's mark and scale. | imported | block → raises or passes |
| `blocks.py` | The kinds of block a study result is made of, built from raw numbers and checked. | imported | numbers → blocks |
| `clip.py` | The one rule every histogram of the window follows: the axis spans percentiles 0.5-99.5, outliers are not drawn. | imported | draws → inside values, span |
| `config.py` | A study's knobs: its config.yaml read, overridden from the command line, and fingerprinted. | imported | YAML + overrides → dict, hash |
| `draws.py` | The simulated distribution behind a z or a p, kept so nobody reruns a test to look at it. | imported | draws → rows → parquet |
| `identity.py` | The identity of a strategy named in an export: from an install, the cosecha, or the export's .sqx. | imported | names → hashes |
| `output.py` | Where a study's results land: one JSON per strategy, and the population's JSON, page and markdown. | imported | results → files |
| `result.py` | The envelope every study result travels in, and the progress line the window reads. | imported | tabs → result dict |
| `verdicts.py` | A population verdict written where the window and /curate find it: verdict.csv plus its manifest. | imported | frame → CSV + manifest |
| `CONTRACT.md` | The result dict and the eight block kinds, field by field | — | — |
| `render/` | The result dict drawn as a self-contained HTML page, one drawer per kind | imported | result → HTML |

## Three rules the validator enforces

- **Eight kinds, no ninth.** A module that needs a new drawing asks first: the window has one
  widget per kind and a new kind is a new widget.
- **Five state words** — `pass`, `fail`, `watch`, `info`, `none`. A module's own words
  (MANTENER, worth_it) belong in `verdict.csv`, which is for `/curate`, not in a block.
- **Aggregated, never raw.** `blocks.distribution` and `blocks.cone` take the draws and keep
  only the histogram and the percentiles, which is what keeps a result in kilobytes.

## Two keys beyond the original encargo

- **`tab["note"]`** — the paragraph a tab opens with. The contract puts every sentence in a
  block's `note`, but a tab's own framing ("the same trades in another order: profit cannot
  move, drawdown can") belongs to no single block.
- **`result["summary"]`** — the flat numbers one strategy contributes to its population's
  table and `verdict.csv`. Without it the population step would re-derive them from the blocks.

A distribution's `band` may be `[null, null]` when the module kept only one percentile, and
its optional `mark` names the line at `real` when that line is not a real run (the CSCV marks
the median, 0).

## Why the override refuses a change of type

`2e4` is a string to YAML. Typed into `global.n_sims`, the old loaders stored the string and the
study crashed three minutes later inside numpy. `config.apply` widens an int into a float and
refuses every other change of type at the command line.
