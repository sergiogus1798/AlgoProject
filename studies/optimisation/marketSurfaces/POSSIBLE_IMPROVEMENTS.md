# marketSurfaces — possible improvements, argued before they are made

The seven readings the README lists as open questions are the owner's to settle; each is one knob
or one function away.

## Plant the transmission in the weeks, not in the scores

The power curve mixes normal scores (README). Adding a weekly lean along the main market's order to
each market's panel would also exercise the null's width under a real edge — the flips of a leaned
panel are wider. It needs the lean that gives rho* on each market, solved per market; the score mix
gives rho* exactly with no solving, which is why it was built first.

## A per-category call

The categories of `_markets.yaml` are annotated with their own joint rho and tails. Deciding per
category would multiply the looks by the number of categories; not built until the owner asks.

## The grids of the detail file

`marketSurfaces_detalle.json` holds a median rank per pair of live parameters and market. It
replaced the heatmaps of SQX metrics, whose JSON reached 299 MB. If nobody opens it, delete it.
