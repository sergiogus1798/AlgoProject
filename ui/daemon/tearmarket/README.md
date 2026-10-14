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
| `__init__.py` | The tear sheet's market side: month signs against the underlying and the trade gallery. | imported | — |
| `api.py` | The tear sheet's market routes: month signs against the underlying, and the trade gallery. | imported | request → JSON or `{"error"}` |
| `months.py` | Item 5: the month-sign count of a strategy against its market, IS and OOS apart, as a contract dict. | imported | frames → contract dict |
| `source.py` | What the two routes read: one strategy's rows of the newest harvest, and its asset's bars cut at oos1. | imported | disk → frames |
| `trades.py` | Item 6: five trades of one sample, at P&L quantiles or drawn with a seed, each with its bar window. | imported | frames → tiles |

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
