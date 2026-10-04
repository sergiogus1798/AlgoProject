"""How a stored Verificar result reads in the window: capitals, percentages and one line per firm.

The stored `result.json` is mt5/verify's (another session's); this only rewrites the copy sent
to the window, never the file.
"""
import re

NUMBERED = re.compile(r"^(\d+[ab]? · )(.)")
PERCENT = {"1": 2, "5": 1}      # verdict rows shown as a percentage, by number: decimals


def initial(text: object) -> object:
    """A string with its first letter in capitals, anything else untouched."""
    return text[:1].upper() + text[1:] if isinstance(text, str) else text


def percent(value: float, decimals: int) -> str:
    """0.9673 -> «96,73%»: the Spanish comma, no space (owner, 2026-10-03 §10)."""
    return f"{value * 100:.{decimals}f}".replace(".", ",") + "%"


def polish(result: dict | None, firm_names: dict[str, str]) -> dict | None:
    """The result as the window draws it.

    Args:
        result: The stored study contract, or None.
        firm_names: Firm key -> label, for the summary lines.

    Returns:
        The same dict, edited in place: the first column of the parameters table and the
        verdict rows start in capitals; rows 1 and 5 carry a `shown` percentage; the summary
        tab opens with one callout per firm, green when validated and red when not.
    """
    if not result:
        return result
    for tab in result.get("tabs", []):
        for block in tab.get("blocks", []):
            if block.get("kind") == "table" and block.get("columns", [""])[0] == "parámetro":
                for row in block["rows"]:
                    row[0] = initial(row[0])
            if block.get("kind") == "verdict":
                for part in block.get("parts", []):
                    part["label"] = NUMBERED.sub(lambda m: m[1] + m[2].upper(), part["label"])
                    digits = PERCENT.get(part["label"].split(" · ")[0])
                    if digits is not None and part.get("value") is not None:
                        part["shown"] = percent(part["value"], digits)
    lines = [{"kind": "callout", "state": "pass" if state == "pass" else "fail",
              "text": f"{firm_names.get(firm, firm)}: "
                      f"{'validada' if state == 'pass' else 'no validada'}"}
             for firm, state in (result.get("summary", {}).get("firms") or {}).items()
             for state in [state["state"]]]
    for tab in result.get("tabs", []):
        if tab.get("name") == "resumen":
            tab["blocks"] = lines + tab["blocks"]
    return result
