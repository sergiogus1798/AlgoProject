"""Typed reads of an XML tree whose layout is known: the element, attribute or text is there or the read fails."""

import xml.etree.ElementTree as ET


def el(e: ET.Element | None) -> ET.Element:
    """The element, which the file's layout guarantees to be there."""
    assert e is not None
    return e


def attr(e: ET.Element | None, name: str) -> str:
    """The attribute `name` of an element the layout guarantees to be there."""
    v = el(e).get(name)
    assert v is not None
    return v


def text(e: ET.Element | None) -> str:
    """The text of an element that the layout guarantees to hold some."""
    t = el(e).text
    assert t is not None
    return t
