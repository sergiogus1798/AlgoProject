"""A starting-point note per asset on how it tends to trade — trend, rango, carry, volatilidad.

Owner, 2026-10-01: a light pass, not an exhaustive study — just something to seed the
«Características» panel with instead of leaving it empty. `core.assets` computes nothing from
this; it is prose, not a cost or a filter. A real reading of which regime an asset's edge lives
in is `studies/readings/monkey/README.md`, not this.
"""

from ui.desktop.names import family
from ui.desktop.theme import C

# Características judges by what the market profile measured, not by the prior alone (owner,
# 2026-10-04): verdict → (what the line opens with, its ink).
VERDICT = {"bien": ("Va bien", C["promising"]), "sin_confirmar": ("Sin confirmar", C["weak"]),
           "sin_medir": ("Sin medir", C["muted"]), "mal": ("Va mal", C["dead"])}
TRAITS_HELP = (
    "Cada línea es una familia de estrategias juzgada para este activo.\n\n"
    "Verde «Va bien»: el perfil de mercado la midió a favor en al menos una temporalidad — la "
    "regla desnuda de la familia saca nota frente a su entrada aleatoria, o su barrido con una "
    "salida razonable cae en meseta.\n"
    "Ámbar «Sin confirmar»: tu prior la da por Alta o Media, pero nada medido la respalda "
    "todavía.\n"
    "Gris «Sin medir»: tu prior la da por Baja y nada medido lo confirma ni lo desmiente.\n"
    "Rojo «Va mal»: medida en contra (ni nota ni múltiplo sobre el coste) sin ninguna "
    "temporalidad a favor.\n\n"
    "Las temporalidades medidas son M15, M30, H1 y H4, sobre el tramo build. «Prior» es tu "
    "matriz cualitativa de familias por activo (H1-H4), que antes era lo único que se leía aquí.")

GENERIC = ("Sin nota todavía — añade aquí lo que se sepa de cómo se mueve este activo.")

TRAITS = {
    "EURUSD": "El par más líquido y sin cruce de materia prima. Desarrolla tendencias claras "
              "cuando la política monetaria del BCE y la Fed diverge, y pasa buena parte del "
              "resto del tiempo en rango.",
    "GBPUSD": "Parecido a EURUSD pero más volátil y más sensible a sorpresas políticas del "
              "Reino Unido y de tipos del BoE. Tendencial en divergencia de política monetaria, "
              "rango en calma.",
    "AUDUSD": "Ligado al ciclo de materias primas y a China. Sigue el apetito de riesgo global "
              "como las bolsas: tramos de tendencia marcados por el diferencial de tipos, con "
              "fases de rango cuando ese diferencial está quieto.",
    "USDCAD": "El CAD va con el petróleo. Tras una tendencia marcada puede entrar en rangos "
              "amplios y largos (todo 2025 lateral en una banda de ~1.000 pips). Sensible al "
              "diferencial Fed/BoC.",
    "USDCHF": "El franco es moneda refugio, así que el par tiende a moverse como el espejo "
              "inverso de EURUSD. Mean-reversion marcada, con rupturas de tendencia bruscas en "
              "episodios de intervención del BNS.",
    "USDJPY": "Muy ligado al diferencial de tipos Fed/BoJ y al carry trade. Tendencias largas y "
              "marcadas cuando el diferencial se amplía, con reversiones muy bruscas si el carry "
              "se deshace (p. ej. agosto 2024).",
    "EURJPY": "Cruce de carry trade y de riesgo global, sin el ancla de materia prima del AUD o "
              "el CAD. Tendencial en fases de política monetaria divergente, cae con fuerza en "
              "aversión al riesgo.",
    "GBPJPY": "El cruce de mayor volatilidad del grupo («the beast»). Muy sensible al apetito de "
              "riesgo global: tendencial, con rupturas violentas cuando se deshace el carry.",
    "AUDJPY": "Cruce de carry trade clásico: AUD de alto rendimiento contra JPY de financiación "
              "barata. Aprecia gradualmente en calma, cae con fuerza en aversión al riesgo — más "
              "tendencial que de rango.",
    "CADJPY": "Mismo patrón que AUDJPY: carry trade con el CAD correlacionado al petróleo y el "
              "JPY como financiación. Tendencial con el apetito de riesgo, rupturas bruscas "
              "cuando el carry se deshace.",
    "XAUUSD": "Sin ancla de valor fundamental — lo mueve el sentimiento, la demanda refugio, los "
              "tipos reales y el dólar. Fuerte tendencia a revertir a la media (vuelve a su EMA20 "
              "en H1 buena parte de las veces tras un RSI extremo), salvo en el 20-25 % de días "
              "que son de tendencia fuerte y revientan esa reversión.",
    "XAGUSD": "Más volátil que el oro — su ATR en % suele triplicar al del oro —, mercado más "
              "pequeño y más ligado al ciclo industrial. Tan propenso a revertir a la media como "
              "el oro, pero con movimientos más bruscos.",
    "USA500": "Drift alcista estructural por flujos institucionales y estabilidad macro. "
              "Tendencial en diario/semanal; por debajo de la hora domina la reversión a la "
              "media.",
    "USATEC": "El mismo patrón que el S&P 500 — tendencia en diario, reversión intradía — pero "
              "más volátil: pesan más la tecnología y los tipos a largo plazo.",
    "DJ30": "El índice más \"viejo\" y menos tecnológico de los tres de EE.UU. Drift alcista "
            "estructural a largo plazo, tendencial en diario/semanal, fuerte reversión a la "
            "media por debajo de la hora.",
    "DAX40": "Índice de un solo país, sensible al ciclo industrial europeo y a los tipos del "
             "BCE. Tendencial en marcos diarios y semanales, con alta reversión a la media "
             "intradía.",
    "NIKKEI225": "Muy correlacionado con el yen (un yen débil impulsa a las exportadoras "
                "japonesas) y con el apetito de riesgo global. Tendencial en marcos altos, "
                "reversión a la media intradía.",
    "USOIL": "Fuerte componente de reversión a la media a medio plazo — vuelve hacia el coste "
             "marginal de producción —, pero con tendencias muy marcadas en shocks de oferta o "
             "geopolítica. Uno de los activos más volátiles de la cartera.",
    "UKOIL": "Mismo patrón que el WTI — reversión a la media entre shocks, tendencias fuertes "
             "durante ellos —, con su propia prima geopolítica (Oriente Medio, rutas marítimas).",
}


def trait(symbol: str) -> str:
    """The note for one asset, or the placeholder when nobody has written one yet.

    Args:
        symbol: Asset name, as `assets/symbols/<S>.yaml` names it.

    Returns:
        The prose, never empty, so the panel always says something.
    """
    return TRAITS.get(symbol, GENERIC)


def trait_line(p: dict) -> str:
    """One family of the Características panel as a row of a rich-text table.

    Args:
        p: One row of the daemon's `prior`: family, level, long_only, favour, against, verdict.

    Returns:
        The cells «● Va bien», «Momentum», «a favor en H1, H4 · en contra en M15 · prior Alta».
    """
    said, ink = VERDICT[p["verdict"]]
    parts = [f"a favor en {', '.join(p['favour'])}" if p["favour"] else "",
             f"en contra en {', '.join(p['against'])}" if p["against"] else "",
             "" if p["favour"] or p["against"] else "nada medido a favor ni en contra",
             f"prior {p['level']}" if p["level"] else "sin prior",
             "solo largos" if p["long_only"] else ""]
    pad = "padding: 2px 18px 2px 0;"
    return (f"<tr><td style='color: {ink}; {pad}'>● {said}</td>"
            f"<td style='{pad}'><b>{family(p['family'])}</b></td>"
            f"<td>{' · '.join(x for x in parts if x)}</td></tr>")


def traits_table(prior: list[dict]) -> str:
    """The whole Características panel: one row per family, the verdicts in one column.

    Args:
        prior: The daemon's `prior` rows, best first; may be empty.

    Returns:
        Rich text. With no family measured for, the first line says so: an asset whose rows
        are all amber, grey and red would otherwise leave the owner looking for the green.
    """
    if not prior:
        return "Sin prior ni perfil medido para este activo"
    none = "" if any(p["verdict"] == "bien" for p in prior) else (
        "Ninguna familia medida a favor todavía.<br>")
    return none + "<table>" + "".join(trait_line(p) for p in prior) + "</table>"


LEGEND = " &nbsp; ".join(f"<span style='color: {ink};'>● {said}</span>" for said, ink in
                         VERDICT.values()) + " &nbsp; — lo que midió el perfil de mercado"
