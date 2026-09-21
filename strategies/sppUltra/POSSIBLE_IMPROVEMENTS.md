# sppUltra — where the design had real alternatives

Argue these here, in writing, before changing them in code.

## 1. The symmetric span can be narrow exactly where it matters

`design_levels` spans `centre ± max(|centre − original|, |centre − argmax|, plateau edges)`. When
those three sit close together, the span collapses — even for an influential parameter.

Measured on `Strategy 17.9.39`: **`DICrossShift1` is the second most influential parameter**
(eta² 0.236 on Ret/DD, 0.785 on trade count) and the SPP explored levels 0 to 6. Its plateau is one
level wide, its argmax is 0 and its original is 1, so the design gets **two levels, [0, 1]**, and
never looks at 2 to 6.

That is the rule working as written, and it is the wrong answer for this parameter. It matters
because the protocol's own measurement says `DICrossShift1` explains **67.6 % of the out-of-sample
variance** — reproduced 2026-09-21 from the paired export, 0.6817 — which is the single strongest
argument in the document for not trusting an in-sample centre.

Three ways out, none taken:

- **Route shifts to their own saturated design.** This is what the protocol already prescribes
  (design B, 7^k, everything else fixed), and the brief marks `is_shift` so the fabrication stage
  can. It fixes shifts and leaves the general case open.
- **A minimum span in levels**, e.g. never fewer than half the levels the SPP explored. Simple, but
  it spends the variant budget on axes the in-sample data says are flat, and the budget is what
  limits how finely the plateau can be resolved.
- **Span by influence**: width proportional to eta², so parameters that move the result get looked
  at more widely as well as more finely. Defensible, and it makes the span depend on the same
  confounded statistic the freezing rule deliberately refuses to trust.

Not decided. The owner picks, or the first real design exposes which one was needed.

## 2. The verdict metric is one choice, and it is not window-invariant

`config.yaml` reads everything on `ReturnDDRatio`, because that is what SQX's own Fitness is
(Spearman +0.999 at >=100 trades) and therefore the axis the builder optimised. But Ret/DD grows
with the horizon — return goes as mu*T and max drawdown as sigma*sqrt(T) — so it is unusable for
comparing windows of different length.

That is harmless here, because Phase 0 never compares two windows. It stops being harmless the
moment this module is pointed at the placebo windows, and the calibration of that exponent is a
deliverable of the protocol, not an assumption to carry in. **Do not reuse this config for a
cross-window reading without changing the metric.**

## 3. The plateau's `share` is 0.5 and nothing measured it

`plateau(share=0.5)` calls a level part of the plateau when its median sits within half the range
between the best and worst level. It is a round number, chosen for being round. It sets the plateau
width, hence the centre, hence where the whole variant design is placed — so it deserves a
sensitivity check on the first real design rather than a second round number.

## 4. Nothing here reads the histograms or the stored medians

`histograms.csv` and `metrics.csv` come out of the same export and are ignored. `metrics.csv`
carries SQX's own `orig_over_median` per metric, which is a ready-made answer to "was the original
tuple lucky?" — cheaper than anything this module computes and not currently cross-checked against
it. Worth doing, if only as a consistency test on the grid reader.
