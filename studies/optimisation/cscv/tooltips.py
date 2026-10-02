"""One sentence per config.yaml knob, for the window's configuration drawer."""

TIPS = {
    "min_trades": "Una combinación que opera menos que esto en alguna de las dos muestras no "
                  "entra en la nube.",
    "split_mode": "Qué se considera fuera de muestra: oos2_only (la lectura estricta) o "
                  "oos1_oos2.",
    "cscv.period": "Las filas de la matriz de rendimientos: D días de mercado (la de López "
                   "de Prado, por defecto), W semanas, ME meses.",
    "cscv.score": "El estadístico por el que se ordenan las variantes: sharpe o sortino, "
                  "nunca Ret/DD.",
    "cscv.blocks": "Bloques en que se corta la historia; 16 dan C(16,8) = 12.870 "
                   "particiones.",
    "cscv.rules": "Las reglas de elección que se juzgan, la primera es la titular.",
    "cscv.random_draws": "Sorteos de la regla aleatoria entre las rentables.",
    "cscv.bootstrap": "Remuestreos del intervalo del percentil fuera de muestra.",
    "cscv.cluster_k_max": "Grupos máximos al contar cuántas pruebas independientes hay.",
    "cscv.seed": "Semilla de todo lo aleatorio del CSCV."}
