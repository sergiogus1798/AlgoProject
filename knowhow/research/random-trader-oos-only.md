---
q: Where may the random trader be read: OOS and additional markets only, never the main market's build?
kw: random trader only vs OOS never vs build IS owner 2026-09-29, monkey IST refused own market, monteCarlo mcRetest OOS restrict, oos_thin veto, MIN_OOS_TRADES
tag: 🔬  date: 2026-09-29  see: research/random-entry-nulls, research/random-trader-benchmark-footprint, research/post-selection-bias
---
# The random trader is read only on OOS or on an additional market — the build already selected the strategy
Owner, 2026-09-29: the random trader may only be read on OOS or on an additional market, never the main market's build — it already selected the strategy. Enforced in `monteCarlo`, `mcRetest`, `readings/monkey` (IST refused on the own market); `crossmarket`, `gate.monkey` already were.

## Evidence
**OOS-only audit, 2026-09-29 (owner).** `monteCarlo.run._family_e()` restricts to
`stream.restrict(source, stream.samples(source)["OOS"])` before `footprint()`/`psr()` (was: whole
IS+OOS); < `confidence.MEAN_PROVISIONAL` OOS trades → NaN + `data`/`oos_thin` veto, never IS.
`mcRetest.measure.originals.read()` keeps `sample == "OOS"` only from the harvest (was: both
sides); < `run.MIN_OOS_TRADES` (5) → printed warning, still computed. KAT:
`tests/test_montecarlo_oos.py`. `crossmarket` already compliant: additional markets run their
whole window (never selected on); the main market's full backtest shows only as "referencia",
excluded from the verdict; the OOS reading was `orchestrate/stretch.py`'s `oos_tab` (deleted 2026-10-07, encargo 46; see git history before that commit).
`gate.monkey` already filters `sample == "OOS"`. `monkey.report --sample` defaults `OOS1`; not a
hard refusal — an additional market legitimately reads `IST` too (never selected on either
sample), so its help text spells out the distinction. `crossTF` reads a retest task's own
window, never a build task's — no mixing found.
