"""One plan's stages and rules, read from the funding catalogue and normalised for the machine."""

import re
import sqlite3

from core.datapaths import funding_dir
from portfolio.funded.catalog.firms import named

_STAGE_ORDER = {"phase1": 1, "phase2": 2, "phase3": 3, "funded": 4}

# Modelling assumptions the catalogue's tables cannot carry (owner, 2026-09-30, PLAN.md §12):
# the order intraday and end-of-day trailing floors update in, never confirmed by either firm.
_MODE_FLAGS = {
    "trailing": {"rule_key": "max_loss_trailing_order", "status": "unconfirmed",
                 "text": "the day's intraday equity high is assumed to raise the trailing floor "
                         "before the day's low is checked (the conservative order)"},
    "eod_trailing": {"rule_key": "max_loss_eod_trailing_basis", "status": "unconfirmed",
                      "text": "assumed to trail the highest end-of-day balance minus max_loss_pct "
                              "of the initial balance, capped at the initial balance"},
}


def _connect() -> sqlite3.Connection:
    """A read-only connection to the funding database — never writes, never refreshes it."""
    path = funding_dir() / "funding.sqlite"
    return sqlite3.connect(f"file:{path}?mode=ro", uri=True)


def plans(max_size: float, ccy: str) -> list[str]:
    """Current plans of the active firms, EAs allowed, at or under a size, in one account currency.

    Args:
        max_size: Account size ceiling, in `ccy`.
        ccy: Account currency, e.g. "USD".

    Returns:
        `plan_key`s ordered by firm, family, size.
    """
    active = named("active")
    db = _connect()
    marks = ",".join("?" * len(active))
    rows = db.execute(
        f"SELECT plan_key FROM plans WHERE valid_to IS NULL AND size <= ? AND account_ccy = ? "
        f"AND eas_allowed = 1 AND firm IN ({marks}) ORDER BY firm, family, size",
        (max_size, ccy, *active)).fetchall()
    return [r[0] for r in rows]


def _min_days(rules: dict, stage_raw: float | None) -> tuple[int | None, str | None, float | None, dict | None]:
    """Resolve a stage's minimum-days rule against the curated compendium.

    Returns:
        `(min_days, kind, profitable_pct, flag)`; `kind` is "trading" or "profitable"; `flag` is a
        `{rule_key, status, text}` dict when the curated rule disagreed with the stage table or is
        itself unconfirmed, else `None`.
    """
    rule = rules.get("min_days")
    if rule is None:
        return (int(stage_raw) if stage_raw is not None else None, "trading", None, None)
    value = rule["value"]
    if value is None:
        return (None, None, None, {"rule_key": "min_days", "status": "unconfirmed", "text": rule["text"]})
    m = re.match(r"(\d+)", value)
    curated = int(m.group(1)) if m else None
    kind = "profitable" if "profitable" in value.lower() else "trading"
    pct = None
    if kind == "profitable":
        pm = re.search(r"([\d.]+)\s*%", value)
        pct = float(pm.group(1)) / 100 if pm else 0.005
    flag = None
    if stage_raw is not None and int(stage_raw) != curated:     # None = not scraped, no conflict
        flag = {"rule_key": "min_days", "status": "conflict",
                "text": f"stage table says {stage_raw}, curated rule says {curated}: {rule['text']}"}
    elif rule["status"] != "confirmed":
        flag = {"rule_key": "min_days", "status": rule["status"], "text": rule["text"]}
    return (curated, kind, pct, flag)


def _consistency(rules: dict, stage_raw: float | None) -> tuple[float, str | None, dict | None]:
    """Resolve a stage's consistency rule against the curated compendium.

    Returns:
        `(consistency, kind, flag)`; `kind` is "best_over_total" (EnhancedX) or
        "best_over_positive_sum" (FTMO 1-step), or `None` when no rule applies.
    """
    formula = rules.get("consistency_formula")
    best_day = rules.get("best_day")
    if formula is not None:
        pm = re.search(r"([\d.]+)\s*%", formula["value"])
        curated, kind, rule = float(pm.group(1)) / 100, "best_over_total", formula
    elif best_day is not None:
        curated, kind, rule = float(best_day["value"]) / 100, "best_over_positive_sum", best_day
    else:
        consistency = (stage_raw or 0) / 100
        return (consistency, None, None)
    flag = None
    stage_pct = (stage_raw or 0) / 100
    if stage_raw is None or abs(stage_pct - curated) > 1e-9:
        flag = {"rule_key": rule["rule_key"] if formula is not None else "best_day", "status": "conflict",
                "text": f"stage table says {stage_pct}, curated rule says {curated}: {rule['text']}"}
    elif rule["status"] != "confirmed":
        flag = {"rule_key": rule["rule_key"], "status": rule["status"], "text": rule["text"]}
    return (curated, kind, flag)


def plan(plan_key: str) -> dict:
    """One plan's stages and rules, normalised, every unconfirmed or conflicting rule named.

    Args:
        plan_key: `firm:family:size:ccy`, as `plans()` lists it.

    Returns:
        `plan_key, firm, family, size, price, price_ccy, stages` (challenge stages then `funded`,
        each a dict of `stage, target, daily_loss, max_loss, max_loss_mode, daily_basis, min_days,
        min_days_kind, profitable_pct, consistency, consistency_kind, time_limit, news_ok,
        weekend_ok`), `flags` (deduplicated by `rule_key`).
    """
    firm, family = plan_key.split(":")[:2]
    db = _connect()
    prow = db.execute("SELECT firm, family, size, price, price_ccy FROM plans WHERE plan_key = ? "
                       "AND valid_to IS NULL", (plan_key,)).fetchone()
    _, _, size, price, price_ccy = prow
    stage_rows = db.execute(
        "SELECT stage, profit_target_pct, daily_loss_pct, max_loss_pct, max_loss_mode, min_days, "
        "time_limit_days, consistency_pct, news_ok, weekend_ok FROM stages WHERE plan_key = ? "
        "AND valid_to IS NULL", (plan_key,)).fetchall()
    rule_rows = db.execute("SELECT rule_key, value, status, text FROM rules WHERE valid_to IS NULL "
                            "AND firm = ? AND family IN ('*', ?)", (firm, family)).fetchall()
    rules = {r[0]: {"rule_key": r[0], "value": r[1], "status": r[2], "text": r[3]} for r in rule_rows}

    flags: dict[str, dict] = {}
    daily_basis = "balance" if firm == "ftmo" else "max_be"
    if firm == "hantec":
        flags["daily_loss_basis"] = {"rule_key": "daily_loss_basis", "status": "unconfirmed",
                                      "text": rules["daily_loss_basis"]["text"]}

    stages = []
    for (stage, target_pct, daily_loss_pct, max_loss_pct, mode, min_days_raw, time_limit,
         consistency_raw, news_ok, weekend_ok) in stage_rows:
        min_days, min_days_kind, profitable_pct, md_flag = _min_days(rules, min_days_raw)
        consistency, consistency_kind, c_flag = _consistency(rules, consistency_raw)
        if consistency > 0 and consistency_kind is None:
            raise NotImplementedError(
                f"{plan_key} stage {stage}: a consistency threshold with no known formula")
        # the curated compendium describes the challenge phases; the funded stage's own scrape gaps
        # (often NULL where a phase concept simply does not apply) are not a real disagreement.
        stage_flags = (md_flag, c_flag) if stage != "funded" else ()
        for flag in (*stage_flags, _MODE_FLAGS.get(mode)):
            if flag is not None:
                flags[flag["rule_key"]] = flag
        stages.append({
            "stage": stage, "target": (target_pct or 0) / 100, "daily_loss": (daily_loss_pct or 0) / 100,
            "max_loss": (max_loss_pct or 0) / 100, "max_loss_mode": mode, "daily_basis": daily_basis,
            "min_days": min_days, "min_days_kind": min_days_kind, "profitable_pct": profitable_pct,
            "consistency": consistency, "consistency_kind": consistency_kind,
            "time_limit": time_limit or 0, "news_ok": bool(news_ok), "weekend_ok": bool(weekend_ok),
        })
    stages.sort(key=lambda s: _STAGE_ORDER[s["stage"]])
    return {"plan_key": plan_key, "firm": firm, "family": family, "size": size, "price": price,
            "price_ccy": price_ccy, "stages": stages, "flags": list(flags.values())}
