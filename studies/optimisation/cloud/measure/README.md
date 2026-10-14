# cloud/measure — is the surface more than noise?

| file | what it does | in → out |
|---|---|---|
| `reference.py` | Whether the surface says anything: its adjusted R² against the same fit on a shuffled metric. | cloud, fit → r2_adj, r2_ref, legible |

Produces the one comparison the ranking is read by; fits through `model/`, never its own surface.

**A shuffle, not a formula.** It keeps the metric's own distribution, heavy tails included, and the
exact design, so the reference is right for this many coefficients on these very points.
