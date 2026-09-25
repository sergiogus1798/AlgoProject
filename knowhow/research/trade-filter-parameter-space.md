---
q: minimum trades filter removes parameter levels, parameter cloud collapsed column, DICrossShift1 single value, space.varying, sensitivity zero, filter before surface fit
tag: 🔬  date: 2026-09-24  see: research/eta-squared-vs-duplicates, research/cloud-ranking-stability
---
# A trade-count floor is a projection in parameter space: report what it removed there
A filter run before fitting a surface (incl. `gate/`'s cascade) can delete whole regions and collapse a
parameter to one value. Any model fitted afterwards must be told: `space.varying()` names collapsed columns and
the report prints them first (else divide-by-zero in rescaling, or a silent unearned sensitivity of zero).

## Evidence
`Strategy 17.9.39` fabricated batch (2,000 variants, `metrics.parquet`), `strategies/parameterCloud/`: dropping the four
canaries and variants with < 30 IS trades leaves 998 rows and `DICrossShift1` with one value — every other level barely trades.
Finding about the strategy: that parameter chooses trading vs not trading. `sppUltra` eta²: `DICrossShift1` = 7.6 % of NetProfit, 78.5 % of trade count.
