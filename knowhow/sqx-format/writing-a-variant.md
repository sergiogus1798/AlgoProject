---
q: write a strategy variant, rewrite parameter in sqx, repack sqx, Fingerprint remove, variant size MB, five-member size, integral double format, variant inherits parent results
tag: 🔬  date: 2026-09-21  see: sqx-format/five-member-sqx, sqx-format/loaded-name-is-filename, sqx-format/declared-parameters, sqx-format/retest-rewrites-sqstats
---
# A variant = four string substitutions in two members; everything else byte-identical
1. `strategy_Portfolio.xml`: `<variable><id>NAME</id>…<value>N</value>`; 2. `settings.xml`: name
**twice** (`<ResultsGroup ResultName="…">`, `<StrategyName type="String">`); 3. remove
`<Fingerprint …>…</Fingerprint>` (non-greedy `<Fingerprint\b.*?</Fingerprint>`); 4. variant id as an XML
comment after the declaration of `strategy_Portfolio.xml`. String substitution, never an `ElementTree`
round trip. Write integral doubles with no decimal point (`%g`). Until retested it carries the parent's results.

## Evidence
- Verified on `XAUUSD/Strategy 17.9.39` and `tests/fixtures/strategy.sqx`: rewrite → repack → read back,
  untouched members byte-identical. `sqx/variants/build/rewrite.py`; `tests/test_variants.py` holds it.
- The databank/export/retest handle is the **filename**, not these names (see loaded-name-is-filename);
  the in-file id exists because SQX may rename on collision.
- Fingerprint: every variant inherits the parent's; outer element's only child is self-closing.
- ElementTree reformats attributes, self-closing tags, whitespace in a file SQX parses with its own reader.
- Fixture's `TrailingStop1` is `double`, stored `50`; an `int` written `67.0` is a different file.
- Sizes as repacked (`Strategy 17.9.39`): full **123.3 KB**, no `optimizationProfile.bin` **98.7 KB**,
  five-member **13.7 KB** → 5,000 variants = 631 / 505 / 70 MB, fabricated in 65 / 49 / 6 s.
  Not: "a full .sqx is 5.2 MB → 26 GB": that parent had a **kept** 2.2 MB SPP profile; batch size depends
  on the parent's cross-check config.
- Inherited results: `orders.bin`, `dailyEquity.bin` and `settings.xml` SQStats are the parent's — in the
  five-member shape too (it keeps `settings.xml`). A never-run variant looks like the parent, not empty.
