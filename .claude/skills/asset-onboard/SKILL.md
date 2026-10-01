---
name: asset-onboard
description: Add a new asset to assets/ with its whole cost card worked out from data — Darwinex's real spread per segment (measured, modelled back where there are no ticks), slippage at half of it, the owner's default commission and swap for its kind, the triple-swap night, and the MC Retest spread range from the real dispersion. Also refreshes the spreads of an existing asset. Use when the owner says "haz lo mismo para el cruce/índice/metal XXX", asks to add, create or onboard an asset, or asks to compute an asset's spread, slippage, commission or swap.
---

# /asset-onboard

The cost «mini-study» of 2026-09-27 (`docs/AgentPDFs/spread-real-2026-09-27.pdf`), as one run.
Everything the conversation decided is data in `studies/data/spread/config.yaml`, under
`onboard:` and `safety:`. **Never re-derive a rule here; if the owner changes one, change the
config.**

## The owner's rules it applies (2026-09-27)

| | index | metal | forex |
|---|---|---|---|
| segments | build from the first day of data to 2019, oos1 2020–2023, oos2 2024–31/08/2026 | build 2008–2017, oos1 2018–2022, oos2 2023–30/08/2026 ⚠️ | same as metal |
| spread | mean Darwinex spread of each segment × 1.25, one per segment (`spread_oos2` its own) | same | same — one per segment since 2026-09-30 (owner) |
| build without ticks | **proportional to price** (`relativo`) | the best-validated model | best-validated |
| slippage | half the spread of its segment | same | same |
| commission | 0 | 8 USD/lot round trip → % of notional at Darwinex's last price | 8 USD/lot |
| swap | worst of FTMO and Hantec per side, live from MT5 (`fundedswap`, owner 2026-10-01): % annual | same | same, in SQX points |
| triple swap | FRIDAY | WEDNESDAY | WEDNESDAY |
| MC Retest spread | quantiles 2.5–97.5 % of measured day ÷ model mean, × the build spread | same | same |

⚠️ The metal/forex segments are gold's and the pairs' as they were; the owner did not restate them.

## Ask first — hard rule 11

Stop and ask, never pick, when:

- **The kind is not obvious.** A commodity (Brent, gas) or a stock is none of the three: its
  commission and swap are the owner's to name. Add a kind to the config only after he answers.
- **There are several feeds.** `registry.feeds()` lists every `<SYMBOL>_DukasM1_*` and
  `<SYMBOL>_DarwTick_*` in SQX (AUDJPY has the5ers and icmarkets). Ask which broker.
- **There is no DarwTick feed.** Without ticks there is no spread to measure; say so and stop.
- **The asset already exists.** Then ask whether to refresh only spreads and slippage
  (`--spread-only`, the default for an existing asset) or everything, commission and swap
  included, which overwrites what the owner set by hand.

## Run it

```bash
python3 -m studies.data.spread.onboard --symbol EURGBP --kind forex            # 1 · plan, writes nothing
python3 -m studies.data.spread.onboard --symbol EURGBP --kind forex --write    # 2 · after the owner says yes
python3 -m studies.data.spread.scan --symbol EURGBP                             # 3 · the asset's report
python3 -m studies.data.spread.bands --symbol EURGBP                            # 4 · the spread band vs price
python3 -m core.assets EURGBP                                                   # 5 · preflight, hard rule 5
```

- **Step 1** takes 15–40 s the first time (it decodes the tick file) and prints the whole card.
  **Show it to the owner and wait for a yes** before step 2.
- **Step 2** creates `assets/symbols/<SYMBOL>.yaml` through `core.assetwrite` and its
  `_policy.yaml` block, and registers the feeds in the study's `config.yaml`.
- **Step 5** has to pass. What it can still block on:
  - **session: null.** The builder borrows the session from a project that holds it
    (`knowhow/costs/sessions-per-asset.md`), and refuses when none does.
  - A market missing from `_markets.yaml`.
- **Then its `mt5:`** — the asset's symbol at each prop firm (`ftmo`, `hantec`), read from each
  terminal (`mcp__mt5__mt5_symbols`), never guessed: `core.assetwrite.set_value(<S>, ["mt5"],
  {...})`. Without it MT5 Bridge › Verificar refuses that firm (owner, 2026-09-30: it moved here
  from the git-ignored `mt5/symbols.csv`).

Say both in the report.

## What to report

The card, in Spanish, as a table: the spread per segment and what was declared, slippage,
commission, swap, triple swap, MC Retest range in points and in multiples, and the model used for
the build with its validation error. Then:

- **Every value that was a default, not a measurement:** commission, swap, the metal/forex windows.
- **A thin MC Retest range:** SQX draws on 0.1-point steps (`knowhow/costs/mc-retest-ranges.md`),
  so a range under ~5 steps gives few distinct runs.

End as every task ends: the files changed, then **¿Quieres hacer el commit?**

## What it never does

- Write `assets/` without `--write`, or without the owner having seen the plan.
- Touch SQX: it reads `data.db` and the History `.dat` files read-only, with the master up or down.
- Invent a commission or swap for a kind the config does not know.
