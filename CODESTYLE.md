# CODESTYLE — Python rules for this project

Read this before writing or changing any Python here. These rules override any default habit.
`python3 tools/checks.py` verifies the mechanical ones; the auditor runs it daily.

---

## 1. Short files

**250 lines maximum.** If the job does not fit, split it into modules inside a folder with a name of
its own — never one giant file. A file approaching 250 lines is usually two concerns wearing one name.

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
  traceback tells the owner more than a silent skip.
- **No edge cases that were not asked for.** Not the empty list, not the missing column, not the
  second date format.
- **No configurability nobody requested.** No flags "for flexibility", no options with defaults nobody
  will change. Hard-code what is fixed; parameterise only what actually varies.
- **No premature abstraction.** Two similar lines are fine. Do not build a helper, a class or a
  registry to avoid repeating yourself twice.
- Plain function over class. Dict over dataclass. Comprehension over loop while it stays readable.
- Order within a file: constants, then helpers, then callers, then `main()`, then the
  `if __name__ == "__main__":` line.
- Names say what the thing is, not how it works: `stop_rate`, not `calc_stop_rate_helper`.

## 5. It must run on another machine

- Every third-party import appears in `requirements.txt` with a pinned version.
- **No absolute path outside `core/paths.py`.** Machine-specific values — where SQX lives, worker
  ports, where the data goes — live in `config/machine.yaml`, which is not in git.
  `config/machine.example.yaml` is the versioned template.
- Paths are `pathlib.Path`, never strings joined with `/`.
- On a fresh machine: copy the example to `config/machine.yaml`, edit it, `pip install -r
  requirements.txt`, done.

## 6. The dependency map is generated

`python3 tools/depmap.py` reads the real imports and rewrites `docs/DEPENDENCIES.md`: the folder tree,
who imports whom, and the external libraries each area uses. **Regenerate it after touching code;
never edit it by hand.** A hand-maintained map is wrong within two weeks.

## 7. Check before you hand work over

```bash
python3 tools/depmap.py && python3 tools/checks.py
```

`checks.py` reports: files over 250 lines, `.py` missing from its folder README, missing module
docstrings, functions without a docstring or without type hints, absolute paths outside
`core/paths.py`, imports missing from `requirements.txt`, and a stale `DEPENDENCIES.md`. It blocks
nothing while you work — it just has to be green before the work is done.

## 8. Review

The owner reads every line. Show the plan before writing a non-trivial script. Do not run anything
destructive without asking. **If a rule here would make the code wrong, say so and explain why** — do
not silently break it, and do not silently write bad code to obey it.

## Tests

Not a suite. Golden-file tests only, in `tests/`, for the `.sqx` and `.cfx` parsers and the strategy
translator: a stored input and its expected output. A parser that breaks silently poisons every
analysis downstream and nobody notices for weeks.
