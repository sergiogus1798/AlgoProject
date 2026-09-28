"""A partial re-run laid into the stored result it belongs to: its tagged blocks replace their twins, the rest stays."""

import json
from copy import deepcopy


def _key(block: dict) -> tuple[str, str]:
    """What makes two blocks the same drawing: their kind and their selector tags."""
    return block["kind"], json.dumps(block.get("select") or {}, sort_keys=True, ensure_ascii=False)


def merge(stored: dict, part: dict) -> dict:
    """The stored result with one sub-test (a market, a Monte Carlo test) taken from a re-run.

    Args:
        stored: The whole result as the study wrote it, with or without its `partials`.
        part: A partial result (CONTRACT §1: `one.run(..., only=...)`), with its `only`.

    Returns:
        A new result: every tagged block of the re-run replaces the stored block of the same
        kind and tags (or joins the tab, a market the full run never reached), the selectors
        gain the values that were absent, and the re-run's own warnings join, marked. Blocks
        without tags describe the partial run alone and stay the stored ones; so does the
        verdict — a verdict comes from a whole analysis or from none.
    """
    out = deepcopy({k: v for k, v in stored.items() if k != "partials"})
    for ptab in part["tabs"]:
        tagged = [b for b in ptab["blocks"] if b.get("select")]
        tab = next((t for t in out["tabs"] if t["name"] == ptab["name"]), None)
        if tab is None:
            out["tabs"].append(deepcopy(ptab))
            continue
        new = {_key(b) for b in tagged}
        tab["blocks"] = [b for b in tab["blocks"] if _key(b) not in new] + deepcopy(tagged)
        for s in tab.get("selectors") or []:
            offered = [str(o) for o in s["options"]]
            for b in tagged:
                v = b["select"].get(s["key"])
                if v is not None and str(v) not in offered:
                    s["options"].append(v)
                    offered.append(str(v))
    out["warnings"] += [{**w, "text": f"re-ejecución · {w['text']}"} for w in part["warnings"]]
    return out


def notice(stored: dict, part: dict) -> str:
    """The sentence under a merged result's header: which part is new, and from when.

    Args:
        stored: The whole result as the study wrote it.
        part: The partial re-run merged into it.

    Returns:
        The sentence in Spanish.
    """
    return (f"Fusionado: «{part.get('only')}» sale de la re-ejecución del "
            f"{part.get('computed_at')}; todo lo demás, veredicto incluido, es el resultado "
            f"guardado del {stored.get('computed_at')}.")
