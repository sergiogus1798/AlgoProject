# ui/text — the words and the figures, for both sides of the window

Two pure-Python modules (no Qt, no FastAPI, no file read) that the window **and** the daemon
import: the daemon writes some sentences the window shows as they come (the filters' funnel
reasons, the pulse line), and they must read exactly as the window's own. They lived in
`ui/desktop/` until F13 of plan 24; a daemon importing `ui.desktop` broke the rule that the
daemon never imports the window, so they moved here.

**Imports from:** the standard library only · **Consumed by:** `ui/desktop/` (every zone),
`ui/daemon/filters/api.py`, `ui/daemon/ops/pulse.py`

| file | what it does | run it | in → out |
|---|---|---|---|
| `glossary.py` | The one glossary of visible labels: `label(key)` → the Spanish words, initial capital; an unknown identifier (`null.chunk3_traits`) is humanised, never shown raw. New keys are appended at the end of `LABELS`. `knob(key)` labels a config knob part by part (`knob.<part>` first): «Nulos › Corridas», never `nulls.draws` | imported | key → label |
| `numbers.py` | The one number formatter: `num(value, unit="")` — never scientific, thousands split by a space, «K»/«M» from 100 000, `unit="p"` prints a p-value as 0.0123 or «< 0.0001» | imported | value → text |

## Contracts and traps

- **Nothing here may import Qt or a daemon module.** Both processes load it; a Qt import would
  pull PySide6 into the daemon, which must never hold a widget.
- **A key is never renamed, only appended.** Other sessions' views look labels up by key; a
  renamed key silently falls back to the humanised identifier.
