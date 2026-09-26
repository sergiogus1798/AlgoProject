"""Pair two databanks by strategy name: the build's file and the retest's file of the same name."""

from pathlib import Path


def pair(build: dict[str, Path], after: dict[str, Path]) -> tuple[dict, dict, list]:
    """Match a build databank against its retest databank.

    Args:
        build: Identity to file, from the build databank.
        after: Identity to file, from the retest databank.

    Returns:
        `pairs` keyed by the BUILD identity, each holding the two files; `alias`, the
        retest identity of every pair whose identity changed on the way, so its exported
        rows can be re-keyed; and `missing`, the build strategies with no twin at all.

        The name decides (owner, 2026-09-26): the retest databank is a retest of the build
        one, and a strategy keeps its file name through it. Within one databank a file name
        is unique — SQX renames on collision — so every name pairs at most once. Identity is
        kept only as the key the downstream modules read.
    """
    by_name = {p.stem: i for i, p in after.items()}
    pairs, alias = {}, {}
    for ib, p in build.items():
        ia = by_name.get(p.stem)
        if ia is None:
            continue
        pairs[ib] = (p, after[ia])
        if ia != ib:
            alias[ia] = ib
    return pairs, alias, sorted(set(build) - set(pairs))
