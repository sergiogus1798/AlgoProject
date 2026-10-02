"""What the stored format costs: the same real table written four ways, read back timed."""

import tempfile
import time
from pathlib import Path

import pandas as pd

from core.datapaths import tmp_dir
from perf.inputs import sample

WRITERS = {
    "csv": lambda f, p: f.to_csv(p, index=False),
    "parquet_snappy": lambda f, p: f.to_parquet(p, compression="snappy", index=False),
    "parquet_zstd": lambda f, p: f.to_parquet(p, compression="zstd", index=False),
    "feather": lambda f, p: f.to_feather(p),
}
READERS = {"csv": pd.read_csv, "parquet_snappy": pd.read_parquet,
           "parquet_zstd": pd.read_parquet, "feather": pd.read_feather}


def one(frame: pd.DataFrame, label: str) -> list[dict]:
    """Write and read one table in every format.

    Args:
        frame: The rows to store.
        label: What this table is, carried into the result.

    Returns:
        One row per format: bytes on disk, seconds to write, seconds to read. Read time is
        the one that matters — a table is written once and read on every run.
    """
    rows = []
    for name, write in WRITERS.items():
        path = Path(tempfile.mkstemp(suffix=f".{name}", dir=tmp_dir())[1])
        start = time.perf_counter()
        write(frame, path)
        written = time.perf_counter() - start
        start = time.perf_counter()
        READERS[name](path)
        rows.append({"table": label, "format": name, "rows": len(frame),
                     "bytes": path.stat().st_size, "write_s": written,
                     "read_s": time.perf_counter() - start})
        path.unlink()
    return rows


def compare(cfg: dict) -> list[dict]:
    """The comparison run on the two tables the project stores most of.

    Args:
        cfg: What config.load() returned.

    Returns:
        Format rows for the exported trades and for the exported bars, capped at
        `disk.sample_rows`. These two carry almost every byte under `raw/`, so a format
        decision taken on them is a decision about the data root.
    """
    trades = pd.concat([pd.read_csv(p) for p in sample.files(cfg, "trades")[:5]])
    bars = pd.read_parquet(sample.bars(cfg))
    cap = cfg["disk"]["sample_rows"]
    return one(trades.head(cap), "trades") + one(bars.head(cap), "bars")
