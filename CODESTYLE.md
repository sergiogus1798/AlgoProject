# CODESTYLE — how Python is written in this project

This file says what the code must look like. How a change is planned, checked, reviewed and handed
over is in `CONTRIBUTING.md`. The hard rules of `CLAUDE.md` take precedence over both.

**MUST** and **MUST NOT** are rules; `tools/checks.py` verifies the mechanical ones (§12) and the
reviewer the rest. **SHOULD** is the default, and a departure is explained in the diff. If a rule here
would make the code wrong, say so and why — never break it silently, and never write bad code to obey it.

---

## 1. Files and folders

- A file MUST NOT exceed **500 lines**. A job that does not fit becomes a folder of modules with a
  name of its own; a file nearing the limit is usually two concerns under one name.
- Every `.py` MUST open with a **one-line module docstring** saying what it is.
- Every folder holding `.py` files MUST carry a `README.md` with one table — file · what it does ·
  run it · in → out. The first two columns are generated from the module docstrings by
  `tools/readmetable.py`; edit the docstring, never the cell.

## 2. Package layering

Imports point one way. `core` imports no other package; `engines` only `core` and `ledger`; `sqx` only
`core`; only `tests` and `tools` import `ui`; only `tests` imports `tools`. `tools/layering.py`
enforces it, and its `ALLOW` list is debt that may only shrink.

## 3. Functions and data

- Logic MUST be a **function that takes data and returns data**. It reads and writes nothing itself:
  `main()` loads, calls and saves. This is what keeps a known-answer test three lines long.
- A **class** MUST NOT be written unless a library demands one — a Qt widget, a pydantic request body —
  and then it holds that library's wiring, never the logic.
- A record that **crosses a module boundary** MUST declare its keys: a `TypedDict` or a
  `@dataclass(frozen=True)`, never `-> dict`. A mapping keyed by data states its types
  (`dict[str, float]`). Inside one module a plain dict is fine.
- A function MUST NOT return `Optional` for a value that cannot be missing. Where it can be missing,
  raise at the source rather than make every caller test for `None`.
- A quantity whose **unit** is not obvious — points vs price, fraction vs percent, bars vs minutes,
  account currency vs return — MUST name it, in the identifier or in the `Args:` line.
- Names say what a thing is (`stop_rate`), not how it is computed (`calc_stop_rate_helper`).
- File order: constants, helpers, callers, `main()`, `if __name__ == "__main__":`.

## 4. Docstrings and types

Every function carries type hints and a docstring (Google style). Types live in the signature and are
never repeated in prose. A private helper's docstring MAY be one line; a public function adds `Args:`
where a format or unit is not obvious, and `Returns:`.

```python
def atr(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int) -> np.ndarray:
    """Wilder-smoothed Average True Range.

    Args:
        high, low, close: Price per bar, same length.
        period: Lookback in bars.

    Returns:
        Same length as the inputs; the first period-1 entries are NaN.
    """
```

One more sentence is allowed where the mathematics has a trap. No line-by-line comments: a comment
says only what the code cannot — a unit conversion, a convention, a quirk of the source data.

## 5. Errors

- **Validate at the door, then trust.** Where data enters from outside — a `.sqx`, `.cfx`, CSV or
  parquet reader, MT5, a scraped page — its shape and range MUST be checked right after the read with
  an explicit `raise ValueError(...)` naming the file. Not `assert`: `python -O` strips it. Past that
  line the code carries no further guards. Bad market data rarely crashes on its own: it becomes a NaN
  that propagates or a join that misaligns, and this check is what catches it.
- **Otherwise, let it crash.** No `try/except` around what will not fail, no fallback for an input
  nobody said would occur. A traceback tells more than a silent skip.
- **A deliberate error says what happened and what to run next** — "databank X has no OOS export: run
  `/export` on it" — never a bare `KeyError`.
- **A bare or broad `except` MUST NOT be written**, with two exceptions:
  1. the boundary with a person — the window and its daemon (`ui/`), where a bad field or a daemon that
     is down is shown, not fatal; the analysis behind it still crashes;
  2. cleanup of an external effect. Code that starts a worker, holds a lock or writes into the data
     root, SQX or MT5 MUST leave them consistent when it fails: `try/finally`, or write to a temporary
     file and rename it. A half-written file there destroys work (`CLAUDE.md` rules 1 and 4).
  3. record and re-raise: a handler that writes the exception where someone will read it — a
     campaign cell marked failed, a notice, a thread's result box — and then re-raises it unchanged
     (owner, 2026-10-14, D23). It hides nothing; a `finally` cannot see the exception.
- An empty population is a normal outcome. A module that receives zero strategies says so; it never
  returns NaN.

## 6. Minimalism

- The smallest thing that answers the question. A 30-line job is 30 lines.
- **Reuse before writing**: `graphify query` or a grep for what already exists. Then the standard
  library, then a dependency already installed. A new dependency for what a few lines can do MUST NOT
  be added.
- No configurability nobody asked for: hard-code what is fixed, parameterise what actually varies.
- No edge cases nobody asked for — not the missing column, not the second date format.
- No premature abstraction. Two similar lines are fine; a helper, class or registry built to avoid
  repeating something twice is not. §7 names the one place a registry is earned.
- Comprehension over loop while it stays readable; vectorised over a Python loop on arrays.
- **Replaced or unreached code is deleted in the same change**, with its citations — no shim, no
  commented-out block (`CLAUDE.md` rule 21). Git is the archive.

## 7. Shape of an analysis

An analysis is split into modules by the four jobs below, in the order the data flows — not into one
file that does the study end to end:

| the module holds | it must not hold |
|---|---|
| **configuration** — what the study runs on | anything computed |
| **modelling** — the assumptions, and the alternatives to them | the execution, or the conclusions |
| **execution** — the numbers under a given model | choosing the model, or judging the output |
| **inference** — the statistics and the decision | producing the numbers it judges |

Modelling and inference are where a study is wrong without crashing. Kept apart, an assumption can be
swapped and the result recomputed under both — the only way to learn whether a conclusion rests on
it. A file that draws its own trades and computes its own p-value cannot be cross-examined.

- One module, one job, said in its docstring; a docstring that needs "and" describes two modules.
- Inference never imports execution.
- Where a study **exposes a choice between models** — several nulls, several resamplers — they share
  one signature and sit in one registry whose table says what each holds fixed and what it randomises.
  A registry that only saves typing is §6's premature abstraction.
- This does not license spreading a thirty-line job over four files: §1 and §6 still decide.

## 8. Research integrity

These rules exist because a quantitative result can be wrong without any error being raised.

- **Randomness is seeded.** Every draw comes from `np.random.default_rng(seed)`; never `default_rng()`
  bare, never the legacy `np.random.*`. The seed is an argument of the drawing function and is saved
  with the result. A null that cannot be rerun to the same number cannot be checked.
- **No look-ahead.** A function that aligns signals, prices or trades states in its docstring which
  bar's information each output uses. Its known-answer test (§11) includes a case that a one-bar leak
  would fail.
- **Samples stay apart.** Code that reads a held-out sample (`oos`, `oos2`) names the sample in its
  arguments, never infers it. `oos2` is read only by the steps the workflow reserves it for.
- **Every search is counted.** Anything that looks at data and reduces a population — a screen, a
  threshold, a filter — records itself with `ledger.record.log`. The multiple-testing correction is
  owed to everything tried, not to what survived.
- **A saved result is reproducible**: next to it are the seed, the parameters and the inputs that
  produced it, so it can be recomputed without the session that made it.
- **NaN never travels silently.** A function that can produce NaN says when in `Returns:`; a NaN that
  reaches inference unannounced is a bug. Floats are compared with `np.isclose`, never `==`.
- **Time:** timestamps inside the code are on the feed's clock, EETUS, without tzinfo — bars, trades
  and SQX's own dates all arrive that way. A wall-clock time that is ever compared with them is
  converted once, where it is read.

## 9. Portability

- **No absolute path outside `core/paths.py`.** Machine-specific values live in `config/machine.yaml`
  (not in git; `config/machine.example.yaml` is its template).
- Paths are `pathlib.Path`, never strings joined with `/`.
- Direct dependencies are pinned in `requirements.txt`; `requirements.lock` pins the whole tree and is
  what gets installed. The Python floor lives in `pyproject.toml`.
- Output is `print`, unattended code included: a cron script's log is its redirected stdout. No
  `logging` configuration.

## 10. Performance

The load is thousands of strategies times hundreds of thousands of simulations, on RAM already split
between three SQX installs. A module that grows in memory does not get slow — it dies halfway through.

- Budgets are stated in **bytes**, not in simulations: "under 4 GB" survives a larger export.
- A module that reads a population or runs simulations has a target in `perf/inputs/targets.py`.
- Speed does not suspend the other rules: a faster module that breaks §6 is not an improvement.

How a change is measured: `CONTRIBUTING.md` §4.

## 11. Tests

Plain scripts in `tests/`, listed in its README — no framework. Three kinds:

- **Golden files** for the readers and writers everything is built on — the `.sqx`, `.cfx` and
  retest parsers, the variant writer, the strategy translator: a stored input and its expected
  output. A parser that breaks silently poisons every analysis downstream.
- **Known-answer tests** for inference — the nulls, the surfaces, CSCV, the ledger, the trade
  statistics: synthetic data whose answer is known by construction (pure noise reads a PBO of 0.5;
  a shuffled surface reads no plateau). A wrong statistic does not crash; this is the only way to
  catch it.
- **Regression tests**: a fixed bug ships with the test that reproduces it.

A test that was never seen failing proves nothing: break the code for a moment and watch it go red.

## 12. Enforcement

`python3 tools/checks.py` verifies file length, READMEs, docstrings and type hints, absolute paths,
requirements, layering, `ruff check` (bugs only, `ruff.toml`) and a stale `docs/DEPENDENCIES.md`.

Pyright (basic) runs over the packages in `pyproject.toml` `[tool.pyright] include`; a package joins
the list once it is clean.

Rules the code does not yet meet everywhere are held by the **ratchet** (`tools/ratchet.py`,
`tools/ratchet.json`): per-package pyright errors, bare `-> dict`, broad `except`, unseeded RNGs,
`layering.ALLOW` and ruff's B905, C901 and PLR0913. A count may fall and never rise; when it falls the
check rewrites the baseline. The ratchet records debt — it does not make the code compliant. The
target is zero for pyright errors, bare `-> dict`, broad `except`, unseeded RNGs and B905 (every `zip`
says `strict=`, the old ones reviewed file by file with their test); C901 and
PLR0913 are only frozen, and no function is rewritten to lower them.
