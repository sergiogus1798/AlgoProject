---
q: Is there any file that maps a live EA magic number to its strategy?
kw: magic number of a live EA; which strategy is magic 3; register magic to strategy; MagicNumber of SQX exported EA; weeklyReconciler register.csv; split account deals per strategy
tag: 📓  date: 2026-10-02  see: mt5/reconcile-mae-both-sides-rebuilt
---
# Live EAs carry magics 1…7; new combinations get 1001+ from `mt5.fleet.magics`, which can write the register
- The repo holds no magic → strategy table; `mt5/verify/config.yaml` `sqx.magic: 1` only seeds a verification's export.
- `AlgoData/mt5/eas/{FTMO,Hantec}/*.mq5` carry `input int MagicNumber`, the same in both firms and in News/NoNews:
  3.29.126 → 1, 2.13.148 → 2, 3.23.151 → 3, 9.5.175 → 4, 13.43.66 → 5, 3.48.75 → 6, 4.30.173 → 7. A source default:
  an input changed on the live server's chart is not visible here.
- `mt5.reconcile.register.read()` derives its register (`magic,strategy,identity,sqx,firm,since`) from the fleet's
  `magics.csv` + workbook (no `register.csv` any more), refuses in Spanish without them, and takes a position's magic from its ENTRY deal (an exit the server fills carries 0).

## Evidence
- 📓 2026-10-02: `grep -rn -i magic mt5/` → the config key and its README row only (`mt5/newsfilter/` copies the EA's
  own `MagicNumber`, assigns none); `grep -H 'input int MagicNumber' AlgoData/mt5/eas/*/*.mq5` → the seven values, 28 files.
- 🤔 The exit-deal magic of 0 is MetaTrader's documented behaviour, not yet seen on this account: the first real
  `history` read confirms it.
- 📓 Owner, 2026-10-14: the seven live EAs keep 1…7 (`magics --adopt`); new strategy x asset x timeframe combinations
  start at 1001 in `AlgoData/fleet/magics.csv`, never reused (retired ones stay), and the reconciler derives its register
  from it (2026-10-15; only combinations whose identity and .sqx were recorded).
