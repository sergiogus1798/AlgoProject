# marketSurfaces — is the good region of parameters the same one on other markets?

Encargo 15 (sections A4 and B3 of the owner's `PARAMETER_SPACE_TESTS.pdf`). WORKFLOW step **18.5**:
same level as the WFC and the CSCV, it reads the variant batch of step 16.5 and its result joins the
blind read of step 20 (owner, 2026-09-26). It never talks to SQX and never runs a backtest.

That a strategy wins on another market is weak evidence — it may simply be long a correlated asset.
That **the same region of parameters** is the good one on two markets is not: a backtest's luck does
not produce that. So each variant of the batch, already retested on every market of
`assets/_markets.yaml`, gives one surface per market and segment, and between every pair (a, b):

```
rho_ab = Spearman(M^a, M^b) over the variants both keep        the order of the variants
J_ab   = |T^a ∩ T^b| / |T^a ∪ T^b|, T = top decile             the overlap of the best ones
```

`M` is **net profit per segment**, the metric the WFC reads (`engines/variants/panel.columns`), so
this rho and the WFC's speak about the same number. Ranks, so account currency and each market's
size of move drop out.

```
config.yaml ─▶ inputs ─▶ measure ─▶ verdict ─▶ contract
 every knob    cells per  rho, J,    pair       the four
               market and the three  states,    tabs
               segment    checks     the call
```

| folder | the question it answers | read its README before |
|---|---|---|
| `inputs/` | which cells, which markets, which costs? | touching the segment filter or the floor |
| `measure/` | what are rho, J and the checks? | touching the null or the dedupe |
| `verdict/` | what does a pair mean, and what does the mother get? | moving a threshold |
| `contract/` | how is it drawn? | adding a figure |

| file | what it does | run it | in → out |
|---|---|---|---|
| `one.py` | Every number of one batch (`measure`) and the contract's result of them (`result`, `run`) | imported — the window calls `run` | batch → result |
| `report.py` | **The command**: asks the ledger's door for each segment before opening anything, writes `marketSurfaces.json/.html/.md`, `pairs.csv`, `checks.csv`, `verdict.csv`, and one ledger row per segment | `python3 -m studies.optimisation.marketSurfaces.report --work <batch> --family <F> [--out <dir>]` | batch → reading + ledger |
| `tooltips.py` | One sentence per `config.yaml` knob, for the window's configuration drawer | imported | — |
| `config.yaml` | Segments, metric, top share and the three thresholds (registered in `ledger/thresholds.yaml`) | edited, or `--set key=value` | — |

Manual page, in Spanish: `docs/manual/09-optimizacion.pdf` (cap. 52-superficies-mercado). Known-answer test:
`tests/test_marketsurfaces.py`.

🔬 **What it costs**, measured 2026-09-26 on the three USDJPY batches (5,000 variants × 10 markets ×
2 segments, `equity_markets.parquet` 430-745 MB): **9-11 s wall, 2.2-2.4 GB peak RSS**. The 228 M-row
file is only read per (market, segment) with the filter pushed down, for the checks.

## The five things this module exists to get right

**`oos2` is never opened.** The segment is a parameter, default `build` and `oos1`, and
`report.py` calls `ledger.gate.allow(18.5, segment, symbol)` for each one before reading a byte;
the Parquet read carries the segment filter, so a reserved row is never materialised. Whether this
step should join the oos2 group is the owner's decision (BOARD, 2026-09-26), not a knob.

**All declared markets, always.** The markets come from `_markets.yaml`, fixed before anything was
looked at, and the call's denominator is their count. Nine were looked at; nine are reported.

**The costs are provisional, and every output says so.** On 2026-09-26 the nine pairs and USDJPY
carry SQX's factory defaults, commission zero (`core.assets`). The flag is read from
`assets/symbols/` on every run (`inputs.surfaces.provisional`) and opens the first tab, the verdict
and the warnings. A per-trade cost moves high-frequency variants most, so it can reorder a surface.

**Rows are not observations.** Two tuples that ran the same backtest count once (`core.surface`);
🔬 on two of the three batches only 36-45 % of the 5,000 variants carry a distinct result.

**Long-only net profit is partly exposure times the market's drift.** Two markets that drifted
apart rank the variants against each other by time-in-market alone. `rho_neutral` removes each
market's exposure from its own ranks; 🔬 23-1-46 `oos1`, USDJPY against AUDUSD, reads −0.87 raw and
much less without it. The call is on the raw rho (the WFC's metric); the table carries both.

## What it does not tell you

- **Anything about oos2**, by construction.
- **Whether the edge is real on the other market.** A shared region at provisional costs says the
  ordering travels, not that it pays: that is `studies/transfer/crossmarket/`.
- **Structural markets.** `_markets.yaml` has none for USDJPY; the nine are one macro family, so
  passing is the easy test and failing is the informative one.
