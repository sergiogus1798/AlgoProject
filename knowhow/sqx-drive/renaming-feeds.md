---
q: rename SQX symbol feed, symbol action=edit name=, change feed timezone, timezone baked into .dat, old projects old feed names, XAUUSD_DukasM1_Infinox to XAUUSD_M1, feed renames table, delete symbol
tag: 🔬  date: 2026-10-01  see: export/feed-clock-timezones, sqx-format/tick-file-format, databanks/sync-deletes-unloaded-files
---
# `-symbol action=edit symbol=OLD name=NEW` renames everywhere; the timezone it silently ignores
- One call renames the registry row, the `History/` folder and the file (`NEW/NEW_M1.dat`, `NEW_TICK_TICK.dat`). M1: instant; a tick feed ~1 min (SQX rescans it). Master only, sqcli headless, GUI closed.
- `timezone=` on `edit` answers "Data updated" and changes nothing: the zone is baked into the `.dat` at download and comes from the `broker=` of `-symbol action=add` (`BROKER.MT_TIMEZONE`; `[[FTMO]]` → EETUS). A zone change = a re-download.
- ⚠️ `edit instrument=X` on a feed holding data refuses an instrument whose broker zone differs («Cannot update…»). On an empty feed it is accepted but **moves the data broker to X's**: a no-broker X downloads in UTC. Use an instrument under the same broker: `-instrument action=add … broker=[[FTMO]]` names it `X_ftmo`. `add instrument=` and `-instrument edit broker=` are ignored.
- Never delete the old feed before the new one holds its name: move it aside (`name=F_OLD`), rename, then delete.
- Projects and `.sqx` keep the old name and stop resolving it. `assets/_feed_renames.yaml` lists old → new; `core.symbols.current()` translates XML from before. The builder applies it to the donor and the borrowed project.
- `-symbol action=delete symbols=A,B` also removes their `History/` folders.
- Workers copy `data.db` from the master only when its fingerprint moved; `History/` is a symlink to the master's, so a rename reaches them at once.

## Evidence
2026-10-01, master headless (`SQX/sqcli`, port 5050): `USDSGD_DukasM1_darwinex` → `USDSGD_M1` in 0.5 s, file mtime kept.
`edit symbol=USDSGD_M1 timezone=EET` → "Data updated."; `-symbol action=list` still `(EST+07) New York`. 61 renames, 3 deletes (icmarkets AUDJPY/GBPJPY).
Zone ids (`-data action=timezones`): `EETUS` (EST+07), `EET`, `Asia/Jerusalem`.
