"""What each profile measure and each of its columns means, one Spanish sentence each."""

MEASURES = {
    "vr4": "Variance ratio a 4 barras: por encima de 1 los movimientos se suman (persisten); "
           "por debajo se deshacen. No opera: sólo dice si hay persistencia.",
    "vr16": "Variance ratio a 16 barras: lo mismo que el de 4, a un horizonte más largo.",
    "hurst": "Exponente de Hurst: más de 0,5 es tendencial, menos es reversivo, 0,5 es azar.",
    "look12_hold4": "Si las 12 barras pasadas subieron, se compra y se mantiene 4 barras.",
    "look12_hold16": "Si las 12 barras pasadas subieron, se compra y se mantiene 16 barras.",
    "look48_hold4": "Si las 48 barras pasadas subieron, se compra y se mantiene 4 barras.",
    "look48_hold16": "Si las 48 barras pasadas subieron, se compra y se mantiene 16 barras.",
    "fitschen": "Mapa de Fitschen: se compra cuando el cierre está 1 desviación por encima de su "
                "media y se mantiene 5 barras: ¿sigue o vuelve?",
    "channel20": "Se compra al cerrar por encima del máximo de 20 barras y se mantiene 8.",
    "channel55": "Se compra al cerrar por encima del máximo de 55 barras y se mantiene 8.",
    "false_break20": "Rupturas del canal de 20 barras que vuelven dentro en 5 barras o menos: "
                     "cuántas son falsas.",
    "vr4_low": "Variance ratio a 4 barras leído al revés: por debajo de 1, el precio revierte.",
    "vr16_low": "Variance ratio a 16 barras leído al revés: por debajo de 1, el precio revierte.",
    "stationarity": "Dickey-Fuller sobre el precio: ¿vuelve a un nivel? Su vida media, en barras.",
    "pullback_speed": "Dickey-Fuller sobre la distancia a la media: lo deprisa que el precio "
                      "vuelve a ella (vida media en barras).",
    "extreme2": "Se compra cuando el precio está 2 ATR por debajo de su media y se mantiene 8 "
                "barras (en corto, el espejo).",
    "extreme3": "Se compra cuando el precio está 3 ATR por debajo de su media y se mantiene 8 "
                "barras (en corto, el espejo).",
    "bar1atr": "Tras una barra de más de 1 ATR a favor, se entra y se mantiene 4 barras.",
    "bar2atr": "Tras una barra de más de 2 ATR a favor, se entra y se mantiene 4 barras.",
    "bar3atr": "Tras una barra de más de 3 ATR a favor, se entra y se mantiene 4 barras.",
    "range_acf": "Autocorrelación del rango de las barras: la volatilidad viene en rachas. No opera.",
    "narrow_then": "Rango de la barra siguiente tras una barra estrecha frente a tras una ancha: "
                   "¿la compresión precede a la expansión? No opera.",
    "narrow_break": "Se compra la ruptura de una barra estrecha y se mantiene 4 barras.",
    "inside": "Tras una barra interior que cierra arriba: ¿sube la probabilidad de otra barra "
              "alcista?",
    "engulfing": "Tras una envolvente alcista: ¿sube la probabilidad de otra barra alcista?",
    "run3_follow": "Tras 3 cierres seguidos a favor, se sigue la racha una barra.",
    "run3_fade": "Tras 3 cierres seguidos en contra, se compra contra la racha una barra.",
    "best_hour": "La mejor hora del día para mantener una barra (elegida también dentro del azar).",
    "best_band": "La mejor franja (Asia, Londres, Nueva York) para mantener de su primera barra "
                 "a la última.",
    "best_weekday": "El mejor día de la semana para mantener de apertura a apertura.",
    "band_range": "Se compra cuando, cerrada una franja, una barra cierra por encima del máximo "
                  "de esa franja."}

COLUMNS = {
    "z": "Cuántas desviaciones se separa la medida real de la misma medida sobre 1.000 series "
         "barajadas. Más de 2 empieza a ser raro.",
    "q": "La p corregida por haber hecho unas 4.000 pruebas a la vez (Benjamini-Hochberg). "
         "Menos de 0,05: significativa.",
    "multiple": "Ganancia media por operación dividida entre el coste de ida y vuelta. Hace "
                "falta 2 o más para que pague.",
    "stability": "Parte de los años de build en los que el signo se repite. Más de la mitad: "
                 "estable.",
    "trades_per_year": "Operaciones al año de la medida en build. No es lo que hará una "
                       "estrategia: es el orden de magnitud. El cuarto filtro pide 40 (35 a lo "
                       "sumo para un activo que el dueño nombre).",
    "passes": "Pasa los cuatro filtros: significativa, paga el doble del coste, estable por "
              "años y con operaciones suficientes al año. Desde el 2026-10-02 no es la única "
              "puerta del tablero: también entra lo que la prior del dueño da por Alta y lo "
              "que pasa en meseta en el barrido de salidas."}

CONTEXT = {
    "drift_per_year": "Deriva: lo que el activo sube o baja solo al año (en logaritmos).",
    "abs_acf_1": "Agrupamiento de la volatilidad: autocorrelación del tamaño de los movimientos.",
    "cost_over_atr": "Coste de una operación dividido entre el ATR del marco: cuanto más alto, "
                     "más difícil operar ese marco.",
    "kaufman_daily": "Eficiencia de Kaufman diaria: 1 es una línea recta, 0 es ruido."}

LEVELS = ((10.0, 3, "fuerte: 10 costes o más"), (5.0, 2, "medio: de 5 a 10 costes"),
          (0.0, 1, "justo: de 2 a 5 costes"))


def level(multiple: float) -> tuple[int, str]:
    """The discrete intensity of an effect in cost multiples: (1-3, its label)."""
    return next((n, label) for floor, n, label in LEVELS if multiple >= floor)
