"""Read a project.cfx without SQX. It is a ZIP holding config.xml plus one XML per task."""

import zipfile
from pathlib import Path
from xml.etree import ElementTree

from core.paths import project_dir

SAMPLE_TYPE = {"10": "IS", "20": "OOS", "127": "Full"}


def resolve(project: str) -> Path:
    """Turn a project name or a path into a .cfx path.

    Args:
        project: A project name under the master's user/projects, or a path to a .cfx.

    Returns:
        Path of the project.cfx. Reading it is safe at any time; it touches no SQX state.
    """
    p = Path(project)
    return p if p.suffix == ".cfx" else project_dir(project) / "project.cfx"


def config(project: str) -> ElementTree.Element:
    """The project's config.xml.

    Args:
        project: Project name or .cfx path.

    Returns:
        Root element, holding the task list, databank registrations and settings.
    """
    with zipfile.ZipFile(resolve(project)) as z:
        return ElementTree.fromstring(z.read("config.xml"))


def tasks(project: str) -> list[dict]:
    """Every task in chain order.

    Args:
        project: Project name or .cfx path.

    Returns:
        One dict per task with its 1-based number, type, SQX name, display title, whether
        it is active, and its XML member name. `title` is a label only — the real output
        databank lives inside the task XML.
    """
    root = config(project)
    return [{"n": i, "type": t.get("type"), "name": t.get("name"), "title": t.get("title"),
             "active": t.get("active") != "false", "file": t.get("taskXMLFile")}
            for i, t in enumerate(root.iter("Task"), 1)]


def task_xml(project: str, member: str) -> ElementTree.Element:
    """One task's own XML.

    Args:
        project: Project name or .cfx path.
        member: The task's file name inside the ZIP, e.g. "Build-Task3.xml".

    Returns:
        Root element of that task definition.
    """
    with zipfile.ZipFile(resolve(project)) as z:
        return ElementTree.fromstring(z.read(member))


def output_databank(task: ElementTree.Element) -> str:
    """Where a task actually writes its strategies.

    Args:
        task: A task's root element.

    Returns:
        The databank name, or "default" when the value is SQX's literal "null", which
        means the task type's own default databank.
    """
    node = task.find(".//Databank[@name='Output']")
    value = node.get("value") if node is not None else "null"
    return "default" if value in (None, "null") else value


def side(node: ElementTree.Element) -> dict:
    """One side of an acceptance condition.

    Args:
        node: A Left-Side or Right-Side element.

    Returns:
        Either {"value": ...} for a fixed number, or the column form with its metric,
        result type, sample and subresult. Both sides can be columns: SPP tasks compare a
        permuted result against the strategy's own main result.
    """
    col = node.find("Column-Value")
    if col is None:
        return {"value": node.find("Numeric-Value").get("value")}
    return {"column": col.get("column"), "result": col.get("resultType"),
            "subresult": col.get("subresult"),
            "sample": SAMPLE_TYPE.get(col.get("sampleType"), col.get("sampleType"))}


def conditions(task: ElementTree.Element) -> list[dict]:
    """Acceptance conditions of a task, both schemas, enabled or not.

    Args:
        task: A task's root element.

    Returns:
        One dict per condition with `used`, and either the acceptance form
        (left, op, right) or the GoToTask form (type, fields). A threshold inside a
        condition with used=False gates nothing — see knowhow/05-conditions.md.
    """
    out = []
    for c in task.iter("Condition"):
        used = c.get("use") != "false"
        left = c.find("Left-Side")
        if left is None:
            out.append({"used": used, "type": c.get("type"),
                        "fields": [f.text for f in c.findall("Field")]})
        else:
            out.append({"used": used, "left": side(left),
                        "op": c.find("Comparator").get("value"),
                        "right": side(c.find("Right-Side"))})
    return out
