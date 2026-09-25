---
q: what is inside a .sqx file? sqx zip members, sqx file size, compare strategies by hash, get symbol from sqx, parse orders.bin, index all sqx
tag: 🔬  date: 2026-09-04  see: sqx-format/strategy-identity, sqx-format/daily-equity-bin, sqx-format/result-sections, export/orderstocsv-schema
---
# A .sqx is a ZIP; compare by inner XML, never by file hash
Members: `META-INF/MANIFEST.MF`, `settings.xml`, `strategy_Portfolio.xml`, `lastSettings.xml`,
`version.txt`, `orders.bin`, one `Results/Main: <SYMBOL>_<feed>/dailyEquity.bin` (more with cross-checks).
Never hash the file (ZIP embeds timestamps) — identity is the hash of `strategy_Portfolio.xml`
(`core.sqxfile.identity`, normalised). Symbol: regex the namelist, don't open `settings.xml`.
Never parse `orders.bin`; use `-tools action=orderstocsv`.

## Evidence
- Sizes over 15,971 `.sqx` on the master: min **28 KB**, median **226 KB**, p90 870 KB, max 15.4 MB.
  Size = `orders.bin` + daily equity (how much *result* it carries), not complexity. `settings.xml`
  and `strategy_Portfolio.xml` stay tens of KB. Not: "a .sqx is ~6 MB" (one large file generalised).
  `tests/fixtures/strategy.sqx` is a real 28 KB golden fixture.
- File hashes inflated a 13,288-strategy corpus into 17,754 "unique".
- Entry names contain `Results/Main: <SYMBOL>_<feed>/…`, e.g.
  `Results/Main: XAUUSD_DukasM1_Infinox_LOM_M30/`. `settings.xml` can be 5.8 MB.
- `strategy_Portfolio.xml` is plain XML, readable with no SQX running.
- Indexing all 17,754 `.sqx` takes **1.5 s** with 48 processes — cheap, do it rather than guess.
  Tool: `sqx/inspect/index_sqx.py`.
- 📓 `orders.bin` = private versioned format inside Java serialization.
