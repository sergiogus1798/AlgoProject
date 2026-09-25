# sqx/curate — act on a verdict inside SQX

The only folder here that **changes what a databank contains**. Nothing runs without `--apply`,
and every cut leaves a record of what it removed next to the verdict that asked for it.

| file | what it does | run it | in → out |
|---|---|---|---|
| `verdict.py` | Write a `verdict.csv` from the databank's metrics export: keep what passes a pandas filter, or drop the names given; identities read from the files | `python3 -m sqx.curate.verdict --project P --databank Results --role custodian --keep "net_profit_oos > 0"` · `--drop "Strategy 11.4.39"` · `--columns` | `metrics.csv` → `AlgoData/reports/P/Results/<day>/curate/verdict-HHMMSS.csv` |
| `apply_verdict.py` | Delete the strategies a verdict rejected from a databank (or move them into another databank with `--into`), after checking each file's identity and recording what was there | `python3 -m sqx.curate.apply_verdict --project P --databank Results --verdict <path>/verdict.csv --role custodian --apply` | `verdict.csv` → files deleted, `before-HHMMSS.csv` + `rejected-HHMMSS.csv` beside the verdict |

## The contract between Python and SQX

A CSV with `strategy` and `verdict`; a verdict of `DESCARTAR` drops that strategy, anything else
keeps it. Optionally `identity` — SHA-256 of the inner `strategy_Portfolio.xml`
(`core.sqxfile.identity`) — and `reason`. **That is the whole contract** — any module that judges
strategies writes one, and `apply_verdict` applies it. Nothing here knows or cares what the judging
was. When `identity` is present the file is hashed before it goes: the name is not an identity
(SQX renames on collision, `copy` stacks identical files), and a mismatch aborts with nothing
touched. `verdict.py` writes the CSV for the two cases that need no module: a metrics filter, or a
name.

## Why it works on files instead of calling the CLI

Because the CLI's own selector cannot be reached, and fails silently when tried
(`knowhow/databanks/curating-a-databank.md`, measured 2026-09-23):

- Over the worker's HTTP API a strategy name is **cut at its first space**, and every SQX name has
  one. `action=delete` answers `Reports removed.` and the count does not move.
- A **one-shot `sqcli`** never loads the databank's records: `action=save` with no selector wrote
  0 of 30 files while answering `Reports saved.`
- `action=move` with a selector that never arrives moves the **whole databank**.

What works is the file level. SQX syncs a databank *from* files on its next access, so removing the
`.sqx` with the install stopped and starting it again makes memory match the curated directory —
and memory is what the next task reads.

## The three guards

1. **The install must be stopped.** It holds the records in memory and rewrites the files from them,
   so a file removed underneath a live instance comes back on the next sync. `--role` picks which
   install; the check is the GUI process for the master and the port for a worker.
2. **A record first.** `before-<stamp>.csv` lists every strategy on disk with identity, size,
   this cut's verdict and **why** (the verdict's `reason`: the filter it failed, the test, or the
   verdict file's name when the judging module wrote no reason); `rejected-<stamp>.csv` keeps the
   dropped ones' rows of the metrics export with that reason as its first column.
   Both land in `AlgoData/reports/<P>/<databank>/<day>/curate/`, beside the verdict. The `.sqx`
   themselves are deleted: at ~5 MB each, 8k rejects would be 40 GB kept for a strategy nobody
   will revisit (owner's decision, 2026-09-23). A `Rejected` databank inside the project would be
   worse: SQX loads every databank of a project on start, so they would cost RAM as well.
3. **Counted back, not trusted.** If the number that left does not match the number removed, or the
   verdict named a strategy with no file, it stops and says which list to compare the directory
   against.

What survives a cut is the population's **metrics**, which is what the population studies read.
Trade-level data of a rejected strategy is gone with the file.
