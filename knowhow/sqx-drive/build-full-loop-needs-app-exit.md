---
q: Why does a Build keep logging «databank is full» after project action=stop?
kw: databank is full loop, Build finished because databank is full, no Task finished, stop does not end build, project stop acknowledged, exitapp ends build, start before APP LOADED, early start, databank-full 0/5, passed-count
tag: 🔬  date: 2026-10-13  see: sqx-drive/start-before-databanks-load, sqx-drive/live-chain-without-restart
---
# A Build started before «APP LOADED» loops on «databank is full»; `project action=stop` does not end it, only the app exit does
Trap: with a `databank-full` stop condition, send `start` only AFTER the log line «APP LOADED». Sent 6-7 s before it, the Build logs «Build finished because databank is full» again and again (52-104 lines, no «Task finished») and `project action=stop` answers success while the lines go on. Only exiting the app ends it.
Sent late, the same condition ends by itself: one «full» line, «Task finished» 2-7 ms later, «Project finished» ~1.5 s later. `passed-count` (30) ended by itself in all 3 runs either way.
Fix: `live.start` waits for «APP LOADED» before returning; wait on that line, never on the web server answering.

## Evidence
- 🔬 conductor, 2026-10-13, encargo 66 live session 3 (`/dev/shm/tmp66/live-session-3.md`): early start 0/5 stopped (first «full» line 100-113 s after start); late start 5/5 stopped (first full 13:44:19, Project finished 13:44:20.954, and four more); passed-count 3/3. Same recompiled jar in every cell.
- 🔬 session 2 saw 63+ looping lines until the session closed; session 1 saw a clean stop at 50: the difference is the start time.
