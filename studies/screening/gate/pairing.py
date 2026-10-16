"""Pair two databanks by strategy identity: the build's file and the retest's file of the same strategy."""

import re
from pathlib import Path

from core import sqxfile

# 🔬 2026-10-16: the OOS retest sometimes writes a variable back as its literal (a Shift
# `variable="true">VortexShift1` becomes `variable="false">1` and its <variable> goes): same
# strategy, other identity (24 and 5 of 10,000 in two builds of USDJPY H1 on gorilla). An alias
# pair whose definitions match with every variable inlined is one strategy, and is paired.
VARIABLE = re.compile(
    r"<variable\b[^>]*>\s*<id>([^<]+)</id>.*?<value>([^<]*)</value>.*?</variable>", re.S
)
REFERENCE = re.compile(r'variable="true">([^<]+)<')


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
    for ia, ib in list(alias.items()):
        if _inlined(build[ib]) == _inlined(after[ia]):
            pairs[ib] = (build[ib], after[ia])
            del alias[ia]
    return pairs, alias, sorted(set(build) - set(pairs))


def _inlined(path: Path) -> str:
    """A strategy's definition with every variable replaced by its value, then hashed."""
    text = sqxfile.rules(path)
    values = dict(VARIABLE.findall(text))
    text = REFERENCE.sub(lambda m: f'variable="false">{values.get(m[1], m[1])}<', text)
    # Whitespace too: a removed <variable> leaves its indentation behind, the retest's file none.
    return sqxfile._hashed(re.sub(r">\s+<", "><", VARIABLE.sub("", text)))
