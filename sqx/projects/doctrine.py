#!/usr/bin/env python3
"""Apply the owner's build doctrine to every task of a project, identically."""

from core.assetdata import doctrine, sqx_settings
from sqx.projects import buildrules as rules
from sqx.projects import tasksettings as settings


def apply_doctrine(text: str, data: dict, segment: str, timeframe: str) -> tuple[str, dict]:
    """Rewrite one task so it generates and trades the way `_build.yaml` says.

    Args:
        text: A task XML.
        data: One asset as load() returned it.
        segment: Segment name, which fixes the spread the high-precision retest reruns at.
        timeframe: SQX timeframe name — the same one for every task of the project.

    Returns:
        The task and what was applied, as data for the caller to report.

    Only a Build task carries a generator, so the rules about what may be generated —
    order types, exit types, rule complexity, SL/PT — are written only where there is a
    <Blocks> section to write them into. The rest (timeframe, engine, session, sizing,
    hours, cross-checks) is written into every task, and that is the point: those are
    exactly the settings an IS and an OOS have to share to be comparable.

    Order matters in one place only: the exit types are counted before the complexity is
    written, because the cap on how many kinds of exit the generator may combine is the
    number that are actually left enabled.
    """
    d = doctrine()
    # Only a Build task carries a generator, and that is also what decides its precision
    # and whether it runs the high-precision cross-check.
    generates = bool(rules.BLOCKS.search(text))
    key = "build" if generates else "default"
    text, charts = settings.set_timeframe(text, timeframe)
    text = settings.set_precision(text, d["precision"][key])
    text = settings.set_engine(text, d["engine"])
    text, sessions = settings.set_session(text, data["session"])
    text = settings.set_money_management(text, d["money_management"])
    text, options = settings.set_params(text, d["trading_options"])
    text = settings.set_databank_caps(text, d["databank"])
    text = settings.set_genetic(text)
    text = settings.set_crosschecks(text, d["crosschecks"],
                                    sqx_settings(data, segment)["defaultSpread"],
                                    d["crosschecks"][key])
    exit_types = None
    if generates:
        text = rules.set_order_types(text, d["order_types"])
        text, exit_types = rules.set_exit_types(text, d["exits"], timeframe)
        text = rules.set_complexity(text, d["complexity"], exit_types,
                                    d["exits"]["condition_required"])
        text = rules.set_slpt(text)
    lo, hi = rules.bar_range(d["exits"], timeframe)
    return text, {"charts": charts, "generator": generates, "exit_types": exit_types,
                  "precision": d["precision"][key],
                  "exit_bars": [lo, hi], "sessions": sessions, "trading_options": options,
                  "session_defined": settings.session_defined(text, data["session"])}


def blockers(data: dict, timeframe: str) -> list[str]:
    """What stops a project being authored for this asset and timeframe.

    Args:
        data: One asset as load() returned it.
        timeframe: SQX timeframe name.

    Returns:
        One line per undecided or unsupported value. The session is the one that does not
        announce itself: a task naming a session the project does not define still loads.
    """
    out = []
    if not data.get("session"):
        out.append(f"{data['symbol']}: `session:` sin decidir en assets/symbols/. "
                   "Dime cuál es la sesión del activo antes de construir nada.")
    if timeframe not in rules.TF_MINUTES:
        out.append(f"{timeframe}: timeframe desconocido. Conocidos: "
                   + ", ".join(rules.TF_MINUTES))
    return out


def unify_sessions(members: dict[str, bytes], session: str) -> list[str] | None:
    """Make every task of a project carry the definition of the session it trades.

    Args:
        members: The .cfx contents by member name, patched in place.
        session: Session name, from the asset's file.

    Returns:
        The tasks that were missing it, or None when NO task of the project defines it.
        The definition is taken from whichever task already has it, so nothing is
        invented; a session no task carries has to come from SQX first, and inventing
        trading hours is exactly the kind of quiet fabrication this refuses to do.
    """
    texts = {n: b.decode("utf-8") for n, b in members.items()
             if n.endswith(".xml") and n != "config.xml"}
    block = next((b for b in (settings.session_block(t, session) for t in texts.values()) if b),
                 None)
    if not block:
        return None
    fixed = []
    for name, text in texts.items():
        if settings.session_block(text, session):
            continue
        members[name] = settings.add_session(text, block).encode("utf-8")
        fixed.append(name)
    return fixed
