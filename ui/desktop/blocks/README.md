# ui/desktop/blocks — one widget per contract block kind, and the page that holds them

Every study returns the contract of `core/study/CONTRACT.md`; this package draws it natively.
Eight kinds, eight modules, one `draw()`, and `ResultView` for a whole result or two compared.
It reads nothing: a view fetches the result from the daemon and hands the dict in.

```
ResultView ─▶ head (verdict, stamp, stale) · tools (report of the screen, partial re-runs)
           └ QTabWidget ─▶ TabPage ─▶ kinds.draw ─▶ <kind>.widget
                               ├ pick.shown() / pairs(): filter, never recompute
                               └ markets: per-market grids side by side + consensus
ResultView.beside / merged ─▶ compare(stored, partial) · fuse.merge(stored, partial)
tools.report ─▶ screen.screen(result, memory) ─▶ POST /api/study/screen ─▶ core.study.render
<kind>.widget ─▶ card (title + note) ─▶ chart.Canvas (paint + hover) · chart.key · axis
```

**Imports from:** `ui/desktop/theme`, `glossary`, `numbers`, `client` (the report button only) · **Consumed by:** `ui/desktop/studypage` (wave 2), and any view drawing a study result

| file | what it does | run it | in → out |
|---|---|---|---|
| `states.py` | Every colour a block is painted in: the contract states, the series and the heat scales | imported | state → hex, label |
| `kinds.py` | `WIDGETS = {kind: widget}` and `draw(block)`, which turns an unknown or broken block into a red line | imported | block → QWidget |
| `result.py` | `ResultView`: `show(result, meta)` and `compare(left, right, titles)` — verdict, stale banner, tabs, warnings, glossary | imported | result dict(s) → page |
| `tabpage.py` | One tab: its note, its selector combos (the market picker on a grouped tab), its blocks in one column or beside their counterparts | imported | tab(s) → page |
| `pick.py` | Pure: a tab's selectors (derived from the tags when a partial re-run writes none), the values picked, the blocks shown, the pairs of a comparison | imported | tab, chosen → blocks |
| `markets.py` | Grids differing only in `select.market`: 2-3 side by side (a toggle per market, a fourth lets go of the oldest) and the consensus grid of the same other picks under them | imported | tab, chosen, pool → row |
| `head.py` | A result's top: verdict, the stamp line, the red stale banner | imported | result, meta → QWidget |
| `tools.py` | The «Informe de lo que ves» button's call, and the strip of partial re-runs (al lado · fusionado · volver) | imported | results → sentence · strip |
| `screen.py` | Pure: a result cut down to what is drawn, selectors removed and the choices written in each tab's note | imported | result, memory → result |
| `fuse.py` | Pure: a partial re-run merged into its stored result — tagged blocks replace their twins, selectors gain the new values, verdict kept | imported | stored, partial → result |
| `card.py` | The frame of a block: its own title and note above the drawing | imported | block, widgets → QFrame |
| `chart.py` | The painting ground: `Canvas` (paint + hover tooltip), axes, number format, the key under a chart | imported | — |
| `axis.py` | Round ticks, data-to-pixel maps, x placement of numbers vs labels, paths broken at gaps | imported | — |
| `distribution.py` | Histogram, band shaded, median dashed, real value marked, headline figures, percentile row; hands a block with `series` to `density` | imported | block → QWidget |
| `density.py` | Several samples (IS, OOS) as densities on the same bins, a toggle per sample, n/median per sample and the median shift + KS p beside, the union's percentiles under | imported | block → QWidget |
| `cone.py` | Percentile bands filled, median dashed, real curve on top, the OOS split | imported | block → QWidget |
| `grid.py` | Heat map on a discrete scale (`levels`, else eight steps of `scale_range` or of its own range), θ₀ `mark` outlined, every cell labelled when it fits, the scale's key beneath | imported | block → QWidget |
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
- **Side by side only on a lone result.** A tab is grouped when it has a `market` selector and
  grids tagged with it (marketSurfaces' «rejillas»). The consensus grid lives in another tab,
  found in the whole result's blocks by the same tags minus the market. In a comparison the
  width goes to the two runs and the tab keeps its plain combo.
- **Shared scale comes from the data.** `scale_range` is written by the study over every market
  of a pair and segment; the widget only spans it. Without it each grid would colour its own
  range and three maps would not compare.
- **A partial re-run has no selectors.** monteCarlo's `_rerun` tags its blocks and writes none:
  `pick.selectors` derives them from the tags, or nothing would agree with a pick. «Al lado»
  sets the stored side's selectors to the partial's single values, so both show the same test.
- **The merge is on screen, never on disk.** `fuse.merge` replaces only tagged blocks; untagged
  ones (overview tables) describe the partial run alone and stay the stored ones, and so does
  the verdict. The first warning of a merged result says what came from where.
- **The report is the screen, not the defaults.** `screen.screen` keeps exactly the blocks
  drawn, empties `selectors` so `core.study.render.page` draws all it keeps, and writes the
  choices into each tab's note. The daemon writes it to `<study>/pantalla/`.
