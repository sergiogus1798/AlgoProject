# perf/render — the page

| file | what it does | run it | in → out |
|---|---|---|---|
| `panel.py` | assembles the catalogue page and writes it beside the history | `python3 -m perf.render.panel` | the CSVs → `rendimiento.html` |
| `charts.py` | the five figures, each carrying the sentence that says how to read it | imported | frames → figures |
| `svg.py` | the drawing primitives: the canvas, the horizontal bar, the curve | imported | numbers → SVG |
| `page.html` | the shell, shared with the other panels of the project | read | — |

Self-contained: no scripts, no fonts, no network. It has to open from a USB stick in five years.

**Every figure carries its reading instruction.** A figure whose caption does not say what to look
at is decoration, and this page exists to support decisions about where to spend engineering time.
