"""The Spanish words of the portfolio result: tab titles, the notes each block opens with."""

MODULE = "portfolio.common.construct"
TABS = {"veredicto": "Veredicto", "universo": "Universo", "parejas": "Parejas",
        "busqueda": "Búsqueda", "cartera": "Cartera"}
STATE = {True: "pass", False: "fail", None: "watch"}

NULL = ("Cada barra cuenta carteras admisibles al azar del mismo tamaño que la elegida, medidas "
        "en oos1 igual que ella; la línea es la cartera elegida. Pasa si queda por encima del "
        "percentil {q:.0f} del azar.")
NO_NULL = ("El azar no discrimina: solo hay {n} combinaciones admisibles de K={k} y la elegida "
           "es ella sola el {share:.0%} de las extracciones. No se dibuja un percentil que no dice nada.")
METRICS = ("Las cuatro métricas de la puntuación y el Sharpe diario de la cartera elegida en "
           "oos1, cada una en su peor valor al desplazar el inicio de la ventana 0-3 meses; por "
           "unidad de riesgo.")
OOS2 = ("Una sola lectura por pool: el Sharpe diario en oos2 menos el máximo que daría el azar "
        "con N pruebas (todas las del proyecto). Pasa si la diferencia es mayor que 0.")
MEMBERS = "Riesgo mínimo: el que exige el lote mínimo en la cuenta. Días: los que cada estrategia aporta por tramo."
FAILING = "Cuántas parejas del pool rechaza cada filtro en build (una pareja puede fallar varios)."
HOLD = ("Las parejas de la cartera elegida medidas otra vez en {segments} con los mismos umbrales. "
        "Se informa: no quita a nadie ni decide el veredicto.")
SCORES = ("La puntuación en build de cada combinación admisible evaluada (0-1: media de los rangos "
          "de las cuatro métricas); la línea es la elegida. Se elige mirando solo build.")
FUNNEL = "De las estrategias del pool a la cartera: cuántas quedan en cada paso y cuántas combinaciones se probaron."
EQUITY = ("P&L acumulado de la cartera a riesgo fijo, por unidad de riesgo, reiniciado en cada "
          "tramo. Tramos dibujados: {segments}. oos2 solo aparece cuando el veredicto lo ha leído. "
          "Las líneas con la identidad de cada miembro son su parte de esa curva, con su peso: suman la cartera.")
MONTHLY = ("Suma del P&L diario de la cartera en cada mes, por unidad de riesgo, en los tramos "
           "dibujados ({segments}); la última columna es el año.")
