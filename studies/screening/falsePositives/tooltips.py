"""One sentence per config.yaml knob, for the window's configuration drawer."""

TIPS = {
    "monkeys.per_donor": "Cuántos monos se sortean con la huella de cada estrategia real: "
    "donantes × este número es la población nula que cruza la cadena.",
    "monkeys.rung": "Qué conserva el mono de su donante: «free» sólo el número de operaciones "
    "y el coste; «timing» también la duración y el tamaño de cada una.",
    "monkeys.sizing": "Cómo se dimensiona cada operación del mono: «atr» con la volatilidad de "
    "la barra anterior a donde cae (como la doctrina), «donor» con el tamaño "
    "de la donante.",
    "population.per_level": "Estrategias por población de prueba: se sortean per_level / "
    "per_donor donantes de la cosecha. Más, tasas más finas y más tiempo.",
    "population.edges": "Los niveles de ventaja plantada (Sharpe por operación, neto: lo que "
    "queda después de los costes), una población cada uno además de la "
    "nula.",
    "population.seed": "Raíz de todos los sorteos; vacía, cada corrida sortea una nueva y la "
    "anota. Con la misma raíz la corrida se repite igual.",
}
