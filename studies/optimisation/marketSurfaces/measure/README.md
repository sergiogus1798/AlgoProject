# marketSurfaces/measure — what are the numbers?

| file | what it does | in → out |
|---|---|---|
| `pairs.py` | rho (Spearman) and J (Jaccard of the top decile) between two surfaces over the variants both keep, each distinct backtest once, with the Fisher interval and the hypergeometric band under independence; and every pair of one segment | surfaces → one row per pair |
| `verify.py` | The encargo's §3: every market's daily curve summed against SQX's net profit (and against the next market's, as the control), the main market's curve and the WFC's C3 column, and the diagonal | batch + cells → checks |

Must never hold a threshold that judges a pair; that is `verdict/`.

**Distinct, not independent.** Two tuples that ran the same backtest count once (`core.surface.dedupe`):
🔬 2026-09-26, on the 23-1-53 batch only 2,245 of 4,999 variants carry a distinct result on
USDJPY `build`. The design still clusters the distinct ones, so the Fisher interval and the
hypergeometric band are narrower than the truth — which is why the call leans on magnitudes
(the rho floor) and not on p-values.

**J under independence is not zero.** Two random top deciles share a tenth of themselves:
J = k²/n / (2k − k²/n) ≈ 0.053. Read J against `j0` and `j_hi`, never against 0.

**The dollars of a curve and of SQX's net profit do not have to agree**, the ranks do.
`verify.against` says why; the card is `knowhow/sqx-format/daily-equity-bin.md`.
