---
q: strategy identity key, join IS and OOS databanks, core.sqxfile.identity, makeExternal retest, hash strategy_Portfolio.xml, structure hash logic identity, duplicate strategies same name different strategy
tag: 🔬  date: 2026-09-23  see: sqx-format/sqx-zip-members, sqx-format/loaded-name-is-filename, databanks/curating-a-databank
---
# Identity = SHA-256 of `strategy_Portfolio.xml` with `makeExternal` stripped — the only cross-databank join key
`core.sqxfile.identity()` normalises (since 2026-09-23): a retest rewrites `makeExternal` on every
`<variable>` and nothing else, so the raw hash breaks across a retest. ⚠️ Identities stored before
2026-09-23 use the old formula and must be regenerated. Names are not keys. `core.sqxfile.structure()`
= hash of block keys in order without parameter values — identity of the LOGIC.

## Evidence
- The member holds definition, no results (those are in `Results/*/dailyEquity.bin`, `orders.bin`,
  `settings.xml`).
- `XAU_ISOOS_ejemplo` pair: 335 lines each side, 29 differing, all `makeExternal`. Raw hash matched
  **0 of 115**; normalised **115 of 115**, identical to the filename pairing.
- 📓 Not: "raw identity survives a retest" (5/5 between `XAUUSD/SPP IS` and `SPP OOS`) — both sides had
  already been retested; a control that passes by accident of the material.
- `Strategy 17.8.29` in `XAUUSD/OOS` and `XAUUSD/MC Trades` are different strategies
  (`StructuralBreakFilters_EntryOnly` vs `DirectionalMomentumFilters_EntryExit`, 281 vs 355 lines); of
  231 and 757 files only 4 names collide, all of this kind.
- `XAUUSD/MC Trades`: 757 `.sqx`, 694 distinct identities — 63 exact copies in their own databank.
- `structure()`: the 115 survivors = **24 structures**, two with 32 strategies each. 0.2 ms per strategy,
  0.18 s to read 235 files.
