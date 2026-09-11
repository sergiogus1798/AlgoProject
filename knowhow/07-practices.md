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
