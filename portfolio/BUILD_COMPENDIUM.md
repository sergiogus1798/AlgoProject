# Portfolio build compendium — everything to consider before and while building `portfolio/`

**Read this whole file before writing any portfolio code.** Owner, 2026-09-28: "apunta TODO".

It merges two sources, gathered 2026-09-27/28 and not yet decided on:

- **AlphaForge** — the owner's earlier portfolio generator, public repo
  `https://github.com/sergiogus1798/AlphaForge`, package `alphaforge/portfolio/` (~5,000 lines).
  It reads the same `orderstocsv` trade schema this project stores in `trades.parquet`, so its
  code ports with little glue.
- **The books-and-internet dossier** — `docs/AgentPDFs/ideas-de-internet-y-libros-2026-09-27.md`,
  above all §5 (lines ~2826-3725: tails, drawdown, sizing, limits, portfolio, live), plus
  §1.11, §1.14, §1.19, the top-30 items 14, 15, 16, 23, 24, 25 and 29, and scattered §3/§4/§6
  entries named below. Each entry there carries its sources with page numbers; go there for the
  citation, come here for the checklist.

**Nothing here is accepted.** Every item is a candidate. An item that needs the owner's choice is
listed in §11 and mirrored in `DECISIONS.md` — ask, do not pick (root `CLAUDE.md` rule 11).

Tags: **[AF]** AlphaForge does it · **[AF✗]** AlphaForge does it in a way the dossier advises
against · **[D·vN]** from the dossier, with its value 1-5 · **🤔** inferred by the session that
wrote this file, not from a source.

---

## 1 · AlphaForge — what it is and where each piece lives

Pipeline (`alphaforge/portfolio/generator/pipeline.py`, design in `PORTFOLIO_GENERATION_PLAN.txt`):
pool of pre-validated strategies at $100 risk/trade → find combinations of `min..max` strategies
(default 6-7) that satisfy prop-firm constraints, maximising size.

| file | what it does | verdict |
|---|---|---|
| `portfolio/config.py` | One dataclass with every threshold: account 60k, daily loss 4.5 %, total DD 9 %, Pearson/Spearman/co-loss/tail ≤ 0.30, same-asset window 8 h, rolling 60 m ≤ 0.40 and ≤ 0.30 in the last 3 y, fitness weights 0.8/0.1/0.1, GA params, WF 6 y IS / 3 y OOS | the "one place for every knob" idea matches `config.yaml` + `gates.py` here |
| `portfolio/universe.py` | Precomputes once: daily P&L matrix (days × N, $0 fill), monthly P&L (NaN where absent), N×N Pearson, Spearman, **co-loss** (share of months both lose), and a boolean **same-asset conflict** matrix (two strategies open on the same canonical symbol within `window_hours`) | **keep** — every combo check becomes an O(K²) lookup. Bug: <6 overlapping months → correlation 0.0, so unknown passes as uncorrelated; should reject or flag |
| `generator/filters.py` | Static filters (Pearson, Spearman, co-loss, **tail correlation** on the worst 30 % of months, same-asset) then **rolling** Pearson/Spearman, stricter in the recent period; short-circuits on first failing pair; counts rejections per filter | **keep**, extend per §3 |
| `generator/sampler.py` | Random combinations, proportional to sizes | fine for small pools |
| `generator/genetic.py` | GA over combinations: tournament, union crossover, swap/add/remove mutation, every filter a hard constraint; **greedy independent-set seeding** (shuffle, add each strategy compatible with all already in); per-pair rolling-correlation cache | **keep the engineering**; the search itself must obey §2.1-2.2 |
| `generator/weighting.py` | Equal, min-variance (SLSQP on daily-P&L covariance), risk parity (1/σ), **HRP** (Ward linkage on correlation distance, recursive bisection) | **keep**; add shrinkage to min-var (§4) |
| `generator/wf.py` | Walk-forward of the weights: OOS windows anchored on 1 Jan, weights from the IS lookback, stitched OOS equity; equal weight excluded because static | **keep** — it is exactly the test that equal weight must be beaten OOS (§4) |
| `generator/scaler.py` | `scale = daily_loss_limit / |worst historical day|`; risk per trade = base × wᵢ × n × scale | **[AF✗] redo** (§5) |
| `generator/validator.py` | Max DD on the rescaled daily closed-P&L equity vs the total-DD limit; flags, never drops | redo on mark-to-market equity (§2.6) |
| `generator/fitness.py` | 0.8·norm(Ret/DD) + 0.1·norm(annual %) + 0.1·norm(winning months), min-max within the pool | **[AF✗] redo** (§8) |
| `stress/mae_stress.py` | Replaces every trade's P&L by −|MAE|×scale and rechecks limits | **[AF✗] redo** (§6) |
| `analysis/correlation_deep.py` | Pool heatmaps, PCA (independent drivers), rolling-correlation heatmap, dendrogram, tail correlation | ideas keep; must end in a decision, not a picture |
| `run_expandPortfolio.py` | Fix a base portfolio, exhaustively try every addable subset that passes all filters against base and each other | **keep** → becomes the marginal-contribution admission rule (§3.2) |
| `exporter.py`, `dashboard*.py` | xlsx + PDF per combination × method; matplotlib/Dash dashboards | do not port — interfaces live in `ui/` (root `CLAUDE.md`) |

Its only prop-firm rules are daily loss and total DD, on **closed** P&L attributed to the close
day. No minimum days, consistency, news windows, static-vs-trailing DD, or portfolio Monte Carlo.

⚠ `TokenAlphaForge.txt` in that public repo holds a GitHub token (`ghp_…`). The owner was told on
2026-09-28 to revoke it. Never use it.

---

## 2 · Process rules — before writing a line

1. **Choosing a portfolio is a search, and it goes to the ledger.** Every combination evaluated,
   every market excluded after seeing it, every overlay counts as a trial. Katz's "625 % OOS"
   portfolio was picked by looking at that OOS. [D·v4, §3.3 "Las bifurcaciones del investigador";
   §5.8 "Los overlays son sistemas"] — [AF✗] 250,000 random combos or a 300×100 GA on the whole
   history, best kept, nothing counted.
2. **Select the combination on one segment, validate on another.** [AF✗] AlphaForge's WF
   protects only the weights, not the combination choice. Here the segments of
   `assets/_policy.yaml` apply; `oos2` is reserved for steps 17-19 — which segment the portfolio
   may read is an owner decision (§11).
3. **Declare the universe and the pass rule before looking.** Any later exclusion ("silver is
   different") is either a prediction checked on unread data or one more trial. [D·v3, §6.1]
4. **Overlays are systems** (Seykota: "if a policy M improves system S, maybe trade M"): specified
   beforehand, tested OOS like a strategy, counted. [D·v4, §5.8, §6.2]
5. **Simulate trade by trade, never by summing curves**, as soon as any rule is path-dependent
   (group limits, heat, free slots, gates that skip a signal). [D·v4, Abraham's seven gates]
6. **Daily mark-to-market equity, not closed trades.** Sharpe and DD on the daily change of
   floating equity. [D·v2, §3.8 "Unidades correctas"] — [AF✗] closed P&L on the close day;
   prop firms measure daily loss on floating equity. 🤔 M1 bars exist for every asset, so floating
   equity can be rebuilt exactly.
7. **Composite scores by signed ranks with equal weights, or 0/1 rules** (Eckhardt, Chan,
   Kahneman). [D·v3, §3.8 "Combinar métricas… con pesos iguales"] — [AF✗] min-max within each
   generation, 0.8/0.1/0.1: not comparable across runs.
8. The existing agreed rules still hold (`CLAUDE.md` here): correlation between equity curves, DD on
   the aggregated curve, funded-account rules are constraints not post-filters, strategies enter
   from the archive.

## 3 · What enters the pool

1. **Keep the near-survivors** instead of deleting them: beat the monkey but failed a secondary
   filter, or win gross but not net of costs. Hite keeps mediocre systems for their low
   correlation; Galante's losing fund 50/50 with the index halved its DD. [D·v4, §1.14, §5.9
   "Confluencia", §4.4 "Confluencia de estrategias que no pagan costes"]
2. **Admission by marginal contribution:** a strategy enters if its incremental Sharpe to the
   existing book is positive net of cost (Euler decomposition, arXiv 1807.09864). Pre-register
   the expected increment, report the realised one. [D·v4, §5.9] — [AF] `run_expandPortfolio.py`
   is almost this; make it the formal rule. For candidates the question is contribution, not
   beating buy-and-hold head-to-head (§1.14).
3. **Judge long and short sides separately and together** before amputating one (Faith: a weak
   short side lifted the pair's R³ from 1.19 to 5.20). [D·v4]
4. **Apply the project's own haircut before showing a metric:** from the ledger, the distribution
   of `oos1/build` per family, asset, timeframe; later `oos2/oos1` and `live/oos2`. External
   reference 0.4-0.75 (McLean-Pontiff, Chan); `decay` measured a median retention of 0.45 on an
   unselected population. [D·v5, §5.6]
5. **One label card per strategy**, which mixing needs:
   - **Convexity** long or short, from data: skew of R and of months, avg win/avg loss vs hit
     rate, stdev/semi-stdev, smile vs frown of monthly return against the underlying. Warn when
     hit rate > 65 % and worst loss > 5× median win. [D·v5, §5.5]
   - **Momentum vs reversion** (entry with or against the last move, payoff asymmetry). [D·v3]
   - **Factor exposure:** underlying direction, vol change, generic trend, generic reversion,
     swap/carry, USD basket. [D·v4, §5.9 "Factores y monocultivo"]
   - **Crisis coverage:** which named episodes (2008, 2010 flash crash, 2011 gold top, 2013
     taper, SNB Jan 2015, CNY Aug 2015, Brexit 2016, Mar 2020, WTI Apr 2020, gilts 2022, yen
     5 Aug 2024) fall in build/oos1/oos2 and how it did. None → "not crisis-tested"; one regime →
     "half cycle". A YAML of dates and an intersection. [D·v4, §5.5]
   - **P&L in the market's extreme months** (return decile of the asset and of a risk proxy such
     as US500): long-vol or short-vol edge. [D·v4, §5.5]

## 4 · Diversification and correlation (AlphaForge's core)

1. [AF] **Keep the six pairwise measures:** Pearson, Spearman, **co-loss**, **tail** (worst 30 %
   of months), **rolling 60 m with a stricter recent threshold**, **same asset within 8 h**. The
   dossier backs all of them.
2. **Stress-day correlation:** the same matrix only on the 5 % largest-|move| days of the asset or
   a risk proxy, on named crises, and on the survivors' own worst days; report the **effective
   number of independent strategies in calm and in stress**. ρ 0.1 overall and 0.8 in stress is
   one strategy for risk. [D·v5, top-30 #14, LTCM, BIS Aug 2024] — [AF] AlphaForge's tail is
   monthly and on each strategy's own worst months; this extends it to days and market stress.
3. 🤔 **Measure daily as well as monthly.** The daily loss cap breaks on same-day co-losses that
   monthly aggregation can hide.
4. **Signal/position overlap ("plateau clones"):** fraction of bars where k strategies hold the
   same direction on the same asset; size on the **joint** position. Turtles' S1+S2 believed −50 %
   worst case, real −80 %; Kovner: "eight highly correlated positions are one position eight times
   larger". [D·v4] ⚠ Contradicts "trade the plateau": variant-factory siblings are exactly such
   clones. — [AF] the 8 h rule is a crude version; generalise it.
5. **Groups from the history of joint stop-outs,** not only return correlation: count how often
   losing trades coincide across related markets (crossmarket output). [D·v4, §5.9 "Calor de
   cartera"]
6. **Monoculture:** share of the pool's risk explained by the first factor; describe the
   post-gate population by traits (% long, holding time, reversion vs breakout, hour, correlation
   with the build's trend). 85 % dip-buyers in a bull segment is one bet. [D·v4] — [AF] PCA and
   dendrogram exist only as plots; here they must end in a decision.
7. **Mix momentum and reversion,** cap the risk share of convergent strategies and give them a
   stricter tail test. [D·v3]
8. **Diversify by effect and timeframe:** crossTF siblings that survive are diversifiers, provided
   they are not clones by 4.4. Build Alpha: redundancy by effect. [D·v2]
9. **Correlation is regime-dependent — look at its rate of change,** use Spearman on changes, look
   at the scatter. In crossmarket publish each market's correlation with the main one per segment:
   an edge that transfers only while correlation is high is the same trade. [D·v4, §4.8
   "Correlación móvil inestable"]
10. **Fix AlphaForge's <6-month overlap → 0.0.** Reject or flag the pair instead.
11. The library holds **five correlated yen bets** (AUDJPY, CADJPY, EURJPY, GBPJPY, USDJPY) plus
    NIKKEI225 — treat as one group until data says otherwise. [D, §5.9]

## 5 · Weights

1. **Equal weight (or equal risk) is the baseline every optimisation must beat out of sample.**
   HRP vs equal: equal usually wins OOS. Answers `DECISIONS.md` #3. [D·v3, §5.9] — [AF] `wf.py`
   is the test; keep it and make it emit a verdict.
2. **Carver's handcrafting** as the standard method: hierarchical grouping by correlation,
   vol-parity inside each group, diversification multiplier (IDM 1-1.4 within one asset class,
   1-2.5 multi-asset). [D·v3]
3. [AF✗] 🤔 **Min-variance needs covariance shrinkage** (Ledoit-Wolf) or it fits sample noise.
4. **Conviction sizing only if a measurable score predicts OOS P&L** (e.g. number of strategies
   in confluence). Otherwise equal size (Eckhardt). [D·v3]
5. **Do results persist or revert?** Rank correlation of strategy performance in window t vs t+1
   in the ledger, against the monkey, by asset/timeframe/family. Decides whether the portfolio
   rotates toward recent winners or buys strategy dips; Lescarbeau and Faulkner disagree.
   [D·v5, top-30 #24]
6. Lower value: relative-strength rotation across markets/strategies and an RRG view [D·v2];
   weight by time survived out of sample (Taleb) [D·v2, craziness 2].

## 6 · Sizing and leverage

1. [AF✗] **Never size on the historical maximum.** The backtest's worst day or DD will almost
   surely be exceeded, and AlphaForge scales so the worst day hits the cap *exactly*. Instead: a
   high quantile of the OOS or MC distribution; survive **twice** the worst historical DD (Faith:
   price shocks understate DD ~2×); Hill et al.: size on 2× optimised MDD. [D·v4, v2; §5.5 "Inyectar
   los peores días", §5.7 "Riesgo de ruina", §5.6 "El descuento propio"]
2. **Fixed fractional risk in R,** never Kelly or optimal f on closed-trade lists (Fitschen,
   Williams). Builds carry no stop, so risk % is undefined: **ATR volatility sizing with a double
   cap** `min(risk/stop_dist, risk/(2·ATR))`. The "largest loss" denominator is a high quantile of
   OOS/MC losses, never the historical max, never from IS trades. [D·v3]
3. **Kelly only as a ceiling and brake** (Chan): min(half Kelly, tolerable DD / worst period
   loss), on the shrunk edge not the backtest's; with fat tails 1/7 Kelly was needed for a 50 % DD;
   rolling-window Kelly de-levers a decaying strategy without a switch. [D·v4] ⚠ Sources disagree:
   Fitschen and Williams reject Kelly except at tiny fractions — owner decision (§11).
4. **Drawdown-constrained Kelly** (Busseti-Ryu-Boyd 2016): convex, beats fractional Kelly at equal
   DD risk, and the constraint *is* the prop firm's DD. [D·v4]
5. **Whale curve:** plot geometric growth vs risk fraction and **stay at the end of the linear
   part**, not the peak ("the optimum is just before the cliff"); report the distance to the peak.
   [D·v3]
6. **Volatility targeting is procyclical:** vol floor (crisis vol or long-run 25th percentile),
   cap on the multiplier (≤ 1.5× average size), never size up to hold returns as edge shrinks.
   Test with and without the floor on the worst days. [D·v4]
7. **Simulate MT5 margin and stop-out** trade by trade (leverage per instrument, margin call and
   stop-out levels, weekend margin hikes); report the minimum margin level on the worst historical
   and MC path; reject anything near stop-out. [D·v3]
8. **Perfect-foresight leverage ceiling** per instrument and holding horizon, from M1 adverse
   excursion (Hite: never more than ~3:1). [D·v3, craziness 2]
9. **Risk of ruin** ≈ e^(−2a/d) as a control number, and the "runs-to-ruin margin": how many more
   consecutive losses than the worst observed the account survives. Minimum capital per strategy.
   [D·v2]
10. **Pyramiding and partial exits forbidden by default;** an added entry is only valid if it
    passes the same tests alone. [D·v2]
11. Meta-labeling (secondary model sizing or skipping a trade): only with purged CV and counted in
    the ledger. [D·v3, craziness 2]

## 7 · Portfolio Monte Carlo and stress

1. **Block bootstrap (~20 trading days, stationary) of the joint daily P&L matrix,** not trade
   shuffling: shuffling breaks simultaneous losses and understates DD (Faith pp. 199-205,
   Fitschen pp. 161-165). [D·v4, §1.11] ⚠ **Contradicts the owner's decision** to keep the trade
   bootstrap exactly for sizing (`docs/AgentPDFs/WORKFLOW.md`, "El Monte Carlo de bootstrap está
   FUERA"); already in `common/monteCarlo/POSSIBLE_IMPROVEMENTS.md`. Owner decision (§11). — [AF]
   no portfolio MC at all.
2. **Start-date distributions** (Fitschen): an equity curve from every possible start, measure
   the worst drop **below starting capital**, first-year return, time to first new high. No
   resampling, so it fits the owner's stance. 🤔 It is also exactly the shape of a prop firm's
   **static** total-DD rule. [D·v4]
3. **Rolling windows:** P(profit) over every L-month window (L = 1-24), IS vs OOS, against the
   monkey; shortest window with 100 % (and 95 %) positive windows = the patience given live.
   [D·v4]
4. [AF✗] **Redo the MAE stress.** AlphaForge turns *every* trade, winners included, into its MAE
   and books it on the close day. Better: the fill degradation toward each trade's MAE already in
   `common/monteCarlo/model/stress.py`, or 🤔 floating equity rebuilt from bars.
5. **Inject the asset's worst historical days** (SNB 2015, Brexit, Mar 2020, 2008, 5 Aug 2024 —
   Nikkei −12.4 %) on the positions open on those dates **and on random dates**, plus synthetic
   gaps of 5, 10, 20 ATR; report the hit in R and survival. A build without stop measures gap
   tails nowhere else. [D·v4]
6. **Maximum loss by scenario, not by probability:** what if price jumps X % against every open
   position at once; budget grows with the year's realised profit and shrinks after losses.
   [D·v3]
7. Per-strategy tail risks:
   - **Weekend gaps:** share of P&L and of the worst trades from positions held over the weekend,
     Friday-close-at-adverse-extreme split, a "flat on Friday" variant. XAUUSD gaps ≥ $5 in ~35 %
     of weeks. [D·v4]
   - **News windows:** split trades inside/outside high-impact windows, one pre-registered "flat
     before the event" overlay. In `funded/` the firm's news rule is a constraint. [D·v3]
   - **Rollover window** (~17:00 NY, spreads 5-20×): entries/exits inside it, re-costed. [D, §5.1]
   - **Broken budget:** trades exiting beyond the stop through gaps, per year, in R; "% of trades
     losing > 1.5R". [D, §5.4]
8. **The tail the sample cannot rule out:** rule of three, P(loss > kR) ≤ 3/N; Hill tail index on
   R and daily P&L (index < 2 → sigma-based machinery invalid, size on tail-aware risk); DD as a
   function of sample length (1, 2, 5 y). [D·v4, v3]
9. **Calibrate the MC itself:** count how often realised DD / worst month / worst run on fresh data
   break the 95th and 99th percentile (Kupiec exceedance test) and widen the bands by the measured
   factor. [D·v5, top-30 #15]

## 8 · Risk limits and overlays (every one pre-registered and counted)

1. **Portfolio heat** (sum of open risk) with caps total, per highly/loosely correlated group and
   per direction (Turtles 4/6/10/12 units); net risk = larger side − smaller side/2; correlated
   markets count as one. [D·v4]
2. **The last in a group to signal is the worst** (Faith, Fitschen): test on crossmarket output
   whether "first 2 of the group" or "strongest of the group" helps, with its cost in trades.
   [D·v4]
3. **Daily and monthly loss switches** (Trout −4 % day / −10 % month; Elder's 6 % rule) vs the
   uncut sequence **and vs random pauses of the same total length**; if losses do not cluster the
   switch only costs money. [D·v3]
4. **Equity-curve trading / smaller after losses only with positive serial dependence** (runs
   z < −2) measured on OOS trades, always vs constant size, judged by Sharpe or Ulcer; add
   E[R | previous signal won] vs lost with shadow trades. Davey: 9 in 10 strategies have none.
   `studies/readings/profitShape/dependence.py` already runs the tests. [D·v4, v2, v3]
5. **Abraham's seven gates** as a numeric starting rulebook: ~1 % risk of *base* (closed) capital,
   ≤ 10 long and 10 short, ≤ $2,000-2,500 risk per contract, ≤ 5 % risk per sector, nothing new
   while open profit > 20 % of base capital, margin/capital ≤ 15 %; failing trades are skipped,
   not resized. [D·v4]
6. **Open profit given back:** does open profit at the peak predict DD depth? From MFE/MAE. [D·v3]

## 9 · Metrics to rank and judge a portfolio

1. [AF✗] Replace "0.8 Ret/DD + 0.1 annual + 0.1 winning months" by window-robust metrics:
   **RAR%** (annualised slope of a regression of log equity) and **R-cubed** (Faith), recomputed on
   windows shifted 0-3 months at each end and taking the min/median [D·v4, §3.8]; **gain-to-pain**
   (annual profit / mean of the N largest DDs, N = years) [D·v3]; **mean annual DD**, **time under
   water**, **longest flat period** [D·v3]; **P(losing year)** as a headline [D·v3].
2. **Serious-losses sheet** before going live: DD episodes (depth, peak, trough, recovery,
   duration) for IS, OOS and MC percentiles, underwater chart, distribution of time to first new
   high after launch. [D·v3]
3. **2×2 table of monthly signs** vs buy-and-hold: the months the portfolio does *not* diversify.
   [D·v2]
4. Sharpe on daily mark-to-market equity, annualised with the asset's real session hours
   (§2.6). [D·v2]

## 10 · Funded account specifics (`funded/`)

1. **P(pass) and P(payout)** by Monte Carlo over the firm's rules; here the trade bootstrap is
   legitimate by the owner's own stance. The risk that maximises them is an inverted U; most
   first-week failures come from the daily cap. Pass rates 5-10 % (FTMO 9-10 %). [D·v4] Answers
   `DECISIONS.md` #6 from data.
2. **Rules to encode as constraints:** daily loss on floating equity by server day; total DD
   **static or trailing** per firm; minimum days; consistency; news windows. [AF] models only the
   first two, on closed P&L.
3. 🤔 **MT5 netting vs hedging:** on a netting account two strategies on one symbol net each
   other; this justifies AlphaForge's same-asset rule beyond diversification.

## 11 · Live: incubation, monitoring, retirement

1. **Pre-registered retirement conditions from the strategy's own distribution,** frozen in the
   ledger before the first trade; the certificate prints "broken at 95 % beyond this DD". Dunn
   fell 42 % then rose 430 %: retiring on feeling sells the bottom. [D·v4, §1.19]
2. **Incubation length from MinTRL** (Bailey-López de Prado) with each strategy's skew and
   kurtosis; `core/significance` already has PSR and min-track-record. [D·v4, top-30 #25]
3. **Size ramp:** start at 1/5; step up after two periods with live P&L and live slippage inside
   band; step down on any failure. [D·v3]
4. **Sequential monitoring** (CUSUM, SPRT, BOCPD, live PSR) against the **OOS** band, not a
   "t-test of the last 20", which inflates error by repeated looks; live losing run vs the
   binomial run-length law. [D·v4]
5. **Two-sided envelope** (exiting above is also an alarm) [D·v3]; **low frequency** — decide only
   at month end [D·v3]; **compare with peers** of the same asset, not zero [D·v3]; **re-admit each
   quarter** as if new [D·v3].
6. **Daily reconciliation** of live vs backtest and a missed-signal monitor; **shadow-track
   retired strategies** (regression to the mean flatters every "fix"). [D·v4]
7. Broker operations: **catastrophic stop on the server, always**; **capital cap per broker**
   (counterparty risk, MF Global); two brokers in parallel to measure execution; orders the broker
   cannot read. [D·v4-v2, §5.3, §5.4, §5.10]
8. **No manual overrides;** if any, logged as shadow and scored. Operator-unavailable switch.
   [D·v2, v1]

## 12 · AlphaForge — keep or redo, at a glance

| piece | verdict |
|---|---|
| Precomputed matrices, greedy independent-set seeding, per-pair caches | keep |
| Pairwise filters incl. co-loss, tail, rolling-recent, same-asset | keep, plus §4.2, §4.3, §4.4 |
| Four weighting methods + weight walk-forward | keep, equal weight as mandatory baseline, shrinkage on min-var |
| Expand-a-portfolio mode | keep → marginal-contribution admission (§3.2) |
| Combination search on the whole history | redo: by segment, counted in the ledger (§2.1, §2.2) |
| Scale to the exact worst day | redo (§6.1-6.5) |
| MAE stress | redo (§7.4) |
| Closed P&L on close day | redo: floating daily equity (§2.6) |
| Min-max 0.8/0.1/0.1 fitness | redo: equal-weight ranks, robust metrics (§2.7, §9.1) |
| Dashboards, xlsx/PDF exporter | do not port; `ui/` |

## 13 · Decisions the owner must take (mirrored in `DECISIONS.md` #7-#12)

1. Trade bootstrap or joint-daily block bootstrap for sizing (§7.1).
2. Capped fractional Kelly or pure fixed fractional (§6.2 vs §6.3).
3. Trade the plateau (clones) or treat siblings as one position (§4.4).
4. Keep near-survivors for confluence and portfolio, or the gate keeps deleting them (§3.1).
5. Which segment the portfolio selection may read, given `oos2` is reserved for steps 17-19 (§2.2).
6. An "unexplained, on probation" category with small capital (dossier §1.20).

Plus the six already in `DECISIONS.md` (same pool for funded and real, strategies per portfolio
and per symbol, weighting, correlation threshold and window, rebalancing, prop-firm rules — and
which firm).
