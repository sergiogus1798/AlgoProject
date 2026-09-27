---
q: real spread Darwinex vs declared SQX spread; is spread constant relative to price; spread gold USDJPY by year; spread at bar open hour; long pays spread entry short exit; spread model volatility; DATATICK retest cheaper
tag: 🔬  date: 2026-09-27  see: sqx-format/tick-file-format, costs/where-the-spread-is, costs/commission-methods
---
# Darwinex's real spread is 3–8× what `assets/` declares for XAUUSD and USDJPY, and not constant even relative to price
- XAUUSD mean opening spread 9 → 63 points (2017 → 2026), 0.69–1.89 bp of price (2020 = 1.96× the median year). Declared: 5 / 10 points.
- USDJPY 4.7 → 10.4 points mean, 0.36–0.66 bp. Declared: 0.1 points. Forex is not constant either (worst year 1.44×).
- The first tick of a full hour costs ~13 % more than an average minute; hour 00 (rollover) 2.1× the day on gold. Price a trade at its own minute, never at the day's mean.
- On bid bars SQX adds the whole spread to the ask side: a long pays the spread standing at entry, a short the one at exit. Reprice with that minute's spread (`studies/data/spread/reprice.py`).
- Indices' daily spread barely follows price (power-law exponent DJ30 −0.01, USA500 −0.10, USATEC −0.14, Nikkei −0.63; DAX +0.56): it moves by regime (2020, 2026 exceed the 97.5 % band on 9–12 % of days). SQX's MC Retest draws ONE spread per simulation (`RandomizeSpread.java`, uniform, 0.1-point steps) → band the DAILY mean, not the minute (`studies.data.spread.bands`). In 2018–19 Darwinex's index spreads were 2–4× dearer in % of price than since 2020, so any model fitted on 2018–2026 with price carries that back to 2012; the owner pinned `relativo` for the indices (2026-09-27).
- Before Oct 2017 there are no ticks: modelled from Dukascopy volatility (gold, 19 % error backwards) or volatility + price (USDJPY, 10 %). Unverified against anything pre-2017.

## Evidence
`python3 -m studies.data.spread.scan` → `AlgoData/spread/<tick feed>/summary.json`, `spread.html` (2026-09-27).
Repricing harvests (`studies.data.spread.report`): XAU_ISOOS_ejemplo OOS 66 → 63 strategies net > 0, net −16 % median; USDJPY_emaCross_H1 OOS 40 → 37, −34 %; Test_USDJPY_donchianUpperCrossUp_M30 OOS 191 → 186, −19 %.
