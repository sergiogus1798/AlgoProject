---
q: edit SQX XML project.cfx by str.index, silence conditions, Project does not exist after sync, broken XML, rewrite YAML section lost other session's blocks, git diff shows no deletions, recover lost assets block
tag: 🔬  date: 2026-09-24  see: eng/editing-asset-yaml
---
# Never cut a shared XML/YAML file by `str.index()`; edit only your section
Edit with a bounded `re.sub` or `replace(old, new, 1)` behind an `assert` on the anchor, or with the existing
function (`sqx/projects/crosschecks.silence()`, `builder.py --silence Retest`); never rebuild the whole file.
Validate SQX XML with `ElementTree.fromstring` before writing the `.cfx`. To check you destroyed nothing, compare
with what was on disk, not with HEAD. 🤔 `cp` the file to scratchpad before rewriting a shared file.

## Evidence
- 📓 XML: `i, j = t.index('<Conditions>'), t.index('</Conditions>') + 13`; first condition was
  `<Conditions CrossCheck="RetestOnAdditionalMarkets">`, so `i > j` and `t[:i] + block + t[j:]` deleted everything between.
- 🔬 Result: `Retest-Task3.xml` without `</Settings>`; SQX answered `Project 'TestXAUUSD2' does not exist` on every sync (on disk, unloadable). Broken XML doesn't announce itself.
- 🔬 YAML: `head = s[:s.index("# ─── MC Retest ")]; p.write_text(head + new)` on `assets/_build.yaml` dropped `spp:` and `wfm:`
  blocks another session had just appended → `KeyError` on `doctrine()["spp"]` in `sqx/projects/spp.py:114`, `wfm.py:112`.
- ⚠️ `git diff --stat` said 133 insertions, 0 deletions: uncommitted blocks don't exist for git. Shared files live half in the worktree.
- Recovery: the module's manual page is a second copy of its config (hard rule 8). Lost values were in `docs/manual/09-optimizacion.pdf (cap. 34-wfm):40-46`
  and `33-spp.md:38,91-93`; only `period`, `optimization`, `max_steps`, `threshold_pct` missing → take from the frozen donor's task.
  Read the consuming module's page before declaring an `assets/` block lost.
