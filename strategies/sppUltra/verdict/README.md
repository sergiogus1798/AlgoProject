# sppUltra/verdict — is this family worth the 5,000 variants?

| file | what it does | in → out |
|---|---|---|
| `noise.py` | The grid's best point against the best a null grid would reach, plus how peaked the surface is | grid → threshold, call, shape |

One question: under the hypothesis that **no parameter does anything**, the best of N draws with
dispersion sigma still lands near `sigma * sqrt(2 ln N)`. A grid whose maximum does not clear that
has found nothing, and neither the saturated phase nor the 5,000 variants are worth running.

**It is fed `n_eff`, never the row count.** Inert parameters duplicate points, so rows would raise
the bar against a grid that is smaller than it looks — the wrong direction, and invisibly.

`plateau_area` and `spike_ratio` are read together with the verdict, never instead of it. A maximum
that clears the threshold while `above_half_max` is 0.001 says the result lives at a single point,
which is the shape that does not survive contact with out-of-sample data.

## What this verdict is not

It is an in-sample screen. It cannot say the strategy will work, only that the surface holds more
than searching noise would have produced. Nothing here compares two windows, and nothing here can:
two SPP runs do not pair. Measured 2026-09-19 on `Strategy 17.9.39`, the IS and OOS runs share
**6 tuples out of ~11,600**.
