"""One sentence per config.yaml knob, for the window's configuration drawer."""

TIPS = {
    "shuffles": "Cuántas veces se baraja el exceso entre las variantes para saber qué R² "
    "ajustado da el ruido puro con estos coeficientes y estas variantes.",
    "shuffle_percentile": "El ranking sólo se lee si el R² ajustado real supera este percentil "
    "de los barajados; con 95, el ruido puro se da por legible 1 vez de 20.",
    "heatmap_pairs": "Cuántos parámetros, los de mayor índice de Sobol total, se cruzan de dos "
    "en dos en los mapas de calor: 4 dan 6 mapas.",
    "per_coefficient": "Por debajo de estas variantes por coeficiente de la superficie "
    "cuadrática, el informe avisa.",
    "sobol_power": "2 elevado a esto puntos base para los índices de Sobol; es aritmética "
    "sobre la superficie, no backtests.",
    "seed": "Semilla de los índices de Sobol y de los barajados.",
    "floor_is_per_param": "Operaciones en build que necesita una variante por cada parámetro "
    "vivo para entrar en el mapa; es el mismo suelo del WFC.",
}
