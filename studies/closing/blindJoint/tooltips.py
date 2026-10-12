"""One sentence per config.yaml knob, for the window's configuration drawer."""

TIPS = {
    "benchmark.rung": "Qué deja al azar el operador con el que se compara cada madre: timing "
                      "mueve sólo el momento de entrar (cada operación conserva su duración y "
                      "sus lotes); timing_holds además reparte al azar las duraciones.",
    "benchmark.draws": "Cuántos operadores al azar se promedian para sacar lo que paga el "
                       "mercado por la huella de la madre; con 2.000 el error de simulación es "
                       "un 2 % del error propio de la madre.",
    "benchmark.seed": "Semilla fija de los operadores al azar: un rerun sortea los mismos.",
    "stepm.fwer": "Probabilidad de nombrar al menos una madre que en realidad no gana más que "
                  "sus mismas operaciones entradas al azar; misma fila del ledger que el paso 8.",
    "joint.pieces": "Cómo se combinan WFC, CSCV, superficies y WFM: peor (provisional: gana el "
                    "peor estado; un No pasa descarta, un Limbo deja a revisar), unanimidad, "
                    "sin_fallo o ninguna. Vacío = decisión pendiente del dueño: se enseñan todas.",
    "joint.population": "Sobre quién cuenta su búsqueda el StepM: supervivientes de las piezas "
                        "o entrantes al paso 20. Vacío = decisión pendiente del dueño.",
    "bootstrap.reps": "Remuestreos del bootstrap estacionario; más, p más finas y más lento.",
    "bootstrap.seed": "Semilla fija: las mismas madres dan siempre el mismo resultado."}
