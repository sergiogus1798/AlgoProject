# ui/desktop/batchview — «Lote»: a variant batch in parallel coordinates

One vertical axis per parameter that varies and a last axis for the outcome; one line per variant
coloured by `NetProfit (oos1)` — or `NetProfit (build)` from the selector — on a nine-step
discrete scale; the mother dashed in the brightest ink. Whether the good variants form a band
(plateau) or a single line (peak) is read off the picture. Reads nothing: it asks `/api/batch`.

**Imports from:** `ui/desktop/client`, `ui/desktop/blocks` (`chart`, `axis`, `states`), `ui/desktop/theme` ·
**Consumed by:** `ui/desktop/studypage/page.py`, as a «Lote» tab beside the drawer — shown only
while the WFC study is open on a mother (owner, 2026-09-29: it left the Ficha, since a strategy
can have no batch)

| file | what it does | run it | in → out |
|---|---|---|---|
| `parallel.py` | The parallel-coordinates canvas: one axis per parameter plus the outcome, one line per variant. | imported | batch dict → QWidget |
| `scale.py` | The discrete colour scale of an outcome: nine round, equal steps symmetric about zero, and its key. | imported | values → colours |
| `tab.py` | «Lote»: one mother's variant batch in parallel coordinates, coloured by NetProfit build, oos1 or oos2. | imported | /api/batch → page |

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
