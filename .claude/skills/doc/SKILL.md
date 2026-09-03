---
name: doc
description: Record what a session discovered into the right knowhow, OPEN.md or CLAUDE.md file, and repair documentation that has drifted from the code. Use after work that found something non-obvious.
---

# /doc

Launch the `documenter` subagent.

1. Tell it what was discovered, in full, including how it was established — 🔬 tested, 📓 read from
   logs or files, or 🤔 inferred. Provenance is not optional; it decides how the claim is written.
2. Give it the reproduction: the command, file or log line that shows it.
3. It decides where the fact belongs and writes it there.

With no findings to record, it does a drift pass instead: every path, command and claim in the
documentation checked against what is actually on disk.

Use this at the end of a task, not at the end of a session. A finding that lives only in a transcript
is lost the moment that session closes.
