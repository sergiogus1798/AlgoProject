# ui/text — the words and the figures, for both sides of the window

Pure-Python modules (no Qt, no FastAPI, no file read) that the window **and** the daemon
import: the daemon writes some sentences the window shows as they come (the filters' funnel
reasons, the pulse line), and they must read exactly as the window's own. They lived in
`ui/desktop/` until F13 of plan 24; a daemon importing `ui.desktop` broke the rule that the
daemon never imports the window, so they moved here.

**Imports from:** the standard library only · **Consumed by:** `ui/desktop/` (every zone; `helpmark` reads `buttonhelp`),
`ui/daemon/filters/api.py`, `ui/daemon/ops/pulse.py`

| file | what it does | run it | in → out |
|---|---|---|---|
| `glossary.py` | The one glossary of visible labels: `label(key)` → the Spanish words, initial capital; an unknown identifier (`null.chunk3_traits`) is humanised, never shown raw. New keys are appended at the end of `LABELS`. `knob(key)` labels a config knob part by part (`knob.<part>` first): «Nulos › Corridas», never `nulls.draws` | imported | key → label |
| `glossary_crossmarket.py` | The Spanish labels of cross-market's verdict.csv columns (P1-P9), merged into `glossary.LABELS` | imported | key → label |
| `glossary_gate.py` | The Spanish labels of the gate's facts (a funnel rule reads «fact + pass line») and of its config knobs in Configuración SQX (`sqx.` keys), merged into `glossary.LABELS` | imported | key → label |
| `verdictwords.py` | `verdict_word(v)`: a study's raw verdict word (`fails`, `pass`, `blind`) in Spanish, sentence case; any other value unchanged | imported by the databank table's model | word → word |
| `buttonhelp.py` | What every button does: `help_for(text, scopes)` finds the sentence by the button's text, `normalise`d (no ▶ ↻ × signs, no «(3)» or «17-19» counts, no «quoted» names, lower case); a «Clase › texto» entry wins for a button inside that class | imported | text → sentence |
| `buttonhelp_texts.py` | The registry itself, `HELP`: one or two Spanish sentences per button text, grounded in what its slot does — whether it writes, whether it asks first, whether it touches SQX | imported | — |
| `brief.py` | Why a button is off, in a few plain words (owner, 2026-09-30: «no me pongas un textaco»): `brief(reasons)` → «el workflow ya está corriendo» when any reason says SQX is busy (`BUSY`), a known case's plain words (`KNOWN`), else the first sentence cut under 60 characters; `off` prefixes «No disponible: », `line` capitalises, `full` is every reason one per line for the tooltip | imported | reasons → words |
| `numbers.py` | The one number formatter: `exact(float)` (shortest digits, never scientific) and `num(value, unit="")` — never scientific, thousands split by a space, «K»/«M» from 100 000, `unit="p"` prints a p-value as 0.0123 or «< 0.0001» | imported | value → text |
| `columnhelp.py` | The «?» and the short header of every databank-table column: `help_for(kind, study, field)` (kind "metric" with the SQX name, sample suffix optional; or "study" with the catalogue key and field, "verdict" for its verdict) and `label_for(study, field)` (≤ 22 characters, None → `glossary.label`); `METRICS`, `STUDY`, `LABEL`, and the atrCalculator percentile / exposure sizing families by pattern; an unknown column returns None, never a guess | imported | column → sentence, header |
| `columnhelp_metrics.py` | `METRICS`: one sentence per SQX metric, from the snippet SQX computes it with (`internal/extend/Snippets/SQ/Columns/Databanks/`) or the project's own columns (PSR, TRL Ratio, DoF Ratio, Param Count) | imported | — |
| `columnhelp_verdicts.py` | `VERDICTS`: per study, the question it answers and what each verdict word the window shows means | imported | — |
| `columnhelp_fields.py` | `FIELDS`: (study, field) → sentence for every non-family study column, grounded in the code that writes it | imported | — |
| `columnhelp_closing.py` | exposure's fixed fields and the two families — `bench_<sizing>_<stat>`, `strat_<stat>`, `lots_<sizing>`, atrCalculator's `<kind>_p<N>` and `n_winners_<segment>` — resolved by regex | imported | field → sentence |
| `columnhelp_criteria.py` | The criteria-metric columns of spp, wfc, mcRetest and marketSurfaces (owner, 2026-10-04: computed and shown, no threshold), resolved by pattern — `criteria(study, field)` → (header of at most 22 characters, sentence saying what it is, how to read it, and whether it is offered or a diagnostic) | imported | (study, field) → header, sentence |
| `columnhelp_tf.py` | `TF`: header (≤ 22 characters) and «?» of the cross-TF `tf_*` columns of the T0-T4 reading (encargo 47), beside the old columns and marked «sin cortar» | imported | field → header, sentence |

## Contracts and traps

- **Nothing here may import Qt or a daemon module.** Both processes load it; a Qt import would
  pull PySide6 into the daemon, which must never hold a widget.
- **A key is never renamed, only appended.** Other sessions' views look labels up by key; a
  renamed key silently falls back to the humanised identifier.
