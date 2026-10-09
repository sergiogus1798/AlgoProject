"""The pooled profile's looks at the data, as rows of the ledger's contract L1."""

import pandas as pd

from core.study.config import fingerprint
from ledger import record, study
from studies.research.marketProfile import inputs as profile

STEP = 1    # like the profile, the workflow's step 1


def rows(tests: pd.DataFrame, cfg: dict, windows: dict) -> list[dict]:
    """One ledger row per group test: a hypothesis looked at on the group's shared `build` bars.

    Args:
        tests: Judged group tests (many.run).
        cfg: The parsed config.
        windows: (group, timeframe) to the first and last shared bar.

    Returns:
        Rows as `ledger.record.search` stamps them, under the study
        `<GROUP>_<TF>_pooledProfile` — the group stands where an asset would: n_in the
        assets pooled, n_out 1 when the group test was named.
    """
    out = []
    for t in tests.to_dict("records"):
        lo, hi = windows[(t["group"], t["timeframe"])]
        out.append(record.search(
            study.study_id(t["group"], t["timeframe"], "pooledProfile"),
            {"step": STEP, "launched_by": "studies.research.pooledProfile.report",
             "config_hash": fingerprint(cfg), "symbol": t["group"], "timeframe": t["timeframe"],
             "segment": profile.SEGMENT, "window_from": str(lo), "window_to": str(hi),
             "n_in": int(t["assets"]), "n_out": int(t["significant"]),
             "criterion": f"pooledProfile/{t['family']}/{t['measure']}/{t['direction']}",
             "thresholds": {"alpha": cfg["judge"]["alpha"]}, "seeds": [cfg["run"]["seed"]],
             "note": f"p {t['p']:.4g}, q {t['q']:.4g}, {cfg['profile']['nulls']['draws']} "
                     "sorteos conjuntos"}))
    return out
