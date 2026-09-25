# retest/inputs — what is this study being run on?

The configuration layer. It turns three outside things — `config.yaml`, the eight task databanks
and the parquet an ingest wrote — into the two objects every other layer takes: a `cfg` dict and
per-simulation frames. **Nothing here is computed from a simulation**, which is what makes it safe
for any layer, inference included, to import.

It is separate from `model/` because the two answer different questions: this layer says *which
runs the study starts from and what SQX did to produce them*, `model/` says *what a number read off
one of those runs actually means*.

**Imports from:** `core/` only · **Consumed by:** every other layer
**Must not contain:** a reconstruction, a statistic, or a threshold

| file | what it does | run it | in → out |
|---|---|---|---|
| `config.py` | Reads `config.yaml`, applies `--set` overrides, and flattens it to dotted keys for the drawer and the manifest | imported | overrides → config |
| `tasks.py` | **The provenance contract.** The eight tasks, what each perturbs and holds fixed, and the check that a databank really holds the task it claims | imported | `.sqx` → provenance, mismatches |

## Contracts and traps

- **`tasks.verify()` asserts the isolation, never the magnitudes.** Which methods ran and over which
  sample is the study's design, and a databank running two methods cannot attribute its damage to
  either — so ingest refuses it. The *numbers* those methods ran with are the owner's decision
  (hard rule 3) and are recorded and printed, never judged. A re-run with a wider spread range still
  parses, and the report says which range.
- **`tasks.usable()` is a different severity from `verify()`, and mixing them was a real bug here.**
  A run cut short is not a wrong task: SQX writes the confidence table over the count it was *asked*
  for, so a run storing 999 of 1000 has every rank in that stored table shifted by one — but the
  simulations themselves are fine, because indices truncate at the tail and never gap. The
  reconstructed channel stays valid; only the stored one is lost. **3 of the 40 runs are like this**
  (`bar/1.19.29`, `exits/1.19.29`, `ohlc/41.5.25`), measured 2026-09-18.
- **`bar` is a control, not a test, and `ROLE` says so.** A backtest re-run with nothing meaningful
  changed still moves — measured, σ of 57 to 579 USD against 4,089 to 11,923 for `params`. Every
  other task's effect is reported in units of that floor. Give it a threshold and it fires on
  strategies with nothing wrong with them; give it no role and the other six are read against an
  implicit zero that does not exist.
- **`stress` is the only `full`-sample task, and its original backtest is a different one.** Tasks 1
  to 7 share one IS original; `stress` has its own, with roughly 50% more trades (763 → 1,132 on
  `1.19.29`). They are not comparable like for like, which is why only `stress` carries production
  thresholds.
- **`SCOPE` says "full", which does not mean out-of-sample trades exist.** The SQX toggle widens the
  retest to whatever split the strategy carries, and an IS-only strategy has none. Verify the
  out-of-sample trade count before reading any "full" result as a production estimate. On this
  battery it is genuinely populated: 304 to 627 trades.
- **`config.yaml` lives one level up, in the module root**, because the manual names it by that path.
  `config.FILE` resolves it with `parents[1]`; moving either breaks the other.
