# monteCarlo/render/families — one strategy's page, one file per family

The five families are the reading key of the whole study: each one isolates **one kind of luck** and
asks what the result would have been without it. One file renders one family, in the same order the
page presents them.

| family | the luck it isolates | the question |
|---|---|---|
| **A** — order | the sequence the trades arrived in | same trades, another order: how much worse could the drawdown have been? |
| **B** — composition | which trades occurred at all | resample the trades: was the result carried by a handful of them? |
| **C** — execution | how the trades were filled and charged | worse fills, worse costs, missed entries: how much of the edge survives? |
| **D** — regime | when in time and in what market state it lived | was the edge there in every window and every volatility tercile, or only in one? |
| **E** — significance | the sample itself | given N and the shape of the returns, could the true edge be zero? |

Split out of a single `familypage.py` once it passed 250 lines. `common.py` holds what every family
shares — the metric labels, `fmt()` and the mini-verdict header — so the five family files import
from it, never from `__init__.py`, which would be circular. `__init__.py` re-exports
`family_a`..`family_e` and `common`'s names, so callers use
`strategies.monteCarlo.render.families.family_a(...)` and `.fmt(...)` without knowing the split.

**Imports from:** `inputs/`, `model/`, `simulate/`, `verdict/`, and `render/`'s own figures
**Consumed by:** `render/strategypage.py` and `explorer/sections.py`
**Must not contain:** a calculation — a family section reads `result[...]`, it never recomputes it

| file | what it does | run it | in → out |
|---|---|---|---|
| `__init__.py` | Re-exports the five sections and `common`'s names | imported | — |
| `common.py` | The metric labels, `fmt()` and the shared family header | imported | metric → label, cell |
| `a_order.py` | Family A — order luck, with the equity cone | imported | result → HTML |
| `b_composition.py` | Family B — composition luck, and the IS/OOS level comparison | imported | result → HTML |
| `c_execution.py` | Family C — execution luck, the four stress tests against their floors | imported | result → HTML |
| `d_regime.py` | Family D — regime luck: calendar windows, volatility terciles, the two time series | imported | result → HTML |
| `e_significance.py` | Family E — significance, the PSR and its bootstrap cross-check | imported | result → HTML |

## Contracts and traps

- **The file name carries the family letter first** (`a_order`, `b_composition`, …) because the
  study, the config, the gates and the report all speak in letters. The word after it is what the
  letter means, so nobody has to open the file to find out.
- **A section renders whatever fired; it does not decide what fired.** The flags come from
  `verdict/gates.check()`, filtered by family. Adding a Family C model means adding it in
  `model/stress.py` and `verdict/gates.py`; `c_execution.py` picks it up from `stress.TITLES`
  without being edited.
