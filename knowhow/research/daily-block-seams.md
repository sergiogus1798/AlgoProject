---
q: How must a daily block bootstrap treat floating equity at each block seam?
kw: joint-daily block bootstrap floating at block seams; float_end resampling; open trade cut at block edge; stationary bootstrap of server days with floating equity; short blocks read risk smaller or larger; Politis-White block length daily P&L; planted loss clusters block length; T1 trade bootstrap destroys co-movement
tag: 🔬  date: 2026-10-02  see: perf/intraday-floating-resolution, research/contemporaneous-dependence-bootstrap
---
# A daily block bootstrap must SETTLE the floating at each seam; carrying it across makes short blocks read riskier for no reason
Resampling server days that carry floating equity (`float_end`), a block's last day books what is still floating as closed and
the next block starts flat (`mc.paths.daily_blocks`): equity still moves by each drawn day's own mark-to-market P&L. Carrying
the floating across seams — as levels or as daily changes — invents equity noise or strands floating the balance never
receives, and the shortest blocks then read as the MOST pessimistic, which would decide under «the most pessimistic length».
Settled, a block of 1 day is lenient instead: last night's floating loss never counts against today's daily-loss floor.
Shorter blocks read planted loss runs as smaller, and T1 (members drawn apart) reads a clone portfolio's drawdown ÷ √K.

## Evidence
- 4 synthetic members holding up to 1.7 days (`tests/test_portfolio_mc_paths.bar_world`), Hantec Enhanced 10k, r 1 %/1 %,
  2,000 paths, horizon 60; P(pass) by mean block length 1 / 5 / 20 days, T2 at 20 = 0.094, T1 = 0.111:

  | seam treatment | L=1 | L=5 | L=20 | daily-loss fails at L=1 |
  |---|---|---|---|---|
  | floating **levels** resampled as they are | 0.055 | 0.084 | 0.091 | 0.72 |
  | floating **changes** summed (stranded) | 0.032 | 0.061 | 0.084 | 0.83 |
  | **settled at the seam** (built) | 0.162 | 0.087 | 0.085 | 0.50 |

- Planted runs of 12 losing days in 1,500 (`test_shorter_blocks_read_loss_clusters_as_less_risky`): mean max drawdown over
  120 days at mean block 1 / 5 / 10 / 20 / 40 = 9.2 / 15.8 / 18.1 / 19.1 / 19.8 (D), 9.2 / 15.9 / 17.8 / 19.1 / 19.8 (T2);
  Politis-White on that series measures 24 days.
- Five clones (`test_t1_destroys_comovement_t2_and_d_keep`): mean max drawdown T1 20.7, T2 45.5, D 45.8 (√5 = 2.24).
- 🤔 Not measured: how often Politis-White lands under 5 days on a real combination (on i.i.d. noise it reads 1), where the
  settled block of 1 would be the lenient outlier, never the one that decides.
