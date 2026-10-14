# studies/optimisation/cloud — which parameters move a mother's result across her variant batch?

Step 16.5's map. It reads one retested batch of the variant factory and says **who moves the
excess** (Sobol indices of a quadratic surface over the live parameters) and **whether that ranking
can be read at all** (the surface's adjusted R² against the same fit on a shuffled metric). It is a
diagnosis: no rule (`criteria.yaml` "16.5", `rules: []`), nothing cut, no variant chosen. It never
talks to SQX, and **it never reads oos2** — only the legs `build` and `oos1` are asked of
`variant_trades.parquet`, filtered before a row is loaded, whoever launches it.

```
config.yaml ─▶ inputs ─▶ model ─▶ measure ─▶ contract
 every knob    the cloud  surface   is it      tabs, warnings
               and its    and its   more than  and facts
               excess     indices   noise?
```

| folder | the question it answers | read its README before |
|---|---|---|
| `inputs/` | which variants enter the map, and what each one earned over the drift? | touching a filter or the measure |
| `model/` | what surface do the parameters draw, and how does its variance split? | changing the surface or the indices |
| `measure/` | does the surface explain more than noise would? | touching the reference |

| file | what it does | run it | in → out |
|---|---|---|---|
| `contract.py` | The map as the contract's tabs, its warnings, and the facts the report carries. | imported | numbers → tabs |
| `heatmaps.py` | The heat maps: the metric over every pair of the most sensitive parameters, the mother marked. | imported | numbers → grids |
| `one.py` | One batch read as a map of who moves the result, returned as the contract's data. | imported — the window and the autopilot call it | batch → result |
| `report.py` | The command: which parameters move a mother's excess across her variant batch, and whether the ranking can be read. | `python3 -m studies.optimisation.cloud.report --work <dir>` | batch → map |
| `tooltips.py` | One sentence per config.yaml knob, for the window's configuration drawer. | imported | — |
| `config.yaml` | Every tunable; a `ledger:<key>` value is a number that lives in `ledger/thresholds.yaml` | edited, or `--set key=value` | — |

Manual page, in Spanish: `docs/manual/09-optimizacion.pdf` (cap. 39-nube-de-parametros).

## What it writes

Facts, in `cloud.json` under `facts` (`pipeline.autopilot.facts` flattens them with dots):
`vivos`, `coeficientes`, `variantes.build` and `variantes.oos1` (variants in the map; of them, those
with a trade in oos1), and per leg `build.*` / `oos1.*`: `r2_ajustado`, `r2_barajado`, `legible`,
`sobol_primer.<parameter>`, `sobol_total.<parameter>`.

## What this module exists to get right

**The metric is the excess per year, step 14's exactly.** `engines.variants.excess` on each
variant's own trades, with the drift block of `studies/screening/gate/config.yaml`. Build is the
map; oos1 is the same surface refitted as a secondary reading.

**The cloud is the WFC's on the inside.** Controls out (`canary`, `inert`), an inside floor of
`15 × k` trades on build (`engines/variants/config.yaml#panel`; a mother under it warns and the
floor is skipped), exact duplicates out — the same profit to the cent on build and on oos1, since
the WFC's own duplicate test reads oos2 and this study may not.

**`k` is read off the batch.** The factory holds frozen parameters and shifts at the mother's value
in every `lhs` row, so the parameters that vary once the controls are out are the live ones with a
plateau wider than one value. A batch of the old stratified design moved frozen ones too; it has no
`variant_trades.parquet` and cannot be read here.

**The ranking is read only above its shuffled reference.** Sobol indices are indices of the fitted
surface: a surface that explains nothing still hands out a ranking. So the adjusted R² is printed
beside the percentile of `shuffles` refits on the metric dealt at random, and under it the report
says «Sin estructura distinguible del ruido». Pure noise is called legible at about the nominal
rate (`tests/test_cloud_map.py`).

**Fewer variants than coefficients is no map**, said in the report, not a crash: the autopilot
launches this for every mother.

## What it does not tell you

- **Whether the mother is a peak**: step 14's T1 judges that, with paired neighbours around her.
- **Whether choosing by the past works**: the WFC (17). **Stability in time**: the WFM (19).
- **Anything about another market**: `studies/optimisation/marketSurfaces/` (18.5).
