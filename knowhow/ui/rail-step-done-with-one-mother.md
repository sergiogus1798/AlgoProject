---
q: Why does the rail mark a per-mother step done as soon as one mother has its result?
kw: rail step 17 18 18.5 21 22 done with one mother, derive.study any batch has a result, autopilot skips mothers, every survivor through every step, blind look per mother skipped, redo after 16.5, plan the block when 19 pending
tag: 📓  date: 2026-10-02  see: pipeline/blind-door-is-per-study-not-per-project
---
# The rail calls a per-mother step «done» as soon as ONE mother has its result
`derive.study` reads `sources.results`: any `estudios/<key>.json` of any batch (17, 18, 18.5), any
`reports/<P>/*/*/<key>` folder (21-25). Five survivors with one WFC read is a step 17 «done»; a walker
that trusts it leaves mothers unread and step 20 lists them INCOMPLETA. So `pipeline.autopilot.tail
.walk` plans the three blind looks whenever ANY of 17, 18, 18.5, 19 is not done, and `blind.look`
decides per mother: skipped when `<batch>/estudios/<key>.json` exists, unless `redo` (16.5 ran in
this plan). A re-run is not free: it signs ledger rows, one more look.
⚠️ 21 and 22 have no per-mother check: done on the rail is skipped whole.

## Evidence
- `derive.study`: `key = next((k for k in spec["studies"] if found[k]), None)`; a batch result
  counts as `n = len(found[key])` batches, with no mother list to compare against.
- `tests/test_autopilot_tail.py::test_a_rerun_takes_up_where_it_stopped` and the `look` block of
  `test_the_door_refuses_to_read_without_the_three_rows` (0 mothers read with the file present,
  1 with `redo`).
