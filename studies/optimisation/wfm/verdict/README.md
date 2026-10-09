# wfm/verdict — what it means

| file | what it does | in → out |
|---|---|---|
| `call.py` | The state from the facts, the rules that fired, and the paragraph a human reads first | facts, mode, alpha → verdict, label, why; sentence |

| rule | fires when | gives | active in |
|---|---|---|---|
| `l1_pierde` | L1 p− <= alpha | `no_pasa` (fail) | both modes |
| `l1_no_gana` | L1 median <= 0 | `limbo` (watch) | both modes |
| `centro_no_gana` | the centre cell's oos2 excess <= 0 | `limbo` | `reoptimizado` |
| `reoptimizar_empeora` | L2 p− <= alpha | `limbo` | `reoptimizado` |

Otherwise `pasa`: «reoptimizar gana» when L1 p+ <= alpha (counts as evidence), else «no descarta».
A loss without significance is `limbo` and not `no_pasa`: the WFC already kills on the same oos2.
`verdict.csv` carries pasa / limbo / no_pasa; the contract's state is `STATE[...]`.
