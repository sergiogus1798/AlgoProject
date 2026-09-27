"""One sentence per config.yaml knob of the spread study, for the window's configuration drawer."""

TIPS = {
    "assets": "Cada activo con su feed de ticks de Darwinex (de donde sale el spread real) y "
              "su feed M1 de Dukascopy (de donde sale la volatilidad de los años sin ticks).",
    "day.min_minutes": "Un día con menos minutos cotizados que esto —festivo, medio día— no "
                       "entra en el ajuste del modelo: su spread medio no es el de un día normal.",
    "constancy.tolerance": "El spread relativo al precio se da por constante si la media de "
                           "cada año completo queda a ± esta fracción de la mediana de los años.",
    "model.candidates": "Los modelos del spread relativo que se comparan en la validación: "
                        "constante en %, constante en puntos, por volatilidad y por "
                        "volatilidad y precio.",
    "model.split": "Primer año del segundo pliegue: cada modelo se ajusta en un lado de este "
                   "año y se juzga por cómo predice el otro, en los dos sentidos.",
    "model.fixed": "El modelo que el dueño eligió para un activo, aunque otro valide mejor: "
                   "`relativo` es el spread proporcional al precio.",
    "safety.factor": "Margen sobre el spread medido al proponer el coste que se declara en SQX.",
    "reprice.near_minutes": "Una operación cuyo minuto no tiene tick de Darwinex a menos de "
                            "estos minutos se reajusta con el spread del modelo, no con uno real.",
    "reprice.judge": "Contra qué se juzga si una estrategia se rompe: sólo el spread real, o el "
                     "spread real más un slippage que es la mitad de él en cada relleno.",
    "reprice.action": "mark sólo señala la estrategia que no cubre el spread real; drop escribe "
                      "DESCARTAR en verdict.csv para que /curate la saque.",
    "band.assets": "Cada activo con su feed de ticks de Darwinex: la curva sólo necesita los ticks.",
    "band.quantiles": "Los cuantiles del spread diario que se ajustan como curvas del precio; el "
                      "primero y el último dan el Min y el Max del MC Retest de spread.",
    "band.min_minutes": "Un día con menos minutos cotizados que esto no entra en el ajuste.",
}
