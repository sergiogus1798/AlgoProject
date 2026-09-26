"""One sentence per config.yaml knob, for the window's configuration drawer."""

TIPS = {
    "benchmark.sizing": "Cómo se dimensiona el buy & hold: equal_risk le da la misma volatilidad "
                        "diaria que a cada madre.",
    "stepm.fwer": "Probabilidad de nombrar al menos una madre que en realidad no bate al "
                  "buy & hold; es la misma fila del ledger que la del paso 8.",
    "joint.pieces": "Cómo se combinan WFC, CSCV, superficies y WFM: unanimidad, sin_fallo o "
                    "ninguna. Vacío = decisión pendiente del dueño: se enseñan todas.",
    "joint.population": "Sobre quién cuenta su búsqueda el StepM: supervivientes de las piezas "
                        "o entrantes al paso 20. Vacío = decisión pendiente del dueño.",
    "bootstrap.reps": "Remuestreos del bootstrap estacionario; más, p más finas y más lento.",
    "bootstrap.seed": "Semilla fija: las mismas madres dan siempre el mismo resultado."}
