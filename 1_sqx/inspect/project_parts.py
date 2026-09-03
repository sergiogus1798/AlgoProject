"""Read the pieces of one task's XML: databanks, conditions, rankings, cross-checks."""

from xml.etree.ElementTree import Element

# Cross-check element name -> the label SQX shows in the GUI.
CROSSCHECK_LABELS = {
    "RetestWithHigherPrecision": "Retest with higher precision",
    "MonteCarloManipulation": "Monte Carlo - manipulate history",
    "RetestOnAdditionalMarkets": "Retest on additional markets",
    "MonteCarloRetest": "Monte Carlo - retest",
    "WalkForwardOptimization": "Walk-Forward Optimization",
    "WalkForwardMatrix": "Walk-Forward Matrix",
    "WhatIf": "What If",
    "OptProfileSysParamPermutation": "SPP (System Parameter Permutation)",
    "SequentialOptimization": "Sequential Optimization",
}


def text_of(parent: Element, path: str, default: str = None) -> str:
    """Stripped text of a child element.

    Args:
        parent: Element to search under; may be None.
        path: ElementTree path of the child.
        default: Returned when the child is absent or empty.

    Returns:
        The child's text, or the default.
    """
    el = parent.find(path) if parent is not None else None
    return el.text.strip() if el is not None and el.text else default


def render_side(side: Element) -> tuple[str, str]:
    """One side of a condition, as display text.

    Args:
        side: A Left-Side or Right-Side element; may be None.

    Returns:
        (value, metadata). A side is a column reference, a plain number, or another
        column — SPP tasks compare a permuted result against the main one.
    """
    if side is None:
        return "?", ""
    cv = side.find("Column-Value")
    if cv is not None:
        name = cv.get("name") or cv.get("column") or "?"
        bits = [f"resultType={cv.get('resultType')}"]
        bits += [f"{k}={cv.get(k)}" for k in ("sampleType", "subresult", "plType", "format")
                 if cv.get(k) is not None]
        return name, ", ".join(bits)
    nv = side.find("Numeric-Value")
    if nv is not None:
        return nv.get("value"), ""
    return (side.get("valueType") or "?"), ""


def render_conditions(conds: Element) -> tuple[list[dict], dict]:
    """Every condition of a Conditions element, in both schemas.

    Args:
        conds: A Conditions element; may be None.

    Returns:
        (rows, attributes). Acceptance conditions use Left-Side/Comparator/Right-Side;
        GoToTask conditions use a flat list of Field elements instead. `use` is kept
        because a disabled condition stays in the file and gates nothing.
    """
    if conds is None:
        return [], {}
    rows = []
    for c in conds.findall("Condition"):
        fields = c.findall("Field")
        if fields and c.find("Left-Side") is None:
            byt = {f.get("type"): (f.text or "").strip() for f in fields}
            rows.append({"use": c.get("use", "true"),
                         "lhs": byt.get("databank", c.get("type") or "?"),
                         "cmp": byt.get("comparator", "?"),
                         "rhs": byt.get("number", "?"),
                         "meta": f"type={c.get('type')}"})
            continue
        lhs, meta = render_side(c.find("Left-Side"))
        comp = c.find("Comparator")
        rhs, _ = render_side(c.find("Right-Side"))
        rows.append({"use": c.get("use", "true"), "lhs": lhs,
                     "cmp": comp.get("value") if comp is not None else "?",
                     "rhs": rhs, "meta": meta})
    return rows, dict(conds.attrib)


def conditions_table(rows: list[dict], attrs: dict, indent: str = "") -> list[str]:
    """Markdown table of conditions.

    Args:
        rows: Output of render_conditions.
        attrs: The Conditions element's own attributes.
        indent: Prefix for every line, for nesting under a heading.

    Returns:
        Markdown lines. Enabled conditions are ticked, disabled ones are not.
    """
    out = []
    if attrs:
        out.append(f"{indent}Matrix/threshold attrs: " +
                   ", ".join(f"`{k}={v}`" for k, v in attrs.items()))
        out.append("")
    if not rows:
        return out + [f"{indent}_No conditions defined._"]
    out.append(f"{indent}| # | on | metric | test | value | source |")
    out.append(f"{indent}|---|----|--------|------|-------|--------|")
    for i, r in enumerate(rows, 1):
        tick = "✅" if r["use"] == "true" else "⬜"
        out.append(f"{indent}| {i} | {tick} | `{r['lhs']}` | `{r['cmp']}` | "
                   f"**{r['rhs']}** | {r['meta']} |")
    return out


def databanks_of(root: Element) -> tuple[str, str]:
    """Input and output databank of a task.

    Args:
        root: A task's root element.

    Returns:
        (input, output). None means SQX's literal "null", i.e. the task type's default
        databank — not a missing value.
    """
    inp = outp = None
    db = root.find("Databanks")
    if db is None:
        return inp, outp
    for d in db.findall("Databank"):
        value = d.get("value")
        value = None if value in (None, "null") else value
        if d.get("name") == "Input":
            inp = value
        elif d.get("name") == "Output":
            outp = value
    return inp, outp


def rankings_summary(root: Element) -> dict:
    """A task's ranking block: how many strategies it keeps and on what conditions.

    Args:
        root: A task's root element.

    Returns:
        The ranking settings and its conditions, or None when the task has no Rankings.
    """
    r = root.find("Rankings")
    if r is None:
        return None
    stop = r.find("StopCondition")
    return {"type": r.get("type"),
            "MaxStrategies": text_of(r, "MaxStrategies"),
            "DeleteFailedStrategies": text_of(r, "DeleteFailedStrategies"),
            "ForceRunCrossChecks": text_of(r, "ForceRunCrossChecks"),
            "StopCondition": dict(stop.attrib) if stop is not None else {},
            "conditions": render_conditions(r.find("Conditions"))}


def crosschecks_summary(root: Element) -> tuple[dict, list[dict]]:
    """Which robustness cross-checks a task runs, with their settings and thresholds.

    Args:
        root: A task's root element.

    Returns:
        (CrossChecks attributes, enabled checks). Only checks with use="true" are
        returned; the rest sit disabled in the file and do nothing.
    """
    cc = root.find("CrossChecks")
    if cc is None:
        return None, []
    enabled = []
    for child in cc:
        if child.get("use") != "true":
            continue
        settings = []
        s = child.find("Settings")
        if s is not None:
            for el in s.iter():
                if el is s:
                    continue
                if el.attrib:
                    settings.append((el.tag, dict(el.attrib)))
                elif el.text and el.text.strip():
                    settings.append((el.tag, el.text.strip()))
        enabled.append({"tag": child.tag,
                        "label": CROSSCHECK_LABELS.get(child.tag, child.tag),
                        "settings": settings,
                        "conditions": render_conditions(
                            child.find("AcceptanceSettings/Conditions"))})
    return dict(cc.attrib), enabled


def special_summary(ttype: str, root: Element) -> list[tuple]:
    """Extras that only one task type has.

    Args:
        ttype: The task's type, e.g. "Build" or "GoToTask".
        root: That task's root element.

    Returns:
        (label, value) pairs. The label "__conditions__" carries a (rows, attrs) pair
        meant for conditions_table.
    """
    out = []
    if ttype == "ClearDatabanks":
        out.append(("Clears databanks",
                    [d.get("name") for d in root.findall("ClearDatabanks/Databank")]))
    elif ttype == "GoToTask":
        g = root.find("GoToTask")
        if g is not None:
            out.append(("Jumps to task", g.get("task")))
            out.append(("resetEvaluatedCycles", g.get("resetEvaluatedCycles")))
            out.append(("resetActivatedCycles", g.get("resetActivatedCycles")))
            out.append(("__conditions__", render_conditions(g.find("Conditions"))))
    elif ttype == "CustomAnalysis":
        ca = root.find("CustomAnalysis")
        if ca is not None:
            out += [(el.tag, el.text.strip()) for el in ca if el.text and el.text.strip()]
    elif ttype == "Build":
        wtb = root.find("WhatToBuild")
        if wtb is not None:
            out += [(el.tag, dict(el.attrib)) for el in wtb]
    return out
