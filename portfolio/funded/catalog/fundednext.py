"""FundedNext's CFD catalogue, read from the `packages` its home page carries in the Next.js payload."""

import json
import re
import urllib.request

SOURCE = "https://fundednext.com/"
STEPS = {"stellar-2-step": 2, "stellar-lite": 2, "stellar-1-step": 1, "fnl001": 1, "stellar-instant": 0}
# EAs only below $50,000 on MT4/MT5 (help centre, "Is EA allowed in FundedNext?", 2026-09-08).
EA_BELOW = 50000


def _balanced(text: str, start: int) -> str:
    """The JSON array or object opening at `start`, closed at its matching bracket."""
    depth, quoted, escaped = 0, False, False
    for i in range(start, len(text)):
        c = text[i]
        if quoted:
            escaped, quoted = (False, quoted) if escaped else (c == "\\", c != '"')
        elif c == '"':
            quoted = True
        elif c in "[{":
            depth += 1
        elif c in "]}":
            depth -= 1
            if depth == 0:
                return text[start:i + 1]


def fetch() -> dict:
    """The CFD packages (MT5); the futures block (Flex, Legacy, Rapid) is not MT5 and is left out."""
    req = urllib.request.Request(SOURCE, headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64)"})
    page = urllib.request.urlopen(req, timeout=60).read().decode()
    payload = "".join(json.loads(f'"{c}"') for c in
                      re.findall(r'self\.__next_f\.push\(\[1,"(.*?)"\]\)', page, re.S))
    blocks = [json.loads(_balanced(payload, m.end() - 1))
              for m in re.finditer(r'"packages":\[', payload)]
    return {"packages": next(b for b in blocks if any(p["id"] in STEPS for p in b))}


def money(text: str) -> float:
    """'$$1,099.99' → 1099.99."""
    return float(re.sub(r"[^\d.]", "", text))


def _pct(rule: dict, size: float) -> float | None:
    """A rule value as % of the account: a currency amount is divided by the size; 'None' → 0 (no
    such rule); an 'Up to …' split → NULL, because it is a ceiling and not what is paid."""
    value = rule["value"]
    if isinstance(value, (int, float)):
        return round(100 * value / size, 4) if rule.get("unit") == "currency" else float(value)
    if value in ("None", "N/A"):
        return 0
    if value.lower().startswith("up to"):
        return None
    found = re.search(r"\d+(\.\d+)?", value)
    return float(found.group()) if found else None


def _stages(key: str, family: str, size: float, details: dict) -> list[dict]:
    """Phases and the funded stage from the site's per-plan rule lists."""
    rules = {r["id"]: r for r in details["challengeRules"]}
    funded = {r["id"]: r for r in details.get("fundedRewardRules", [])}
    mode = {"Static": "static", "Trailing": "trailing", "EOD Trailing": "eod_trailing"}[
        rules["ddType"]["value"]]
    common = {"plan_key": key, "daily_loss_pct": _pct(rules["dailyDD"], size),
              "max_loss_pct": _pct(rules["maxDD"], size), "max_loss_mode": mode,
              "time_limit_days": 0, "consistency_pct": _pct(rules["consistency"], size)
              if "consistency" in rules else 0, "reward_share_pct": None, "payout_days": None,
              "news_ok": int(rules.get("news", {"value": ""})["value"] == "Allowed") or None,
              "weekend_ok": None, "filled_from": ""}
    targets = [rules[k] for k in ("p1", "p2") if k in rules] or (
        [rules["target"]] if STEPS[family] else [])
    min_days = _pct(rules["minDays"], size) if "minDays" in rules else None
    rows = [{**common, "stage": f"phase{i + 1}", "profit_target_pct": _pct(t, size),
             "min_days": min_days} for i, t in enumerate(targets)]
    payout = funded.get("subsequentWithdrawal", {"value": ""})["value"]
    rows.append({**common, "stage": "funded", "profit_target_pct": 0, "min_days": None,
                 "reward_share_pct": _pct(funded["split"], size) if "split" in funded else None,
                 "payout_days": payout if isinstance(payout, int) else None})
    return rows


def normalise(raw: dict) -> dict:
    """Plans and stages in the schema of `schema.TABLES`, at list price (the crossed-out one when on sale)."""
    plans, stages = [], []
    for package in raw["packages"]:
        family = package["id"]
        for variant in package["challengesSubVariant"]:
            for c in variant["challenges"]:
                size = float(c["numericAccountSize"])
                key = f"fundednext:{family}:{int(size)}:USD"
                plans.append({"plan_key": key, "firm": "fundednext", "family": family,
                              "steps": STEPS[family], "size": size, "account_ccy": "USD",
                              "price": money(c.get("originalPrice") or c["discountedPrice"]),
                              "price_ccy": "USD", "platform": "MT4/MT5",
                              "eas_allowed": int(size < EA_BELOW)})
                stages += _stages(key, family, size, c["details"])
    return {"plans": plans, "stages": stages, "options": []}
