---
q: SQX log huge gigabytes, log retention prune archive, sqx-log-prune.sh --auto, archive_logs, keep days, current day log, error storm, WFM custom columns log, EdgeDecay project log noise, condensed log
tag: 🔬  date: 2026-10-01  see: columns/custom-columns-stored, columns/edge-decay-retired
---
# Logs: archive first, prune only what has a `.gz`, never today's file
`sqx.export.archive_logs` gzips every install's logs to `AlgoData/logs/<install>/`; `bin/sqx-log-prune.sh` deletes a live log only if its
`.gz` exists (else prints `KEEP … sin copia en el archivo`), keeps 7 days (`KEEP_DAYS`), skips `log_$(date +%Y_%m_%d).log` by name.
Run `--auto` (archive then prune, rate-limited, silent unless bytes moved; shouts when today's log > `WARN_MB` 200). SQX prunes nothing.
Big logs are tailed/grepped, never opened. The storm's cause stays unrepaired (owner, `OPEN.md` issue 3 ⚪), so pruning is permanent; readers of the master log filter `ProgressEngine` at source.

## Evidence
- Master 2026-09-21: 35 files, 4.5 GB — `log_2026_08_18.log` 4.4 GB, `log_2026_09_20.log` 55.5 MB, `log_2026_09_19.log` 1.2 MB, idle day ~130 KB (34,000×).
  Not: "SQX keeps 14 days / prunes on start" (`archive_logs.py` docstring) — files from 2026-06-13 still present.
- 📓 4.66 GB day: 43.9 M lines, 39.8 M Java frames; 2 M × `TradingException: Setting 'TradingSetup.StrategyClass' is not set.` from `StatsComputer` in
  `WFSimulationJob` computing custom columns `ParameterCount`, `DoFRatio` (`SQ.Columns.Databanks.*`) on every WF step; 49,080 × `NonexistingVariableException:
  Variable 'PriceEntryMult…' doesn't exist`; 184 × `Project 'Infinox - SPNft - HN (High Precision)' does not exist` (`OPEN.md` issue 6); rest 2,825 lines.
  → a WFM cross-check whose custom columns can't compute per step writes ~1 GB/hour. Kept as `log_2026_08_18.condensed.log.gz` (36 KB; frames dropped, 4 messages counted on the last line).
- 📓 2026-09-29 custodian: `log_2026_09_29.log` 526 MB, ~220k × the same `StrategyClass is not set` exception in `WFSimulationJob` (custodian log folder 202 → 704 MB in a day; `OPEN.md` #86). Recurrence of the storm above, not a new cause.
- 📓 2026-09-30 custodian: `log_2026_09_30.log` 167 MB, 70,212 lines mention `StrategyClass` — the same exception a second day running (audit 2026-10-01); custodian folder 861 MB, conductor 32 MB, master 1.6 MB. Archiver + prune cover it (7-day keep); the cause is SQX config, not repaired.
- 55 MB day = one error: `Infinox_SP500ft_H4_HighPrecision` sync failure looping hourly (`OPEN.md` issue 3).
- 📓 `user/projects/<P>/log/global_log_*` is 97 % `EdgeDecayFilter` noise (3 lines/strategy/pass: `running Per strategy analysis: EdgeDecayFilter` / `- OK` / `- Failed`):
  USDJPY 566 MB = 15.5 M lines, 135 K without. Signal (`TASK STARTED`/`TASK FINISHED` with databank counts, per-filter rejections, time/strategy) kept in
  `AlgoData/logs/SQX/projects/<P>/*.condensed.log.gz` (1,278 files, 6.7 MB, ten projects, 2026-09-21 snapshot). `archive_logs.py` walks only `user/log`; a `user/projects` snapshot must exclude these folders.
- Archive: 4.5 GB → 104 MB (2.3 %); 101 MB is `log_2026_08_18.log.gz` (43×), rest of the year 3 MB — each storm adds ~100 MB forever. Archive is never pruned
  (it's what makes pruning safe); bounded by `logs: 1 GB` in `perf/config.yaml`, `perf.disk.report` exits non-zero when over. 🤔 digest option (first/last + count per message) recorded, not taken.
- `--auto`: stamp `AlgoData/logs/.prune-stamp`, `MIN_HOURS` 4; 50 ms blocked, 170 ms idle run (`archive_logs` skips up-to-date `.gz` by mtime, 77 ms).
  Triggers: `SessionStart`/`Stop` hooks in `.claude/settings.json` (async), `bin/sqx-worker.sh start`/`stop`, cron backstop.
  Cron: archiver `0 4 * * *`, prune `15 4 * * *` (moved from 08:00 on 2026-09-25) (order not load-bearing). A machine off at cron time skipped days — the 4.4 GB file sat a month.
- Warning text: `AVISO: SQX/log_2026_09_21.log son 412 MB y es el log del dia en curso — la poda no puede tocarlo.` The check must sit outside the
  `find -mtime +$KEEP_DAYS` loop (inside, unreachable).
- ⚠️ Guard checks a `.gz` exists, not that it matches (divergence needs a rewrite with older mtime — SQX never, test fixtures do).
- Covers every install, `log_*.log` and `launcher_*.log`; `--dry-run` lists. First run reclaimed 4.4 GB.
- ⚠️ Archiver and pruner must walk the same installs: `archive_logs.py` defaulted to `[MASTER, WORKER]` so the custodian was never archived nor pruned; now
  `[MASTER, *WORKERS]` from `core.paths` — roles added to `machine.yaml` are picked up by both.
