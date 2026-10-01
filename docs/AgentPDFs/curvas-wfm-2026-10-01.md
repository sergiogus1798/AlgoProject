# Las 30 curvas del WFM: qué pueden decir del sobreajuste y de si merece la pena operar

*2026-10-01. Datos: `AlgoData/raw/Test_XAUUSD_donchianUpperCrossUp_H1/WFM/2026-10-01/wfm/`, las 5
madres del WFM del custodio, sólo el tramo fuera de muestra de cada celda (2016-06 → 2026-08). Bases:
el dossier `ideas-de-internet-y-libros-2026-09-27`, las tarjetas de `knowhow/research/` y la
literatura citada en cada punto.*

## 0. Lo que ya dicen las curvas sin construir nada

Tres medidas rápidas sobre los datos reales, antes de proponer:

| estrategia | SQX la marca | Sharpe de la celda mediana | celdas independientes de 30 | Sharpe del oro comprado, mismo tramo |
|---|---|---|---|---|
| 9.10.57 | **aprueba** | 0,47 | **1,6** | 0,64 |
| 4.18.70 | suspende (11 de 12) | 0,59 | 2,0 | 0,64 |
| 4.19.71 | suspende | 0,53 | 2,5 | 0,64 |
| 20.25.72 | suspende | 0,51 | 2,9 | 0,64 |
| 3.21.83 | suspende | −0,24 | 7,2 | 0,64 |

1. **Las 30 celdas no son 30 pruebas: son entre 1,6 y 3.** Su P/L diario se correlaciona 0,56–0,79
   entre celdas (en la que pierde, 0,30). «28 de 30 celdas en beneficio» suena a robustez y equivale
   a decir lo mismo dos o tres veces. *Celdas independientes* = número efectivo de los autovalores de
   la matriz de correlación de las 30 series diarias.
2. **Ganan y pierden los mismos años que el oro.** Las cinco ganan en 2020, 2024 y 2025 y pierden en
   2018, 2021 y 2022 (en 2022 el 0 % de las celdas de 4 de ellas cerró en positivo). Son estrategias
   largas en un activo que subió: el beneficio se parece demasiado al del propio oro.
3. **Ninguna supera a mantener oro comprado**, fuera de muestra y sobre el mismo tramo (Sharpe
   0,45–0,59 frente a 0,64). Al quitarles la parte que es oro (beta diaria), bajan a 0,36–0,46.
4. **La que aprueba en SQX es «perversa» en el estudio del WFM** (ρ IS→OOS −0,49): lo que mejor se
   optimizaba en cada tramo fue lo que peor fue después. Aprobar la matriz no dice que reoptimizar
   sirva.

Esto ya es una decisión para estas cinco: **no merecen operarse tal cual** — no baten a la
alternativa trivial, y el filtro de SQX no lo detecta.

## 1. Propuestas, ordenadas por lo que deciden

Cada una dice la pregunta, qué se mide, qué decisión produce y lo que cuesta.

### A. Contra el oro comprado y contra el trader al azar (decide: ¿se opera?)
- **Pregunta:** ¿las curvas fuera de muestra ganan algo que no gane ya el activo, o una entrada al
  azar con la misma huella?
- **Mide:** Sharpe de cada celda frente a comprar y mantener con el mismo riesgo; alfa tras quitar la
  beta diaria; y el benchmark del trader aleatorio de `core/significance.footprint` (ya existe, se usa
  en el paso 8) aplicado a la celda recomendada. Regla del dueño: el azar sólo fuera de muestra — se
  cumple, las curvas del WFM son todas OOS.
- **Decisión:** si la mediana de las celdas no bate a ninguno de los dos, se descarta, apruebe o no
  la matriz. **Coste:** bajo, todo existe. **Recomendado: el primero.**

### B. Contar las celdas como lo que valen (decide: ¿cuánto creer el «% de celdas rentables»?)
- **Pregunta:** ¿cuántas pruebas independientes hay de verdad en la matriz?
- **Mide:** número efectivo de celdas (arriba); y repetir cada estadístico agregado con un bootstrap
  por bloques de calendario en vez de por celdas — es la mejora nº 1 que el propio
  `POSSIBLE_IMPROVEMENTS.md` del WFM tiene apuntada.
- **Decisión:** el intervalo honesto de la tabla «El conjunto de las celdas»; un % de celdas que no
  significa nada cuando el número efectivo es 2. **Coste:** bajo.

### C. Año a año y la decadencia del edge (decide: ¿el edge sigue vivo?)
- **Pregunta:** ¿el edge depende de un régimen (oro alcista) o se gasta con el tiempo?
  (Chan, *Quantitative Trading* pp. 24-25 y 52-53; Katz pp. 86-92.)
- **Mide:** P/L por año natural de cada celda y la parte de celdas en positivo por año (la tabla de
  §0 lo enseña), la pendiente del Sharpe anual, y P(año perdedor) (Blake). Con un régimen de
  volatilidad o de tendencia del oro (`engines/regimes/`) como explicación.
- **Decisión:** «sólo gana en oro alcista» → no se opera sola; como mucho dentro de una cartera con
  algo que gane en los años malos. **Coste:** bajo-medio.

### D. Reoptimizar o congelar (decide: ¿cómo se opera, si se opera?)
- **Pregunta:** ¿la estrategia reoptimizada rinde más que con sus parámetros fijos?
- **Mide:** el *Score* de SQX por celda (ya en la pestaña «Los objetivos»: PF del walk-forward ÷ PF
  con parámetros fijos) junto con la ρ IS→OOS y la deriva del estudio actual.
- **Decisión:** Score ≈ 100 y ρ ≤ 0 → **se opera con parámetros fijos**; reoptimizar sólo añade
  ruido. Score > 100 con ρ > 0 → se opera reoptimizando cada X días, la combinación ◆. **Coste:** nada
  nuevo; es leer junto lo que ya sale.

### E. Monte Carlo de las curvas contra las reglas de la cuenta de fondeo (decide: ¿qué cuenta y qué riesgo?)
- **Pregunta:** con las curvas fuera de muestra, ¿qué probabilidad hay de pasar y de no quemar la
  cuenta de cada firma?
- **Mide:** las curvas de la celda recomendada por el Monte Carlo de operaciones
  (`portfolio/common/monteCarlo/`, cuyo formato ya encaja) y por la máquina de reglas de fondeo
  (`portfolio/funded/rules/`), que necesita el flotante intradía — aún no sale del export del WFM.
- **Decisión:** riesgo por operación y firma, o descartarla para fondeo. **Coste:** medio (el
  flotante). Es lo que prioriza el dueño (fondeo primero), pero sólo tiene sentido tras A.

### F. Calidad de la curva: K-ratio, Ulcer, tiempo bajo agua (informa, no decide sola)
- Ninguna existe hoy en Python. Útiles para comparar celdas o madres entre sí (Kestner; Martin;
  Fitschen, Chande). **Ojo:** suavidad no es robustez — las curvas más lisas suelen ser las más
  frágiles (Faith pp. 101-104). Por eso va la última.

## 2. Lo que propongo

**A + B + C juntas como un estudio nuevo de la familia `optimisation/` (o una pestaña más del WFM)**,
porque son una sola lectura: *¿el WFM fuera de muestra gana algo que no gane el activo, contado con
el número real de pruebas, y en todos los regímenes?* D es leer lo que ya hay; E después.

## 3. Antes de construir necesito que elijas

1. **¿Qué es «la alternativa trivial» contra la que se mide?** (a) comprar y mantener el activo con
   el mismo riesgo, (b) el trader al azar con la misma huella, o (c) las dos y debe batir a ambas.
2. **¿Qué curva representa a la estrategia?** (a) la celda recomendada ◆ de SQX, (b) la mediana de
   las celdas, o (c) la peor del rectángulo.
3. **¿Dónde va?** (a) una pestaña más dentro del WFM, o (b) un estudio propio que también lea el
   `oos1` y el `oos2` de las madres que no pasaron por el WFM.

## Lo que no está verificado

- El Sharpe usa P/L por fecha de cierre; una operación de varios días cae entera en su cierre, lo
  que rebaja la correlación con el oro diaria (la beta real es mayor que la medida).
- Cinco estrategias de una sola plantilla y un solo activo: no es una población.
- Comparar con el oro comprado por Sharpe ignora el apalancamiento y el coste del swap de mantenerlo.
