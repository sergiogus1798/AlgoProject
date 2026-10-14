# marketSurfaces/contract — how is it read?

| file | what it does | in → out |
|---|---|---|
| `tabs.py` | Step 18.5 as the contract's blocks: the call, the joint rho against its null, the markets, the premium, the power. | numbers → tabs |
| `words.py` | Every Spanish sentence of step 18.5: labels, meanings, column help, notes and the glossary. | — → text |

Must never judge. Every statistic shown carries a line saying what it is (`words.MARKETS`,
`CATEGORIES`, `REFERENCE`, the notes). Market names and categories come from `_markets.yaml`;
nothing here names an asset.
