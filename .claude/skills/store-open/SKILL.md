---
name: store-open
description: Read a strategy back from the strategy store — find it by name or identity, unpack its folder (the .sqx under its own name, every test's results, distributions, trades per market and timeframe) and read any number or histogram without rerunning a test. Use when the owner asks for a saved strategy's results, metrics, distributions or trades, wants its .sqx to load in StrategyQuant, or asks what the store holds («qué hay guardado», «enséñame la 12.20.323», «dame el sqx»).
---

# /store-open

Everything about a stored strategy is in `AlgoData/store/<cell>/<name> <identity8>/` — never rerun a study
to answer a question the folder already answers.

1. **Find it.** `python3 -m core.store list` (one line each: identity, cell, project, name, last
   step and verdict); `| grep '<name or cell>'`. What a cell's runs generated and saved:
   `AlgoData/store/<cell>/runs.json`.
2. **Unpack it**, outside the repo (rule 7):
   `python3 -m core.store open '<name or start of identity>' --out <folder>` → prints the folder.
   Two strategies under one name (the same name in two runs) are listed and nothing is opened:
   ask the owner which (rule 11), then pass the identity. A damaged folder is refused: report it.
3. **Read what was asked**, from the unpacked folder — one sub-folder per stored zip:

   | asked for | where |
   |---|---|
   | what each step said | `manifest.json` → `steps` |
   | the `.sqx` for StrategyQuant | `<name>.sqx` (the stored bytes; identity = the folder's) |
   | a test's numbers | `<study>.<databank>.<day>/` — its tables cut to this strategy, `estrategias/<name>.json` |
   | the histogram behind a z or p | `<study>…/distribuciones.parquet`: `test`, `metric`, `where`, `observed`, `edges`+`counts` (200 bins, whole range), `n_ge`/`n_le`, `draws` (sorted) or `low`/`high` |
   | trades in another market or timeframe | `operaciones.<databank>.<day>/trades.parquet` (`Symbol` for markets; sisters are `<name>_Scaled<TF>`); `also` in the manifest names a databank with the same trades |
   | MC simulations, SPP runs, WFM cells (steps 13, 15, 19) | `exportacion.<databank>.<day>/` — the export's sub-folders cut to this strategy (`sims/task=…/`, `spp/`, `wfm/`) |
   | the 500-5,000 variants of step 16.5 | `variantes.<day>/` — `design.json`, `plan.csv`, `manifest.parquet` (every variant's parameters), `metrics.parquet`, `equity*.parquet`, `trades.parquet`, `segments.parquet`; no variant's `.sqx` |
   | cloud, WFC, CSCV, market surfaces (16.5-18.5) | `optimizacion.<day>/estudios/` — each study's JSON and `distribuciones.parquet` |
   | WFM reading and the joint reading (19, 20) | `wfm.WFM.<day>/`, `blindJoint.WFM.<day>/` — filed under the mother although the WFM gave it another identity (`lineage.csv` in `operaciones.WFM.<day>/`) |
   | the step-12 sisters | `hermanas.<day>/scaling.parquet` and their rows per study; the file itself: `/rebuild-sister` |
   | the population it came from | `<study>….poblacion/` (funnel, population JSON, the rejected) |
   | costs on the day it was saved | `costes.<SYMBOL>/` |

   A long table or JSON goes to a subagent (rule 16) with the question; charts follow the owner's
   visualisation preferences (big, high contrast, every statistic explained).
4. **Delete the unpacked copy** when the answer is given; the store is never edited by hand.

Carrying a stored strategy on through steps 13-20 is `/store-resume`. Not built yet — say so,
do not improvise: the window's «Guardadas» zone, and steps 21 on (stop grid, structural tests). Handing the owner the `.sqx` file is fine; a
project built around it goes through the builder (rules 5, 6, 10).
