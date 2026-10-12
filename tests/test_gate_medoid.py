"""Known answers for `redundancy.medoides`: the medoid of each of the largest structure groups."""

import pandas as pd

from studies.screening.gate.redundancy import medoides


def table(groups: dict[str, dict[str, list[int]]]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """{structure: {name: entry bars}} -> (metrics, oos) with identity = name."""
    rows = [(n, n, s) for s, g in groups.items() for n in g]
    metrics = pd.DataFrame(rows, columns=["identity", "strategy", "structure"]).set_index("identity", drop=False)
    oos = pd.DataFrame([(n, b) for g in groups.values() for n, bars in g.items() for b in bars],
                       columns=["identity", "open_time"])
    return metrics, oos


def test_medoid_is_the_most_overlapping_member() -> None:
    """Group of 3, hand-written bars: b overlaps the others most."""
    metrics, oos = table({"S": {"a": [1, 2, 3], "b": [1, 2, 3, 4], "c": [1, 2, 3, 4, 5]}})
    got = medoides(metrics, oos, metrics.index)
    assert list(got.index[got["medoide"]]) == ["b"]      # means: a .675, b .775, c .70
    assert (got["grupo"] == "a").all()


def test_tie_goes_to_the_first_name_and_singletons_are_their_own_medoid() -> None:
    """A tie goes to the first name; a group of one is its own medoid."""
    metrics, oos = table({"S": {"x": [1, 2], "y": [1, 2]}, "T": {"z": [5]}})
    got = medoides(metrics, oos, metrics.index)
    assert list(got.index[got["medoide"]]) == ["x", "z"]
