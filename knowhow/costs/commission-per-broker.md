---
q: which broker commission is confirmed vs guessed; no_forex commission default Darwinex 0.005 percent whole workflow; gold silver crude commission by segment; forex commission most restrictive; commission method same build oos1 oos2; broker pct_now price_now; core.commission broker_pct; step 26 commission; weeklyReconciler commission
tag: 🔬  date: 2026-09-29  see: costs/commission-methods, costs/sqx-fx-costs, costs/darwinex-real-spread
---
# `commission.use` for a `no_forex` asset is Darwinex's own % in EVERY segment — no per-segment "max broker" pick
Owner, 2026-09-29, correcting the same day's earlier reading ("aplica el máximo de cada a la hora de buildear y testear", read as picking the broker that charges most separately in each segment): for a `no_forex` asset with commission confirmed (XAUUSD, XAGUSD, BRENT), the WHOLE SQX workflow — build and every retest, OOS through WFM and the variants — prices at **Darwinex's `PercentageBased 0.005 %`**, the same `{method, value}` in `build`, `oos1` and `oos2`. Forex stays 5 USD/lot `SizeBased` everywhere; indices stay 0 % — neither changes. Written the ordinary way: `core.assetwrite.set_cost(symbol, "commission", 0.005, why)` spreads the bare figure over the three segments in the class's own method (no_forex → `PercentageBased`). `core.commission.per_segment` (the per-segment "max broker" picker) is retired from this role — it no longer decides `use`.

Every asset still carries `costs.commission.brokers: {<name>: {method, value, unit, source, date, confirmed, note?}}`; `confirmed: true` only off the firm's own page or the owner's own statement (`source: "dueño, <date>"`), dated. These per-broker figures are for STEP 26 and `weeklyReconciler` only, never for `use`: each confirmed broker also carries `pct_now` (its own figure converted to a % of notional), `price_now` and `price_date`, refreshed weekly by `python3 -m core.commission --refresh` from **the newest bar `core.barstore` holds for the asset's own feed** (its `Close`, not a segment median — this is "what would this broker charge today", not a historical cost) and written through `core.assetwrite.set_brokers`. `core.commission.commission_pct(method, value, price, point_value)` is the conversion (`PercentageBased` returns its own value; `SizeBased` divides by the notional of one lot at that price); `core.commission.broker_pct(asset, broker)` is the one accessor that reads the stored `pct_now` back — step 26 (encargo 34, MT5 validation on each firm's feed) and `weeklyReconciler` (OPEN.md #78, not yet built) read commission through it; an SQX workflow task never does, it reads `costs.commission.use[segment]` instead.

## Evidence
`core/commission.py` (`commission_pct`, `broker_pct`, `refresh`, `python3 -m core.commission --refresh`); `core/assetwrite/__init__.py` `set_cost()` (bare-figure segment spread, the writer used for the Darwinex default); `core/assetwrite/brokers.py` (`set_brokers`, the only writer of the `brokers` table); `core/assetdata.py` `sqx_settings()` (`use("commission")[segment]`, unchanged); `core/assets.py` `broker_table()`/`report()` render the table under the commission line; `core/assetcheck.py` `pending()` blocks on ANY segment's `value` still `None`; `tests/test_commission_segments.py` (gold's `use.build == use.oos2`, the pct_now KAT: 8 $/lot at price 4000, contract 100 → 0.002 %).

**The owner's figures, 2026-09-29 (all `confirmed: true`, `source: "dueño, 2026-09-29"`), applied per class:**
- **FOREX, all ten pairs** — every broker at **5 USD/lot, SizeBased**, all three segments alike. Unchanged by this correction.
- **INDICES, DAX40/DJ30/NIKKEI225/USA500/USATEC** — every broker at **0 %, PercentageBased**, all three segments. Unchanged; `pct_now` is 0 % for all of them too (no bars synced for these five feeds yet, so `price_now`/`price_date` are `null` — a `PercentageBased` broker needs no price to convert).
- **GOLD/SILVER/CRUDE, XAUUSD/XAGUSD/BRENT** — Infinox **8 USD/lot SizeBased**, FTMO **0.0014 % PercentageBased**, Darwinex **0.005 % PercentageBased**. `use` is now Darwinex's `PercentageBased 0.005` in build/oos1/oos2 alike, on all three assets. Each confirmed broker's `pct_now` at the last close `--refresh` found (2026-09-29 or 2026-09-22, per feed):

| asset | broker | pct_now | price_now | price_date |
|---|---|---|---|---|
| XAUUSD | darwinex | 0.005 % | 4369.12 | 2026-09-22 |
| XAUUSD | ftmo | 0.0014 % | 4369.12 | 2026-09-22 |
| XAUUSD | fundednext | 0.0016 % | 4369.12 | 2026-09-22 |
| XAUUSD | infinox | 0.001831 % | 4369.12 | 2026-09-22 |
| XAGUSD | darwinex | 0.005 % | 66.639 | 2026-09-22 |
| XAGUSD | ftmo | 0.0014 % | 66.639 | 2026-09-22 |
| XAGUSD | fundednext | 0.0016 % | 66.639 | 2026-09-22 |
| XAGUSD | infinox | 0.002401 % | 66.639 | 2026-09-22 |
| BRENT | darwinex | 0.005 % | 100.044 | 2026-09-21 |
| BRENT | ftmo | 0.0014 % | 100.044 | 2026-09-21 |
| BRENT | infinox | 0.079965 % | 100.044 | 2026-09-21 |

Infinox's flat $8/lot reads as the cheapest of the three on gold and silver at today's price (it is what made it win `build` under the retired per-segment pick) and as by far the most expensive on Brent, whose price is too low relative to its point_value (100) for a flat $/lot figure to look small in percentage terms — exactly the comparison the retired per-segment logic used to make, now kept only for step 26/reconciliation and not for `use`.

**Superseded by this session**: the per-segment "max broker" pick (gold's `build` on Infinox `SizeBased 8.0`, `oos1`/`oos2` on Darwinex `PercentageBased 0.005`, `XAGUSD`/`BRENT` on Infinox `SizeBased 8.0` throughout, via `core.commission.per_segment` priced at each segment's own median price) is retired from deciding `use`; all three no_forex assets with commission now carry Darwinex's flat 0.005 % in every segment. The per-broker table and its per-segment median pricing remain accurate history, not `use`'s source any more.
