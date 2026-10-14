# seasonality — is a strategy's oos1 result made of one month, weekday or hour?

Encargo 56, front 1 (ex 25: BuildAlpha's «seasonality breakdown»). A reading, no step of the
WORKFLOW. It **describes** a finished strategy by calendar and never returns a time filter to a
generation: rule 15 forbids time blocks in the builder, and the owner answered D-1 «sólo se
informa». Calendar in **UTC** (D-2): SQX stamps trades in the feed's broker clock
(`knowhow/export/feed-clock-timezones.md`); a time a change of hour skips or repeats is dropped.
Cells under **30 trades** (D-3) are shown as «sin datos suficientes» and never tested.

```
inputs ─▶ cells ─▶ null ─▶ verdict ─▶ one / many ─▶ report
harvest   UTC        p per    BH, the     contract     the
oos1      calendar   cell     word        dicts        command
```

## The null

Two layers, as the encargo asks: the breakdown (P&L, trades, win rate per cell, by open and by
close separately), and before it is read, each cell against chance. The value shuffled is **P&L
per lot** (`Profit/Loss / Size`), so equity-scaled sizing does not read as a season.

| dimension | held fixed | shuffled | why |
|---|---|---|---|
| weekday, hour | each UTC year-month's trades and values; each cell's count | which of that month's trades sits in which cell | a volatile month or a grown account is not an hour |
| month | each year-month block whole | which calendar month each block is called | one hot July is one observation, not many |

Two-sided Monte Carlo p, then Benjamini-Hochberg over **every tested cell of the strategy at
once** (12 + 7 + 24 cells, at open and at close), `fdr_q` 0.05. Calibrated on pure noise
(150 synthetic strategies): any-discovery rate 4.7 %, cell p uniform (5.6 % under 0.05).
Weekdays and hours rank the draws by the cell's sum (its count is fixed inside every stratum,
so sum and mean rank alike); months rank by the mean, since a relabel changes the count. The
colour of a discovery (pays more / less) is the sign of `excess`, the cell's mean against the
rest's. With one or two years of oos1 a month holds one or two blocks, and its smallest
attainable p may never pass BH: the month null is then blind, conservatively.
The stratum is not what decides: on two real populations year-month, quarter, year or no
stratum change the count by at most four strategies.

## The words

| verdict | meaning |
|---|---|
| `fragil` | a cell paying more than the rest is a discovery, and without its trades the oos1 net is ≤ 0 |
| `concentrado` | some cell is a discovery, but the rest still earns |
| `repartido` | no discovery |
| `sin_datos` | fewer than two cells reach 30 trades |

The population counts strategies with any discovery against `q × N`, the ceiling of chance;
strategies of one build share trades, so that binomial is a reference, not an exact test.

| file | what it does | run it | in → out |
|---|---|---|---|
| `cells.py` | Each oos1 trade placed on the calendar in UTC: its month, weekday and hour, at open and at close. | imported | trades + zone → cells |
| `inputs.py` | Every knob, the harvest's oos1 trades, and the clock they are stamped in. | imported | folder → frames |
| `many.py` | Every strategy of one harvest read by calendar, and whether the block shows more calendar than chance. | imported | trades → population + panel |
| `null.py` | The calendar null: how far each cell's mean per lot strays when the same trades are shuffled across cells. | imported | values + cells → p |
| `one.py` | One strategy's oos1 result broken down by UTC month, weekday and hour, each cell against the calendar null. | imported — the window calls it | cells → result |
| `report.py` | Seasonality: oos1 by UTC month, weekday and hour against the calendar null — encargo 56 F1. Describes, never filters. | `python3 -m studies.readings.seasonality.report --project P --databank D --feed XAUUSD_M1 [--strategy "Strategy 1.2.3"]` | harvest → reports |
| `tooltips.py` | One sentence per config.yaml knob, for the window's configuration drawer. | imported | — |
| `verdict.py` | Which calendar cells stand out after Benjamini-Hochberg, and whether the result leans on one. | imported | p per cell → word |

## Limits

- A harvest built before 2026-10-01 may carry the old feed's clock: hours can be 2-3 h off
  (highlighted warning; months and days barely move).
- ~0.3 s per strategy at 20,000 draws; a 10,000-strategy harvest is about an hour.
