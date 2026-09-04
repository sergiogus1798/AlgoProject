# tasks/analysis — the maths over a whole population

Libraries, not commands. The entry points that use them live in `../reports/`.

| file | what it does | run it | in → out |
|---|---|---|---|
| `metrics.py` | Reads a metrics export and works out which columns are IS, which are OOS, and which pair up | imported | `metrics.csv` → numeric columns + metric name lists |
| `correlations.py` | Pearson/Spearman, the single-test significance floor, and Benjamini-Hochberg over a family of tests | imported | two columns → correlation rows |

Two things these enforce, because both have already produced wrong answers:

- **A constant column is dropped, not reported as NaN.** SQX leaves some metrics at one value for
  a whole population (`PSR` and `Symmetry` did this in the previous project). `measured()` excludes
  them, so they never reach a correlation.
- **The significance floor is not the threshold.** At n=10,000 a correlation clears the ordinary 5%
  level at |r| > 0.02. Every in-sample metric is tested against the same outcome at once, so
  `discoveries()` controls the false discovery rate across the family instead.

Spearman leads every ranking. These metrics are heavy-tailed and one blow-up strategy moves Pearson
a long way; where the two disagree, suspect outliers.
