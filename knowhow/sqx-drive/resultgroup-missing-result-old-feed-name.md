---
q: What is «ResultGroup doesn't contain result with key 'Main: USDCAD_DukasM1_the5ers/H1'» in SQX's log?
kw: ResultGroup doesn't contain result with key, SQ4LoaderPlugin Cannot find result, ResultsMap.get, DukasM1_the5ers, old feed name, loadSQ4File
tag: 🔬  date: 2026-10-10  see: sqx-drive/unresolved-resources-exact-xml
---
# It is SQX loading an old `.sqx` whose stored result names a feed renamed on 2026-10-01
`SQ4LoaderPlugin.loadResultsData` (stack: `FileHandler.loadFile` → `ResultsGroup.subResult`) logs it as ERROR
«Cannot find result» when a strategy file carries a result keyed by a pre-rename feed (`USDCAD_DukasM1_the5ers`,
now `USDCAD_M1`: `assets/_feed_renames.yaml`). It is raised while a databank/file loads, not by a task's
config: 22 times on 2026-10-09 and 3 on 10-08 in `SQX_w2` log, around loads of other projects' databanks.
It is not what stopped `Test_NIKKEI225_H1_aroonL_mc1` (that failed at step 13: `sqx.projects.wfc: None no esta
en project.cfx`, `fallo.md` merely quotes the log's tail). Noise unless the load then yields no strategy.

## Evidence
- 🔬 `SQX_w2/user/log/StrategyQuant/log_2026_10_09.log:7297` (and 7360, 7380); `grep -c` 22 / 3 / 0 for 10-09 / 08 / 07.
- 🤔 Which file carries the old key was not traced (it needs opening archived `.sqx` files).
