---
q: where is the .sqx of a finished workflow project; databank folder empty on the install; loader.find finds nothing; raw strategies copy same identity; strategymeta backtest empty; metadata of a strategy without SQX
tag: 🔬  date: 2026-09-28  see: identity-differs-across-databanks
---
# A finished project's .sqx is often only in `raw/…/strategies/`, and E2's reader needs it under the databank's name
`Test_USDJPY_donchianUpperCrossUp_M30` keeps `project.cfx` on the custodian but an **empty
`databanks/`**, so `loader.find` finds no file. The `Results` strategy survives as the copy the
SPP export left in `AlgoData/raw/<P>/SPP_IS/<day>/strategies/` — **same identity** as in Results
(`4d679e0c…`), but its `lastSettings` is the SPP IS task, not the build. Look there (then the
archive) by hashing each file; say which copy you read. `sqx.inspect.strategymeta.read` matches the
project's tasks by the `.sqx`'s **folder name**: read in `strategies/`, `backtest` lists no task, so
copy it to a temporary folder named as the databank first (`ui/daemon/strategy/meta.py`).

## Evidence
`find.install_of(P, "Results")` → None; `ls SQX_w2/user/projects/<P>/databanks/` → empty.
`sqxfile.identity(raw/<P>/SPP_IS/2026-09-27/strategies/Strategy 10.11.79.sqx)` = `4d679e0c…`,
the identity of Results' row in the cosecha; `read()` of that file: `last_test.output = "SPP IS"`;
the same file under `<tmp>/Results/`: `backtest[0].task = "Build strategies 2"`.
