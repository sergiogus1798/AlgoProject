# retest/render — how is all of that read?

The presentation layer. It owns every word the owner sees and **not one number**. Anything here
that computed a value would be a second source of truth for it, and the day the panel and the
report disagreed one of them would be lying.

**Imports from:** `inputs/` for the task names · **Consumed by:** `../report.py`, `explorer/`
**Must not contain:** a statistic, a threshold, or a decision

| file | what it does | run it | in → out |
|---|---|---|---|
| `svg.py` | The drawing primitives every figure shares: canvas, axes, number format, legend | imported | value → pixels |
| `charts.py` | The three figures: what a task cost in control sigmas, the outcome of its re-runs, and the equity envelope | imported | arrays → SVG |
| `panel.py` | Assembles the page: the shell, the tables and one section per strategy | imported | result → HTML |
| `panel.html` | The page shell — self-contained, no scripts, no fonts, no network | template | — |
| `text.py` | The Spanish sentence behind every veto, every task and every verdict tier | imported | flag → sentence |

## Contracts and traps

- **`svg.py` is copied from `monteCarlo/render/`, not shared.** `strategies/CLAUDE.md` says a
  helper two studies need is copied and promoted to `core/` when a third one wants it. The palette
  differs anyway: there the simulations are reshuffles of real trades, here they are complete
  re-runs and the mark is the unperturbed backtest.
- **The equity fan's x-axis is progress from 0 to 1, not the trade index**, and no real curve is
  drawn over it. Every re-run has its own trade count — 676 to 2,031 measured — so there is no
  common index to stack them on, and the unperturbed backtest would be a further length rather
  than a reference.
- **A negative bar in the cost figure is not an error.** Some tasks *improve* the median; clipping
  that to zero would hide a strategy sitting off its own optimum.
- **The page is self-contained.** No script, no font, no network call: it has to open from a USB
  stick in five years. The panel's own `page.html` is the only place JavaScript lives.

- **`SENTENCES` must cover `gates.VETOES` exactly, and `report.py` asserts it at start-up.** A
  veto that fires with no words attached is a verdict nobody can argue with; a sentence with no
  veto behind it is a claim the code cannot make. The assertion is a symmetric difference, so both
  directions fail.
- **`PERTURBA` mirrors `tasks.PERTURBS` in Spanish, on purpose.** The English table is the contract
  the code reasons about and is printed beside the numbers in provenance; this one is the sentence
  the owner reads. Keeping them apart is what stops English leaking into a Spanish report, which it
  did on the first render.
- **`gates` decides and this narrates.** The split is the reason a threshold can be argued with:
  the number, the limit and the words that explain it come from three different places.
