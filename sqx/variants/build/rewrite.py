"""Write one .sqx into another: new values, new name, no inherited fingerprint. Decides nothing."""

import re
import zipfile
from pathlib import Path

PORTFOLIO = "strategy_Portfolio.xml"
SETTINGS = "settings.xml"
PROFILE = "optimizationProfile.bin"
MINIMAL = ("META-INF/MANIFEST.MF", SETTINGS, PORTFOLIO, "lastSettings.xml", "version.txt")

# Which members a variant carries. Measured whole-file sizes, knowhow/sqx-format/writing-a-variant.md:
# full 123.3 KB · no_profile 98.7 KB · minimal 13.7 KB. No shape drops the parent's <SQStats>:
# those are in settings.xml, which all three keep.
SHAPES = {"full": lambda name: True,
          "no_profile": lambda name: not name.endswith(PROFILE),
          "minimal": lambda name: name in MINIMAL}

VARIABLE = re.compile(r"<variable\b[^>]*>.*?</variable>", re.S)
FIELD = {key: re.compile(rf"<{key}>(.*?)</{key}>", re.S) for key in ("id", "type", "value")}
RESULT_NAME = re.compile(r'(<ResultsGroup\b[^>]*?ResultName=")[^"]*(")')
STRATEGY_NAME = re.compile(r'(<StrategyName type="String">)[^<]*(</StrategyName>)')
FINGERPRINT = re.compile(r"<Fingerprint\b.*?</Fingerprint>", re.S)
DECLARATION = re.compile(r"^(<\?xml[^>]*\?>)")
STAMP = re.compile(r"<!--variant_id:([^-]*)-->")


def declared(portfolio: str) -> dict[str, str]:
    """Every variable the strategy declares and its type.

    Args:
        portfolio: Text of `strategy_Portfolio.xml`.

    Returns:
        Variable name to `int`, `double` or `boolean`. The type decides how a value is
        written back: `67.0` into an int parameter is not the same file as `67`.
    """
    return {FIELD["id"].search(b).group(1): FIELD["type"].search(b).group(1)
            for b in VARIABLE.findall(portfolio)}


def values(portfolio: str) -> dict[str, str]:
    """Every variable's current value, as stored.

    Args:
        portfolio: Text of `strategy_Portfolio.xml`.

    Returns:
        Variable name to value text. This is the one place a parameter lives: the rules
        reference the variable by name, so rewriting `<value>` rewrites the rule.
        `settings.xml` carries no parameter names at all.
    """
    return {FIELD["id"].search(b).group(1): FIELD["value"].search(b).group(1)
            for b in VARIABLE.findall(portfolio)}


def _format(value: float, kind: str) -> str:
    """One value as the file spells it.

    Args:
        value: The number to write.
        kind: The variable's declared type.

    Returns:
        A decimal string, integral when the variable is an int.
    """
    return str(int(round(value))) if kind == "int" else f"{value:g}"


def set_values(portfolio: str, wanted: dict[str, float]) -> str:
    """Put a tuple into the strategy definition.

    Args:
        portfolio: Text of `strategy_Portfolio.xml`.
        wanted: Parameter name to value.

    Returns:
        The same text with those variables' values replaced and nothing else touched --
        substitution rather than an XML round trip, so a member SQX has to read back comes
        out byte-identical everywhere the tuple did not reach.

        Raises `KeyError` when a name in the tuple is not a variable of this strategy. A
        silent miss is failure mode 3 of this module: the manifest would claim a
        combination the file does not contain, and nothing downstream could tell.
    """
    types, hit = declared(portfolio), set()

    def replace(match: re.Match) -> str:
        """One variable block, with its value swapped when the tuple names it.

        Args:
            match: A `<variable>…</variable>` block.

        Returns:
            The block, rewritten or untouched.
        """
        block = match.group(0)
        name = FIELD["id"].search(block).group(1)
        if name not in wanted:
            return block
        hit.add(name)
        return FIELD["value"].sub(f"<value>{_format(wanted[name], types[name])}</value>",
                                  block, count=1)

    out = VARIABLE.sub(replace, portfolio)
    missing = set(wanted) - hit
    if missing:
        raise KeyError(f"not variables of this strategy: {sorted(missing)}")
    return out


def stamp(portfolio: str, variant_id: str) -> str:
    """Write the identifier inside the strategy.

    Args:
        portfolio: Text of `strategy_Portfolio.xml`.
        variant_id: `P00000` and up.

    Returns:
        The text with a comment carrying the identifier after the XML declaration. SQX may
        hand a strategy back under a different name after a collision, so the external
        name cannot be the identity. This can only change if the file itself is rewritten.
    """
    return DECLARATION.sub(rf"\1<!--variant_id:{variant_id}-->", portfolio, count=1)


def stamped(portfolio: str) -> str:
    """The identifier a file carries, read back.

    Args:
        portfolio: Text of `strategy_Portfolio.xml`.

    Returns:
        The variant id, or an empty string when the file was not written by this factory.
    """
    found = STAMP.search(portfolio)
    return found.group(1) if found else ""


def rename(settings: str, name: str) -> str:
    """Give the strategy a new name, in both places it is stored.

    Args:
        settings: Text of `settings.xml`.
        name: The new name.

    Returns:
        The text with `ResultsGroup/@ResultName` and `<StrategyName>` replaced. Both, or
        the whole batch arrives in the databank under one name and the export cannot be
        joined to anything.
    """
    out, first = RESULT_NAME.subn(rf"\g<1>{name}\g<2>", settings, count=1)
    out, second = STRATEGY_NAME.subn(rf"\g<1>{name}\g<2>", out, count=1)
    if first + second != 2:
        raise KeyError("settings.xml does not carry both name fields")
    return out


def drop_fingerprint(settings: str) -> str:
    """Remove the result fingerprint the parent stamped on itself.

    Args:
        settings: Text of `settings.xml`.

    Returns:
        The text without its `<Fingerprint>` element. Every variant is born from one
        parent and would inherit one identical fingerprint; if the databank deduplicates
        on it, five thousand variants collapse into one and nobody is told.
    """
    return FINGERPRINT.sub("", settings, count=1)


def members(path: Path) -> dict[str, bytes]:
    """Read a .sqx into memory.

    Args:
        path: The parent strategy.

    Returns:
        ZIP entry name to bytes, in the order the archive stores them.
    """
    with zipfile.ZipFile(path) as archive:
        return {name: archive.read(name) for name in archive.namelist()}


def variant(parent: dict[str, bytes], variant_id: str, name: str,
            wanted: dict[str, float]) -> dict[str, bytes]:
    """One variant's members, from the parent's.

    Args:
        parent: Output of `members`.
        variant_id: `P00000` and up.
        name: The strategy name to write.
        wanted: The tuple.

    Returns:
        A new mapping. Four changes and no others: the values, the identifier stamp, the
        two name fields, and the fingerprint removed.
    """
    portfolio = stamp(set_values(parent[PORTFOLIO].decode("utf-8"), wanted), variant_id)
    settings = drop_fingerprint(rename(parent[SETTINGS].decode("utf-8"), name))
    return {**parent, PORTFOLIO: portfolio.encode("utf-8"),
            SETTINGS: settings.encode("utf-8")}


def save(path: Path, parts: dict[str, bytes], shape: str) -> int:
    """Write a .sqx.

    Args:
        path: Where it goes.
        parts: Output of `variant`.
        shape: A key of `SHAPES`.

    Returns:
        Bytes written.
    """
    keep = SHAPES[shape]
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, blob in parts.items():
            if keep(name):
                archive.writestr(name, blob)
    return path.stat().st_size
