# Smoothing the performance-vs-parameter sweep — the idea, the objection, the test

Raised by the owner on 2026-09-22, from a podcast talk by Marty Tinsley (quant researcher). Parked
deliberately: nothing here is implemented. This file exists so the reasoning does not die with the
session, and so whoever picks it up starts from the objection rather than from the enthusiasm.

## The proposal, as heard

Plot a strategy's performance (Y) against one parameter (X) — a moving-average period, say. If the
edge is small, market noise and one-off events can produce a peak that is not the edge. You pick
that period, believing it best; it was the noise's best, not the strategy's. Tinsley's fix: run a
**top-hat filter** over that curve to strip the high frequencies the noise contributed, and read the
parameter off what is left. The owner's own instinct was an FFT for the same job.

## Translation into what this project already has

A top-hat over the parameter axis is a boxcar kernel — a moving average. Taking the argmax of the
smoothed curve is **choosing the centre of the plateau instead of the peak**. That is Pardo's
peak-vs-plateau rule written as a filter; the filter is a spelling, not a new idea. It is a sound
estimator: the argmax is an order statistic and therefore biased upward by construction, while the
plateau centre has lower estimation variance.

Two mechanical notes, if it is ever built:

- **Do not use an FFT.** The sweep axis is tens of points, not periodic (the FFT's circular envelope
  manufactures edge artefacts exactly at the ends of the range, which is where the decision is
  often made), frequently sampled irregularly, and in practice multidimensional. Direct convolution
  or a local regression — Nadaraya-Watson, LOESS, Savitzky-Golay — gives the same answer without any
  of that.
- **Do not use a boxcar either.** Its frequency response is a sinc; the sidelobes invent ripples
  (Gibbs) in the smoothed curve. Gaussian or Epanechnikov.

## The objection that decides whether any of this is worth building

The whole argument rests on one assumption: **noise is high-frequency along the parameter axis and
edge is low-frequency.** That holds when the errors at neighbouring parameter values are
independent. They are not. Periods 19, 20 and 21 trade **the same price history**. One event, one
streak, one outsized trade displaces the entire neighbourhood together. That contamination is
*low*-frequency — precisely the component a low-pass filter passes through untouched.

This is measured, not speculated, on our own grid: `core/surface/README.md` records lag-1
autocorrelation up to **+0.89** on the `XAUUSD/SPP IS` surface, and describes the surface as smooth
on top of duplicate-inflated rows. The surface is already smoothed by the structure of the problem.
Filtering further mostly costs resolution that is real — genuinely abrupt thresholds exist (session
boundaries, tick rounding, broker stop minima) — while leaving the correlated noise in place.

Second point, less fatal but worth stating: most of what the proposal is reaching for is already
answered here by a different and more defensible route, in `core/surface/plateau.py`:

| existing | what it answers |
|---|---|
| `plateau_area`, `above_half_max` | how much of the surface works — the plateau, with nothing filtered |
| `expected_max` (σ·√(2·ln n_eff)), `expected_max_sharpe`, `deflated_sharpe` | the peak pure search noise would have produced anyway |

The filter is a **selection** rule (which tuple do I pick); those are **validation** rules (is the
peak beyond noise at all). They are complementary, not substitutes — which is the honest reason the
idea is parked rather than rejected.

## Where it would go, if the test below passes

**The designed variants — the natural home.** The 5,000 variants of `strategies/sppUltra` sit on a
grid that is **regular by construction**, the only case where a multidimensional top-hat is even
well defined. `design_levels` already centres the variant grid on the plateau; a smoothed argmax is
a candidate estimator of that centre. Two cautions: run `core/surface/dedupe.distinct()` **first**
(inert parameters duplicate points and a kernel would weight the duplicates as observations), and
smooth per live axis, not over the full tuple space.

**The raw SPP grid — as a regression, not a convolution.** An SPP samples unbalanced; there is no
lattice to convolve over. Nadaraya-Watson with bandwidth by cross-validation.

**This module — not directly.** WFM cells are (steps × OOS share): split geometry, not a parameter
axis. Smoothing across cells answers a different question and should not be confused with this one.

## The one place where this module *is* the right instrument

Inside each walk-forward step, SQX picks the in-sample argmax and runs it forward. Replacing that
pick with a plateau-centre pick **is exactly Tinsley's proposal**, and rho IS→OOS is exactly the
metric that would say whether it works. The first run's verdicts — `blind` at +0.076 and `perverse`
at −0.505 — are the measurement of the failure he is describing.

It cannot be done from this export. `inputs/README.md`: *what the optimiser rejected is not stored*
— only its pick per step survives, so the surface each step chose from cannot be reconstructed, and
we do not touch SQX's optimiser. Related to `POSSIBLE_IMPROVEMENTS.md` §3, which is blocked on the
same missing data.

So the test has to run on the variant grid instead, where IS and OOS are pairable. Note that two SPP
runs are **not** pairable — `strategies/sppUltra/README.md`, 6 shared tuples out of ~11,600 — so the
designed variants are the only vehicle.

## The test, when it is picked up

For each strategy, take two picks off the in-sample surface and compare their **out-of-sample**
result:

1. `argmax` of the raw IS surface (what is done today);
2. `argmax` of the kernel-smoothed IS surface;
3. as a rival that assumes no frequency separation at all: the tuple maximising the **worst
   neighbour** in its neighbourhood (a min over the neighbourhood — robust-optimisation style).

Δ aggregated with a paired bootstrap over strategies. Bandwidth *h* chosen by cross-validation
**inside IS only**; touching OOS to pick *h* invalidates the whole thing.

| outcome | what it decides |
|---|---|
| Δ > 0, significant | the smoothed centre enters `design_levels` as the centre estimator, and becomes the final-tuple rule |
| Δ ≈ 0 | the objection above is confirmed — correlated, not high-frequency, noise. Record it in `knowhow/` and stop re-proposing it |
| Δ < 0 | the filter is erasing real structure. Also a finding, and a sharper one |

Cost: roughly an 80-line `core/surface/smooth.py` (Gaussian kernel, local-linear fit, CV bandwidth)
plus the experiment script. Touches no SQX install and no project.

**Cheaper prerequisite, 20 minutes, do this first.** Detrend the existing SPP grid along each axis
and measure the residual's autocorrelation / variogram. If the residual is as correlated as the raw
surface, Tinsley's frequency separation does not hold on this data and the 80 lines are not worth
writing. That measurement is worth having regardless of what is decided about the filter.
