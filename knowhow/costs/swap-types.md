---
q: SQX swap types points percent money formula; percent swap annual or nightly 360; convert points to percent; triple swap day per feed WEDNESDAY FRIDAY; tripleSwapOn override asset file
tag: 🔬  date: 2026-09-23  see: costs/per-task-costs, costs/where-the-spread-is
---
# `percent` swap is an ANNUAL rate (÷100 ÷360); the triple-swap day is per feed
- One night × nights held (3 on the triple day). `pct_annual = points × tick_size × 36000 / reference_price` (dropping the 100 → 100× too small, still plausible).
- `tripleSwapOn`: WEDNESDAY for FX, XAUUSD, XAGUSD; FRIDAY for BRENT, DJ30, NIKKEI225, USA500, USATEC — these override via a top-level `swap:` in their asset file.
- ⚠️ An asset-file `swap:` replaces the policy block wholesale (`core.assetdata.load` = `{**policy, **asset_file}`): repeat `rollout_hour`.

## Evidence
📓 `SwapTypes` = `points`, `percent`, `money`. Master: `points` on every FX pair and gold, `money` on index CFDs. `SwapCalculator.calculateSwapCost`:

| type | one night |
|---|---|
| `points` | `size × pointValue × tickStep × swap` |
| `percent` | `size × pointValue × openPrice × (swap / 100 / 360)` |
| `money` | `size × swap` |

- Gold `-73.42` pts long, tick 0.01, ref 3500 → 7.55 % annual; short `+38.76` → 3.99 %. Either way one night on one lot = $73.42 / $38.76.
- Per feed: WEDNESDAY 17 (every FX pair, XAUUSD, XAGUSD); FRIDAY 7 (`BRENTCMDUSD_ftmo`, `DJ30`, `NIKKEI225` ×2 feeds, `USA500` ×2, `USATEC`); NEVER 1 (`EURUSD_M1_dukas`, stale, unclaimed).
  Not: "all instruments share `tripleSwapOn="WEDNESDAY" rolloutHour="23:00"`". `assets/_policy.yaml` still declares `triple_swap_on: WEDNESDAY` once; the 5 files override; `load()` agrees with the master on all 19.
- Wrong day matters: triple = 3× one night; BRENT short alone −9.54 % annual.
- 🤔 Cleaner fix (not done): per-asset `triple_swap_on` in `_policy.yaml` next to the segments; needs a small `load()` change.
