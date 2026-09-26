# marketSurfaces/verdict — what does each pair mean, and what does the mother get?

| file | what it does | in → out |
|---|---|---|
| `call.py` | A pair's state (rho interval over the floor AND J over the independence band), the main market against each declared one, and the mother-level call | pairs → states, call |

Must never compute a statistic.

**Both numbers are asked for because they fail differently.** A rho can be carried by the bottom of
the surface — both markets hate the same corner — while the top deciles share nothing; that is not
a shared good region, and `tests/test_marketsurfaces.py` builds exactly that case.

**The denominator is the declared count, always.** Nine markets were fixed in `_markets.yaml` before
anything was looked at; a market the batch lacks counts as not passing. Reading the three that
worked out of nine is the data snooping the owner's PDF (§E) names.
