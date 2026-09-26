"""One sentence per config.yaml knob, for the window's configuration drawer."""

TIPS = {
    "stop.atr_period": "El periodo del ATR del stop; la cadena usa siempre 20.",
    "stop.percentiles": "Los percentiles del MAE/ATR de las ganadoras del IS que dan cada X; "
                        "uno por sub-estudio, y ninguno se elige.",
    "bootstrap.n": "Cuántas veces se remuestrean las ganadoras del IS para el intervalo de X.",
    "bootstrap.confidence": "La cobertura del intervalo de X.",
    "bootstrap.seed": "La semilla: el mismo informe mañana da el mismo intervalo.",
    "bootstrap.wide": "Un intervalo más ancho que esta parte de X marca la X como poco fiable.",
    "noreturn.x_max": "Hasta qué distancia, en ATR, se recorre el punto sin retorno.",
    "noreturn.x_step": "El paso de esa distancia.",
    "noreturn.recover_max": "«Casi ninguna se recupera»: como mucho esta parte de las que "
                            "llegaron a x acabó ganando. Sólo nombra la zona.",
    "noreturn.min_reached": "Con menos operaciones que esto llegando a x, la zona no se lee.",
    "transfer.tolerance": "Puntos de percentil: si la X del IS sigue a esta distancia de su "
                          "percentil en oos1/oos2, se transfiere.",
    "transfer.min_winners": "Con menos ganadoras fuera de muestra, sólo se enseña.",
    "grid.band": "Cuánto se mueve X arriba y abajo en la rejilla de estabilidad.",
    "grid.steps": "Cuántos pasos a cada lado: 2 con ±20 % da X·{0,8 0,9 1 1,1 1,2}.",
    "shape.tolerance": "Un neto que no se mueve más que esta parte del de X es meseta.",
    "proof.pl_tolerance": "USD: la sonda X = 1000 tiene que reproducir cada P/L a esto.",
    "proof.atr_spread": "Cuánto puede separarse, del p5 al p95, la distancia de cada stop "
                        "partida por X·ATR: en la barra buena sólo la mueve el slippage."}
