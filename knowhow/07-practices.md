# Working practices and research lessons

## Practices that already bit

- 🔬 **Don't pipe complex Python through `bash -c` heredocs.** Quoting mangles it and you get
  `SyntaxError: '(' was never closed`. Write the script to a file, then run it.
- 🔬 **Verify a write by reading back what SQX stored**, never by trusting the success message. The
  `loadconfig` auto-rename (`03-driving-sqx.md`) makes a successful-looking write land somewhere else
  entirely.
- 🔬 **Session names are not stable.** A session is auto-named (e.g. `algoproject-88 [4d9316]`) and a
  reopened window gets a different name; `ListAgents` shows only sessions running right now. Put
  identity in **files**, not in session names.
- Multiple sessions share all this state and destructive operations are not reversible. One owner per
  lane — see the lanes table in `sqx/CLAUDE.md`.
- 🔬 **A `ProcessPoolExecutor` started with `fork` hangs if the parent process has threads.** Measured
  2026-09-10: the `strategies/monteCarlo/explorer/` panel runs the analysis on a Flask thread, and the
  pool would deadlock partway through the seventh sub-test, with no error and no CPU use — the child
  inherits a mutex another thread held at the moment of the `fork`. The fix is the **`forkserver`**
  context, which forks from a clean, single-threaded process
  (`multiprocessing.get_context("forkserver")` + `set_forkserver_preload([...])` so workers start with
  numpy already imported). While at it, **one pool reused** instead of one per sub-test: it was 19
  pools of 96 workers per strategy.
- 🤔 **`set_forkserver_preload()` takes a module path as a *string*, so no import checker follows
  it, and getting it wrong does not fail — it only gets slower.** Found 2026-09-18 while moving
  `strategies/monteCarlo/` into layer packages: `engine.py` names its own module there, and a move
  that missed the rename would have left every worker reimporting numpy from scratch with no error
  anywhere. Any refactor that moves a module has to grep for its own dotted path inside strings, and
  the test that catches this one is **a stopwatch, not a traceback**: time one strategy before and
  after (2m07s → 2m01s on the 36-strategy XAUUSD databank at 3,000 sims, i.e. unchanged).
- 🔬 Launch SQX only with `ELECTRON_RUN_AS_NODE` unset. VS Code exports it; inheriting it makes SQX's
  Electron shell run as plain Node and the GUI dies with `bad option: --no-sandbox`.

## 🔬 What is and is not portable to Windows (2026-09-11)

The project splits cleanly in two, and only one half is tied to Linux.

- **Linux-only: everything that drives SQX.** `core/worker.py`, `core/exportdrv.py`,
  `sqx/export/`, `sqx/curate/apply_verdict.py`. They all shell out to `bin/sqx-worker.sh`,
  which needs `rsync`, `ss`, `md5sum`, `curl`, `setsid` and `stat -c`; `apply_verdict.py` also
  uses `pgrep` and the bare `sqcli` name (Windows ships `sqcli.bat`). `core.worker.require_posix()`
  raises on `win32` at each entry point, so the failure is one clear sentence instead of a
  `FileNotFoundError` on a `.sh`.
- **Portable: the analysis.** `tasks/`, `strategies/`, `portfolio/` and the panels are pure Python
  over CSVs already exported. The working split is export on Linux, analyse anywhere.
- 🔬 Two things would have broken silently on the first Windows clone and are now fixed:
  `PyYAML==5.4.1` publishes no wheel above cp39, so pip would try to compile it and fail on any
  modern Python; and ten `read_text()` / `open()` calls carried no `encoding=`, which on Windows
  means cp1252 and a `UnicodeDecodeError` on the first accented word of the Spanish manual.
  **Every file read in this project passes `encoding="utf-8"` — the default is not the same on
  both platforms.**
- 🔬 Python 3.10–3.13. numpy, scipy and arch publish no 3.14 wheels at the pinned versions.

## 📓 A checker only sees the files it is handed — `bin/*.sh` was never one of them (2026-09-21)

`tools/checks.py` enforces "no absolute path outside `core/paths.py`" over `depmap.py_files()`,
which yields **only `.py`**. `bin/sqx-worker.sh` and `bin/clone-sqx-worker.sh` therefore carried
`/home/sergioguslw/Desktop/SQX` at the top for months, in green builds, and
`docs/SETUP-NEW-MACHINE.md` had grown a manual "⚠️ edit these two files first" step to compensate.
A documented workaround for a rule the checker cannot see is the signal that the checker's *input*
is wrong, not its rule. `hardcoded_paths()` now takes `files + bin/*.sh`; the same regex works on
bash because a shell comment also starts with `#`.

## 🔬 `mapfile` over a process substitution hides the exit status, and a line count is not a substitute

Reading a helper's output with `mapfile -t X < <(python3 -c ... 2>&1)` discards `$?`. The obvious
patch — "trust it only if it printed the 3 lines I expect" — fails silently here: a `KeyError`
traceback from `python3 -c` is **exactly three lines**, so an unknown worker role sailed through and
the script ran with an empty install path. Use command substitution, which preserves the status:

```bash
_W=$(python3 -c '...' "$ROLE" 2>&1) || { printf 'cannot resolve %s:\n  %s\n' "$ROLE" "$_W"; exit 1; }
mapfile -t _W <<< "$_W"
```

## Research lessons

- 🔬 **A stop-fill assumption can dominate a stop study's conclusion.** In the ATR-stop study
  (`archive/studies/atr_stop_study.py`), filling exactly at the stop made tight stops look
  excellent (PF 2.09 at 0.5×ATR); allowing 0.25×ATR of slippage erased it (PF 1.49, net −37%), while a
  3×ATR stop lost only 11%. **Never present an MAE-threshold stop simulation without a slippage
  sensitivity — the tighter the stop, the more of the answer is the assumption.**
- 🔬 In this architecture a stop does **not** add round trips: it moves an exit, so total commission is
  constant in the number of trades.
- 🔬 Two structurally different populations can share one databank (`06-locations.md`). Check for that
  before pooling any exit statistic.

- 🔬 **Conditioning on a metric destroys that metric's own remaining signal.** Measured 2026-09-04 on
  the 10,000 strategies of `XAUUSD/OOS` (`AlgoData/metrics/XAUUSD/OOS/metrics.csv`, report in
  `AlgoData/reports/XAUUSD/OOS/2026-09-04/`; reproduce with
  `python3 -m tasks.reports.is_oos --project XAUUSD --databank OOS`). Deduplication was **checked,
  not assumed**: 10,000 distinct names and only 2 byte-identical metric vectors, so n stands.
  `Sharpe Ratio (IS)` predicts `Profit factor (OOS)` at ρ +0.223 over the
  whole population, but **inside the top 20% by that same Sharpe it falls to +0.088** and a different
  metric leads the ranking. This is range restriction, and it means a predictor ranking computed on
  the full population **does not tell you what to filter on second**. Any multi-clause filter must
  have its ranking recomputed inside the surviving subset — which is why
  `tasks/reports/panel.html` recomputes rather than showing stored numbers.
- 🔬 **At n≈10,000 the single-test significance floor carries no information.** |r| > 0.020 clears the
  ordinary two-tailed 5% level, so 19 of 21 in-sample metrics "pass" against OOS profit factor. Report
  a family-wise or FDR correction (`tasks/analysis/correlations.py:discoveries`) and then argue from
  **effect size**, never from p. A p-value at this sample size only says the population is large.
- 🤔 The XAUUSD population these two lessons came from is **generic strategies**, not template-driven
  ones — see the owner's 2026-09-04 decision in `03-driving-sqx.md`. Whether the same relationships
  hold for a template-built population is untested.

## The worker's process is called `sqcli`, and `sqx-worker.sh stop` can lie

🔬 2026-09-05. After `export_metrics`, both the export and a follow-up `bin/sqx-worker.sh stop`
printed **"worker did not stop"**, yet `ps -eo pid,cmd | grep -i StrategyQuant` and a grep for
`SQX_w1` showed nothing — the worker was still up and answering on 5060.

Its command line is just `./sqcli`; the install only shows in its working directory. So:

```bash
ss -lptn 'sport = :5060'          # names the pid holding the port
readlink /proc/<pid>/cwd          # confirm it is .../SQX_w1 before killing
kill <pid>                        # by PID — never pkill -f, per CLAUDE.md hard rule 2
curl -s -m 3 "http://localhost:5060/call?cmd=-h" && echo up || echo down
```

🔬 A plain `kill` was enough; the port was dead on the first poll. **Never trust the script's exit
message — poll the port.**

## A genetic-algorithm target cannot be chosen from one run per arm

🔬 2026-09-05, XAUUSD, five 10,000-strategy generation runs of the **same build** with the same
in-sample condition (minimum 100 trades), differing only in the GA target: `OOS` → Ret/DD,
`OOS-Sharpe` → Sharpe, `OOS-Rexpect` and `OOS-Rexpect2` → R Expectancy (same target, two runs),
`OOS-Rsquared` → RSquared. `reports/XAUUSD/_comparison/2026-09-05/`.

🔬 **Two runs of the same target differed by −16.0 pp [−20.2, −11.7]** in out-of-sample hit rate at
the operating point (each sample's own top 10% of `Sharpe Ratio (IS)`), and −17.0 pp on Sharpe (OOS).
**That run-to-run gap was larger than every between-target difference measured** (Sharpe +3.4,
R Expectancy +6.5, RSquared −1.7 pp against the Ret/DD baseline over the whole population). At one run
per arm the target effect is **not identifiable** — seed variance dominates it. Any target ranking
drawn from single runs on this project is noise; treat the target as unresolved.

🔬 The failure is not detectable from inside the winning sample. `OOS-Rexpect` looked coherent —
flattest 10%-to-5% curve, best medians, enrichment matching its label — and none of it reproduced.
Two prior attempts to *predict* target quality had already failed: the persistence table could not
rank the winner (`R Expectancy` has no OOS column, below) and the carried-threshold sweep gave every
ratio ≈50% hit. Prediction fails, and so does a single outcome measurement.

🔬 **The filter conclusion does reproduce, including in the bad draws.** In all five samples the
sample's own top 10% of `Sharpe Ratio (IS)` beat its own unfiltered population (hit 39.4–56.4% against
25.0–33.2%), and a full 210-candidate sweep re-run on `OOS-Rexpect2` returned `Sharpe Ratio (IS)` as
the best surviving filter, +11.8 pp at the top 10%, BH-corrected. **A within-sample filter effect,
measured against the population it selects from, replicates where a between-run comparison does not.**
Prefer that shape of question whenever both are available.

🤔 To settle a target question here you would need replicates per arm, or fewer sources of noise:
more strategies per run narrows every interval, and a seed held fixed across arms — if SQX exposes one
— removes the dominant term outright. Both are cheaper than replicating every arm.

### Targets that rank strategies identically in sample still search differently

🔬 In the Ret/DD-targeted sample, Spearman between candidate target metrics **in sample** collapses
them into one axis: `R Expectancy` ≡ `SQN` ≡ `Profit factor` at ρ **+1.00**, `Sharpe` ≡ `Sortino` ≡
`PSR` at ρ **+1.00**, those two clusters at ρ +0.94 with each other, `Ret/DD` +0.98 with Sharpe,
`Ulcer Index %` −0.92 (the same axis inverted), `Net profit` +0.97. **The only axis that is not that
cluster is `RSquared`** (ρ −0.32 to −0.40 against all of it), with `TRL Ratio` its neighbour (+0.77).

🤔 A GA does not rank the population, it climbs a surface, so objectives that order the same
strategies identically could still steer the search differently. That was the reasoning behind
targeting `SQN` as a diagnostic — but with seed variance at ~16 pp it cannot be tested one run at a
time either.

📓 **`Export Data View` emits `R Expectancy`, `Stability`, `RSquared`, `TRL Ratio`, `DoF Ratio`,
`# of trades`, `Max DD %`, `Drawdown` and `Param Count` at `sampleType="10"` only.** That is why no
target has a persistence figure for its own metric. Adding them at `sampleType="20"` in
`user/settings/views/databanks/Export Data View.vw` closes the gap, but it changes the column set, so
every databank must be re-exported through the new view before samples compare — and the `.sqx` of
`OOS` and `OOS-Sharpe` were cleared on 2026-09-05, so those two arms can never be re-exported.

### Absolute thresholds, and why the trade floor must stay at 100

🔬 2026-09-05, the same five XAUUSD runs. A percentile cut does not transfer as a number: the top 10%
of `Sharpe Ratio (IS)` sits at 0.480 / 0.580 / 0.500 / 0.470 / 0.390 across them. Judged as absolute
thresholds on Ret/DD (OOS), against unfiltered populations of 25.0–33.2% hit:

| `Sharpe Ratio (IS)` ≥ | kept | hit % |
|---|---|---|
| 0.5 | 6.1–13.8% | 39.9–56.0 |
| **0.6** | **3.9–9.6%** | **43.2–59.1** |
| 0.7 | 2.4–5.7% | 47.3–64.1 |
| 0.8 | 1.2–2.6% | 48.0–64.9 |

No knee — it is a smooth trade. 0.6 is the point where all five runs clear +14 pp over their own
population with 400–950 survivors per 10,000. `R Expectancy (IS)` ≥ 0.15 and `Profit factor (IS)`
≥ 1.20 are the same axis but **saturate**: past those the two weak runs stop improving while the
Sharpe threshold keeps climbing in all five.

🔬 **Raising the minimum trade count hurts, monotonically, in all five runs**: hit falls from
25.0–33.2% at ≥100 to 18.6–23.9% at ≥800. At 100 the condition passes 99.1–99.8% of what is
generated — a sanity floor, not a filter. **Keep it at 100.** In this population more trades goes with
less edge per trade.

🔬 **No second condition survives.** Nine tried on top of `Sharpe Ratio (IS)` ≥ 0.6 (`RSquared`,
`Stability`, `DoF Ratio`, `Param Count`, `TRL Ratio`, `Winning Percent`, `# of trades` ceilings): all
change sign across runs at ±3 pp, well inside the ~16 pp run-to-run noise, except a `DoF Ratio` floor
which is consistently harmful (−3.6 to −22.0 pp). Ship one condition.

🤔 All of it is measured as a **selection** rule on a finished databank. As a build-time **acceptance**
condition it also changes what the GA breeds from, which is precisely the class of intervention this
project has shown cannot be predicted from filtering data. Prefer selection after the build; if set at
build time, treat it as a new arm.

## 🔬 Any statistic measured after selecting on the OOS reports the opposite of the truth

2026-09-06, all five XAUUSD runs (~10,000 rows each), IS 2008–2017 vs OOS 2018–2022. The populations
are essentially unselected: median PF (IS) is 0.98–1.01 and only 42.0–52.2% are profitable in sample.

Unbiased decay, over the **whole** population, is small, negative and remarkably stable across runs:

| | OOS | OOS-Sharpe | OOS-Rexpect | OOS-Rexpect2 | OOS-Rsquared |
|---|---|---|---|---|---|
| median Sharpe IS → OOS | −0.11 → −0.28 | 0.00 → −0.24 | 0.01 → −0.20 | −0.03 → −0.26 | −0.08 → −0.27 |
| median PF IS → OOS | 0.98 → 0.95 | 1.00 → 0.95 | 1.01 → 0.96 | 1.00 → 0.95 | 0.98 → 0.95 |
| profitable OOS | 26.9% | 30.2% | 33.5% | 27.9% | 25.3% |

**Use −0.17 Sharpe and −0.03 PF as this generator's decay.** Now condition on `Net profit (OOS) > 0`,
which keeps 25.3–33.5%, and remeasure inside the survivors: the median change flips to **+0.10 to
+0.19 Sharpe and +0.03 to +0.06 PF** in all five runs. Strategies appear to *improve* out of sample.
Nothing improved — conditioning on OOS success selects whoever was lucky in that window, and every
decay figure computed afterwards is biased toward zero or beyond it.

The rule this fixes: **a filter on the OOS spends the OOS.** Decay measured after an OOS filter
answers no question. Measure decay on the unselected population as a diagnostic of the generator, and
keep selection filters on IS-side columns only, as `improvement.py` already enforces.

### 🤔 IS proxies that separate survivors inside the top Sharpe decile

Stratifying on `Sharpe Ratio (IS)` first removes the mechanical regression-to-the-mean that makes
(OOS − IS) correlate with IS by construction. Within each run's top decile of `Sharpe Ratio (IS)`
(n=1000, baseline hit 39.4–56.7% on NP(OOS)>0), splitting at the candidate's median, high half minus
low half:

| candidate | per-run gap (pp) | mean |
|---|---|---|
| `TRL Ratio (IS)` | +5.0 +14.8 +7.4 +6.8 +5.2 | **+7.8** |
| `SQN (IS)` | +4.2 +7.6 +9.0 +3.6 +2.8 | +5.4 |
| `ZScore (IS)` | +12.2 +2.0 +4.2 +0.4 +6.0 | +5.0 |
| `R Expectancy (IS)` | +3.4 +8.4 +8.6 +2.8 +1.2 | +4.9 |
| `Param Count (IS)` | −0.6 −11.2 −3.0 −8.4 +3.2 | −4.0 |
| `DoF Ratio (IS)`, `# of trades (IS)` | sign changes | ~−3 |

Same sign 5/5 for the first four — but they are one axis (per-trade edge quality), not four findings,
and this **contradicts** the nine-candidate result above, where `TRL Ratio` on top of
`Sharpe Ratio (IS)` ≥ 0.6 changed sign across runs. The two differ in stratification (top decile vs
absolute 0.6) and outcome (NP(OOS)>0 vs Ret/DD(OOS)). **Not a shippable filter** until run through
`improvement.py` with its bootstrap interval and `replication.py`. Worth noting that `Param Count`
leans negative — high parameter count hurts — which is the direction overfitting theory predicts.

## Robustness Monte Carlo (2026-09-09)

Measured on the 36 strategies of `XAUUSD/Results` (export `raw/XAUUSD/Results/2026-09-03/trades/`,
report in `AlgoData/reports/XAUUSD/Results/2026-09-09/montecarlo/`; reproduce with
`python3 -m strategies.monteCarlo.report --project XAUUSD --databank Results --asset XAUUSD
--export 2026-09-03`).

- 🔬 **The backtest drawdown underestimates the real one by a factor of ~2.** The median drawdown
  inflation — the 95th percentile of reordered drawdown against the observed one — is **1.95** across
  the 36 strategies, and the lowest is 1.52. Sizing the account on the backtest drawdown sizes it on
  half the real figure. Reordering does not change a single trade: it is pure order effect.
- 🔬 **Stitching the 5th percentile of every two-year block multiplies the drawdown by ~4-5.** On
  `Strategy 18.28.28`, 2.4% observed → 4.4% at the 95th percentile of reordering → **9-12%** on the
  stitched path. That third number is the one to compare against a prop firm's rules. The stitched
  path is itself a draw, so it moves between runs more than the percentiles do: read it as an order of
  magnitude, not an exact figure.
- 🔬 **This fleet's edge dies out after 2013.** The 24-month rolling windows are positive early and
  negative in the second half for almost all of them; **29-30 of 36** have a non-overlapping 24-month
  block whose resampled median is negative (the count moves by one or two between runs, because some
  block lands right at zero). The databank shows none of this in any column: the total result is
  carried by the early years.
- 🔬 **The median out-of-sample Sharpe is ~0.13-0.14 times the in-sample one** (median of the 36). It
  is a level comparison, not an overfitting test — but it is optimism the decay test did not catch.
- 🔬 **At 20,000 simulations the numbers that decide are already stable**: repeating eight times with
  fresh entropy, the percentile that moves most (the drawdown's 99th) varies **2-4%** of its mean. At
  the default 100,000 it drops to **1.2-1.3%**, and **all 36 verdicts are the same**: raising the
  simulation count sharpens the tails, it does not change decisions. The 36 strategies at 100,000, with
  six block sizes and stability included, take **15 minutes** on 96 cores. Raising to 100,000 sharpens
  the tails, not the decisions. No seed is used anywhere on purpose; this dispersion is what stands in
  for one.
- 🤔 **A veto that fails 5 of every 6 candidates speaks to the threshold, not the fleet.** The 10%
  of-account drawdown ceiling vetoes 21 of 36 at $1,000 risk per trade on $100,000; it is as much a
  statement about **position size** as about the strategy. It stays provisional until the prop firm's
  rules are known.
- 🔬 **Shuffling without replacement has to leave net profit identical.** `sweeps.invariant()` measures
  the standard deviation of net profit across reorderings: it comes out at ~1e-11 $, i.e. zero in
  floating point. If it is ever not zero, the model is touching composition, and the split between
  "order luck" and "composition luck" stops holding.


## A gate that excludes evidence is a decision, and it belongs to the owner

🔬 Found 2026-09-14 rebuilding `strategies/crossmarket/`. The first build turned every diagnostic
into a gate: a market with fewer than 30 trades, or with under 95% of entries on a bar open, was
dropped from the study entirely, and a strategy measured on fewer than four surviving markets came
out NO EVALUABLE. Two things followed, both bad.

- **It threw away real results.** `Strategy 24.14.35` came out NO EVALUABLE despite p = 0.005 on
  Brent under every null model, because 8.6% of its Brent entries were pending fills. Losing 100% of
  a market's evidence over 8% of its trades is not conservatism, it is discarding the measurement.
- **It was structurally unreachable.** `MIN_MARKETS = 4` against the two markets the retest actually
  ran made NO EVALUABLE the only possible outcome for XAUUSD, for every strategy, forever — and
  nothing in the code or the report said so.

The replacement: the study reports every market it measured and names, beside each one, every reason
to distrust it (`inference.warnings()`). Nothing is hidden and nothing is decided. **A threshold that
removes data is a decision about what counts as evidence; it is the owner's, not the analysis's.**

## Dividing by a drift that is statistically zero

🔬 Found 2026-09-14. The source note's "primary tool" for cross-market comparison is
`E = mean(bar return while held) / mu_m`, the market's own mean bar return. Measured over M30 bars:
gold `t = +3.13`, silver `t = +1.61`, **Brent `t = −0.11`**. On Brent, E came out **−69.4** — for the
market with the *strongest* drift-neutral excess A of the three. The ratio inverts whenever the
denominator is near zero and flips sign whenever the market drifted down.

The fix is not a clamp. **A is the number to read** — it subtracts the drift instead of dividing by
it, so it is defined everywhere — and E is withheld unless the market's drift clears a t threshold.
Any metric shaped "strategy over market" inherits this; check the denominator's own significance
before publishing the ratio.

🔬 **Updated 2026-09-16: withholding the ratio was still not the honest answer.** Hiding E where the
drift is weak leaves the reader with no idea how badly determined it was, and a percentile bootstrap
on the ratio is worse — it returns a comfortable finite interval precisely when no finite interval
exists. **Fieller's theorem is the tool.** Given the two means, their variances and their covariance,
it returns an interval that is genuinely **unbounded** when `z²·var(den)/den² ≥ 1`, which is the
algebra's own way of saying the denominator cannot be told from zero. Measured on Brent,
`Strategy 1.10.80`: E = +17.4, CI 90% **unbounded**, and 54.5% of bootstrap replicates had a market
drift at or below zero. All three numbers together are a sentence; any one of them alone is not.

Two details that decide whether the interval means anything:

- **Resample the numerator and the denominator from the same replicate.** The occupied bars are a
  *subset* of the market's bars, so the two estimates move together; treating them as independent
  understates the interval on their ratio. Bootstrapping blocks of bars and computing both sides
  from the same drawn blocks carries the covariance instead of assuming it away.
- **Aggregate into blocks before resampling, not after.** A 120,000-bar market times 2,000 draws is
  a matrix nobody needs: reduce each block to its four totals (sum and count of all bars, sum and
  count of occupied ones) and resample those. It is the same estimator at a thousandth of the memory.

And the reframing that made the panel readable: **the headline number is A divided by the market's
typical bar move**, not E. That denominator is a volatility, so it is always positive and never near
zero — it is defined in every market, and the ratio E becomes context with an interval rather than a
figure anyone reads first.


## A reference window with fixed boundaries measures the trades near its edge against the past

🔬 Found 2026-09-16 in `strategies/crossmarket/simulate/paired.py`, on the owner asking "why six months, and
what about three back and three forward?". Test 1b compared each trade against the mean of every
window of its own length inside **the fixed semester partition** the null model shifts trades within.
Reusing that partition looked like consistency and hid two artefacts:

- A trade entering three days before a block ends is measured against a stretch that is **almost
  entirely past**. Its reference describes a regime that had mostly already happened.
- Two trades a week apart, on opposite sides of a boundary, get **disjoint** references. That
  difference is a property of where the calendar was cut, not of the market.

The replacement is a **centered window**: every blind trade of the same length starting within ±N
months of the entry. It is a running mean over the per-bar return series, so it costs one pass per
distinct hold whatever the width — no per-trade loop, no sampling. It reads bars *after* the entry,
which is legitimate here and must be said out loud: the reference is "what this market was paying
around then", not a rule anyone could have traded.

The general lesson is the one worth keeping: **when a modelling choice is arbitrary, sweep it and
print every answer.** The test now runs under ±3m, ±6m, ±12m and the block partition, and shows all
four. Measured on `Strategy 1.10.80` / Brent: p = 0.749 / 0.677 / 0.667 / 0.753 and alpha −5.27 /
−4.68 / −4.72 / −5.22 bps. The four agreeing is a *measurement*; assuming they would have agreed is
what the old code did.

🔬 **The same session, a presentation finding.** The statistic is a log return, so it prints as
0.00042 and nobody reads it. Printing the identical number in basis points, per cent, ATR units,
dollars per trade and **dollars accumulated over the sample** changed what the owner asked about it
immediately: "the timing put −$6,507 into this market" is a sentence, and "−0.00053" is not. The
maths stays in log space, where subtracting two windows is legitimate; only the presentation changes.


## A zero-duration trade is a real trade that no bar-grid study can hold

🔬 Found 2026-09-16 by the owner, who compared a cross-market panel against SQX and saw fewer
trades. `Strategy 24.7.38` on gold: 2,142 in the databank, 2,089 in the study. The 53 missing ones
have `Open time == Close time`, `Time in trade` of `0s` and `Close type` of `Exit Signal` — SQX's
exit rule fired on the entry bar.

Across the whole `Retest Markets - Family` export: **1,695 of 92,329 trades (1.84%)** are
zero-duration, in 57 of the (strategy, market) pairs, reaching **9.8%** on `Strategy 8.16.41(1)` /
silver. Three more are `Exit After X Bars` that also collapse to one bar, and five fall before the
first bar of their own file.

`envelope.occupancy()` keeps a trade only where `exit > entry`, which is correct for what it feeds:
a trade with no interval cannot be displaced by a null model, matched against a blind window of its
own duration, or counted as occupied bars. The mistake was letting that subset also define **what
the backtest did**. Net profit, drawdown, profit factor and the trade count are properties of the
trade list, not of the bar grid, and they must come from every row SQX exported or they silently
disagree with the databank by whatever the grid could not hold.

The general rule: **separate "what the run did" from "what the test could compare", compute each
from its own population, and print both counts.** Any study that locates trades on a grid — this
one, a stop simulation, an MAE/MFE study — inherits the same split. A single trade count on a page
is a claim that the two populations are the same one, and here they are not.


## A contemporaneous dependence cannot be bootstrapped by resampling trades

🔬 Recorded 2026-09-16, building `strategies/crossmarket/simulate/portfolio.py`. When several markets are
merged into one account, the dependence that matters is **contemporaneous** — two markets losing in
the same week — not serial. A trade-level bootstrap, even a block one, draws trades that never
co-occurred and destroys exactly the thing being measured, while reporting a comfortably narrow
interval for the portfolio's drawdown.

Resample **whole calendar blocks** instead: partition the timeline into N-week blocks, draw blocks
with replacement, and every market's trades inside a drawn block travel together. Trade-level
reordering still has a place next to it — it answers a different question, "did the sequence matter",
and leaves composition untouched so net profit is invariant by construction — but it is not a
substitute.

🤔 A related trap, found by the numbers looking wrong: an event sweep over `(open, +1)` and
`(close, −1)` pairs reported **four** concurrent positions across **three** markets. A close and an
open at the same instant are one position handing over to the next; sort closes before opens at
equal timestamps (`np.lexsort((moves, times))`) or every re-entry on its own exit bar counts twice.


## A bar file is wider than the backtest that ran on it, and a null will happily use the rest

🔬 Found 2026-09-15 in `strategies/crossmarket`, by the owner reading an equity chart. Exported bars
cover whatever window was asked of SQX; the retest that produced the trades covers a narrower one.
Measured on `XAUUSD / Retest Markets - Family`: bars 2003-05 to 2026-01, backtests 2008-01 to
2022-12 — **a third of every bar file sits outside the backtest**.

A random-entry null that samples the whole file is then trading years the real strategy never saw,
each with its own drift and its own volatility regime. The damage is not confined to the null: the
market drift `mu_m` that Test 1c subtracts, the blind-window benchmark Test 1b compares against, the
structural profile in `drivers.py`, and the x axis of the equity curve were all computed over the
wrong stretch.

**The fix is one slice, applied once, before anything else** — `envelope.window(trades, bars)` cuts
to the first entry and the last exit, and every downstream function receives the slice rather than
the file. Per strategy, not per market: two strategies in one databank need not cover the same span.

**Generalise it.** Any study that places synthetic events on a price series has to bound the series
to what the real events could have used. Ask of any such test: *could a simulated trade land where a
real one structurally could not?* Here the answer was yes for a third of the sample and nothing
crashed.

## Which null is hardest to beat is a measurement, not an intuition — and it moved twice

🔬 `strategies/crossmarket` runs four random-entry nulls. Three re-lay the whole run from a random
start; `block_shift` moves each trade inside its own six-month block and its own weekday-hour slot.

- **First reading (2026-09-15, unbounded sample).** `block_shift` looked systematically tightest —
  σ 0.073 against 0.095 on XAGUSD — and returned the lowest p everywhere tried. This contradicted
  the module's own docstring, which had reasoned that destroying clustering would *reduce* the null's
  variance, and the docstring was corrected.
- **Second reading (same day, window bounded).** Most of that gap was the artefact above: the other
  three had been roaming a third more sample. With the window bounded, `block_shift` has the
  narrowest null in **5 of 8** (strategy, market) pairs and the lowest p in **7 of 8** — usually, not
  systematically.

Two lessons worth more than the numbers:

- **"Randomises more things" does not imply "harder to beat."** Check each null's spread before
  calling one conservative.
- **A measurement that contradicts a docstring may be measuring a bug.** The first reading was real
  and reproducible and still mostly an artefact. Before rewriting documentation around a surprising
  number, ask what else would have to be true for it — here, that the nulls had more room than the
  backtest, which was exactly the defect.

`block_shift` stays the model the summary reports, and the reason is unchanged by either reading: it
is the only one that changes exactly one thing, so the only one whose low p is attributable to entry
timing rather than to where the run landed. **A strategy that survives all four says more than one
that survives only it.**

## Moving a module into a layer package: the three things no checker catches

🔬 Found 2026-09-18/19 reorganising `strategies/crossmarket/` into `inputs/ mechanics/ model/
simulate/ verdict/ render/`, the second study after `strategies/monteCarlo/`.
`python3 tools/checks.py` and a repo-wide import loop both come out green while all three of these
are broken.

- 🔬 **`Path(__file__).with_name("x.yaml")` follows the `.py`, not the data.** Three modules
  resolved their own config that way, and the three `.yaml` had to stay in the module root because
  `docs/manual/05-retest-mercados.md` names them by that path. After a `git mv` one level down,
  `with_name` points at `inputs/` and the file is simply not found — at **run** time, not import
  time. It has to become `Path(__file__).parents[1] / "x.yaml"`, and the line deserves a comment
  saying why, because the next reader will "simplify" it back.
- 🔬 **A private name imported from another module is a public API nobody declared**, and renaming
  it can collide with a local. `render/charts.py` exported `_x` and `_ticks` to two other modules.
  `_x` → `xpos` was free; `_ticks` → `ticks` **was not** — `ticks` is already a local holding
  rendered markup in both `charts.cone()` and `overlays.py`, and a local shadowing an import fails
  at *render* time, with no traceback anywhere near the import. Named it `tickvals` instead. Grep
  for local assignments of every candidate name before choosing it; in monteCarlo the same trap was
  `line`.
- 🔬 **A layer violation is usually a function in the wrong layer, not a bad boundary.** crossmarket
  had exactly two `simulate/ → verdict/` arrows. One, `fingerprint → significance`, used a single
  function: `trade_returns()`, which is `realised(...) − cost` — a measurement wearing an inference
  module's name. Moving it to `mechanics/pricing.py` removed the violation **and** left two dead
  imports (`pricing`, `pandas`) in `significance.py`, after which `verdict/` imports nothing outside
  `model/`. The other, `exposure → fieller`, is real and was **declared in the README table** rather
  than dissolved, the same way monteCarlo declares `simulate/ → verdict/confidence`. In monteCarlo
  the equivalent finding was two vocabulary constants that were really configuration.

**How to know it still works when the module has no batch command.** crossmarket's only entry point
is a Flask panel, so the baseline was taken **over its own HTTP API**: read the `@APP.get` /
`@APP.post` decorators for the routes and the exact parameter names, run one strategy with the
simulation counts cut by `--set`, and save every rendered view — 11 tabs plus every switchable
`market × model × metric × window` combination, 214 in all. Then normalise every digit to `#` and
diff before against after: the numbers move (there is no seed), the **structure must not**. 🔬 214
of 214 came out identical. A stopwatch over 5 repeats is the companion test, the one that catches a
module path left inside a string: median 10.12 s before, 10.10 s after.

🔬 And the cheap proof for an extracted primitive: import the pre-move file straight out of git
(`git show HEAD:<path>`) beside the new one and compare their output character for character on
fixed inputs. `render/svg.py` against the old `charts.py` — both figures at three widths, plus every
constant and primitive — came out with **0 differences**, which turns "I think nothing changed" into
a fact for the cost of thirty lines.

## Monte Carlo: la máquina no es lenta por CPU, es lenta por ancho de banda de memoria

🔬 Medido 2026-09-19 con `XAUUSD / MC Trades` (757 estrategias, N mediano 1.132 operaciones)
sobre la máquina de 96 núcleos y 125 GB.

- 🔬 **El kernel satura a ~24 procesos.** El mismo lote (`draws.stationary` + `metrics.paths`,
  2.000 caminos × 1.132 operaciones) escala 8,5× con 8 procesos, 16,5× con 24 y **17,9× con 95**.
  De 24 a 95 procesos el tiempo por lote crece linealmente (175 ms → 642 ms) y el rendimiento
  agregado no se mueve: 133 lotes/s en los tres casos. Es saturación de ancho de banda, no de
  cálculo. Pedir `max_workers=96` no compra nada por encima de ~24 y multiplica por 4 la RAM.
- 🔬 **Los bytes son el presupuesto, no los FLOPs.** Pasando la matriz de caminos a `float32`, los
  índices a `int32` y fusionando los temporales de `metrics.paths` (siete arrays `(sims, N)` se
  quedan en tres), el rendimiento saturado pasa de **271.000 a 532.000 caminos/s — 1,96× con el
  mismo hardware** y con el mismo resultado numérico (`np.allclose` rtol 1e-9 en los ocho
  estadísticos).
- 🔬 **`chunk` acota simulaciones, no memoria.** Un lote de 2.000 caminos asigna 53 MB con N=542 y
  **337 MB con N=3.437**: ×95 trabajadores son 5 GB frente a 32 GB según qué estrategia toque. El
  presupuesto tiene que ser en bytes (`chunk = bytes_objetivo // N`), no en caminos.
- 🔬 **El 24% del trabajo simulado corre en el proceso padre, en un solo núcleo**: `family_d`
  (ventanas y terciles, vía `engine.single`), `_family_b` (IS/OOS, vía `engine.sequential`) y
  `stitch`. Son 8,1 s + 4,6 s de los 28,2 s que cuesta una estrategia mediana.
- 🔬 **`n_sims: 100000` está cinco veces por encima de lo que el propio módulo exige.**
  `stability.spread()` sobre la misma estrategia da una dispersión relativa máxima de 3,0% con
  100.000 caminos, 8,3% con 20.000 y 11,8% con 10.000, contra una tolerancia declarada de 10%:
  20.000 es el primer valor que la cumple, y cuesta 5,0 s frente a 26,1 s.

## El kernel Monte Carlo por tiras: 84× menos memoria y 3,6× más rápido, a la vez

🔬 Medido 2026-09-19 sobre `XAUUSD / MC Trades`. Toda la memoria del módulo está en los
trabajadores; el padre nunca pasa de 0,74 GB (96 MB de arrays crudos en `sweeps.execute`, 1,4 MB de
resultado, 0,7 MB de JSON de caché). El problema es `_batch`.

- 🔬 **`_batch` vive con 6,1 matrices `(chunk, N)` de `float64` a la vez.** Repartidas así, medidas
  con `tracemalloc` y en unidades de "matriz base" (`chunk × N × 8 B`): `draws.stationary` 2,1 ·
  `block_shuffle` 3,2 (el `argsort` del relleno) · `iid_bootstrap` 1,0 · los cuatro `stress` entre
  1,1 y 3,1 · `metrics.paths` **5,1 encima de su entrada**. Con `chunk: 2000` eso es 111 MB por
  trabajador con N=1.132 y **337 MB con N=3.437** — ×96 trabajadores, 32,3 GB.
- 🔬 **La solución es tirar el lote en tiras y reutilizar buffers**, no bajar `chunk`. Con buffers
  persistentes en `float32`/`int32` dimensionados por un presupuesto en **bytes**, la memoria por
  trabajador es **constante sea cual sea N**: 12,2 / 12,1 / 12,1 / 12,0 MB para N = 542 / 1.132 /
  2.374 / 3.437, contra 53 / 111 / 233 / 337 MB hoy.
- 🔬 **Y el mismo cambio rompe el techo de ancho de banda**, porque el conjunto de trabajo pasa a
  caber en L3. Caminos/s agregados, N=1.132:

  | procesos | actual | por tiras |
  |---|---|---|
  | 24 | 188.961 | 333.902 |
  | 48 | 191.093 | 549.773 |
  | 96 | 200.602 | **714.801** |

  El actual está plano desde 24 procesos; el de tiras **sigue escalando a 96**. Esto invierte la
  recomendación de bajar `max_workers`: una vez el kernel cabe en caché, los 96 sí valen.
- 🔬 **El presupuesto óptimo de la tira es 4 MB** en este EPYC (L3 ~5 MB por núcleo): 1 MB →
  203.057 caminos/s, 2 MB → 494.914, **4 MB → 714.801**, 8 MB → 652.162, 16 MB → 481.943, 32 MB →
  405.100. Por debajo manda el intérprete (tiras de 36 filas), por encima se sale de L3.
- 🔬 **`float32` no degrada ningún número que decida, y arregla el invariante.** Los percentiles que
  alimentan los vetos coinciden con `float64` con error relativo entre 4e-8 y 5e-7 — cinco órdenes
  de magnitud por debajo del 3% que se mueven entre corridas. Y `sweeps.invariant()` sobre
  `iid_shuffle` da **std exactamente 0,0** con caminos en `float32` sumados en `float64`, frente a
  7,5e-12 hoy: 24 bits de mantisa sumados en `float64` no redondean nunca.
  ⚠️ **El acumulador tiene que ser `float64` explícito** (`sum(..., dtype=np.float64)`,
  `einsum(..., dtype=np.float64)`). Con acumulación en `float32` esa misma std sube a 7,7e-3 USD y
  el invariante deja de serlo.
- ⚠️ Un sorteo por tiras no puede reutilizar los mismos uniformes para "quién reinicia" y "dónde
  reinicia": las posiciones de arranque quedarían correlacionadas con el umbral `1/block` y
  sesgadas hacia el principio de la serie. Dos buffers, no uno.

### Lo que salió al implementarlo de verdad (rama `perf/montecarlo-tiles`)

🔬 Medido 2026-09-20 con `python3 -m perf.catalogue`, que muestrea el RSS del árbol entero.

- 🔬 **La ganancia del kernel no llega al comando: el pool nunca se satura.** `engine.run` parte el
  sub-test en tareas de `chunk: 2000`, así que con `n_sims: 5000` sólo hay **3 tareas a la vez**, no
  96. El 3,6× del kernel se queda en **−13,5% de reloj** en `montecarlo.analyse` (10,13 s → 8,76 s)
  y **−14,6%** con `n_sims: 100000` (24,44 s → 20,88 s). El resto del tiempo es el trabajo monohilo
  del padre. Medir el kernel aislado y medir el comando son dos preguntas distintas.
- 🔬 **El pico de memoria del árbol lo manda el pool, no el kernel.** Con `n_sims: 100000` sobre la
  estrategia más larga (3.437 operaciones) el pico pasa de **19.671 MB a 8.814 MB (−55%)**, pero
  esos 8,8 GB que quedan son **96 intérpretes vivos** con numpy cargado: con 920 operaciones el
  pico por tiras es 8.723 MB, prácticamente el mismo. Lo que el cambio elimina es la parte que
  crecía con N — master sube **+83%** de 920 a 3.437 operaciones, las tiras **+1,0%**.
- 🔬 **No hace falta escribir un muestreador por tiras: basta con pedirle al modelo un sorteo por
  tira.** `draws.stationary(145, ...)` llamado 138 veces sortea sus dos buffers cada vez, así que la
  trampa de los uniformes compartidos no puede ocurrir. Medido sobre 20.000 caminos de N=3.437 con
  bloque 15: fracción de operaciones consecutivas **0,9333** en una llamada grande y **0,9333** por
  tiras (teórico 1 − 1/15 = 0,9333), y **0,1000** de los reinicios en la primera décima de la serie
  en ambos — sin sesgo hacia el principio.
- 🔬 **El óptimo de `tile_bytes` medido dentro del comando confirma los 4 MB, pero no es plano.**
  Barrido de siete puntos, reloj de `montecarlo.analyse` (920 ops) y `analyse_long` (3.437 ops):
  0,5 MB → 13,3 / 101,7 s · 1 MB → 10,6 / 62,5 · 2 MB → 9,2 / 43,1 · **4 MB → 8,7 / 33,0** ·
  8 MB → 8,8 / 30,1 · 16 MB → 9,6 / 29,4 · 64 MB → 9,9 / 33,0. Con N grande el reloj sigue bajando
  hasta 16 MB, pero el pico del árbol sube de 2.520 a 2.993 MB: 4 MB es el mínimo de la estrategia
  corta y la elección conjunta.
- ⚠️ **Un solo bloque de repeticiones no sirve para comparar dos versiones de un módulo sin
  semilla.** `net_5` (el mínimo del percentil 5 sobre siete remuestreos) dio con 8 repeticiones
  master −19.678 y tiras −18.903: z = +3,3, aparentemente significativo. Con dos bloques más de
  master salieron −18.841 y −19.261: **la media de un bloque de 8 tiene un 2,2% de dispersión
  propia**, y agrupando 24 contra 16 la diferencia cae a +1,6% (z = +1,7). La comparación que sí
  decide es **apareada**: los mismos sorteos evaluados en `float64` y en `float32` mueven `net` p5
  6,3e-8, `pf` p5 5,4e-10, `dd_pct` p95 1,0e-8 y p99 1,6e-9 en relativo, y `losing_run` sale
  idéntico bit a bit.

## Este servidor tiene 48 núcleos, no 96, y SQX se queda con 71 GB de los 128

🔬 Medido 2026-09-19 buscando por qué `strategies/monteCarlo` no escala.

**CPU — SQX no reserva núcleos, pero `os.cpu_count()` miente.**

- 🔬 Nadie limita nada: afinidad `0-95` para el shell, para Python y para el propio SQX; sin
  `cpu.max`, sin `cpuset`, sin `memory.max` en el cgroup. Con la GUI abierta y ociosa, SQX consume
  **0,8% de un núcleo**. Los núcleos están ahí.
- 🔬 **96 lógicos son 48 físicos.** AMD EPYC 7413, 2 sockets × 24 núcleos × 2 hilos. Los hermanos
  SMT son `cpu N` ↔ `cpu N+48` (`/sys/devices/system/cpu/cpuN/topology/thread_siblings_list`). Un
  solo nodo NUMA.
- 🔬 **El SMT no aporta nada en esta carga, resta.** Mismo kernel, mismo número de procesos:
  96 procesos sobre los 48 físicos → 211.419 caminos/s; 96 procesos sobre los 96 lógicos →
  203.617 caminos/s.
- 🔬 **Los núcleos están libres; lo que falta es DRAM.** Control compute-bound (8 KB, cabe en L1)
  escala **46,1× con 95 procesos**; el kernel real, fuera de caché, escala **18,3×** con los mismos
  95 procesos y con 85,6 de 96 núcleos marcados como ocupados. Ocupados esperando memoria.
- 🔬 **Sobresuscribir empeora el ancho de banda, no sólo lo deja plano.** Triada tipo STREAM
  agregada: **143,7 GB/s con 24 procesos, 121,7 con 48, 101,6 con 95.** Pedir 96 trabajadores
  cuesta un 29% del ancho de banda de la máquina.
- 🤔 De ahí `max_workers`: el punto bueno está entre 24 y 48, y `null` (= `os.cpu_count()` = 96) es
  justo el peor de la curva.
- ⚠️ SQX arranca con **95 hilos `comput` aparcados** ("Preparing thread executors: 95" en el log).
  Ociosos no molestan, pero un build en la GUI compite por la máquina entera. Los dos no caben.

**Memoria — aquí sí hay reserva, y es enorme.**

- 🔬 `~/Desktop/SQX/StrategyQuantX.config` contiene `option -Xmx108g`: la GUI puede crecer hasta
  **108 de los 125 GB**. Ahora mismo tiene **71,5 GB, todos anónimos** (heap de la JVM, 0,1 GB
  respaldado por fichero), así que el kernel no puede recuperar ni un byte mientras esté abierta.
  `user/settings/settings.xml` trae además `memoryCleanup=false`.
- 🔬 `~/Desktop/SQX/sqcli.config` trae `option -Xmx32g`: el worker pide otros 32 GB al arrancar.
- 🔬 Queda **37,4 GB disponibles y 1,2 GB de swap libre**. El módulo Monte Carlo con `chunk: 2000`
  y 95 trabajadores pide **32 GB** en la estrategia más larga de `MC Trades` (N=3.437). Cabe por
  5 GB — y no cabe si el worker de SQX está arrancado a la vez (71,5 + 32 + 32 = 135 > 125).

## SMT y núcleos en un retest de SQX: 48 hilos rinden casi como 95, y 24 la mitad

🔬 Medido 2026-09-23 en el custodio (`SQX_w2`, `-Xmx48g`), con un proyecto desechable `bench_smt`:
un Retest sin SPP ni SO, XAUUSD M1 2008-01-01..2026-08-30, motor MT5 hedged, sobre 2.886 estrategias
(la carpeta `Retester/databanks/RetestOut` de 962 cargada tres veces — `action=load` no deduplica).
`coreUsage` se cambia en `user/settings/settings.xml` **con el worker parado**; el log confirma el
valor en `Preparing thread executors: N`.

| `coreUsage` | hilos | reloj | ms/estrategia (SQX) | %CPU medio del proceso | limpio |
|---|---|---|---|---|---|
| 24 | 24 | 55,5 s | 18 | 1.355 % | ⚠️ no: otra sesión arrancó dos proyectos pequeños encima |
| 48 | 48 | 31,1 s | 10 | 1.815 % | ✅ sí |
| 95 (`-1`) | 95 | 30,4 s | 9 | 3.114 % | ⚠️ no: otra sesión arrancó cuatro proyectos pequeños encima |

- 🔬 **De 24 a 48 hilos el retest escala casi lineal (1,8×). De 48 a 95 gana un 2-10 %.** Las 48
  son los núcleos físicos; los otros 47 son hermanos SMT (`cpu N` ↔ `cpu N+48`). Lo mismo que
  ya se vio en el Monte Carlo de Python: **lo que cuenta son los 48 físicos**. Los dos ciclos
  contaminados lo son *en contra* de la conclusión (carga ajena encima hace que 95 parezca peor de
  lo que es), así que "≤ 10 %" es una cota indicativa, no un número cerrado. Repetir con W2 libre.
- 🤔 Consecuencia: el maestro con `coreUsage -1` (95) y el custodio con 48 **no suman 143 núcleos,
  se pelean por los mismos 48 físicos**. Si el maestro genera mientras el custodio retestea, los dos
  van a la mitad. Y si el maestro pasa a ser sólo un visor (sin builds), el custodio no gana casi
  nada subiendo de 48 a 95.
- 🔬 **Un `sqcli` ocioso cuesta 1,9 GB de RSS y 160 MB de heap vivo** (`jstat`: old 90 MB +
  survivor 71 MB, 267 hilos, `-Xms1g`). Con 964 estrategias cargadas y sin retestear: +350 MB de
  heap tras un young GC (≈ 0,4 MB por estrategia, cota superior sin full GC). Con las 2.886
  retesteadas (entrada + salida con resultados): old gen 5,7 GB a 48 hilos, 7,4 GB a 95, sin full GC
  — basura incluida. **`jcmd` no funciona contra el JVM de SQX** (`AttachNotSupportedException:
  The VM does not support the attach mechanism`, es un build jvmci); sólo `jstat`.
- 🔬 **`sqcli` no carga las estrategias de los proyectos al arrancar.** Recién arrancado,
  `-databank action=count` devuelve `Records: 0`; es `-databank action=list project=X` (o `count`
  sobre un databank concreto) lo que dispara `Syncing databank(s) from files` y las carga. Por eso
  un `action=copy` inmediato copia **0** registros: copia lo que hay en memoria. Para meter una
  carpeta en un databank nuevo: `-databank action=load project=P name=D folder=/ruta` (carga desde
  disco, sí funciona recién arrancado).
- 🔬 `-project action=loadconfig` **exige `name=`** además de `file=` (`Error: Missing parameter
  'name'`), y `file=` relativo se resuelve contra la carpeta del install, no contra el cliente.
- ⚠️ **El `status` de un Retest sin SPP no tiene la línea `Total tested`.** Trae `Strategies
  generated`, `Time per strategy`, `Running time so far`, `In databank`. El `TESTED` de
  `sqx/variants/execute.py` sólo existe porque la tarea del pipeline lleva SPP; sobre un retest
  plano `re.search` devuelve `None` y el `.group` revienta. La señal de fin que sirve para ambos es
  `-databank action=count` del databank de salida.

### ⚠️ Lo que salió mal: dos sesiones sobre el custodio a la vez

📓 Mientras yo hacía estos ciclos (cada uno arranca, carga, corre, **para** W2 y edita su
`coreUsage`), **otra sesión de Claude estaba usando el mismo custodio** para bisecar costes
(`bisect_sin_costes`, `bis_fechas_solo`, `bis_slippage`, `bis_comision`, `bis_swap`,
`bis_slip_*`, `chat_keltner_M30`, `ctrl_*`). Consecuencias, todas visibles en
`SQX_w2/user/log/StrategyQuant/log_2026_09_23.log` entre 07:20 y 07:37:

- Mis `stop` (07:26:21, 07:27:11, 07:27:42, 07:29:19, 07:30:28, 07:31:37, 07:32:58) **mataron sus
  corridas** a medias. Sus proyectos arrancaron encima de mis instancias y los míos encima de las
  suyas; dos de mis tres medidas quedaron contaminadas y las suyas corrieron con un `coreUsage`
  que yo había cambiado (24 ó 95 en vez de 48).
- Un `start` a las 07:31:41 abrió puerto **5050** desde `SQX_w2` y murió con `Database may be
  already in use: Locked by another` — dos procesos intentando el mismo H2.
- La regla «al custodio no se le habla mientras trabaja» **no la impone ninguna herramienta**:
  `execute.awake()` respeta una instancia ya levantada, pero `bin/sqx-worker.sh stop` para lo que
  haya, sea de quien sea, y un script ad hoc (el mío) ni siquiera pasa por `awake()`. Con cinco
  sesiones paralelas en la máquina (`ListAgents` las lista) la colisión no es un accidente raro,
  es lo esperable. Pendiente en `OPEN.md`: un lock de propietario en `bin/sqx-worker.sh`
  (`start` escribe quién lo levantó; `stop` de otro se niega salvo `--force`), y **antes de tocar un
  worker, `ListAgents` + mirar `ls -lt user/projects` y la cola del log**.

## Un `ProcessPoolExecutor` global sin apagado deja el pool vivo cuando el padre muere

🔬 Encontrado 2026-09-19. `strategies/monteCarlo/simulate/engine.py` guarda el pool en `_POOL` y no
lo cierra nunca — no hay `shutdown()` ni `atexit` en todo el repositorio. Si el proceso padre muere
sin desenrollar la pila (Ctrl-C duro, `kill -9`, el panel Flask cerrado desde la terminal), el
`forkserver` y sus trabajadores quedan **reparentados a systemd y vivos indefinidamente**. En esta
máquina había **68 procesos huérfanos ocupando 9,4 GB**, uno de ellos de hace nueve días y con la
ruta de módulo *anterior* a la reorganización (`strategies.monteCarlo.engine`), lo que prueba que
sobreviven a cualquier cosa. Se ven con:

```bash
ps -eo pid,ppid,etime,rss,cmd | grep -E 'forkserver|resource_tracker' | grep -v grep
```

y se limpian matando por PID el padre `forkserver` cuyo PPID sea 1. Nunca `pkill -f python3`.

## 🔬 Measuring this project's own cost (2026-09-20)

Found building `perf/`, the performance catalogue. Every number here is measured on this machine.

- 🔬 **`ru_maxrss` is the wrong memory number as soon as a module spawns workers.** For child
  processes `getrusage(RUSAGE_CHILDREN)` reports the **largest single child**, not their sum, and
  `RUSAGE_SELF` of course sees only the parent. `montecarlo.analyse` on one strategy at 5,000
  simulations reads **535 MB** by `ru_maxrss` and **2,340 MB** by sampling the whole process tree
  from `/proc/<pid>/stat`. Anything deciding whether a run fits in RAM has to sample the tree.
  Sampling every 50 ms can still miss a shorter peak, so the tree figure is a floor.
- 🔬 **A `tracemalloc` snapshot taken after the call shows what survived, which is nothing.** The
  first version of `perf/measure/runner.py` reported every allocation site at 0.0 MB for this
  reason. The sites that matter are alive at the peak, so a watcher thread keeps a snapshot from the
  moment the traced total was highest.
- 🔬 **This machine's ceiling is memory bandwidth, and it arrives at 16 processes.** The same STREAM
  triad moving the same bytes: cache-resident it scales to **575 GB/s at 96 processes and keeps
  rising**; DRAM-resident it flattens at **57 GB/s from 16 processes on**. A kernel whose working
  set does not fit in cache gets nothing from the 80 cores past that point — they wait for memory.
  Reproduce with `python3 -m perf.catalogue --scaling`.
- 🔬 **Comparing wall clock between dates is wrong here; compare per unit of work.** Exports grow.
  `history.csv` stores the scale with every measurement for exactly this.
- 🔬 **A pool that is never shut down outlives everything.** Found 68 orphaned `forkserver` workers
  holding 8.9 GB, one of them nine days old and carrying the module path from *before* the
  `strategies/monteCarlo/` reorganisation. They are reparented to systemd and survive any restart of
  the panel. `ps -eo pid,ppid,etime,rss,cmd | grep forkserver` finds them; they are killed by PID,
  children first — never `pkill -f python3`, which matches your own shell.

## 🔬 Budgeting RAM across SQX and Python (2026-09-21)

Found while deciding how many SQX installs fit on one machine. Measured on the 96-core / 125 GB box.

### `jstat -gc` separates what a JVM *needs* from what it was *allowed*

⚠️ **RSS of a JVM with a generous `-Xmx` measures nothing.** The master showed **67.5 GB RSS** and
looked like it needed 67 GB. It did not:

```
$ ~/Desktop/SQX/j64/bin/jstat -gc 3385011
   EC 12,711,936 KB   EU          0 KB     ← eden, just collected
   OC 47,538,176 KB   OU 16,686,751 KB     ← old gen
   YGC 252 (21.3 s)   FGC 39 (41.9 s)
```

**Committed heap 57.4 GB · live set 15.9 GB.** With `-Xmx108g` and `UseParallelGC` there was never
any pressure to collect, so the heap grew lazily and kept the garbage. 1.5× the measured live set is
`-Xmx24g`, and that is what the master should carry.

⚠️ **An earlier version of this page said the master "was re-sized to `-Xmx24g` on that evidence".
It had not been** — `StrategyQuantX.config` still read `-Xmx108g` on 2026-09-21, file mtime
2026-09-19. Either the edit was never applied or something reverted it. **Applied for real
2026-09-21**, verified by reading the file back. The lesson is the cheap one: a heap figure in a
document is not a heap figure on disk; `grep Xm <install>/*.config` is one command.

- **The JDK tools ship inside the install**: `~/Desktop/SQX/j64/bin/{jstat,jcmd,jinfo,jps}`. They are
  not on `PATH`.
- **Use `jstat`, not `jcmd`**, on the owner's running master: `jstat` reads the shared perf counters
  off disk and never attaches to or signals the process.
- `OU + EU` is the number that matters. `FGCT` growing by more than a few seconds per hour means the
  heap is too small.

### The budget, and why the two halves are not symmetric

```
Σ(-Xmx)  ≈  (RAM_total − 5_OS − Python_reserve) / 1.08      # 1.08 = JVM overhead beyond heap
```

🔬 **A Python reserve costs nothing until it is used; an `-Xmx` is spent the moment it is granted.**
A reserve is just RAM not promised to any JVM — if unused it stays free for whoever needs it. An
`-Xmx` is a permission the JVM *exercises*, as the master proved. So be generous with the Python
reserve and careful with heap ceilings.

🔬 **The Python side does not compete for RAM.** Worst of the nine catalogue targets,
`montecarlo.analyse_long`, peaks at **2.5 GB** (`AlgoData/perf/history.csv`, 2026-09-21);
`montecarlo.analyse` at 0.33 GB. The owner's 24 GB reserve is for the future app, not for today's
analysis.

🔬 **`-Xms` low on the workers is what makes three installs fit.** An idle worker with `-Xms4g`
(the shipped default in `sqcli.config`) holds 4 GB doing nothing. Dropped to `1g`/`2g`, an idle
worker costs almost nothing and only the busy one is expensive.

### Revised 2026-09-23 — the master is rarely open, so W2 takes the RAM

⚪ Owner's decision: W2 `-Xmx80g` (was 48g) and `coreUsage -1` (was 48), Python reserve 20 GB, OS
10-12 GB. Applied to `SQX_w2/sqcli.config` and `settings.xml` with the install stopped. The
constraint that comes with it: the master GUI as a viewer (`-Xmx12g`) still fits next to a full W2;
the master **generating** with 24g does not (swap is 4 GB, whoever overflows is OOM-killed).

### The two machines

| | PC-A 96c / 125 GB | PC-B 16c / 128 GB |
|---|---|---|
| binding constraint | **RAM** | **CPU** — RAM is abundant |
| M / W1 / W2 `-Xmx` | 24 / 16 / 48 GB | **identical** |
| M / W1 / W2 `coreUsage` | −1 / 8 / 48 | −1 / 2 / 8 |
| **applied on PC-A** | **2026-09-21, all three** | not yet |
| 5,000-variant retest | 3.5 min | ~21 min |

**Identical heaps on both, despite PC-B having more RAM.** Raising ceilings because RAM is free buys
nothing but uncollected garbage — that is the master's lesson, above. 🔭 On PC-B the longer jobs make
the custodian role *more* valuable, not less: the window in which a stray command would destroy work
is six times wider.

## 🔬 A resumable job needs three separate facts, and two of them are not the ledger (2026-09-21)

Written while building `pipeline/`, and measured with `pipeline/verify/selftest.py`.

### A ledger entry is not evidence that the work survived

"Did this stage finish?" has three different answers and a multi-day unattended run meets all
three. The ledger says done; the outputs are on disk; the outputs are *still what was written*.
`pipeline/stages/gates.py` needs the first two to skip a stage, because the ledger outlives the
data it describes on purpose — a mother whose variants were swept would otherwise read as one that
never finished, and the pipeline would rebuild 5,000 variants to reach a verdict it already had.
`pipeline/cleanup.py` needs the third, and gets it by re-hashing: a recorded sha256 is what turns
"the export probably worked" into evidence that outlives the data.

### `os.replace` plus a polling reader: measured, not assumed

The claim that an atomic replace lets a monitor read a file another process is writing is easy to
repeat and easy to get wrong (a plain `write_text` truncates first, and a reader lands in the
hole). Measured: a thread reading `state.json` every 20 ms while five stages wrote it through
temp-file-plus-`os.replace` never caught a partial file across the whole self-test. The temp file
must be in the **same directory**, not `/tmp` — `os.replace` is only atomic within a filesystem,
and `AlgoData` is not necessarily on the same one as the repository.

### `SIGKILL` the process *group*, or the test is a lie

The resume test kills the pipeline mid-stage. Killing the child alone leaves the stage's own
subprocess running, and it keeps writing progress into the ledger of a pipeline that no longer
exists — which passes the test for the wrong reason. `start_new_session=True` plus
`os.killpg(os.getpgid(pid), SIGKILL)` is what actually reproduces a power cut. Measured: the stage
died at 20 %, `state.json` still parsed, the stage was not recorded as finished, and relaunching
skipped the completed stage and retook the killed one.

### "Progress never decreases" is not the property worth testing

A stage that writes 0 and then 100 at the very end satisfies monotonicity perfectly and is exactly
the failure the requirement exists to prevent — the owner staring at a screen that shows nothing,
unable to tell a long stage from a hung one. The test that bites is **an outside reader seeing at
least two distinct intermediate values**, which is what `pipeline/verify/monotonic.py` asserts.
Monotonicity is worth enforcing too, but as a raise rather than a clamp: clamping turns a stage
that repeats work it already did into a bar that merely sits still.

### Split a command template before filling it in, not after

`shlex.split(template.format(...))` turns `--strategy Strategy 17.9.39` into three arguments. The
same whitespace trap that forces SQX project names to use underscores (`CLAUDE.md` rule 6) reaches
any subprocess built from a template. Formatting each token of an already-split template is one
line and has no such failure mode.

### A stage joins by printing, not by importing

`pipeline/` chains modules that three other agents are writing at the same time. The entire
coupling is one stdout line, `PROGRESS <0..100> <status>`; anything else a stage prints becomes its
status without moving the bar. Measured on the one real stage that exists: `strategies.sppUltra`
does not know the protocol, and still records a live status line each time it prints, with progress
going 0 → 100 at the end. An import-based contract would have blocked all three agents on each
other's signatures.

## 🔬 Log retention: archive first, prune second, never the day in course (2026-09-21)

📓 **What the 4.66 GB day actually was (read 2026-09-23, then condensed).** 43.9 million lines, of
which **39.8 million were Java stack frames** and 2 million the same exception:
`TradingException: Setting 'TradingSetup.StrategyClass' is not set.`, thrown by `StatsComputer`
inside `WFSimulationJob` while a Walk-Forward Matrix cross-check computed the custom databank
columns `ParameterCount` and `DoFRatio` (`SQ.Columns.Databanks.*`, the owner's own columns) on
every WF step. Plus 49,080 × `NonexistingVariableException: Variable 'PriceEntryMult…' doesn't exist`
from the same job, and 184 × `Project 'Infinox - SPNft - HN (High Precision)' does not exist` (the
hourly sync failure `OPEN.md` issue 6 already tracks). Everything else fitted in **2,825 lines**.
So: **a WFM cross-check over strategies whose custom columns cannot compute per step writes a
gigabyte per hour of log**, and a log that size is a symptom of that job, not of the day's work.
The archive keeps `log_2026_08_18.condensed.log.gz` (36 KB): stack frames dropped, the four
repeated messages replaced by their counts on the last line.

📓 **The projects' own `log/` folders are 97 % EdgeDecay noise.** `user/projects/<P>/log/global_log_*`
logs three lines per strategy per pass of the `EdgeDecayFilter` custom analysis
(`Strategy N, running Per strategy analysis: EdgeDecayFilter` / `- OK` / `- Failed`): USDJPY's
566 MB file was 15.5 M lines, 135 K without them. The signal that remains — every `TASK STARTED` /
`TASK FINISHED` block with databank counts before and after, per-filter rejection counts and
time per strategy — is kept in `AlgoData/logs/SQX/projects/<P>/*.condensed.log.gz` (1,278 files,
6.7 MB for the ten projects of the 2026-09-21 snapshot). `archive_logs.py` does not cover these
folders (it walks `user/log`), and a `user/projects` snapshot must exclude them.

SQX's own log directory has no ceiling and no working prune. Measured on the master that day:
**35 files, 4.5 GB**, and the distribution is not gradual — it is two error storms.

| file | size |
|---|---|
| `log_2026_08_18.log` | **4.4 GB** |
| `log_2026_09_20.log` | **55.5 MB** |
| `log_2026_09_19.log` | 1.2 MB |
| a normal idle day | ~130 KB |

📓 One bad day is 34,000× a normal one. `archive_logs.py`'s docstring says "SQX keeps only 14 days —
SQX prunes on start"; **on this install that is false** — files from 2026-06-13 were still present.
Do not rely on SQX pruning anything.

**The policy, in force from 2026-09-21.** Two halves, and the order between them is the whole safety
argument:

1. **Archive.** `sqx.export.archive_logs` runs from cron at 08:00 daily and gzips **every**
   install's logs into `AlgoData/logs/<install>/`. It compresses **4.5 GB → 104 MB** (2.3%). Nothing
   is being kept for its bytes; it is being kept for its content, and the archive keeps that.
2. **Prune.** `bin/sqx-log-prune.sh` deletes a live log only when **a `.gz` copy of it already
   exists in the archive** — it prints `KEEP … sin copia en el archivo` and refuses otherwise. So a
   prune can never outrun the archiver, whatever order cron happens to fire them in.

**🔬 A daily cron is the wrong shape for this, and `--auto` is the fix (2026-09-21).** Cron fires at
a wall-clock time; a machine that is off at 08:15 simply skips that day, and the 4.4 GB file sat for
a month. `sqx-log-prune.sh --auto` is the event-driven form, wired to **activity** instead:

- It **archives first, then prunes.** Without that a frequent prune finds nothing it is allowed to
  delete, because deletability is exactly "a `.gz` already exists". This is the whole reason `--auto`
  is not just "the prune, but more often".
- It is **rate-limited by a stamp file** (`AlgoData/logs/.prune-stamp`, `MIN_HOURS`, default 4), so
  calling it on every trigger is free: **50 ms** when the limit blocks it, **170 ms** when it runs
  with nothing to do (`archive_logs` skips an up-to-date `.gz` by mtime and costs 77 ms).
- It is **silent unless bytes moved or something is wrong.** A trigger that prints on every session
  start gets ignored within a week.

Triggers, in order of how often they fire: the `SessionStart` and `Stop` hooks in
`.claude/settings.json` (async, so they never delay a turn), `bin/sqx-worker.sh start` and `stop`
(a stopped worker holds no log — the quiescent moment), and the 08:15 cron as the backstop for a day
when nobody opens the project at all.

⚠️ **The guard checks that a `.gz` exists, not that it matches.** SQX's logs are append-only and the
archiver re-archives whenever mtime moves, so divergence needs a file rewritten *with an older
mtime* — which SQX never does, but a test fixture does. Found while testing, worth knowing before
trusting the guard against something other than SQX.

**⚠️ The one thing pruning can never reclaim is the current day's log**, and on an error-storm day
that is the entire problem: 55 MB by 20:44, 4.4 GB over one day. SQX holds it open. So `--auto`
does the only useful thing instead — it **shouts** when the live log passes `WARN_MB` (default 200):

```
AVISO: SQX/log_2026_09_21.log son 412 MB y es el log del dia en curso — la poda no puede tocarlo.
       Eso es una tormenta de errores en marcha. 'tail -100' ese fichero y arregla la causa.
```

📓 That check must live **outside** the `find -mtime +$KEEP_DAYS` loop. Written inside it, it is
unreachable code: `-mtime +7` can never return a file written today. It was wrong that way first.

- **Retention: 7 days** in the install (`KEEP_DAYS`, overridable), unbounded in the archive.
  7 days is enough to tail a live incident; anything older is a forensic question, and forensics
  reads the `.gz`.
- ⚠️ **Never the current day's log.** The script skips `log_$(date +%Y_%m_%d).log` by name. SQX holds
  it open and appends; deleting it under a running instance loses the day.
- **Scheduled**: `15 8 * * *`, fifteen minutes after the archiver's `0 8 * * *`. The order is
  belt-and-braces, not load-bearing — the archive check makes the prune safe at any hour. Since
  `--auto` exists this cron is only the backstop for a day with no session at all.
- The script covers **every install** and both file families (`log_*.log` and `launcher_*.log`), and
  `--dry-run` lists what would go without deleting. First real run reclaimed the 4.4 GB.
- ⚠️ 🔬 **The archiver and the pruner have to walk the same list of installs, and for one day they
  did not (fixed 2026-09-21, evening).** `archive_logs.py` defaulted to `[MASTER, WORKER]` — a
  two-install constant written before roles existed — while `sqx-log-prune.sh` asks `core.paths` for
  the master plus *every* role. So the custodian's logs were archived never, and therefore, by the
  safety rule, pruned never: they just printed `KEEP … sin copia en el archivo` and grew. The
  archiver now defaults to `[MASTER, *WORKERS]`. **A role added to `machine.yaml` in future is
  picked up by both halves automatically** — that is the point of asking `core.paths` rather than
  naming installs.
- **The archive itself is not pruned, and does not need to be.** It is bounded by the `logs: 1 GB`
  entry in `perf/config.yaml` (0.11 GB today, compressing 2.3%), and `perf.disk.report` exits
  non-zero when a branch is over. That check is the periodic look, not a deletion. Deleting archived
  logs would remove exactly the thing that makes deleting live logs safe.
- ⚠️ **That log is never read whole — it is tailed.** 4.4 GB in an editor is a dead session.
  `tail` and `grep`, always.

🔬 **The archive is dominated by the same storms, and it has no ceiling.** Measured 2026-09-21:
`AlgoData/logs/` is **104 MB, of which 101 MB is one file** — `log_2026_08_18.log.gz`, the 4.4 GB
day compressed 43×. Every other day of the year together is 3 MB. So "the archive is cheap" is true
only while no storm happens; each one adds ~100 MB forever. 🤔 Untested but obvious: a log that is
one stack trace repeated millions of times keeps all its information in a digest (first and last
occurrence, plus a count per distinct message). Nothing has been deleted from the archive — the
option is recorded, not taken.

🔬 **The 55 MB day was not volume, it was one repeating error.** `log_2026_09_20.log` is the
`Infinox_SP500ft_H4_HighPrecision` sync failure looping hourly (`OPEN.md` issue 3). **Log hygiene
and that repair were one problem seen from two sides**: prune and the disk stops filling; graft the
missing task files and it stops being written in the first place.

⚠️ **Only one of those two sides is being done.** The owner withdrew the repair on 2026-09-21
(`OPEN.md` issue 3, ⚪). So **the cause stays and the pruning is permanent load-bearing
infrastructure**, not a tidy-up while a fix lands. Two things follow: the retention policy cannot be
relaxed, and anything that reads the master's log must filter `ProgressEngine` at source rather than
expect a quiet file.

### The number that stops the run and the number that produces a verdict are different things

Both are "a figure compared against a limit", and putting them in the same place is the easy
mistake. A failed canary does not mean the strategy is bad — it means the variants SQX returned
are not the ones that were written, so **nothing measured afterwards means anything**. Judging it
produces a verdict nobody should read; gating on it stops the machine before it spends hours. The
test that separates them: does the number say *this strategy is not good enough* (a threshold, the
user's, in `config.yaml`, changeable without reprocessing) or *this measurement is invalid* (a
gate, on the recipe row, stops the run)? In `pipeline/` the canaries are a gate and are
deliberately absent from `verdict.rules`.

### Fingerprinting the design is what catches the failure that does not crash

`brief_hash` in the C5 ledger looks like bookkeeping until you ask what it is for. The brief is
read once, 5,000 variants are fabricated from it, and everything afterwards is measured against
numbers the brief also carries. If the brief is regenerated in between — sppUltra rerun, a
threshold changed, a different export day — nothing errors: the run completes and reports one
design judged against another's numbers. `gates.unchanged` compares the recorded hash to the file
before every stage and refuses. **A recorded hash with nothing reading it is decoration**; the
gate is what makes the field worth writing.

### A provisional cost is a decision; a missing one is a blocker

`core.assets.pending()` returns only the fields whose `use` is null, not the ones marked
PROVISIONAL. That distinction is the right one for a gate: XAUUSD's spread and commission are SQX
defaults the owner has not replaced yet, and refusing to run on that would block everything for
weeks. What the pipeline does instead is start, and stamp `costs_provisional: true` into every
ledger, so no money figure produced under it can later be mistaken for one priced properly.

## 🔬 In-sample parameter optimisation does not rank the out-of-sample result (2026-09-22)

First real output of the walk-forward-correlation chain, and it is a result about the research
method rather than about one strategy.

`XAUUSD/Strategy 17.9.39`, M30, 2008–2017 in sample and 2018–2022 out, 2,000 parameter tuples drawn
across the whole design, every one of them retested for real:

| points asked | usable | rho | 95 % interval | call |
|---|---|---|---|---|
| 11 | 9 | 0.18 | [−0.55, 0.75] | indeciso |
| 150 | 74 | 0.23 | [−0.00, 0.43] | indeciso |
| 600 | 297 | 0.22 | [0.10, 0.32] | indeciso |
| **2,000** | **1,001** | **0.19** | **[0.13, 0.25]** | **no_fiable** |

- 🔬 **Spearman rho ≈ 0.19, and the interval excludes both 0 and the 0.30 floor.** So the surface
  carries *some* information — this is not noise — but nowhere near enough to rank on. Picking the
  parameter set with the best in-sample net profit buys almost nothing out of sample.
- 🔬 **rho barely moved across a 180-fold increase in sample size (0.18 → 0.19).** The estimate was
  right at eleven points and useless at eleven points; what changed was the interval. **Report the
  interval, not the coefficient** — a study that had stopped at a dozen tuples would have had the
  correct number and no way to know it.
- 🔬 **About half of any batch is unusable.** 1,001 of 2,000 tuples traded fewer than 30 times in
  one of the two samples. That is a property of the design, not of the filter: the neighbourhood
  and coverage strata reach into corners where the strategy stops trading. Budget for it — ask for
  twice the points you want.
- 🤔 **The obvious next question is whether this is the strategy or the family.** One strategy
  cannot distinguish "this one's parameters are meaningless" from "the XAUUSD generation run
  produces strategies whose parameters are meaningless". The chain now runs unattended, so the
  answer is to run it over the databank rather than to argue about it.
- ⚠️ **Costs were the PROVISIONAL XAUUSD figures** (SQX defaults, not agreed Infinox ones). A rank
  correlation is far less sensitive to a constant cost error than a net profit is, so the finding
  should survive the correction — but it has not been re-run against agreed costs, and
  `state.json` carries `costs_provisional: true` for exactly this reason.

## Nulos de entrada aleatoria — qué mide un "mono" y qué no

Medido 2026-09-22 con `nulls/` sobre `raw/XAUUSD/MC_Trades/2026-09-19/`: 757 estrategias,
960.705 trades, muestra `OOS1` (2018–2022, 320.423 trades), 2.500 draws por peldaño, fill
`open-open` reconciliado (mediana 0.999983, mínimo 0.99945). Costes PROVISIONALES de XAUUSD.

⚠️ **Las primeras cifras de este hilo se midieron con fill close-close y estaban mal.** Un 4-13 %
de correlación perdida en la reconstrucción movía los porcentajes entre 10 y 26 puntos sin que
nada saltara. Las de aquí abajo son las del motor reconciliado.

🔬 **El canal de edge por sizing está vacío en este corpus.** `corr(Size, P/L por unidad)` tiene
mediana **+0.001**; |corr| > 0.05 en el 10.7 % de las estrategias contra el ~7 % que da el azar
con n≈1.270. **Esto solo descarta el canal de *retorno*, no el de *varianza*:** normalizar por
volatilidad estabiliza la varianza y sube el Sharpe sin tocar la media, y esa correlación no lo
ve. Lo mide el peldaño `timing_sizing` de `nulls/`, y nada más.

🔬 **El sizing es ATR puro y NO compone sobre el equity.** `CV(Size × ATR)` baja de 0.384 (Size
crudo) a 0.200 con ATR(14) y 0.119 con ATR(50); dividir además por `Balance` lo **empeora** en
todos los periodos (0.220 / 0.157). La familia está identificada y los parámetros no — el periodo
del ATR está en el `.sqx`, no se ajusta. Consecuencia: los runs aleatorios no tienen dependencia
secuencial y el problema es vergonzosamente paralelo (757 estrategias × 4 peldaños × 2.500 draws
en **2m37s**).

🔬 **El listón del mono lo fija el coste, no la deriva.** Con ocupación del 7.4 % (366 trades ×
12 barras M30 sobre 59.112), el mono captura ~2.867 $ de la subida del oro (1307 → 1822) y paga
~7.756 $ de coste. Su media es negativa en el **100 %** de las 757 estrategias (mediana −4.698 $).
Por eso batir al mono es un listón **más bajo** que batir a cero, y no al revés.

🔬 **El estadístico mueve el veredicto mucho más que el null.** De una sola simulación, peldaño
`timing`, p < 0.05:

| estadístico | pasan | |
|---|---|---|
| `dd` | 84.5 % | el más permisivo |
| `sharpe` | 77.4 % | |
| `retdd` | 76.9 % | |
| `pf` | 55.2 % | |
| `net` | **39.5 %** | el más duro |

**Nunca reportar un solo estadístico.** `nulls/config.yaml` lista cinco y no elige.

🔬 **La razón es que el Sharpe es invariante de escala y las dos poblaciones de trades no son la
misma.** Con fill open-open, sobre 120 estrategias:

| por trade | estrategia | mono | |
|---|---|---|---|
| desviación | 491 $ | 661 $ | el mono es un **36 %** más volátil |
| skew | +0.53 | −0.78 | signo opuesto |
| curtosis | 6.4 | 27.0 | 4× más cola |

`mean/std` divide fuera justo esa diferencia. **Ser más tranquilo que el azar es un edge**, el
Sharpe lo cobra y el neto no.

🔬 **Frente a MinTRL: el mismo eje con el Sharpe, tests distintos con el neto.** MinTRL sobre el
P/L que SQX reportó pasa **202/757 (26.7 %)**. Cruzado contra el mono:

| estadístico del mono | pasan MinTRL y NO el mono | pasan el mono y NO MinTRL |
|---|---|---|
| `sharpe` | **0** | 384 |
| `retdd` | **0** | 380 |
| `pf` | 5 | 221 |
| `dd` | 15 | 453 |
| `net` | **48** | **145** |

Con `sharpe` la contención es total —MinTRL ⊂ mono— y coincide con que la dispersión del null
del mono × √n da **1.006**, que es la dispersión iid: ahí `psr(returns, benchmark=media_del_mono)`
reproduce la simulación (corr 0.9956 en el p). Con `net` los dos tests **se cruzan en las dos
direcciones**: no es que uno domine al otro, es que miden cosas distintas. Un cribado con MinTRL
antes del mono descarta 48 estrategias que el mono aprueba por beneficio.

⚠️ La aproximación normal tiene la cola más fina que el null simulado, así que sirve para la
puerta en p≈0.05 y **no** para la cola extrema tras corregir por multiplicidad. Para un
Benjamini-Hochberg sobre la lista corta manda la simulación.
