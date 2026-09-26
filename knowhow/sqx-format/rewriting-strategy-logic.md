---
q: edit strategy logic in sqx, delete a condition block, ablation, AND with one block, invert long to short, rewrite IfThen rule, Long entry Short entry, #Direction# flip, MarketPositionIsLong, same trades after ablation redundant or ignored
tag: 🔬  date: 2026-09-26  see: sqx-format/writing-a-variant, conditions/no-seeded-hash-in-sqx
---
# SQX runs a rewritten rule as written: an AND of one block, and an order flipped to the other side
- Delete one direct child `<Block>` of the entry signal's `<Item key="AND">` → loads, retests, trades
  differently; an AND left with **one** block is accepted. The retested file keeps the edit.
- Invert = negate every `#Direction#` in `<Rules>` (entries and `ClosePosition`) and swap the side
  words (`Long entry`/`exit` rule names, `MarketPositionIsLong`). Same entries, opposite side, exactly.
- ⚠️ Same trades after an ablation ≠ SQX ignored it: read the **retested** file back. If the block is
  gone, the condition was redundant on that history (`sqx.structural.keep`).
- Only without stop/target/trailing is the flip a mirror; `sqx.structural.logic.invert` refuses otherwise.

## Evidence
`USDJPY_structural_v1` on the custodian, USDJPY H1 `Strategy 23.1.53` (EMA50 close-above AND QQE(14)
Value1 crosses above 57.72, exit after 24 bars), WFC legs at precision 2, 2026-09-26:
- identity rebuild: build 694 trades / 30,062.63, oos1 364 / 35,062.48 = the mother's stored results.
- drop QQE (AND of one): build **1,980** trades, oos1 1,050. Drop EMA: 694 / 364, identical trade for
  trade, retested XML without the block; in Python (Value1 ≈ EMA9 of Wilder RSI14), 0 of 1,330 crosses of 57.72 (2008–2022) come on
  a close below EMA(50) — at level 50 it would be 221. Redundant, not ignored.
- inversion: 694 of 694 paired (same open and close time, same size, Sell); per-trade gross corr
  −1.0000; move at mid +32,349 / −32,349. Nets: mother 30,063 = 32,349 − 2,286 spread; inverted
  −49,521 = −32,349 − 2,286 spread − 14,886 short swap (−10.4 points/night).
- SQX's own short entry keeps `label="Long"` beside `-1` (`tests/fixtures/strategy.sqx`): the label is cosmetic.
- Factory: `sqx/structural/`; golden `tests/test_structural.py` hashes equal the retested XML.
