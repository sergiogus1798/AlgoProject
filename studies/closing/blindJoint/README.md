# blindJoint — step 20: the four withheld results read at once, and does the mother beat buy and hold?

WORKFLOW step 20, encargo 10 part B. Steps 17 (WFC), 18 (CSCV), 18.5 (market surfaces) and 19
(WFM) run one after another and **nobody reads them until all exist** (owner, 2026-09-23). This is
the reading: it opens the four through the ledger's door, puts each study's own call side by side,
and adds the question none of them asks — **does the mother beat buy and hold on `oos2`, with every
mother that reached this step paid for** (Hansen's SPA, Romano and Wolf's StepM, the engine of
part A).

```
config.yaml ─▶ inputs ──────▶ pieces ─▶ measure ─────────▶ many / one ─▶ report
 every knob    the two doors,  what 17,  buy & hold, SPA,   the contract  pages, verdict.csv,
               oos2 days,      18, 18.5  StepM per reading  dicts         readings.csv,
               the asset       and 19    (readings)                       ledger row
                               said
```

| file | what it does | run it | in → out |
|---|---|---|---|
| `inputs.py` | The knobs, the blind door (`ledger.gate.allow_read`), the oos2 door (`gate.allow(20, "oos2")`), the mothers' own oos2 days from their batches, and the asset's moves | imported | ledger + batches + feed → frame, panel, moves |
| `pieces.py` | Which mothers reached step 20, and what WFC, CSCV, surfaces and WFM said of each — their own state, never re-derived; a mother missing one is listed and never read | imported | batches + WFM report → population |
| `benchmark.py` | Buy and hold sized to each mother's own daily volatility, and the excess over it (copied from part A) | imported | panel + moves → excess, lots |
| `readings.py` | **The open decisions as a registry**: how the four pieces combine, and over whom the StepM counts its search | imported | states, named → calls |
| `measure.py` | The excess panel through the SPA and a StepM per reading, one row per mother | imported | inputs → p-values, named, calls |
| `one.py` | One mother as the contract's data: her four pieces as parts, her call under every reading | imported — the window calls it | row → result |
| `many.py` | The population: the pieces grid, the readings grid, the SPA tab | imported | inputs → results |
| `report.py` | **The command**: writes `reports/<P>/<WFM>/<day>/blindJoint/` and, when it read oos2, a step-20 ledger row | `python3 -m studies.closing.blindJoint.report --project USDJPY_workflow_profiling_v1 --wfm-databank WFM --feed USDJPY_DukasM1_the5ers --symbol USDJPY --timeframe H1 --family crossAboveHMA_v1` | pieces + oos2 → reports + ledger row |
| `tooltips.py` | One Spanish sentence per `config.yaml` knob | imported | — |
| `config.yaml` | The benchmark's sizing, the FWER (the ledger row part A reads), the two open decisions (`joint`), the bootstrap | edited | — |

Manual page, in Spanish: `docs/manual/10-cierre.pdf` (cap. 56-paso-20). Known-answer test:
`tests/test_blindjoint.py`. The engine: `engines/inference/snooping/`.

## What it decides, and what it leaves to the owner

**Unambiguous, built:** the door; which mothers are complete; each piece's state exactly as its
study wrote it; the mother's oos2 curve against equal-risk buy and hold (the owner's benchmark
for part A, kept); the SPA's three p-values and the StepM at the FWER of `ledger/thresholds.yaml`.

**Open, exposed rather than chosen (hard rule 11):** `joint.pieces` — `unanimidad`, `sin_fallo`
or `ninguna` — and `joint.population` — `supervivientes` or `entrantes`. While either is null the
study computes the call under **every** reading, shows them side by side, writes MANTENER for all
(as part A annotates) and, if it read oos2, a soft ledger row. With both set, `verdict.csv` says
DESCARTAR for a mother that reading drops.

**Not its call, the policy's:** `assets/_policy.yaml` reserves oos2 for WFC, MarketSurfaces, WFM
and ATRStop. Step 20 is not listed, so today the SPA half is **not read** and nothing is spent:
the report says so, the pieces are still read (they open no raw segment), and no ledger row is
written. The word the owner would add is `BlindJoint` (`ledger/gate.py` `STEPS`). A chosen
reading needs the StepM, so choosing one while the policy refuses oos2 raises.

## The four things this module exists to get right

**Blind by construction.** `inputs.blind_door` raises unless the study's ledger has rows for 17,
18 and 19 — presence in the ledger is what "ran" means. ⚠️ Those three studies do not write rows
themselves (`knowhow/eng/blind-steps-write-no-ledger-rows.md`); `python3 -m ledger.backfill
--blind <project>` rebuilds them from their results, marked `backfill`.

**A piece's threshold lives in its study.** The state is read from each result's `verdict`
block — WFC `no_fiable`/`indeciso`/`fiable`, CSCV PBO over 0.5, surfaces `no viaja`/`a medias`/
`viaja`, WFM `perverse`/`blind`/`predicts`. Step 20 moves none of them.

**The mother's own days, and only oos2.** The mother is the `origin` variant of her batch, whose
`equity.parquet` joins build, oos1 and oos2 on daily increments. 🔬 Each leg opens with two months
of zero-P&L warm-up repeating the previous leg's dates, and the leg is not recorded
(`knowhow/sqx-format/leg-curve-warmup.md`); oos2 from its policy start is clear of them, and a cut
that catches a duplicated date raises. The last day is dropped, as SQX marks an open position there.

**The StepM is written on `arch`'s SPA**, not `arch`'s `StepM`, which raises when its rounds
name every column between them — never at part A's K = 200, often at step 20's K of 2 to 5.

## What it found the first time (2026-09-26, `USDJPY_workflow_profiling_v1`)

| mother | 17 WFC | 18 CSCV | 18.5 surfaces | 19 WFM | every reading using the pieces |
|---|---|---|---|---|---|
| Strategy 1.28.59 | indeciso · watch | PBO 9 % · pass | no viaja · fail | blind · watch (SQX area filter FAILED) | NO PASA |
| Strategy 1.29.55 | no fiable · fail | PBO 15 % · pass | no viaja · fail | perverse · fail | NO PASA |
| Strategy 1.23.51 | — | — | — | (unread) | INCOMPLETA |

Same as the hand reading of `docs/AgentPDFs/profiling-workflow-2026-09-26.md` §4.7: neither
passes, under any reading of the pieces — the surfaces fail both. The StepM half is unread
(policy). 🔬 The two mothers carry the same five parameters and 98.8 % of their oos2 days have
identical P&L (ρ 0.978): K = 2 on paper, one strategy in fact.
