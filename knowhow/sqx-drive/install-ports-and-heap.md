---
q: where is the SQX CLI port set AppSettings.txt; WebServerPortUsed; coreUsage missing means all cores; -Xms -Xmx per install; worker answering on 5050; History symlink; disk cost of an install
tag: 🔬  date: 2026-09-25  see: sqx-drive/three-install-topology, perf/ram-budget
---
# Ports live in `internal/AppSettings.txt` + `settings.xml`; heap in `sqcli.config`; absent `coreUsage` = all cores
CLI+editor ports: `internal/AppSettings.txt` (`<AppWebServerPortSQUANT>`, `<AppWebServerPortSQEDITOR>`);
web port: `<WebServerPortUsed>` in `user/settings/settings.xml`. `sqcli` binaries are byte-identical.
A worker answering on 5050 = its `AppSettings.txt` was reset (two `sqcli` started at once), not the master.
`<coreUsage>` in `user/settings/settings.xml`, `-1` = all; absent also = all — add it on old clones.

## Evidence
| install | CLI/editor/web | `-Xms`/`-Xmx` (`sqcli.config`, read 2026-09-25) | `coreUsage` 96c/16c | size |
|---|---|---|---|---|
| `SQX` master | 5050/5051/8080 | 4g / 24g | −1 | 9.7 G + History |
| `SQX_w1` conductor | 5060/5061/8081 | 1g / 16g | 8 / 2 | 4.4 G |
| `SQX_w2` custodian | 5070/5071/8082 | 1g / 80g | −1 / 8 | 4.3 G |
W2 was built at 48g/48 cores (2026-09-21); owner raised it to 80g/all cores 2026-09-23. The GUI
launchers (`StrategyQuantX.config`) differ: master 2g/24g, workers 1g/8g — irrelevant headless.
⚠️ Before 2026-09-21: master `-Xmx108g` + W1 `-Xmx32g` = 140 GB on a 125 GB machine.

- 📓 Port reset: two sessions launched `sqcli` in `SQX_w2` 200 ms apart; one logged
  `Cannot load settings. Exc.`, fell back to defaults, opened 5050, died with
  `Database may be already in use: Locked by another process`, and on exit wrote
  `AppWebServerPortSQUANT=5050`, no `SQEDITOR` line. Later starts refused:
  `Preventing multiple instances: already running on port 5050`. Fixed by hand (5070/5071, web 8082), install stopped.
  ✅ `bin/sqx-worker.sh start|run` now refuses when the port in `AppSettings.txt` isn't the role's, or
  when another `sqcli` has that install as cwd (`running()` only watched the port). Still no owner
  lock — sessions can `stop` each other's runs (`OPEN.md` issue 32).
- 🔬 W1 ran weeks with no `coreUsage` (38-line `settings.xml`) = all 96 cores. `clone-sqx-worker.sh` writes it per role.
- 🔬 `-Xms` is the idle cost: at `1g` a fresh worker commits 1.7 GB (`jstat -gc`, eden 1.0 + old 0.7) vs 4 GB at `4g`.
- 🔬 `user/data/History` is a symlink to the master's on both workers (84 GB once); the three H2 bar
  files (42 MB) are per-install copies (exclusive lock). Extra install ≈ 3 GB disk (`internal/` 2.8 GB).
