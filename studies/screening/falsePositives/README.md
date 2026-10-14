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
| `chain.py` | The chain's own criteria applied to a population's facts, step by step: who is left. | imported | trades → facts → funnel, per-rule counts |
| `inputs.py` | What the control runs on: its knobs, the real population's harvest, and the chain's rules. | imported | project + databank + feed (+ folder) → harvest, rules |
| `many.py` | The control: a null population and the same one with a planted edge, through the chain, beside the real one. | imported | harvest → result |
| `model.py` | What a monkey strategy is: one real strategy's footprint, its entries handed to chance. | imported | donor trades + bars → monkey trades, curve; per-trade table + edge → planted table |
| `report.py` | The chain's false-positive control: monkeys on a real population's footprint, step by step. | `python3 -m studies.screening.falsePositives.report --project P --databank Results --feed USA500_M1 [--harvest <folder>] [--seed N] [--criteria file.yaml] [--ledger] [--set population.per_level=500]` | harvest → reports |
| `tooltips.py` | One sentence per config.yaml knob, for the window's configuration drawer. | imported | — |
| `config.yaml` | The knobs: monkeys per donor, the rung, the sizing, strategies per population and the planted edges. No threshold lives here | edited, or `--set population.per_level=500` | — |

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

**The planted edge** (`model.planted`) is **net of costs** (owner, 2026-10-07): a population
labelled 0.15 answers «if a strategy earns 0.15 after costs, does the gate see it?». Every oos1
trade of a monkey gains one constant: `edge x the sd of that monkey's excess` plus `that monkey's
mean cost per trade`. The series is level 1a's `excess` — the repricer's P/L after the declared
costs, minus the drift term — which is what R3's `drift_excess_t` is the t of. Three things
follow, and each moves how a rate is read:

- **The cost is paid back on average, the luck is kept.** The monkey's expected net excess per
  trade becomes `edge x sd`; its own draw still scatters around it, so the plain t is
  `edge x sqrt(n)` plus a standard normal, not a fixed number. The null population is not
  planted and keeps paying. 🔬 2026-10-07, synthetic driftless walk, 196 oos1 trades of 1 to 5
  bars, 1,000 monkeys, a spread worth 0.83 of t (`tests/test_false_positives.py`): R3
  (`drift_excess_t >= 1.65`) passes **0.9 %** of the null population, **13.2 %** of the 0.05
  one, **33.8 %** of the 0.10 one and **62.0 %** of the 0.15 one; with no cost charged the null
  is 4.1 % and the planted three the same (13.2 / 33.8 / 62.1 %). The textbook 5 % and 67 % are
  the plain t's: the gate's t is at the AR(1) effective n over the skewness-and-kurtosis error,
  which only shrink it (the 0.15 lift is 2.01, not 0.15 x 14 = 2.1; with holds up to 40 bars,
  whose trades overlap, it was 1.89 and 58 %). On real populations a no-edge strategy crosses
  R3 4.05 % gross and 0.87 % net (`knowhow/research/gate-t-scales.md`).
- **Against the gate's own monkey the planted strategy is ahead by the cost too**: that monkey
  pays, so `z_mono` rises by (edge + mean cost / sd) x sqrt(n) — 🔬 2.92 in the run above, 2.11
  with no cost.
- **It is a constant per trade, so it does not depend on the fill**: the one-bar delay keeps it
  whole. Level 2 reprices the moved trade from the bars, so `chain._delayed` adds the plant back
  to the moved mean and takes `retraso_t_delta` from the table before the plant (exact unless a
  variant drops trades shorter than its shift).
- **The four rungs of level 3c share their random entries** (N12 B, 2026-10-13; `knowhow/research/rungs-share-random-entries.md`): one stream per strategy, a rung differs by its treatment alone; results stored before it are not comparable draw for draw.
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

Two runs of this study with the same seed and a different `monkeys.rung` share their uniforms (the rung is not in the stream key, `simulate.TAG`): a comparison between them is paired, not independent, so an SE computed as if independent is overstated (conservative).
