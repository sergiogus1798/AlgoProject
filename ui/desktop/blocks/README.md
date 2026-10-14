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
| `axis.py` | The geometry of a chart: round ticks, data-to-pixel maps and paths through the points. | imported | — |
| `bars.py` | The bars block: one bar per item, coloured by its state, with its error and a reference — horizontal, or columns over their labels. | imported | block → QWidget |
| `callout.py` | The callout block: one coloured sentence the study wants seen, not read past. | imported | block → QWidget |
| `card.py` | The frame every block sits in: its title, its explanation, then what it draws. | imported | block, widgets → QFrame |
| `chart.py` | The painting ground every chart block shares: the canvas, its axes, its numbers and its key. | imported | — |
| `cone.py` | The cone block: the simulated equity bands, the real curve on top and where the OOS starts. | imported | block → QWidget |
| `density.py` | A distribution with several samples: each one a density on the same bins, a toggle per sample, the shift beside. | imported | block → QWidget |
| `desclist.py` | The list block: a title in bold and a short description under it, one item after another. | imported | block → QWidget |
| `distribution.py` | The distribution block: the null's histogram, its band, its median and the real value marked — or several samples as densities. | imported | block → QWidget |
| `fuse.py` | A partial re-run laid into the stored result it belongs to: its tagged blocks replace their twins, the rest stays. | imported | stored, partial → result |
| `grid.py` | The grid block: a heat map on a discrete scale, every cell labelled, θ₀ marked, the scale's key beneath. | imported | block → QWidget |
| `head.py` | The top of a result: its verdict, the line saying when and under what it was computed, the stale banner. | imported | result, meta → QWidget |
| `kinds.py` | Which widget draws which block kind, and the one call every view makes to draw a block. | imported | block → QWidget |
| `lines.py` | The lines block: several series over one x axis, each in the colour of its role. | imported | block → QWidget |
| `markets.py` | Grids that differ only in their market, laid side by side (2-3 chosen), with the consensus grid under them. | imported | tab, chosen, pool → row |
| `pick.py` | Which stored blocks the chosen selector values pick, and which block sits beside which: filters, never recomputes. | imported | tab, chosen → blocks |
| `result.py` | The whole of one study result, or two side by side: verdict, staleness, tabs, warnings, glossary. | imported | result dict(s) → page |
| `scatter.py` | The scatter block: points by group, the quadrants through zero and the fitted line if any. | imported | block → QWidget |
| `screen.py` | The result as it stands on screen: each tab reduced to the blocks drawn, its choices written in its note. | imported | result, memory → result |
| `shade.py` | The sign shade of a histogram: faint red behind the negative side of the x axis, faint green behind the positive. | imported | painter, box, x map → paint |
| `states.py` | Every colour a block is painted in: the contract states, the series and the heat scales. | imported | state → hex, label |
| `table.py` | The table block: sortable, numbers printed the window's way, every cell's full text on hover. | imported | block → QWidget |
| `tabpage.py` | One contract tab, in one column or beside its counterpart: its note, its selectors, its blocks. | imported | tab(s) → page |
| `tools.py` | Above a result: the report of what is on screen, and the partial re-runs kept beside the stored result. | imported | results → sentence · strip |
| `verdict.py` | The verdict block: the label in its state's colour, never alone, with its meaning and its parts. | imported | block → QWidget |

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
- **A tab is as tall as its own page.** `QTabWidget.sizeHint()` and the stack's height-for-width
  take the maximum over every page whatever its size policy (`Ignored` did nothing), so each page
  sits in a `tabpage.Slot` that asks for zero size while its tab is not the current one.
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
- **Warnings sit at the top now, highlighted ones first** (2026-09-30, feedback §1): `_warnings`
  splits into a study's `highlight: true` warnings (bigger, bolder, drawn right after the
  header) and the rest, folded behind a count as before. `ResultView._build` draws them before
  the tabs, not after — a hueco below a short tab used to sit between the tab and the warnings.
- **A tab's height is its own, not its `QTabWidget`'s.** `TabPage` and the `QTabWidget` that
  holds it are both pinned to `QSizePolicy.Minimum` on the vertical axis (2026-09-30): left at
  Qt's default `Expanding`, either one grabs the leftover space the page's own trailing
  stretch was meant to hold, and a short tab shows a blank gap instead of the glossary
  starting right under it.
- **A number's unit goes through `chart.num`/`numbers.num`, not string concatenation**
  (2026-09-30): only that path applies the one-decimal rule for `%`. Every block file routes
  its unit-bearing figures this way now; a new one should too.
