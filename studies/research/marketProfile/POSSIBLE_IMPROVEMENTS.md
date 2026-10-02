# marketProfile — alternatives that were on the table

Argue a change here before making it in code.

- **The null.** Block resampling keeps everything shorter than a block, so a measure whose
  lookback plus hold fits inside a block is tested with a fraction of its power, and a block
  short enough to test it no longer keeps the volatility clustering (which lasts hundreds of
  bars: `blocklen.py`). A sign-flip (wild) null keeps the volatility path exactly and breaks
  every directional dependence at any horizon — `series.flipped` already builds it, as the
  yardstick of `blocklen` — but it also removes the drift, which the owner's design keeps.
  A null per family (block for the volatility measures, sign-flip around the mean for the
  directional ones) would test each family against what it does not claim.
- **The score.** Mean clipped z of the family's measures. Alternatives: the best measure's z
  (rewards a single hit, punishes nothing), or the share of significant measures (coarse with
  three to nine measures per family).
- **The lead measure.** The best payer among those that pass, else the smallest corrected p.
  A family's `multiple` is therefore the best of several: the p pays for the choice (every
  measure is in the correction), the multiple does not.
- **The cost.** Spread, slippage on both fills and commission of the `build` segment. The swap
  is not in it: it depends on the nights held, which a measure does not fix. Holds of 16 H4
  bars cross two or three nights.
- **The effect is gross of drift.** A long measure on a rising asset earns the drift; the p is
  against a null with the same drift, the multiple is not. `null_mean` is stored so the excess
  can be read.
- **Best hour, band and weekday** pay for their choice in the p (the null chooses too) but
  their effect in money is the chosen one's: biased upwards.
- **Sessions** are fixed hours of the feed's clock, not each city's local hours as
  `conditionalMap/sessions.py` does; they drift an hour a few weeks a year, and at H4 a band
  is whichever 4-hour bars open inside it.
- **Variance ratio** is the plain one; Lo-MacKinlay's heteroskedasticity-robust statistic would
  lean less on the null to absorb the volatility clustering.
- **The correction.** One Benjamini-Hochberg over every test is the verdict. It is not the
  harsh choice it looks: the dense families (`patron`, `reversion`'s structure, `volatilidad`)
  put hundreds of tiny p-values in the pool and lift the threshold for everyone, so a sparse
  family (`tendencia`, `ruptura`) is judged at p ≤ ~0.005 instead of the ~0.0001 it would need
  alone. Inside each family (`q_family`, stored beside the verdict) each family answers its own
  question at its own 5 %, which is stricter for the sparse ones and looser for the dense ones.
  Per asset was measured too: 6 measures pass instead of 2. **The draws bound the correction**:
  with 14,364 tests and 1,000 draws only a p at the floor (1/1001) could be named, so the map
  runs 3,000; the sweep (53,352 variants, 1,000 draws) takes the normal tail of z for a
  statistic that beat every draw. More tests need more draws, or the tail.
- **Power per cell.** A long-horizon rule makes 3-12 trades a year on one asset; against a null
  with the same drift a per-trade mean/sd of ~0.4-0.6 is needed to be seen in 8-10 years. The
  documented single-asset trend and dip-buying effects are 0.2-0.35. A test pooled over the
  assets of a class (Stouffer on `z`, with the cross-correlation paid for) is the instrument
  for those; the profile has none.
- **One position at a time** for the `rule` measures; the original ones (`lookback`, `breakout`…)
  open a trade on every signal bar, overlapping, so their `trades_per_year` counts signals.
