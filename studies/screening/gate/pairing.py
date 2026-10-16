"""Pair two databanks by strategy identity: the build's file and the retest's file of the same strategy."""

from pathlib import Path


def pair(build: dict[str, Path], after: dict[str, Path]) -> tuple[dict, dict, list]:
    """Match a build databank against its retest databank.

    Args:
        build: Identity to file, from the build databank.
        after: Identity to file, from the retest databank.

    Returns:
        `pairs` keyed by the BUILD identity, each holding the two files; `alias`, the
        retest identity of each pair that shares a file NAME but not an identity. Those are
        NOT paired (a name is reused between builds, `knowhow/sqx-format/names-reused-between-builds.md`)
        and stay in `missing`; and `missing`, the build strategies with no twin.

        Identity (`core.sqxfile.identity`) is the same for one strategy in the build and its
        retest, so it is the key; the name is only used to flag what identity refused to pair.
    """
    pairs = {ib: (p, after[ib]) for ib, p in build.items() if ib in after}
    # Same file name, other identity: the name was reused by a different strategy (a retry,
    # a second build) or the file was rewritten. Never paired; reported so the harvest stops.
    names = {p.stem: ia for ia, p in after.items() if ia not in pairs}
    alias = {
        names[p.stem]: ib
        for ib, p in build.items()
        if ib not in pairs and p.stem in names
    }
    return pairs, alias, sorted(set(build) - set(pairs))
