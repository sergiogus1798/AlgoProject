# ui/desktop/blocks — one widget per contract block kind, and the page that holds them

Every study returns the contract of `core/study/CONTRACT.md`; this package draws it natively.
Eight kinds, eight modules, one `draw()`, and `ResultView` for a whole result or two compared.
It reads nothing: a view fetches the result from the daemon and hands the dict in.

```
ResultView ─▶ verdict (header) · stale banner · QTabWidget ─▶ TabPage ─▶ kinds.draw ─▶ <kind>.widget
                                                               └ shown() / pairs(): filter, never recompute
<kind>.widget ─▶ card (title + note) ─▶ chart.Canvas (paint + hover) · chart.key · axis
```

**Imports from:** `ui/desktop/theme` · **Consumed by:** `ui/desktop/studypage` (wave 2), and any view drawing a study result

| file | what it does | run it | in → out |
|---|---|---|---|
| `states.py` | Every colour a block is painted in: the contract states, the series and the heat scales | imported | state → hex, label |
| `kinds.py` | `WIDGETS = {kind: widget}` and `draw(block)`, which turns an unknown or broken block into a red line | imported | block → QWidget |
| `result.py` | `ResultView`: `show(result, meta)` and `compare(left, right, titles)` — verdict, stale banner, tabs, warnings, glossary | imported | result dict(s) → page |
| `tabpage.py` | One tab: its note, its selector combos, its blocks in one column or beside their counterparts | imported | tab(s) → page |
| `card.py` | The frame of a block: its own title and note above the drawing | imported | block, widgets → QFrame |
| `chart.py` | The painting ground: `Canvas` (paint + hover tooltip), axes, number format, the key under a chart | imported | — |
| `axis.py` | Round ticks, data-to-pixel maps, x placement of numbers vs labels, paths broken at gaps | imported | — |
| `distribution.py` | Histogram, band shaded, median dashed, real value marked, headline figures, percentile row | imported | block → QWidget |
| `cone.py` | Percentile bands filled, median dashed, real curve on top, the OOS split | imported | block → QWidget |
| `grid.py` | Heat map on a discrete scale (`levels`), every cell labelled, the scale's key beneath | imported | block → QWidget |
| `scatter.py` | Points by group, quadrants through zero, fitted line with its r | imported | block → QWidget |
| `bars.py` | Horizontal bars coloured by state, error whiskers, reference line, value past the whisker | imported | block → QWidget |
| `lines.py` | Series over one x axis: a lone real series in the real ink, references dashed | imported | block → QWidget |
| `table.py` | Sortable table in the study's own order, numbers the window's way, full cell on hover | imported | block → QWidget |
| `verdict.py` | The label in its state's colour, never without its meaning, and its parts as tiles | imported | block → QWidget |

Test: `python3 tests/test_ui_blocks.py` draws every population result and three strategy results
per study under `AlgoData/reports/`, offscreen, in ~3 s.

## Contracts and traps

- **The window invents no text about the data.** Each block shows its `title` and `note` as the
  study wrote them. What the window adds is the key, the hover sentence and the percentile row —
  they say what a mark is, never what it means for the strategy. The distribution's key says
  «distribución», not «simulaciones»: the snooping screen puts 200 real strategies in one.
- **Selectors filter, they never recompute.** `tabpage.shown` keeps the untagged blocks and
  those whose every `select` value is chosen, compared as text (a combo hands back text, the JSON
  may hold a number). In a comparison, a value one side does not offer falls back to that side's
  default — two WFM runs over different strategies still both draw.
- **`ResultView.show` keeps Qt's `show()`.** The spec names the method `show(result, meta)`,
  which hides `QWidget.show`; called with no arguments it forwards to Qt. `show_result` is the
  same thing with an unambiguous name.
- **Pages are built on first opening.** A population result holds hundreds of tables; building
  every tab up front paid for tabs nobody opened. The tab and the selector values are remembered
  across `show` calls, so stepping through strategies keeps the reader on the same drawing.
- **A tab is as tall as its own page.** A `QStackedWidget` takes the height of its tallest page;
  the others are set `Ignored` so a short tab does not sit on the blank height of a long one.
- **`deleteLater` is not immediate.** A replaced body is hidden first: until the event loop
  runs it still paints, and did, over the selectors.
- **Diverging runs red (low) to blue (high).** The static pages (`core/study/render/grids.py`)
  run blue to red; on this dark window a high red cell next to the red of «falla» read as a
  failure. No study note names a diverging colour (checked 2026-09-26), so the notes stay true.
- **Repeated `levels` are legal.** `blindJoint` writes three states as eight cuts; the empty
  steps are left out of the key.
- **Grids are sized to their rows**, not to the 320 px floor the other charts keep: two rows
  stretched to 320 px read as a colour field, and blank space under a short map read as missing
  rows.
- **Identical warnings are counted, not repeated.** A population raises one sentence per
  strategy; `×N` in front, the first eight shown and the rest behind a button. None is dropped.
- **A cone with no real curve says so** in its key: `mcRetest` stores `real` as all `None`.
