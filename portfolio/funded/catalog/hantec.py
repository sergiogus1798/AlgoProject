"""Hantec Trader's catalogue, read from the public JSON its purchase page loads, as normalised rows."""

import json
import urllib.request

SOURCE = "https://myhtrader.hmarkets.com/purchasechallenge?handler=InitState"
STEPS = {1: 1, 2: 2, 3: 3, 99: 0}  # challengeType → evaluation phases; 99 is instant funding


def fetch() -> dict:
    """The raw JSON, without the visitor fields (login state, language)."""
    req = urllib.request.Request(SOURCE, headers={"User-Agent": "Mozilla/5.0",
                                                  "X-Requested-With": "XMLHttpRequest"})
    raw = json.load(urllib.request.urlopen(req, timeout=60))
    return {k: raw[k] for k in ("plans", "discountCodes", "highlightedPlanIds")}


def _stages(p: dict, key: str) -> list[dict]:
    """One row per phase plus the funded stage. NULL = not in the JSON; the overlay may fill it."""
    common = {"plan_key": key, "daily_loss_pct": p["dailyLossLimitPct"],
              "max_loss_pct": p["maxTotalDrawdownPct"],
              "max_loss_mode": "static" if p["staticDrawdown"] else "trailing",
              "time_limit_days": p["timeLimit"], "consistency_pct": 0 if not p["consistency"] else None,
              "news_ok": int(not p["newsProhibited"]), "weekend_ok": int(not p["liquidateFriday"]),
              "reward_share_pct": None, "payout_days": None, "filled_from": ""}
    steps = STEPS[p["challengeType"]]
    rows = [{**common, "stage": f"phase{i}", "min_days": p["minimumRequiredProfitableTradingDays"],
             "profit_target_pct": p["profitTargetPct"] if i == 1 else None}
            for i in range(1, steps + 1)]
    funded = {**common, "stage": "funded", "profit_target_pct": 0,
              "min_days": p["minimumRequiredProfitableTradingDays"] if steps == 0 else None,
              "reward_share_pct": p["profitSharePct"] or None,
              "payout_days": p["rewardFrequency"] or None}
    return rows + [funded]


def normalise(raw: dict) -> dict:
    """Plans, stages and options in the schema of `schema.TABLES`."""
    plans, stages, options = [], [], []
    for p in raw["plans"]:
        family = p["productCategoryName"].lower().replace(" ", "-")
        key = f"hantec:{family}:{int(p['startingBalance'])}:USD"
        plans.append({"plan_key": key, "firm": "hantec", "family": family,
                      "steps": STEPS[p["challengeType"]], "size": p["startingBalance"],
                      "account_ccy": "USD", "price": p["price"], "price_ccy": "USD",
                      "platform": p["platform"], "eas_allowed": None})
        stages += _stages(p, key)
        options += [{"plan_key": key, "option_key": a["key"], "label": a["label"],
                     "effect": a["secondary"] or a["label"], "price_pct": a["pricePct"]}
                    for a in p["addons"] if a["isActive"]]
    return {"plans": plans, "stages": stages, "options": options}
