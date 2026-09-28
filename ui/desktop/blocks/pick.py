"""Which stored blocks the chosen selector values pick, and which block sits beside which: filters, never recomputes."""

from ui.text.glossary import label


def selectors(tab: dict) -> list[dict]:
    """A tab's selectors, or one per tag when its blocks are tagged but it offers none.

    Args:
        tab: One contract tab.

    Returns:
        The tab's own selectors; for a partial re-run, which tags its blocks and writes no
        selector (monteCarlo's `_rerun`), one per tag key, its values in order of appearance —
        otherwise no block would agree with a pick and the tab would draw nothing.
    """
    if tab.get("selectors"):
        return tab["selectors"]
    found: dict[str, list[str]] = {}
    for b in tab["blocks"]:
        for k, v in (b.get("select") or {}).items():
            seen = found.setdefault(k, [])
            if str(v) not in seen:
                seen.append(str(v))
    return [{"key": k, "label": label(k), "options": v, "default": v[0]} for k, v in found.items()]


def picked(tab: dict, chosen: dict) -> dict[str, str]:
    """The value each selector of a tab takes, as text.

    Args:
        tab: One contract tab.
        chosen: {selector key: option}. A value this tab does not offer falls back to the
            tab's own default, so two runs whose options differ still both draw something.

    Returns:
        {key: option}, compared as text: a combo hands back text, the JSON may hold a number.
    """
    out = {}
    for s in selectors(tab):
        want = str(chosen.get(s["key"]))
        out[s["key"]] = want if want in [str(o) for o in s["options"]] else str(s["default"])
    return out


def shown(tab: dict, chosen: dict) -> list[dict]:
    """The blocks of a tab that agree with the chosen selector values.

    Args:
        tab: One contract tab.
        chosen: As in `picked`.

    Returns:
        The blocks to draw: those untagged, and those whose every `select` value is chosen.
        Nothing is recomputed; the study already stored every combination (CONTRACT §1).
    """
    pick = picked(tab, chosen)
    return [b for b in tab["blocks"]
            if all(pick.get(k) == str(v) for k, v in (b.get("select") or {}).items())]


def pairs(left: list[dict], right: list[dict]) -> list[tuple[dict | None, dict | None]]:
    """Each block beside its counterpart: same kind and title first, else the next of its kind.

    Args:
        left, right: The blocks each side shows.

    Returns:
        (left, right) rows in the left's order, the right's leftovers at the end.
    """
    free = list(right)
    out = []
    for b in left:
        same = [r for r in free if (r["kind"], r.get("title")) == (b["kind"], b.get("title"))]
        kin = [r for r in free if r["kind"] == b["kind"]]
        twin = (same or kin or [None])[0]
        if twin is not None:
            free.remove(twin)
        out.append((b, twin))
    return out + [(None, r) for r in free]
