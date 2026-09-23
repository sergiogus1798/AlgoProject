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

- 🔬 **A `.sqx` retested with a cross-check carries THREE `dailyEquity.bin`, and the one you want is
  not the first.** Measured 2026-09-22 on the variant batch of `Strategy 17.9.39`, retested by a
  harness whose task holds an XAGUSD cross-market check. The archive holds, in this order:
  `Results/Portfolio/dailyEquity.bin`, `Results/Main: XAUUSD_DukasM1_Infinox_LOM_M30/…` and
  `Results/AdditionalMarket: XAGUSD_…/…`. On `P00000` their final values are **10,476 / 35,328 /
  −24,852**: `Portfolio` is gold plus silver, and only `Main` matches the `Net profit` the databank
  shows. `core/sqxstats.equity()` now takes the result by name and defaults to `Main`; taking
  whichever member appears first silently studies a two-market portfolio.

- 🔬 **The daily curve and the stored net profit disagree exactly when a position is open on the
  last bar.** Same batch, 2026-09-22: at the in-sample boundary all 962 curves matched the stored
  `Net profit (IS)` to within **0.59 $** (float32 storage against two decimals in the panel), but
  over the whole history 172 of them ran 95 to 332 $ below it. Those 172 average **551 out-of-sample
  trades against 186** for the rest — they trade often enough to be holding something when the data
  ends, and SQX marks that to market in the curve while net profit counts only closed trades. So:
  **reconcile a harvested curve at a window boundary, never at the end of the file**, and any study
  aggregating the curve into periods should drop the last one.

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

- 🔬 **A strategy declares its own tunable parameters, and that list is authoritative.**
  Every one is a `<variable>` in `strategy_Portfolio.xml` carrying `id`, `name`, `type` (`int` or
  `double`), `value` (the current setting) and `paramType`. The `paramType` values seen on this
  install -- `ParamTypePeriod`, `ParamTypeShift`, `ParamTypeConstant`, `ParamTypeOtherParam`,
  `ParamTypeExitUsed` -- are exactly the classes a task's `<WhatToParametrize>` switches on. Checked
  against what SPP actually permuted on all 5 XAUUSD strategies: **the variable list and the permuted
  list match one for one** (8 of 8, 11 of 11). No block catalog lookup is needed to enumerate them.

  🔬 **The ranges SQX builds are per class, and a percentage is not one of them for shifts.**
  Measured off the stored permutation domains (settings: +/-30 %, 20 steps): `ParamTypePeriod`,
  `ParamTypeConstant` and `ParamTypeExitUsed` get +/-30 % of the original, stepped and rounded --
  `DICrossPeriod1` 67 -> 46..88, `ATRPrcRnkCrsDwnLvl1` 48.76 -> 34.13..63.20 at 2 decimals. Every
  `ParamTypeShift` instead gets a flat **0..6** whatever its value. ⚠️ **A percentage range collapses
  on small integers**: `MomentumPeriod1` = 14 yields only 10 distinct values out of 20 steps, and
  `IsBars1` = 3 yields 5. A generator that uses percentages alone will silently produce a much
  coarser grid than it thinks for every small-valued parameter.

  🔬 **A declared parameter can be completely inert, and the permutation table proves it
  cheaply.** Group the permutations by every parameter but one; where a group holds more than one
  permutation, they differ only in that parameter. `CBlock_SqzMmnInt21` on `Strategy 17.9.39`:
  **757 comparable groups, 757 with byte-identical `NetProfit` and trade count** -- the parameter
  does nothing, and its 13 values multiply the grid for free. Same on `Strategy 23.16.37` (338 of
  338). On `Strategy 41.5.25` the same name is *nearly* inert: 287 of 302. Dropping it shrinks those
  grids by 13x. The test doubles as proof that **the engine is deterministic**: identical parameters
  reproduce identical results to the last decimal.


- 🔬 **Writing a variant of a strategy is four changes to two members, and nothing else.** Verified
  end to end 2026-09-21 on `XAUUSD/Strategy 17.9.39` and on `tests/fixtures/strategy.sqx`: rewrite
  → repack → read back → values correct, and every untouched member byte-identical.
  1. the tuple, in `strategy_Portfolio.xml`, `<variable><id>NAME</id>…<value>N</value>`;
  2. the name in `settings.xml`, **twice** — `<ResultsGroup ResultName="…">` and
     `<StrategyName type="String">`. Miss one and the whole batch lands under a single name;
  3. the `<Fingerprint …>…</Fingerprint>` element of `settings.xml`, **removed** — every variant
     inherits the parent's, and the outer element's only child is self-closing, so a non-greedy
     `<Fingerprint\b.*?</Fingerprint>` cuts exactly the right span;
  4. the variant's own identifier, as an XML comment after the declaration of
     `strategy_Portfolio.xml`. The external name cannot be the identity because SQX may rename on
     collision.
  Do it by **string substitution, not an `ElementTree` round trip**: the round trip reformats
  attributes, self-closing tags and whitespace across a file SQX parses with its own reader, and
  buys nothing. `sqx/variants/build/rewrite.py` does it; `tests/test_variants.py` holds the byte
  identity as an invariant.

- 🔬 **The tunable parameters are exactly the variables with a non-empty `<paramType>`.** The
  others — `MagicNumber`, the four direction booleans — carry a UUID as their `<id>` and an empty
  `<paramType />`, while every tunable has its own name as its id. Seen on `Strategy 17.9.39`
  (8 tunables of 13 variables) and on the USDCHF test fixture (7 of 9). No catalog lookup needed.

- 🔬 **SQX writes an integral `double` with no decimal point**, so a variant must too: the fixture's
  `TrailingStop1` is declared `double` and stored `50`. `%g` reproduces the file's own convention.
  An `int` variable written `67.0` instead of `67` is a different file, and the type is declared
  right there in the block being rewritten.

- 🔬 **"A full `.sqx` is 5.2 MB" does not generalise, and the 26 GB it implies for 5,000 variants is
  wrong by forty times.** Measured 2026-09-21 on `XAUUSD/Strategy 17.9.39` as the repack actually
  writes it — full **123.3 KB**, without `optimizationProfile.bin` **98.7 KB**, and the five-member
  form (`META-INF`, `settings.xml`, `strategy_Portfolio.xml`, `lastSettings.xml`, `version.txt`)
  **13.7 KB**. For 5,000 variants that is 631 MB, 505 MB and 70 MB, fabricated in 65 s, 49 s and
  6 s. The 5.2 MB figure belongs to a parent whose SPP profile was **kept** — the 2.2 MB
  `optimizationProfile.bin` the 3D-charts setting produces — so the size of a batch depends on how
  its parent's cross-check was configured, not on the strategy.

- 🤔 **A fabricated variant carries the parent's results until it is retested**, in every shape but
  the five-member one: `orders.bin`, `dailyEquity.bin` and the `SQStats` blobs in `settings.xml` are
  the parent's. So a variant that silently never ran does not look empty, it looks like the parent.
  Nothing readable off the file distinguishes the two; only a canary with a known different result,
  or the databank count, can. It is the strongest argument for the five-member shape — and 🔬 SQX
  does load one: settled 2026-09-21, see *The five-member `.sqx` and databank de-duplication* below.

- 🔬 **A sequential-optimisation cross-check writes plain XML, not a binary profile.** The
  `.sqx` gains `Results/Main: <SYMBOL>_<feed>/SequentialOptimization_Results.xml` (11 KB, root
  `<ChainOptimizationResults>`) and, on this install, **no `optimizationProfile.bin` at all** -- the
  two cross-checks do not share a container. One `<Parameter originalValue="…">` per optimised
  variable, each holding the variable definition, a `;`-separated `<Values>` list (30 steps over
  +/-30 % here, rounded, so 30 or 31 distinct values), a `;`-separated `<Fitness>` of the same
  length, and `<Results>` with `BestValue`, `BestAreaStartValue/EndValue` and `StableAreaFound`.
  Trivial to parse with `ElementTree`, no SQX running.

  🔬 **Only fitness is stored -- one scalar per point, never an `SQStats` blob.** Where an
  SPP permutation carries 152 statistics, a sequential-optimisation point carries a single number in
  [0,1]. Any study over this surface is a study of the fitness function the task was configured with.

  🔬 **`BestValue` is the centre of the stable area, not the argmax of the scan** -- it is
  the scan's best point on only 5 to 9 of each strategy's parameters. Reading it as "the best value
  found" is wrong.

  🔬 **The scan is chained: parameter k is measured with parameters 1..k-1 already fixed at
  the values this run chose.** Proven off the file rather than assumed -- the fitness at parameter
  k+1's *original* value equals the fitness at parameter k's `BestValue` on nearly every link
  (7/7, 7/7, 6/6, 8/9 on four of the five XAUUSD strategies; the misses are the links where
  `BestValue` is not the argmax). So the fitness at the original value **differs from parameter to
  parameter inside one run** (8 distinct values across 10 parameters on `Strategy 1.19.29`), which
  is the cheap tell. Only the **first** parameter of the chain is measured on the untouched
  strategy.

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

## Metric formulas confirmed 2026-09-20 (SPP export, XAUUSD)

🔬 **`CalmarRatio?` = `CAGR` / `DrawdownPct`.** Verified over 20,554 rows with more than 50 trades.
The 1.9 % median relative error is entirely the two-decimal storage of a small number: 2.20 / 5.52 =
0.3986 is stored as 0.40, 0.59 / 9.11 = 0.0648 as 0.06. It is a legitimate Calmar ratio.

🔬 **`CalmarRatio?` is byte-identical to `AnnualPctReturnDDRatio?`** — relative error 0.00e+00 on all
20,554 rows, rho = 1.0000. They are one column under two names; store one.

🔬 **`RExpectancyScore` is `RExpectancy` weighted by trade count.** It tracks `RExpectancy * sqrt(n)`
with rho +0.89 to +0.99 across the five strategies, at a per-strategy scale factor of 2.0 to 3.6
(exact formula not identified). It behaves as a t-statistic: the same edge scores higher when it was
measured on more trades. It is **not** redundant with `RExpectancy` — rho between the two runs +0.856
to +0.976 — and it is the column that penalises the few-trade regions a grid study most needs to
distrust.

🔬 **`UlcerPerformanceIndex` is NOT reconstructible** — reconciled 2026-09-21 against 21,179 SPP
permutations and the attempt failed, which is the useful outcome. Its **functional form is
confirmed**: it tracks `AnnualPctReturn / UlcerIndex` at rho +0.998 (and `AHPR / UlcerIndex` at
+0.9993). But the proportionality constant is **not constant**. It sits near 16 (median exactly
16.0000 over the 1,440 rows with `UlcerIndex` >= 0.5) yet refuses to converge as precision
improves — restricting to rows where both values are large gives median 16.53 with a standard
deviation of 3.36, *worse* rather than better — and the residual correlates with `NumberOfTrades`
(+0.52) and `DataLength` (+0.50).

That rules out rounding and points at a time- or observation-dependent term absent from the 152
stored columns, which is consistent with `UlcerIndex` being computed on the **daily equity curve**
— the same reason `SharpeRatio`, `SortinoRatio`, `UlcerIndex`, `RSquared` and `Stability` are
already listed as non-reconstructible. **`UlcerPerformanceIndex` joins that list.** Do not compute
an analogue and compare it against the stored value; export the column and use SQX's.

Do not read the near-16 constant as a finding. sqrt(252) = 15.87 and 16 both sit inside the spread
and the data cannot separate them — fitting a constant and then naming it would be the mistake.

## Trade exports — what is derivable and what is not

🔬 Measured 2026-09-20 over the five XAUUSD strategies, 4,115 trades.

- **`Ticket` = the row order, and the row order is already sorted by `Open time`.** In all five
  files: zero duplicate open times, zero overlapping trades, and sorting by
  (`Open time`, `Close time`) reproduces `Ticket` exactly. Parquet preserves row order, so the file
  itself carries the ticket. ⚠️ These five hold one position at a time; a strategy that pyramids
  would have duplicate open times and the tie would not be resolvable, so **an ingest must check
  (sorted, no duplicates, no overlaps) per file and keep `Ticket` when the check fails**.
- **`Balance` = initial capital + cumsum(`Profit/Loss`)**, maximum deviation 0.17 over 763 rows —
  rounding of the two-decimal P/L, not a fee applied elsewhere.
- **`Time in trade` = `Close time` - `Open time`**, and is stored as text (`"2h 0m"`).
- **`Comment` is empty**: 763 of 763 null.
- **`Close type` is not disposable** — `Exit Signal` 662 / `Exit After X Bars` 83 /
  `End Of Friday (Time)` 18. Which one fires moves with the parameters, so a parameter-surface study
  needs it.

## The five-member `.sqx` and databank de-duplication — settled 2026-09-21

The two questions `sqx/variants/` was blocked on. Probed on the **conductor (W1, 5060)** with three
hand-made variants of `XAUUSD/SPP IS/Strategy 17.9.39` (`DICrossPeriod1` 55 / 60 / 70, distinct
`ResultName` and `StrategyName`, **parent `<Fingerprint>` deliberately left in**), loaded into a
fresh databank `Retester/ProbeA` with `-databank action=load folder=…`.

- 🔬 **SQX loads a five-member `.sqx`.** `META-INF/MANIFEST.MF` + `settings.xml` +
  `strategy_Portfolio.xml` + `lastSettings.xml` + `version.txt`, 15.0 KB as `zipfile` deflates it.
  All three landed (`Records: 3`), under their own names, and `-databank action=export` rendered a
  full metrics row for each. Dropping `optimizationProfile.bin`, `orders.bin` and
  `Results/…/dailyEquity.bin` costs nothing at load time. **So the 70 MB shape is the one to build.**
- ⚠️ **"Loads" here means loads, lists, exports and copies — not "retests".** No CLI verb exercises
  a strategy's *rules*; only a project task does, and on this install no worker project is wired to
  XAUUSD M30, so that half is untested. 🤔 The rules live in `strategy_Portfolio.xml`, which the
  five-member form keeps intact, so a retest is expected to work — but expected, not measured. The
  measurement is one retest task on W2 against the variant databank, and it should be the **first**
  thing the 5,000-variant batch does, on three files, before fabricating the rest.
  ✅ **Done 2026-09-22 — see *ANSWERED: a retest DOES rewrite the inherited `SQStats`* below.**
  A retested variant returns its own numbers; the five-member shape retests like a full one.

- 🔬 **The databank does not de-duplicate on the inherited `<Fingerprint>` — because on these write
  paths it does not de-duplicate at all.** This is the important correction: a bare "three variants
  went in, three came out" proves nothing, since it is also what a databank with no de-duplication
  whatsoever produces. The controls:

  | write path | action | records |
  |---|---|---|
  | `load` a folder of 3 variants into an empty databank | — | 3 |
  | `load` **the same folder again** | identical files, identical names, identical fingerprint | **6** |
  | `copy` those 6 into another databank | — | 6 |
  | `copy` **the same 6 again** into the same destination | — | **12** |

  Byte-identical files under the same name accumulate. There is no fingerprint check, no name
  check, no similarity check on `load` or `copy`.
- 📓 **The only similarity filter in a project lives in the builder, not in a databank.**
  `DismissTooSimilarStrategies` and `FreshBloodReplaceSimilar` appear in `Build-Task*.xml`
  (the generation loop); no `Retest-Task*.xml` and no `<Databank …>` registration in `config.xml`
  carries any de-duplication attribute. So the risk, if it exists anywhere, is on the **output of a
  retest task**, and that is the same untested path as the point above — one measurement settles
  both.
- 🔬 **Removing the parent `<Fingerprint>` is therefore prudence, not a requirement.** Nothing on
  the load path reads it. Keep removing it (it is wrong data, and the retest path is unproven), but
  it is not what makes the study possible.
- 🔬 **A databank created through `-databank action=create` does not appear on disk, and
  `synctofiles` does not make it appear.** `Retester/ProbeA` held 3 records through the API while
  `user/projects/Retester/databanks/ProbeA/` never existed, before or after an explicit
  `action=synctofiles`. Expect to read a fabricated-variant databank through `action=export`, not
  off the filesystem — and see `02-databanks.md`, which records the same memory-versus-disk gap
  from the other direction.

## The five-member shape does NOT strip inherited results — verified 2026-09-21 (evening)

Re-ran the probe on the **custodian (W2, 5070)** against the real output of `sqx/variants/`
(`python3 -m sqx.variants.make --limit 3`, `shape: minimal`), not hand-made files. It corrects the
🤔 above into a 🔬, and in the direction that costs the most.

- 🔬 **`settings.xml` carries 36 `SQStats` blobs, and the five-member form keeps `settings.xml`.**
  So dropping `optimizationProfile.bin`, `orders.bin` and `dailyEquity.bin` does **not** drop the
  parent's results. The earlier note argued the minimal shape was the strongest defence against a
  variant that silently never ran. It is not a defence at all.
- 🔬 **Three variants with genuinely different tuples export three byte-identical metric rows.**
  Loaded into `Retester/VerifA`, `action=export` rendered for all three: net profit `22650.2`,
  755 trades, PF `1.15`, Sharpe `0.38`, drawdown `8449.28` — the parent's numbers, to the decimal.
  The tuples inside the files really do differ (`DICrossPeriod1` 67 / 43 / 94, and seven more), and
  `<Fingerprint>` was removed from all three. Fabrication is correct; the *results* are inherited.

  | what is right | what is wrong |
  |---|---|
  | `P00000/1/2` keep their own names — no collision rename | every metric column is the parent's |
  | `Symbol`/`TimeFrame` correct (`XAUUSD_DukasM1_Infinox`, M30) | `Filters result: FAILED` is the parent's verdict too |
  | no de-duplication: 3 in, 3 out | nothing on the file distinguishes "not yet run" from "ran" |

- ⚠️ **This is failure mode 2 of `4-variantes.md` §4, and it is live.** A 5,000-variant batch read
  back today returns 5,000 copies of one row and looks entirely plausible. The **canaries are the
  only detector**, and they cannot fire until a retest has actually run. 🤔 A cheaper second
  detector is free and should exist: the collect step refusing a batch whose metric rows are
  identical across distinct `tuple_hash` values.
- **The measurement still outstanding is unchanged and is now urgent**: one retest task on the
  custodian against a variant databank, on three files, *before* fabricating 5,000. Nothing on this
  install is wired to XAUUSD M30 for it — `Retester` is a clean 1-task harness (no Build, no
  `GoToTask`) but its `Setup` points elsewhere.

- 🔬 **`-databank action=count` destroys an in-memory load; `action=export` does not.** Straight
  after `action=load` put 3 strategies in `Retester/VerifA`, `action=count` printed
  `Syncing databank(s) from files / Loaded 0 strategies to databank VerifA / Records: 0` — the count
  verb runs a sync-from-files first, disk holds nothing (see the note above), and the load is gone.
  Re-loading and calling `action=export` returned all 3. **Never verify a load with `count`.** It is
  hard rule 1 reaching through a verb that reads like a read.

## Does a retest rewrite the inherited `SQStats`? — attempted 2026-09-22, NOT answered

The question the variant study is blocked on. It is still open, but the attempt narrowed it a long
way and the narrowing is the useful part.

**What was built.** `Retester` on the custodian (W2, 5070) is a stock 1-task harness — no Build, no
`GoToTask`, so it is the safe place to run one. Its task was rewired to the donor's own retest
settings, taken verbatim from `AlgoData/projectsBackup/XAUUSD_base_2026-09-21/project.cfx`,
`Retest-Task1.xml`:

| | value |
|---|---|
| `Setup` | `dateFrom 2008.01.01` `dateTo 2022.12.31` `testPrecision 2` `slippage 0` `minDist 10` `engine MetaTrader5 (hedged)` |
| `Chart` | `XAUUSD_DukasM1_Infinox` M30 `spread 0` |
| `OutOfSample` | `Range 2018.01.01 → 2022.12.31` |
| cross-checks | off |
| acceptance conditions | all 30 set `use="false"`, so nothing is filtered out of the output |

Backup of the harness as it was: `AlgoData/snapshots/2026-09-21/w2-retester-before/project.cfx`
(md5 `593ea6ac11eeb600ed7a4e569dd1f910`).

- 🔬 **The task starts and tests nothing, silently.** `-project action=startOnlyTask name=Retester
  task=1` logs `=========== Project started ===========` and then `Total tested 0`, `In databank 3`,
  `Running time so far 0 ms`, forever. No error, no `Project finished`. Tried with input and output
  on the same databank and on separate ones; same result.
- 🔬 **It is NOT the five-member shape.** The control settles it: the **parent itself**, the full
  126 KB `Strategy 17.9.39.sqx` straight out of `raw/XAUUSD/SPP_IS/2026-09-10/strategies/`, loaded
  alone into the same databank, retests exactly as little — `Total tested 0`. Whatever is wrong is
  in the harness or in headless task execution, not in what the factory writes. **So the variant
  format is not implicated, and the 70 MB minimal shape stays.**
- 🔬 **The bars are present and the symbol resolves.** `SQX_w2/user/data/History` is a symlink to
  the master's and holds `XAUUSD_DukasM1_Infinox_M30.dat`. After the symbol fix below there is no
  error of any kind in the custodian's log for the run.
- ⚠️ **What is still unknown:** whether headless `sqcli` can execute a project task at all on this
  install, or whether this stock `Retester` needs something a hand-rewired task does not carry.
  **The next step is to compare against a task known to have run** — the master's own XAUUSD
  `Retest-Task1` has produced databanks, so diffing its XML against the rewired one, element by
  element, is the cheapest way in. Do not start the master's project to find out.

Three facts worth keeping, all met while doing this:

- 🔬 **SQX renames on collision by appending `(N)`.** Loading the same folder of `P00000/1/2` twice
  gave six records: `P00000`, `P00001`, `P00002` and `P00002(1)`, `P00001(1)`, `P00000(1)`. This is
  failure mode 1 of `docs/encargos/4-variantes.md` §4 observed live, and it is exactly why the
  `variant_id` is also written **inside** the file and why C2 carries `sqx_name` separately.
- 🔬 **A cross-check that is switched off still has its symbol resolved,** and an unresolvable one
  kills the task without failing it. With `<CrossChecks use="false">` the log still showed
  `ERROR ProjectResources - Error while adding symbol to resources - Symbol 'EURUSD_M1_dukas'
  doesn't exist`, and the task did nothing. Every `<Chart>` in a task must name a symbol the install
  actually has, used or not.
- 🔬 **`-project action=loadconfig` takes only the task, not the project,** and SQX merges it into
  `project.cfx` when the instance exits. A cfx built from `action=saveconfig` contains a single
  `config.xml` holding the task; pushing it back left the live project without its databank
  registrations until the instance was stopped, at which point SQX rewrote `project.cfx` on disk
  with the merged result — databanks restored, task settings kept. Hard rule 4 from the other side:
  **the rewrite-on-exit is not only a hazard, it is also how a `loadconfig` becomes permanent.**

## 🔬 ANSWERED: a retest DOES rewrite the inherited `SQStats` (2026-09-22)

The question the whole variant study hung on. Measured on the custodian, 11 fabricated variants of
`XAUUSD/Strategy 17.9.39` in the five-member shape, one `action=start` of the rewired harness.

Before the retest all three controls exported the parent's row to the decimal (net profit
`22650.2`, 755 trades, PF `1.15`). After it:

| variant | `DICrossPeriod1` | net profit IS | trades IS | net profit OOS | trades OOS |
|---|---|---|---|---|---|
| `P00000` (origin) | 67 | **+26,138.78** | 755 | **+14,622.08** | 423 |
| `P00001` | 43 | **+43,647.37** | 1077 | **−6,988.39** | 588 |
| `P00002` | 94 | **−33,472.63** | 843 | **−12,962.25** | 497 |

- 🔬 **The chain is sound.** Different tuples produce different results, and none of them is the
  inherited one. The five-member `.sqx` retests exactly like a full one.
- 🔬 **One run gives both samples.** With `<OutOfSample><Range/></OutOfSample>` in the task, sample
  10 and sample 20 come back in the same export. A walk-forward correlation needs one run, not two.
- 🤔 **The origin's own retest is the reference, not the number it inherited.** `P00000` carries the
  parent's exact tuple and returns `26,138.78` against the inherited `22,650.2` — with the *same*
  755 trades. Same trades, different P&L, so the gap is costs and precision, not rules: the retest
  Setup is not the setup that produced the stored figure. **Never compare a retested variant against
  an inherited number.** That is why `origin` is a stratum and gets fabricated and retested like any
  other point.
- 🔬 **The inert-pair control fires correctly.** `P00004` differs from `P00000` only in a *frozen*
  parameter and returns an identical row — which is what that control exists to demonstrate. So
  "all controls identical" means a dead chain, but "one pair identical" means the freezing was
  justified. `sqx/variants/collect.py` counts distinct results among the controls and aborts only
  on the former.

## 🔬 SQX names a loaded strategy after the FILE, not after the name inside it (2026-09-22)

`P00000.sqx` appears in the databank as `P00000`, even though both `<StrategyName>` and
`ResultsGroup/@ResultName` inside it say `Strategy 17.9.39 P00000`. This **corrects** the note above
that says renaming those two fields is what keeps a batch from collapsing under one name: renaming
them is right and worth doing, but it is the **filename** that the databank, the export and the
retest all use as the handle. So:

- the join key between contract C2 and the retested panel is `variant_id`, not `sqx_name`;
- 🔬 on collision SQX appends `(N)` to the *file-derived* name — loading the same folder twice gives
  `P00000` and `P00000(1)` — so a reader must strip `\(\d+\)$` before joining.
