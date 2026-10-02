---
q: forex one spread vs no_forex spread_is spread_oos spread_oos2; AUDJPY only one spread; spread per segment every asset; slippage_oos2; _classes forex fields; segments_default oos2 spread; rename_cost spread spread_is
tag: 🔬  date: 2026-09-30  see: costs/darwinex-real-spread, costs/sqx-fx-costs
---
# Every asset carries spread and slippage for IS, OOS1 and OOS2 — forex included
Owner, 2026-09-30: forex used to declare one spread (the mean over build..oos2) while XAUUSD had
three; the real Darwinex spread of a pair also moves by segment. `_classes.yaml` forex now has
`spread_is`/`spread_oos`, `_policy.yaml` `segments_default.oos2.spread: oos2`, `assetdata.fields`
adds the `oos2` half for every class, and `studies.data.spread.onboard` writes one per segment for
every kind. Migration: `core.assetwrite.rename_cost(S, "spread", "spread_is")`, then
`onboard --spread-only --write`. BRENT has no Darwinex ticks: its OOS2 copies OOS1, said in `why`.

## Evidence
- 🔬 2026-09-30, measured (× 1.25): AUDJPY 1.61/1.27/1.92, EURUSD 0.54/0.45/0.49, USDJPY 0.49/0.59/
  1.16 (was one 0.65), GBPJPY 2.13/2.06/2.70. `core.assetdata.sqx_settings` now differs by segment
  for USDJPY: build 0.49, oos1 0.59, oos2 1.16. ⚠️ A migration half done breaks `reindex` (it walks
  every asset): rename all files first, then measure.
