---
q: arch StepM ValueError zero-size array to reduction operation maximum, StepM crashes, small K, every column named, Romano Wolf step-down, superior.stepm
tag: 🔬  date: 2026-09-26  see: research/post-selection-bias
---
# arch 7.2.0's StepM raises when its rounds name every column — use engines' own step-down
`StepM.compute` loops while the LAST round named fewer than K, not all rounds together: when one
round names some and the next names the rest, it runs the SPA on zero columns and raises
`zero-size array to reduction operation maximum`. Never at K = 200; routinely at K of 2–5. Use
`engines.inference.snooping.superior.stepm`, the same step-down written on `arch`'s `SPA` (fresh
SPA per round, same seed so same draws), never `arch.bootstrap.StepM` directly.

## Evidence
- `arch/bootstrap/multiple_comparison.py` `StepM.compute`: `while better_models and (len(better_models) < self.k)`.
- Reproduced: `tests/test_blindjoint.py` noise seed 17, K = 4, block 1 — all four excesses positive
  because buy and hold's realised path is common to every column.
- Equivalence: 80 panels of `tests/test_snooping.noise` with 0/1/5/15 planted edges, reps 300 —
  identical sets in 80 of 80 (41 non-empty); `tests/test_snooping.py` still 0/20 and 20/20.
