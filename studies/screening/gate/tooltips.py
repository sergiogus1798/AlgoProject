"""One sentence per config.yaml knob, for the window's configuration drawer.

A screen's knob is addressed by the screen's own name, as `--set` takes it."""

TIPS = {
    "presencia.kind": "Dura: la estrategia que no pasa esta criba muere aquí y no llega a la siguiente.",
    "sanidad.kind": "Dura: la estrategia que no pasa esta criba muere aquí y no llega a la siguiente.",
    "estaticas.kind": "Dura: la estrategia que no pasa esta criba muere aquí y no llega a la siguiente.",
    "redundancia.kind": "Blanda: esta criba mide y avisa, pero no elimina a nadie.",
    "sanidad.min_trades": "Operaciones mínimas en la cosecha para que la estrategia se lea.",
    "monkey.draws": "Runs nulos por estrategia; el resto de mandos del nulo son los de "
                    "engines/nulls/config.yaml.",
    "monkey.timeframe": "Las barras de la corrida cuando la cosecha no dice su timeframe.",
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
    "drawdown.percentile": "Percentil de los drawdowns remuestreados que se guarda como drawdown "
                           "esperado, en R: 95 = solo 1 de cada 20 secuencias cae más.",
    "drawdown.seed": "Raíz del remuestreo; vacía, cada corrida sortea una nueva y la anota en "
                     "el scorecard."}
