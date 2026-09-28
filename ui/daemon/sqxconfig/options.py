"""What each value of the SQX settings files may hold: its type, its options or range, or why it is locked.

The option lists live in `lists.py`. The SQX ones there (precisions, engines, stop conditions) are
constants copied BY HAND on 2026-09-27 from the install's settings page
`SQX/internal/web/RESULTS2/result2.js`; nothing reads that file at run time, so a value a new SQX
version adds appears here only once `lists.py` is edited.
"""

from core.assetdata import doctrine, policy
from sqx.projects.acceptance import ESCAPED, READS
from sqx.projects.wfm import WF_TYPES
from sqx.variants.scale import MINUTES
from ui.daemon.sqxconfig import lists as L


def choice(values: list) -> list[dict]:
    """Plain values as the option list the window shows: {value, text} with text = value."""
    return [{"value": v, "text": str(v)} for v in values]


def spans(section: str) -> list[str]:
    """Every segment and every contiguous span a task of this section may run on.

    Args:
        section: The top-level key of _build.yaml, e.g. "mc_retest".

    Returns:
        The segment names of `segments_default`, then each `a..b` in order. A segment
        reserved to some consumers (`reserved_for`) is offered only to a section that is one
        of them: `sqx.projects.setups.span` refuses the rest, and offering it would be a trap.
    """
    segs = policy()["segments_default"]
    allowed = [n for n in segs if section.upper() in segs[n].get("reserved_for", [section.upper()])]
    names = list(segs)
    return allowed + [f"{a}..{b}" for i, a in enumerate(names) for b in names[i + 1:]
                      if a in allowed and b in allowed]


def metrics(index: int) -> list[str]:
    """The metrics one WFM condition may read, given the family its `read` names.

    Args:
        index: Its position in `wfm.conditions`.

    Returns:
        The four special columns for `special`; otherwise the metrics the file's other
        non-special conditions already use — the ones whose thresholds were calibrated on the
        master's 150 cells. A new metric is added in the YAML, with its calibration beside it.
    """
    conds = doctrine()["wfm"]["conditions"]
    if conds[index]["read"] == "special":
        return L.WF_SPECIAL
    return sorted({c["metric"] for c in conds if c["read"] != "special"})


def _number(path: list) -> dict:
    """A number's spec with the range `lists.RANGES` gives it, if any."""
    lo, hi = L.RANGES.get((path[0], path[-1]), L.WFM_AXES.get(path[-2], (None, None))
                          if path[0] == "wfm" and len(path) > 2 else (None, None))
    return {"type": "number", "min": lo, "max": hi}


def _build(path: list, value: object) -> dict | None:
    """The spec of one value of _build.yaml, or None to fall back on the value's own type.

    Args:
        path: Keys and indices leading to it.
        value: Its current value.

    Returns:
        Keys `type` and, when fixed, `options`; `locked` when the window may not write it;
        `warn` when a run already done would be re-read with the new value.
    """
    section, last = path[0], path[-1]
    if last == "precision" or section == "precision":
        return {"type": "choice", "options": L.MC_PRECISIONS if section == "mc_retest"
                else L.PRECISIONS}
    if path == ["engine"]:
        return {"type": "choice", "options": choice(L.ENGINES)}
    if path == ["order_types"]:
        return {"type": "choices", "options": choice(L.ORDER_TYPES)}
    if path == ["money_management", "method"]:
        return {"type": "choice", "options": choice(L.MM_METHODS)}
    if path == ["databank", "stop_condition"]:
        return {"type": "choice", "options": choice(L.STOP_CONDITIONS)}
    if path[:2] == ["crosstf", "timeframes"]:
        return {"type": "choices", "options": choice([t for t in MINUTES if t != last]),
                "warn": L.REREAD.format(who="el estudio crossTF (studies/transfer/crossTF)")}
    if section == "crosschecks" and last in ("build", "default"):
        return {"type": "choices", "options": choice(L.CROSSCHECKS)}
    if last in ("segment", "costs_segment"):
        found = {"type": "choice", "options": choice(spans(section))}
        if section == "wfc":
            found["warn"] = L.REREAD.format(who="la lectura de estructura (studies/readings/structure)")
        return found
    if path == ["wfm", "wf_type"]:
        return {"type": "choice", "options": [{"value": k, "text": f"{k} · {v[1]}"}
                                              for k, v in WF_TYPES.items()]}
    if section == "wfm" and last in ("period_type", "optimization_type"):
        return {"type": "text", "locked": L.LOCKED["fixed"]}
    if path[:2] == ["wfm", "conditions"]:
        if last == "read":
            return {"type": "choice", "options": choice(list(READS))}
        if last == "op":
            return {"type": "choice", "options": choice(list(ESCAPED))}
        if last == "metric":
            return {"type": "choice", "options": choice(metrics(path[2]))}
    if last == "conditions":
        return {"type": "list", "locked": L.LOCKED["conditions"]}
    if last in L.CONTRACT:
        return {"type": "text", "locked": L.LOCKED["contract"]}
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return _number(path)
    return None


def _policy(path: list, value: object) -> dict | None:
    """The spec of one global value of _policy.yaml, or None to fall back on its type."""
    if path[0] == "segments_default" and path[-1] == "spread":
        return {"type": "choice", "options": choice(L.SPREADS)}
    if path == ["swap", "triple_swap_on"]:
        return {"type": "choice", "options": choice(L.WEEKDAYS)}
    if path[0] == "mc_retest" and path[1] in ("unit", "methods", "sqx_factory_default"):
        return {"type": "text", "locked": L.LOCKED["sqx"]}
    if path[0] == "mc_retest" and path[1] == "default_multiples":
        return {"type": "number", "min": 0, "max": None}
    return None


def _classes(path: list, value: object) -> dict | None:
    """The spec of one value of _classes.yaml, or None to fall back on its type."""
    if path[-1] in L.CLASS_CONTRACT:
        return {"type": "list" if isinstance(value, list) else "text", "locked": L.LOCKED["classes"]}
    if path[-1] == "sqx_method":
        return {"type": "choice", "options": choice(L.COMMISSIONS)}
    if path[-1] == "sqx_type":
        return {"type": "choice", "options": choice(L.SWAP_TYPES)}
    return None


def spec(name: str, path: list, value: object) -> dict:
    """What the window may do with one value.

    Args:
        name: "build", "policy", "classes" or "markets" — a key of `assetwrite.SHARED`.
        path: Keys and indices leading to it.
        value: Its current value.

    Returns:
        `type` — "choice" (one of `options`), "choices" (an ordered list, each item one of
        `options`, no repeats), "bool", "number" (with `min`/`max`, None when open), "list"
        (free items) or "text" — plus `options` when fixed, `locked` (the reason) when it may
        not be written here, and `warn` when changing it re-reads past runs.
    """
    if name == "markets":
        return {"type": "list" if isinstance(value, list) else "text", "locked": L.LOCKED["markets"]}
    found = {"build": _build, "policy": _policy, "classes": _classes}[name](path, value)
    if found:
        return found
    if isinstance(value, bool):
        return {"type": "bool", "options": [{"value": True, "text": "sí · true"},
                                            {"value": False, "text": "no · false"}]}
    # SQX's own booleans travel as the strings "true"/"false"; the quotes are kept on write.
    if value in ("true", "false"):
        return {"type": "choice", "options": choice(["true", "false"])}
    if isinstance(value, (int, float)):
        return {"type": "number", "min": None, "max": None}
    return {"type": "list" if isinstance(value, list) else "text"}
