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
| `brief.py` | Why a button is off, in a few plain words; the full sentences go in its tooltip. | imported | reasons → words |
| `buttonhelp.py` | What every button of the window does, in one or two Spanish sentences, found by its text. | imported | text → sentence |
| `buttonhelp_texts.py` | The registry of button sentences, keyed by the button text as the window shows it. | imported | — |
| `columnhelp.py` | The «?» and the short header of every column the databank tables show: `help_for`, `label_for`. | imported | column → sentence, header |
| `columnhelp_closing.py` | The «?» of the closing studies' columns: exposure's fixed fields and the family that comes one column per buy-and-hold sizing. | imported | field → sentence |
| `columnhelp_criteria.py` | The «?» and the header of the criteria-metric columns (owner, 2026-10-04: computed, shown, no threshold). | imported | (study, field) → header, sentence |
| `columnhelp_fields.py` | The «?» of every study column that is not a verdict and not a family, keyed (study, field). | imported | — |
| `columnhelp_metrics.py` | The «?» of every SQX metric column, keyed by the metric's name without its sample suffix. | imported | — |
| `columnhelp_steps.py` | The «?» of the study columns of steps 18, 18.5 and 19 (CSCV, market surfaces, WFM), keyed (study, field). | imported | — |
| `columnhelp_tf.py` | The columns of the cross-TF «isolated peak» reading (`tf_*`, encargo 47): header and «?» of each, as the study writes them. | imported | field → header, sentence |
| `columnhelp_verdicts.py` | The «?» of every study's verdict column: the question it answers and what its words mean. | imported | — |
| `glossary.py` | The one glossary of visible labels: a key a module writes → the Spanish words the window shows. | imported | key → label |
| `glossary_crossmarket.py` | The Spanish words for cross-market's verdict.csv columns («¿la lógica viaja?», encargo 46). | imported | key → label |
| `glossary_gate.py` | The gate's facts and knobs in words (encargo 44): the funnel's rules and the Configuración SQX values. | imported | key → label |
| `glossary_steps.py` | The facts and knobs of steps 17-19 (WFC, CSCV, market surfaces, WFM) in words, as the Criterios zone and the drawers read them. | imported | key → label |
| `numbers.py` | The one way the window prints a number: never scientific, thousands grouped, K and M when large. | imported | value → text |
| `verdictwords.py` | A study's English or lowercase verdict words, in Spanish for the databank table. | imported by the databank table's model | word → word |

## Contracts and traps

- **Nothing here may import Qt or a daemon module.** Both processes load it; a Qt import would
  pull PySide6 into the daemon, which must never hold a widget.
- **A key is never renamed, only appended.** Other sessions' views look labels up by key; a
  renamed key silently falls back to the humanised identifier.
