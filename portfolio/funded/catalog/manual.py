"""A firm whose site cannot be read by code: its catalogue typed in `AlgoData/funding/manual/<firm>.yaml`, as normalised rows."""

import yaml

from core.datapaths import funding_dir


def fetch(firm: str) -> dict:
    """The typed catalogue, as the file says it."""
    return yaml.safe_load((funding_dir() / "manual" / f"{firm}.yaml").read_text(encoding="utf-8"))


def _stage(key: str, stage: str, rule: dict) -> dict:
    """One stage row from a typed phase or funded block; a missing key is NULL (not known)."""
    return {"plan_key": key, "stage": stage, "profit_target_pct": rule.get("target", 0),
            "daily_loss_pct": rule.get("daily"), "max_loss_pct": rule.get("max"),
            "max_loss_mode": rule.get("mode"), "min_days": rule.get("min_days"),
            "time_limit_days": rule.get("time_limit_days", 0),
            "consistency_pct": rule.get("consistency", 0),
            "reward_share_pct": rule.get("reward_share"), "payout_days": rule.get("payout_days"),
            "news_ok": rule.get("news_ok"), "weekend_ok": rule.get("weekend_ok"), "filled_from": ""}


def normalise(raw: dict, firm: str) -> dict:
    """Plans, stages and options in the schema of `schema.TABLES`."""
    plans, stages, options = [], [], []
    for family in raw["families"]:
        for size, price in family["sizes"].items():
            key = f"{firm}:{family['family']}:{size}:USD"
            plans.append({"plan_key": key, "firm": firm, "family": family["family"],
                          "steps": len(family["phases"]), "size": float(size),
                          "account_ccy": "USD", "price": float(price), "price_ccy": "USD",
                          "platform": family["platform"], "eas_allowed": None})
            stages += [_stage(key, f"phase{i + 1}", p) for i, p in enumerate(family["phases"])]
            stages.append(_stage(key, "funded", family["funded"]))
            options += [{"plan_key": key, **o} for o in family.get("options", [])]
    return {"plans": plans, "stages": stages, "options": options}
