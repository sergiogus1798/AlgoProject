# oos2Reading — the single reading of oos2: does the mother beat her hours-restricted monkey there? (step 17 + 19, after both)

Encargo 65 §6; owner D2, 2026-10-12: the rules of 17 and 19 keep judging and this reading cuts in
addition — a mother survives only if she passes all three. It cuts **only by sign** (`z <= 0`); the
level `z` only orders the medoids. One look per cell (asset x timeframe x direction x family),
counted in `ledger.cells.look_oos2`; a cell with 3 looks is «solo vivo» and the 4th is refused
(exit code 3). Re-running the same project adds no look.

| file | what it does | run it | in → out |
|---|---|---|---|
| `inputs.py` | What the reading opens: the mothers' variant batches, their oos2 trades, the oos2 dates and her daily P&L. | imported | batch → trades, P&L |
| `measure.py` | The inference: a mother's weekly excess over her monkey, summed, against a centred sign-flip null. | imported | daily series → facts |
| `report.py` | The single reading of oos2: every mother of a project, one look in her cell, cut by sign only. | `python3 -m studies.optimisation.oos2Reading.report --project <P>` | project → facts |
| `tooltips.py` | One sentence per config.yaml knob, for the window's configuration drawer. | imported | — |
| `config.yaml` | Every knob: 100,000 flips (5,000 is the floor), alpha 0.05, seed, the monkey's draws, `max_looks` 3 | edited, or `--set` | — |
| (monkey) | The monkey's mean daily P&L comes from `engines/nulls/footprint.py`, shared with step 20 | — | — |

Test: `tests/test_oos2_reading.py`. Manual: cap. 110 (PDF `09-optimizacion`).

## Settled points (and where from)

- **Rail position:** after 17 and 19 (title «17 + 19»; `docs/encargos/65-consenso-cuatro-opiniones.md` §6).
  It is signed to the ledger's door as **step 19**: `assets/_policy.yaml` reserves oos2 for
  WFC/CSCV/MarketSurfaces/WFM/BlindJoint/ATRStop and `gate.seal` refuses any other number. Its
  rail step is **19.5** (owner, 2026-10-12): `criteria.yaml` `"19.5"`, `cut: SPP OOS`, rule `oos2Reading.z > 0`; the tail runs it (`oos2read`) right after 19 and exit 3 («solo vivo») is limbo, never a cut.
- **Trades:** the mother's own oos2 trades from her variant batch (`trades.parquet`, step 16.5's
  harvest), exactly as step 20 reads them; no SQX task is added.
- **Net excess:** her P&L minus the monkey's mean P&L (spread, slippage, commission and swap paid
  by every draw), i.e. drift already discounted; the same null family as step 8 but over the whole
  of oos2, as step 20's benchmark does, not step 8's calendar window.
- **Not checked here:** the reconciliation of the rebuilt daily P&L with SQX's own curve that step 20
  demands (`mother_low`); `closecurve` sums to her trades' Profit/Loss by construction.
