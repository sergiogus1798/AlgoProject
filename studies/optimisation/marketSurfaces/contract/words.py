"""Every Spanish sentence of step 18.5: labels, meanings, column help, notes and the glossary."""

CATEGORY = {"family": "familia", "structural": "estructural"}     # _markets.yaml's words, on screen
ORDER = {"positivo": "positivo", "neutro": "neutro", "perverso": "perverso", "sin_dato": "sin dato"}
LABEL = {("pass", True): "PASA · la zona viaja", ("pass", False): "PASA · no descarta",
         ("watch", False): "LIMBO", ("fail", False): "NO PASA · orden perverso"}
MEANING = {
    "positivo": "Lo que es mejor en {main} dentro de la familia de variantes tiende a ser también "
                "lo mejor en los otros mercados, más de lo que da el ruido (p+ {p_mas}). Cuenta "
                "como evidencia.",
    "neutro": "El orden de las variantes en {main} no se transmite a los otros mercados ni a "
              "favor ni en contra (p+ {p_mas}, p− {p_menos}): los parámetros no se distinguen "
              "fuera. No descarta.",
    "perverso": "Lo mejor en {main} tiende a ser lo peor en los otros mercados (p− {p_menos}): "
                "el óptimo se ajustó a peculiaridades de {main}.",
    "sin_dato": "Sólo entran en la media mercados por un peso de {peso}, menos de {need}: no hay "
                "con qué medir el orden conjunto."}
LOW = (" La prima del {share} % mejor ({pi}) cae en el p{pct} de su nulo ({cut}) o por debajo: lo "
       "que elegiría el optimizador en {main} rinde fuera peor que una variante cualquiera.")
LATER = " En oos2 el orden conjunto sale perverso (p− {p_menos})."

TAB_NOTE = ("¿Lo que es mejor en {main} dentro de la familia de variantes es también lo mejor en "
            "otros mercados? {main} (build+oos1) contra {n} mercados de _markets.yaml ({cats}), "
            "{window}. El orden se mide con el exceso bruto (antes de costes); la prima, con el neto.")
JOINT_TITLE = "ρ conjunta frente a su nulo — {window}"
JOINT_NOTE = ("La línea es la ρ conjunta: la media, con los pesos, de la correlación de rangos "
              "entre el exceso bruto por año de cada variante en {main} y en cada mercado. El "
              "histograma es la misma media con cada semana de los otros mercados volteada de "
              "signo ({draws} sorteos; el mismo signo para todas las variantes y todos los "
              "mercados; {main} no se voltea): lo que saldría sin ventaja fuera. La banda va del "
              "p5 al p95 del nulo; p es p+, la fracción de sorteos con una ρ igual o mayor.")
MARKETS_TITLE = "Por mercado — no decide"
MARKETS_NOTE = ("Dónde se transmite el orden y dónde no. Ninguna fila decide: decide la media. "
                "Un mercado no entra en la media con menos de {common} variantes comunes o con "
                "más del {ties} % de variantes empatadas.")
MARKETS = {
    "Mercado": "El mercado declarado en _markets.yaml.",
    "Categoría": "La categoría que _markets.yaml le da frente al principal.",
    "ρ": "Correlación de rangos (Spearman) entre el exceso bruto de cada variante en el principal "
         "y en este mercado. 1: mismo orden; 0: sin relación; −1: orden inverso.",
    "p+": "Fracción de sorteos del nulo con una ρ igual o mayor que la observada en este mercado.",
    "p−": "Fracción de sorteos del nulo con una ρ igual o menor que la observada.",
    "Variantes comunes": "Variantes utilizables a la vez en el principal y en este mercado (suelo "
                         "de operaciones por año en cada uno); la ρ y su nulo usan sólo ésas.",
    "Empates (%)": "Porcentaje de esas variantes cuyo exceso aquí es idéntico al de otra: un "
                   "parámetro que no actúa en este mercado deja variantes distintas iguales.",
    "Peso": "Lo que cuenta este mercado en la media: 1, o 1 repartido entre los casi idénticos "
            "de su grupo (_markets.yaml, near_identical). 0: no entra.",
    "Prima π": "Mediana del exceso neto aquí de las variantes del top del principal, menos la "
               "mediana de todas, dividido por el rango intercuartílico del mercado.",
    "Madre (%)": "Porcentaje de las variantes comunes con un exceso neto aquí menor que el de la "
                 "madre. 100: la madre es la mejor; 50: está en medio.",
    "Entra": "Si el mercado entra en la media conjunta."}
CATEGORIES_TITLE = "Por categoría de mercado"
CATEGORIES_NOTE = ("La misma ρ conjunta sólo con los mercados de cada categoría de _markets.yaml: "
                   "si la transmisión depende del tipo de mercado. Se anota; no decide.")
CATEGORIES = [None, "La media ponderada de ρ de los mercados de la categoría que entran.",
              "Fracción de sorteos con una media igual o mayor.",
              "Fracción de sorteos con una media igual o menor.",
              "Suma de los pesos de sus mercados en la media.", "Cuántos mercados suyos entran."]
PREMIUM_TITLE = "Prima del {share} % mejor frente a su nulo"
PREMIUM_NOTE = ("La línea es la prima conjunta: en cada mercado, la mediana del exceso neto de las "
                "variantes del {share} % mejor en {main} menos la mediana de todas, en rangos "
                "intercuartílicos del mercado; después, la media con los pesos. El histograma es "
                "la misma prima con las semanas volteadas (los mismos sorteos que el orden). En o "
                "por debajo del p{pct} del nulo ({cut}), LIMBO: elegir por {main} rinde fuera peor "
                "que una variante cualquiera.")
REFERENCE_TITLE = "Referencia: {main} contra sí mismo"
REFERENCE_NOTE = ("Cuánto orden se conserva en el propio mercado de build a oos1. Si dentro de "
                  "{main} apenas se conserva, no cabe esperar que se conserve fuera. El cociente "
                  "sólo se escribe con una ρ propia por encima de {floor}. Se anota; no decide.")
REFERENCE = ["Spearman entre el exceso bruto de cada variante en build y en oos1 del principal.",
             "La ρ conjunta entre mercados de la primera pestaña.",
             "ρ conjunta / ρ propia: cuánto viaja el orden a otros mercados respecto a lo que "
             "viaja en el tiempo. 1: lo mismo."]
POWER_TITLE = "Potencia: transmisión plantada que el paso es capaz de ver"
POWER_NOTE = ("Para cada ρ verdadera, {draws} familias sin ventaja (las semanas reales volteadas) "
              "a las que se mezcla el orden de {main} hasta esa correlación en cada mercado; la "
              "barra es el porcentaje que el paso lee como orden positivo (p+ ≤ {alpha}). La línea "
              "de referencia es lo que saldría sin transmisión. Se anota; no decide.")
GLOSSARY = [
    {"term": "Exceso bruto y neto", "text": "El resultado de una operación menos la deriva que el "
     "mercado pagó por estar dentro. Bruto: antes de comisión, swap, spread y deslizamiento "
     "(sólo la lógica; con él se mide el orden). Neto: después (el dinero; con él, la prima)."},
    {"term": "Spearman (ρ)", "text": "Correlación entre dos órdenes: 1 si las variantes quedan en "
     "el mismo puesto en los dos mercados, −1 si en el inverso."},
    {"term": "Nulo de volteo por semanas", "text": "Cada semana de los otros mercados se "
     "multiplica por +1 o −1 al azar, el mismo signo para todas las variantes y mercados. Borra "
     "cualquier ventaja fuera y conserva lo que se parecen las variantes y los mercados entre sí."},
    {"term": "Peso", "text": "Los mercados casi idénticos de un grupo de _markets.yaml reparten "
     "un peso total de 1; el resto pesa 1."}]
COSTS = ("Costes provisionales en la ficha de: {markets}. Un coste por operación mueve más a las "
         "variantes que más operan: la prima (neta) puede cambiar cuando se fijen.")
ABSENT = "Declarados en _markets.yaml y sin operaciones en el lote: {markets}. No entran en la media."
OUT = "No entran en la media: {markets}."
GAP = ("El P/L reconstruido no reproduce el NetProfit de SQX en más del {share} % de las "
       "variantes de: {markets}. El exceso bruto de esos mercados no es de fiar.")
STRADDLE = ("El {share} % de las operaciones de los otros mercados cierra lunes o martes tras un "
            "fin de semana abierto (tope {limit} %): el nulo semanal puede salir estrecho. Con "
            "bloques de dos semanas el orden sale {again}.")
