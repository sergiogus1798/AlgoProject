---
q: How do I import a CSV of bars as a new symbol headless, and what does it cost?
kw: -data action=import, Missing parameter 'format', format=MT4, -symbol action=add datasource=file, synthetic series, custom data import, import is asynchronous, imported feed timezone UTC
tag: 🔬  date: 2026-10-10  see: sqx-drive/renaming-feeds, costs/refreshing-sqx-costs
---
# Two verbs, no GUI: `-symbol action=add … datasource=file`, then `-data action=import … format=MT4`
- `-symbol action=add symbols=X datasource=file instrument=I datatype=M1 timeframe=M1 broker=[[FTMO]]` creates an empty feed named exactly `X` (no `_M1` postfix added).
- `-data action=import symbol=X instrument=I timeframe=M1 format=MT4 filepath=/abs.csv` — `format` is required despite the help calling it optional («Missing parameter 'format'»). CSV: `yyyy.MM.dd,HH:mm,O,H,L,C,V`, no header.
- The call returns at once; the import runs behind it. Done = the `-symbol action=list` row of `X` shows `M1` and its record count. 4.06 M M1 bars (221 MB CSV → 95 MB `.dat`): 14.5 s on the conductor.
- ⚠️ The feed lands in UTC, not in the instrument's broker zone (USA500_M1 is EST+07); `timezone=` on import untested.
- Reusing the real instrument (`instrument=USA500_ftmo`) gives the same point value, tick and default spread with nothing to clone.
- Done on a worker: the `.dat` is written into the master's `History/` (symlink) but the registry row lives only in that worker's `data.db` — the other worker does not see it, and it is lost when the master's `data.db` is copied over again.
- A project pointed at it: copy a `project.cfx` (a zip) replacing the feed name in every member, worker stopped; 0.06 s.

## Evidence
2026-10-10, conductor, `USA500_SYN01` from `AlgoData/scratch/synthetic/USA500_SYN01_M1.csv`, project `Test_USA500_SYN01_H1_carga` listed and answering `status`; no task started.
