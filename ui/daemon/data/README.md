# ui/daemon/data — what the «Datos» zone asks

The routes of the Datos zone (encargo 22 §8.3, plan 24 front F10). Read-only over the data root:
nothing here writes a file of its own, exports anything or reaches SQX. The one write is
`core.barstore`'s own cache: a timeframe asked for the first time is resampled from M1 and kept in
`barsDerived/<feed>/<TF>-<fingerprint>.parquet`, as every other reader of the bar library does.

```
api ─▶ catalogue ─▶ one os.walk of the data root (files, formats, age) + every manifest.json
    └▶ market ─▶ core.barstore (bars) · spread/<tick feed>/{spread,band}.json · feedQuality/<feed>/feedQuality.json
```

**Imports from:** `core/` (`barstore`, `manifest`, `paths`, `datapaths`), `perf/inputs` · **Consumed by:** `ui/desktop/datazone` over HTTP

| file | what it does | run it | in → out |
|---|---|---|---|
| `__init__.py` | The Datos zone's routes: what the data root holds, the bar library, and the two step-4 studies. | imported | — |
| `api.py` | The Datos zone's routes: the catalogue of the data root, the assets, their bars and their step-4 studies. | imported | request → JSON |
| `catalogue.py` | What the data root holds, tree by tree: files, formats, newest write, and the manifests that sign it. | imported | disk → rows |
| `market.py` | One asset's data as the Datos zone shows it: its feeds, its bars, and its step-4 studies off the disk. | imported | disk → JSON |

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
