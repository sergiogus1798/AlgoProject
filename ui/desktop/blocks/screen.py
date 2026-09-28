"""The result as it stands on screen: each tab reduced to the blocks drawn, its choices written in its note."""

from ui.desktop.blocks import markets
from ui.desktop.blocks.pick import picked, selectors, shown


def screen(result: dict, memory: dict[str, dict], alone: bool = True) -> dict:
    """One result cut down to what the window draws, for `core.study.render` to write as a page.

    Args:
        result: A contract result as shown (stored, merged or a partial re-run).
        memory: {tab name: chosen selector values}, as `ResultView` remembers them; a tab
            never opened draws its defaults, as it would on screen.
        alone: False when the result is one side of a comparison: then per-market grids are
            not laid side by side, exactly as on screen.

    Returns:
        A result whose tabs hold no selectors and whose blocks carry no `select` — so the
        static page draws every block kept — and whose notes end with the combination on screen. The report is then the
        same dict through the same renderer, not a second drawing of it (22 §6.3 point 10).
    """
    pool = [b for t in result["tabs"] for b in t["blocks"]]
    tabs = []
    for tab in result["tabs"]:
        chosen = memory.get(tab["name"]) or {}
        pick = picked(tab, chosen)
        if alone and markets.grouped(tab):
            plain, maps, consensus = markets.split(tab, chosen, pool)
            kept = plain + maps + ([consensus] if consensus else [])
            pick[markets.KEY] = ", ".join(chosen.get(markets.CHOSEN) or markets.first(tab))
        else:
            kept = shown(tab, chosen)
        said = " · ".join(f"{s['label']}: {pick[s['key']]}" for s in selectors(tab))
        note = (tab.get("note") or "") + (f" En pantalla: {said}." if said else "")
        # The static page draws only blocks whose tags agree with its selectors' defaults
        # (render/page.shown); with the selectors gone, a kept block must carry no tag either.
        tabs.append({**tab, "note": note.strip(), "selectors": [],
                     "blocks": [{k: v for k, v in b.items() if k != "select"} for b in kept]})
    return {**{k: v for k, v in result.items() if k != "partials"}, "tabs": tabs}
