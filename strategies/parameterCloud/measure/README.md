# parameterCloud/measure — the numbers, under the model above

| file | what it does | in → out |
|---|---|---|
| `stability.py` | B2: per-period metric, the profitable fraction, the rank persistence, the centroid and its drift | curves → per-period tables |
| `ensemble.py` | C1: the plateau, K members spread across it, and the blended curve against the single point | curves → comparison |

Produces numbers and judges none of them.

**The per-period metric is an annualised Sharpe off daily P&L**, not net profit: it is scale-free,
so a period of 250 days and one of 120 are comparable, and a period where the family simply traded
more does not read as a better one.

**The ensemble picks members spread across the plateau, never the K best.** Greedy farthest-point in
the normalised parameter space. Picking the best K would be selection wearing an ensemble's clothes,
and the entire point is to stop depending on which point scored highest.

**A member with no harvested curve is dropped and counted.** `blend` reports the K it actually had,
because a blend of 6 when 8 were asked for is a different statement about risk.
