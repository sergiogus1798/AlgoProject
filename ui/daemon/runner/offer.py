"""Which studies a strategy page can use in its own databank, and where the others live."""

from ui.daemon.databank import layout
from ui.daemon.loader import find
from ui.daemon.results.catalogue import STUDIES
from ui.daemon.runner import table


def _home(project: str) -> dict[str, tuple[str, str]]:
    """Each study's own databank: the one its Databanks tab reads, and that tab's name.

    Args:
        project: Project name.

    Returns:
        Study key → (databank, tab); a study no tab names, or the build's `*`, is absent.
    """
    out, written = {}, layout.outputs(project)
    for tab, subs in layout.TABS:
        for _, studies, stage, _ in subs:
            for key in studies:
                if key != "*" and key not in out:
                    out[key] = (layout.databank(project, written, stage, studies), tab)
    return out


def _refusal(key: str, project: str, databank: str, strategy: str, asset: str) -> str | None:
    """The runner's sentence when the study cannot start here on this strategy, else None."""
    entry = table.STUDIES.get(key, {})
    scope = "one" if entry.get("one") else "many"
    try:
        got = table.jobs({"study": key, "scope": scope, "project": project,
                          "databank": databank, "strategies": [strategy], "asset": asset,
                          "overrides": [], "only": None})
    except (FileNotFoundError, KeyError, ValueError, OSError) as e:
        return f"no se pudo comprobar: {e}"
    return got if isinstance(got, str) else None


def _go(project: str, databank: str, strategy: str, home: tuple[str, str] | None) -> dict:
    """Where the study's own databank holds this strategy, by name, or why it does not.

    Returns:
        `{"databank", "tab", "strategy", "identity"}` when exactly one strategy of that name
        is there; `{"absent": sentence}` otherwise; `{}` when the study's databank is this one.
    """
    if home is None or home[0].replace(" ", "_") == databank.replace(" ", "_"):
        return {}
    bank, tab = home
    where = find.install_of(project, find.spelled(project, bank))
    if where is None or find.writing(where[1], project):
        return {"absent": f"no se puede mirar {bank}, el databank de este test, ahora: no está "
                          "en ningún install o SQX lo está escribiendo"}
    same = [i for i, name in find.roster(project, bank).items() if name == strategy]
    if len(same) == 1:
        return {"databank": bank, "tab": tab, "strategy": strategy, "identity": same[0]}
    if not same:
        return {"absent": f"«{strategy}» no está en {bank}, el databank de este test: no pasó "
                          "a ese paso, o el paso aún no ha corrido"}
    return {"absent": f"{bank} tiene {len(same)} estrategias llamadas «{strategy}»: ábrela "
                      f"desde la pestaña {tab} de Databanks"}


def offer(project: str, databank: str, strategy: str, asset: str) -> dict[str, dict]:
    """Every study the runner refuses here for this strategy, why, and where to go instead.

    A study with a stored result here is still listed when its runner refuses: the page
    greys only what has neither (owner, 2026-09-30: «apagado + ir al bueno»). Pairing across
    databanks is by name and offered as a jump, never done in silence — the identity changes
    between databanks (knowhow sqx-format/identity-differs-across-databanks).

    Args:
        project, databank, strategy, asset: The strategy page's place.

    Returns:
        Study key → `{"why": sentence, "go": {...}}`, `go` as `_go` returns it.
    """
    homes = _home(project)
    out = {}
    for key in STUDIES:
        why = _refusal(key, project, databank, strategy, asset)
        if why:
            out[key] = {"why": why, "go": _go(project, databank, strategy, homes.get(key))}
    return out

