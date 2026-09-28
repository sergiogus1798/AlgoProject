# ui/daemon/tearmarket — the strategy against its market, and five of its trades

Two routes of the Estrategia «Ficha» (order items 5 and 6, 2026-09-27). Both read one
`(project, databank, identity)` in the newest harvest of that databank, with a pyarrow filter on
`identity`, and the asset's bars through `core.barstore.read` at the strategy's timeframe
(`metrics.parquet` `TimeFrame [IS]`).

```
api ─▶ source.newest · described · rows (equity | trades, filtered) · market (runs.context → feed) · bars (cut at oos1)
    ├▶ months.result   → contract dict (tabs IS, OOS: table 2×2 + bars, both-down in `watch`)
    └▶ trades.gallery  → five tiles, each with its bar window
```

**Imports from:** `core/` (`barstore`, `assetdata`, `paths`, `study.blocks.validate`), `ui/daemon/runs` · **Consumed by:** `ui/daemon/routers.py` (router), `ui/desktop/tradegallery`, the Ficha's «Contra el subyacente» tab (ResultView)

| file | what it does | run it | in → out |
|---|---|---|---|
| `__init__.py` | Package marker | imported | — |
| `api.py` | `ROUTER`: `GET /api/tearsheet/market?project&databank&identity&asset=` and `GET /api/tearsheet/trades?project&databank&identity&sample=IS\|OOS&pick=quantile\|random&seed=&asset=`; both take `source=live\|archive&version=` — archive reads the version's frozen `harvest/` rows, the bars stay the library's | imported | request → JSON or `{"error"}` |
| `source.py` | Newest harvest, one strategy's rows, its name and timeframe, the asset and feed as the run buttons find them, bars cut after the last day of oos1 | imported | disk → frames |
| `months.py` | Monthly P&L of the strategy and month return of the market, counted into four cells, a flat line and a no-market line, per sample | imported | frames → contract dict |
| `trades.py` | Picks at P&L quantiles 0/25/50/75/100 % (or seeded random), and each trade's bar window | imported | frames → tiles |

## Contracts and traps

- **Nothing past oos1 leaves.** Every sample the harvest holds must be `IS` or `OOS` (refused
  otherwise), and the bars are cut after `runs.context()["end"]` (31 Dec of the asset's oos1),
  so a trade window near the end of OOS cannot draw oos2 bars.
- **`barstore.read` may write.** A timeframe not yet cached is resampled from M1 and saved under
  `AlgoData/barsDerived/<feed>/<TF>-<version>.parquet` — that cache is barstore's design. Nothing
  else here writes. USDJPY H1 was already cached on 2026-09-26.
- **Month of the strategy** = last daily equity of the month minus that of the month before
  (the first month against 0), rounded to the cent; zero is a *flat* month, on its own line.
  **Month of the market** = last close / first close of the month − 1, as the order states
  (not against the previous month's close). A month with no bar or a zero return has no sign
  and goes on its own line. Four cells + flat + no-market = months of the sample.
- **Quantile picks are deterministic**: stable sort by P&L, rank `round(q·(n−1))`. Fewer than five
  trades → all of them. Random picks are `numpy.default_rng(seed)`; the seed goes back to the
  window so the same five can be redrawn. There is no pick of the best trade alone.
- **Unknown asset or feed**: `/market` refuses with a sentence; `/trades` still answers, each
  tile's `bars` saying `missing`, and `bars_note` holding the reason.
- **Identity pairs only inside one databank**
  (`knowhow/sqx-format/identity-differs-across-databanks.md`): an identity not in this harvest
  is refused with that sentence, never looked up elsewhere.
- Warm: `/market` ~0.12 s, `/trades` ~0.08 s on `USDJPY_workflow_profiling_v1/Results`.
