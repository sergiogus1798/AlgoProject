"""Known answers for the batch check: a batch against itself, two fair draws, and a shifted funnel."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from studies.screening.batches import measure

DESTS = ["estaticas_value", "drift_excess_t", "is_trades_per_year", measure.ALIVE]


def batch(seed: int, shift: float = 0.0, tag: str = "") -> pd.DataFrame:
    """A build of 20 islands of 300 as `measure.parts` gives it: each island has its own mix of
    destinations (relatives), `shift` moves every island's share from the first rule to the third."""
    rng = np.random.default_rng(seed)
    rows = []
    for island in range(1, 21):
        mix = rng.dirichlet(np.array([42.0, 35.0, 18.0, 5.0]))
        mix = mix + np.array([-shift, 0.0, shift, 0.0])
        rows += [{"island": island, "dest": d} for d in rng.choice(DESTS, 300, p=mix)]
    out = pd.DataFrame(rows)
    out["identity"] = [f"{tag}{seed}-{i}" for i in range(len(out))]
    return out


def test_a_batch_against_itself_stops_the_cell() -> None:
    """The positive control: every identity repeats, so the check has to shout."""
    one = batch(1)
    dup = measure.repeats({"a": one, "b": one})
    assert dup[0]["share"] == 1.0 and dup[0]["state"] == "parar"
    same = measure.homogeneity(measure.table({"a": one, "b": one}), 0)
    assert measure.decision([], same, dup)[0] == "PARAR CELDA"


def test_two_fair_draws_add_up_though_their_islands_are_relatives() -> None:
    """Islands differ a lot inside a batch (phi well above 1): relabelling islands, not
    strategies, is what keeps two honest batches from raising the alarm."""
    lots = {"a": batch(1), "b": batch(2)}
    same = measure.homogeneity(measure.table(lots), 0)
    assert same["phi"] > 3 and not same["alarm"]
    assert measure.decision([], same, measure.repeats(lots))[0] == "SUMAR"


def test_a_shifted_funnel_is_not_added() -> None:
    """Twelve points moved from one rule to another in every island is seen through the relatives."""
    lots = {"a": batch(1), "b": batch(2, shift=0.12)}
    same = measure.homogeneity(measure.table(lots), 0)
    assert same["alarm"]
    assert measure.decision([], same, measure.repeats(lots))[0] == "NO SUMAR"


def test_a_different_setup_is_named_and_nothing_else_is_judged() -> None:
    """Batches under different rules are not compared: the field is named and that is the answer."""
    prints = {"a": {"feed": "USDJPY_M1", "rules": ["x"]}, "b": {"feed": "USDJPY_M1", "rules": ["y"]}}
    fields = measure.differing(prints)
    assert fields == ["rules"]
    assert measure.decision(fields, None, [])[0] == "NO SUMAR"


def test_parts_reads_the_island_and_the_first_rule_that_killed() -> None:
    """A kept strategy is alive whatever its limbo reason names; a dead one died at its first rule."""
    verdict = pd.DataFrame({
        "strategy": ["Strategy 12.3.250", "Strategy 2.17.257"],
        "verdict": ["MANTENER", "DESCARTAR"], "identity": ["a", "b"],
        "reason": ["limbo: gate.scorecard.is_trades_per_year=27.4",
                   "nivel 1a: gate.scorecard.drift_excess_t=1.06"]})
    got = measure.parts(verdict)
    assert list(got["island"]) == [12, 2] and list(got["dest"]) == [measure.ALIVE, "drift_excess_t"]


def test_a_tenth_repeated_warns_and_sizes_the_cell() -> None:
    """600 of 6,000 already generated: a warning, and a cell of about 60,000 distinct strategies."""
    one, two = batch(1), batch(2)
    two.loc[:599, "identity"] = one["identity"][:600].to_numpy()
    got = measure.repeats({"a": one, "b": two})[0]
    assert got["state"] == "aviso" and got["repeated"] == 600 and got["space"] == 6000 * 6000 / 600


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
    print("ok")
