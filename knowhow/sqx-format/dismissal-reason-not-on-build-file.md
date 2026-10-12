---
q: Can the harvest read why SQX dismissed a strategy that has no OOS twin from the build file?
kw: StrategyProblems bitmask 0, missing_oos.csv, unexplained missing twin, AutomaticDismissal, dismissed strategy reason, harvest warning
tag: 🔬  date: 2026-10-11  see: sqx-format/names-reused-between-builds, sqx-format/strategy-identity
---
# The reason SQX dismissed a strategy is on the retested file, not the build file
Trap: reading `StrategyProblems` of the build-file copy to explain a missing OOS twin. It is 0 for
every such strategy; the reason lives on the retested file, which is the one gone.
`missing_oos.csv` has the column and the harvest prints a warning in capitals; a stop on «unexplained
missing twin» is NOT enabled. To enable it, read the reason from SQX before dismissal: the Retest
task's `AutomaticDismissal` (10 codes, inherited from the donor). Decision pending: `OPEN.md` #115.

## Evidence
🔬 2026-10-11: `Test_NIKKEI225_M30_simpleL_fin`, `_val`, `Test_USDJPY_M30_doubleROCLong`; 300 strategies
sampled in each among those missing their OOS twin, `StrategyProblems` = 0 in all.
