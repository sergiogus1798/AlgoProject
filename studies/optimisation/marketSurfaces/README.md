# marketSurfaces — is what is best on the main market also best on the others?

WORKFLOW step **18.5** — **off in the chain** (encargo 65 row 8, 2026-10-12): `pipeline/autopilot/tail.py` neither runs nor judges it and step 20 does not read it; it returns when the repricer's `descuadre < wfc.sqx_gap_relative`. The study stays and runs by hand. Rewritten on 2026-10-07 from the owner's
`criterios-implementados-2026-10-12.md`. It reads the variant batch of step 16.5, never talks
to SQX and never runs a backtest.

```
python3 -m studies.optimisation.marketSurfaces.report --work <batch> --family <f> [--oos2] [--out DIR] [--set a.b=v]
```

That a strategy wins on another market is weak evidence. That **the order of its variants** carries
over is not: a backtest's luck does not produce that. Per declared market *m* of
`assets/_markets.yaml`:

```
rho_m   = Spearman(gross excess on the main market, gross excess on m)   over the common variants
rho_bar = sum(w_m rho_m) / sum(w_m)                                       what decides
```

| file | what it does |
|---|---|
| `config.yaml` | every knob; the tuned ones point at `ledger/thresholds.yaml` (`marketSurfaces.*`) |
| `tooltips.py` | one Spanish sentence per knob, for the window's drawer |
| `one.py` | `legs` (which legs are read where), `measure` (the common sets, the readings, the reference) and `facts` (what the judge and step 20 read, and the state) |
| `report.py` | the command: asks the ledger's door, reads, measures, writes, logs the look |

| folder | the question it answers |
|---|---|
| `inputs/` | which markets, which variants, which weekly excess? |
| `measure/` | what are the numbers? |
| `verdict/` | what do they mean? |
| `contract/` | how is it read? |

## Two readings, one command

| reading | main market | other markets | when | what it can do |
|---|---|---|---|---|
| deciding | build+oos1 | build+oos1 | always | `perverso` → NO PASA; `sin_dato` → LIMBO |
| oos2 | build+oos1 | oos2 | only with `--oos2` (blind block) | `perverso` or `sin_dato` → LIMBO, nothing else |

Without `--oos2` no oos2 leg is asked of the parquet (`one.legs`, and the leg filter is pushed into
the read), the door is asked for build and oos1 only, and no `oos2.*` fact is written. The main
market's oos2 is never read by either reading.

## What is measured

- **Excess**: `engines.weekly.panel` reprices each market's trades on its own bars at its own cost
  card (`reprice.costs(feed, leg)`), minus the gate's drift (`studies/screening/gate/config.yaml`,
  `drift`). Gross (before costs) orders the variants; net prices the premium.
- **Usable on the main market**: not an exact duplicate (fingerprint of its `Main` trades over
  build+oos1, the mother first) and at or over both floors of `engines/variants/config.yaml`
  (`panel`). **Common set of m**: those that also reach `floor_oos_per_year` × the years m has data.
- **A market enters the mean** with at least `markets.min_common` common variants and at most
  `markets.max_ties` of them tied (a variant is tied when another has exactly its gross excess).
- **Weights**: 1, or 1 shared among the members of a `near_identical` group that enter the mean.
- **Null** (`engines.weekly.flip`): one sign per week, the same for every variant and every other
  market; the main market is never flipped. `p_mas`, `p_menos`, `nulo_p5`, `nulo_p95` are its tails.
  The weeks are the main asset's leg windows on every market; the week two legs share takes one sign.
- **Premium**: the top `premium.top_share` of the usable variants by NET excess on the main market;
  per market (median of the top − median of all) / IQR over its common set; the weighted mean over
  the same markets, against the same signs applied to the net panels. At or under
  `premium.percentile` of that null → LIMBO.
- **Reference**: Spearman of the main market's build against its oos1; the ratio rho_bar / rho_auto
  is written only when rho_auto exceeds `reference.min_rho`. Annotated.
- **Power**: for each rho* of `power.rhos`, `power.draws` no-edge draws of every included market (the
  real weeks under fresh signs), their normal scores mixed with the main market's as
  r·x + sqrt(1−r²)·z, r = 2 sin(π rho*/6) (a Gaussian pair of Pearson r has Spearman rho* exactly);
  the share whose joint rho the real family's null reads positive. Annotated.
- **Weekend straddle**: when more than `null.straddle_max` of the other markets' trades close on a
  Monday or Tuesday after an open weekend, the deciding order is drawn again with two-week blocks
  (`orden.estado_2sem`, a warning). It does not change the state.

## Facts (`marketSurfaces.<...>` once flattened)

`orden.estado` (positivo / neutro / perverso; **absent** when there is no data), `orden.{rho, p_mas,
p_menos, nulo_p5, nulo_p95, mercados (sum of weights), n_mercados, finde, estado_2sem}`,
`prima.{valor, nulo_p5, bajo_p5}`, `auto.{rho, cociente}`, `potencia.{r01, r02, r03}`, `variantes`,
`duplicados`, `costes.descuadre`, and with `--oos2` only `oos2.{rho, p_mas, p_menos, mercados,
sin_dato, perverso (absent when sin_dato = 1)}`. State: `fail` on a perverse deciding order; `watch` without data, with a low premium or
with a perverse or unreadable oos2; else `pass` («la zona viaja» when positive, «no descarta» when neutral).

## What it writes, in `<batch>/estudios/`

`marketSurfaces.json` (small: envelope, summary, facts, four light tabs; `.html` and `.md` from the
same dict), `marketSurfaces_detalle.json` (the grids, loaded by nobody who decides), `mercados.csv`,
`verdict.csv`, `distribuciones.parquet` (the joint order's and the premium's nulls per reading). `summary.segundos` is the run's time.

## Readings chosen where the proposal left room — open questions for the owner

1. **«Fewer than 5 markets (with weights)»** is read as the SUM OF WEIGHTS under
   `markets.min_weight` (the US trio counts 1), not the count of markets.
2. **The power's planted family** is the Gaussian-copula mix above, judged against the real family's
   null. A weekly lean added to the panels would be the other reading; it needs a scale per market.
3. **The top** is one set, picked on the main market's net excess among its usable variants, then
   intersected with each market's common set — not a top re-picked per common set, nor by gross.
4. **Ties** are exact equality of the gross excess, counted as the share of variants with a twin.
5. **Duplicates** are told on the main market's build+oos1 trades only, so the deciding reading
   never opens oos2.
6. **An oos2 reading without data** writes `oos2.sin_dato = 1` and NO `oos2.perverso` (owner, 2026-10-08): it was run and could not be read, which is LIMBO, not a pass. With data: `sin_dato = 0` and `perverso`.
7. The proposal's per-year scaling is not applied: a rho and an IQR-scaled premium do not move with it.

Not run on a real batch: on 2026-10-07 no `variant_trades.parquet` existed under the data root. The
code is checked on synthetic panels only (`tests/test_marketsurfaces.py`); measured there, 500
variants × 11 markets × 620 weeks × 2,000 draws take 18 s (28 s with `--oos2`), reading excluded.
