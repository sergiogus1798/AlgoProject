# cscv — alternatives weighed, and what would change the choice

1. **The mean of the equalised columns.** Chosen: the panel's median weekly Sharpe. Alternatives:
   zero (the seesaw alone: P(loss) of the null near 1 without resampling, near 0.5 with it), or
   the median of the raw means with a pooled deviation. The median Sharpe keeps the null's
   probability of loss comparable with the real one. Owner's question, open.
2. **First-order dominance with a tolerance.** Strict dominance of a subset over its superset
   fails at the top by construction. Alternative: drop first order and report the gap only.
3. **The planted subset is redrawn each draw**, and the null and each δ use independent streams.
   Common random numbers (the same rows for the null and the planted draws) would cut the noise
   of the power figures at equal cost; it was not asked for.
4. **LIMBO against the null's own P(loss)** — decided by the owner on 2026-10-08, replacing the
   fixed 0.25 cut (under the no-edge null's median, 0.36 to 0.38). Measured the same day: the
   rule holds its 5 % only on independent columns and fires about never on correlated ones
   (README, «The state»), because the null is centred on the panel's own sample median Sharpe and
   the real loss is the centre of that null, not a draw from it. Alternatives, the owner's call:
   centre the null elsewhere (item 1), or read the loss against the null's median plus a margin.
5. **More draws.** 1,000 draws for 1,000 variants cost 40 s on 48 cores. The default stays 200.
6. **GPU / float32.** Not needed at these sizes: the queue is under the budget on CPU.
