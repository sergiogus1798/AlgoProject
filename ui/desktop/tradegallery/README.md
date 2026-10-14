# ui/desktop/tradegallery — five trades on their bars, never the best one alone

The «Operaciones» sub-tab of the Estrategia «Ficha» (order item 6, 2026-09-27). It reads
nothing: it asks `GET /api/tearsheet/trades` (`ui/daemon/tearmarket/`) and paints the five tiles.

```
TradeGallery.load(project, databank, identity, sample) ─▶ fetch("tearsheet/trades") ─▶ tile × 5
tile ─▶ price.canvas (blocks.chart.Canvas + blocks.axis) · figures with hover sentences
```

**Imports from:** `ui/desktop/blocks` (`chart`, `axis`, `card`, `states`), `ui/desktop/studypage/net` (the never-raising fetch), `ui/desktop/theme` · **Consumed by:** `ui/desktop/studypage` (Ficha › Operaciones, imported lazily by H1)

| file | what it does | run it | in → out |
|---|---|---|---|
| `__init__.py` | The trade gallery of the Ficha: five trades by P&L quantile, or five at random with the seed shown. | imported | — |
| `gallery.py` | `TradeGallery`: five trades of one sample, by P&L quantile or drawn with a shown seed — never the best alone. | imported | route → widget |
| `price.py` | The price painter of one trade: bar ranges, the close line, the entry and exit marked, on `chart.Canvas`. | imported | tile dict → Canvas |
| `tile.py` | One tile of the gallery: the trade's price window and its figures, each with the sentence of what it counts. | imported | tile dict → QFrame |

Test: `python3 tests/test_ui_tearmarket.py` (routes in-process, gallery offscreen, grabs in
`scratch/ui-plan/shots/H2-*.png`).

## Contracts and traps

- **No control shows the best trade alone** (Tharp/Eckhardt). The two picks are the five P&L
  quantiles 0/25/50/75/100 % or five at random; the seed is printed and a seed redraws the same five.
- **Entry and exit are blue and orange**, never green and red: those are verdict colours
  (`blocks/states.py`). The P&L figure is plain ink for the same reason.
- **A trade whose bars are missing** (asset or feed unknown, or outside what the window may show)
  keeps its tile and figures; the chart is replaced by the daemon's sentence.
- **Switching IS/OOS keeps the pick**: a random pick keeps its seed, which then draws other
  trades (another sample, another list).
- `fetch` is injectable (`TradeGallery(fetch)`) so the test answers in-process; in the window it
  is `studypage.net.fetch`, which turns a dead daemon into a sentence.
