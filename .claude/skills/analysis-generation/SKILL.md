---
name: analysis-generation
description: Run the generation study for a databank — export the metrics from SQX, build the IS/OOS panel, sweep the filters, and write the conclusions saying which filters to set when generating strategies, which to set when testing out of sample, and which metric the SQX genetic algorithm should optimise. Given several databanks, check instead whether an earlier sample's conclusions replicate on the newer generation runs. Use when the owner asks to analyse a databank, what a report means, what to filter on, what to target, or whether a conclusion held.
---

# /analysis-generation

Two modes, decided by how many databanks the owner names.

**One databank — the study.** Everything from the export to the decisions:

```
export_metrics  →  is_oos  →  filters  →  conclusions.md
   (SQX)           (panel)    (sweep)      (the decisions)
```

**Several databanks — the replication check.** Whether the conclusions drawn on one sample hold on
independently generated ones: jump to *Mode B* below.

It **reads data and writes reports**. It never changes a project, a task or a build — hard rule 3
stands. The recommendations are for the owner to apply in the GUI himself.

## Step 0 — decide whether to re-export

```bash
ls -l ~/Desktop/AlgoData/metrics/<PROJECT>/<DATABANK>/metrics.csv
```

**Reuse the CSV if it is recent enough for the question** — analysing it again costs a second, and
re-exporting costs minutes and starts the worker. Re-export when the databank has been rebuilt or
retested since that date, or when the owner asks for fresh data. If the file does not exist, there
is nothing to reuse.

To refresh (see `/export` for the traps):

```bash
python3 -m sqx.export.export_metrics --project XAUUSD --databank OOS
```

The worker must end stopped — `bin/sqx-worker.sh stop` if the run failed halfway. Never run `sqcli`
against the master while its GUI is up.

## Step 1 — the two analyses

```bash
python3 -m tasks.reports.is_oos  --project XAUUSD --databank OOS   # ~1 s   panel + summary.md
python3 -m tasks.reports.filters --project XAUUSD --databank OOS   # ~40 s  filters/improvement.md
```

Both write into `~/Desktop/AlgoData/reports/<P>/<D>/<date>/`. Neither touches SQX, so both are safe
with the GUI open. If the owner named no project, list that reports directory and use the most
recent, then say which one you used.

## Step 2 — read, in this order

1. `filters/improvement.md` — the sweep of 210 candidates. It carries the intervals and the
   correction, so **this is the evidence**, not the correlations.
2. `summary.md` — persistence and predictor rankings. Use it for *why* a filter works, and for the
   genetic-algorithm target, which the sweep does not answer.
3. `manifest.json` in both — which CSV, which export date, which commit. Name them in the output.

## Step 3 — the three answers

**Generation filters** — what to demand while SQX is building. Take from the sweep the filters that
survive BH, improve the median, and leave enough strategies to be worth generating. **At most three**,
each with its kept count and Δ hit pp. State the cost in the same breath as the gain: a filter is a
trade, never a free improvement.

**Out-of-sample testing filters** — what to demand afterwards, cribbing a databank that already
exists. Same evidence, different tolerance: here the owner can afford to be harsher. Compare the
cuts and **say where the curve flattens** — on XAUUSD the first cut buys 22 points of hit rate and
tightening from 10% to 5% buys under 2 more while halving the survivors.

**Target metric for the genetic algorithm** — which OOS outcome the search should chase. Argue it
from the persistence table (does the metric hold its own value from IS to OOS at all?) and from how
many IS metrics predict it. A metric that decays to nothing out of sample is a bad target however
good it looks in sample.

## Rules that keep the answer honest

- **Near-identical metrics are one filter, not several.** In XAUUSD, CAGR/Max DD %, CalmarRatio,
  R Expectancy, SQN, Profit factor, Sharpe and Sortino at the same cut give the same survivors to
  within noise, and CAGR/Max DD % and CalmarRatio are literally the same column. Pick one; never
  present seven names as seven independent edges.
- **Read the interval, not the p.** The bootstrap p has a floor at 1/2000 and sits there for most
  rows. An interval straddling zero kills a filter whatever the p says.
- **Report the search space.** 210 candidates were tried. A conclusion that does not say so is not a
  conclusion, per `tasks/CLAUDE.md`.
- **One asset, one period.** Never generalise a XAUUSD result to another symbol. Say what would have
  to be run to check it.
- **Say when the answer is "this does not help much".** Even under the best filter these medians sit
  around zero. A recommendation that hides that is worthless.

## Output

Write `conclusions.md` into the report directory it read, **in English** like the other report files,
then give the owner the same conclusions in Spanish in the conversation. Structure:

1. What was read — the reports, the export date, the commit, the strategy count.
2. The three decisions, each as a recommendation plus its cost and its evidence line.
3. What would change the answer — the check that has not been run yet.

One page. It is a decision memo, not a second copy of the tables.

---

# Mode B — did the conclusions replicate?

When the owner names several databanks (a random reference plus generation runs made under the
recommendations, or the same population over another period):

```bash
python3 -m tasks.reports.compare --project XAUUSD --reference OOS \
    --databank OOS-sharpe --databank OOS-rExpectancy --databank OOS-hasta2026   # ~25 s
```

Writes `reports/<project>/_comparison/<date>/comparison.md`. **The reference is the sample the
conclusions came from** — normally the unfiltered random generation. Every databank needs its
metrics export first, all through the same SQX view or the columns will not line up.

## First, establish what the samples are

**Ask if it is not obvious.** The whole reading changes:

- **Independently generated** (new strategies, a run with that acceptance condition or that target):
  a real replication. Proceed.
- **A subset of the reference** (the same strategies, filtered and retested): there is nothing to
  replicate — the panel's own filter already shows that, and the answer is known in advance. Say so
  instead of producing a report that looks like evidence.
- **Another period** of the same population: a genuine test, but it differs in two things at once
  (period and strategies) unless one is held fixed. Say which when reporting.

## How to read what comes back

- **The outcome table is the verdict.** Δ hit pp against the reference, and its interval. Straddles
  zero, no difference.
- **`predicted` vs `observed` is the promise kept or broken.** The reference's threshold carried
  over. An interval on Δ that includes zero means the filter delivered what it said.
- **`% of sample passing` near 100 confirms the sample really was built to that filter** — it is how
  you check the owner's databank matches the label on it.
- **A collapsed rank agreement on a selected sample is arithmetic, not failure.** Read the
  restriction line under it before concluding anything.
- **Overlapping filters move together.** Six rows agreeing is one observation.

## Reporting it

Write `replication.md` next to `comparison.md`, same shape as the study's memo: what was compared,
did each recommendation hold, what to change in the next generation run. Then say it in Spanish in
the conversation.

State plainly which of the three questions from Mode A survived, which did not, and which cannot be
answered yet because the sample is too small or was selected on the very metric being tested.
