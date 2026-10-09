# marketSurfaces/verdict — what do the numbers mean?

| file | what it does | in → out |
|---|---|---|
| `call.py` | The class of a joint order (`positivo`, `neutro`, `perverso`, `sin_dato`) from its two tails and its weight, and the step's state from the deciding order, the premium and the oos2 order | numbers → words |

Must never compute a statistic.

**Only a perverse deciding order fails.** A neutral one passes («no descarta»): parameters that do
not tell themselves apart elsewhere are not evidence against the mother. The premium and the oos2
reading can only add LIMBO.

**No market decides alone.** The per-market rows are shown, never judged.
