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
| `degrade.py` | Whether each family's headline statistic degrades from in-sample to out-of-sample. | imported | stream → shapes |
| `engine.py` | Run one simulated sub-test across every core, and say how far along it is while it does. | imported | model → statistics |
| `family_d.py` | Family D's execution: stationary bootstrap inside every calendar window and volatility tercile, plus the two time series its page draws. | imported | stream, bars → dict |
| `fan.py` | The equity envelope: where the simulated paths ran, trade by trade, around the real one. | imported | stream → bands |
| `kernel.py` | The core statistics of many equity paths in one compiled pass, without the path matrix. | imported | positions or P&L → statistics |
| `metrics.py` | The core statistics of an equity path, computed on thousands of paths at once. | imported | paths → statistics |
| `stability.py` | Whether the simulation count is high enough: the same gate numbers, computed again. | imported | stream → spread |
| `stitch.py` | The adversarial path: a bad draw from every period of the history, one after another. | imported | stream → worst path |
| `sweeps.py` | Which reordering and resampling runs a stream of this size gets, and the numbers they give. | imported | N → runs |
| `tiles.py` | One worker's batch, computed in strips of rows small enough to stay in cache. | imported | batch → statistics |

## Contracts and traps

- **`engine.py` holds a module path inside a string.** `set_forkserver_preload(["strategies.
  monteCarlo.simulate.engine"])` is not an import and no linter will follow it. Get it wrong and
  nothing fails — every worker just reimports from scratch and the study quietly gets slower. If a
  run takes noticeably longer than it used to, check this line first.
- **Family D is the only family with execution of its own.** A/B are `sweeps` over `draws`, C is
  `engine` over `stress`, E is closed-form in `verdict/significance`; D bootstraps *inside* each
  window and each tercile, which is a different loop, so it gets `family_d.py`. The asymmetry is
  real, not an accident of naming.
- **Every draw is seeded (owner, 2026-10-14).** `engine.single/sequential/run`, `fan.*` and
  `tiles.batch` take a required `seed` (the CLI's `--seed`, `config.seed(cfg)`); the engine derives
  one `SeedSequence` per sub-test and chunk, so no two share a stream. The stitched worst path keeps
  its constant `stitch.SEED`. `stability.py` still asks how far the gate-driving percentiles move
  between independent runs: it passes a distinct seed per repeat (`seed + 1 + i`) and records them.
  Figures stored before 2026-10-14 do not reproduce.
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
