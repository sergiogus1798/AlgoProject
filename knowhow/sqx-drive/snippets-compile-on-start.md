---
q: How does a Java snippet of ours get compiled and loaded by a worker, and how do I know it did?
kw: user/extend/Snippets, Snippets.jar, SnippetsCompiler, Compilation FAILED NO snippets were updated, Class with name doesn't exist, snippet not found after copying, old class still runs, two starts, sqcli headless compile, CustomAnalysis, custom block java
tag: 🔬  date: 2026-10-12  see: customanalysis-task-reads-any-project
---
# SQX compiles snippets on start and loads what the PREVIOUS start compiled; a compile error keeps every old class in silence
A `.java` under `<install>/user/extend/Snippets/SQ/…` is compiled when SQX starts (sqcli or GUI)
into `internal/libs/Snippets.jar`, but that JVM already loaded the previous jar: **a new snippet
needs a start, a stop, and is live on the next start.** One error in any snippet and NONE is
updated — the old class keeps answering, and only `user/log/StrategyQuant/log_<date>.log` says
`Compilation FAILED`. `python3 -m sqx.snippets.install --role <role>` does it all and fails
loudly; `--check` names what an install does not run yet.

## Evidence
- 🔬 conductor, 2026-10-12: `AlgoKeep.java` copied, worker started, `action=start` on a task naming
  it → «Class with name 'AlgoKeep' doesn't exist»; stopped, started again → the task ran.
- 🔬 same day: `AlgoTrades.java` (deleted 2026-10-13; `install` now prunes installed snippets the repo dropped) edited to cache `DataManager.getDataInfo` without its import →
  `cannot find symbol DataManager`, `Compilation FAILED`; the next run timed exactly as the old
  class (245 s) and produced the old output. With the import: 3.9 s.
- 🔬 `SeededRandomEntry.java` plus its `Code/PseudoCode/blocks/SeededRandomEntry.tpl` compiled the
  same way and appeared in `python3 -m sqx.inspect.vocabulary --role conductor seeded`.

## Also
A `.java` under `<install>/user/extend/Snippets/SQ/…` (a block's code templates under
`user/extend/Code/<language>/blocks/`) is compiled when SQX starts — headless `sqcli` and GUI mode
alike — into `internal/libs/Snippets.jar`. But the JVM of that start has already loaded the jar the
previous start left: **a new or changed snippet needs one start to compile, a stop, and is live on
the next start.** One error in any snippet and SQX updates NONE of them: it keeps the old jar and
says so only in `user/log/StrategyQuant/log_<date>.log` (`SnippetsCompiler - Compilation FAILED …
NO snippets were updated`). The old class then answers under the same name, and a measurement of
"the new code" is a measurement of the old one. `python3 -m sqx.snippets.install --role <role>`
does the copy, the compiling start and the stop, fails with the compiler's reason, and `--check`
(`install.pending`) names what an install does not run yet: not copied, changed, no `.class` in
the jar, or a jar older than the installed source.

Writing snippets is the extension the vendor offers. Reading SQX's own classes is not:
`SQ_License_and_Service_Terms.pdf` §4.9 forbids decompiling — the snippets shipped as source in
`internal/extend/Snippets/` are the reference, and enough.
