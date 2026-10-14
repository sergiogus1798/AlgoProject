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
| `__init__.py` | «Datos»: the catalogue of the data root, each asset's bars, and its spread and feed-quality studies. | imported | — |
| `candles.py` | The price painter of one asset: candles when they fit, each pixel column's range and close when they do not. | imported | bars → Canvas |
| `pages.py` | The Datos zone's pages that depend on the asset: its bars, and one step-4 study read back as a ResultView. | imported | asset → page |
| `preview.py` | The Datos zone alone in a window, until the sidebar wires it; `--shot` saves each tab as a PNG and exits. | `python3 -m ui.desktop.datazone.preview [--asset S] [--tab T] [--shot DIR]` | daemon → window · PNGs |
| `tree.py` | The catalogue of the data root as a tree: each branch's files, formats, newest write and signed exports. | imported | catalogue → QTreeWidget |
| `zone.py` | The «Datos» zone: the catalogue of AlgoData, and per asset its bars, its real spread and its feed quality. | imported | routes → zone |

## Contracts and traps

- **Candles are blue and orange, never green and red**: those two are verdict colours in this
  window (`blocks/states.py`), and the trade gallery already marks entry and exit that way.
- **A tab is fetched once per asset**, on first opening; choosing another asset marks the asset
  tabs to fetch again and leaves the catalogue alone. A whole-history H1 is 7.7 MB: nothing is
  fetched that the reader did not open.
- **The studies are shown as their study wrote them.** The zone adds one line saying which file it
  read; the verdict, the tabs and the glossary are the study's.
