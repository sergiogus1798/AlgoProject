---
q: What breaks after a mass `ruff format`, and what do pyright stubs reject that looks like valid code?
kw: ruff format markdown code blocks CODESTYLE.md, extend-exclude *.md, pyright ignore moved after format, reportArgumentType Series.map dict, reportCallIssue objectName PySide6, 65 new pyright errors
tag: 🔬  date: 2026-10-14  see: eng/checker-blind-spots
---
# `ruff format` reformats Markdown code blocks and strands `# pyright: ignore` comments
- ruff 0.16 formats Python blocks inside `.md` (it rewrote CODESTYLE.md's `atr` example, a SKILL.md, a README). `ruff.toml` has `"*.md"` in `extend-exclude`.
- Splitting a long line moves the expression off a trailing `# pyright: ignore[...]`: 65 new pyright errors after formatting 1,527 files. Fix: move the comment to the reported line (copy it when one statement became several). **After any format run, rerun pyright.**
- pandas stubs reject a dict mapper in `Series.map`: keep `.map(d)` with `# pyright: ignore[reportArgumentType]`; `.map(lambda k: d.get(k))` returns None instead of NaN.
- PySide6 stubs reject property kwargs (`objectName=`): `# pyright: ignore[reportCallIssue]`.

## Evidence
Encargo 68 F18 (`fa2e64f`, `4d31f07`), 2026-10-14: `ruff format .` then `pyright`; `git show 4d31f07 --stat | tail -1`.
