"""The runner of the T0-T4 reading: what the study loaded in, `tf_siblings.parquet` and `tf_mothers.csv` out, beside the old reading."""

from pathlib import Path
from typing import cast

import pandas as pd

from core.study import draws
from engines.market import reprice
from studies.transfer.crossmarket.travel import sizing
from studies.transfer.crossTF import many
from studies.transfer.crossTF.tf import inputs, table

SIBLINGS, MOTHERS = "tf_siblings.parquet", "tf_mothers.csv"


def read(made: pd.DataFrame, trades: dict[str, pd.DataFrame | None], bars: dict[str, pd.DataFrame],
         costs: dict[str, reprice.Costs] | None, cuts: dict | None, params: dict, tf: dict, source: str,
         identity: dict, reason: str = "", sink: list | None = None) -> dict[str, pd.DataFrame]:
    """Both tables from plain data: no file, no asset card, no SQX.

    Args:
        made, trades, bars, costs, cuts, params, tf, source: As `table.measure` takes them;
            `costs` and `cuts` are None when `reason` says the batch cannot be priced.
        identity: Mother name to identity.
        reason: Why nothing can be measured; "" when it can.
        sink: As `table.measure` takes it.

    Returns:
        `siblings` (`table.SIBLINGS`, one row per mother and sibling timeframe) and `mothers`
        (`table.MOTHERS`, one row per mother). With `trades["build"]` None the frame is the
        phase-1 reading: T1 and T2b are limbo with `no_build_data`, `phase1` is final.
    """
    measured = table.blank(made) if reason else table.measure(made, trades, bars, cast(dict, costs), cast(dict, cuts),
                                                               params, tf, source, sink)
    siblings = table.judge(measured, tf, source, reason)
    return {"siblings": siblings, "mothers": table.mothers(siblings, tf, source, identity)}


def write(out: Path, got: many.Loaded, cfg: dict, export: Path, directory: Path,
          before: list[dict] | None = None) -> dict[str, pd.DataFrame]:
    """Read a loaded batch with T0-T4 and write the two files into the run's folder.

    Args:
        out: The study's report folder of this run; the old reading is already written there.
        got: What `crossTF.many.load` returned.
        cfg: What `crossTF.inputs.config` returned, `run.blocks` resolved by that load.
        export: The `CrossTF` `trades.parquet` read.
        directory: The batch's folder, which holds `scaling.parquet` and `blocks.json`.
        before: The old reading's `draws.record` rows, saved in the same single write (a second
            save recompressed the file the first had just written).

    Returns:
        What read() returned; written as `tf_siblings.parquet` and `tf_mothers.csv`, plus `distribuciones.parquet`.
    """
    made = inputs.made(got["plan"])
    costs, cuts, reason = inputs.cards(got["feed"])
    trades = {"oos1": inputs.oos1(got["plan"], got["trades"]),
              "build": None if reason else inputs.build(export, directory, got["identity"], made)}
    kept = []
    before = before or []
    try:
        both = read(made, trades, got["frames"], costs, cuts, sizing.doctrine(), cfg["tf"],
                    cfg["run"]["blocks"][0], got["identity"], reason, kept)
    except Exception:
        draws.save(out, before)       # the old reading's rows are on disk even when this one raises
        raise
    mine = {r["test"] for r in kept}      # a test in both: the later row wins, as two saves did
    draws.save(out, [r for r in before if r["test"] not in mine] + kept)
    both["siblings"].to_parquet(out / SIBLINGS, index=False)
    both["mothers"].to_csv(out / MOTHERS, index=False)
    return both
