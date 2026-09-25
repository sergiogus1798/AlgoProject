# cscv/inputs — what the study is run on

| file | what it does | in → out |
|---|---|---|
| `config.py` | This study's `config.yaml` over the batch-reading knobs it shares with the WFC (`engines/variants/config.yaml`) | — → settings |

The panel, the split and the usable points are `engines/variants/panel.py`: the rho and the PBO are
two statements about one set of points, so both studies read them from one place.
