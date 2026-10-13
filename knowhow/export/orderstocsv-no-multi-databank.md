---
q: Can one orderstocsv launch export several databanks, and what does `file=A file=B` do?
kw: orderstocsv file=A file=B only last exported, File 'A;B' doesn't exist, parent folder not recursive, one JVM several banks, 14 s per launch, single-JVM export 7.4a, silent export loss
tag: 🔬  date: 2026-10-13  see: orderstocsv-slow-is-datamanager
---
# orderstocsv has no multi-databank syntax: `file=A file=B` silently exports only B
Trap: repeating `file=` returns rc 0 and writes only the LAST databank's CSVs. `file="A;B"` fails (rc 1,
«File 'A;B' doesn't exist»); a parent folder of both fails too (not recursive). Each launch costs
~14.4 s (30 strategies, nearly all JVM start). One JVM for several banks is only possible by staging
every `.sqx` into ONE flat folder, and `Results` and `OOS` hold the same strategy names, so files and
CSVs collide: staging needs a rename per bank. Never use `file=A file=B`. Saves ~14 s per extra bank at best.

## Evidence
- 🔬 conductor, 2026-10-13, encargo 66 live session 1: `sqx-worker.sh run -tools action=orderstocsv file=… output=… data=main`;
  one bank 14.3-14.6 s; the three multi-bank forms above. Replaced in the live route by AlgoBank (`perf/algobank-vs-algotrades-vs-orderstocsv.md`).
