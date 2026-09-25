# core/study/render — a result dict drawn as HTML

The batch report of every study is drawn here, from the same dict the window paints. Nothing in
this folder computes: it reads a validated result and writes markup. Self-contained pages — no
script, no font, no network.

| file | what it does | run it | in → out |
|---|---|---|---|
| `__init__.py` | Names what the package is; holds no code | — | — |
| `page.py` | The whole page: verdict, warnings, one section per tab, glossary, provenance footer; `body()` for embedding one result inside a batch page | imported | result → HTML |
| `markdown.py` | The same result as Markdown: tables and bars in full, a drawing by its numbers | imported | result → text |
| `figures.py` | The four drawings over a continuous axis: `distribution`, `cone`, `lines`, `bars` | imported | block → SVG |
| `grids.py` | The two over two axes: `grid` on a discrete scale, and `scatter` | imported | block → SVG |
| `tables.py` | `table` and `verdict` | imported | block → HTML |
| `svg.py` | Canvas, linear scales, round ticks, number format, legend chips | imported | numbers → SVG |
| `page.html` | The shell and its CSS; light and dark | — | — |

A block that belongs to a selector combination (`"select": {"market": …}`) is drawn with that
combination written above it: a static page cannot redraw, so it shows every combination in turn.
