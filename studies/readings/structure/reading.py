"""The words a measurement earns: what a condition does for the edge, and where the inversion puts it."""

# Every label with its state and the sentence that goes with it. The label is never shown alone.
MEANS = {
    "aporta": ("pass", "Con la condición, la expectativa por operación es mejor que la de "
               "quedarse con el mismo número de operaciones al azar de la estrategia sin ella."),
    "no se distingue": ("watch", "Con la condición la estrategia opera menos, pero lo que "
                        "queda no es mejor que un recorte al azar del mismo tamaño: compra "
                        "una muestra más pequeña y nada más."),
    "resta": ("watch", "Sin la condición la expectativa por operación es mayor. No es una "
              "estrategia mejor que adoptar (encargo 12 §5): es una condición que no "
              "aportaba. Quitarla es decisión del dueño, va al ledger y se revalida aparte."),
    "redundante": ("info", "Quitarla no cambia ni una operación: en esta historia la cumplen "
                   "siempre las demás. El fichero reteseado conserva la edición, así que no "
                   "es que SQX la ignorase."),
    "no aplicada": ("fail", "El fichero que SQX devolvió ya no es el que se fabricó: la "
                    "ablación no llegó a correrse y su resultado no se lee."),
    "no es un filtro": ("info", "Sin ella la estrategia opera igual o menos, así que no "
                        "recortaba entradas (una rama de un OR, o una ruta dependiente de "
                        "estar posicionado). El recorte al azar no aplica."),
    "en la dirección": ("pass", "Invertida, las mismas entradas pierden a precio medio lo "
                        "que la madre gana: el filo está en hacia dónde entra."),
    "sin filo a precio medio": ("watch", "La madre no gana a precio medio: lo que muestre "
                                "neto lo ponen los costes o el swap, no la dirección de la "
                                "entrada. Invertida gana lo que ella pierde."),
    "no invertida": ("fail", "La inversión no tomó las mismas operaciones al revés: la "
                     "edición no se aplicó y el resto de esta pestaña no se lee."),
}


def condition(found: dict, retained: bool, alpha: float) -> str:
    """What one ablation says about the condition it removed.

    Args:
        found: What `measure.ablation` returned for one leg.
        retained: Whether the retested file still carries the edit (`sqx.structural.keep`).
        alpha: Level of the random-subset test on expectancy.

    Returns:
        A key of MEANS.
    """
    if not retained:
        return "no aplicada"
    if found["identical"]:
        return "redundante"
    p = found["null"]["expectancy"]["p"]
    if p is None:
        return "no es un filtro"
    if found["delta"]["expectancy"] < 0:
        return "resta"
    return "aporta" if p < alpha else "no se distingue"


def direction(found: dict, min_paired: float) -> str:
    """Where the inversion says the edge lives.

    Args:
        found: What `measure.inversion` returned for one leg.
        min_paired: Share of the mother's trades that must come back paired, opposite side.

    Returns:
        A key of MEANS.
    """
    if found["paired"] < min_paired:
        return "no invertida"
    return "en la dirección" if found["mid"] > 0 else "sin filo a precio medio"
