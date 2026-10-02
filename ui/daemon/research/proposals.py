"""The saved proposals as the window reads and changes them: the veto and the owner's answers."""

from studies.research.board import proposal, store


def view(p: dict) -> dict:
    """A proposal with, per idea, whether it may be launched and why not."""
    ideas = []
    for i in p["ideas"]:
        ok, why = proposal.launchable(i)
        ideas.append({**i, "launchable": ok, "why_not": why})
    return {**p, "ideas": ideas}


def latest(proposal_id: str = "") -> dict:
    """One proposal by id, or the newest; `{"none": True}` when there is none yet."""
    ids = proposal.listing()
    if not ids:
        return {"none": True, "ids": []}
    return {**view(proposal.load(proposal_id or ids[0])), "ids": ids}


def _idea(p: dict, name: str) -> dict:
    """The idea of that name inside a proposal."""
    return next(i for i in p["ideas"] if i["name"] == name)


def veto(proposal_id: str, name: str, vetoed: bool) -> dict:
    """Set or lift the owner's veto on one idea, and save."""
    p = proposal.load(proposal_id)
    _idea(p, name)["vetoed"] = vetoed
    proposal.save(p)
    return view(p)


def answer(proposal_id: str, name: str, question: int, text: str) -> dict:
    """Write the owner's answer to one open question of an idea (hard rule 11), and save."""
    p = proposal.load(proposal_id)
    _idea(p, name)["questions"][question]["answer"] = text
    proposal.save(p)
    return view(p)


def state() -> dict:
    """The director's last recorded step (`proposal.step`), or nothing."""
    f = store.proposals_dir() / "estado.json"
    return store.read(f) if f.exists() else {}
