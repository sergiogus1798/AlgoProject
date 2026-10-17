"""The monkey's z for EVERY strategy of a harvest, not only those the cascade lets reach 3c.

The IS recipe (encargo 50 §5.2 R1, owner L5 A, 2026-10-17) reads z_mono over the whole
unselected population. The gate computes it only for who survives levels 0-2 (~20 % of a
GBPJPY build), so a filter measured on that z would carry level 0's OOS selection. This
reruns level 1a (the per-trade table) and level 3c (the monkey) on everybody, into a folder
of its own: the gate's scorecard, its verdict and step 8's cut are not touched.
"""

from datetime import date
from pathlib import Path

import pandas as pd

from core.paths import latest_harvest, report_dir
from studies.screening.gate import inputs, level1a, level3c


def everyone(
    project: str, feed: str, folder: Path | None = None, databank: str = "Results"
) -> pd.DataFrame:
    """z_mono and R3's t for every strategy the build and the retest both hold.

    Args:
        project: An SQX project whose step 8 left a harvest, e.g. a `Test_Calib_` one.
        feed: SQX feed name, e.g. "GBPJPY_M1".
        folder: The harvest to read. Omitted, the databank's newest — which after step 8's
            cut holds only the survivors: the whole population is the one the cut set aside
            under `<databank>/_aparte/<day>.<time>`.
        databank: The harvested databank.

    Returns:
        Indexed by identity: level 3c's FACTS (`z_mono`, `mono_p`, the rungs, `mono_seed`)
        and level 1a's `drift_excess_t`. Also written as `mono_all.parquet` in
        `<report_dir>/gate-all`, beside the trade table level 1a leaves there.
    """
    cfg = inputs.config([])
    harvest = inputs.load(folder or latest_harvest(project, databank))
    out = report_dir(project, databank, date.today().isoformat()) / "gate-all"
    out.mkdir(parents=True, exist_ok=True)
    data = inputs.staged(
        harvest, feed, inputs.timeframe(harvest["metrics"], cfg, []), out
    )
    data["keep_draws"] = False  # ponytail: no per-monkey distributions, z only
    who = pd.Index(data["metrics"].index)
    r3 = level1a.run(data, who, cfg)  # first: it leaves data["oos"], which 3c reads
    frame = level3c.run(data, who, cfg).join(r3)
    frame.to_parquet(out / "mono_all.parquet", compression="zstd")
    return frame
