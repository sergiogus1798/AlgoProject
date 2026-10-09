"""P1 for an export: find each strategy's .sqx among the project's exports and count its fixed distances."""

import numpy as np
import pandas as pd

from core import paths, sqxfile
from sqx.inspect.strategymeta import fixed_distance


def fixed(project: str, names: list[str], identity: dict[str, str | None]) -> pd.Series:
    """Number of fixed pips/points distances (`fixed_distances`) of each strategy.

    Args:
        project: SQX project name; its `raw/<project>/` and its databanks on the workers are
            searched for `<name>.sqx` (at step 10 the files are only on the worker).
        names: Strategy names.
        identity: name -> identity, as `core.study.identity.resolve` returns it. A file is
            taken only when its identity equals the strategy's: a databank can hold another
            strategy under the same name.

    Returns:
        Indexed by name; NaN where no .sqx of that identity is found (not 0: nothing was read).
    """
    found = {}
    roots = [paths.DATA / "raw" / project]
    roots += [paths.project_dir(project, w["path"]) / "databanks" for w in paths.WORKERS.values()]
    for path in (f for root in roots for f in root.rglob("*.sqx")):
        if path.stem in names and path.stem not in found and identity.get(path.stem):
            if sqxfile.identity(path) == identity[path.stem]:
                found[path.stem] = len(fixed_distance.fixed_distances(path))
    return pd.Series([found.get(n, np.nan) for n in names], index=names, dtype=float)
