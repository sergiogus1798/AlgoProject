---
q: What throws or silently returns 0 when a Java snippet reads a strategy's statistics?
kw: StatsDontExistException, Result doesn't contain stats for, subResult stats Both Money, getDouble returns 0, absent key ParameterCount DoFRatio, NaN default, computeAllStats, AlgoBank stats pass
tag: 🔬  date: 2026-10-13  see: snippets-compile-on-start
---
# In a snippet, an absent statistic THROWS (`StatsDontExistException`) and an absent key reads as 0
Two traps. (1) `rg.subResult(key).stats(Both, Money, code)` throws `StatsDontExistException` for a
(result, sample) SQX never computed; it does not return null: catch it and skip the block. Never call
`computeAllStats()`: it writes into the strategy. (2) `stats.getDouble(name)` returns 0 for an absent
key (ParameterCount, DoFRatio, DataLength, MaxNewHighDuration* in some samples) where the disk has no
value: pass `getDouble(name, Double.NaN)`.

## Evidence
- 🔬 conductor, 2026-10-13, encargo 66 session 2: `sqx/snippets/Snippets/SQ/CustomAnalysis/AlgoBank.java`, v2 gave 0 where the
  `.sqx` block lacks the key; first run died with «Result doesn't contain stats for '2581' … D: 0, PL: 10, S: 21» (no `.abk`, SQX kept running).
  After both fixes 116 named keys equal on every bank.
