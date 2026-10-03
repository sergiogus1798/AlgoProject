---
q: Can the EDGE estimator of spread from OHLC bars be used as a fifth spread model?
kw: EDGE estimator spread from OHLC bars, eguidotti bidask Ardia Guidotti Kroencke JFE 2024, fifth spread model, effective spread without ticks, model.MODELS add edge, spread from Dukascopy M1 bars, bid bars no bid-ask bounce, reconstruct spread before 2017
tag: 🔬  date: 2026-10-02  see: costs/darwinex-real-spread, costs/spread-per-segment-every-asset
---
# EDGE (spread from OHLC) is not a fifth spread model: on our bid bars it reads a fifth of the real spread, and it breaks before 2012
Tried 2026-10-02 on 23 assets in `verdict.validate`'s own held-out-years validation; **not added to `model.MODELS`**. Three reasons, each sufficient:
- **It measures something else.** EDGE recovers the bid-ask bounce in TRADE prices. Our M1 bars are bid quotes: no bounce. Raw EDGE reads 0.07–0.35 bp where Darwinex's opening spread is 0.33–2.8 bp (÷5 to ÷8), is ≤ 0 on 18–42 % of days for most FX and gold, and misses the year's mean by 46–88 % on every asset. Darwinex's own bid bars give the same (gold 0.15 bp vs 1.03 measured).
- **Calibrated on the tick days it is a covariate, not an estimator** — then it fits the registry's contract (`fit(days)`, `predict(params, days)`, with an `edge` column beside `rv`) — but no variant wins steadily: by more than 2 pp of mean |error| in at most 4 of 23 assets and loses by more than 2 pp in 10–18, at splits 2020, 2022 and 2024 alike.
- **The bars' EDGE changes regime before the ticks begin**, which the validation (2017–2026) cannot see: EURUSD 0.59 bp in 2008–11 against 0.035 in 2012–16, XAGUSD 17.9 against 1.6. A scale fitted on 2017–2026 would declare gold's build segment at 18.6 bp (measured: 1.03), AUDJPY's at 7.3.
AUDJPY (`edge_escala` −9 to −24 pp at all three splits) is the one steady win, and exactly the case the third point disqualifies.

## Evidence
`scratch/ext/c2/edge_compare.py` and `edge_robust.py` (estimator ported from eguidotti/bidask, MIT,
commit 1caba55; daily EDGE on each day's M1 bars). Tables:
`AlgoData/spread/edge_vs_models_2026-10-02.csv`, `edge_vs_models_robustness_2026-10-02.csv`.
Split 2022, best of four vs best EDGE variant, mean |error|: XAUUSD 0.256 / 0.221, USDJPY 0.097 /
0.260, AUDJPY 0.316 / 0.182, AUDNZD 0.241 / 0.165, EURUSD 0.126 / 0.135, GBPUSD 0.072 / 0.081,
DJ30 0.175 / 0.324, USATEC 0.274 / 0.766. Picking the best of four variants per asset "wins" 11 of
23 — an artefact of the pick: a single pre-named variant wins 4–8 of 23.
