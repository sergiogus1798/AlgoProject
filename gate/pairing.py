"""Pair two databanks: on identity first, and on file name for whatever identity missed."""

from pathlib import Path


def pair(build: dict[str, Path], after: dict[str, Path]) -> tuple[dict, dict, list]:
    """Match a build databank against its retest databank.

    Args:
        build: Identity to file, from the build databank.
        after: Identity to file, from the retest databank.

    Returns:
        `pairs` keyed by the BUILD identity, each holding the two files; `alias`, the
        retest identity of every pair the names had to rescue, so its exported rows can be
        re-keyed; and `missing`, the build strategies with no twin at all.

        Identity is tried first because it is what a strategy IS. The name is the fallback
        (owner, 2026-09-23): SQX renames on collision, so a name is not an identity — but
        a name that appears exactly ONCE on each side names one strategy, and refusing to
        use it would throw away a pair the numbers are sitting right there for. A name
        that repeats within either databank is ambiguous and is left unpaired.
    """
    pairs = {i: (build[i], after[i]) for i in build.keys() & after.keys()}
    left_b = {i: p for i, p in build.items() if i not in pairs}
    left_a = {i: p for i, p in after.items() if i not in build}

    def unique(left: dict) -> dict:
        """File name to identity, keeping only the names that occur once."""
        seen: dict[str, list] = {}
        for i, p in left.items():
            seen.setdefault(p.stem, []).append(i)
        return {n: v[0] for n, v in seen.items() if len(v) == 1}

    names_b, names_a = unique(left_b), unique(left_a)
    alias = {}
    for name in names_b.keys() & names_a.keys():
        ib, ia = names_b[name], names_a[name]
        pairs[ib] = (build[ib], after[ia])
        alias[ia] = ib
    return pairs, alias, sorted(set(build) - set(pairs))
