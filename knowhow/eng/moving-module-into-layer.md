---
q: refactor move module into layer package inputs mechanics model simulate verdict render, Path(__file__).with_name config not found, private name import collision shadowing local, layer violation, verify refactor no batch command, git show HEAD compare output
tag: 🔬  date: 2026-09-19  see: eng/practices-that-bit, eng/checker-blind-spots
---
# Moving a module into layers: three breakages `checks.py` and an import loop don't catch
1. `Path(__file__).with_name("x.yaml")` follows the `.py`: after moving one level down use `Path(__file__).parents[1] / "x.yaml"`, with a comment why (fails at run time).
2. A private name imported elsewhere is an undeclared public API; before renaming, grep local assignments of the candidate name (a shadowing local fails at render time).
3. A layer violation is usually a function in the wrong layer: move it; declare in the README table only the arrows that are real.
Verify: structure-diff every rendered output with digits normalised to `#` (numbers move, no seed), a stopwatch (catches module paths in strings), and `git show HEAD:<path>` output compared char-for-char.

## Evidence
`studies/transfer/crossmarket/` → `inputs/ mechanics/ model/ simulate/ verdict/ render/` (second after `portfolio/common/monteCarlo/`).
- Three configs stay in the module root because `docs/manual/05-retest-mercados.md` names them by path.
- `render/charts.py` exported `_x`, `_ticks` to two modules: `_x` → `xpos` fine; `ticks` already a local (rendered markup) in `charts.cone()` and `overlays.py` → named `tickvals`. In monteCarlo the trap was `line`.
- Two `simulate/ → verdict/` arrows: `fingerprint → significance` used only `trade_returns()` (`realised(...) − cost`, a measurement) → moved to `mechanics/pricing.py`,
  leaving dead imports (`pricing`, `pandas`) in `significance.py`; `verdict/` now imports nothing outside `model/`. `exposure → fieller` is real → declared (as monteCarlo declares `simulate/ → verdict/confidence`). monteCarlo's case: two vocabulary constants that were configuration.
- No batch command (only a Flask panel): baseline over its HTTP API — routes/params from `@APP.get`/`@APP.post`, one strategy with sim counts cut via `--set`,
  11 tabs + every `market × model × metric × window` view = 214; 214/214 identical. Stopwatch 5 repeats: median 10.12 s → 10.10 s.
- `render/svg.py` vs old `charts.py` from git: both figures at three widths + every constant and primitive, 0 differences (~30 lines of test).
