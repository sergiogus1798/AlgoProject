#!/usr/bin/env python3
"""Known-answer test for studies.optimisation.wfc.measure.persistence: the top's persistence is
1 for one ranking kept, 0 for it reversed and `keep` under a shuffled assignment; the ratio is a
median of ratios above the in-sample floor; the sign-flip null has no edge and keeps the
variants' dependence, and a family whose ranking persists reads beyond it."""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from studies.optimisation.wfc.measure import persistence as p


def main() -> None:
    """Fail loudly if a metric stops matching the number its definition gives."""
    rng = np.random.default_rng(3)
    x = np.arange(100.0)
    assert p.persistence(x, x, 0.20, 0.50) == 1.0               # the same ranking
    assert p.persistence(x, -x, 0.20, 0.50) == 0.0              # reversed
    assert p.persistence(x, x, 0.20, 0.10) == 0.5               # top 20 % in the top 10 %: half
    shuffled = np.mean([p.persistence(x, rng.permutation(x), 0.20, 0.50) for _ in range(4000)])
    assert abs(shuffled - 0.50) < 0.01, shuffled                # chance is `keep`

    inside = np.array([0.05, 1.0, 2.0, 4.0, 1.0, 2.0, -3.0])
    outside = np.array([9.0, 0.5, 1.0, 2.0, 1.0, 4.0, 3.0])
    assert p.ratio(inside, outside, 0.1) == (0.5, 5)            # ratios .5 .5 .5 1 2, floor drops two
    assert p.ratio(inside[:5], outside[:5], 0.1) == (None, 4)   # under five variants: missing

    days = np.abs(rng.normal(1.0, 1.0, (500, 40)))              # every variant wins every day
    nets, sharpes = p.flipped(days, rng)
    assert nets.shape == sharpes.shape == (p.DRAWS, 40)
    assert abs(nets.mean()) < 0.05 * days.sum(axis=0).mean()    # zero edge once the signs are drawn
    assert (np.abs(nets) <= days.sum(axis=0) + 1e-9).all()
    one = p.flipped(days[:1], rng)[0]
    assert np.allclose(np.abs(one), days[0])                    # one day: its profit, either sign

    # 300 variants, 750 out-of-sample days. A skill that persists: each variant's daily mean out
    # of sample is its in-sample net, in the same order. No skill: out of sample is common noise.
    skill = rng.normal(0.0, 1.0, 300)
    common = rng.normal(0.0, 5.0, (750, 1))
    kept = common + skill + rng.normal(0.0, 5.0, (750, 300))
    lost = common + rng.normal(0.0, 5.0, (750, 300))
    sharpe = np.full(300, np.nan)
    good = p.measure(skill, kept.sum(axis=0), sharpe, sharpe, kept, 0.20, 0.50, 0.1)
    none = p.measure(skill, lost.sum(axis=0), sharpe, sharpe, lost, 0.20, 0.50, 0.1)
    assert good["baseline"] == 0.50 and good["ratio"] is None and good["null"]["ratio"] is None
    assert good["excess"] > good["null"]["excess"][4], good     # beyond the null's 95th percentile
    assert none["null"]["excess"][0] < none["excess"] < none["null"]["excess"][4], none
    assert abs(good["null"]["excess"][2]) < 0.1                 # the null's excess is centred on 0
    print("ok")


if __name__ == "__main__":
    main()
