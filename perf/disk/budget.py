"""Is the data root bigger than it is allowed to be? One verdict per branch, and an exit code."""

OVER, NEAR, OK, UNBUDGETED = "over", "near", "ok", "unbudgeted"


def top_level(rows: list[dict]) -> list[dict]:
    """The rows that are whole branches rather than sub-branches.

    Args:
        rows: Output of `inventory.tree`.

    Returns:
        Only the depth-1 rows, so bytes are counted once. `tree` reports every level down
        to depth 3, and summing all of them counts the same file three times.
    """
    return [r for r in rows if "/" not in r["branch"]]


def judge(rows: list[dict], cfg: dict) -> list[dict]:
    """Compare each branch against its budget.

    Args:
        rows: Output of `inventory.tree`.
        cfg: What config.load() returned; reads `disk.budget_gb` and `disk.near_share`.

    Returns:
        One row per top-level branch with its budget, its share of it, and a verdict.
        A branch with no budget is reported `unbudgeted` rather than passed silently: the
        point of this table is that a new branch appearing and growing is visible, and a
        default of "unlimited" would hide exactly that.
    """
    budgets = cfg["disk"]["budget_gb"]
    near = cfg["disk"]["near_share"]
    out = []
    for row in top_level(rows):
        gb = row["bytes"] / 1e9
        limit = budgets.get(row["branch"])
        if limit is None:
            verdict, share = UNBUDGETED, None
        else:
            share = gb / limit
            verdict = OVER if share > 1 else NEAR if share >= near else OK
        out.append({"branch": row["branch"], "gb": gb, "budget_gb": limit,
                    "share": share, "files": row["files"], "verdict": verdict})
    return sorted(out, key=lambda r: r["gb"], reverse=True)


def failed(judged: list[dict]) -> list[dict]:
    """Branches that broke their budget.

    Args:
        judged: Output of `judge`.

    Returns:
        The `over` rows. `report.main` exits non-zero when this is non-empty, the same way
        `perf.catalogue` exits non-zero on a regression -- which is what lets either sit in
        cron and be believed.
    """
    return [r for r in judged if r["verdict"] == OVER]


def total(rows: list[dict], cfg: dict) -> dict:
    """The whole data root against its own ceiling.

    Args:
        rows: Output of `inventory.tree`.
        cfg: What config.load() returned; reads `disk.total_gb`.

    Returns:
        Bytes used, the ceiling, the share, and whether it is over. The per-branch budgets
        need not add up to this: they are there to say *where* growth happened, and the
        total is there to say whether it matters yet.
    """
    gb = sum(r["bytes"] for r in top_level(rows)) / 1e9
    limit = cfg["disk"]["total_gb"]
    return {"gb": gb, "budget_gb": limit, "share": gb / limit, "over": gb > limit}
