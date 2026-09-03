"""Turn a parsed project.cfx into the sections of its Markdown pipeline map."""

from xml.etree.ElementTree import Element

from project_parts import (conditions_table, crosschecks_summary, databanks_of,
                           rankings_summary, special_summary)


def databank_table(cfg: Element) -> list[str]:
    """The project's registered databanks and their sync setting.

    Args:
        cfg: The project's config.xml root.

    Returns:
        Markdown lines. A databank that auto-syncs is flagged, because a sync deletes
        on-disk .sqx not held in memory.
    """
    out = ["## Databanks", "", "| databank | view | sync | position |", "|---|---|---|---|"]
    for d in cfg.findall("Databanks/Databank"):
        sync = d.get("syncType")
        warn = " ⚠️" if sync and "never" not in sync else ""
        out.append(f"| `{d.get('name')}` | {d.get('view')} | {sync}{warn} | {d.get('position')} |")
    return out + ["", "⚠️ = auto-syncs on a timer. A sync writes memory → disk and **deletes "
                  "on-disk `.sqx` files not present in memory**. Combined with a "
                  "`ClearDatabanks` task this is what empties a databank. See "
                  "`knowhow/02-databanks.md`.", ""]


def databank_flow(cfg: Element, task_xml: dict) -> dict:
    """Which task numbers read, write and clear each databank.

    Args:
        cfg: The project's config.xml root.
        task_xml: Task number to that task's parsed XML.

    Returns:
        Databank name to {"reads", "writes", "cleared"}, each a list of task numbers.
    """
    flow = {}
    for i, t in enumerate(cfg.findall("Tasks/Task"), 1):
        root = task_xml[i]
        din, dout = databanks_of(root)
        if din:
            flow.setdefault(din, {"reads": [], "writes": [], "cleared": []})["reads"].append(str(i))
        if dout:
            flow.setdefault(dout, {"reads": [], "writes": [], "cleared": []})["writes"].append(str(i))
        if t.get("type") == "ClearDatabanks":
            for d in root.findall("ClearDatabanks/Databank"):
                flow.setdefault(d.get("name"),
                                {"reads": [], "writes": [], "cleared": []})["cleared"].append(str(i))
    return flow


def tldr(cfg: Element, task_xml: dict, flow: dict) -> list[str]:
    """The computed summary a reader should see first.

    Args:
        cfg: The project's config.xml root.
        task_xml: Task number to that task's parsed XML.
        flow: Output of databank_flow.

    Returns:
        Markdown lines: task count, every loop and whether it is conditional, the
        databanks at risk of strategy loss, and the terminal output databanks.
    """
    tasks = cfg.findall("Tasks/Task")
    names = [t.get("name") for t in tasks]
    sync_of = {d.get("name"): d.get("syncType") or "" for d in cfg.findall("Databanks/Databank")}

    out = ["## TL;DR", "",
           f"- **{len(tasks)} tasks**, "
           f"{sum(1 for t in tasks if t.get('active') != 'true')} inactive."]
    for i, t in enumerate(tasks, 1):
        if t.get("type") != "GoToTask":
            continue
        g = task_xml[i].find("GoToTask")
        target = g.get("task")
        j = names.index(target) + 1 if target in names else "?"
        conditional = len(g.findall("Conditions/Condition")) > 0
        out.append(f"- Task {i} loops back to task {j} (`{target}`) — "
                   + ("conditional." if conditional
                      else "**unconditional**. This chain never terminates on its own."))

    at_risk = [db for db, f in flow.items()
               if f["cleared"] and "never" not in sync_of.get(db, "never")]
    if at_risk:
        out.append(f"- **{len(at_risk)} databanks are cleared by a task while auto-sync is on**: "
                   + ", ".join(f"`{d}`" for d in sorted(at_risk))
                   + ". Each clear empties the databank in memory; the next sync then deletes "
                     "its `.sqx` files. This is the strategy-loss mechanism.")
    terminal = [db for db, f in flow.items()
                if f["writes"] and not f["reads"] and not f["cleared"]]
    if terminal:
        out.append("- **Terminal output databanks** (written, never read, never cleared): "
                   + ", ".join(f"`{d}`" for d in sorted(terminal)) + ".")
    return out + [""]


def flow_table(flow: dict, cfg: Element) -> list[str]:
    """The databank flow as a table, riskiest first.

    Args:
        flow: Output of databank_flow.
        cfg: The project's config.xml root.

    Returns:
        Markdown lines.
    """
    sync_of = {d.get("name"): d.get("syncType") or "" for d in cfg.findall("Databanks/Databank")}
    out = ["## Databank flow", "",
           "Which task numbers read, write and clear each databank. A databank that is "
           "**cleared while it auto-syncs** loses its `.sqx` files on the next sync.", "",
           "| databank | written by | read by | cleared by | at risk |", "|---|---|---|---|---|"]
    for db in sorted(flow, key=lambda d: (not flow[d]["cleared"], d)):
        f = flow[db]
        auto = "never" not in sync_of.get(db, "never")
        risk = "🔴 **yes**" if f["cleared"] and auto else ("cleared, sync off" if f["cleared"] else "—")
        out.append(f"| `{db}` | {', '.join(f['writes']) or '—'} | {', '.join(f['reads']) or '—'} "
                   f"| {', '.join(f['cleared']) or '—'} | {risk} |")
    return out + [""]


def task_order(cfg: Element, task_xml: dict) -> list[str]:
    """The chain as SQX runs it, with jump targets resolved.

    Args:
        cfg: The project's config.xml root.
        task_xml: Task number to that task's parsed XML.

    Returns:
        Markdown lines wrapping a plain-text listing.
    """
    tasks = cfg.findall("Tasks/Task")
    order = {t.get("name"): i for i, t in enumerate(tasks, 1)}
    out = ["## Task order", "", "```"]
    for i, t in enumerate(tasks, 1):
        title = t.get("title") or t.get("name")
        flag = "" if t.get("active") == "true" else "   [INACTIVE]"
        out.append(f"{i:>2}. {title:<28} ({t.get('type')}){flag}")
        if t.get("type") == "GoToTask":
            g = task_xml[i].find("GoToTask")
            target = g.get("task")
            kind = "if condition" if g.findall("Conditions/Condition") else "ALWAYS"
            out.append(f"     └─> jumps back to #{order.get(target, '?')} '{target}'  [{kind}]")
    return out + ["```", ""]


def task_detail(number: int, task: Element, root: Element) -> list[str]:
    """Everything one task declares: databanks, extras, rankings and cross-checks.

    Args:
        number: The task's 1-based position in the chain.
        task: Its entry in config.xml.
        root: Its own parsed XML.

    Returns:
        Markdown lines for one task's section.
    """
    ttype = task.get("type")
    out = [f"### {number}. {task.get('title') or task.get('name')}", "",
           f"- **type** `{ttype}` · **internal name** `{task.get('name')}` · "
           f"**file** `{task.get('taskXMLFile')}`",
           f"- **active**: {task.get('active')}"]
    template = task.get("templateFile")
    if template:
        mangled = "Ã" in template or "Æ" in template
        out.append(f"- **templateFile**: `{template}`" + ("  ⚠️ mojibake" if mangled else ""))
    out.append("")

    inp, outp = databanks_of(root)
    if inp or outp or ttype in ("Build", "Retest", "AutomaticRetest"):
        fmt = lambda v: f"`{v}`" if v else "_(task default)_"
        out += [f"**Databanks:** {fmt(inp)} → {fmt(outp)}", ""]

    for key, value in special_summary(ttype, root):
        if key == "__conditions__":
            out += ["**Jump conditions:**", ""] + conditions_table(*value) + [""]
        elif isinstance(value, list):
            out += [f"**{key}:** " + ", ".join(f"`{v}`" for v in value), ""]
        else:
            out.append(f"- **{key}**: `{value}`")

    ranking = rankings_summary(root)
    if ranking:
        bits = [f"MaxStrategies **{ranking['MaxStrategies']}**"]
        bits += [f"{k} `{ranking[k]}`" for k in ("DeleteFailedStrategies", "ForceRunCrossChecks")
                 if ranking[k]]
        if ranking["StopCondition"].get("type"):
            bits.append(f"StopCondition `{ranking['StopCondition']['type']}`")
        out += ["", "**Rankings:** " + " · ".join(bits), ""]
        rows, attrs = ranking["conditions"]
        if rows:
            out += ["**Task-level acceptance conditions:**", ""] + conditions_table(rows, attrs) + [""]

    attrs, enabled = crosschecks_summary(root)
    if attrs is not None and not enabled:
        out += ["**Cross-checks:** none enabled", ""]
    elif attrs is not None:
        out += [f"**Cross-checks enabled** (`{attrs}`):", ""]
        for e in enabled:
            out += [f"#### ↳ {e['label']} (`{e['tag']}`)", ""]
            if e["settings"]:
                out += ["Settings:", ""] + [f"- `{t}` = `{v}`" for t, v in e["settings"]] + [""]
            out += ["Acceptance conditions:", ""] + conditions_table(*e["conditions"]) + [""]
    return out + ["---", ""]
