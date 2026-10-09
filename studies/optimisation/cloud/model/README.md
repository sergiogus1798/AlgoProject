# cloud/model — the surface the parameters draw, and how its variance splits

| file | what it does | in → out |
|---|---|---|
| `space.py` | Which parameters still vary (the live ones), and the unit cube they span | cloud → varying, unit |
| `surrogate.py` | The full quadratic over the live parameters: its design matrix, the least-squares fit and its adjusted R² (for one metric or many columns at once), its prediction | cloud → fit |
| `sensitivity.py` | First-order and total Sobol indices, computed on the fitted surface | fit → indices |

Decides nothing and reads no file.

**Why a quadratic and not a Gaussian process.** It fits no hyperparameter on the data it is judged
on, and its coefficient count — 1 + 2k + k(k−1)/2 — is what the factory sizes the batch by.

**The adjustment uses the matrix's rank.** A parameter with two values makes its square a copy of
itself; counting both would charge the fit a coefficient it does not have.

**The indices are over a uniform cube**, parameters treated as continuous: "if every live parameter
were dialled anywhere in its plateau, who would move the result".
