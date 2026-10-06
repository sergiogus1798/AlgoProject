# falsePositives — the chain's negative control: how many strategies with no edge get through?

Encargo 9 (`docs/encargos/9-monos-de-punta-a-punta.md`). Monkeys — random-entry trade lists drawn
on the footprint of every strategy of a real population — are judged by the chain's own rules,
`pipeline/autopilot/criteria.yaml`, step by step, and counted beside the real population put
through the same code. It ends in one number per rule and per step: the share of a null
population it lets through. It judges no real strategy, so it writes no `verdict.csv`.

```
config.yaml ─▶ inputs ─▶ model ─▶ chain ─▶ many ─▶ report
 how many,     the real   a monkey  the facts  monkeys   the funnel,
 which rung,   harvest,   as a      and the    beside    reglas.csv,
 which sizing  the rules  trade     rules      real      the ledger rows
                          list
```

| file | what it does | run it | in → out |
|---|---|---|---|
| `config.yaml` | The knobs: monkeys per donor, the rung, the sizing. No threshold lives here | edited, or `--set monkeys.per_donor=50` | — |
| `tooltips.py` | One Spanish sentence per knob, for the window's configuration drawer | imported | — |
| `inputs.py` | The knobs, the real population's gate harvest with its bars and market, the gate's and the null engine's configs, and the criteria file | imported | project + databank + feed → harvest, rules |
| `model.py` | **Modelling**: a monkey as a trade list — `engines/nulls` draws entries, holds and sizes under a rung and `barrier.pnl` prices them at the donor's measured point value and cost; `SIZING` holds the two ways to size it; the daily curve from closed trades | imported | donor trades + bars → monkey trades, curve |
| `chain.py` | **Execution and judging**: the monkeys dressed as a harvest, step 8's facts by the gate's own cascade and measures, and `walk`, the population through every step of criteria.yaml | imported | trades → facts → funnel, per-rule counts |
| `many.py` | The control over one population: every donor's monkeys, the real population through the same code, the side-by-side funnel as the contract's result | imported | harvest → result |
| `report.py` | **The command**: prints the funnel, writes `falsePositives.json/.html/.md`, `funnel.csv`, `reglas.csv`, `hechos_monos.parquet` and the manifest under `reports/<P>/<D>/<day>/falsePositives/`; `--ledger` writes one row per judged step | `python3 -m studies.screening.falsePositives.report --project Test_XAUUSD_donchianUpperCrossUp2_H1 --databank Results --feed XAUUSD_M1 [--seed N] [--criteria file.yaml] [--ledger] [--set monkeys.sizing=atr]` | harvest → reports |

Manual page, in Spanish: `docs/manual/05-cribado-oos.pdf` (cap. 99-monos-por-la-cadena). Test:
`tests/test_false_positives.py`.

## What it measures, and what it does not

**The mortality of our filters, not of SQX's generator** (encargo 9 §2.1 bis). A monkey is born
in Python: it crosses the chain's criteria, not its SQX tasks, and it was never selected by a
build. The selection is encargo 30's.

**Random entries are read on `oos1` only.** Each monkey also carries an in-sample half, drawn
the same way inside the donor's build window, because step 8's rules read it (trades per year,
drawdown OOS / IS, the Sharpe's retention); no p and no significance is taken on it.

**The rules are a parameter.** `--criteria` names the file; the default is the autopilot's. The
result carries a warning while that file is not frozen: every rule in it is then provisional.

| step | applied to a monkey | why not |
|---|---|---|
| 8 | every rule on a `gate.scorecard.*` fact and the OOS trade count, by the gate's own `cascade.run` and `measures.table` | `edgeCost.*` needs Darwinex's tick scan and the SQX task's flat spread: no fact, rule not applied, listed in `reglas.csv` with `applied = False` |
| 10 | nothing | the monkey on the other markets — its donor's retest footprint placed on each market's bars (`engines/nulls/placement`) — is not built |
| 12 | nothing | scaled siblings are fabricated by SQX from parameters; a monkey has none. The rule never fails anyway |
| 14 | nothing | MC Retest's combined stress is an SQX task with no Python model |
| 16 | — | no rule in criteria.yaml |
| 17–20 | — | no rule exists anywhere (owner's D3), and they read `oos2`, which needs the owner's word |

A step that is not applied lets everyone through, so **from step 10 on the monkeys alive are a
ceiling, not a measurement**. A rule that is not applied inflates the monkey's survival; none is
applied that a real strategy is spared.

## Where the monkey is not the real thing — each one moves the count

- **`presencia` always passes.** SQX's red flags, which drop a real strategy from the retest
  databank, cannot fire on a list Python drew.
- **Trades per year are the donor's**, in and out of sample: the trade count is what every rung
  keeps. Those rules fail a monkey exactly when they fail its donor.
- **The curve is closed P&L by close day**; SQX's is each day's lowest equity, floating included
  (OPEN.md #88). A monkey's worst day and drawdown read milder than a real strategy's would.
- **`MAE ($)` is read on the strategy's bars**, SQX's on M1: 🔬 on a real donor the two correlate
  at 0.9998 with a median ratio of 0.94.
- **The size.** Under `sizing: donor` a monkey's trade keeps a size fitted to the volatility of
  the donor's entry, and lands on a bar of any volatility: 🔬 79 % of `timing` monkeys showed a
  trade 5R under water against 1 % of their 300 donors, so the floating-risk rules kill monkeys
  for a pairing no sizing rule would allow. `sizing: atr` re-sizes at the monkey's own entry with
  the engine's ATR (not the strategy's, which is not fitted). The two bracket the count; which
  one is the control is the owner's call (`knowhow/research/monkey-size-carries-donor-volatility.md`).
- **It imports the gate** (`studies.screening.gate.cascade`, `.measures`, `.inputs`), against the
  rule that a study imports no other. A control has to run the code it controls: a copy of the
  scorecard is how the two would drift apart unseen.
- **A donor that does not reconcile is left out** (`verdict.RECONCILE_FLOOR`, 0.99), and so is
  one without trades on one of the two samples; both are counted in the result. 🔬 Every donor
  of the USDJPY harvests of 2026-09-27..29 fails it (0.966–0.988): they were exported before the
  feeds were re-clocked on 2026-10-01.

## Not done

Step 10 for the monkey; the false-positive rate of each threshold written into
`ledger/thresholds.yaml` (the chain's rules live in `criteria.yaml`, and a rate is only worth
writing from the owner's full-scale run); the dev draw of criteria.yaml (`dev.sample`) is ignored
on purpose — it is a development device, not a criterion.
