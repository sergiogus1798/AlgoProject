"""Which studies have a result for one strategy anywhere in the project, and what each says — the
strategy page's tabs and dots in one cheap answer."""

from ui.daemon.results import catalogue, hits, runs


def presence(project: str, databank: str, strategy: str, identity: str) -> dict[str, dict]:
    """Per study, the result `/api/result` would show for this strategy, without reading it.

    Only file stats and the cached slim reads of `hits` (a population result is parsed once
    per version of its file, to know which names it speaks of): a page hides the studies
    absent here and labels none of the others «sin datos» (owner, 2026-09-30).

    Args:
        project: SQX project name.
        databank: The databank the page opened from.
        strategy: Strategy name.
        identity: Its identity, "" to trust the name.

    Returns:
        Study key → {state, label, stale, day, elsewhere, other_identity}, only for the
        studies with a result.
    """
    out = {}
    for key in catalogue.ordered():
        hit, _ = runs.pick(hits.sources(project, databank, key, strategy), identity)
        if hit is not None:
            out[key] = {"state": hit["state"], "label": hit["label"],
                        "stale": runs.judged(hit, key, project)[0], "day": hit["day"],
                        "elsewhere": hit["elsewhere"] or (hit["note"] or None),
                        "other_identity": runs.other(hit, identity)}
    return out
