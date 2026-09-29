"""Every add-on combination of every plan, priced, with the rules it leaves in force."""

import itertools
import re

# What each add-on does to the rules: (column, stages, how). An add-on not listed here is still
# priced and combined; it lands in `extras`, and the refresh names it so the effect gets written.
EFFECTS = {
    "PROFIT_SHARE_FLEXIBLE": [("reward_share_pct", "funded", "set")],
    "MAX_DRAWDOWN": [("max_loss_pct", "all", "add")],
    "PROFIT_TARGET": [("profit_target_pct", "phases", "add")],
    "CONSISTENCY_RULE": [("consistency_pct", "all", "add")],
    "REMOVE_CONSISTENCY_CHALLENGE": [("consistency_pct", "phases", "zero")],
    "WEEKLY_PAYOUT": [("payout_days", "funded", "seven")],
    "NEWS_TRADING": [("news_ok", "all", "one")],
    "WEEKEND_HOLDING_NEWS_TRADING": [("news_ok", "all", "one"), ("weekend_ok", "all", "one")],
    "NO_MINIMUM_TRADING_DAYS": [("min_days", "all", "zero")],
    "NO_MINIMUM_PROFITABLE_DAYS": [("min_days", "all", "zero")],
    "SWING": [("news_ok", "funded", "one"), ("weekend_ok", "funded", "one")],
}
RULE_ONLY = {"FIRST_PAYOUT_ON_DEMAND", "EXTRA_TIME_HOURS"}  # no column to change, noted in extras


def _number(effect: str) -> float:
    """'+2%' → 2.0, '-2%' → -2.0, '95%' → 95.0."""
    return float(re.search(r"[-+]?\d+(\.\d+)?", effect).group())


def _change(stage: dict, column: str, how: str, effect: str) -> None:
    """Apply one effect to one stage row in place. An unknown value (NULL) stays unknown."""
    if how == "set":
        stage[column] = _number(effect)
    elif how == "add" and stage[column]:
        stage[column] = stage[column] + _number(effect)
    elif how in ("zero", "one", "seven"):
        stage[column] = {"zero": 0, "one": 1, "seven": 7}[how]


def _row(plan: dict, stages: list[dict], chosen: tuple[dict, ...]) -> dict:
    """One combination: price, and the rules after its add-ons."""
    stages = [dict(s) for s in stages]
    for o in chosen:
        for column, where, how in EFFECTS.get(o["option_key"], []):
            for s in stages:
                if where == "all" or s["stage"] == where or (where == "phases" and s["stage"] != "funded"):
                    _change(s, column, how, o["effect"])
    by = {s["stage"]: s for s in stages}
    first, funded = by.get("phase1", by["funded"]), by["funded"]
    return {"plan_key": plan["plan_key"], "options": ",".join(o["option_key"] for o in chosen),
            "price": round(plan["price"] * (1 + sum(o["price_pct"] for o in chosen) / 100), 2),
            "price_ccy": plan["price_ccy"], "firm": plan["firm"], "family": plan["family"],
            "size": plan["size"], "eas_allowed": plan["eas_allowed"],
            **{f"p{i}_target_pct": by[f"phase{i}"]["profit_target_pct"] if f"phase{i}" in by else None
               for i in (1, 2, 3)},
            "daily_loss_pct": first["daily_loss_pct"], "max_loss_pct": first["max_loss_pct"],
            "max_loss_mode": first["max_loss_mode"], "min_days": first["min_days"],
            "consistency_pct": first["consistency_pct"],
            "reward_share_pct": funded["reward_share_pct"], "payout_days": funded["payout_days"],
            "news_ok": funded["news_ok"], "weekend_ok": funded["weekend_ok"],
            "extras": ",".join(o["option_key"] for o in chosen if o["option_key"] not in EFFECTS)}


def build(rows: dict) -> list[dict]:
    """All subsets of each plan's priced add-ons (2^n rows per plan, the empty set included)."""
    stages, options = {}, {}
    for s in rows["stages"]:
        stages.setdefault(s["plan_key"], []).append(s)
    for o in rows["options"]:
        if o["price_pct"] is not None:
            options.setdefault(o["plan_key"], []).append(o)
    return [_row(p, stages[p["plan_key"]], chosen)
            for p in rows["plans"]
            for n in range(len(options.get(p["plan_key"], [])) + 1)
            for chosen in itertools.combinations(options.get(p["plan_key"], []), n)]


def unmodelled(rows: dict) -> set[str]:
    """Add-on keys whose effect on the rules nobody has written into `EFFECTS` yet."""
    return {o["option_key"] for o in rows["options"]} - set(EFFECTS) - RULE_ONLY
