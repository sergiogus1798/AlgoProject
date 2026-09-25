# cscv/verdict — what the numbers mean

| file | what it does | in → out |
|---|---|---|
| `summary.py` | What a run of partitions says: PBO, carry-over, probability of loss, dominance | rows → numbers |
| `trials.py` | The deflated Sharpe, given a count of independent trials | panel, n_eff → DSR |
| `cost.py` | What each rule cost on the split that actually happened, and how far the optimum moved | panel → percentiles |

**The PBO of pure noise has a standard deviation of 0.21** (measured 2026-09-22 over twelve
synthetic panels of 252). The partitions overlap heavily and are nothing like as many independent
observations, so 0.45 and 0.55 are not distinguishable and the 50 % gate is a coarse filter. Moving
from 252 partitions to 924 moved `argmax` on the measured grid from 41 % to 30 %: the same reading,
and a reason not to quote either figure to the decimal.

**The counting itself moved to `core.surface.trials`** on 2026-09-24, when the global ledger needed
the same n_eff over a whole surviving population rather than over one mother's variants. The rule
it carries went with it: **it refuses any split where one cluster holds half the variants.** Left alone the
silhouette picks the most flattering answer — 478 against 1 counts as two trials and deflates
nothing. On the measured grid that refusal is the difference between reporting 2 independent trials
and 21, and between a deflated Sharpe of 0.91 and 0.66.

`cost` is the only thing here that looks at the real chronological split; everything else is
combinatorial and says nothing about this history.
