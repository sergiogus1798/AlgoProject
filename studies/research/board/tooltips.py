"""One sentence per config.yaml knob, for the window's configuration drawer."""

TIPS = {
    "weights.prior": "Peso de la prior del dueño (Alta 1, Media 0,5, ninguna 0) en los puntos.",
    "weights.evidence": "Peso de la evidencia medida, graduada, en los puntos.",
    "prior.values": "Valor de 0 a 1 de cada nivel de la prior.",
    "prior.pullback_as": "Familia del perfil bajo la que entra el «pullback» de la prior.",
    "evidence.values": "Valor de cada grado de evidencia: desnuda, barrido en meseta, débil, ninguna, en contra.",
    "evidence.against_brake": "Lo que multiplica los puntos de una celda medida en contra.",
    "page.rows": "Celdas que se imprimen en la página; el resto queda en board.json.",
    "weights.signal": "Peso de la señal del perfil (efecto en múltiplos del coste) en los puntos.",
    "weights.gap": "Peso del hueco de cobertura: lo poco que se ha probado esa familia en la celda.",
    "weights.past": "Peso del rendimiento pasado de la familia en esa clase de activo.",
    "signal.cap": "Efecto, en costes, a partir del cual la señal ya cuenta como completa.",
    "past.prior_strength": "Intentos ficticios a la tasa media: con menos corridas cerradas que "
                           "esto, la tasa de la familia apenas se separa de la media.",
    "past.interval": "Intervalo de credibilidad que se imprime junto a la tasa de supervivencia.",
    "brake.half": "Ideas gastadas en la celda con las que sus puntos se quedan en la mitad.",
    "marks.provisional_costs": "Activos cuyos costes siguen sin cerrar: se marcan, no se excluyen.",
    "taxonomy_family": "La única tabla que traduce las familias del perfil a las de los bloques.",
    "palette.data": "Qué clase de dato lee cada familia de bloques (regla de ortogonalidad).",
    "palette.alike": "Familias que siguen el movimiento: dos de estas juntas son «dos iguales».",
    "palette.counter": "La familia de contratendencia.",
    "palette.weights": "Peso de una familia en el hueco según su relación con la condición fija.",
    "palette.min_block_weight": "Peso mínimo de un bloque en su familia para entrar en la paleta.",
    "selfcheck.min_closed": "Corridas cerradas necesarias para examinar si el perfil orienta.",
    "selfcheck.alpha": "p de Fisher (una cola) con la que se da por probado que orienta."}
