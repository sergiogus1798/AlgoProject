# crossmarket/travel — «does the logic travel?»: one set of random runs, one tensor

The machinery of step 10's redesign (encargo 46, spec §3). The real run on every market and `B`
random runs are priced by the **same** repricer at the **same** doctrine size, in R, and summed per
market and calendar cell. Every z of the step — joint, per window, per market, all-but-one, per
year — is read from that tensor with `stat.total`, nothing is simulated twice.

**Imports from:** `core/`, `engines/market` (`reprice`, `atr`), `engines/nulls` (`semester_shift`)
**Must not contain (part A files):** a threshold, a verdict, a rule P1-P9, a file read or written.
Part C's files (`rules`, `frequency`, `validity`, `units`, `run`) hold the rules and the one file-writing
runner; the thresholds that cut Pasa / Limbo / Falla still live in `criteria.yaml` (part E), never here.

| file | what it does | run it | in → out |
|---|---|---|---|
| `cells.py` | The calendar cells: natural years (or semesters), split where a segment of the MAIN asset starts, each labelled V0 / V1 / V2 / after; and `occupancy`, which locates every trade on the bar grid | imported | first and last bar, the main's cuts → cells table |
| `sizing.py` | The doctrine's lots at any bar (`Amount / (ATRMult × ATR(ATRPeriod) × point value)`, ATR of the bar closed before the entry) and where an entry on a defective bar moves to | imported | bars, card point value → lots per bar |
| `shift.py` | The joint draw — one whole-week (or business-day) shift per cell and run, keyed by the cell's date and not by the market — and where each real entry lands under it | imported | cells, seed → shifts; bar times, entries → moved entries |
| `tensor.py` | Per market what pricing needs (once), and per strategy the tensor: real `(markets, cells)`, random `(runs, markets, cells)`, trade counts; and the validity probe `displaced_share` / `exclude` (below) | imported | trades, bars, costs → tensor |
| `stat.py` | A total in R over any markets and cells that keeps «no data» apart from 0, and its z and empirical p against the runs; the weekly pooled t that annotates `net_t_pooled` | imported | tensor → z, p |
| `validity.py` | §7.1 per market, once, from every strategy's trades pooled: fill mismatch, card point value against the regression, share of defective bars, a complete cost card | imported | trades, bars, card → valid / reason |
| `frequency.py` | P2: z_freq of every strategy in every market, centred on the population's median log-rate | imported | counts, main trades → z_freq |
| `units.py` | P1 for an export: finds each strategy's `.sqx` under `raw/<project>/` (identity must match) and counts `fixed_distances` | imported | names, identities → count or NaN |
| `rules.py` | P3-P9 from one strategy's tensor: z_conj and windows, leave-one-market-out, breadth, tau_half, N_peor, degradation | imported | tensor → verdict columns |
| `run.py` | `run.run(project, databank, asset, export, out)`: loads the export, checks the markets, builds the tensors, writes `verdict.csv`, `markets.parquet`, `crossmarket.json` into `out` | imported (no `__main__`: part E wires it) | export → three files |

## Gross or net: `travel.judge_on` (encargo 46, decision 10, part G)

The cost in R is cost / (ATRMult × entry ATR × …): a strategy entering on high ATR pays less R of cost
than its shifted copies, so costs do not cancel (a no-edge population entering on the top-third ATR read
z_conj +1.20 on net). With `judge_on: gross` (default; `net` restores the old numbers exactly) the tensor
carries both, `gross = net + cost` from `reprice.pnl`:

- **On the judged quantity (gross):** `z_conj`, `p_conj`, `z_conj_v0/v1/v2`, `z_minus_market`, per-market
  `z` and `p`, `p_breadth`, `breadth_count`, `worse`, `worse_fraction`, `z_beta`.
- **Always on NET R, the cost kept in `e`:** per-market `e`, hence `tau_half`; `e_end`, `beta`,
  `e_end_ratio`, `d_y`. The tensor keeps `real_net` / `null_net` beside `real` / `null` for them.

## The API part C calls

```python
from engines.market import reprice
from studies.transfer.crossmarket.travel import cells, shift, sizing, stat, tensor

t = cfg["travel"]
cal = cells.table(first_bar, last_bar, cells.cuts(main_asset), t["shift_unit"], t["shift_step"])
shifts = shift.draws(cal, t["seed"], t["draws"])                      # (runs, cells), ONCE per export
markets = {feed: tensor.market(bars_cut_to_own_window, reprice.costs(feed, segment),
                               sizing.doctrine(), cal, t["validity"]["flat_atr_fraction"])
           for feed in valid_feeds}                                    # ONCE per export
one = tensor.build({feed: trades_of_strategy_on_feed}, markets, cal, shifts, t["shift_step"])
stat.joint(one)                                                        # z_conj, whole span
stat.joint(one, cells=(cal["window"] == "V2").to_numpy())             # z_conj(V2)
stat.joint(one, markets=[j])                                           # z_j
stat.total(one["trades"], cells=...)                                   # real trades closed there
```

| function | returns |
|---|---|
| `cells.cuts(asset) -> dict[str, pd.Timestamp]` | `build`, `oos1`, `end` of the main asset, from `core.assetdata` |
| `cells.table(first, last, cuts, unit, step) -> pd.DataFrame` | one row per cell: `start`, `end` (exclusive), `window`, `steps` |
| `shift.draws(cells, seed, count) -> np.ndarray` | `(count, cells)` int shifts, `0..steps-1` |
| `shift.entries(seconds, entry, cell, cells, shifts, step) -> np.ndarray` | `(runs, trades)` bar positions |
| `sizing.doctrine() -> dict` | `assets/_build.yaml › money_management.params` |
| `sizing.entry_atr(bars, period)`, `sizing.lots(atr, point_value, params)`, `sizing.usable(atr, flat_fraction)` | per-bar arrays |
| `tensor.market(bars, costs, params, cells, flat_fraction=0.0) -> dict` | the prepared market; `["data"]` says which cells it has bars in |
| `tensor.build(trades, markets, cells, shifts, step) -> dict` | `markets`, `real (M, C)`, `null (B, M, C)`, `trades (M, C)` |
| `stat.total(values, markets=None, cells=None) -> np.ndarray` | sum over the last two axes; masks or position lists |
| `stat.z(real, null) -> dict`, `stat.joint(tensor, markets=None, cells=None) -> dict` | `z`, `p`, `real`, `mean`, `sd` |

## What the numbers mean — read before building a rule on them

- **NaN is «no data», 0 is «nothing happened».** A cell the market has no bars in is NaN in
  `real`, `null` and `trades`; a cell with bars where no trade closed is 0. `stat.total` returns NaN
  only when *none* of the chosen cells has data, and `stat.z` then gives NaN z **and NaN p**. Never
  `np.nansum`/`fillna(0)` the tensor directly: a market missing a window would then read z = 0 and
  count as a neutral market. z is also NaN when the runs do not vary (a market with no trades).
- **A trade belongs to the cell it CLOSES in** (§3.5), real and random alike; the shift is decided
  by the cell it *opens* in. A run's trade count per cell can therefore differ by the few trades
  that straddle a frontier.
- **The real run is not SQX's P/L.** It is the row of zero shifts through the same code: SQX's
  stamps and side, the doctrine's size at that bar, the repricer's bar-open fills. SQX's `Size`
  and `Profit/Loss` are never read (§3.11, one repricer). An exit on a stop or a target inside a
  bar is priced at that bar's open, for the real run and the random ones alike.
- **One run is one shift everywhere.** The shift is calendar arithmetic (stamp + k weeks), so it is
  the same instant in every market; a stamp with no bar takes the next bar. A year is not a whole
  number of weeks, so a weekday with 53 dates in the year wraps one week later than one with 52:
  the pattern is rigid except across the wrap. A market that covers a cell only in part wraps
  inside the part it has bars for (shift modulo its own weeks — not exactly uniform there).
- **Holds are kept in bars**, and cut only at the last bar handed in. Give `tensor.market` bars
  already cut to the market's own build..oos1, or a moved trade will be closed on `oos2` bars.
  Not re-applied: the Friday close and «flat to enter» (the rigid move keeps both except in
  holiday weeks and at the wrap).
- **Lots are unrounded and uncapped** (`Decimals`, `MaxLots` of the doctrine are not applied), so
  1R is the same everywhere. `Amount` cancels in every z up to the repricer's cent rounding.
- **`window == "after"`**: cells past the main's oos1 end. A market whose own oos1 ends later than
  the main's has trades there; the spec's whole window is V0 + V1 + V2, so leave them out.
- **Which segment's costs** (`reprice.costs(feed, segment)`) is the caller's choice; one `Costs`
  per market. They cancel in z (measured: 300 no-edge strategies losing 58 R each on average read
  mean z −0.02), but not in `e`, the advantage per trade.
- `shift_step: day` counts business days; a weekend bar is treated as the following Monday.

## Unverified in the repricer — inherited, not fixed here

`engines/market/reprice.py` is audited against SQX only for **longs, zero commission, percent
swap** (`knowhow/research/monkey-reprice-audit.md`). Never reconciled trade by trade:

1. **Shorts** — the literal mirror of the long (sell at open − spread − slippage, buy back at
   open + slippage; `swap_short` with the long's sign rule).
2. **A non-zero commission** — charged once at the open (`PercentageBased` on the entry notional,
   `SizeBased` per lot).
3. **A swap in points** (every forex card) — `tick_step` is taken as `tick_size / 10`.

The real run and the random ones share any error, so z is robust to it; `e` in R is not.

## Validity per (market, cell) — the holes (encargo 46, part D3)

Index feeds have holes of months in 2011-2015. A shifted entry whose stamp has no bar takes the next
bar, so the random runs pile up after each hole and a population with no edge read z_conj +0.44 in V1.
`tensor.exclude` runs once per market, before any strategy: a fixed sample of uniformly placed entries
(generator seed 0, 20,000 per market, the first 300 shift rows) measures, per cell, the share that lands
on a different instant than its own stamp or on a defective bar. A (market, cell) above
`travel.validity.max_displaced_share` (0.20) is cleared in `data`, so `build` writes NaN there — never 0 —
for the real run and every random run. It reads only bars and cells, never a trade. The pairs left out
are listed in `crossmarket.json` under `excluded` (market, cell, share); `markets.parquet` and the
`verdict.csv` columns are unchanged. Card: `knowhow/research/index-feed-holes-and-the-shift-null.md`.

## The gate

`tests/test_crossmarket_travel.py` — synthetic, seconds, no parquet: 300 no-edge strategies on 11
correlated markets (z centred, unit spread, nominal rejection), a planted drift whose z is derived
by hand, zero shift = observed, market labels, `Amount`, seed, one draw moves every market alike,
a missing year is NaN.

## Part C — readings the spec left open

- **Costs:** each market's own card at `oos1` (`reprice.costs(feed, "oos1")`), as step 9 charges. A card with a
  pending field or none → market invalid (`no_cost_card`, `cost_card_pending`).
- **§7.1 fill mismatch** is measured per market over the trades of ALL the export's strategies pooled (side-signed
  median gap between recorded fill and bar open, in median-ATR units, ), refused above
  `travel.validity.max_fill_error` (0.25). **Point value:** slope of P/L on side x move x size, pooled, against the card.
  Defective bars are excluded from sizing by `flat_atr_fraction`; their share is reported, never a reason to refuse.
  A feed in `universe.absent` is invalid (`not_in_export`) and counts in `markets` and `invalid_fraction`.
- **P2:** main trades from `harvest/<project>/Results/<export date>/trades.parquet`, joined by identity; missing →
  `freq_off` NaN. An absent market (no trade) counts as flagged; its `z_freq` is NaN. The population median needs
  two strategies (`centred.centre`, `min_strategies=2`), otherwise the centre is 0.
- **P1:** `.sqx` located by `rglob` in `raw/<project>/` and accepted only when its identity equals the strategy's.
- **P7:** `e_principal` is read from an `e_principal` column of the export if it has one, else NaN (tau_half NaN).
  `tau_half` is -inf when fewer than half the markets stand; NaN needs e_principal not above 0.
- **P9:** the year is the calendar year of the close; a year under `min_trades_year` joins the next, a short tail
  joins the last group; a group sits at its trades-weighted mean year; `t_fin` is the last calendar year with data.
- **`net_t_pooled`:** weekly pooled t on SQX's net P/L over the valid markets, through `stat.weekly` and `stat.t`.
- Every cell outside V0 + V1 + V2 (`after`) is out of every statistic; a market invalid for §7.1 is out of the
  tensor and listed in `markets.parquet` (`valid` False, `z` NaN) and `crossmarket.json › checks`.
- `run.run` refuses an `out` that holds a result or lies in the live study's reports folder.

Gate of C: `tests/test_crossmarket_travel_rules.py` (toy tensor worked out by hand).
