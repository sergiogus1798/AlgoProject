# marketSurfaces — possible improvements, argued before they are made

## The null is too narrow, and the fix is not obvious

The Fisher interval uses `n_eff` (distinct results) and the J band is hypergeometric. Both assume
the distinct variants are exchangeable, and they are not: the design places them in a
neighbourhood, a factorial and a coverage stratum, and neighbours share most of their trades. The
honest null keeps the design's clustering and breaks only the pairing between markets — e.g. a
block permutation of the variant labels within strata, or rotating one market's surface along the
factorial grid. Until then the call leans on a magnitude (the rho floor) rather than on p.

## Call on `rho_neutral` instead of raw rho?

Raw net-profit rho carries exposure × drift (README). The owner asked for the WFC's metric, so the
call stays on raw and the table shows both. Switching the call is one line in `verdict/call.py`;
it needs the owner's word, because it changes what "the same region" means — the same region net
of how long it stays in the market.

## A per-trade metric

`AvgTrade` or net profit per unit of exposure would remove the drift channel at the source and make
the surfaces less sensitive to the zero-commission placeholder. It would stop speaking the WFC's
number, which is the reason it is not the default.

## Cross-segment pairs

Main `build` against market `oos1` asks whether the region chosen in sample on USDJPY is the good
one later on another market — the strongest form of B3. It is the WFC's question crossed with this
one, and it would double the table. Not built until the owner asks for it.
