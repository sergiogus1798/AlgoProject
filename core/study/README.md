# core/study — the contract every study module speaks

A study (`studies/…`, `portfolio/common/monteCarlo`) computes; this folder only says **what shape
its answer takes** so the desktop window and the batch report read one structure and cannot
disagree. It analyses nothing. The contract itself is `docs/encargos/19-contrato-de-datos-para-la-ventana.md`
§2–§3; `studies/CLAUDE.md` says how a module is laid out around it.

| file | what it does | run it | in → out |
|---|---|---|---|
| `__init__.py` | Names what the package is; holds no code | — | — |
| `config.py` | A module's `config.yaml` read, `--set section.key=value` applied with the type of the value it replaces, and the config's fingerprint | imported | YAML + overrides → dict, hash |
| `blocks.py` | The eight block kinds, the five state words, builders for the two that aggregate raw draws (`distribution`, `cone`) plus `table` and `verdict`, and the validator that refuses anything else | imported | numbers → blocks |
| `result.py` | The envelope of one result — module, strategy, identity, config hash, tabs, warnings, glossary — validated on the way out, and the `PROGRESS` line | imported | tabs → result dict |
| `verdicts.py` | A population verdict: `verdict.csv` with `strategy`, `identity`, `verdict`, and the manifest naming the absolute input it judged | imported | frame → CSV + manifest |
| `identity.py` | The identity of a strategy an export only names, read from its `.sqx` on the master or a worker | imported | names → hashes |
| `render/` | The result dict drawn as a self-contained HTML page, one drawer per kind | imported | result → HTML |

## Three rules the validator enforces

- **Eight kinds, no ninth.** A module that needs a new drawing asks first: the window has one
  widget per kind and a new kind is a new widget.
- **Five state words** — `pass`, `fail`, `watch`, `info`, `none`. A module's own words
  (MANTENER, worth_it) belong in `verdict.csv`, which is for `/curate`, not in a block.
- **Aggregated, never raw.** `blocks.distribution` and `blocks.cone` take the draws and keep
  only the histogram and the percentiles, which is what keeps a result in kilobytes.

## Two keys beyond the encargo's §3

- **`tab["note"]`** — the paragraph a tab opens with. The contract puts every sentence in a
  block's `note`, but a tab's own framing ("the same trades in another order: profit cannot
  move, drawdown can") belongs to no single block.
- **`result["summary"]`** — the flat numbers one strategy contributes to its population's
  table and `verdict.csv`. Without it the population step would re-derive them from the blocks.

A distribution's `band` may be `[null, null]` when the module kept only one percentile.

## Why the override refuses a change of type

`2e4` is a string to YAML. Typed into `global.n_sims`, the old loaders stored the string and the
study crashed three minutes later inside numpy. `config.apply` widens an int into a float and
refuses every other change of type at the command line.
