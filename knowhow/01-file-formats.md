# File formats

## `.sqx` — a strategy

🔬 It is a **ZIP**. Members: `META-INF/MANIFEST.MF`, `settings.xml`, `strategy_Portfolio.xml`,
`lastSettings.xml`, `version.txt`, `orders.bin` and one `Results/Main: <SYMBOL>_<feed>/dailyEquity.bin`.

- 🔬 **They are not all multi-MB.** Measured over the 15,971 `.sqx` on the master, 2026-09-04:
  min **28 KB**, median **226 KB**, p90 870 KB, max 15.4 MB. The size is `orders.bin` plus the daily
  equity curve — how much *result* the strategy carries, not how complex it is. `settings.xml` and
  `strategy_Portfolio.xml` stay in the tens of KB throughout. The old "a `.sqx` is about 6 MB" note
  was generalising from one large file, and it was the stated reason `core.sqxfile` had no golden
  test; `tests/fixtures/strategy.sqx` is a real 28 KB one.

- **Never hash the file to compare strategies.** The ZIP embeds timestamps, so identical strategies
  produce different file hashes. **Identity = SHA-256 of the inner `strategy_Portfolio.xml`.** Using
  file hashes inflated a 13,288-strategy corpus into 17,754 "unique" ones.
- **Get the symbol without parsing anything.** ZIP entry names contain
  `Results/Main: <SYMBOL>_<feed>/…` — e.g. `Results/Main: XAUUSD_DukasM1_Infinox_LOM_M30/`. Regex the
  namelist; do not open the 5.8 MB `settings.xml`.
- `strategy_Portfolio.xml` is plain XML, readable with no SQX running.
- 🔬 Indexing all 17,754 `.sqx` on this box takes **1.5 s** with 48 processes. It is cheap; do it
  rather than guessing. Tool: `sqx/inspect/index_sqx.py`.
- 📓 Do **not** try to parse `orders.bin` — private versioned format inside Java serialization. SQX
  exports the same data natively (`-tools action=orderstocsv`, see `04-export.md`).

- 🔬 **`dailyEquity.bin` IS parseable, and it is the way to get a period-by-period result without
  SQX.** Unlike `orders.bin` it holds no objects: after the `aced0005` stream header it is nothing
  but Java block-data markers — `0x7a` with a 4-byte length, `0x77` with a 1-byte one — whose
  concatenated payload is an int count followed by that many `(big-endian int64 epoch millis,
  big-endian float64)` pairs. The value is **cumulative P&L in account currency**, not balance, one
  point per calendar trading day. Measured 2026-09-06 on `XAUUSD/OOS`: 3,946 points per strategy
  spanning 2007-11-02 → 2022-12-29. `core/sqxstats.equity()` reads it.
  This is what makes an arbitrary sub-period study possible — SQX's own sample types are only
  IS/OOS/full, so splitting the OOS in two is impossible through any export but trivial from here.

- 🔬 **`optimizationProfile.bin` is a strategy's SPP / optimization profile, and it parses.** It
  appears only in a `.sqx` that went through a cross-check driving the optimizer (Sys. Param
  Permutation, sequential optimization); 225 of the `.sqx` under the master's `user/projects`
  carry one, 2026-09-10.
  Framing is the same block-data stream as `dailyEquity.bin`. Layout, read straight off
  `OptimizationProfile.readFormat2` in `internal/libs/SQTradingLib.jar`:
  int format (2) · boolean *kept* · **if kept**, the original result and every permutation
  (`writeUTF` params + an `SQStats` blob each) · three int-keyed maps of 135 entries — medians,
  original values, and one JSON histogram per metric · `writeUTF` of the permuted parameter names ·
  `writeUTF` of the profitable/losing counts · five ints and six doubles of run statistics ·
  `writeUTF` of the profit distribution chart. `core/optprofile.py` reads it.

  🔬 **`kept` follows *Settings → Performance → "Don't store data for 3D charts in Optimization
  profile"*** (`user/settings/settings.xml`, `<dontStoreOP3DChartsData>`). Ticked, the
  per-permutation results are dropped at save and only medians and histograms survive; a saved
  strategy never recovers them, the SPP has to be re-run. Unticking it on 2026-09-10 and re-running
  `XAUUSD/SPP IS` took each `.sqx` from **125 KB to 2.2 MB** and stored 4,309 permutations for one
  strategy. `Infinox_SP500ft_H4_HighPrecision/SPP` carries 29 more from an earlier era.

  🔬 **A permutation is `params` + `SQStats` and nothing else, so SPP permutation trades do not
  exist.** This is now read off the format, not inferred: `SQStats.deserialize` is a loop over one
  byte-tagged record type each — `1` int, `2` long, `3` float (double when the stats format is 1),
  and `101`/`102`/`103` the same three under a name — and `default:` throws. `SQStats` does own an
  `objectMap`, but **`serialize` never writes it**. No order list is reachable from the profile.

  🔬 **`SQUtils.writeUTF` is not `writeUTF`**: a marker byte, then a 2-byte length when the marker is
  1 and a 4-byte one otherwise, then UTF-8. `OptimizationTestResult` and the named `SQStats` records
  use it; the chart strings in the tail use the plain Java form.

  🔬 **The `SQStats` array indices are the same key space `core/sqxstats.py` decodes from the base64
  XML blob**, and the binary form gives a way to calibrate them wholesale: the profile's own
  medians/original table is name-keyed, so matching the original result's stats against it named
  **79 of the 116 indexed slots** (`core/optprofile_stats.json`); the rest arrive already named, for
  118 of 152 in all, and the last 34 are 0 everywhere. `docs/manual/09-diccionario-spp.md` is the
  full field-by-field inventory. `core/sqxstats.KEYS` still carries only its original 14 — extending
  it from this file is an open, cheap win.

  🔬 **The 135 metric keys are `SQUtils.betterHashCode(<DatabankColumn simple name>)`**, and that
  method ships in `internal/libs/SQLib.jar`, which is **not on disk** — the launcher loads it as an
  embedded resource. The hash is not `String.hashCode` with any of the usual finalisers (tested), so
  the names were recovered by **matching the stored original values against a 135-column databank
  export of 50 SPP strategies**; the map lives in `core/optprofile_columns.json`. 101 of 135 are
  verified one to one, 6 more are known to a pair (`Exposure`/`ExposurePosition`,
  `Outlier`/`Outlier2`, `CalmarRatio`/`AnnualPctReturnDDRatio` — each pair's two members are equal
  on all 225 profiles, so they cannot be told apart here) and are suffixed `?`. The remaining 28 are
  exactly 0 in every strategy and stay as `id:<key>`.

- 🔬 **`SQStats` decodes completely, and it holds 152 statistics, not 14.** The blob is a flat
  record stream: a type byte, then either a one-byte metric id or -- when the type byte is over 100
  -- a `writeUTF` name, then the value (1 int, 2 long, 3 float, big-endian). On this install every
  blob is 116 id-keyed records followed by 36 self-naming ones (`SortinoRatio`, `RecoveryFactor`,
  `UlcerIndex`, `ProbSharpeRatio`, `EdgeDecayRatio`, `MaxNewHighDurationFrom/To`, the `AddMarkets*`
  medians…). The old reader stopped at the first type byte it did not know, which was the start of
  the named tail, so **a quarter of every blob was silently discarded**. `core/sqxstats.records()`
  reads all of it.

  🔬 The id-keyed half is named by `core/sqxstats_columns.json`, **shared with `core/optprofile.py`**
  (it replaced `optprofile_stats.json`). 79 of the 116 ids are named. Calibrated 2026-09-10 by
  exporting XAUUSD/WFM through a generated 107-column databank view and matching the values against
  each strategy's own blob; that agreed with the earlier, independent optprofile calibration on
  **76 of 76** shared slots. Four ids carry `?` because their pair's two members are equal on every
  strategy here (`AnnualPctReturnDDRatio`/`CalmarRatio`, `AvgTrade`/`Expectancy`); the remaining 37
  are exactly zero everywhere and stay `stat:<f|i|l>:<id>`. Three ties were broken by arithmetic
  inside the blob rather than left ambiguous: `AnnualPctReturn` is `NetProfitPct / TotalDataYears`,
  `TotalDataYears` is `floor(TotalDataMonths/12)`, and `ExposurePosition` is in the named tail so the
  id-keyed twin must be `Exposure`.

- 🔬 **A Walk-Forward Matrix cross-check writes its whole grid into `settings.xml`**, under
  `<WalkForwardResult type="…WalkForwardMatrixResult"><MatrixResult>`. `MatrixResult` carries the two
  axes as ranges (`start1/stop1/increment1` is the OOS percentage, `start2/…` the number of runs;
  `periodType=10` is a **rolling** window, measured: IS and OOS keep a constant length and
  slide, they do not expand). Under it, one `<RunResult>` per cell -- 5 x 6 = 30 on
  XAUUSD -- each with the parameters it settled on, a `stats` blob and a `statsOOS` blob. Under each
  cell, `<Periods>` holds one `<WalkForwardPeriod>` per step with `optimizeFrom/To`, `runFrom/To`,
  `futurePeriod`, the `testParameters` the optimiser picked on that window, and two more blobs:
  `OptimizationStats` (in sample) and `RunStats` (out of sample). 30 cells x 12 steps = 360 steps,
  1,212 blobs, 2.9 MB of XML. `core/wfmatrix.py` reads it; no SQX needed.

  🔬 **`RunResult/stats` is the FULL period, not the in-sample one**, even though it sits beside a
  field called `statsOOS`. Reading it as in-sample is a silent, plausible-looking error -- it was
  made here and caught by additivity. The cell's own `<Result>` element carries **15 blobs**,
  direction (0 both, 1 long, -1 short) x sample, and those are unambiguous: sample **10 is the first
  optimisation window alone**, **20 every walk-forward run concatenated**, **127 the two together**.
  Verified on two strategies: 532 + 559 = 1,091 trades and 2,389 + 4,185 = 6,574 days, exactly.
  `RunResult/stats` equals sample 127 and `statsOOS` equals sample 20. Samples 11 and 21 duplicate
  10 and 20 on this install. Take a cell's metrics from the `<Result>` blobs, never from `RunResult`.

  🔬 **The WFM panel's own numbers live in `SpecialValuesMap`, not in the matrix**: one
  `ParametersStability_WF_<runs>_runs_<pct>_OOS` per cell plus `AvgParametersStability` and
  `WorstParametersStability`, `FiltersResultFailedReason` (the acceptance verdict in words),
  `WalkForwardConditions` (the conditions it was judged against), and one `MEC_FULL_WF_<cell>`
  sparkline JSON for the cell SQX chose. The four WF-only databank columns
  (`WFPctOfProfitableRuns`, `WFMaxProfitByRunInPct`, `WFMinTradesInRun`, `WFMaxPctDDbyRun`,
  `resultType="WalkForwardMatrix"`, `subresult` 30/31/33) are **not** stored as numbers -- they are
  recomputed from the matrix, and all four are derivable in Python from the steps table.

  🔬 **The last step of every cell has an empty `RunStats`.** It is optimised on the tail of the
  history and there is nothing left to run it on, so it is `futurePeriod="true"` and carries no OOS
  statistics at all -- not zeros, no element. Drop those 30 rows per strategy before correlating.

- 🔬 **The per-step optimisation population is not stored, and the 3D-charts setting does not change
  that.** `<MaxTests>10000</MaxTests>` in `lastSettings.xml` says each step tries up to ten thousand
  parameter sets; only the winner survives into `WalkForwardPeriod`. Tested directly 2026-09-10: the
  owner re-ran the WFM on two strategies with *"Don't store data for 3D charts in Optimization
  profile"* switched **off**, and the new `settings.xml` came out **structurally identical** -- same
  360 periods, same 1,212 blobs, no new tags. The setting governs `optimizationProfile.bin`, which
  only an SPP or sequential-optimisation cross-check creates, and a WFM strategy has none. The same
  run did light up SPP: the five strategies in `XAUUSD/SPP IS` now carry `kept=true` with 3,940 to
  4,523 permutations each, params plus 152 statistics apiece -- but one sample only, no IS/OOS split.
  **So the closest thing to "every parameter set with its IS and OOS result" is the 360 walk-forward
  steps, not the optimiser's population.**

- 🔬 **A Monte Carlo Retest cross-check stores every simulation's P/L, and nothing else per
  simulation.** Measured 2026-09-17 on the ten `.sqx` of `XAUUSD/databanks/MC Random IS` and
  `MC Random IS 2.0` (4,896 simulations). Three new members appear under
  `Results/Main: <SYMBOL>_<feed>/`:
  `MonteCarloRetest_Results.xml`, `RobustnessOriginalOrders.bin`, and one
  `MonteCarloRetest_Simulation<N>Orders.bin` per simulation.

  **The `.bin` format is a 4-byte big-endian trade count followed by that many big-endian int32
  P/L values in cents, in chronological order.** `size == 4 + 4*count` held on 4,896 of 4,896
  files. It is *not* the `orders.bin` private format — no dates, no prices, no MAE/MFE, no size,
  no direction. Four bytes per trade is the whole record, so per simulation the only recoverable
  object is the P/L vector and everything derivable from it (equity path, drawdown, streaks).
  `RobustnessOriginalOrders.bin` is the same format for the original backtest and is the bridge:
  summing it gives `NetProfit` to within the cent rounding (24,268.56 vs a stored 24,269.22 on
  `Strategy 1.19.29`, 763 trades).

  🔬 **Simulation indices are contiguous and truncate at the tail; they never have holes.** Three
  of the ten runs stopped early (499, 440 and 457 of a declared 500) and in all three the surviving
  indices were `0..n-1`. So a short run is lost sample, never selection bias.

  🔬 **`MonteCarloRetest_Results.xml` holds one `SQStats` blob for the original (152 metrics) plus
  eleven `LevelStat` blobs, one per confidence level — 50, 60, 70, 80, 90, 92, 95, 97, 98, 99, 100
  and no others.** The level blobs carry 148 metrics; they lack `DataLength` and
  `MaxNewHighDurationFrom/To/Pct`. Of the 148, **97 move with the level and 51 are constant**
  (the Walk-Forward and Add-Markets holes, `Fitness`, `Complexity`, `ParameterCount`,
  `TotalDataDays/Months/Years` and 34 slots that are zero everywhere). Unlike the main result,
  this XML stores **one direction and one sample only** — there is no long/short or IS/OOS split
  inside a retest result.

  🔬 **A confidence level is a per-metric marginal order statistic, not a simulation.** Level `L`
  of metric `m` is the value at rank `n*(100-L)/100` of the `n` simulations sorted so that worse
  is later — reconciled against the stored table on 9 of the 10 files to under 1 unit, i.e. to the
  cent rounding of the P/L, for both `NetProfit` (higher is better) and `Drawdown` (lower is
  better). The tenth is the 499-simulation run, where the table was written over 500 and every
  rank is shifted by one. **Consequence: the "95% confidence" row is not a scenario** — its
  NetProfit and its Drawdown come from different simulations, so no row of that table is a
  coherent equity curve and the pair must never be read as one.

  🔬 **The ~61 metrics that need dates or prices are lost per simulation but survive as those
  eleven quantiles.** `AvgBarsInTrade`, `Exposure`, `BiggestMAE`, `TotalMFE`, `Efficiency`,
  `EdgeRatioInPips`, `ExitQuality`, `RExpectancy`, `Stagnation`, `MaxNewHighDuration`,
  `TotalTradingDays`, `CAGR`, `ProfitableMonthsPct`, `EquityAngle`, `AmbiguousTrades`,
  `OpenDrawdown`, `MaxTSIntradayDrawdown`, `SortinoRatio` and `ProbSharpeRatio` all vary across
  the levels, so SQX did compute them per simulation and threw the individuals away. Eleven points
  of a marginal CDF is far less than 1,000, but it is not nothing — it is the only channel for any
  MAE/MFE or duration question about a retest.

  🔬 **The full method configuration is in `lastSettings.xml` under `<MonteCarloRetest>`**, with
  every one of the ten methods listed whether used or not, each with its own `<Params>` — so the
  exact perturbation that produced a databank is recoverable without reading the prose in
  `<Method>`. The ten types: `RandomizeExitParameters` (bentra's script), `RandomizeHistoryData`
  (by tick), `RandomizeHistoryDataFixedRange`, `RandomizeHistoryDataOHLC`, `RandomizeMinDistance`,
  `RandomizeSlippage`, `RandomizeSpread`, `RandomizeStartingBar`, `RandomizeStrategyParameters`
  and `RandomizeStrategyParametersCustomizable` (the last one adds per-kind switches: Period,
  Shift, Constant, OtherParam, ExitUsed, ExitUnused, Boolean, TradingOptions). Beside them sit
  `<NumberOfSimulations>`, `<MCUseFullSample>` and `<MCBacktestPrecision>`.

  🔬 **`MCUseFullSample=true` does not mean the run saw out-of-sample data.** Both XAUUSD
  databanks have it set and both ran `2008.01.01 - 2017.12.31` with sample 20 empty in all five
  strategies. The toggle widens the retest to whatever the strategy's own sample split is; when
  the strategy was retested IS-only, "full" is IS. Check `NumberOfTrades` on sample 20 of the main
  result before reading any retest as out-of-sample.

  🔬 **A re-run overwrites: one `.sqx` carries exactly one MC Retest result.** The two XAUUSD
  databanks are the same five strategies with different method sets, and each file holds only its
  own. Isolating perturbation methods therefore costs one databank per method — there is no way to
  keep several retests inside one strategy file.

  🔬 **Calibrating reconstructed formulas against the stored original settles four ambiguities the
  metric names invite.** Run on `Strategy 1.19.29`'s original P/L vector, agreement to the stored
  value is exact (relative error < 2e-3) for NetProfit, GrossProfit/Loss, NumberOfTrades,
  NumberOfProfits/Losses, WinningPct, AvgWin, AvgTrade/Expectancy, StandardDev (ddof=1), Drawdown,
  ReturnDDRatio, MaxProfit/MaxLoss, MaxConsecWins/Losses, AvgConsecWins/Losses and KellyFormula.
  The four that do **not** mean what they look like:
  - **`WinLossRatio` is the count ratio `#wins/#losses`** (459/304 = 1.51), **not** the ratio of
    average win to average loss. **`PayoutRatio` is that one** (0.88). They are different columns,
    not two names for one quantity, and `KellyFormula` uses `PayoutRatio` as its `R`.
  - **`AvgLoss` is stored positive** (an absolute value), so a signed reconstruction is off by −2×.
  - **`SQN` is `sqrt(min(n,100)) * mean / stddev`, not `sqrt(n) * …`** — 0.768 against a stored
    0.77, where the textbook Van Tharp form gives 2.12 on 763 trades.
  - **`RSquared` is measured on the daily equity curve, not on trade-indexed equity** (0.9146 vs a
    stored 0.92; trade-indexed gives 0.897). `Stability` (0.81) and `StabilitySQ3` (0.86) are
    separate quantities and neither is that R², still uncalibrated.
  🔬 **The eleven confidence levels are a far stronger calibration oracle than the original.** A
  candidate per-simulation formula is the one SQX used only if its own order statistic reproduces
  the stored level table; that is 11 levels x 5 strategies = **55 constraint points per metric**
  instead of the single value the original offers, and it tests the formula on perturbed data
  rather than on one point. Run that way on `MC Random IS 2.0`, four more fall (worst relative
  error over all 55 points in brackets), all against a *capital-relative* drawdown with
  `MoneyManagement.InitialCapital` = 100,000:
  - **`DrawdownPct` = max of `dd_k / (capital + peak_k)`** [7e-4] — not `dd/peak`.
  - **`AvgDrawdown` = the mean of `dd_k` over EVERY trade, zeros included** [4e-5]. Averaging only
    the points in drawdown is wrong by 11%, averaging episode maxima by 67%.
  - **`AvgPctDrawdown` = the same mean of `dd_k / (capital + peak_k)`, zeros included** [2e-3].
  - **`RecoveryFactor` = NetProfit / (DrawdownPct x capital)** [5e-3, at the limit of the stored
    2-decimal precision] — i.e. it divides by the capital-relative drawdown, which is why it
    differs from `ReturnDDRatio` = NetProfit / absolute `Drawdown`. The two are **not** synonyms.
  - **`ZScore` carries a +0.5 continuity correction**: `(R - mu_R + 0.5) / sigma_R`. The offset
    matches `0.5/sigma_R` on all five originals and cuts the oracle error from 0.046 to 0.014.

  🔬 **`SharpeRatio`, `SortinoRatio`, `UlcerIndex`, `RSquared` and `Stability` are NOT
  reconstructible per simulation**, and the oracle says so rather than leaving it a suspicion.
  Sharpe-per-trade fails the level table by 70% and its sqrt(12) rescaling by 56%; every
  trade-indexed Ulcer variant fails by 61% or worse. These are computed on the **daily equity
  curve**, which exists for the original (`dailyEquity.bin`) and for no simulation. Any
  per-simulation version is a declared analogue, never a replication -- and must not be compared
  against the value SQX stores for the original.

  🔬 **Validated at scale on the eight isolated-task databanks** (`MCR 1 Bar` .. `MCR 8 Stress`,
  5 strategies x 1,000 simulations, 39,996 in all, 2026-09-18): **13,200 checks of 30 metrics x 11
  levels x 5 strategies x 8 tasks reconcile, with 16 isolated failures (0.12%)**, all single levels
  in the two widest-dispersion tasks (5 and 8) and all consistent with rank ties rather than wrong
  formulas. That run forced two more corrections:
  - **`StandardDev` is the POPULATION standard deviation, `ddof=0`.** With `ddof=1` the worst error
    over the level tables is 0.47; with `ddof=0` it is 0.008. `SQN` cannot tell the two apart
    (the difference is below its 2-decimal storage), so `StandardDev` is the only column that
    settles it -- and any Sharpe-per-trade analogue must use `ddof=0` too, or it will not be the
    same quantity SQX reports.
  - **Every metric needs a ranking direction, and the losing half of the table runs the other
    way.** Level 100 of `Drawdown` is the *deepest* fall while level 100 of `NetProfit` is the
    *smallest* profit. Eleven of the reconstructible metrics rank worse-when-higher:
    `GrossLoss`, `Drawdown`, `DrawdownPct`, `AvgDrawdown`, `AvgPctDrawdown`, `NumberOfLosses`,
    `AvgLoss`, `StandardDev`, `MaxConsecLosses`, `AvgConsecLosses` and `MaxLoss`. Ranking them
    the common way produces relative errors of **0.88 to 0.94** against the stored table — big
    enough to be obvious, which is the only reason it was caught.
    **`MaxLoss` being in that set is a trap for the reader, not just for the code**: its level
    100 is the worst trade *closest to zero* (-1,743 on `MCR 5 Params / 23.16.37`, while the
    actual worst simulation had -8,494), so a high-confidence `MaxLoss` read as a stress number
    is backwards.
  - Still unresolved: **`AvgAbsTrade`** sits at a constant ratio of 1.00215 to `mean(|p_i|)` across
    every level and task -- systematic, small, formula unidentified. It is also nearly invariant
    across simulations, so it carries almost no information for a robustness study; exclude it or
    mark it approximate rather than trusting it.

  **Net result: 29 of the 97 varying metrics are exactly reconstructible per simulation** from the
  P/L vector alone -- NetProfit, GrossProfit/Loss, NumberOfTrades/Profits/Losses, WinningPct,
  AvgWin, AvgLoss, AvgTrade, Expectancy, AvgAbsTrade, StandardDev, Drawdown, DrawdownPct,
  AvgDrawdown, AvgPctDrawdown, ReturnDDRatio, RecoveryFactor, MaxProfit, MaxLoss,
  MaxConsecWins/Losses, AvgConsecWins/Losses, ProfitFactor, PayoutRatio, WinLossRatio,
  KellyFormula, SQN and ZScore. The rest need dates, prices or daily equity and exist only as the
  eleven quantiles.

## `project.cfx` — a project

🔬 Also a **ZIP**: `config.xml` + one `<TaskType>-Task<N>.xml` per task. Reading is safe at any time —
no SQX process needed, no state touched. `sqx/inspect/dump_project.py` renders one as Markdown.

- 🔬 **SQX rewrites the whole `project.cfx` on save and on exit.** All 14 project files were restamped
  within the same second (`14:33:43`, 2026-09-02). **Any on-disk edit to a project a running instance
  holds is silently discarded.** No error. Use the `-project` API instead (`03-driving-sqx.md`).
- 🔬 `config.xml`'s `<Task title=>` is a **display label only**. The task's real output databank lives
  inside the task XML at `<Databank name="Output" value=>`. Clone a task without changing that and
  every clone writes to the same databank.
- 🔬 `<Databank … value="null">` is not a bug — `null` is SQX's literal for "use the task type's
  default databank". Build tasks ship this way.
- 🔬 A `.cfx` with **only `config.xml`** is not a loadable project template. Both
  `~/Desktop/Benchmark.cfx` and anything `saveconfig` produces are single-file and rejected.
- 🔬 **The opposite failure exists too: a `config.xml` declaring task files the archive does not
  hold.** The GUI then drops the project with no error at all. Scan every project for it with
  `sqx/inspect/project_health.py`; heal one with `sqx/repair/graft_tasks.py`.
- 🔬 **`<Project templateFile=>` in `config.xml` is dead metadata, and is not the strategy template.**
  It records the `.cfx` the project was imported from. On this install it is a Windows path on every
  project imported off Windows, re-encoded UTF-8-as-CP1252 **seven times over**; decoded it reads
  `C:\Users\Rubén Martínez\OneDrive\Escritorio\FILTROS\Build strategies.cfx`. The strategy
  template that actually matters is `<StrategyType templateFile=>` inside the Build task.
  `project_health.py` decodes any such field.
