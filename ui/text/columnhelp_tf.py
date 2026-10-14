"""The columns of the cross-TF «isolated peak» reading (`tf_*`, encargo 47): header and «?» of each, as the study writes them."""

# (study, field) → (header of at most 22 characters, sentence). The study is "crossTF"; the fields
# are `ui.daemon.results.tfrows`'s. Beside the old reading, which still judges: «sin cortar».
TF = {
    "tf_state": (
        "T · Veredicto nuevo",
        "Veredicto de la madre con T0-T4 (pass, limbo o fail), "
        "sin cortar: hoy sólo se anota, el paso 12 sigue juzgando por z_new. Lo que "
        "no se pudo medir es limbo, nunca un cero.",
    ),
    "tf_phase1": (
        "T · Fase 1",
        "Lo mismo con sólo lo que hay en oos1 (T0, T2a y T3): lo que "
        "decidirá el paso 11.5 antes de gastar SQX en el build.",
    ),
    "tf_t3": (
        "T3 · Lejana",
        "Si la lejana comparable (la H4 de una madre M30) cae en T2a, un "
        "pass baja a limbo.",
    ),
    "tf_t0": (
        "T0 · Comparable",
        "Si la hermana es comparable con su madre: sin recortar, "
        "sin redondeo grande de periodos, con operaciones de sobra.",
    ),
    "tf_t1": (
        "T1 · Frecuencia",
        "Si la hermana opera con la frecuencia que su madre predice "
        "(z_frec contra la mediana de las madres de la misma corrida).",
    ),
    "tf_t2a": ("T2a · oos1", "La hermana frente a su madre en oos1: retención y z_Δ."),
    "tf_t2b": ("T2b · build", "La hermana frente al azar en el build, sin la madre."),
    "tf_z_frec": (
        "z frecuencia",
        "Diferencia de ln(operaciones hermana / madre) frente a la "
        "mediana de la corrida, en errores estándar con sobredispersión.",
    ),
    "tf_z_delta": (
        "z Δ oos1",
        "Ventaja de la madre menos la de la hermana, frente a la misma "
        "diferencia en las corridas al azar conjuntas. Cerca de 0: iguales.",
    ),
    "tf_ret": (
        "Retención oos1",
        "Ventaja por operación de la hermana / la de la madre, en R "
        "propia de cada timeframe: lee más en M15 y menos en H1 aunque gane lo mismo "
        "en precio (pregunta abierta del dueño, K-1).",
    ),
    "tf_z_build": (
        "z build",
        "Ventaja de la hermana en el build frente a sus corridas al azar.",
    ),
    "tf_ret_build": (
        "Retención build",
        "Lo mismo que la retención de oos1, en el build.",
    ),
    "tf_ret_build_pct": (
        "Percentil retención",
        "Percentil de esa retención entre las madres "
        "comparables de la corrida; vacío con menos de las mínimas.",
    ),
}
