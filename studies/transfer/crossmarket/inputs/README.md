# crossmarket/inputs — what is this study being run on?

The two declarations, and nothing computed from them: every tunable of the study, and which
markets exist and what they are called. A module here reads a `.yaml`, validates it against what
the export really carries, and hands back a plain dict.

**Imports from:** `core/` only
**Consumed by:** `travel/`, `load.py`, `many.py` and the two `.yaml` files in the module root
**Must not contain:** a statistic, a p-value, a threshold's *consequence* (that is `pipeline/autopilot/criteria.yaml`), or
anything that reads bars

| file | what it does | run it | in → out |
|---|---|---|---|
| `config.py` | The single source of truth for every tunable of the study; it computes nothing. | imported | overrides → config |
| `markets.py` | What the study runs on: the export says which markets exist, assets/ says what they are. | imported | asset + export → universe, OOS span |

## Where a threshold is changed

**Every tunable of this study is a key of `config.yaml`, and `config.py` is the only module that
reads it.** Nothing else opens the file, and no module holds a number the owner might want to move.
To change one: edit `config.yaml`, or pass `--set section.key=value` on the command line, or move it
in the panel's config drawer — the drawer is built from the config's keys plus one sentence per knob
in `tooltips.py`, so a new knob needs a row there too or it appears without its hover text.

What the knob then *does* is in `travel/`; the lines that judge P1-P9 are in `criteria.yaml`. A limit hard-coded in code would be a rule
nobody can find; it belongs in `config.yaml`.

## The `.yaml` files stay in the module root

`config.yaml` and `assets/_markets.yaml` sit **one level up**, beside `README.md`, because
`docs/manual/07-otros-mercados-y-timeframes.pdf` (cap. 05-retest-mercados) names them by that path. Each of the two modules resolves its
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
