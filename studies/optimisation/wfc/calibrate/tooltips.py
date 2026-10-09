"""One sentence per config.yaml knob of the calibration, for the window's configuration drawer."""

TIPS = {
    "families": "Familias sintéticas por escenario: cuántas veces se mide el criterio sobre "
                "una familia fabricada para saber con qué frecuencia dice PASA.",
    "max_false_pass": "Tope de la fracción de familias SIN ventaja que el criterio da por "
                      "PASA (el falso PASA). Por encima, el registro que abre el bloque ciego se escribe "
                      "cerrado. Provisional: del Council, no del dueño.",
    "max_false_fail": "Tope de la fracción de familias CON ventaja plantada (la casilla de "
                      "referencia) que el criterio da por NO PASA: el error irreversible, "
                      "porque un NO PASA no se revisa. Provisional: del Council, no del dueño.",
    "seed": "Semilla de las familias sintéticas.",
    "family.variants": "Variantes de cada familia sintética.",
    "family.years_in": "Años de dentro de cada familia (build + oos1).",
    "family.own_noise": "Desviación del ruido propio de cada variante, con el factor común "
                        "en 1: fija cuánto se parecen las variantes entre sí.",
    "family.order_spread": "Dispersión de la ventaja entre variantes en «ventaja con "
                           "orden», como fracción de la ventaja.",
    "grid.years_out": "Años de fuera ensayados.",
    "grid.edges": "Ventajas plantadas ensayadas, en Sharpe anualizado del exceso semanal.",
    "grid.costs": "Medias negativas (costes) ensayadas para la familia sin ventaja.",
    "reference.years_out": "Años de fuera de las casillas de referencia de las que sale `abre`.",
    "reference.edge": "Ventaja plantada de la casilla de referencia.",
    "sensitivity.own_noise": "Ruidos propios con los que se repiten las casillas de "
                             "referencia, para ver cuánto depende el resultado de ellos."}
