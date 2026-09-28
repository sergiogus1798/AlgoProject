# ui/desktop/datazone — «Datos»: the data root, each asset's bars, and its step-4 studies

The BIBLIOTECA zone of encargo 22 §8.3 (plan 24 front F10, a zone of its own: §10 Q16). It reads
nothing: every figure comes from `ui/daemon/data/` over HTTP, through `studypage.net.fetch`, which
turns a dead daemon into a sentence. `DataZone` is the class the sidebar wires.

```
DataZone ─▶ asset picker (data/assets) · tabs, each fetched on first opening for that asset
          ├ Catálogo          ─▶ tree.build (data/catalogue)
          ├ Velas             ─▶ pages.BarsPage ─▶ candles.canvas (data/bars)
          ├ Spread real       ─▶ pages.StudyPage ─▶ blocks/ResultView (data/spread, part=spread)
          ├ Banda del spread  ─▶ pages.StudyPage ─▶ blocks/ResultView (data/spread, part=band)
          └ Calidad del feed  ─▶ pages.StudyPage ─▶ blocks/ResultView (data/feedquality)
```

**Imports from:** `ui/desktop/blocks` (`ResultView`, `chart`, `axis`, `card`, `states`), `ui/desktop/studypage/net`, `glossary`, `numbers`, `theme` · **Consumed by:** `ui/desktop/shell` (wired by the sidebar's owner)

| file | what it does | run it | in → out |
|---|---|---|---|
| `__init__.py` | Package marker, one docstring | imported | — |
| `zone.py` | `DataZone(QFrame term)`: the kicker, the root's total, the asset picker with its one-line facts, the five tabs; `open(symbol, tab)` for a launcher | imported | routes → zone |
| `tree.py` | The catalogue as a tree nested by path, biggest first at each level; sizes in B/KB/MB/GB; a stale date in amber; the command of a branch's own manifest on hover | imported | catalogue → QTreeWidget |
| `pages.py` | `BarsPage` (timeframe and period pickers, the head line, the chart and its key) and `StudyPage` (one step-4 report in a `ResultView`) | imported | asset → page |
| `candles.py` | The price painter: candles (blue up, orange down) when every bar gets 3 px, otherwise each pixel column's high–low range and its last close; hover per candle or column | imported | bars → Canvas |
| `preview.py` | The zone alone in a window until the sidebar wires it; `--shot DIR` saves every tab as a PNG | `python3 -m ui.desktop.datazone.preview [--asset S] [--tab T] [--shot DIR]` | daemon → window · PNGs |

## Contracts and traps

- **Candles are blue and orange, never green and red**: those two are verdict colours in this
  window (`blocks/states.py`), and the trade gallery already marks entry and exit that way.
- **A tab is fetched once per asset**, on first opening; choosing another asset marks the asset
  tabs to fetch again and leaves the catalogue alone. A whole-history H1 is 7.7 MB: nothing is
  fetched that the reader did not open.
- **The studies are shown as their study wrote them.** The zone adds one line saying which file it
  read; the verdict, the tabs and the glossary are the study's.
