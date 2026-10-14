# studies/closing/exposure — what did that return cost in market time?

The last step of the workflow, and the only one that asks a question about the *shape* of an
edge rather than about its significance. Owner, 2026-09-24:

> *«Una estrategia que saque 5 %, pero solo se exponga al mercado 1 hora a la semana, me
> parecería mejor que sacar un 10 % con el buy and hold.»*

Every other study here asks whether the number is real. This one asks what the number cost:
a return earned while standing in the market four hours a week is not the same object as the
same return earned by being in it every minute, because the hours it was not exposed carry no
gap, no news and no drawdown.

```
config.yaml ─▶ inputs ─▶ occupancy ─▶ benchmark ─▶ compare ─▶ report
 every knob    trades,   how much     what buy     the        the
               bars,     market it    and hold     numbers    panel
               window    stood in     means here
```

| file | what it does | run it | in → out |
|---|---|---|---|
| `benchmark.py` | What "buy and hold" means here: three sizing conventions, and the P&L each one earns. | imported | bars + trades → lots, daily P&L |
| `compare.py` | The numbers: what each side earned, what it risked, and what an hour of exposure bought. | imported | daily P&L → statistics, trade-off |
| `inputs.py` | What the study is run on: its knobs, one strategy's trades, its bars and its window. | imported | export + feed → trades, bars, span |
| `load.py` | Everything one run of the exposure study reads, assembled once: window, bars, trades. | imported | export + feed → inputs |
| `many.py` | Every strategy of one export against buy & hold, and the population read as one result. | imported | inputs → results |
| `occupancy.py` | How much of the market's open time the strategy actually held a position, and how big. | imported | trades + bars → exposure, presence |
| `one.py` | One strategy against buy & hold, priced in market time, as the contract's data. | imported — the window calls it | inputs → result |
| `report.py` | Every strategy of one export against buy and hold, priced in the market time it spent. | `python3 -m studies.closing.exposure.report --project XAUUSD --databank "MC Trades" --feed XAUUSD_M1 --symbol XAUUSD [--strategy S]` | export → reports |
| `tooltips.py` | One sentence per config.yaml knob, for the window's configuration drawer. | imported | — |
| `config.yaml` | The sample, the segment, the three conventions and when to warn | edited | — |

Manual page, in Spanish, for whoever runs it: `docs/manual/10-cierre.pdf` (cap. 38-exposicion).

## The three things this module exists to get right

**The denominator is the window, never the trades.** The span comes from `assets/_policy.yaml`,
so a strategy that happened not to trade in 2018 is measured over the whole of `oos1` anyway.
Taking the window from the first and last trade is the silent way to turn a dormant strategy
into a busy one.

**"Buy and hold" is three different sentences and the study says which one it is speaking.**
`one_lot` is an absolute yardstick, `avg_size` commits the same money the strategy commits, and
`equal_risk` — the headline — holds whatever size makes the benchmark's daily volatility equal
to the strategy's. Only the third turns "it returns less than buy and hold" into a statement
about the edge instead of a statement about position sizing. 🔬 On `Strategy 1.10.39(1)` over
`oos1` the three are 50,650 $, 45,711 $ and 7,133 $ for the same held asset: reporting one
without naming it would be reporting nothing.

**The per-hour rate is an extrapolation and is labelled as one.** `return_per_exposure_pct`
divides the return by the occupancy — 7.57 % over 3.71 % of the bars reads as 204 % — and nobody
could have earned that: a strategy that waits for a setup does not find twenty-seven times as
many of them. It measures the quality of the time spent. The absolute comparison
(`return_ratio`) is printed right under it so the two are never confused.

## What it deliberately does not do

**No alpha/beta regression.** Parked by the owner on 2026-09-24 until the individual-strategy
sequence is closed. The groundwork is already here and is what that regression would need:
`occupancy.presence` says how much of the market's movement happened while the strategy was
holding and how much of it the strategy was pointed the right way for, which is a beta in the
only two terms that matter before a regression is worth running. If alpha/beta ever gets built,
it belongs in this folder.

**No mark-to-market daily series.** Profit is attributed to the day a trade closed, which is
what SQX reports. The series is lumpier than a mark-to-market one and its standard deviation is
therefore larger, which makes `equal_risk` hold *less* of the benchmark and the comparison
conservative towards the strategy. Stated rather than hidden, because the fix is a daily equity
export and the bias runs the safe way.

**No swap and no spread on the benchmark.** Over a window of years one entry is a rounding
error, and the financing cost of holding gold for five years is a decision about the benchmark,
not a fact about it. Naming it here is cheaper than pretending it was modelled.

## It describes, it does not judge

Owner, 2026-10-11: there is no `worth_it` / `not_worth_it` and no efficiency threshold. The 2.0x
bar was what random placement of the same exposure achieves, it was read on oos1 (which selected
the mothers), and nothing consumed the verdict. The study reports occupancy, hours per week,
notional committed, the buy and hold comparison and `efficiency` as plain numbers, and `notes`
lists why a figure may be hard to read (few trades, short window, a losing side, timing-like
presence). `verdict.csv` keeps its name for the window but carries no `verdict` column.
