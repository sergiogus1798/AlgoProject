---
q: Does a UUID stamped in a strategy's `<Description>` survive SQX's retests, the crossmarket retest, sync and export?
kw: UUID in description, stamp an identifier in the strategy, Description survives retest, crossmarket keeps description, export copies sqx byte for byte, stable strategy id, encargo 76 C
tag: 🔬  date: 2026-10-16  see: sqx-format/strategy-identity, sqx-format/identity-differs-across-databanks
---
# A UUID in `<Description>` survives the OOS retest, the crossmarket retest, the sync and the export
Measured on the conductor in `Test_Identity_UUID` (XAUUSD H1, 3 strategies, retired the same day): a UUID written into each build file's `<Description>`, loaded into Results, came out unchanged in `OOS` and in `Retest Markets` (15 additional markets, `sqx.projects.crossmarket`), after the databank sync on stop, and in the afterrun export, which copies the `.sqx` byte for byte. So a stamped UUID could be the identity. The canonical hash already ignores `<Description>`, so the two can live together; which one is the key is the owner's call (encargo 76 C). Not measured: the MC retest, the SPP, the WFM and the step-12 fabricated sisters.

## Evidence
🔬 2026-10-16 3 of 3 strategies kept their UUID in Results, OOS and Retest Markets; their canonical identity was equal across the three databanks and matched the store's new identities (569ee685, e7a0b2da, 6eb685ab). Archived config: `AlgoData/projects/retired/SQX_w1/Test_Identity_UUID-2026-10-16.tar.gz`.
