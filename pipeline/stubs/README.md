# pipeline/stubs — what stands in for the modules that are not built yet

Five of the seven stages have no module behind them: variant design, fabrication, execution,
collection and walk forward correlation are being written elsewhere. Their rows in `recipe.yaml`
point here so the chain runs end to end today, which is what makes the resumption and progress
tests real rather than a description of an intention.

| file | what it does | run it | in → out |
|---|---|---|---|
| `placeholder.py` | reports progress like a real stage, then writes an invented output | `python3 -m pipeline.stubs.placeholder --stage build --work DIR` | nothing → `<work>/<stage>.json` |

⚠️ **Every number it writes is invented**, and the file it writes says `"placeholder": true` so
nothing downstream can mistake it for a measurement. The `collected` stage additionally writes a
real, tiny export and a real, tiny folder of variants, so the sweep in `pipeline/cleanup.py` is
exercised against something that is actually on disk.

Wiring a real module in is editing `command` and `produces` on its row in `recipe.yaml` — the line
it becomes is written in the comment above each one. Nothing in this folder is imported by
anything; deleting it once all five exist is a clean removal.
