# CODESTYLE — Python rules for this project

Read this before writing or changing any Python here. These rules override any default habit.
`python3 tools/checks.py` verifies the mechanical ones; the auditor runs it daily.

---

## 1. Short files

**500 lines maximum.** If the job does not fit, split it into modules inside a folder with a name of
its own — never one giant file. A file approaching 500 lines is usually two concerns wearing one name.

## 2. Every code folder has a README

Each folder containing `.py` files carries a `README.md` with one table:

| file | what it does | run it | in → out |
|---|---|---|---|

Every `.py` also opens with a **one-line module docstring**. A future session reads a twenty-line
README instead of opening five files. `checks.py` fails if a `.py` is missing from its folder's table.

## 3. Google-style docstrings and type hints

Types live in the signature and are never repeated in prose. The docstring gives one line of what,
then `Args:` with format and units where they are not obvious, then `Returns:`.

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

Add at most one short sentence when the logic is mathematical or has a trap. No equations, no worked
examples. **Do not comment line by line.** Comment only what the code cannot say: a unit conversion,
a non-obvious convention, a trap in the source data.

## 4. Minimalism

- Write the smallest thing that answers the question. If a job fits in 30 lines, it is 30 lines.
- **No defensive code.** No `try/except` around things that will not fail, no `if x is None` guards,
  no fallbacks for inputs nobody said would occur. If the data is malformed, let it crash — a
  traceback tells the owner more than a silent skip. **The one exception is the boundary with a
  person** — the window and its daemon (`ui/`). There a daemon that is down, a field the owner typed
  wrong or a value that is not a number is caught and shown, because one bad input must not take
  the app down. The analysis the window calls still crashes as above.
- **Check at the door, then trust.** "Let it crash" only works when it crashes, and bad market data
  usually does not: it becomes a NaN that propagates or a join that misaligns. So where data enters
  from outside — a reader of `.sqx`, `.cfx`, CSV or parquet, MT5, a scraped page — one `assert` on
  shape and range goes right after the read, with a message that names the file. Past that line the
  code trusts what it holds and carries no further guards.
- **An error raised on purpose says what happened and what to run next** — "databank X has no OOS
  export: run `/export` on it" — never a bare `KeyError` the owner has to decode.
- **No edge cases that were not asked for.** Not the missing column, not the second date format.
  An empty population is not one of them: zero survivors after a filter is a normal outcome here,
  and a module that receives none says so instead of returning NaN.
- **No configurability nobody requested.** No flags "for flexibility", no options with defaults nobody
  will change. Hard-code what is fixed; parameterise only what actually varies.
- **No premature abstraction.** Two similar lines are fine. Do not build a helper, a class or a
  registry to avoid repeating yourself twice. Rule 5 is the exception, and only the exception: a
  registry earns its place when the thing it holds is a **choice the study has to expose**, never
  when it only saves typing.
- Plain function over class. Comprehension over loop while it stays readable.
  Logic is a function that takes data and returns data, never an object that keeps state and changes
  it through methods — and it does no reading or writing of its own: the caller (`main()`) loads,
  calls and saves, which is what keeps a known-answer test three lines long.
- **A record that crosses a module boundary declares its keys.** Inside one module a plain dict is
  fine. What another module receives is a `TypedDict` or a `@dataclass(frozen=True)` — still data
  without methods — because `-> dict` tells the reader nothing and a mistyped key is found only at
  run time. A mapping whose keys come from the data says its types: `dict[str, float]`, never a
  bare `dict`. **A class is written only when a library demands one** — a Qt widget or dialog
  is a subclass, a FastAPI request body is a pydantic `BaseModel` — and it holds the wiring that
  library asks for, not the logic, which stays in functions.
- Order within a file: constants, then helpers, then callers, then `main()`, then the
  `if __name__ == "__main__":` line.
- Names say what the thing is, not how it works: `stop_rate`, not `calc_stop_rate_helper`.

## 5. An analysis is built from modules with one job each

Analysis and tooling are split into **named modules with a stated boundary**, not into one file that
does the study end to end. Each module answers a question a future session can name without opening
it, and the boundaries are chosen so that a module can be replaced without touching its neighbours.

The four boundaries that keep an analysis honest, in the order the data flows:

| the module holds | it must not hold |
|---|---|
| **configuration** — what the study is run on | anything computed |
| **modelling** — the assumptions, and the alternatives to them | the execution, or the conclusions |
| **execution** — producing the numbers under a given model | choosing the model, or judging the output |
| **inference** — the statistics and the decision | producing the numbers it judges |

Why this and not one file: the modelling and the inference are where a study can be wrong in ways
that do not crash. Keeping them apart means a modelling assumption can be swapped and the result
recomputed under both, which is the only way to find out whether a conclusion depended on it. A file
that draws its own trades and computes its own p-value cannot be cross-examined.

Rules for a module in this shape:

- **One name, one job, said in the module docstring.** If the docstring needs "and", it is two.
- **State the contract.** Where several implementations of one job exist — several ways to model the
  same thing — they share one signature, are collected in one registry in that module, and the
  registry's table says what each holds fixed and what it randomises. Adding a fifth is then adding a
  function and one row, and nothing else changes.
- **Dependencies point one way**, along the table above. Inference never imports execution.
- **Packages layer too** (`tools/layering.py`, run by `checks.py`): `core` imports no other package, `engines` only
  `core` and `ledger`, `sqx` only `core`; only `tests` and `tools` import `ui`, only `tests` imports `tools`. Old violations sit in its ALLOW list as debt to shrink.
- **A module is replaceable.** If swapping it means editing three other files, the boundary is wrong.
- **Extension over modification.** New capability arrives as a new entry, not as a flag threaded
  through the existing ones.

This applies to analysis and tooling. It does not license spreading a thirty-line job over four files:
rule 1 still decides when to split, and rule 4 still decides how much to build.

## 6. It must run on another machine

- Every third-party import appears in `requirements.txt` with a pinned version.
- **No absolute path outside `core/paths.py`.** Machine-specific values — where SQX lives, worker
  ports, where the data goes — live in `config/machine.yaml`, which is not in git.
  `config/machine.example.yaml` is the versioned template.
- Paths are `pathlib.Path`, never strings joined with `/`.
- On a fresh machine: copy the example to `config/machine.yaml`, edit it, `pip install -r
  requirements.txt`, done.

## 7. The dependency map is generated

`python3 tools/depmap.py` reads the real imports and rewrites `docs/DEPENDENCIES.md`: the folder tree,
who imports whom, and the external libraries each area uses. **Regenerate it after touching code;
never edit it by hand.** A hand-maintained map is wrong within two weeks.

## 8. Check before you hand work over

```bash
python3 tools/depmap.py && python3 tools/checks.py && python3 tools/audit_tests.py --changed
```

`--changed` runs the tests you touched plus every `tests/test_*.py` that imports, directly or
transitively, a `.py` that `git status` shows changed; the whole suite still runs nightly.

The lint config is `ruff.toml` (real bugs only, no formatter); `ruff check .` must be clean for its selected rules — `checks.py` runs it as its "lint" check.

`checks.py` reports: files over 500 lines, `.py` missing from its folder README, missing module
docstrings, functions without a docstring or without type hints, absolute paths outside
`core/paths.py`, imports missing from `requirements.txt`, and a stale `DEPENDENCIES.md`. It blocks
nothing while you work — it just has to be green before the work is done.

`checks.py` also runs the ratchet (`tools/ratchet.py`): public functions annotated bare `-> dict` (per package), broad `except`,
unseeded `default_rng()`, legacy `np.random.*`, the size of `layering.ALLOW` and ruff's B905/C901/PLR0913 may not rise above
`tools/ratchet.json`. When a count falls the check rewrites that file by itself; commit it with the change.

## 9. Measure what you change

The load here is thousands of strategies times hundreds of thousands of simulations, on a machine
whose RAM is already split between three SQX installs. A module that grows in memory does not get
slow — it dies halfway through a run. So speed and memory are part of the work, not an extra:

- **A change to analysis code is measured before and after**, with
  `python3 -m perf.catalogue --only <target>`, and the two numbers go in the commit message. The
  history under the data root only grows, so the next session can see what the change cost.
- **A new module that reads a population or runs simulations gets a target** in
  `perf/inputs/targets.py`, in the same task. What is not in the catalogue is never measured again.
- **Budgets are in bytes, not in simulations.** "Keep it under 4 GB" survives a bigger export;
  "at most 10,000 draws" does not say whether it fits.
- **Speed does not suspend the other rules.** A faster module that is longer, more configurable or
  harder to read than rule 4 allows is not an improvement.

→ `perf/README.md`, `docs/manual/03-datos-costes-y-registro.pdf` (cap. 12-rendimiento), and the `/perf` skill.

## 10. Review

The owner reviews the plan and the diff, not every line. Show the plan before writing a non-trivial
script (§12); everything is written on `master` and left uncommitted, and the owner reads the diff
before he commits it (`CLAUDE.md` rule 12). Do not run anything destructive without asking — a skill the owner
invokes that deletes by design (`curate`, `oos-gate`) is the asking. **If a rule here would make the code wrong, say so and explain why** — do
not silently break it, and do not silently write bad code to obey it.

## 11. Randomness is seeded

Every random draw comes from `np.random.default_rng(seed)` — never `default_rng()` bare, never the
legacy `np.random.*` functions. The seed is an argument of the function that draws, and it is saved
with the result it produced. A Monte Carlo or a null that cannot be rerun to the same number cannot
be checked, and a difference between two runs cannot be told from a bug.

## 12. How a change is made

1. **Plan first when it is big.** More than 3 files, or a new module: five lines before any code —
   what, which files, what is deleted, what is reused, and the command that will prove it works.
2. **Look before you write.** `graphify query` or a grep for a helper that already does it.
   Re-implementing what lives three folders away is the commonest way this codebase grows.
3. **A bug arrives with its test.** First the test that fails, seen failing; then the fix, seen
   passing. A test that was never red proves nothing — so a new known-answer test is also seen red
   once: break the function for a moment and it must fail.
4. **Stay inside the task.** The diff touches what the task named. What you notice on the way goes
   to `OPEN.md`, not into the diff.
5. **"Done" carries its evidence**: the command that was run and the tail of its output. Never
   "this should work". A new command is also run once for real, on a small real input, not only
   through its test. And read your own `git diff` before reporting: a debugging `print`, a leftover
   or a file that was not the task's is found there.
6. **An independent review before the commit question**, for any change beyond a one-file fix.
   Spawn a `general-purpose` subagent, `model: "sonnet"` (Opus, said in the brief, when the diff
   touches inference or statistics), and give it three things only: `git diff -- <the task's files>`,
   this file, and the task's goal in one line. **Never your reasoning or your summary** — a reviewer
   handed the author's account returns it confirmed. It answers with findings as `file:line`; fix
   or rebut each one, and tell the owner the ones left standing.
7. **Three tries, then a report.** The same failure three times: stop and say what was tried. Green
   is never reached by weakening the test, loosening a threshold or catching the error.
8. **A refactor is proved by difference.** Before the old code is deleted (`CLAUDE.md` rule 21), old
   and new are run on the same real input and their outputs compared; the comparison is the evidence.
9. **A mistake made twice becomes a check.** What the review or the owner catches a second time is
   added to `tools/checks.py`, so the third time is caught by a machine.

## 13. Significant work is orchestrated

A change that creates a module, touches more than 3 files or changes a contract between packages is
planned by one capable agent and written by cheaper ones (`CLAUDE.md` rule 17). Below that size one
session does it directly: writing the briefs would cost more than the change.

- **The orchestrator (Opus) reads, decides and splits — it writes no code.** It also keeps out of
  the executors' output: it receives file lists and command tails, never diffs or whole files, or
  the work is paid for twice.
- **Each piece is a brief with five things**: the goal in one sentence; the closed list of files it
  may touch; the existing code it must reuse; the acceptance command; and the line "if the plan
  looks wrong, stop and say so — do not improvise".
- **Executors run on Sonnet**, Haiku when the piece is purely mechanical. A piece of design,
  statistics or template authoring is not handed down. Each returns the files it changed and the
  tail of its acceptance command, nothing else.
- **Parallel only on disjoint files.** There is one folder and no worktree: two pieces that share a
  file run one after the other.
- **The orchestrator closes the loop itself**: it runs every acceptance command and `checks.py` —
  an executor's "done" reads the same whether it is right or wrong — and then the review of §12.6
  reads the whole diff.

## Tests

Not a suite, and no framework: each test is a plain script in `tests/`, listed in its README. Two
kinds, and only where a silent break would go unnoticed for weeks:

- **Golden files** for the readers and writers everything else is built on — the `.sqx`, `.cfx` and
  retest parsers, the variant writer, the strategy translator: a stored input and its expected
  output. A parser that breaks silently poisons every analysis downstream.
- **Known-answer tests** for the inference — the nulls, the surfaces, CSCV, the ledger, the trade
  statistics: synthetic data built so the answer is known by construction (pure noise must read a
  PBO of 0.5, a shuffled surface must read no plateau). A statistic that is wrong does not crash;
  this is the only way to catch it.
