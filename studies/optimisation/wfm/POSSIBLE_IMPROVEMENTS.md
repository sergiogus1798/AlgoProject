# wfm — where the design had real alternatives

Each is a question for the owner; argue it here before changing code.

## 1. L2's reference in `fijo`: the weekly median series, or the difference of the medians?

Implemented: each WEEK's median across the 30 cells, minus the mother, summed. It is one tradable-
looking series and takes the same sign sets as L1. The alternative — L1's median of per-year sums
minus the mother's per-year sum — is consistent with L1 but is not a series. The two differ.

## 2. The null's lower tail on skewed weeks

The sign flip assumes each week's excess is symmetric around zero under no edge. A trend follower's
weeks are right-skewed, and the median statistic then rejects below more often than alpha. The study
annotates the skewness and warns above `null.skew_warn` (1.0, provisional, set by the agent). On
symmetric noise the test rejects 3 % below and 6 % above at alpha 5 % (400 synthetic mothers).

## 3. Which drift is subtracted

The spec says «net excess»; the study subtracts the gate's own drift term (`drift:` of
`studies/screening/gate/config.yaml`, window `year`, variant `d`) so steps 8 and 19 mean the same.
If the gate's block changes, this study follows it silently.

## 4. Re-charging is arithmetic

Spread, twice the slippage and the commission's difference, on SQX's own fills. A stop or target
the wider oos2 spread would have touched earlier is not moved, and no tick rounding. The exact way
is a second WFM task charged at oos2 — CPU the owner has not asked for.

## 5. build and oos1 are not re-charged in the per-segment table

They read at the costs the task ran with (oos1): build is charged too much, by oos1 − build.

## 6. Effective cells are biased down on few weeks

~25 of 30 for independent cells on 143 weeks. Left raw; a shrinkage correction is possible.

## 7. The drift number counts changes, not distance to the plateau

A parameter moving by one step on a flat surface counts like one jumping across the range.
