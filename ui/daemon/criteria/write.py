"""One rule of criteria.yaml added, changed or deleted from the window, stamped; and the freeze."""

from typing import Any
import json
from datetime import datetime

from ruamel.yaml.comments import CommentedMap, CommentedSeq
from ruamel.yaml.scalarstring import DoubleQuotedScalarString

from core.assetyaml import read, write
from pipeline.autopilot import criteria
from ui.daemon.criteria.read import FILES, plain, sha

OWNER = "dueño"  # who a write from the window is, in the words the ledger already uses
HOW = "«>= 0.5»: un comparador (" + " ".join(criteria.OPS) + "), un espacio y un número"


def check(rule: dict) -> None:
    """Refuse a rule the judge could not read, with the sentence to show.

    Args:
        rule: As the dialog built it: one fact with a threshold, a median band or a verdict,
            or a compound of such rules; `by` entries are checked folded over their rule.
    """
    parts = rule.get("all") or rule.get("any")
    if "all" in rule or "any" in rule:
        if not parts or "all" in rule and "any" in rule:
            raise ValueError(
                "Una regla compuesta lleva al menos una condición, y es «todas» o "
                "«alguna», no las dos."
            )
        for part in parts:
            check(part)
        return
    if not str(rule.get("fact") or "").strip():
        raise ValueError("Falta el dato que la regla mira.")
    if rule.get("missing", "limbo") not in ("pass", "limbo", "fail"):
        raise ValueError("`missing` solo admite «pass», «limbo» o «fail».")
    if rule.get("else", "limbo") != "limbo":
        raise ValueError("`else` solo admite «limbo»: sin él, no cumplir es Fallo.")
    for _tags, fields in (rule.get("by") or {}).items():
        check({k: v for k, v in rule.items() if k != "by"} | fields)
    if "is" in rule:
        if rule["is"] not in ("pass", "fail"):
            raise ValueError(f"Un veredicto es «pass» o «fail», no «{rule['is']}».")
    elif "alpha" in rule:  # per-cell line: the judge computes it from B
        if not (isinstance(rule["alpha"], (int, float)) and 0 < rule["alpha"] < 1):
            raise ValueError(f"alpha «{rule['alpha']}» no está entre 0 y 1.")
    elif "near_median" in rule:
        for key in ("near_median", "limbo_near_median"):
            if key in rule and not (
                isinstance(rule[key], (int, float)) and rule[key] >= 0
            ):
                raise ValueError(
                    f"La tolerancia «{rule[key]}» no es un número positivo."
                )
    else:
        for key in ("pass", "limbo"):
            if key == "pass" or key in rule:
                try:
                    criteria.holds(0.0, str(rule.get(key)))
                except (ValueError, KeyError) as err:
                    raise ValueError(
                        f"«{rule.get(key)}» no es una condición. Se escribe {HOW}."
                    ) from err


def node(value: object) -> object:
    """A rule as the file writes its own: on one line, its tests in double quotes."""
    if isinstance(value, dict):
        out = CommentedMap((k, node(v)) for k, v in value.items())
        out.fa.set_flow_style()
        return out
    if isinstance(value, list):
        out = CommentedSeq(node(v) for v in value)
        out.fa.set_flow_style()
        return out
    return (
        DoubleQuotedScalarString(value)
        if isinstance(value, str) and " " in value
        else value
    )


def stamp(n: str, what: str, before: object, after: object) -> None:
    """Append one line to the history: when, who, the step, and the rule before and after."""
    line = {
        "at": datetime.now().isoformat(timespec="seconds"),
        "by": OWNER,
        "step": n,
        "what": what,
        "before": before,
        "after": after,
    }
    with FILES["history"].open("a", encoding="utf-8") as f:
        f.write(json.dumps(line, ensure_ascii=False) + "\n")


def opened() -> CommentedMap:
    """criteria.yaml with its comments, or the refusal: frozen criteria are not written."""
    doc = read(FILES["criteria"])
    if doc.get("frozen"):
        raise ValueError(
            f"Los criterios están congelados desde el {doc['frozen']['on']}: "
            "desde la ventana ya no se cambian."
        )
    return doc


def set_rule(
    n: str, at: int | None, rule: dict | None, was: dict | None
) -> dict[str, Any]:
    """Add, change or delete one rule of one step; every other line of the file stays.

    Args:
        n: The step, a key of `steps` that carries a `cut`.
        at: The rule's position in the step; None appends `rule`.
        rule: The new rule; None deletes the one at `at`.
        was: The rule the window showed at `at`: a file that no longer holds it there is
            not written.

    Returns:
        {step, what, note}: `what` is «añadida», «cambiada» or «borrada».
    """
    doc = opened()
    spec = doc["steps"].get(n)
    if spec is None or not spec.get("cut"):
        raise ValueError(
            f"El paso {n} no tiene en criteria.yaml el databank que se corta "
            "(`cut`): sin él el autopilot se pararía al juzgarlo."
        )
    rules = spec["rules"]
    before = plain(rules[at]) if at is not None and at < len(rules) else None
    if at is not None and before != was:
        raise ValueError(
            "criteria.yaml ha cambiado desde que se leyó: recarga y repite."
        )
    if rule is None:
        del rules[at]
        what = "borrada"
    else:
        check(rule)
        if at is None:
            rules.append(node(rule))
        else:
            rules[at] = node(rule)
        what = "añadida" if at is None else "cambiada"
    write(FILES["criteria"], doc)
    stamp(n, what, before, rule)
    return {
        "step": n,
        "what": what,
        "note": f"paso {n}: regla {what}, anotada en el historial",
    }


def freeze() -> dict[str, Any]:
    """Lock the criteria: `frozen` goes into criteria.yaml, first, with the day and the sha of
    what was frozen, and every later write from the window is refused. There is no unfreeze
    here: lifting it is an edit of the file by hand, which git shows."""
    doc = opened()
    mark = {
        "on": datetime.now().date().isoformat(),
        "by": OWNER,
        "sha": sha(plain(doc["steps"])),
    }
    doc.insert(0, "frozen", node(mark))
    write(FILES["criteria"], doc)
    stamp("", "congelado", None, mark)
    return {"frozen": mark, "note": f"criterios congelados el {mark['on']}"}
