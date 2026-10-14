# core/study/render — a result dict drawn as HTML

The batch report of every study is drawn here, from the same dict the window paints. Nothing in
this folder computes: it reads a validated result and writes markup. Self-contained pages — no
script, no font, no network.

| file | what it does | run it | in → out |
|---|---|---|---|
| `__init__.py` | A study result drawn as a self-contained HTML page. | — | — |
| `figures.py` | The four drawings over a continuous axis: distribution (one sample or several overlaid), cone, lines and bars. | imported | block → SVG |
| `grids.py` | The two drawings over two axes: the heat grid and the scatter. | imported | block → SVG |
| `markdown.py` | A study result written as Markdown, for the .md report and for reading in a terminal. | imported | result → text |
| `page.py` | A study result drawn as a self-contained HTML page, from the result dict and nothing else. | imported | result → HTML |
| `svg.py` | The drawing primitives every figure shares: the canvas, the scales, the ticks and the legend. | imported | numbers → SVG |
| `tables.py` | The two blocks that are not drawings: the table and the verdict with its meaning. | imported | block → HTML |
| `page.html` | The shell and its CSS; light and dark | — | — |

A block that belongs to a selector combination (`"select": {"market": …}`) is drawn with that
combination written above it: a static page cannot redraw, so it shows every combination in turn.
