# monteCarlo/simulate — what are the numbers, under a given model?

The execution layer. It takes a stream from `inputs/` and an assumption from `model/`, runs it tens
of thousands of times across every core, and returns distributions: percentiles, histograms, ranks,
equity bands. **It chooses no model and judges no output** — every threshold lives in `verdict/`,
and every module here would produce the same arrays if the study's verdict rules changed tomorrow.

**Imports from:** `inputs/`, `model/`, and `verdict/confidence` for the sample-size tier
**Consumed by:** `run.py`, `verdict/`, `render/`, `explorer/`
**Must not contain:** a threshold, a pass/fail, or a sentence the owner reads

| file | what it does | run it | in → out |
|---|---|---|---|
| `tiles.py` | One worker's batch, in strips of rows sized in bytes so memory does not grow with N | imported | batch → statistics |
| `kernel.py` | The core statistics of many equity paths in one compiled numba pass, read straight out of `source[idx]` without building the path matrix; checked against `metrics.paths` to 2.5e-15 | imported | positions or P&L → statistics |
| `metrics.py` | Net, drawdown, Ret/DD, Sharpe, profit factor and the longest losing run, on thousands of paths at once | imported | paths → statistics |
| `engine.py` | Runs one sub-test across every core, with a live progress bar | imported | model → statistics |
| `sweeps.py` | Which reordering and resampling runs a stream of this size gets | imported | N → runs |
| `fan.py` | The equity envelope of the reordered paths | imported | stream → bands |
| `stitch.py` | The adversarial path: a bad draw from every period, concatenated | imported | stream → worst path |
| `family_d.py` | **Family D's execution.** Composition bootstrap inside every window and volatility tercile, the equity curve with its window marks, and the price/vol time series | imported | stream, bars → dict |
| `degrade.py` | The IS/OOS pair of each family's headline statistic, resampled on just that scope | imported | stream → shapes |
| `stability.py` | The same gate numbers computed again, to price the noise in them | imported | stream → spread |

## Contracts and traps

- **`engine.py` holds a module path inside a string.** `set_forkserver_preload(["strategies.
  monteCarlo.simulate.engine"])` is not an import and no linter will follow it. Get it wrong and
  nothing fails — every worker just reimports from scratch and the study quietly gets slower. If a
  run takes noticeably longer than it used to, check this line first.
- **Family D is the only family with execution of its own.** A/B are `sweeps` over `draws`, C is
  `engine` over `stress`, E is closed-form in `verdict/significance`; D bootstraps *inside* each
  window and each tercile, which is a different loop, so it gets `family_d.py`. The asymmetry is
  real, not an accident of naming.
- **There is no seed anywhere, on purpose.** Every run draws fresh entropy, so two runs never agree
  to the last decimal. `stability.py` replaces reproducibility with the honest version of the same
  question: how far do the gate-driving percentiles move between independent runs? A seed would hide
  exactly that.
- **The block sweep can vanish.** When N cannot support `min_blocks` blocks of the smallest size,
  `sweeps.plan()` skips it and flags it rather than running a degenerate randomisation.
- **`chunk` is task granularity, `tile_bytes` is the memory knob.** `chunk` bounds simulations, so
  what a worker cost used to depend on how long the strategy was; `tile_bytes` bounds the strip in
  bytes, so it does not. Neither may change a number.
- **A strip sampler must not recycle its uniforms.** `tiles.batch()` asks the model for a fresh
  draw per strip instead of reusing one buffer for "does the block restart" and "where does it
  restart": sharing it correlates the restart positions with the 1/block threshold and piles them
  at the head of the stream.
- **The gathered P&L is float32 and every accumulator in `metrics.paths` is float64.** Accumulating
  in float32 moves net profit by millidollars and `sweeps.invariant()` stops being zero, which is
  the one thing it is allowed to be.
