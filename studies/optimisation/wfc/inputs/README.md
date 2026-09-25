# wfc/inputs — what the study is run on

| file | what it does | in → out |
|---|---|---|
| `config.py` | This study's `config.yaml` over the batch-reading knobs it shares with the CSCV (`engines/variants/config.yaml`) | — → settings |

Holds nothing computed.

The panel, the split and the usable points moved to `engines/variants/panel.py` on 2026-09-25,
when the CSCV became a study of its own.
