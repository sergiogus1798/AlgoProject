"""The SPP permutation table: one row per permutation, streamed to Parquet a strategy at a time."""

from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq


def rows(name: str, profile: dict) -> tuple[pd.DataFrame, list[str], list[str]]:
    """One strategy's permutations: its parameter values wide, then every statistic SQX kept.

    Args:
        name: Strategy name.
        profile: Output of `core.optprofile.read` with `permutation_results` true.

    Returns:
        (the frame, its parameter columns, its statistic columns). The frame holds
        `strategy`, `permutation` (-1 is the original, the strategy as SQX saved it and the
        row every permutation is compared against), then the parameters, already numeric,
        then the statistics.
    """
    runs = [(-1, profile["original"])] + list(enumerate(profile["results"]))
    params = pd.DataFrame([dict(kv.partition("=")[::2] for kv in r["params"].split(",") if kv)
                           for _, r in runs]).apply(pd.to_numeric, errors="coerce")
    stats = pd.DataFrame([r["stats"] for _, r in runs])
    frame = pd.concat([pd.DataFrame({"strategy": name, "permutation": [i for i, _ in runs]}),
                       params, stats], axis=1)
    return frame, list(params.columns), list(stats.columns)


def spill(name: str, profile: dict, folder: Path) -> dict:
    """Write one strategy's rows aside, so no process ever holds the whole table.

    Args:
        name: Strategy name.
        profile: As rows() takes it.
        folder: Scratch directory for the per-strategy files.

    Returns:
        {"params", "stats": its columns, "dtypes": column to dtype name}. 🔬 2026-09-26, the
        table is ~1.4 MB per 1,000 permutations in memory: 500 strategies at 10,000 each
        would have been 7 GB in one frame.
    """
    frame, params, stats = rows(name, profile)
    frame.to_parquet(folder / f"{name}.parquet", index=False)
    return {"params": params, "stats": stats,
            "dtypes": {c: str(t) for c, t in frame.dtypes.items()}}


def write(spilled: dict, folder: Path, path: Path) -> int:
    """Stream every spilled strategy into one zstd Parquet with a single schema.

    Args:
        spilled: Strategy name to what spill() returned, in the order to write them.
        folder: Where spill() wrote.
        path: Parquet to write.

    Returns:
        Rows written. Columns `strategy` (categorical), `permutation`, one column per
        parameter any strategy permuted (NaN where this strategy did not), then the
        statistics, each group sorted. A column keeps its dtype only when every strategy
        has it with that dtype; otherwise it is float64, as concatenating them would make
        it. Wide on purpose: a reader that needs four of 154 columns asks Parquet for those.

    Raises:
        SystemExit: A parameter and a statistic share a name, which would silently merge
            two columns.
    """
    names = sorted({c for s in spilled.values() for c in s["params"]})
    stats = sorted({c for s in spilled.values() for c in s["stats"]})
    if set(names) & set(stats):
        raise SystemExit(f"parameter and statistic share a name: {sorted(set(names) & set(stats))}")
    dtypes = {c: ({s["dtypes"].get(c) for s in spilled.values()} | {None}) - {None}
              for c in names + stats}
    dtypes = {c: t.pop() if len(t) == 1 and all(c in s["dtypes"] for s in spilled.values())
              else "float64" for c, t in dtypes.items()}
    categories = sorted(spilled)
    writer, total = None, 0
    for name in spilled:
        frame = pd.read_parquet(folder / f"{name}.parquet").reindex(
            columns=["strategy", "permutation", *names, *stats]).astype(dtypes)
        frame["strategy"] = pd.Categorical(frame["strategy"], categories=categories)
        frame["permutation"] = frame["permutation"].astype("int32")
        table = pa.Table.from_pandas(frame, preserve_index=False)
        writer = writer or pq.ParquetWriter(path, table.schema, compression="zstd")
        writer.write_table(table.cast(writer.schema))
        total += len(frame)
    writer.close()
    return total
