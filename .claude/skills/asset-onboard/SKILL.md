---
name: asset-onboard
description: Refresh the spread and slippage of existing assets by the funded-firms method (owner, 2026-10-14) — the widest funded firm's time-weighted % of price times each segment's mean price, slippage at 35 % of it, written through core.assetwrite. Darwinex is no longer read. Use when the owner asks to compute or refresh an asset's spread or slippage.
---

# /asset-onboard

The method is `studies/data/spread/funded.py`, the rules `assets/RULES.md` (lines 95-103). Everything
the owner decided is data in `studies/data/spread/config.yaml` under `safety:`. **Never re-derive a
rule here; if the owner changes one, change the config.**

The Darwinex path (segments, commission, swap and spread from Darwinex ticks, new-card creation) was
deleted on 2026-10-14 (owner, encargo 59, rule 21). Consequence: **this command only recomputes
spreads and slippage of cards that already exist, from the firms' ticks.** A new asset's card
(class, broker, instrument, segments, commission, swap, triple swap) has no command today — ask the
owner how to create it before doing anything (hard rule 11), then run the steps below.

## Ask first — hard rule 11

Stop and ask, never pick, when:

- **The asset has no card.** Say so; creating it by hand is the owner's call.
- **The asset has no firm ticks** (`AlgoData/INDEX.md`). `funded.plan` prints why and skips it.
- **The kind is not obvious** for a new card: a commodity or a stock has no default commission or swap.

## Run it

```bash
python3 -m studies.data.spread.onboard --symbol EURGBP           # 1 · plan, writes nothing
python3 -m studies.data.spread.onboard --symbol EURGBP --write   # 2 · after the owner says yes
python3 -m studies.data.spread.scan --symbol EURGBP              # 3 · the asset's report
python3 -m core.assets EURGBP                                    # 4 · preflight, hard rule 5
```

Without `--symbol` it does every card. **Show the plan to the owner and wait for a yes** before step 2.
Step 4 has to pass; it can still block on `session: null` (`knowhow/costs/sessions-per-asset.md`) or
a market missing from `_markets.yaml`. A card also needs its `mt5:` — the symbol at each firm, read
from each terminal (`mcp__mt5__mt5_symbols`), never guessed (`core.assetwrite.set_value(<S>, ["mt5"], {...})`).

## What to report

The card in Spanish, as a table: spread per segment, slippage, the firm that was widest. Then
the files changed and **¿Quieres hacer el commit?**

## What it never does

- Write `assets/` without `--write`, or without the owner having seen the plan.
- Touch SQX, or write a commission, swap or segment: they are not this command's any more.
