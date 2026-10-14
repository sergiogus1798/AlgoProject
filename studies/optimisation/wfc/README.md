# wfc — does what optimises well in sample predict what does well out of it?

Step 17. Its sibling `../cscv/` (step 18) asks the other question about the same grid; the two
read the batch through `engines/variants/`, with one trade floor and one split between them.

**Does in-sample performance predict out-of-sample performance?** One point per parameter
combination, in-sample excess per year against out-of-sample excess per year. A cloud that fills all four
quadrants means optimising in-sample buys nothing out of sample; a cloud on the rising diagonal
means the surface carries information and the in-sample ranking is worth trusting.

**The other question — is the way I pick parameters prone to overfitting at all? — is `../cscv/`.**

Reads one mother's batch (`metrics.parquet` and **`variant_trades.parquet`**, the trades of every
variant in every leg, from `sqx.variants.varianttrades`) and measures **three compositions** of the
split — `c1` = build+oos1 → oos2 (the one that decides), `c2` = build → oos1+oos2, `c3` = build →
oos2 (`engines.variants.panel.KEYS`; `build → oos1` alone is not read here). Per variant and window
the measure is the **excess** (the P/L minus the drift the market paid the position), per year, in
two readings from `engines/weekly/panel.py`: **gross** (before the commission, swap, spread and
slippage `engines/market/reprice.py` charged each trade from the asset's card) for the **order**,
**net** for the **level** and `R_sel`. Costs alone rank the variants alike on both sides — the ones
that trade more pay more inside and outside — and a sign flip turns a cost into a gain, so the
null cannot see it: hence the order before costs. One `estudios/wfc.{json,html,md}` (and `distribuciones.parquet`: the sign-flip nulls behind `p_mas`, `p_nivel`, `p_mas_bloque` per composition) per batch carries the
three, with `facts.c1`, `facts.c2`, `facts.c3`; only `facts.c1.estado` (`pasa` / `limbo` /
`no_pasa`) is judged by the pilot, and **step 17 cuts nothing** (`cut: null`: it writes a verdict
and a ledger row, it deletes no strategy). **Every read is a ledger row per segment** (step 17,
`launched_by: wfc`), and **oos2 is sealed**: `look.admit` → `ledger.gate.seal` refuses it unless
`criteria.yaml` has a rule for step 17 and a calibration record (`AlgoData/ledger/wfc_calibration.json`)
with `abre: true` exists for the same `criteria.yaml` entry (hash). `--family` names the template
family of the study id; asset and timeframe come off the batch.

```
config.yaml ─▶ inputs ─▶ measure ─▶ verdict ─▶ contract
 every knob    excess    rho, null,  order and   estudios/
               per year  the level   the state   wfc.*
```

| folder | the question it answers | read its README before |
|---|---|---|
| `inputs/` | what is the study run on? — the batch's trades as excess per year | touching the pricing or the drift |
| `measure/` | what are the numbers? | touching the rho, its null or the level |
| `verdict/` | what do they say? — the owner's table | touching a state |
| `contract/` | how is it read? — the three compositions as the contract's blocks | adding a figure or a table |

| file | what it does | run it |
|---|---|---|
| `one.py` | One mother's batch through step 17's three compositions: values, filters, numbers and the call. | imported |
| `report.py` | Step 17 over one mother's variant batch: the three compositions, the state, the ledger's looks. | `python3 -m studies.optimisation.wfc.report --work <dir> --family <F>` |
| `tooltips.py` | One sentence per config.yaml knob, for the window's configuration drawer. | imported |
| `config.yaml` | The deciding composition, the null (draws, weeks per block, the straddle warning), the «fuerte» label, the top's share, the tolerance of the SQX check; every number is a `ledger:` key, the floors are in `engines/variants/config.yaml` | edited, or `--set section.key=value` |
| `calibrate/` | How often the table says PASA of a family with no edge and NO PASA of one with a planted edge; writes the record that opens (or keeps shut) oos2 | `python3 -m studies.optimisation.wfc.calibrate` |
| `POSSIBLE_IMPROVEMENTS.md` | The modelling choices that had real alternatives, and what is still the owner's to decide | read before changing one |

## What it measures, and the table

- **Order** — Spearman's rho between the in-sample and the out-of-sample **gross** excess, against
  a **weekly sign-flip null** (`engines/weekly/flip.py`, `wfc.null_draws` = 2000): each out-of-sample
  week takes one random sign, the same for every variant, and every trade counts whole in the week
  it closes in, so the family keeps its dependence and loses its edge. `p+` and `p-` (cut
  `wfc.alpha`) class the order `positivo`, `perverso` or `neutro`; `fuerte` when rho passes
  `wfc.rho_strong`. When more than `wfc.straddle_warn` (10 %) of the outside trades close on a
  Monday or Tuesday after a weekend held open, the step warns and draws the null again in blocks
  of `wfc.straddle_block_weeks` (2): `p_mas_bloque`, `p_menos_bloque`, `orden_bloque`, annotated.
- **Level** — the out-of-sample median **net** excess of the in-sample top (`wfc.top_share`, 20 %,
  picked on net). **It wins when that median is above zero and beats its own null**: `p_nivel` —
  the share of the order's very weekly sign draws, applied to the **net** weekly panel, whose top
  median is at or above the observed one — at or under `wfc.level_alpha` (0.05; encargo 48,
  decisions 5 and 6; owner, confirmed 2026-10-08). One upper tail only: a median at or under zero
  is NO PASA however far under.
- **State** (`verdict/state.py`, pure): order × level.

| order \ top's median | > 0 and `p_nivel` ≤ α | > 0, `p_nivel` > α | ≤ 0 |
|---|---|---|---|
| positivo / neutro | PASA | LIMBO | NO PASA |
| perverso | LIMBO | LIMBO | NO PASA |
| sin dato (or under `wfc.min_variants`) | LIMBO | LIMBO | LIMBO |

PASA is a veto lifted, not a vote in favour (owner, 2026-10-07); step 20 translates it
(`closing/blindJoint/pieces.py`): PASA = no failure, NO PASA = failure, LIMBO = undecided.
Annotated beside, never deciding: the null in wider blocks, the rho without the trade
floors (`rho_sin_suelos`, deciding composition), the cloud's four quadrants (on net), the count per
filter, `descuadre_sqx`, the partial rho controlling for the number of trades
(`measure/order.partial`), the level with a drift taken from bars before oos2, and `R_sel` (the
share of the top's in-sample premium that survives, with its 5th and 95th percentiles in the same
null; «sin dato» when that premium is under `wfc.r_sel_min_gap` of the in-sample interquartile
range — provisional, owner not yet asked).

## Traps measured here, and the code is shaped around them

**«The median of the top is above zero» alone passes half of the families with no edge — hence
the level's null.** The median of a symmetric noise is above zero half the time, so without the
null a no-edge family is PASA 0.5 × (1 − α) of the time by construction. With it (300 families,
`tests/test_wfc_families.py`): PASA 0.03, LIMBO 0.48, NO PASA 0.49. The null moves families from
PASA to LIMBO only; NO PASA is untouched. Its price is paid in LIMBO: at Sharpe 0.5 and 2.75
years outside, up to 0.60 of the families with a planted edge wait there (`calibrate/`, whose
comparison column `_sin` is the table without the null). **The register of 2026-10-07 measured
this rule with a daily null**: see `calibrate/README.md`.
→ `knowhow/research/wfc-top-persistence-sign-flip-null.md`

**A flat edge traded at unequal frequencies fakes an order after costs, and, when the edge is
per trade, before them too.** 300 synthetic families, 120 variants trading 0.5 to 3 times a week,
no real order (`python3 tests/test_wfc_families.py`): with the same gross level per year for every
variant the order is «positivo» 3 % of the time on gross and 23 % on net; with the same gross
edge per trade, 75 % on gross and 30 % on net. Gross removes the cost artefact; it does not
remove «trades more, earns more», which the partial rho annotates.

**The dependence between variants moves the false-NO-PASA and LIMBO rates, not the no-edge PASA one.** Variants
that are copies of one another make the null wider (rho of a no-edge family spreads more), so a real
edge is harder to see; the false rate stays where the construction put it. The families of
`calibrate/` set the variants' own noise (`family.own_noise`) so that a no-edge rho has a deviation
of ~0.23–0.26, the real batches' (`knowhow/research/wfc-dependence-moves-missed-pass.md`).

**Exact duplicates are equal trade lists, not equal totals** (`engines/variants/fingerprint.py`,
over the legs read): two distinct variants that happen to total the same to the cent stay.

**A weekly panel's column sums to the variant's excess** (`engines/weekly/panel.weekly` asserts
every close falls inside the window); a drift variant `b` or `d` cannot take a `drift_span` outside
the trade's own year, `per_trade` refuses.

## What it does not tell you

A PASA says the in-sample order and the top did not fail out of sample on the window that was read;
it does not say the strategy will work going forward, and a batch has never been run end to end on
real data (OPEN.md, part V of encargo 48). The CSCV (`../cscv/`) judges the selection procedure
across the whole history, and the walk-forward matrix (`../wfm/`) the strategy itself. Read
`POSSIBLE_IMPROVEMENTS.md` before changing a modelling choice.
