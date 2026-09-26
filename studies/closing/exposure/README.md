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
config.yaml ─▶ inputs ─▶ occupancy ─▶ benchmark ─▶ compare ─▶ verdict ─▶ report
 every knob    trades,   how much     what buy     the        is that    the
               bars,     market it    and hold     numbers    time worth  panel
               window    stood in     means here              it
```

| file | what it does | run it | in → out |
|---|---|---|---|
| `inputs.py` | The knobs, one export's trades on one sample, its bars and the window from policy | imported | export + feed → trades, bars, span |
| `occupancy.py` | Lots held at every bar, the share of open hours that is, and how much of the market's movement happened while it was holding | imported | trades + bars → exposure, presence |
| `benchmark.py` | The three sizing conventions of "buy and hold", and what each earned per day | imported | bars + trades → lots, daily P&L |
| `compare.py` | What each side earned and risked, and what one hour of exposure bought | imported | daily P&L → statistics, trade-off |
| `verdict.py` | Is the market time worth what it brings back | imported | numbers → verdict, reasons |
| `load.py` | The window from policy, its bars, the point value, the newest export on the configured sample, and each strategy's identity | imported | export + feed → inputs |
| `one.py` | One strategy measured — occupancy, the three buy and hold conventions, the trade-off, presence — and judged, as the contract's data the window paints | imported — the window calls it | inputs → result |
| `many.py` | Every strategy, and the population read as one result | imported | inputs → results |
| `report.py` | **The command**: every strategy to `reports/<P>/<D>/<day>/exposure/` (`verdict.csv`, a page and a JSON each, the population's page), or `--strategy` for one alone | `python3 -m studies.closing.exposure.report --project XAUUSD --databank "MC Trades" --feed XAUUSD_DukasM1_Infinox --symbol XAUUSD [--strategy S]` | export → reports |
| `tooltips.py` | One sentence per `config.yaml` knob, for the window's configuration drawer | imported | — |
| `config.yaml` | The sample, the segment, the three conventions and the gate | edited | — |

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

## A warning about the population it was first run on

🔬 Run over the 757 strategies of `XAUUSD/MC Trades`, 755 come out `worth_it`. That is not a
useless gate: that databank descends from a task carrying three acceptance conditions on
`main/OOS`, so 99.9 % of it is profitable out of sample by construction
(`docs/encargos/5-nulos.md` §6bis). A gate applied to a population that was already filtered on
the same axis has nothing left to cut. Read the distribution instead — median occupancy 8.3 %,
median efficiency 16.3x — and run the gate where it bites, which is a population that has not
been pre-filtered on profit.
