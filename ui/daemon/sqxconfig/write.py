"""One value of the SQX settings written from the window, checked against its spec, comments kept."""

import yaml
from ruamel.yaml.comments import CommentedSeq
from ruamel.yaml.scalarstring import ScalarString

from core import assetwrite
from core.assetyaml import leaves, read
from core.paths import ASSETS
from ui.daemon.sqxconfig.options import spec
from ui.daemon.sqxconfig.sections import POLICY_KEYS

WRITABLE = ("build", "classes", "policy")


def _number(text: object, kind: dict) -> int | float:
    """What was typed in a number box, as the number it means, inside its range.

    Args:
        text: The box's text, or a number already.
        kind: The field's spec, with `min` and `max` (None when open).

    Returns:
        An int or a float. Anything else, or a number out of range, raises ValueError with
        the sentence to show.
    """
    value = yaml.safe_load(str(text).replace(",", ".")) if str(text).strip() else None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"«{text}» no es un número.")
    if kind.get("min") is not None and value < kind["min"]:
        raise ValueError(f"{value} está por debajo del mínimo, {kind['min']}.")
    if kind.get("max") is not None and value > kind["max"]:
        raise ValueError(f"{value} está por encima del máximo, {kind['max']}.")
    return value


def _seq(items: list, current: object) -> CommentedSeq:
    """A list as the file wrote the one it replaces: on one line when that one was.

    Args:
        items: The new items.
        current: The list being replaced.

    Returns:
        A list that keeps the flow style, so changing one item of `[H4, H12]` is a one-line
        diff instead of the list exploding into a block of its own.
    """
    seq = CommentedSeq(items)
    if isinstance(current, CommentedSeq) and current.fa.flow_style():
        seq.fa.set_flow_style()
    return seq


def _among(value: object, allowed: list) -> bool:
    """Whether a value is one of the options, type included — `1` is not `True`."""
    return any(v == value and type(v) is type(value) for v in allowed)


def coerce(kind: dict, current: object, value: object) -> object:
    """The value to write, in the form the file already holds.

    Args:
        kind: The field's spec.
        current: What the file holds now.
        value: What the window sent: an option value, a list, or the typed text.

    Returns:
        The value as it goes into the file. Anything the spec does not allow raises
        ValueError with the reason.
    """
    allowed = [o["value"] for o in kind.get("options", [])]
    if kind["type"] in ("choice", "bool"):
        if not _among(value, allowed):
            raise ValueError(f"«{value}» no es una de las opciones: {allowed}.")
        # "true" quoted stays quoted: unquoted it would turn into a YAML boolean.
        return type(current)(value) if isinstance(current, ScalarString) else value
    if kind["type"] in ("choices", "list") and not isinstance(value, list):
        raise ValueError(f"Aquí va una lista, no «{value}».")
    if kind["type"] == "choices":
        wrong = [v for v in value if not _among(v, allowed)]
        if wrong:
            raise ValueError(f"{wrong} no están entre las opciones: {allowed}.")
        if len(set(value)) != len(value):
            raise ValueError(f"{value} repite un elemento.")
        return _seq(list(value), current)
    if kind["type"] == "number":
        return _number(value, kind)
    if kind["type"] == "list":
        return _seq([yaml.safe_load(str(v)) for v in value if str(v).strip()], current)
    text = str(value)
    return type(current)(text) if isinstance(current, ScalarString) else assetwrite.parse(text, "scalar")


def _pair(doc: object, path: list, value: object) -> None:
    """The one check across two values: the bar exit's minimum hours never above its maximum."""
    if path[:2] == ["exits", "bars"]:
        bars = {**doc["exits"]["bars"], path[-1]: value}
        if bars["min_hours"] > bars["max_hours"]:
            raise ValueError(f"min_hours {bars['min_hours']} quedaría por encima de "
                             f"max_hours {bars['max_hours']}.")


def _current(doc: object, path: list) -> object:
    """The node the file holds at a path already known to exist, style and quotes included."""
    node = doc
    for key in path:
        node = node[key]
    return node


def set_field(name: str, path: list, value: object) -> dict:
    """Write one value of one shared file, through the only writer of assets/.

    Args:
        name: "build", "classes" or "policy".
        path: Keys and list indices leading to the value, as the section listed them.
        value: What the window sent.

    Returns:
        What `assetwrite.set_value` wrote. A path that does not exist or that names a whole
        section rather than one value is refused: writing a scalar over `exits` would erase
        the section.
    """
    if name not in WRITABLE or not path or (name == "policy" and path[0] not in POLICY_KEYS):
        raise ValueError(f"{name}:{path} no se escribe desde esta zona.")
    file = ASSETS / assetwrite.SHARED[name]
    doc = read(file)
    # Only a path the zone listed is written: a branch («exits»), an item inside a list of
    # values or a key the file lacks is refused, because `set_value` would replace or create
    # whatever sits there — a scalar over «exits» erases the whole section.
    found = [leaf for leaf in leaves(file, doc) if leaf["path"] == list(path)]
    if not found:
        raise ValueError(f"{name}:{path} no es un valor de este fichero: o no existe, o es "
                         "una sección entera o un elemento suelto de una lista.")
    node = found[0]["value"]
    kind = spec(name, list(path), node)
    if kind.get("locked"):
        raise ValueError(kind["locked"])
    new = coerce(kind, _current(doc, path), value)
    _pair(doc, path, new)
    return assetwrite.set_value(name, list(path), new)
