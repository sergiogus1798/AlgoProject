"""Which family tab, and which study, a strategy page opens on by the databank it came from."""

OPTIMISATION = "WFM + WFC + CSCV + Market Surfaces"

# Which family tab opens first, by the databank panel the page was opened from — a fallback
# for a sub-panel `ORIGIN_STUDY` does not name (or before the panel is known, `Ficha` tab).
ORIGIN_FAMILY = {"Puerta IS/OOS": "Cribado", "Cross Market": "Transferencia",
                 "Cross Timeframe": "Transferencia", "MC Retest": "Rotura", "SPP": "Optimización",
                 OPTIMISATION: "Optimización", "Cierre": "Cierre"}

# The study a databank panel's tab (or one of its sub-panels) opens by default (owner,
# 2026-09-30 §4.3/§9.4): a single study key for a tab that reads only one, or {sub: key} for
# a tab whose sub-panels each read a different one — "" is the fallback sub.
ORIGIN_STUDY: dict[str, str | dict[str, str]] = {
    "Puerta IS/OOS": "gate", "Cross Market": "crossmarket", "Cross Timeframe": "crossTF",
    "MC Retest": "mcRetest", "SPP": "spp",
    OPTIMISATION: {"Nube de parámetros": "cloud", "CSCV": "cscv",
                  "Market Surfaces": "marketSurfaces", "Walk Forward Matrix": "wfm",
                  "WFC": "wfc", "": "wfc"},
    "Cierre": {"Análisis conjunto (paso 20)": "blindJoint", "Exposición": "exposure",
              "Mapa condicional": "conditionalMap", "Estructura": "structure",
              "Stop ATR": "atrCalculator", "Edge por coste": "edgeCost"}}


def default_study(databank: str, sub: str) -> str | None:
    """The study a strategy page opens on, by the databank panel it came from.

    Args:
        databank: The panel's top tab, as `ORIGIN_STUDY` names it.
        sub: The panel's open sub-panel; ignored for a tab with a single default study.

    Returns:
        A catalogue key, or None for a databank with no rule (`open_family` alone decides).
    """
    entry = ORIGIN_STUDY.get(databank)
    if entry is None or isinstance(entry, str):
        return entry
    return entry.get(sub, entry.get(""))
