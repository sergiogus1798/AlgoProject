# wfc/verdict — the order's word and the step's state

| file | what it does | in → out |
|---|---|---|
| `state.py` | `classify`: positivo / neutro / perverso from the two tails at alpha. `state`: the owner's table (proposal, section 6, with the level's null of encargo 48) — the top wins outside (median above zero **and** `p_nivel` ≤ `level.alpha`) and the order is not perverse → `pasa`; a median above zero that does not beat its null (any order), a perverse order with a top that wins, or no data → `limbo`; a median at or under zero → `no_pasa`. `judge`: both, plus the «fuerte» label and, when the null was drawn again in wider blocks, `orden_bloque` | facts → orden, fuerte, estado |

Holds no arithmetic on excess and no text for the owner: the numbers are `../measure/`'s, the
sentences `../contract/words.py`'s.
