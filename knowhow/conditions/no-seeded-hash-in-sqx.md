---
q: monkey test inside SQX, random entry custom block, seeded hash timestamp seed, XOR modulo bit shift in SQX vocabulary, RandomCondition runtime random, sin hash, D3 encargo 12, always true block
tag: 🔬  date: 2026-09-26  see: sqx-format/rewriting-strategy-logic
---
# No monkey inside SQX: the block vocabulary has no integer operation to build a seeded hash
Encargo 12 D3 is closed as impossible. A decent seeded hash of `(bar time, seed)` needs 64-bit
integer XOR, shifts and wrap-around multiply; this install composes only doubles (`Plus`, `Minus`,
`Multiplication`, `Division`, `Round`, `Abs`, `talib_*` incl. `SIN`/`FLOOR`). A double-precision
`frac(x·k)` or `sin` hash is the generator the PDF warns against, and a bad one is worse than none.
The random-entry question is answered outside SQX: `studies/readings/monkey/` (open-open 0.999985).

## Evidence
- `python3 -m sqx.inspect.vocabulary --role custodian <term>` on SQX_w2 (849 native + 175 own
  blocks), 2026-09-26: `xor`, `bit`, `hash`, `integer`, `Remainder` → nothing; `mod` matches only
  indicator names. Every `Values/Functions` block returns `pricenumber` (double).
- `RandomCondition`, `RandomValue`, `SameCondition`, `NegatedCondition` (`Random Conditions`) are the
  builder's template slots, filled at generation — not a runtime random draw. 🤔 inferred from their
  category and their use in templates; a retest of a strategy that keeps one would confirm.
- `AlwaysTrue` / `AlwaysFalse` exist (`Bar And Time`), but an ablation does not need them: deleting
  the `<Block>` is the neutralised condition (sqx-format/rewriting-strategy-logic).
- Not tried, and the only route left: a Java snippet custom block compiled in SQX's code editor,
  where any integer arithmetic is available. That is authoring code inside the master's GUI — the
  owner's call, not a vocabulary composition.
