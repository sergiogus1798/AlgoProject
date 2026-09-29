"""The curated rules file of a firm: loaded as compendium rows and laid over the scraped rows."""

from pathlib import Path

import yaml

from core.datapaths import funding_dir

PHASES = ("phase1", "phase2", "phase3")


def rules_file(firm: str) -> Path:
    """`AlgoData/funding/rules/<firm>.yaml`, edited by hand and by the fundingWatcher agent."""
    return funding_dir() / "rules" / f"{firm}.yaml"


def load(firm: str) -> list[dict]:
    """The firm's rules, one entry per family: a list or '*' in the file becomes several rows."""
    rows = []
    for r in yaml.safe_load(rules_file(firm).read_text(encoding="utf-8")):
        families = r["family"] if isinstance(r["family"], list) else [r["family"]]
        rows += [{**r, "family": f, "checked_on": str(r["checked_on"])} for f in families]
    return rows


def _stage_matches(selector: str, stage: str) -> bool:
    """'phases' = every evaluation phase, 'all' = every stage, else one stage by name."""
    return selector == "all" or stage == selector or (selector == "phases" and stage in PHASES)


def apply(rows: dict, rules: list[dict]) -> None:
    """Write each known, non-conflicting rule value into its column, recording where it came from.

    A curated value wins over the scraped one: it exists precisely because the site is silent or
    ambiguous there. `filled_from` names the rule, with '?' when it is unconfirmed.
    """
    family_of = {p["plan_key"]: p["family"] for p in rows["plans"]}
    for r in rules:
        if "field" not in r or r["value"] is None or r["status"] == "conflict":
            continue
        value = int(r["value"]) if isinstance(r["value"], bool) else r["value"]
        tag = r["rule_key"] + ("" if r["status"] == "confirmed" else "?")
        if r["stage"] == "plan":
            for p in rows["plans"]:
                if r["family"] in ("*", p["family"]):
                    p[r["field"]] = value
            continue
        for s in rows["stages"]:
            if r["family"] in ("*", family_of[s["plan_key"]]) and _stage_matches(r["stage"], s["stage"]):
                s[r["field"]] = value
                s["filled_from"] = ",".join(filter(None, [s["filled_from"], tag]))


def compendium(firm: str, rules: list[dict]) -> list[dict]:
    """The rules as rows of the `rules` table."""
    return [{"firm": firm, "family": r["family"], "rule_key": r["rule_key"],
             "value": None if r["value"] is None else str(r["value"]), "text": r["text"],
             "source": r["source"], "status": r["status"], "checked_on": r["checked_on"]}
            for r in rules]
