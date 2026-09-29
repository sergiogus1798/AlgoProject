"""FTMO's catalogue, read from the pricing table embedded in its home page, as normalised rows."""

import json
import re
import urllib.request

SOURCE = "https://ftmo.com/en/"
TYPES = {"step_2": ("2step", "objectives", {"step_1": "phase1", "step_2": "phase2",
                                            "step_3": "funded"}),
         "step_1": ("1step", "objectives_step_1", {"step_1": "phase1", "step_3": "funded"})}
FIELDS = ("profit_target", "max_daily_loss", "max_loss", "min_trading_days", "trading_period",
          "best_day", "rewards")


def fetch() -> dict:
    """The `ftmoPricingTable` object the home page carries inline."""
    req = urllib.request.Request(SOURCE, headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64)"})
    page = urllib.request.urlopen(req, timeout=60).read().decode()
    return json.loads(re.search(r"var ftmoPricingTable = (\{.*?\});\s*\n", page, re.S).group(1))


def _number(text: str) -> float | None:
    """'10' or '4 days' or '90%' → the number; 'Unlimited' or '-' → 0 (no such rule); '' → NULL."""
    if not text.strip():
        return None
    found = re.search(r"\d+(\.\d+)?", text)
    return float(found.group()) if found else 0


def _stages(objectives: dict, names: dict, key: str) -> list[dict]:
    """One row per phase plus the funded stage, from the site's objectives table."""
    trailing = "trailing" in objectives["max_loss"]["description"].lower()
    rows = []
    for step, stage in names.items():
        v = {field: _number(objectives[field]["steps"][step]) for field in FIELDS}
        rows.append({"plan_key": key, "stage": stage, "profit_target_pct": v["profit_target"],
                     "daily_loss_pct": v["max_daily_loss"], "max_loss_pct": v["max_loss"],
                     "max_loss_mode": "eod_trailing" if trailing else "static",
                     "min_days": v["min_trading_days"], "time_limit_days": v["trading_period"],
                     "consistency_pct": v["best_day"] or 0,
                     "reward_share_pct": v["rewards"] if stage == "funded" else None,
                     "payout_days": None, "news_ok": None, "weekend_ok": None, "filled_from": ""})
    return rows


def normalise(raw: dict) -> dict:
    """Plans, stages and options in the schema of `schema.TABLES`. Prices are list prices in EUR."""
    data = raw["data"]
    plans, stages, options = [], [], []
    for price_key, (family, objectives_key, names) in TYPES.items():
        for item in data["items"]:
            for challenge, price in zip(item["challenges"], data["prices"][price_key]):
                size = float(challenge["balance"])
                key = f"ftmo:{family}:{int(size)}:{item['currency']}"
                plans.append({"plan_key": key, "firm": "ftmo", "family": family,
                              "steps": len(names) - 1, "size": size,
                              "account_ccy": item["currency"], "price": float(price["price"]),
                              "price_ccy": "EUR", "platform": "MT4/MT5/cTrader/DXtrade",
                              "eas_allowed": None})
                stages += _stages(data[objectives_key], names, key)
                if family == "2step":  # the site does not price it; the rules file says what is known
                    options.append({"plan_key": key, "option_key": "SWING",
                                    "label": "Swing account type",
                                    "effect": "no news or weekend restriction on the funded account",
                                    "price_pct": None})
    return {"plans": plans, "stages": stages, "options": options}
