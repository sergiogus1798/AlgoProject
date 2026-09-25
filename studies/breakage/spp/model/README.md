# sppUltra/model — what a number read off the grid means

| file | what it does | in → out |
|---|---|---|
| `influence.py` | Which parameters move the result: variance explained per metric, and the exact-duplicate test that sees what variance cannot | grid → eta² table, inert calls |
| `profile.py` | The shape of one parameter's curve: its marginal, its contiguous plateau, its centre, and where to place the variant grid's levels | grid → curve, plateau, levels |

## The two measurements do different jobs, and only one of them is proof

🔬 Measured 2026-09-20 on `Strategy 17.9.39`. `CBlock_SqzMmnInt21` gives **217 groups of tuples
differing only in it, and all 217 produced an identical backtest** — it provably never moved
anything. Its eta-squared on Ret/DD is nonetheless **0.0173**, above any freezing threshold you
would pick.

The reason is that an SPP **samples unbalanced**: each level of an inert parameter met a different
mix of the other parameters, so the spread between group means is confounding, not effect.
**Eta-squared of an inert parameter is not zero — it is biased upward.** The converse fails too:
`IsBars1` scores 0.0016 and is demonstrably live, with only 1 of 188 groups identical.

So: **the duplicate test decides who leaves the design. Eta-squared allocates levels among those
who stay.** There is no eta-squared freezing threshold in `config.yaml`, deliberately.

And eta-squared is reported **as a table over several metrics, never one column**: the same
`DICrossShift1` explains 7.6 % of NetProfit and 78.5 % of trade count. "Freeze what scores low" is a
choice of metric wearing the clothes of a measurement, so the metric is named in the report.

## Inertness belongs to the strategy, not to the block

The same `CBlock_SqzMmnInt21` gives 108 groups on `Strategy 41.5.25` of which **106** are identical
— not all. It is tested per strategy and never carried across.

## Plateaus

`plateau()` requires the good levels to be **contiguous**. A scattered set of good levels is not a
plateau: a design centred on it would sit next to levels that fail, and a parameter you have to hit
exactly is not one you can deploy. A plateau of width 1 is flagged `spike` in the brief — there the
"centre" is the argmax under another name.

`design_levels()` snaps to levels the SPP actually explored. These parameters are bar counts and
periods; a linear span produces a shift of 0.1429 bars, which SQX cannot run.
