# wfm/model — when each cell runs

| file | what it does | in → out |
|---|---|---|
| `windows.py` | The shape of each cell's windows: their lengths, their overlap and the dates its runs cover. | steps → one row per (strategy, cell) |

`run.covered` turns `covers_from`/`covers_to` into the years of each segment a cell's runs reach:
a cell's first out-of-sample run starts years into `build`, so its excess per year in `build` is
divided by what it covered, not by the segment.

The 30 cells re-split one history and are near copies of each other: 1.4 to 4.1 effective cells on
the reference export (`measure/levels.effective`). Nothing here or downstream counts cells as trials.
