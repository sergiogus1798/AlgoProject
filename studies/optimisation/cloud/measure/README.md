# cloud/measure — is the surface more than noise?

| file | what it does | in → out |
|---|---|---|
| `reference.py` | The adjusted R² of the same surface refitted on the metric shuffled among the variants, and `legible`: the real one against a percentile of those | cloud, fit → r2_adj, r2_ref, legible |

Produces the one comparison the ranking is read by; fits through `model/`, never its own surface.

**A shuffle, not a formula.** It keeps the metric's own distribution, heavy tails included, and the
exact design, so the reference is right for this many coefficients on these very points.
