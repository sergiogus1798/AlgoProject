---
name: store-save
description: Save the strategies of a project that passed the gate (step 8, limbo included) into the strategy store — the .sqx once, every test's results, distributions, trades in every market and timeframe, the step-12 sisters — and verify the store is whole. Use when a workflow run ends or is cut, before retiring any project, when the owner says «guarda las estrategias», «guárdalas en el almacén», or when `retire` refuses because survivors are not saved.
---

# /store-save

A gate survivor cannot be generated again (the build is genetic). `sqx.projects.retire` deletes the
project folder with its `.sqx`, and refuses while a survivor is not whole in the store. This is the
command that makes it whole. It reads files only: no SQX call, any install may be up or down.

1. **Save.** `python3 -m core.store save <PROJECT>` — the `.sqx` are looked for in the project's
   databanks on both workers. If the project is gone from the workers but copies exist
   (`AlgoData/crosstf/<P>/<day>/sqx/`), add `--sqx-dir <folder>` (repeatable).
2. **Read its last lines.**
   - `N guardadas, 0 sin .sqx …, 0 con problemas` → done.
   - `SIN .sqx  <name>` (exit 1): no file with the judged identity anywhere. Look for it —
     `find ~/Desktop/SQX_w1 ~/Desktop/SQX_w2 ~/Desktop/AlgoData -name '<name>.sqx'` — and rerun with
     `--sqx-dir`. A file of that name with another identity is another strategy (names are reused
     between builds) and is never saved in its place. Still none: tell the owner which are lost,
     by name; never report the save as complete.
   - `MAL  <identity>` (exit 1): report the line as printed; do not delete or repair by hand.
3. **Verify.** `python3 -m core.store verify` — every line must start with `ok`.
4. **Audit.** `python3 -m core.store audit <PROJECT>` — everything the project left on disk must
   be in some zip.
   - `FALTA …` (exit 1): a report folder, an export or a variant batch of a stored strategy that
     no zip holds, or a data folder the store does not know. Report the lines; never retire the
     project with one standing. A new kind of folder is a change to `core/store/` (a reader, or
     a reasoned line in `audit.IGNORED`), not something to copy in by hand.
   - `ajeno …`: exports and reports that vouch for no stored strategy — another build's, or a
     strategy that died at the gate. Expected for old days; for TODAY's run it is a pairing that
     broke (an export without `lineage.csv`, a name that changed): report those.
5. **Later steps.** Run it again after any further step or study on the project: it adds only
   what is new (a test repeated with other results is kept beside the old one as `….2.zip`), and
   marks each step's verdict in the manifest. A strategy that fails a later step is marked, never
   deleted — purging is the owner's.
6. Only then may the project be retired (`python3 -m sqx.projects.retire <P> --role <role> --yes`,
   worker stopped, rule 6).

What a folder holds and how to read it back: `/store-open`. Layout: `core/store/README.md`.
A distribution missing from a zip means the study ran before 2026-10-08: say so, do not rerun a
study on your own to fill it. A step marked `[smoke]` in `list` was judged by the readability
rules alone (`--smoke`): it is not a verdict. Carrying saved strategies on: `/store-resume`.
