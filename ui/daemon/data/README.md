# ui/daemon/data — what the «Datos» zone asks

The routes of the Datos zone (encargo 22 §8.3, plan 24 front F10). Read-only over the data root:
nothing here writes a file of its own, exports anything or reaches SQX. The one write is
`core.barstore`'s own cache: a timeframe asked for the first time is resampled from M1 and kept in
`barsDerived/<feed>/<TF>-<fingerprint>.parquet`, as every other reader of the bar library does.

```
api ─▶ catalogue ─▶ perf.disk.inventory (bytes, files, formats, age) + every manifest.json
    └▶ market ─▶ core.barstore (bars) · spread/<tick feed>/{spread,band}.json · feedQuality/<feed>/feedQuality.json
```

**Imports from:** `core/` (`barstore`, `manifest`, `paths`, `datapaths`), `perf/disk`, `perf/inputs` · **Consumed by:** `ui/desktop/datazone` over HTTP

| file | what it does | run it | in → out |
|---|---|---|---|
| `__init__.py` | Package marker, one docstring | imported | — |
| `api.py` | The five routes: `/api/data/catalogue`, `/api/data/assets`, `/api/data/bars?feed&tf&since`, `/api/data/spread?feed&part`, `/api/data/feedquality?feed`; a feed is checked against the listing of its tree, and a failure is a sentence, never a 500 | imported | request → JSON |
| `catalogue.py` | Every branch of AlgoData down to three levels with bytes, files, formats, the date of its newest write, whether it is stale, and how many `manifest.json` sign it and the newest date one of them carries | imported | disk → rows |
| `market.py` | The assets the three trees know (symbol = feed up to its first `_`) with their bar, tick and quality feeds; one feed's OHLC at D1/H4/H1, columnar; one feed's step-4 report read back as the contract dict its study wrote | imported | disk → JSON |

## Contracts and traps

- **The studies are read, never run.** `spread.json`, `band.json` and `feedQuality.json` are the
  contract dicts `studies.data.spread.scan`, `.bands` and `studies.data.feedQuality.scan` write
  beside their tables. A feed never scanned answers with the sentence naming that command.
- **An archived strategy's folder is named by its identity**, which the window never prints:
  every branch under `archive/<identity>/` is left out of the catalogue; the `archive` row still
  counts their bytes, files and manifests.
- **An asset is the feed name up to its first underscore.** `DAX40_TICK` has ticks
  and no bars: the zone says so instead of drawing an empty chart.
- **H1 over the whole history is 140 000 bars and 7.7 MB of JSON** (XAUUSD, 2026-09-27, 0.55 s);
  the zone asks for a period (`since`) and draws columns, not candles, when they do not fit.
