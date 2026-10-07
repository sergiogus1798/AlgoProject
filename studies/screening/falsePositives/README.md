# falsePositives — the chain's control: how many strategies with no edge get through, and how many with one are lost?

Encargo 9 (`docs/encargos/9-monos-de-punta-a-punta.md`) and encargo 44, part K. Monkeys —
random-entry trade lists drawn on the footprint of real strategies — are judged by the chain's
own rules, `pipeline/autopilot/criteria.yaml`, as a **null population** and again with an **edge
of known size planted** on every oos1 trade (Sharpe per trade 0.05, 0.10, 0.15), beside the real
population put through the same code. Step 8 is the whole gate (`gate/levels.py`) with the
**cascade off**: every rule is computed for everybody, so each rule's effect can be read alone.
It ends in, per rule and per population, the share in Pass, Limbo and Fail — what a null
population gets through and what a good one loses, and at which rule. It judges no real
strategy, so it writes no `verdict.csv`.

```
config.yaml ─▶ inputs ─▶ model ─▶ chain ─▶ many ─▶ report
 how many,     the staged  a monkey, the gate's  null, planted  the funnel,
 which rung,   harvest,    and the   levels and  and real,      reglas.csv,
 which edges   the rules   plant     the rules   side by side   the ledger rows
```

| file | what it does | run it | in → out |
|---|---|---|---|
| `config.yaml` | The knobs: monkeys per donor, the rung, the sizing, strategies per population and the planted edges. No threshold lives here | edited, or `--set population.per_level=500` | — |
| `tooltips.py` | One Spanish sentence per knob, for the window's configuration drawer | imported | — |
| `inputs.py` | The knobs; the real population's harvest (`harvest=` an explicit folder, else the newest) staged as the gate's levels read it; the gate's config with the cascade off and its three seeds set to the run's root; the null engine's config; the criteria file | imported | project + databank + feed (+ folder) → harvest, rules |
| `model.py` | **Modelling**: a monkey as a trade list — `engines/nulls` draws entries, holds and sizes under a rung and `barrier.pnl` prices them at the donor's measured point value and cost; `SIZING`, the two ways to size it (`atr`: the ATR of the bar before the entry); `planted`, the edge added to level 1a's per-trade table; the daily curve from closed trades | imported | donor trades + bars → monkey trades, curve; per-trade table + edge → planted table |
| `chain.py` | **Execution and judging**: the monkeys dressed as a harvest; `facts8`, every level of `gate.levels.LEVELS` over everybody plus the measured columns, the edge planted right after level 1a; and `walk`, a population through every step of criteria.yaml, per rule alone and in order | imported | trades → facts → funnel, per-rule counts |
| `many.py` | The control over one harvest: the monkeys of the donors drawn, the chain once per edge on the same monkeys and once on the real population, the funnel and the rule tables with `nivel` in front | imported | harvest → result |
| `report.py` | **The command**: prints the funnel and each rule's Pass and Fail share per population, writes `falsePositives.json/.html/.md`, `funnel.csv`, `reglas.csv`, `hechos_monos.parquet` and the manifest under `reports/<P>/<D>/<day>/falsePositives/`; `--ledger` writes one row per judged step, the null population's | `python3 -m studies.screening.falsePositives.report --project P --databank Results --feed USA500_M1 [--harvest <folder>] [--seed N] [--criteria file.yaml] [--ledger] [--set population.per_level=500]` | harvest → reports |

Manual page, in Spanish: `docs/manual/05-cribado-oos.pdf` (cap. 99-monos-por-la-cadena). Test:
`tests/test_false_positives.py`.

## What it measures, and what it does not

**The mortality of our filters, not of SQX's generator** (encargo 9 §2.1 bis). A monkey is born
in Python: it crosses the chain's criteria, not its SQX tasks, and it was never selected by a
build. The selection is encargo 30's.

**Random entries are read on `oos1` only.** Each monkey also carries an in-sample half, drawn
the same way inside the donor's build window, because step 8's rules read it (trades per year,
the frequency's stability, R6's resampled drawdown); no p and no significance is taken on it, and
no edge is planted on it.

**The planted edge** (`model.planted`): every oos1 trade of a monkey gains `edge x the sd of that
monkey's excess` — level 1a's excess, the repricer's P/L minus the drift term. Three things
follow, and each moves how a rate is read:

- **It is added on top of what the monkey has, and the monkey pays the declared costs.** The
  null population's mean excess is below zero by its cost, so a planted 0.15 is a net Sharpe of
  0.15 minus mean cost / sd. 🔬 2026-10-07, synthetic driftless walk, 196 oos1 trades of 1 to 5
  bars, 1,000 monkeys (`tests/test_false_positives.py`): **gross** of costs R3 (`drift_excess_t
  >= 1.65`) passes 4.1 % of the null population and 62 % of the 0.15 one; with a spread worth
  0.81 of t, 0.25 % and 33 %. The textbook 5 % and 67 % are the plain t's: the gate's t is at
  the AR(1) effective n over the skewness-and-kurtosis error, which only shrink it (the lift was
  2.02, not 0.15 x 14 = 2.1; with holds up to 40 bars, whose trades overlap, 1.89 and 2.0 % /
  58 %). On real populations a no-edge strategy crosses R3 4.05 % gross and 0.87 % net
  (`knowhow/research/gate-t-scales.md`).
- **It is a constant per trade, so it does not depend on the fill**: the one-bar delay keeps it
  whole. Level 2 reprices the moved trade from the bars, so `chain._delayed` adds the plant back
  to the moved mean and takes `retraso_t_delta` from the table before the plant (exact unless a
  variant drops trades shorter than its shift).
- **The same monkeys make every population**, and the gate's three seeds are the run's root:
  two populations differ in the plant and in nothing else, draw for draw.

**The rules are a parameter.** `--criteria` names the file; the default is the autopilot's. The
result carries a warning while that file is not frozen: every rule in it is then provisional.

**What a count is not** — `nota` in `reglas.csv`, per rule:

| rules | on monkeys |
|---|---|
| presence (R1a), clones and trade counts (R1b, R4a, R5b), frequency stability (R5) | **inherited from the donor**: a monkey keeps its donor's trade count on both samples and is always in the retest. Not measured |
| R5 and R5d (`z_frec`, `t_b`, `e_fin`) | centred on everybody, since nobody leaves with the cascade off: **diagnostic only** (owner, 2026-10-07) |
| the one-bar delay and data quality (`retraso_ret_min`, `ret_datos`) | a retention exists only where the mean excess is positive: the rest has no fact, which the rule sends to Limbo |
| data quality | all Limbo when the feed has no anomaly inventory covering oos1 |

| step | applied to a monkey | why not |
|---|---|---|
| 8 | every rule: the gate's eight levels and its measured columns | — |
| 10 | nothing | the monkey on the other markets — its donor's retest footprint placed on each market's bars (`engines/nulls/placement`) — is not built |
| 12 | nothing | scaled siblings are fabricated by SQX from parameters; a monkey has none. The rule never fails anyway |
| 14 | nothing | MC Retest's combined stress is an SQX task with no Python model |
| 16 | — | no rule in criteria.yaml |
| 17–20 | — | no rule exists anywhere (owner's D3), and they read `oos2`, which needs the owner's word |

A step that is not applied lets everyone through, so **from step 10 on the monkeys alive are a
ceiling, not a measurement**.

## Where the monkey is not the real thing — each one moves the count

- **`presencia` always passes.** SQX's red flags, which drop a real strategy from the retest
  databank, cannot fire on a list Python drew.
- **Trades per year are the donor's**, in and out of sample: the trade count is what every rung
  keeps. Those rules fail a monkey exactly when they fail its donor.
- **The curve is closed P&L by close day**; SQX's is each day's lowest equity, floating included
  (OPEN.md #88). A monkey's worst day and drawdown read milder than a real strategy's would.
- **`MAE ($)` is read on the strategy's bars**, SQX's on M1: 🔬 on a real donor the two correlate
  at 0.9998 with a median ratio of 0.94.
- **The size.** `sizing: atr`, the default (owner, 2026-10-07: the doctrine's sizing, never the
  donor's lots), sizes each trade by the ATR of the bar before its entry — the engine's ATR, not
  the strategy's, which is not fitted. Under `sizing: donor` a trade keeps a size fitted to the
  volatility of the donor's entry and lands on a bar of any volatility: 🔬 79 % of `timing`
  monkeys showed a trade 5R under water against 1 % of their 300 donors
  (`knowhow/research/monkey-size-carries-donor-volatility.md`).
- **Two P/Ls, as a real strategy has.** Level 0 reads the monkey's net at the donor's MEASURED
  cost (`barrier.pnl`); level 1a on reads the common repricer's at the asset's DECLARED costs.
- **It imports the gate** (`studies.screening.gate.levels`, `.cascade`, `.measures`, `.inputs`,
  three of its levels by name), against the rule that a study imports no other. A control has to
  run the code it controls: a copy of the scorecard is how the two would drift apart unseen.
- **A donor that does not reconcile is left out** (`verdict.RECONCILE_FLOOR`, 0.99), and so is
  one without trades on one of the two samples; both are counted in the result. 🔬 Every donor
  of the USDJPY harvests of 2026-09-27..29 fails it (0.966–0.988): they were exported before the
  feeds were re-clocked on 2026-10-01.

## Not done

The full-scale run and its lines (encargo 44, K-m). Step 10 for the monkey. The exact delay of a
planted trade that a variant drops (`chain._delayed`). The dev draw of criteria.yaml
(`dev.sample`) is ignored on purpose — it is a development device, not a criterion.
