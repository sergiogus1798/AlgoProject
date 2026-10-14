"""The monkey's recorded distributions reproduce its own p: (n_ge or n_le, + 1) / (n + 1)."""

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from engines.nulls import inputs, simulate, verdict
from studies.readings.monkey import one, report
from test_nulls_seed import kept

NAME = "Strategy 1.0"


def test_recorded_row_reproduces_the_p() -> None:
    """Every (rung, statistic) row gives the p nulls.csv holds, on the side the study uses."""
    cfg = inputs.config(["nulls.draws=300", "nulls.seed=7"])
    held = kept(NAME)
    got = {
        "kept": held,
        "seen": simulate.real(held, cfg["statistics"]["report"]),
        "per_rung": {
            r: simulate.nulls(held, r, cfg, NAME) for r in cfg["nulls"]["rungs"]
        },
    }
    rows = one.records(got, NAME, cfg)
    assert len(rows) == len(cfg["nulls"]["rungs"]) * len(cfg["statistics"]["report"])
    for r in rows:
        w = json.loads(r["where"])
        assert r["metric"] == f"p_{w['rung']}_{w['stat']}" and w["seed"] == 7
        side = r["n_ge"] if verdict.GOOD_HIGH[w["stat"]] else r["n_le"]
        p = verdict.pvalue(
            got["seen"][w["stat"]], got["per_rung"][w["rung"]][w["stat"]], w["stat"]
        )
        assert np.isclose((side + 1) / (r["n_finite"] + 1), p)
    # the report signs these rows by their own `strategy` column: it once looked for it inside
    # `where`, which never held it, and ended step 8 (📓 2026-10-08, KeyError 'strategy')
    report.sign(rows, {NAME: "id"})
    assert {r["identity"] for r in rows} == {"id"}
