"""The cosecha's three tables (metrics, equity, trades) cut to one identity and frozen."""

import threading
from pathlib import Path

import pandas as pd


_PARTS: dict = {}  # parquet path -> (mtime, table, rows by identity); a save reads each file once
_LOCK = threading.Lock()  # the daemon's threads archive side by side
_KEEP = 4  # tables held at once; a save walks every day of one project per survivor


def _by_identity(path: Path, identity: str) -> pd.DataFrame:
    """The table cut to one identity, as `read_parquet(filters=identity==)` gives it, the file read once."""
    stamp = path.stat().st_mtime_ns
    with _LOCK:
        hit = _PARTS.get(path)
    if hit is None or hit[0] != stamp:
        frame = pd.read_parquet(path)
        on_index = (
            frame.index.name == "identity"
        )  # metrics.parquet: the identity is its index
        codes, ids = pd.factorize(frame.index if on_index else frame["identity"])
        order = codes.argsort(
            kind="stable"
        )  # stable: each strategy's rows keep their order
        where = {
            i: (a, b)
            for i, a, b in zip(
                ids,
                codes[order].searchsorted(range(len(ids))),
                codes[order].searchsorted(range(1, len(ids) + 1)),
            )
        }
        hit = (stamp, frame, order, where, on_index)
        with _LOCK:
            while len(_PARTS) >= _KEEP:
                del _PARTS[next(iter(_PARTS))]
            _PARTS[path] = hit
    _, frame, order, where, on_index = hit
    a, b = where.get(identity, (0, 0))
    rows = frame.iloc[order[a:b]]
    return rows if on_index else rows.reset_index(drop=True)


def release() -> None:
    """Drop the tables held: a save or an archive is over."""
    with _LOCK:
        _PARTS.clear()


def harvest_rows(folder: Path, identity: str, out: Path) -> dict[str, int]:
    """The cosecha's three tables cut to this identity, every column kept.

    Args:
        folder: harvest/<P>/<D>/<day>/.
        identity: The strategy's identity.
        out: `<version>/harvest/`.

    Returns:
        Rows kept per table.
    """
    out.mkdir()
    counts: dict[str, int] = {}
    for name in ("metrics", "equity", "trades"):
        if not (
            folder / f"{name}.parquet"
        ).exists():  # a harvest of metrics alone (Stop_p90)
            continue
        rows = _by_identity(folder / f"{name}.parquet", identity)
        rows.to_parquet(out / f"{name}.parquet")
        counts[name] = len(rows)
    return counts
