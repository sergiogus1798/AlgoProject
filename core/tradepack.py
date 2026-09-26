"""Pack one export's CSVs into the trade library: parsed in parallel, written a strategy at a time."""

import shutil
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from core import fanout, tradestore

# 🔬 2026-09-26, 499 strategies x 10 markets, 12.0 M trades: the old one-frame pack 39.1 s and
# 3.2 GB; this one 28.7 s and 1.1 GB at 8 processes, 25.7 s and 1.8 GB at 16, 23.9 s and 4.1 GB
# at 48. The writing is serial and sets the floor, so more processes only buy memory.
WORKERS = 8
# Where the workers spill, and how to parse, set before the fork.
_PARTS: dict = {}


def _part(path: Path) -> dict:
    """One strategy's CSV parsed and spilled as its own Parquet, in a worker.

    Args:
        path: A CSV orderstocsv wrote.

    Returns:
        What write() needs without reopening it: its columns and dtypes, the values of its
        text columns, whether it kept `Ticket`, whether its blocks came out torn, and where
        it was spilled.
    """
    frame, kept, torn = tradestore._prepared(path, _PARTS["per_market"])
    spill = _PARTS["folder"] / f"{path.stem}.parquet"
    frame.to_parquet(spill, index=False)
    return {"spill": spill, "kept": kept, "torn": torn, "rows": len(frame),
            "dtypes": {c: str(t) for c, t in frame.dtypes.items()},
            "values": {c: set(frame[c].astype(str)) for c in tradestore.CATEGORICAL
                       if c in frame}}


def pack(files: list[Path], out: Path, per_market: bool) -> dict:
    """Every strategy of one export as a single typed Parquet, never whole in memory.

    Args:
        files: One CSV per strategy, as orderstocsv wrote them.
        out: Parquet to write.
        per_market: As in tradestore.frame().

    Returns:
        What tradestore.frame() counts. The file reads back equal to packing
        tradestore.frame(): same rows in the same order, `Ticket` NaN for the strategies
        that did not need it, the text columns categorical over every value of the export.
        Processes, not threads: 🔬 2026-09-25 sixteen threads were slower than one, the
        parse beyond read_csv holds the GIL.
    """
    parts = out.parent / "_parts"
    parts.mkdir(parents=True, exist_ok=True)
    _PARTS.update(folder=parts, per_market=per_market)
    got = dict(fanout.run(_part, {f: f.stat().st_size for f in files}, WORKERS))
    info = [got[f] for f in files]
    columns = list(dict.fromkeys(c for i in info for c in i["dtypes"]))
    # A column missing from some strategy, or typed two ways, is what concat makes float64.
    dtypes = {c: next(iter(kinds)) if len(kinds) == 1 and all(c in i["dtypes"] for i in info)
              else "float64"
              for c in columns
              for kinds in [{i["dtypes"][c] for i in info if c in i["dtypes"]}]}
    categories = {c: sorted(set().union(*(i["values"][c] for i in info if c in i["values"])))
                  for c in tradestore.CATEGORICAL if c in dtypes}
    writer = None
    for i in info:
        frame = pd.read_parquet(i["spill"]).reindex(columns=columns)
        frame = frame.astype({c: t for c, t in dtypes.items() if c not in categories})
        for c, values in categories.items():
            frame[c] = pd.Categorical(frame[c].astype(str), categories=values)
        table = pa.Table.from_pandas(frame, preserve_index=False)
        writer = writer or pq.ParquetWriter(out, table.schema, compression="zstd")
        writer.write_table(table.cast(writer.schema))
    writer.close()
    shutil.rmtree(parts)
    return {"strategies": len(files), "trades": sum(i["rows"] for i in info),
            "columns": columns,
            "kept_ticket": [f.stem for f, i in zip(files, info) if i["kept"]],
            "torn_blocks": [f.stem for f, i in zip(files, info) if i["torn"]]}
