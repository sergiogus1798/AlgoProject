"""One sentence per config.yaml knob, for the window's configuration drawer.

A screen's knob is addressed by the screen's own name, as `--set` takes it."""

TIPS = {
    "presencia.kind": "Dura: la estrategia que no pasa esta criba muere aquí y no llega a la siguiente.",
    "sanidad.kind": "Dura: la estrategia que no pasa esta criba muere aquí y no llega a la siguiente.",
    "estaticas.kind": "Dura: la estrategia que no pasa esta criba muere aquí y no llega a la siguiente.",
    "degradacion.kind": "Dura: la estrategia que no pasa esta criba muere aquí y no llega a la siguiente.",
    "forma.kind": "Dura: la estrategia que no pasa esta criba muere aquí y no llega a la siguiente.",
    "mono.kind": "Dura: la estrategia que no pasa esta criba muere aquí y no llega a la siguiente.",
    "familia.kind": "Blanda: esta criba mide y avisa, pero no elimina a nadie.",
    "redundancia.kind": "Blanda: esta criba mide y avisa, pero no elimina a nadie.",
    "sanidad.min_trades": "Operaciones mínimas en la cosecha para que la estrategia se lea.",
    "estaticas.keep": "La condición sobre las métricas fuera de muestra que tiene que cumplir, "
                      "escrita como la lee la criba.",
    "estaticas.value": "La métrica que se enseña como número de esta criba.",
    "degradacion.min_retention": "Qué parte del filo dentro de muestra tiene que sobrevivir "
                                 "fuera.",
    "degradacion.min_t": "Cuántos errores estándar tiene que batir lo que queda.",
    "degradacion.min_years_positive": "Años fuera de muestra con beneficio positivo, como "
                                      "mínimo.",
    "degradacion.max_concentration": "Parte del beneficio fuera de muestra que puede poner "
                                     "un solo año.",
    "forma.max_dd_ratio": "Cuántas veces puede ser el peor descenso fuera de muestra el "
                          "esperado; 5 es casi no pedir nada.",
    "mono.statistic": "El estadístico con el que la estrategia se mide contra sus monos.",
    "mono.rung": "El peldaño del nulo; timing sólo aleatoriza el momento de entrar.",
    "mono.max_p": "La p más alta que se deja pasar; laxa a propósito.",
    "familia.alpha": "Nivel de la corrección por multiplicidad sobre todas las p del mono. "
                     "Blanda: informa, no elimina.",
    "monkey.draws": "Runs nulos por estrategia; el resto de mandos del nulo son los de "
                    "engines/nulls/config.yaml.",
    "monkey.timeframe": "Las barras sobre las que se colocan los monos.",
    "monkey.seed": "Raíz de los sorteos del mono; vacía, cada corrida sortea una nueva y la "
                   "anota en el scorecard.",
    "cascade.on": "Encendida, una estrategia sale en su primer Falla y no se le calcula nada "
                  "más; apagada, se calcula todo para todas.",
    "drift.window": "Ventana de calendario en la que se mide la deriva del mercado y se "
                    "sortean los monos (year, semester o quarter); más corta resta más mercado "
                    "y deja menos exceso.",
    "drift.variant": "Cómo se calcula lo que habría ganado una operación ciega: a la de hoy, "
                     "b por ventana, c con la operación ciega de la misma duración, d las dos.",
    "drift.se_skew_kurt": "Corrige el error estándar de la t por el sesgo y la curtosis del "
                          "exceso; apagado, la t es la clásica.",
    "frequency.phi_min": "Sobredispersión mínima que se admite para la frecuencia; subirla "
                         "ensancha el error y hace la z de frecuencia más indulgente.",
    "frequency.phi_max": "Sobredispersión máxima que se admite para la frecuencia; bajarla "
                         "hace la z de frecuencia más exigente con las estrategias irregulares.",
    "centring.min_strategies": "Estrategias mínimas del mismo activo, timeframe y lado para "
                               "restar el centro de la población; con menos no se centra.",
    "centring.cap_log_rate": "Cuánto puede valer como mucho el centro de la frecuencia, en "
                             "logaritmo; lo que pase de ahí cuenta contra cada estrategia.",
    "centring.cap_slope": "Cuánto puede valer como mucho el centro de la pendiente del exceso; "
                          "vacío, el centro no tiene tope.",
    "cost_stress.k": "Por cuánto se multiplica el coste de cada operación al estresarlo; "
                     "subirlo exige más ventaja sobre el coste.",
    "concentration.drop_trades": "Cuántas de las mejores operaciones se quitan antes de "
                                 "recalcular la t; más, más exigente.",
    "concentration.drop_period": "El mejor periodo natural que se quita antes de recalcular la "
                                 "t (quarter = trimestre).",
    "mae.percentile": "Percentil de la peor excursión en contra de las operaciones que se "
                      "compara con 1R; 100 sería la peor de todas.",
    "delay.variants": "Qué retrasos de una barra se prueban: E la entrada, S la salida, ES las "
                      "dos; se juzga el peor.",
    "delay.on_build": "Encendido, el retraso se prueba también sobre las operaciones del build.",
    "homogeneity.permutations": "Veces que se barajan las operaciones entre periodos; más, una "
                                "p más fina y más tiempo.",
    "homogeneity.period": "El periodo natural en que se parte oos1 para comparar el exceso "
                          "(quarter = trimestre).",
    "homogeneity.min_trades": "Operaciones mínimas de un periodo; con menos, se une al siguiente.",
    "homogeneity.seed": "Raíz de las permutaciones; vacía, cada corrida sortea una nueva y la "
                        "anota en el scorecard.",
    "drawdown.block": "Operaciones seguidas que se remuestrean juntas; más largo conserva más "
                      "las rachas.",
    "drawdown.sequences": "Secuencias remuestreadas con las que se compara el drawdown; más, "
                          "una p más fina y más tiempo.",
    "drawdown.seed": "Raíz del remuestreo; vacía, cada corrida sortea una nueva y la anota en "
                     "el scorecard."}
