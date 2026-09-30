# Portfolio engine — execution plan

Written 2026-09-30 by the orchestrating session, after the owner answered the questions of
`PLAN.md` §12 (table «Answered»). `PLAN.md` says **what**; this file says **who builds which file
against which signature**. Interfaces here are frozen: an agent implements them and never invents a
cross-module contract. A change to a signature is made here first, by the orchestrator.

Milestones run in this session: **M0 (code only), M1 (with §14.2), M2, F1**. Not run, and why:
M3/M4/M5/M8 (Q10, Q11, Q16, `DECISIONS.md` #2 real side, #5); F2 (needs the definition of a
strategy's unit of risk — asked when F1 and M2 are verified); F3-F5 (after F2); M6-M7, M9 (after M5).
The development pool itself waits for `Test_USDJPY_donchianUpperCrossUp_H1` to finish (Q2).

## 0 · Written by the orchestrator before any agent starts

| file | what |
|---|---|
| `core/datapaths.py` `portfolio_dir()` | `DATA / "portfolio"` — `core/paths.py` is at the 250-line cap, `funding_dir()` already lives here |
| `ledger/thresholds.yaml` | `portfolio.pairs.{pearson,spearman,co_loss,tail,rolling_whole,rolling_recent}` = 0.30, owner 2026-09-29 |
| `portfolio/common/construct/config.yaml` | every knob of M1-M2 |
| `portfolio/common/construct/inputs/config.py` | `load(overrides) -> dict`, with `relaxed` = thresholds moved off the ledger's value |
| `portfolio/common/construct/equity/clock.py` | `to_utc(times, zone) -> (utc, n_nat)`, `local(utc, zone)`, `day_of(utc, zone)`, `day_end(days, zone)`; zone `"EETUS"` = New York + 7 h |
| every folder `README.md`, `tests/README.md` rows, manual chapters, `tools/manual.py`, knowhow cards, `OPEN.md`, CLAUDE files | the orchestrator only |

## 1 · Shared data contracts

**Trades (T)** — one strategy on one feed, orderstocsv schema as the archive freezes it
(`harvest/trades.parquet`): `Type` ("Buy"/"Sell", may be categorical — cast with `.astype(object)`),
`Open time`, `Close time` (datetime64, **naive, the feed's clock**), `Open price`, `Close price`,
`Size` (lots, varies per trade), `Profit/Loss` (account currency, **net**), `MAE ($)` (≤ 0),
`MFE ($)` (≥ 0). `side = +1` Buy, `−1` Sell.

**Bars (B)** — `core.barstore.source(feed, ["High", "Low", "Close"])`: float64, index = naive bar-open
minute in the feed's clock. The feed's zone: `sqx.inspect.feeds.timezone(feed)`.

**Point value** — `engines.market.calibrate.point_value(trades)` (account currency per 1.0 of price per
lot; 653.92 on the archived USDJPY strategy).

**Minute path (P)** — dict of numpy arrays over every bar from the first trade's open minute to the
last trade's close minute, both included:
`t` int64 ns (bar open, naive feed clock) · `worst`, `best`, `close` float64 — the strategy's equity
relative to its start: realised P&L of the trades whose close minute ≤ this minute, plus, for each
position with open minute ≤ this minute < close minute, `side × (price − Open price) × Size × point_value`
at the minute's worst wick (`worst`: Low for a long, High for a short), best wick (`best`) or `Close` ·
`open` int16 — positions open in the minute. A trade's minute is the bar that contains its time
(`searchsorted(..., side="right") − 1`). **The exit minute is not floating; its realised P&L is booked
at that minute** (`knowhow/export/mae-mfe-from-m1.md`).

**Server-day table (D)** — `pd.DataFrame` indexed by naive day label (midnight of the server zone's
calendar date), one row per server day holding at least one path minute:
`closed` realised P&L booked that day · `float_end` floating P&L at the day's last minute
(`close` − realised) · `low`, `high` — min / max over the day's minutes of (`worst` / `best` − E0),
where E0 = realised at the previous day's end + that day's `float_end` (0 on the first day) ·
`opened` int, trades opened that day · `open_end` bool. Daily MTM P&L = `closed + float_end −
float_end.shift(fill 0)`; over a whole strategy it sums **exactly** to Σ `Profit/Loss` (the realised
P&L anchors each close).

**M5 blocks (M)** — on a UTC grid of 5-minute block starts (tz-aware): `low`, `high` float32 per block
= min / max over the block's minutes of (`worst` / `best` − E0 of that minute's server day); a block
with no minute carries the member's last level of the same server day (`close` − E0), or 0 before its
first minute of the day; 0 outside the path. Server midnights fall on whole hours, so no block
straddles two days. Joint intraday low of a combination on day d = min over d's blocks of Σ members'
`low` (exact at block resolution, `knowhow/perf/intraday-floating-resolution.md`).

**SQX's daily curve** — `harvest/equity.parquet` (`day, identity, equity, sample`) holds, per trading day
on the feed's clock, **the day's lowest equity** since the leg started (closed + floating at the worst
wick) — 🔬 found 2026-09-30 while verifying wave 1, `knowhow/sqx-format/daily-equity-bin.md`. It is a
known answer for the rebuild (`reconcile.low_equity` vs `sqxcurve.from_harvest`, exact ≤ 1 $), never a
source of daily P&L. Legs overlap with warm-up zeros and duplicate dates
(`knowhow/sqx-format/leg-curve-warmup.md`): slice by the policy's dates, earlier leg's row first.

**Daily matrix** — `pd.DataFrame`, index naive day, one column per identity, float64: 0 on a day
inside the strategy's history with no P&L, **NaN outside its history** (never 0 — AlphaForge's bug).
Monthly = calendar-month sums, NaN when the whole month is outside history.

**Portfolio calendar (Q1)** — `{"build": (from, to), "oos1": (…), "oos2": (…)}` naive `Timestamp`s,
both inclusive: build from the earliest member build start to the **latest** member build end; oos1
from the next day to the latest member oos1 end; oos2 likewise.

## 2 · Wave 1 — five agents, disjoint files

### A · the M1 rebuild (`equity/`: paths, days, blocks, excursions)

| file | signatures |
|---|---|
| `equity/paths.py` | `minute_path(trades: pd.DataFrame, bars: pd.DataFrame, point_value: float) -> dict[str, np.ndarray]` (P) |
| `equity/days.py` | `server_days(path: dict, feed_zone: str, day_zone: str) -> pd.DataFrame` (D) · `daily_pnl(days: pd.DataFrame) -> pd.Series` |
| `equity/blocks.py` | `grid(start: pd.Timestamp, end: pd.Timestamp, minutes: int) -> pd.DatetimeIndex` (UTC) · `blocks(path: dict, feed_zone: str, day_zone: str, grid: pd.DatetimeIndex) -> dict[str, np.ndarray]` (M) · `block_days(grid: pd.DatetimeIndex, day_zone: str) -> np.ndarray` (int64 ns day label per block) · `joint_day_low(members: list[np.ndarray], days: np.ndarray) -> pd.Series` and `joint_day_high(...)` |
| `equity/excursions.py` | `rebuild(trades, bars, point_value) -> pd.DataFrame` (`mae` ≤ 0, `mfe` ≥ 0, account currency, window open minute … close minute − 1, wicks) · `licence(trades, rebuilt, tolerance: float, min_share: float) -> dict` (`n, mae_exact, mfe_exact, mae_median_gap, mfe_median_gap, licensed`) |
| `tests/test_portfolio_mtm.py` | PLAN §8.2: hand-made M1 bars; a long across three day boundaries — floating to the cent; close-day increment = realised − last floating; a same-day trade whole on its day; Σ daily = Σ P/L exactly; a weekend; a short (worst = High); `EETUS` day cut 7 h off New York; an ambiguous DST hour counted; M5 `low` equals the M1 day-min for one member and the joint low of two members whose worst minutes differ is above the sum of their day-lows; the carried level of a flat block after a closed loss. Golden: the archived USDJPY strategy (`AlgoData/archive/4d679e…/2026-09-28T0919`) MAE exact ≥ 0.99 and MFE ≥ 0.99 (🔬 1.000 / 0.999) — skipped with a message if absent |

Clock: `equity.clock` only. Numba allowed (pinned). Perf: one strategy's path + days + blocks under
2 s and 1.5 GB (card: 0.08 s path, 0.55 s read). Must NOT touch: anything outside these five files.

### B · SQX's curve, matrices, calendar, reconciliation

| file | signatures |
|---|---|
| `equity/sqxcurve.py` | `from_harvest(equity: pd.DataFrame, symbol: str) -> pd.DataFrame` · `from_batch(column: pd.Series, symbol: str) -> pd.DataFrame` — columns `low` (SQX's day low, cumulative per leg) and `segment`, index naive day. *Amended by the orchestrator after verification: SQX's curve is the day's low, not MTM* |
| `equity/matrix.py` | `stack(series: dict[str, pd.Series], spans: dict[str, tuple[pd.Timestamp, pd.Timestamp]]) -> pd.DataFrame` (rows = days some series carries, never weekends — amended) · `monthly(daily: pd.DataFrame) -> pd.DataFrame` · `segment(frame: pd.DataFrame, calendar: dict, name: str) -> pd.DataFrame` |
| `equity/reconcile.py` | `low_equity(days) -> pd.Series` · `curve(rebuilt, sqx, tolerance, min_share) -> dict` (`n_days, exact, max_gap, p99_gap, verdict`) — amended as above |
| `inputs/calendar.py` | `portfolio(symbols: list[str]) -> dict` (Q1) · `borrowed(calendar: dict, symbol: str) -> dict[str, int]` — days of each portfolio segment that the symbol spends in another of its own segments |
| `tests/test_portfolio_universe.py` | the shift of SQX's day label; warm-up zeros and duplicate dates dropped on a synthetic batch; 0 inside / NaN outside history; monthly NaN only when the whole month is outside; calendar: USDJPY+XAUUSD = their own dates, FX + a synthetic index policy → build ends at the later end and `borrowed` counts the FX days; reconcile `ok` on a copy, `out` on a copy with a planted 5-trade gap |

Reads `core.assetdata`. Must NOT import `equity/paths|days|blocks|excursions` (A's, in flight).

### C · pair measures (`pairs/`)

| file | signatures |
|---|---|
| `pairs/measures.py` | `MEASURES: dict[str, Callable]`, each `fn(a: np.ndarray, b: np.ndarray, cfg: dict) -> float` on the rows where both are finite, **signed** (the admissible graph applies `sign: abs`): `pearson`, `spearman`, `co_loss` (share of overlapping months where both < 0), `tail` (Pearson on the months where either is at or below its own `tail_quantile`) · `overlap(a, b) -> int` |
| `pairs/rolling.py` | `rolling_max(a, b, window: int, recent: int, method: str) -> dict` (`whole`, `recent`, `n_windows`): max of the signed coefficient over every full window (one-step), and over the windows whose last row is in the final `recent` rows; a window with a non-finite row is skipped. The admissible graph reads the maximum of \|ρ\| — so also return `whole_abs`, `recent_abs` |
| `pairs/stress.py` | `stress_days(build_daily: pd.DataFrame, quantile: float) -> pd.DatetimeIndex` (the worst `quantile` of days of the row-mean over available members) · `stress_corr(a, b, mask) -> float` · `effective_n(corr: np.ndarray) -> dict` (`participation` = (Σλ)²/Σλ², `average` = K/(1+(K−1)·mean off-diagonal ρ)) |
| `tests/test_portfolio_measures.py` | PLAN §8.1: Pearson/Spearman = scipy; co-loss on a 12-month hand table = 3/12; tail on a pair built to correlate only in its worst months; rolling: ρ≈0 for 60 months then 0.9 for 36 → whole and recent maxima known; 5 shared months → `overlap` 5 (the rejection is the graph's, wave 2); stress: independent calm days, identical planted stress days → calm ≈ 0, stress = 1; effective N: k clones → 1, k independent → ≈ k (both formulas) |

Pure numpy/scipy/numba; imports nothing of the project. Must NOT touch other files.

### D · the funded rule machine (`portfolio/funded/rules/`, F1, encargo 33 deliverable 2)

Semantics frozen by the owner (PLAN §12 «Answered», rule machine row) — implement exactly:

- A stage runs on server-day arrays `closed, float_end, low, high` (account currency at unit scale) and
  `opened`, each multiplied by the stage's risk multiplier `k`. It starts the day after the previous
  stage passed, balance = equity = `size`; floating is measured from the start
  (`float_end − float_end[start−1]`).
- Day loop: `B0` balance at day start, `E0 = B0 + floating`. Daily floor: FTMO `B0 − dl·size`; Hantec
  `base·(1 − dl)` with `base = max(B0, E0)` (unconfirmed → flag). Max floor: `static` `size·(1 − ml)`;
  Hantec `trailing` `min(hw − ml·size, size)` with `hw` the highest **intraday equity** — raised by the
  day's `E0 + high·k` **before** the low is checked (unconfirmed → flag); FTMO `eod_trailing`
  `min(eod − ml·size, size)`, `eod` the highest **end-of-day balance** (unconfirmed → flag). Breach when
  `E0 + low·k` is **strictly below** a floor → `fail`, rule named.
- End of day: `B += closed·k`. A day's profit is its **closed** P&L. Trading day = `opened > 0`;
  profitable day (Hantec Enhanced) = closed ≥ 0.5 % of size. Consistency: EnhancedX best day ÷ total
  profit ≤ 35 %; FTMO 1-step best day ≤ 50 % of the positive days' sum.
- Target met when `B − size ≥ target·size` at the day's end **and** the stage's minimum days and
  consistency hold → the next stage. All challenge stages passed → `pass`. Time limit 0 = none.
- Values come from `funding.sqlite` (`stages` + curated `rules`); where a stage value and a curated rule
  disagree (Endurance `min_days` 0 vs «3 trading days per stage»), the curated rule wins and the plan
  carries a `conflict` flag. Every rule used whose status ≠ confirmed is in `plan["flags"]`.

| file | signatures |
|---|---|
| `rules/catalog.py` | `plans(max_size: float, ccy: str) -> list[str]` (current, EAs allowed, active firms of `firms.yaml`) · `plan(plan_key: str) -> dict` (`plan_key, firm, family, size, price, price_ccy, stages: [ {stage, target, daily_loss, max_loss, max_loss_mode, daily_basis, min_days, min_days_kind, profitable_pct, consistency, consistency_kind, time_limit, news_ok, weekend_ok} ]` challenge stages then `funded`, `flags: [{rule_key, status, text}]`) — percentages as fractions |
| `rules/floors.py` | pure per-rule functions: `daily_floor(b0, e0, size, pct, basis) -> float` · `max_floor(mode, size, pct, hw, eod) -> float` · `target_met(balance, size, pct) -> bool` · `days_ok(stats: dict, stage: dict) -> bool` · `consistency_ok(profits: np.ndarray, stage: dict) -> bool` |
| `rules/machine.py` | `challenge(days: dict[str, np.ndarray], plan: dict, risk: dict[str, float], start: int) -> dict` (`outcome` ∈ pass/fail/open, `stage`, `day`, `rule`, `stage_days: list[int]`, `flags`) — the reference · `sweep(days, plan, risk, starts: np.ndarray) -> np.ndarray` — the same for many start days (numba), outcome codes 1 pass / 0 fail / −1 open, **equal to `challenge` on every test path** |
| `tests/test_funded_rules.py` | per rule a hand path that breaks it by one tick (0.01) and one that touches it without breaking: daily loss (FTMO balance basis, Hantec max(B,E) basis — a floating profit at midnight raising the next day's base), static max, Hantec trailing (hw from an intraday high, locked at size after +6 %), FTMO eod trailing, target with open floating (not met on equity alone), min trading days, profitable days, both consistency rules, phase 2 starts fresh; catalogue: an unconfirmed rule appears in `flags`, Endurance carries the `conflict`; `sweep` == `challenge` on 200 random paths |

Reads `core.datapaths.funding_dir()` read-only (`mode=ro`). Must NOT touch `portfolio/funded/catalog/`
or the database.

### E · M0: pool, source, candidates

| file | signatures |
|---|---|
| `inputs/pool.py` | `ROOT = portfolio_dir()` · `declare(name: str, rows: list[dict], added_by: str) -> Path` (writes `pools/<name>.csv`: `identity, version, development, near, added_on, added_by, note`; `development` = archived `step` < 26 read from the archive's manifest (Q13); refuses an existing name — a declared pool is frozen) · `read(name: str, firm: str \| None) -> dict` (`members`, `prohibited`, `n_pool`, `n_prohibited`, `hash` = sha256 of the sorted `identity@version` left after `prohibitions/<firm>.csv`) |
| `inputs/source.py` | `load(identity: str, version: str) -> dict` (`identity, version, step, development, symbol, feed, clock, trades, sqx_equity, point_value`) from `core.archive.read` files only; `feed` from the frozen `strategy.sqx` (`core.sqxfile`) |
| `candidates.py` | THE COMMAND `python3 -m portfolio.common.construct.candidates [--project P]`: every `verdict.csv` with an `identity` column under `AlgoData/reports/<P>/<databank>/<day>/<study>/` (latest day per databank and study); per identity the furthest workflow step that judged it (study → step from `docs/AgentPDFs/WORKFLOW.md`, a table in the module) and its word. **Survivor** = MANTENER / survives / worth_it / predicts / PASS at that step; **near-survivor** = DUDOSA / INCONCLUSIVE (owner 2026-09-30); prints, for each not already archived (`core.archive.read.versions`), the exact `python3 -m core.archive archive --project P --databank D --identity <sha> --step S --family <template folder from registry.csv>` line with its class and words. **Runs none.** |
| `tests/test_portfolio_pool.py` | a pool in a temp `ROOT`: hash stable under row order, changes with a version; prohibited identities dropped and counted; a second `declare` of the same name refused; `development` true for step 16.5 |

Must NOT import `ui.*`, must NOT run `core.archive archive`, must NOT read SQX installs.

## 3 · Wave 2 (after wave 1 is verified)

- `equity/universe.py` + the command `python3 -m portfolio.common.construct.universe --pool <name>`:
  pool → sources → per feed one M1 read → paths → server days in EET and in each firm's zone → M5 arrays
  → matrices → reconciliation (curve and excursions) → `AlgoData/portfolio/universe/<pool_hash>/`
  (`daily.parquet`, `daily_sqx.parquet`, `monthly.parquet`, `days_<zone>.parquet`, `m5_<zone>.npz`,
  `reconcile.csv`, `manifest.json`).
- `pairs/table.py` (every measure × pair on build → `pairs.parquet`, chunked) and `search/admissible.py`
  (thresholds with `sign: abs`, overlap < 24 months → rejected, failing filter per pair, relaxed flag).
- Perf targets `portfolio.universe_one`, `portfolio.pairs_table` in `perf/inputs/targets.py`.
- Manual chapters 77-cartera-pool and 78-cartera-universo, family «11-cartera».

## 3b · What happened (2026-09-30)

- **Wave 1 verified**; three contracts amended by the orchestrator after verification: SQX's
  daily curve is the day's **low**, not MTM (`sqxcurve`, `reconcile` rewritten; `OPEN.md` #88);
  `matrix.stack` rows are market days, never the whole calendar; candidates follow what the
  workflow carried to 16.5 (owner).
- **Wave 2 verified**; tail filter made one-sided and rolling filters skipped under 60 shared
  months (owner); the universe rebuilt for the owner's compute rule (below).
- **Compute rule (owner, 2026-09-30): all physical cores, under 80 GB.** `core.fanout` with fork-shared
  inputs; universe members in parallel within a feed, one minute path per member, never returned;
  pair blocks in parallel; worker counts from `config.yaml compute:`. Measured: 48 members 15 s,
  57 GB; 124,750 pairs 30 s, 1.8 GB; admissible graph 1.1 s (vectorised).

## 5 · Wave 3 — F2, the funded search's stage A (owner's answers: PLAN §12, rows «F2 …»)

A member of a funded search is a strategy **with the step-24 stop grafted** (SL = X·ATR(20)),
archived as its own identity; its harvest trades already carry the stop. SQX sized every trade at
`risk_usd` over `atr_multiple`·ATR(20) (`ATRRiskBasedSizingFixedRisk`, 🔬 $1,000 over 4·ATR on the
archived one), so at risk r of an account of size S a member's P&L is SQX's × f × r × S with
**f = atr_multiple / (risk_usd · X)** — one constant per member. Every member at the same r
(`funded.risk_grid`, fraction of the initial balance). A level is **infeasible** for a combination
when some member's smallest trade lot, `min(Size) · f · r · S`, is below `min_lot / 2` (it would
round to 0). A pass counts within `funded.horizon_days` (126) trading days of the start; starts are
the build days with a full horizon after them. One risk for every phase (stage B sweeps per phase).

### H · the objective (`search/stagea_data.py`, `search/stagea.py`, horizon in `machine.py`)

| file | signatures |
|---|---|
| `portfolio/funded/rules/machine.py` | add `horizon: int` to `sweep` and `_sweep_kernel` (0 = none): a start whose last stage has not passed by `start + horizon − 1` is −1; `challenge` gets the same argument. Every existing test still passes |
| `search/stagea_data.py` | `prepare(universe: dict, firm: str, members: list[str], calendar: dict, factors: dict[str, float], min_size: dict[str, float]) -> dict` — `universe` = `equity.universe.load()`; build days of `days_<firm>` only: `identities`, `days` (int64 ns), `closed`, `float_end` (float64 [N, D], × f), `opened` (int32 [N, D]), `low5`, `high5` (float32 [N, B], build blocks only, × f), `block_day` (int32 [B], index into `days`), `lot_unit` (float64 [N] = min_size · f) |
| `search/stagea.py` | `evaluate(data: dict, combos: np.ndarray, plan: dict, cfg: dict) -> np.ndarray` — `combos` int32 [M, K_max] member indices padded with −1; returns float64 [M, L]: P(pass within the horizon) over the start days, per risk level, NaN where infeasible. **numba `parallel=True`, prange over combinations**, each thread builds its combination's day arrays (Σ members) and joint M5 low/high per day (min/max over the day's blocks of Σ members), scales by r·S and runs the machine's kernel · `best(scores: np.ndarray, grid: list[float]) -> tuple[np.ndarray, np.ndarray]` (best P and its r per row) |
| `tests/test_portfolio_stagea.py` | a combination's arrays are the members' sums; its P(pass) equals `challenge` run start by start on the summed arrays for every level; an infeasible level is NaN; the parallel result equals a serial loop; horizon: a path that passes on day 127 is not a pass at 126; throughput on a synthetic 50-member pool over a 10-year build (≈ 2,600 days, ≈ 1.05 M blocks): combinations per second on 48 cores, K = 5 and K = 10, and peak RAM |

### I · the search and its command (`search/greedy.py`, `search/genetic.py`, `search/trials.py`, `inputs/risk.py`, `funded.py`)

| file | signatures |
|---|---|
| `inputs/risk.py` | `sizing(identity: str, version: str) -> dict` (`x`, `risk_usd`, `atr_multiple`, `min_size`, `factor`) from the archived `strategy.sqx` (the grafted `ATRBasedValue` stop, `sqx/variants/build/stoploss.py` writes it; the active `ATRRiskBasedSizingFixedRisk` of `lastSettings.xml`) and `harvest/trades.parquet`; raises `ValueError("sin stop del paso 24")` when there is no ATR stop |
| `search/greedy.py` | `seeds(graph: np.ndarray, n: int, rng: np.random.Generator) -> list[np.ndarray]` — shuffled greedy maximal cliques |
| `search/genetic.py` | `run(graph, score: Callable[[np.ndarray], np.ndarray], seeds, cfg, rng) -> dict` — AF's GA rewritten as functions: tournament, union crossover, swap/add/remove mutation, children repaired to cliques (drop the worst-scoring offender) or discarded, elitism, stop on `stagnation` generations of the best **absolute** score; `score` takes a padded int32 [M, K_max] batch (the whole population at once, so `evaluate` fills every core) and returns [M]; returns every evaluated combination with its score, origin (seed/ga) and generation, and the best |
| `search/trials.py` | `record(run: dict, pool: dict, plan_key: str, members_meta: dict, cfg: dict) -> list[dict]` — ledger rows (Q12, both): study `PORTFOLIO_<pool>_construct` (symbol = members' symbols joined with `+`, timeframe `mixed`) **and** one row in each member's own study; step 27, segment `build`, `n_in` = admissible pool, `n_out` = K, criterion `portfolio/funded/<plan_key>`, scores = every evaluated P(pass) (`score_unit: p_pass`) |
| `funded.py` | THE COMMAND `python3 -m portfolio.common.construct.funded --pool <name> --plan <plan_key> [--set k=v]`: universe (cached) → members' sizing (no stop → excluded, named) → pair screen on build → prepare → greedy seeds + GA with `evaluate` → `AlgoData/portfolio/runs/<stamp>_<pool>_<plan>/` (`search.parquet`: members, score, level, origin, generation; `manifest.json`) → ledger rows → Spanish summary: the best 10 combinations (members, K, P(pass), r), evaluations, wall time, peak RAM, unconfirmed rules and clocks |
| `tests/test_portfolio_search.py` | PLAN §8.3 with a synthetic score: 40 strategies, one planted 6-clique scoring best → greedy + GA return it; children are always cliques; stagnation stops early; `search.parquet` rows == evaluations == the ledger row's `n_scored` (temp ledger); `risk.sizing` reads X back from a strategy grafted in memory (`stoploss.graft`) and refuses the stopless archived one |

## 5b · Wave 3 verified (2026-09-30)

- H: horizon in the machine (40 checks), `stagea` equal to the machine start by start, parallel =
  serial; 1,500-1,860 combinations/s on 48 cores vs 165/s serial, 1.3 GB (custodian busy meanwhile).
  Build blocks are the server days' blocks only (751,680 over 10 years, not the raw 1.05 M grid).
- I: GA repairs a non-clique child by dropping its least-connected member (structural, no extra
  scoring call) — accepted; a duplicated combination is scored and counted again (N overstated).
  `gate.allow` receives the pool row's joined symbol (`A+B`), harmless while `ALGO_AUTONOMOUS` is unset.

## 4 · Verification after each wave (the orchestrator)

Read every diff; run each test; rerun the golden against the archived USDJPY strategy; `python3 -m
perf.catalogue --only <target>`; `python3 tools/depmap.py && python3 tools/checks.py`.
