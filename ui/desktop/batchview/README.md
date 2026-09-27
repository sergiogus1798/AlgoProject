# ui/desktop/batchview — «Lote»: a variant batch in parallel coordinates

One vertical axis per parameter that varies and a last axis for the outcome; one line per variant
coloured by `NetProfit (oos1)` — or `NetProfit (build)` from the selector — on a nine-step
discrete scale; the mother dashed in the brightest ink. Whether the good variants form a band
(plateau) or a single line (peak) is read off the picture. Reads nothing: it asks `/api/batch`.

**Imports from:** `ui/desktop/client`, `ui/desktop/blocks` (`chart`, `axis`, `states`), `ui/desktop/theme` ·
**Consumed by:** the strategy page, as the tab «Lote» (wired by the integrator)

| file | what it does | run it | in → out |
|---|---|---|---|
| `tab.py` | `BatchTab(QFrame "term")`: `load(project, strategy) -> has_batch`, `show_batch(data)`; the note, the colour selector, the chart and its key. `has_batch(project, strategy)` for the page to decide whether to show the tab | imported | /api/batch → page |
| `parallel.py` | `Parallel`: the painted chart — lines cached in a pixmap, the one under the pointer lit and explained on hover | imported | batch dict → QWidget |
| `scale.py` | The discrete outcome scale: nine round, equal steps symmetric about zero (`blocks.states.DIVERGING`), and its key with counts | imported | values → colours |

Test: `python3 tests/test_ui_batch.py` (route in-process, view offscreen, writes
`scratch/ui-plan/shots/K-batch.png`).

## Contracts and traps

- **Never name an attribute `metric` on a Qt widget.** `QPaintDevice.metric()` is a virtual that
  Qt calls from `devicePixelRatioF()`; an instance attribute of that name shadows it and the
  process segfaults at the first paint.
- **The lines are painted once.** A few thousand polylines repainted on every mouse move stall
  the pointer; they go into a pixmap on data, selector or size change, and hover paints only the
  lit line over it.
- **Worst first, best on top.** Lines are drawn in ascending outcome so the gainers are the ones
  the eye sees where lines pile; the mother goes last with a dark halo and a dot on every axis.
- **The scale is symmetric about zero on purpose**: the pale middle step holds zero, so red is
  always a loss and blue always a gain, whichever outcome is selected.
