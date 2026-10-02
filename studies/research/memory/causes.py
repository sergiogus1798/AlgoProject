"""Why a run died: one cause of a closed vocabulary, from the reasons the autopilot's judge wrote."""

import csv
from collections import Counter
from fnmatch import fnmatchcase
from pathlib import Path

from studies.research.memory.sources import CONFIG

CAUSES = CONFIG["causes"]
VOCABULARY = CAUSES["vocabulary"]
BLANK = {"cause": "", "cause_share": "", "causes": "", "rules_out": "", "try_next": ""}


def of_fact(fact: str, value: str) -> str:
    """The cause a failed rule on `fact` names: the first pattern of `causes.facts` it matches,
    a two-sided rule by which side of `split` the value fell; `unclassified` when none does."""
    for rule in CAUSES["facts"]:
        if fnmatchcase(fact, rule["fact"]):
            if "split" not in rule:
                return rule["cause"]
            return rule["below"] if float(value) < rule["split"] else rule["above"]
    return "unclassified"


def of_reason(reason: str) -> set[str]:
    """The causes in one strategy's reason, `<state>: <fact>=<value>` parts joined by "; ".

    Only `fail:` parts count: a limbo goes on, and the dev draw and the scaled siblings are
    not failures of the strategy.
    """
    parts = [p[len("fail: "):].rpartition("=") for p in reason.split("; ") if p.startswith("fail: ")]
    return {of_fact(fact, value) for fact, _, value in parts}


def of_verdicts(paths: list[Path]) -> Counter:
    """How many failed strategies each cause took, over some judging steps' verdict.csv.

    Returns:
        Cause → strategies, a strategy counting once per cause it failed by; the key "" holds
        how many strategies failed at all.
    """
    seen = Counter()
    for path in paths:
        with open(path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                found = of_reason(row["reason"] or "")
                seen.update(found)
                seen[""] += bool(found)
    return seen


def verdicts(folder: Path, stage: str) -> list[Path]:
    """The newest verdict.csv of each judging step that cuts into `stage`, in a project's
    autopilot folder (`<root>/<project>/<stamp>/paso-<n>/verdict.csv`)."""
    found = [sorted(folder.glob(f"*/paso-{n}/verdict.csv")) for n in CAUSES["judged_at"].get(stage, [])]
    return [runs[-1] for runs in found if runs]


def ranked(seen: dict) -> list[str]:
    """The causes counted, the one that took most strategies first; ties in the vocabulary's order."""
    order = list(VOCABULARY)
    return sorted((c for c in seen if c), key=lambda c: (-seen[c], order.index(c)))


def named(cause: str, seen: Counter | None = None) -> dict:
    """A cause with its two texts and, when it was counted, its share and the other causes."""
    others = [c for c in ranked(seen or {})]
    return {"cause": cause,
            "cause_share": f"{seen[cause]}/{seen['']}" if others else "",
            "causes": ";".join(f"{c}:{seen[c]}" for c in others),
            "rules_out": VOCABULARY[cause]["rules_out"], "try_next": VOCABULARY[cause]["try_next"]}


def typed(row: dict, folder: Path) -> dict:
    """The cause of one attempt.

    Args:
        row: An attempts row with `outcome`, `died_at` and `hypothesis` filled.
        folder: The project's autopilot folder.

    Returns:
        `cause`, `cause_share` (strategies it took / strategies that failed, '' when no judge
        wrote reasons), `causes` (every cause counted, `name:n` joined by ";"), `rules_out`
        and `try_next`. A failed run is `infrastructure`; a dead one takes the cause that
        failed the most strategies at the step that emptied it (ties: the vocabulary's
        order), or its stage's default when no reason was written; a run that did not die
        whose build contradicts its sheet is `hypothesis_mismatch`. A dead run with a
        mismatch keeps its death as the cause and lists the mismatch in `causes`. Anything
        else has none.
    """
    kind = row["outcome"].split("@")[0]
    mismatch = row["hypothesis"] == "mismatch"
    if kind == "failed":
        return named("infrastructure")
    if kind != "died":
        return named("hypothesis_mismatch") if mismatch and kind == "survivors" else dict(BLANK)
    seen = of_verdicts(verdicts(folder, row["died_at"]))
    first = ranked(seen)
    got = named(first[0], seen) if first else named(CAUSES["stage"][row["died_at"]])
    if mismatch:
        got["causes"] = ";".join(filter(None, [got["causes"] or got["cause"], "hypothesis_mismatch"]))
    return got
