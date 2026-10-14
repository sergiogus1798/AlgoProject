# cloud/model — the surface the parameters draw, and how its variance splits

| file | what it does | in → out |
|---|---|---|
| `sensitivity.py` | How the surface's variance splits between parameters: first-order and total Sobol indices. | fit → indices |
| `space.py` | The geometry of the cloud: which parameters still vary, and the unit cube they span. | cloud → varying, unit |
| `surrogate.py` | The smooth model of the surface: a full quadratic over the live parameters, and how much it explains. | cloud → fit |

Decides nothing and reads no file.

**Why a quadratic and not a Gaussian process.** It fits no hyperparameter on the data it is judged
on, and its coefficient count — 1 + 2k + k(k−1)/2 — is what the factory sizes the batch by.

**The adjustment uses the matrix's rank.** A parameter with two values makes its square a copy of
itself; counting both would charge the fit a coefficient it does not have.

**The indices are over a uniform cube**, parameters treated as continuous: "if every live parameter
were dialled anywhere in its plateau, who would move the result".
