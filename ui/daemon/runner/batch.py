"""Fold N one-strategy jobs of one study into a single batch job that forks over the cores."""

import json
from datetime import datetime

import psutil

from core import fanout
from ui.daemon import jobs

# 🔬 2026-09-28, owner's feedback «la UI se congela … no usa todos los cores»: a population
# run was one process per strategy (207 for profitShape), each ~1 s of which 0.7 s is Python
# importing pandas and the study, and 16 at a time. One process imports once and forks.
RESERVE = 4              # physical cores left to the window, the daemon and the OS
PER_WORKER_GB = 0.6      # a forked worker's own pages over a 12 MB trades export, rounded up
PLANS = jobs.LOGS / "batches"


def workers(n: int) -> int:
    """How many forked workers a batch of `n` tasks gets now.

    Args:
        n: Tasks in the batch.

    Returns:
        The physical cores minus RESERVE, fewer when the free RAM above the Python floor
        (`jobs.FLOOR_GB`) does not hold that many workers, and never more than `n`.
    """
    spare = psutil.virtual_memory().available / 1e9 - jobs.FLOOR_GB
    return max(1, min(n, fanout.CORES - RESERVE, int(spare / PER_WORKER_GB)))


def fold(planned: list[dict]) -> list[dict]:
    """Group the plans of one study over several strategies into one batch plan each.

    Args:
        planned: `{label, argv, about}` per job, as `runner.table.jobs` or
            `workflow.run.plan` return them.

    Returns:
        The same list where every study with two or more one-strategy plans — and that does
        not fan out on its own (`jobs.WIDE`), which would put a pool inside each worker — is
        one plan running `ui.daemon.runner.batchrun` over them; its `about` keeps the project,
        databank and study, `strategy` empty and `scope` "many", and `weight` is its workers.
    """
    groups: dict[str, list[dict]] = {}
    for p in planned:
        if p["about"].get("strategy") and p["label"] not in jobs.WIDE:
            groups.setdefault(p["label"], []).append(p)
    groups = {label: same for label, same in groups.items() if len(same) >= 2}
    out = [p for p in planned if not (p["label"] in groups and p["about"].get("strategy"))]
    for label, same in groups.items():
        PLANS.mkdir(parents=True, exist_ok=True)
        plan = PLANS / f"{datetime.now():%Y%m%d-%H%M%S-%f}-{label}.json"
        plan.write_text(json.dumps([{"strategy": p["about"]["strategy"], "argv": p["argv"]}
                                    for p in same], ensure_ascii=False), encoding="utf-8")
        n = workers(len(same))
        out.append({"label": label, "weight": n,
                    "argv": ["-m", "ui.daemon.runner.batchrun", "--plan", str(plan),
                             "--workers", str(n)],
                    "about": same[0]["about"] | {"strategy": "", "scope": "many",
                                                 "strategies": len(same)}})
    return out
