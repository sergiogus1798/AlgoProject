---
name: curate
description: Apply a Python verdict back into SQX — move the strategies a filter, a test or an analysis rejected out of a databank, so the next task in the chain only sees the survivors. Works between any two tasks and with any module that can name what it drops. Use when the owner asks to filter a databank, remove strategies, apply a verdict, or make the next task read only what passed.
---

# /curate

The one thing that closes the loop. Python reads a databank, judges it, and this puts the judgement
back where SQX will act on it: the next task reads the databank, and the databank no longer holds
what was rejected.

It changes what a databank contains: the rejected `.sqx` are **deleted**, after a record of what
was there (names, identities, metrics) is written beside the verdict. Nothing goes without `--apply`.

## The contract — this is what makes it generic

A CSV with these columns:

| column | |
|---|---|
| `strategy` | the name exactly as SQX has it, e.g. `Strategy 11.3.25` |
| `verdict` | `DESCARTAR` drops it; anything else keeps it |
| `identity` | optional: SHA-256 of the inner `strategy_Portfolio.xml` (`core.sqxfile.identity`). When present, the file is hashed before it moves and a mismatch aborts with nothing moved |
| `reason` | optional, free text: what the strategy failed. The trace, not the mechanism |

The identity is there because the name is not one: SQX renames on collision (`Strategy 19.6.36(1)`)
and `copy` stacks identical files under one name. Any module that can hash the file should fill it.

**Any module that judges strategies writes one of these, and this skill applies it.** Between the
build and the OOS, after an MC Retest, after a cross-market study, after a filter sweep, after a
one-off pandas script the owner wrote this morning — the mechanism does not change and does not care
what the judging was. If a module does not emit that CSV yet, writing one is two lines.

## Before anything: are the strategies on disk at all?

A databank set to **`Auto-sync never`** keeps its records in memory and leaves its directory empty.
The whole mechanism here is file-level, so there would be nothing to curate — and nothing for Python
to have filtered either. The donor's build databank ships that way. Two ways out, both before the
install stops: set it to `Auto-sync every 1 hour` in `project.cfx`, or run
`-databank action=synctofiles` on the instance that holds the records and give it time to land. The
command refuses on an empty directory and says this.

## Writing the verdict without a module: a filter, or a name

`sqx.curate.verdict` writes the CSV from the databank's current metrics export
(`sqx.export.export_metrics` first), with identities read from the files:

```bash
python3 -m sqx.curate.verdict --project <P> --databank Results --role custodian --columns
python3 -m sqx.curate.verdict --project <P> --databank Results --role custodian \
    --keep "net_profit_oos > 0 and n_of_trades_is >= 100"      # what fails is DESCARTAR
python3 -m sqx.curate.verdict --project <P> --databank Results --role custodian \
    --drop "Strategy 11.4.39"                                  # one selected in the owner's own table
```

Columns are the export headers slugged: `# of trades (IS)` is `n_of_trades_is`; `--columns` lists
them. The CSV lands in `AlgoData/reports/<P>/<databank>/<day>/curate/verdict-HHMMSS.csv`, one per
run, so a chain of cuts stays auditable. This is the repeatable loop the owner asked for: any filter
in Python, or any single strategy picked from his UI, becomes one verdict and one apply.

## Run it

```bash
# 1. always look first. Nothing moves without --apply. The identity check runs here too.
python3 -m sqx.curate.apply_verdict --project <P> --databank Results \
    --verdict <path>/verdict.csv --role custodian

# 2. stop the install, then apply
bin/sqx-worker.sh --role custodian stop
python3 -m sqx.curate.apply_verdict ... --apply

# 3. start it again — the sync from files is what makes memory match
bin/sqx-worker.sh --role custodian start
python3 -c "from core import worker; print(worker.call('-databank action=list project=<P>','custodian'))"
```

That last count is the verification, and it is not optional: it is the only place SQX tells you what
the next task will actually read.

## Why it moves files, and why you must not "just use the CLI"

The CLI has a `strategies=` selector. **It cannot be reached, and it fails silently when tried** —
measured 2026-09-23, written up in `knowhow/databanks/curating-a-databank.md`:

- Over the worker's HTTP API the name is **cut at its first space**, and every SQX strategy name has
  one. `action=delete` answers `Reports removed.` and the count does not move. `%20`, `+`, `%2520`
  and quotes were all tried.
- A **one-shot `sqcli`** never loads the databank's records. `action=save` with no selector at all
  wrote **0 of 30** files while answering `Reports saved.`
- ⚠️ `action=move` with a selector that never arrives moves the **whole databank**. Naming two
  strategies moved all thirty, with no error.

So if you find yourself reaching for `-databank action=delete strategies=…`, stop: it will report
success and do nothing, or move everything. The file level is the mechanism, because SQX syncs a
databank **from** files on its next access and memory is what a task reads.

## The three guards, and what to do when one fires

1. **The install must be stopped.** It holds the records in memory and rewrites the files from them,
   so a move under a live instance is undone by the next sync. The command refuses; stop it.
2. **A record is written first**, beside the verdict in `AlgoData/reports/<P>/<databank>/<day>/curate/`:
   `before-<stamp>.csv` (every strategy on disk: name, identity, bytes, this cut's verdict and its
   `reason`) and `rejected-<stamp>.csv` (the dropped ones' metrics rows, reason first). A verdict
   without a `reason` column gets the verdict file's name as the reason. **Re-export the metrics
   after every cut**: a verdict written from a stale export names strategies already gone. No copy of the `.sqx`: ~5 MB each,
   so 8k rejects would be 40 GB for strategies nobody revisits — the owner's decision, 2026-09-23.
3. **Counted back, not trusted.** If the verdict names a strategy with no file, or the numbers do
   not add up, it stops and names the list to compare the directory against. Do not re-run over
   it — look first.

## Rules

- **Record, then delete.** What a later study needs from the full population is its metrics, and
  those are kept in `rejected-<stamp>.csv`. The trades and XML of a rejected strategy go with the
  file; that is the trade-off the owner chose over keeping 40 GB.
- **Not into a databank unless asked.** `--into <databank>` moves instead of deleting, and SQX
  loads **every** databank of a project into memory on start, not just the one a task touches —
  measured in the custodian's log, five databanks loaded with individual timings on each sync. So
  rejects parked inside the project cost RAM, which is what the owner does not want when 8,000 of
  10,000 are cut.
- **One verdict, one move.** Applying two verdicts to the same databank without a count in between
  hides which one removed what.
- **Never curate a databank a task is writing.** The custodian takes one job at a time; curate
  between runs, never during.
- **Say what was dropped and on what evidence** when reporting — the count alone is not an answer.
  If the verdict came from thresholds that are placeholders, say so: the cut is then about the
  threshold, not about the strategies.
