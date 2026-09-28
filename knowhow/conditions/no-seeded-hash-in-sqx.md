---
q: monkey test inside SQX, random entry custom block, RAND block WinRateEdge Math.random unseeded, seeded hash timestamp seed, XOR modulo bit shift in SQX vocabulary, Java snippet, RandomCondition runtime random, D3 encargo 12, encargo 30, always true block
tag: 🔬  date: 2026-09-28  see: sqx-format/rewriting-strategy-logic
---
# A random entry inside SQX needs a Java snippet, and the RAND block installed on the master is unseeded
The block vocabulary composes only doubles, so it cannot build a seeded hash of `(bar time, seed)`
(encargo 12 D3 stays closed for the vocabulary). A Java snippet can. The owner installed the
WinRateEdge «(RAND) Random Entry» snippet on the **master only** on 2026-09-28: its
`OnBlockEvaluate` is `Math.random() * 100 < Probability`, **unseeded**, so two backtests of one
strategy give different trades. Fine as a null whose every retest is a fresh draw; useless as a
fixed degree of freedom or for anything that must reproduce. The seeded variant is encargo 30.

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
