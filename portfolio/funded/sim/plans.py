"""A plan as the bank simulation reads it: the rule machine's plan, an add-on set applied, and the funded stage's cash terms."""

import itertools
import sqlite3
from typing import Any, TypedDict, cast

from core.paths import funding_dir
from portfolio.funded.rules import catalog


class Terms(catalog.Plan):
    """One plan with one add-on set: the machine's plan plus the funded cash terms."""

    options: str
    share: float
    payout_days: Any
    refund: Any
    lock: Any


class Cash(TypedDict):
    """The `kernel.TERMS` of a plan under the owner's policy, money in USD."""

    price: float
    share: float
    cycle: int
    refund: float
    cushion: float
    fee: float
    tax: float
    budget: float
    rebuy: float
    lock: float


# What this simulation assumes about a funded account and no catalogue table states — carried
# into every result beside the plan's own flags, as the rule machine does with its modes.
ASSUMED = [
    {"rule_key": "funded_payout_eligibility", "status": "unconfirmed",
     "text": "the funded stage's minimum days and consistency are counted since the previous "
             "payout, and a payout needs a positive closed profit in that cycle"},
    {"rule_key": "funded_first_payout", "status": "unconfirmed",
     "text": "the first payout is due one payout cycle after the funded stage starts, on the "
             "closed balance; calendar days become path days at days_per_year / 365"},
]
_SIMULATED = ("p1_target_pct", "p2_target_pct", "p3_target_pct", "max_loss_pct", "min_days",
              "consistency_pct", "reward_share_pct", "payout_days")
_NO_MIN_DAYS = ("NO_MINIMUM_TRADING_DAYS", "NO_MINIMUM_PROFITABLE_DAYS")


class Gap(ValueError):
    """Values the catalogue does not hold and nobody supplied; `missing` maps each `gaps` key to what it means."""

    def __init__(self, missing: dict[str, str]) -> None:
        """Remember the config keys that fill the gaps."""
        super().__init__("; ".join(f"gaps.{key}: {what}" for key, what in missing.items()))
        self.missing = missing


def _db() -> sqlite3.Connection:
    """The funding database, read-only."""
    db = sqlite3.connect(f"file:{funding_dir() / 'funding.sqlite'}?mode=ro", uri=True)
    db.row_factory = sqlite3.Row
    return db


def addon_sets(plan_key: str, max_set: int) -> tuple[list[str], list[str]]:
    """The add-on sets of a plan the simulation can tell apart, up to a size.

    Returns:
        `(simulated, skipped)`: `options` strings as the `combos` table spells them, the empty
        set first; `skipped` are sets whose effect is on nothing the simulation reads (news,
        weekend, an unmodelled extra) or is unknown to the catalogue — price only.
    """
    db = _db()
    base = db.execute("SELECT * FROM combos WHERE plan_key = ? AND options = ''", (plan_key,)).fetchone()
    simulated, skipped = [""], []
    for row in db.execute("SELECT * FROM combos WHERE plan_key = ? AND options != ''", (plan_key,)):
        names = row["options"].split(",")
        if len(names) > max_set:
            continue
        # every member must move a rule on its own: a set padded with a no-effect add-on only costs more
        singles = [db.execute("SELECT * FROM combos WHERE plan_key = ? AND options = ?",
                              (plan_key, name)).fetchone() for name in names]
        moves = all(any(s[c] != base[c] for c in _SIMULATED) or name in _NO_MIN_DAYS
                    for s, name in zip(singles, names))
        (simulated if moves and not row["extras"] else skipped).append(row["options"])
    return simulated, skipped


def _gap(gaps: dict, key: str, what: str, missing: dict[str, str]) -> object:
    """The owner's value for a catalogue gap; a gap nobody filled is noted in `missing`."""
    if gaps.get(key) is None:
        missing[key] = what
    return gaps.get(key)


def _refund(db: sqlite3.Connection, firm: str, family: str, gaps: dict,
            missing: dict[str, str]) -> tuple[bool, list[dict]]:
    """Whether the fee comes back with the first payout, and the flags that reading carries."""
    rules = {r["rule_key"]: r for r in db.execute(
        "SELECT * FROM rules WHERE valid_to IS NULL AND firm = ? AND family IN ('*', ?) "
        "ORDER BY family = '*' DESC", (firm, family))}
    rule = rules.get("fee_refund")
    flags = [{"rule_key": k, "status": rules[k]["status"], "text": rules[k]["text"]}
             for k in ("fee_refund", "fee_refund_scope", "reward_share_base")
             if k in rules and rules[k]["status"] != "confirmed"]
    if rule is None or rule["value"] not in ("True", "False"):
        value = _gap(gaps, f"{firm}_fee_refund", f"¿{firm} devuelve la cuota con el primer cobro? (true/false)",
                     missing)
        return bool(value), [f for f in flags if f["rule_key"] != "fee_refund"] + [{
            "rule_key": "fee_refund", "status": "unconfirmed",
            "text": f"not in the catalogue; the owner's input gaps.{firm}_fee_refund = {value}"}]
    return rule["value"] == "True", flags


def terms(plan_key: str, options: str, gaps: dict) -> Terms:
    """One plan with one add-on set, ready for `bank`: the machine's plan plus the funded cash terms.

    Args:
        plan_key: `firm:family:size:ccy`.
        options: An add-on set as `combos.options` spells it; "" = the bare plan.
        gaps: The config's `gaps` section — the owner's reading where the catalogue holds none.

    Returns:
        `catalog.plan()`'s dict with the add-ons applied to its stages and `price`, plus
        `options`, `share` (fraction), `payout_days` (calendar), `refund` (bool), `lock` (bool:
        a trailing funded floor moves to the initial balance at the first payout); `flags` gains
        every unconfirmed funded-stage rule used and `ASSUMED`.

    Raises:
        Gap: The funded stage lacks the split, the payout frequency or the refund.
    """
    plan = catalog.plan(plan_key)
    db = _db()
    base = db.execute("SELECT * FROM combos WHERE plan_key = ? AND options = ''", (plan_key,)).fetchone()
    combo = db.execute("SELECT * FROM combos WHERE plan_key = ? AND options = ?",
                       (plan_key, options)).fetchone()
    by = {s["stage"]: s for s in plan["stages"]}
    for i in (1, 2, 3):
        if combo[f"p{i}_target_pct"] != base[f"p{i}_target_pct"]:
            by[f"phase{i}"]["target"] = combo[f"p{i}_target_pct"] / 100
    for stage in plan["stages"]:
        stage["max_loss"] += ((combo["max_loss_pct"] or 0) - (base["max_loss_pct"] or 0)) / 100
        if set(options.split(",")) & set(_NO_MIN_DAYS):
            stage["min_days"] = 0
        if combo["consistency_pct"] != base["consistency_pct"] and stage["stage"] != "funded":
            # combos carries the first phase's value only; 0 after REMOVE_CONSISTENCY_CHALLENGE
            stage["consistency"] = (combo["consistency_pct"] or 0) / 100
    firm, family = plan["firm"], plan["family"]
    tag = f"{firm}_{family}"
    missing: dict[str, str] = {}
    refund, flags = _refund(db, firm, family, gaps, missing)
    share = combo["reward_share_pct"] if combo["reward_share_pct"] is not None else _gap(
        gaps, f"{tag}_reward_share_pct", f"reparto de la cuenta fondeada de {firm} {family}, en %", missing)
    payout_days = combo["payout_days"] or _gap(
        gaps, f"{tag}_payout_days", f"cada cuántos días naturales cobra la fondeada de {firm} {family}", missing)
    lock = False
    if by["funded"]["max_loss_mode"] != "static":
        reading = _gap(gaps, f"{tag}_floor_after_payout",
                       f"suelo de pérdida máxima de la fondeada de {firm} {family} tras un cobro: stays (no se "
                       f"mueve con el retiro) o initial (queda fijo en el balance inicial tras el primer retiro)",
                       missing)
        if reading not in (None, "stays", "initial"):
            missing[f"{tag}_floor_after_payout"] = f"{reading!r} no vale: sólo stays o initial"
        lock = reading == "initial"
        flags.append({"rule_key": "funded_floor_after_payout", "status": "unconfirmed",
                      "text": f"not in the catalogue; the owner's input gaps.{tag}_floor_after_payout = {reading}"})
    if missing:
        raise Gap(missing)
    seen = {f["rule_key"] for f in plan["flags"]}
    return {"plan_key": plan["plan_key"], "firm": plan["firm"], "family": plan["family"], "size": plan["size"],
            "price": combo["price"], "price_ccy": plan["price_ccy"], "stages": plan["stages"],
            "options": options, "share": cast(float, share) / 100,
            "payout_days": payout_days, "refund": refund, "lock": lock,
            "flags": plan["flags"] + [f for f in flags + ASSUMED if f["rule_key"] not in seen]}


def cash(plan: Terms, owner: dict, days_per_year: float, rebuy: str) -> Cash:
    """The `kernel.TERMS` of a plan under the owner's policy, money in USD.

    Args:
        plan: What `terms` returned.
        owner: The config's `owner` section, complete (`inputs.refuse` checked it).
        days_per_year: Path days in a year — a fact of the path set.
        rebuy: One policy of `owner.rebuy`: `same_plan` or `none`.
    """
    fx = owner["eurusd"] if plan["price_ccy"] == "EUR" else 1.0
    return {"price": plan["price"] * fx, "share": plan["share"],
            "cycle": max(1, round(plan["payout_days"] * days_per_year / 365)),
            "refund": float(plan["refund"]), "cushion": owner["payout_cushion"],
            "fee": owner["payout_fee"], "tax": owner["tax_rate"],
            "budget": owner["budget_eur"] * owner["eurusd"],
            "rebuy": float(rebuy == "same_plan"), "lock": float(plan["lock"])}


def risk_grid(plan: Terms, challenge: list[float], funded: list[float]) -> list[dict[str, float]]:
    """Every risk-per-phase combination of a plan: one level per challenge stage, one for funded."""
    names = [s["stage"] for s in plan["stages"][:-1]]
    return [dict(zip([*names, "funded"], levels))
            for levels in itertools.product(*[challenge] * len(names), funded)]
