---
q: market profile null block length, block bootstrap of bars size and power, which block for marketProfile, why block 1, volatility clustering vs directional tests, BLAS threads slow small arrays
tag: 🔬  date: 2026-10-01  see: research/random-entry-nulls
---
# Market profile: a block of 1 bar is the only null with the right size; longer blocks only lose power
`studies/research/marketProfile` resamples bars in blocks. On sign-flipped series (real volatility, no
direction) block 1 rejects 4.0-7.5 % at the 5 % level; block 6 1.3-2.9 %; block 24 0.3-0.8 %. The null's
spread is the same at every length (studentised statistics); a block keeps what is shorter than itself, so
the null inherits the structure under test. An AR(1) of +0.2 scores trend 55 at block 1 and 5 at block 24.
Not: choose the block from the memory of |returns| (Politis-White 240-750 bars) — that is the volatility's
memory, and the directional measures do not need it once they are t statistics.
⚠️ Unlimited BLAS threads made a 20k-bar cell 20× slower (53 s vs 2.6 s): wrap in `threadpool_limits(1)`.

## Evidence
`AlgoData/research/profiles/blocklen.csv` — XAUUSD, EURUSD, USA500 × H1, H4 × blocks 1, 6, 24, 72, 240;
30 flipped copies × 200 draws × 51 directional tests per trial. `python3 -m studies.research.marketProfile.blocklen`.
