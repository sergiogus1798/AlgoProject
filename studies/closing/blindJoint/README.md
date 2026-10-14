# blindJoint — step 20: the three withheld results read at once, and does the mother beat her own trades entered at random?

WORKFLOW step 20, encargo 10 part B. Steps 17 (WFC), 18 (CSCV) and 19 (18.5, market surfaces, is off: encargo 65 row 8, back when the repricer's `descuadre < wfc.sqx_gap_relative`)
(WFM) run one after another and **nobody reads them until all exist** (owner, 2026-09-23). This is
the reading: it opens the three through the ledger's door, puts each study's own call side by side,
and adds the question none of them asks — **does the mother beat a random trader with her own
footprint on `oos2`, with every mother that reached this step paid for** (Hansen's SPA, Romano and Wolf's StepM, the engine of
part A).

```
config.yaml ─▶ inputs ──────▶ pieces ─▶ measure ─────────▶ many / one ─▶ report
 every knob    the two doors,  what 17,  excess, SPA,       the contract  pages, verdict.csv,
               oos2 days, the  18, 18.5  StepM per reading  dicts         readings.csv,
               random traders  and 19    (readings)                       ledger row
               (benchmark)
                               said
```

| file | what it does | run it | in → out |
|---|---|---|---|
| `inputs.py` | What step 20 reads: its knobs, the ledger's two doors, the mothers' oos2 days and their random traders'. | imported | ledger + batches + feed → frame, panel, benchmark |
| `many.py` | Every mother that reached step 20, read as one result: the three pieces, the readings, the SPA. | imported | inputs → results |
| `measure.py` | The numbers of step 20: each mother against her random trader on oos2, the SPA, and the StepM per reading. | imported | inputs → p-values, named, calls |
| `one.py` | One mother at step 20: her three withheld results side by side, and her call under each reading. | imported — the window calls it | row → result |
| `pieces.py` | The three withheld results of each mother — 17, 18 and 19 — as their own studies said them. | imported | batches + WFM report → population |
| `readings.py` | The readings of "passes step 20" the spec leaves open, one entry each, for the owner to choose. | imported | states, named → calls |
| `report.py` | Step 20: the blind joint reading of 17, 18 and 19, with SPA and StepM on oos2, and its ledger row. | `python3 -m studies.closing.blindJoint.report --project USDJPY_workflow_profiling_v1 --wfm-databank WFM --feed USDJPY_M1 --symbol USDJPY --timeframe H1 --family crossAboveHMA_v1` | pieces + oos2 → reports + ledger row |
| `tooltips.py` | One sentence per config.yaml knob, for the window's configuration drawer. | imported | — |
| `words.py` | The words of another study's call, as the owner reads them: Spanish, sentence case, decimal comma. | imported by `one.py` | — |
| `config.yaml` | The benchmark's rung, draws and seed, the FWER (the ledger row part A reads), the two open decisions (`joint`), the bootstrap | edited | — |

Manual page, in Spanish: `docs/manual/10-cierre.pdf` (cap. 56-paso-20). Known-answer test:
`tests/test_blindjoint.py`. The engine: `engines/inference/snooping/`.

## What it decides, and what it leaves to the owner

**Unambiguous, built:** the door; which mothers are complete; each piece's state exactly as its
study wrote it; the mother's oos2 curve against the random trader of her own footprint (owner,
2026-10-11; it replaced equal-risk buy and hold); the SPA's three p-values and the StepM at the FWER of `ledger/thresholds.yaml`.

**Decided 2026-10-04 (P2):** `joint.population` is `entrantes` — the StepM's K is every mother
that entered step 20. **Still open, exposed rather than chosen (hard rule 11):** `joint.pieces` —
`unanimidad`, `sin_fallo` or `ninguna`. While it is null the study computes the call under **every** reading, shows them side by side, writes MANTENER for all
(as part A annotates) and, if it read oos2, a soft ledger row. With both set, `verdict.csv` says
DESCARTAR for a mother that reading drops.

**Not its call, the policy's:** `assets/_policy.yaml` reserves oos2 for WFC, MarketSurfaces, WFM
and ATRStop. Step 20 is not listed, so today the SPA half is **not read** and nothing is spent:
the report says so, the pieces are still read (they open no raw segment), and no ledger row is
written. The word the owner would add is `BlindJoint` (`ledger/gate.py` `STEPS`). A chosen
reading that uses the StepM raises while the policy refuses oos2 (`report.need_stepm`).

**Owner, 2026-10-12: nobody is discarded at step 20.** `joint.pieces: null`, so no reading is chosen,
every row is `MANTENER` and `verdict_csv.drop` is 0 (the rule in `criteria.yaml` stays and finds
nothing to cut). The step is a summary: the StepM and the SPA are a diagnostic, and the `REVISAR`
label stays in `report.VERDICT`. The `peor` reading («the worst state wins») was removed. `sin_fallo`,
`unanimidad` and `ninguna` remain selectable and are shown side by side in `readings.csv`.

## The benchmark: the mother's own trades, entered at random (owner, 2026-10-11)

**What it is.** For each mother, `benchmark.draws` traders who each take *her* oos2 trades — the
same count, the same side, the same lots, each trade's own holding time, the same declared
costs — at entry bars drawn uniformly over oos2, at the hour of the trade they replace. The benchmark is their **mean** P&L per day,
and the excess the SPA reads is the mother's day minus that mean. In plain words it is what the
market pays for being in it that long, on that side, at that size: 🤔 away from the edges of the
segment it is buy and hold at the mother's *time-averaged* lots, minus her costs. So it discounts
the asset's drift without asking her to beat a leveraged long, which is what equal-risk buy and
hold did (a strategy in the market 7 % of the time was held against a position sized to be as
volatile as she is).

**The null hypothesis of step 20.** *No mother that reached step 20 has an expected daily oos2
P&L above that of her own trades entered at random*: `E[mother_k − random_k] ≤ 0` for every k.
«Beating it» is the SPA rejecting that (one p for the family) and the StepM naming her (FWER of
the ledger). The null is **conditional on her footprint**: how many trades she made, how long she
held and at what size in oos2 are given to the null, so only *when she entered* is tested — the
ladder's `timing` rung, the monkey study's headline. Read on oos2 only, never on the in-sample
(owner, 2026-09-29; `knowhow/research/random-trader-oos-only.md`).

**One generator, one repricer.** The draws are `engines.nulls.model.RUNGS[benchmark.rung]`, the
ladder the monkey study reads, with two things changed on purpose and neither in the engine: the
window is the whole of oos2 rather than her first trade to her last, and the bars are M1, the
grid the mother's panel is marked on. The pricing is `engines.market.reprice.pnl` at
`reprice.costs(feed, "oos2")`, not the ladder's `calibrate.charged`, which holds no spread and no
slippage: in the monkey study that cancels (the real run is repriced the same way), here the
mother's side is SQX's own P&L, so an under-charged benchmark would be a bar she pays twice.
The ladder's kernel returns five statistics per run and no days; the mean needs none of them —
it is linear, so `footprint` prices the traders' average position per M1 bar and marks it at each
day's last M1 close, as the mother's panel is.

**Does the SPA still hold?** Yes, with one approximation that is measured. The SPA needs the
excess series stationary and weakly dependent; the benchmark is a smooth function of the same
price path buy and hold was, so nothing changes there. What is new is that the mean is
simulated: its Monte Carlo error is a fixed offset the bootstrap does not resample. One trader's
total is about as volatile as the mother's own, so the offset's standard deviation is
`1/sqrt(draws)` of the mother's standard error: at `draws: 2000`, **2.2 %** of it (🔬 1.2 %
median, 1.5 % worst, over 300 synthetic mothers of 150 trades) — 0.05 % more variance than the
SPA studentizes by, a t moved by less than 0.05. It is printed per mother (`mc_day`, «error
simulación»). Draws are seeded (`benchmark.seed`), so a rerun gives the same benchmark.

**Looks.** None added: the benchmark reads the mothers' oos2 trades and the feed's M1 bars,
which `inputs.panel` already opens behind `gate.allow(20, "oos2")`, and the asset card. When
the policy or the trades door refuses, it is not computed. The step-20 ledger row carries the
benchmark's rung, draws and seed.

**Known limits, the ladder's own** (`engines/nulls/README.md`): the random trades may overlap
where the mother's never do; her lots are kept as they were, carrying the volatility of her real
entries. Entries are uniform over every M1 bar of oos2 **at the clock hour of the trade each replaces** (the hours null, `engines.nulls.windowed`, owner 2026-10-12; lots stay hers). The
costs are the asset card's for oos2 — a card recalibrated after the retest moves the benchmark
by the difference.

## The four things this module exists to get right

**Blind by construction.** `inputs.blind_door` raises unless the study's ledger has rows for 17,
18 and 19 — presence in the ledger is what "ran" means. ⚠️ Those three studies do not write rows
themselves (`knowhow/pipeline/blind-steps-write-no-ledger-rows.md`); `python3 -m ledger.backfill
--blind <project>` rebuilds them from their results, marked `backfill`.

**A piece's threshold lives in its study.** Only the small result is opened
(`<batch>/estudios/<study>.json`, the WFM's page), never a study's heavy detail. The state is read from each result's `verdict`
block — WFC `no_fiable`/`indeciso`/`fiable`, CSCV PBO over 0.5, surfaces `no viaja`/`a medias`/
`viaja`, WFM `perverse`/`blind`/`predicts`. Step 20 moves none of them.

**The mother's own days, and only oos2.** The mother is the `origin` variant of her batch, whose
`equity.parquet` joins build, oos1 and oos2 on daily increments. 🔬 Each leg opens with two months
of zero-P&L warm-up repeating the previous leg's dates, and the leg is not recorded
(`knowhow/sqx-format/leg-curve-warmup.md`); oos2 from its policy start is clear of them, and a cut
that catches a duplicated date raises. 🔬 That curve is each day's LOWEST equity, not a mark to
market, so since 2026-10-04 it is only the known answer: the panel is the close-to-close P&L rebuilt
from the mother's oos2 trades and the M1 bars (`portfolio/common/construct/equity/closecurve`, as
part A), and it is refused unless its own daily lows match the curve. The trades are read from
`trades.parquet` in the batch folder (schema T plus `variant_id` and `segment`), which step 16.5 writes
for the mother only since 2026-10-04 (`sqx/variants/mothertrades.py`; decision E3, owner: «solo para
la madre»). A batch made before that has none: `inputs.trades_door` refuses, and with a chosen
reading the report stops. 🔬 2026-10-04, first real oos2:
NIKKEI225 M30, 10 mothers, the rebuilt panel reconciled with SQX's curve and the report ran whole (known
answer on synthetic data: `tests/test_close_curve.py`).

**The StepM is written on `arch`'s SPA**, not `arch`'s `StepM`, which raises when its rounds
name every column between them — never at part A's K = 200, often at step 20's K of 2 to 5.

## What it found the first time (2026-09-26, `USDJPY_workflow_profiling_v1`)

| mother | 17 WFC | 18 CSCV | (18.5 off) | 19 WFM | every reading using the pieces |
|---|---|---|---|---|---|
| Strategy 1.28.59 | indeciso · watch | PBO 9 % · pass | no viaja · fail | blind · watch (SQX area filter FAILED) | NO PASA |
| Strategy 1.29.55 | no fiable · fail | PBO 15 % · pass | no viaja · fail | perverse · fail | NO PASA |
| Strategy 1.23.51 | — | — | — | (unread) | INCOMPLETA |

Same as the hand reading of `docs/AgentPDFs/profiling-workflow-2026-09-26.md` §4.7: neither
passes, under any reading of the pieces — the surfaces fail both. The StepM half is unread
(policy). 🔬 The two mothers carry the same five parameters and 98.8 % of their oos2 days have
identical P&L (ρ 0.978): K = 2 on paper, one strategy in fact.
