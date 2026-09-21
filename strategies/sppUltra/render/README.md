# sppUltra/render — how the reconnaissance is read

| file | what it does | in → out |
|---|---|---|
| `text.py` | The whole report as markdown: the verdict first, then the influence table and the plateaus it rests on | results → markdown |

Tables are written out by hand rather than through `DataFrame.to_markdown`, which pulls in
`tabulate` — a whole pinned dependency for one table. The helper is copied from
`strategies/retest/report.py`; it moves to `core/` when a third study wants it.

The page opens with the pairing warning on purpose. Every number below it is single-window, and a
reader who arrives expecting an IS-versus-OOS comparison has to be told in the first paragraph that
this export cannot give one.
