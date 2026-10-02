"""The registry of measures: every function a row of config.yaml's `measures` may name."""

from studies.research.marketProfile.measure import pattern, price, rules, session, structure

# One signature for all: fn(x, cal, **args) -> (statistic, entry bars, exit bars, detail).
# A larger statistic is more of the family's behaviour. Entry and exit are None for a measure
# that places no trade; such a measure has a p but no effect in money, so it can raise a
# family's score and can never pass the cost filter on its own.
REGISTRY = {
    "variance_ratio": structure.variance_ratio, "hurst": structure.hurst, "adf": structure.adf,
    "range_acf": structure.range_acf, "narrow_wide": structure.narrow_wide,
    "lookback": price.lookback, "above_band": price.above_band, "breakout": price.breakout,
    "false_break": price.false_break, "extreme": price.extreme, "big_bar": price.big_bar,
    "narrow_break": price.narrow_break,
    "inside": pattern.inside, "engulfing": pattern.engulfing, "run": pattern.run,
    "hour": session.hour, "band": session.band, "weekday": session.weekday,
    "band_range": session.band_range, "rule": rules.rule}

# Measures of the series as a whole: they have no direction and are run once per cell. Every
# other measure is run twice, on the series and on its mirror (long and short).
SYMMETRIC = ("variance_ratio", "hurst", "adf", "range_acf", "narrow_wide")
