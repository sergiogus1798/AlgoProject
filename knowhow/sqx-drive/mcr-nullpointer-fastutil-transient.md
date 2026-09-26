---
q: MC Retest crash NullPointerException fastutil IntArrayList wrapped null; MCR 1 Bar Error while running project; project hangs after MCR crash no Project finished; transient SQX engine bug
tag: 🔬  date: 2026-09-26  see: authoring/cloned-custom-block-native-key
---
# MCR 1 Bar can crash SQX's own engine with a NullPointerException — transient, not caused by project config, and the project hangs silently afterwards
Running the eight MC Retest tasks (`/mcretest`, paso 13) on `USDJPY_workflow_profiling_v1` (8
strategies, market entries, `RandomizeStartingBar` first): `MCR 1 Bar` printed
`Task finished in 27.96 s.` and immediately after, the SAME thread logged
`Error while running project 'USDJPY_workflow_profiling_v1'.` with
`java.lang.NullPointerException: Cannot invoke "it.unimi.dsi.fastutil.ints.IntArrayList.getInt(int)"
because "this.wrapped" is null`, stack rooted in `it.unimi.dsi.fastutil.ints.Int2IntOpenHashMap`
iteration — SQX's own internal collections library, nothing in this project's task XML or the
custom block chain.

**The project does not report the crash as a failure state.** `-project action=status` kept
answering with the frozen numbers from the moment of the crash (`Running time so far 27 s.`,
`In databank <N>`) indefinitely — three status calls minutes apart returned byte-identical text.
The only way to tell it was dead, not merely slow, was `ps` on the `sqcli` PID: CPU time had stopped
climbing (`TIME` frozen across a 4-minute window) while `ps` still listed it `Ssl` (sleeping,
not zombie). A live, computing MCR task shows the opposite signature — CPU time climbing every few
seconds even while `action=status` itself does not refresh mid-task (see caveat below).

**It was transient.** `action=stop` then `action=start` again (a full project restart, which redoes
`MCR 1 Bar` from scratch since it is still the only other active task) ran clean the second time:
all eight strategies retested across all seven configured MCR tasks (`MinDist` correctly unconfigured,
market entries) with no repeat of the exception anywhere in a fresh multi-thousand-line log window.

## Evidence
- Crash: 2026-09-26 09:57:17, custodian, first `action=start` of the MC Retest step, right after
  `MCR 1 Bar : Task finished in 27.96 s.` (log line 562112 → 562124/562129,
  `log_2026_09_26.log`). `MCR 1 Bar`'s own databank had already been written to disk (8/8 `.sqx`
  files present), so the crash landed in the task-transition/stats code, not the backtest itself.
- Frozen status confirmed real by cross-check: `ps -o pid,etimes,time,%cpu,cmd -p <pid>` showed
  `TIME` unchanged (`00:27:53`→`00:27:54`) across ~4 minutes elapsed while `%cpu` decayed from
  219%→170% (a lifetime average, not current load) — the process was idling, not computing.
- Retry (10:14:13–10:31:xx, fresh `sqcli` PID): `MCR 1 Bar` 28.13 s, `MCR 2 Spread` 260.08 s,
  `MCR 3 Slippage` 268.86 s, `MCR 5 Params` 21.25 s, `MCR 6 Exits` 261.54 s — no exception, `In
  databank` climbing normally task by task (80→88→96→98→104→112→...). During a genuinely running
  task, `ps` `TIME` climbed by ~8 minutes of CPU per 5 seconds of wall clock (≈70-80 cores active),
  a clean discriminator from the frozen-crash signature above.
- 🤔 `action=status` does not refresh its own counters mid-task for MCR-type tasks the way it does
  during the build/generation phase (which shows `Strategies generated` climbing into the thousands
  live) — several consecutive real, non-crashed status calls returned identical text for tens of
  seconds while the task was genuinely retesting. Do not read a static status line alone as a hang;
  corroborate with `ps` CPU time before concluding the project is stuck.
- Not reproduced a third time; no other session's log around that timestamp shows JVM GC pressure or
  OOM. Left as 🤔 whether it's a race in SQX's stats aggregation when a MC task with silenced
  acceptance conditions finishes and the next one's databank stats are computed concurrently.
- **The crashed attempt's 8 `MCR 1 Bar` files are not cleaned up by the restart.** The retry reran
  `MCR 1 Bar` from scratch and SQX wrote 8 new files under colliding names, so the databank folder
  ended up with 16: the original 8 (from the crashed run, task-complete but nothing downstream) plus
  `Strategy <name>(1).sqx` for each (the successful retry). `studies.breakage.mcRetest.report`
  correctly excludes the `(1)` siblings ("fuera del informe, le faltan tareas: ...(1) — sin exits,
  ohlc, params, ...", since they only ever got the one task) and the ingest flags them as "level
  tables unusable (run cut short)" — so the analysis is unaffected, but a project restarted after a
  mid-chain crash leaves stale duplicate `.sqx` on disk that a naive count or a manual glob would
  double. Worth a manual check of `databanks/<task>/` for `(1)` names after any run that crashed and
  was restarted rather than resumed.
