# marketSurfaces/contract — how is it read?

| file | what it does | in → out |
|---|---|---|
| `words.py` | Every Spanish sentence: labels, meanings, column help, notes, warnings, the glossary | — → text |
| `tabs.py` | The verdict block, the tabs of the small result (the deciding order on its null with the per-market and per-category tables, the premium, the reference with the power bars, oos2 when read) and the warnings | numbers → tabs |

Must never judge. Every statistic shown carries a line saying what it is (`words.MARKETS`,
`CATEGORIES`, `REFERENCE`, the notes). Market names and categories come from `_markets.yaml`;
nothing here names an asset.
