"""A strategy's result as one entity across the whole project (owner, 2026-09-30): the one stored
result its page shows, chosen among `hits.sources` — its identity first, else its name."""

from collections.abc import Iterable

from ui.daemon.results import hits, stale, store
from ui.daemon.results.slice import slice_for, verdict_row, whole


def pick(found: Iterable[dict], identity: str) -> tuple[dict | None, list[dict]]:
    """The candidate to show: the first that carries this identity, else the first by name.

    Args:
        found: `hits.sources`, in preference order.
        identity: The identity asked for, "" to take the first.

    Returns:
        (the hit or None, `{day, reason}` of every folder passed over before it). Stops at
        the first identity match, so a strategy found at home reads nothing further.
    """
    first, skipped, before = None, [], []
    for h in found:
        if "skip" in h:
            where = f" ({h['elsewhere']})" if h.get("elsewhere") else ""
            (skipped if first is None else before).append(
                {"day": f"{h['day']}{where}", "reason": h["skip"]})
            continue
        if identity and h["identity"] == identity:
            return h, skipped + before
        if first is None:
            first = h
        if not identity:
            break
    return first, skipped


def other(hit: dict, identity: str) -> bool:
    """Whether a hit found by name is a different XML than the one asked for (shown with a
    discreet marker, never hidden: owner, 2026-09-30). Unknown identity is not «other»."""
    return bool(identity and hit["identity"] and hit["identity"] != identity)


def judged(hit: dict, study: str, project: str) -> tuple[bool, str | None]:
    """`stale.judge` of one hit."""
    return stale.judge(study, hit["config_hash"], project, hit["manifest"], hit["population"])


def full(hit: dict, identity: str) -> dict:
    """The contract result a hit points at, as the strategy's page shows it.

    Args:
        hit: A hit of `hits.sources`.
        identity: The identity asked for; a population result that says nothing per
            strategy carries it, being nobody's in particular.

    Returns:
        The result dict, sliced to this strategy when it is the population's run.
    """
    got, _ = store.load(hit["path"])
    kind, alias = hit["kind"], hit["alias"]
    if kind in ("file", "population"):
        return got
    if kind == "whole":
        return {**whole(got, alias), "identity": identity or None}
    row = (store.verdicts(hit["path"].parent) or {}).get(alias)
    mine = slice_for(got, alias) if kind == "slice" else None
    return {**(mine or verdict_row(got, row, alias)), "identity": hit["identity"]}


def meta(hit: dict | None, skipped: list[dict], study: str, project: str,
         identity: str) -> dict:
    """The `meta` beside a result: where it came from and whether it is current.

    Returns:
        day, path, config_hash, current_hash, stale, computed_at, skipped, elsewhere (the
        databank it came from, None for this one), other_identity, note (which lote, when
        it came from one).
    """
    if hit is None:
        return {"day": None, "path": None, "config_hash": None, "current_hash": None,
                "stale": False, "computed_at": None, "skipped": skipped, "elsewhere": None,
                "other_identity": False, "note": ""}
    old, current = judged(hit, study, project)
    return {"day": hit["day"], "path": str(hit["path"]), "config_hash": hit["config_hash"],
            "current_hash": current, "stale": old, "computed_at": hit["computed_at"],
            "skipped": skipped, "elsewhere": hit["elsewhere"],
            "other_identity": other(hit, identity), "note": hit["note"]}


def result(project: str, databank: str, study: str, strategy: str, identity: str,
           day: str) -> dict:
    """The newest contract result of a study for the population or one strategy.

    Args:
        project: SQX project name.
        databank: The databank the page opened from.
        study: Study key.
        strategy: Strategy name, "" for the population result (this databank only).
        identity: The strategy's identity, "" to trust the name.
        day: A report day, "" for the newest.

    Returns:
        `result` (the contract dict or None) and `meta` as `meta`.
    """
    hit, skipped = pick(hits.sources(project, databank, study, strategy, day), identity)
    return {"result": full(hit, identity) if hit else None,
            "meta": meta(hit, skipped, study, project, identity)}


def history(project: str, databank: str, study: str, strategy: str, identity: str) -> dict:
    """Every run of the place the page's result comes from, newest first.

    Args:
        project, databank, study, strategy, identity: As `result`.

    Returns:
        `runs` — day, config_hash, computed_at, state, label, stale, elsewhere — of the
        databank or lote the chosen result lives in, and `skipped`, its days passed over.
    """
    found = list(hits.sources(project, databank, study, strategy))
    hit, _ = pick(found, identity)
    if hit is None:
        return {"runs": [], "skipped": [{"day": h["day"], "reason": h["skip"]} for h in found]}
    mine = [h for h in found if h.get("origin") == hit.get("origin")]
    runs = [{"day": h["day"], "config_hash": h["config_hash"], "computed_at": h["computed_at"],
             "state": h["state"], "label": h["label"], "stale": judged(h, study, project)[0],
             "elsewhere": h["elsewhere"]} for h in mine if "skip" not in h]
    return {"runs": runs, "skipped": [{"day": h["day"], "reason": h["skip"]}
                                      for h in mine if "skip" in h]}
