---
q: Can SQX blocks make a seeded random entry, and is the installed RAND block seeded?
kw: monkey test inside SQX, random entry custom block, RAND block WinRateEdge Math.random unseeded, seeded hash timestamp seed, XOR modulo bit shift in SQX vocabulary, Java snippet, RandomCondition runtime random, D3 encargo 12, encargo 30, always true block
tag: 🔬  date: 2026-10-12  see: sqx-format/rewriting-strategy-logic
---
# A seeded random entry exists as our own Java snippet; the RAND block on the master is unseeded
The block vocabulary composes only doubles and cannot hash `(bar time, seed)`; a Java snippet can.
«(RAND) Seeded Random Entry» (`sqx/snippets/`, `python3 -m sqx.snippets.install`) is true on a bar
when SplitMix64 of `Strategy.Time(0)` and `Seed` falls under `Probability` %: the same strategy
retested gives the same trades. Pseudocode only — a null is never exported. The WinRateEdge
«(RAND) Random Entry» on the **master only** is `Math.random()`, unseeded: every retest is a
fresh draw.

## Evidence
- `python3 -m sqx.inspect.vocabulary --role custodian <term>` on SQX_w2 (849 native + 175 own
  blocks), 2026-09-26: `xor`, `bit`, `hash`, `integer`, `Remainder` → nothing; `mod` matches only
  indicator names. Every `Values/Functions` block returns `pricenumber` (double).
- `RandomCondition`, `RandomValue`, `SameCondition`, `NegatedCondition` (`Random Conditions`) are the
  builder's template slots, filled at generation — not a runtime random draw. 🤔 inferred from their
  category and their use in templates; a retest of a strategy that keeps one would confirm.
- `AlwaysTrue` / `AlwaysFalse` exist (`Bar And Time`), but an ablation does not need them: deleting
  the `<Block>` is the neutralised condition (sqx-format/rewriting-strategy-logic).
- 🔬 `~/Desktop/SQX/user/extend/Snippets/SQ/Blocks/RandomEntry/RandomEntry.java`, dated
  2026-09-28, read that day: the body above, `Probability` 0.01–100 step 0.01, default 5. Absent from
  `SQX_w1` and `SQX_w2`. Source copy: `~/Downloads/codebase-strategy-vs-random-edge-testing-winrateedge-results-panel/RandomEntries-1.sxp`
  (its MT4/MT5 `.tpl` use `MathRand()`, EasyLanguage `Random(10000)`).
- 🤔 How SQX compiles a snippet copied into a worker's `user/extend/Snippets` without the GUI is
  untested; encargo 30 §5.2 checks it with `sqx.inspect.vocabulary --diff`.
- 🔬 conductor, 2026-10-12, `Test_XAUUSD_H1_seeded` (template `seededRandomLong`, live session): 6
  strategies built, OOS retested, databank cut, retested again — 183 to 320 trades each, the two
  trade lists byte-identical for all 6. The snippet compiled headless on a worker's start
  (sqx-drive/snippets-compile-on-start), which answers the open question above.

## Also
The block vocabulary composes only doubles, so it cannot build a seeded hash of `(bar time, seed)`.
A Java snippet can: «(RAND) Seeded Random Entry» (`sqx/snippets/…/SeededRandomEntry.java`,
installed by `python3 -m sqx.snippets.install`) is true on a bar when SplitMix64 of
`Strategy.Time(0)` and `Seed` falls under `Probability` % — the same strategy retested gives the
same trades, and another `Seed` another draw. It has pseudocode only, no MT4/MT5 template: a null
is never exported. The WinRateEdge «(RAND) Random Entry» the owner installed on the **master
only** (2026-09-28) is `Math.random() * 100 < Probability`, **unseeded**: every retest is a fresh
draw — fine as a null redrawn each time, useless for anything that must reproduce.
