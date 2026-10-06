"""One sentence per config.yaml knob, for the window's configuration drawer."""

TIPS = {
    "monkeys.per_donor": "Cuántos monos se sortean con la huella de cada estrategia real: "
                         "donantes × este número es la población nula que cruza la cadena.",
    "monkeys.rung": "Qué conserva el mono de su donante: «free» sólo el número de operaciones "
                    "y el coste; «timing» también la duración y el tamaño de cada una.",
    "monkeys.sizing": "Cómo se dimensiona cada operación del mono: «donor» con el tamaño de la "
                      "donante, «atr» recalculado con la volatilidad de la barra donde cae.",
    "population.per_level": "Estrategias de prueba por cada nivel de ventaja; más, tasas más "
                            "finas y más tiempo.",
    "population.edges": "Los niveles de ventaja plantada, uno por población de prueba.",
    "population.seed": "Raíz de las poblaciones de prueba; vacía, cada corrida sortea una nueva "
                       "y la anota.",
}
