"""One sentence per config.yaml knob of the variant factory, for the window's Configuración SQX › WFC."""

TIPS = {
    "minimum.variants": "Mínimo de variantes distintas por madre (dueño, 26-09). Si su ±30 % no da "
                        "para tantas —parámetros enteros de valor pequeño—, los recorridos enteros "
                        "se ensanchan hasta llegar, y lo que aún falte se avisa. "
                        "`make --min-variants` lo pisa para una ejecución.",
    "minimum.widen_step": "Cuánto se ensancha por lado cada vuelta buscando el mínimo, como "
                          "fracción del valor original: 0.05 es ±5 %.",
    "minimum.max_span": "Hasta dónde puede llegar ese ensanche: 0.60 es ±60 % del valor original.",
    "design.seed": "Semilla de todos los sorteos del diseño: la misma madre da el mismo lote "
                   "cada vez.",
    "design.neighbourhood.radius": "Cuántos pasos de nivel alrededor de la combinación central "
                                   "cubre la rejilla densa de la vecindad.",
    "design.factorial.min_levels": "La rejilla gruesa nunca baja de estos niveles: como mínimo "
                                   "los dos extremos del recorrido.",
    "design.frozen.span": "El estrato de cobertura varía también los parámetros congelados, ± "
                          "esta fracción de su valor, como hace SQX (±30 %). Un shift no se "
                          "varía nunca.",
    "design.frozen.steps": "Niveles que recorre un parámetro congelado dentro de ese ±.",
    "canaries.n": "Controles cuyo resultado se sabe antes del retest, sacados de los extremos de "
                  "la tabla del SPP: una cadena mal cableada devuelve un número mediocre, no el "
                  "máximo de la rejilla.",
    "canaries.inert_pairs": "Un par de variantes por parámetro congelado que sólo se diferencian "
                            "en él: si dan distinto, el parámetro no estaba muerto."}
