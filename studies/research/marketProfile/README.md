# marketProfile — what behaviour each asset × timeframe × direction shows, against chance

Piece 1 of the research director (`docs/AgentPDFs/director-de-investigacion-2026-10-01.md` §3).
For each of the 19 assets, on M15, M30, H1 and H4, long and short apart: the seven families
(tendencia, ruptura, reversion, momentum, volatilidad, patron, sesion), every measure against the
same series resampled in blocks, all p-values corrected together, and four filters before a
cell counts: significant, pays twice its cost, stable across the build years, and at least 40
trades a year (owner, 2026-10-02; an asset may be set down to 35 in
`filters.min_trades_per_year_by_asset`, never lower: `many.min_trades` refuses).

**It reads only the `build` segment.** `inputs.cut` is the one place bars enter, and it drops
everything from the build end on before any resampling; `tests/test_marketprofile.py` poisons
the bars after the build end and checks that no measure and no D1 value moves.

**Widened 2026-10-02** (audit: `knowhow/market-profile/market-profile-blind-spots.md`): the original
31 measures looked back at most 55 bars and held at most 16, read no higher timeframe and no
volatility regime, and left only by a bar count. 68 measures were added, each tagged with what
it adds (`tag`: `horizon`, `hold`, `exit`, `context`, `regime`, and `literature` for the rules of
`AlgoData/research/literature/edges-2026-10-02.yaml`, named in `lit`; the originals are `base`):
189 tests per cell, 14,364 in the map, 3,000 draws (at 1,000 the smallest p was the only one the
correction could still name). **No clock**: a measure with `clock: true` (best hour, band,
weekday, a band's range) is still measured, and never leads a family, never grades and never
reaches the board. **Two corrections side by side**: the verdict is Benjamini-Hochberg over every
test (`q`, `significant`, `passes`); `q_family`, `significant_family`, `passes_family` are the
same procedure inside each family — the owner chooses, the code never switches.

| file | what it does | run it | in → out |
|---|---|---|---|
| `bibliography.py` | What the literature says beside what the profile measured: the bibliography view of `assets/FAMILIAS.md`. | imported; `report --bibliography` | `measures.csv` + the file → Markdown |
| `blocklen.py` | The command: how the block length of the null moves the p-values, measured on real assets. | `python3 -m studies.research.marketProfile.blocklen` | bars → `blocklen.csv` |
| `context.py` | The context block of a cell: drift, volatility clustering and cost against the bar's ATR. | imported | bars → dict |
| `contract.py` | The judged map as the study contract: what the window and the page draw. | imported | tables → result dict |
| `familias.py` | `assets/FAMILIAS.md` assembled: the owner's prior leads, what was measured annotates it. | imported; `report --familias` | map + sweep + prior → `assets/FAMILIAS.md` |
| `favourable.py` | Which families favour each asset, graded A/B/C from the judged map — the tables of `assets/FAMILIAS.md`. | imported; `report --favourable` | `scores.csv`, `measures.csv` → `favourable.csv`, `avoid.csv`, `by_timeframe.csv`, `clock.csv` |
| `favourablemd.py` | The favourable-families tables as Markdown: what `report --favourable` prints for `assets/FAMILIAS.md`. | imported | tables → text |
| `higher.py` | The wider frame of every bar: the D1 context as the day BEFORE left it, and the long averages. | imported | derived series → the same plus `d1_*`, `sma5/50/200`, `rsi` |
| `inputs.py` | What the profile is run on: the config, the build bars of an asset, and its cost per trade. | imported | asset → bars, cost |
| `ledgerrows.py` | The profile's own looks at the data, as rows of the ledger's contract L1. | imported | measures → rows |
| `literature.py` | The literature scout's entries as measures of the profile: their `translation.measures`, checked. | imported by `report` (not by `inputs.config`: the tests and the other commands read `config.yaml` alone) | entries → measure rows, what was skipped |
| `many.py` | Every cell judged together: the correction, the four filters, the scores, the overlap. | imported | rows → measures, scores, correlation |
| `one.py` | One cell — an asset on a timeframe: every measure on the real bars and on its null draws. | imported | bars → rows |
| `priorview.py` | The owner's prior beside what was measured: each prior family of an asset and timeframe, with its state. | imported | measures + variants → rows |
| `report.py` | The command: the market profile of every asset on its build segment, measured and judged. | `python3 -m studies.research.marketProfile.report [--symbols XAUUSD ...] [--force] [--judge-only]`; `--favourable` prints only the ranking below, `--bibliography` only the literature view, `--sweep` runs the separate exit and parameter sweep, `--familias` rewrites `assets/FAMILIAS.md`, `--top-up` measures only the measures the stored assets lack (the scout's new entries) and judges the whole map again | bars → the map |
| `series.py` | A cell's bars as log arrays with their shared indicators, mirrored for shorts, and resampled. | imported | bars → arrays |
| `store.py` | Where the profile lives on disk: one file of measures per asset, and the judged tables. | imported | — |
| `sweep.py` | The exit and parameter sweep of one cell: every entry at nearby parameters under every exit. | imported; `report --sweep` | bars → variant rows |
| `sweepjudge.py` | The sweep judged: its own correction, each variant's plateau, the best variant per cell-family. | imported | variant rows → `sweep/variants.parquet`, `best.csv`, `counts.csv`, `ledger.jsonl` |
| `tooltips.py` | One sentence per config.yaml knob, for the window's configuration drawer. | imported | — |
| `topup.py` | Measure on an asset only the measures its stored cells lack, and add them to what is stored. | imported; `report --top-up` | bars → rows added to `cells/<SYMBOL>.parquet` |
| `variance.py` | Lo-MacKinlay's variance ratio per asset and timeframe on build, with its sign year by year. | imported (`--familias` writes `variance_ratio.csv` when missing) | bars → table |
| `config.yaml` | Every knob: timeframes, the null (model, draws, block per timeframe), the four filters, the score, the sessions, and the list of measures | edited, or `--set section.key=value` | — |
| `measure/` | The measures, one signature each (its own README) | imported | arrays → statistic, trades |
| `familias_texto.yaml` | The hand-written part of that document, in Spanish: the paragraphs of judgement and the description of every condition | edited | — |

Manual page, in Spanish: chapter `82-perfil-de-mercado` of `AlgoData/manual-fuentes/`.

## What it writes — `AlgoData/research/profiles/`

| file | one row per | columns |
|---|---|---|
| `scores.csv` | symbol × timeframe × direction × family | `score` 0-100 · `lead` (the measure that speaks for the family) · `p` (its BH-corrected p) · `p_raw` · `multiple` (effect / cost) · `effect`, `cost` (price units per trade) · `stability` (share of build years with the sign), `years_with_sign`, `years` · `trades_per_year` · `significant`, `pays`, `stable`, `frequent` (the four filters, of the lead) · `passes` (some trade measure of the family passes all four) · `fragile` (significant and pays, but a minority of years) · `measures`, `measures_significant` · `needs_clock` (the family has only clock measures) · `p_family`, `significant_family`, `passes_family` (the alternative correction) |
| `measures.csv` | symbol × timeframe × direction × measure (`direction` is `both` for a directionless one) | `family` · `tag` (what the measure adds to the original set) · `needs_clock` · `q_family`, `significant_family`, `passes_family` (the alternative correction) · `stat`, `null_mean`, `null_sd`, `z`, `p`, `q` · `n_trades`, `trades_per_year`, `effect`, `cost`, `multiple` · `years`, `years_with_sign`, `stability`, `per_year` (JSON) · `detail` (JSON: the raw reading — best hour, half-life, break size…) · `significant`, `pays`, `stable`, `frequent`, `passes` |
| `context.csv` | symbol × timeframe | `bars`, `block`, `drift_per_year`, `abs_acf_1`, `abs_acf_1_20`, `cost`, `atr`, `cost_over_atr`, `kaufman_daily` |
| `correlation.csv` | scope (`ALL` or a timeframe) × pair of families | `cells`, `pearson`, `spearman` of the two scores across cells |
| `overlap.csv` | symbol × timeframe × direction × pair of families | `phi`: correlation between "a measure of this family enters on this bar" for the two |
| `favourable.csv` | symbol × listed family, most favourable first (`report --favourable`) | `rank`, `grade` (A/B/C), `weak`, the best cell's `timeframe`, `direction`, `lead`, `multiple`, `p`, `p_raw`, `stability`, `trades_per_year`, `also`, `palette`, `hole` |
| `by_timeframe.csv` | symbol × family × timeframe: the better direction, graded or not | `direction`, `grade`, `lead`, `multiple`, `p`, `p_raw`, `trades_per_year`, `weak` |
| `clock.csv` | clock measure that would have earned a grade — measured, never proposed | `timeframe`, `direction`, `measure`, `detail`, `grade`, `multiple`, `p`, `p_raw`, `stability`, `trades_per_year` |
| `avoid.csv` | symbol × family with no graded cell that is measurably bad | `reason` (`no_paga`, `plana`, `signo_contrario`), `scope` (`familia`/`celda`), `cells`, `of`, `where`, `best_multiple` |
| `cells/<SYMBOL>.parquet`, `.json` | the asset's raw rows before judging; build window, bars, seed, timings | — |
| `profile.json`, `.html`, `.md` | the map as the study contract | — |
| `ledger.jsonl` | measure × direction × run, contract L1 | merge into `AlgoData/ledger/` pending |
| `run.json` | the last run: seed, config hash, what was skipped and why | — |
| `blocklen.csv` | the block-length experiment | — |

## Pending owner answer: BH over a sealed family

Owner, 2026-10-14 (encargo 62, answer 3): families are declared and sealed before measuring, and Benjamini-Hochberg is applied over a family fixed per proposal. Not applied: step 1 is switched off (encargo 65 section 2; the map is regenerated by hand), so no proposal has a family to seal. Owner, 2026-10-15 (P62-B = A): `many.py` is left as it is and the answer waits here for the day step 1 returns.

## The three decisions the code takes that the design left open

- **Score** = 100 × mean over the family's measures of z clipped to [0, `z_cap`], z being the
  real statistic against its null draws. White noise scores about 8; nothing can exceed 100.
  Since the widening a family averages more measures (tendencia 26, reversion 34), so a
  structure only its short-horizon measures see scores lower than before: an AR(+0.2) series
  read 40+ on `tendencia` and now reads 23. The score orders nothing any more: the board and
  `FAMILIAS.md` read the filters.
- **A family passes** when one of its measures *with trades* passes the four filters. A
  directionless measure (variance ratio, Hurst, stationarity, range autocorrelation) has a p
  and no money: it lifts the score and never passes on its own.
- **The lead** of a family is its best payer among the measures that pass, else its smallest
  corrected p. Its numbers are the family's `p`, `multiple` and `stability`.

Alternatives and known limits: `POSSIBLE_IMPROVEMENTS.md`.

## The block length (measured 2026-10-01, `blocklen.py`, XAUUSD · EURUSD · USA500 on H1 and H4)

| block (bars) | false alarms at 5 % on sign-flipped series | real measures with p ≤ 0.05 (of 53) |
|---|---|---|
| 1 | 4.0-7.5 % (mean 4.9 %) | 5-10 |
| 6 | 1.3-2.9 % | 2-11 |
| 24 | 0.3-0.8 % | 2-7 |
| 72 | 0.3-0.7 % | 1-4 |
| 240 | 0.5-0.7 % | 1-4 |

The spread of the null does not move with the block (0.87-1.05 of block 1), because the trade
statistics are studentised; what moves is its centre: a block keeps whatever is shorter than
itself, so the null inherits the structure under test. Politis-White says the same from the
other side: 1-4 bars for returns, 240-750 for absolute returns. `config.yaml` carries **1** on
every timeframe. The price: the directionless volatility measures are then tested against "no
clustering", which is false in every market — `volatilidad` scores ~33 everywhere and says nothing.

Runtime, 19 assets × 4 timeframes × 1,000 draws, 4 processes at nice 19 on a loaded machine:
1,169 s with the original 31 measures (per cell: M15 45-190 s, M30 23-84 s, H1 17-50 s, H4
6-30 s); with the 99 of 2026-10-02 and 3,000 draws, 19 processes (one per asset) on a free machine: about
40 minutes (an FX asset alone: M15 ~25 min, M30 ~9, H1 ~5, H4 ~2). The sweep, 60 processes: 21 minutes.
