# 20 · ATRCalculator — el stop loss leído del MAE, sin optimizar — encargo autocontenido

> **ESTADO 2026-09-26: construido y fusionado** en `master`. §2 completo, injerto §3.1
> probado en SQX (X = 1000 idéntico operación a operación en IS, oos1 y oos2; el ATR de Python es el
> del stop de SQX), rejilla §3.2 retesteada con la puntuación del dueño (40 % PF, 30 % neto, 30 % DD).
> Percentiles como parámetro (`--percentiles`, por defecto 80 85 90 95). oos2 abierto a este paso en
> el ledger. Probado sobre `Strategy 19.8.78` XAUUSD M30. **No se borra** hasta correrlo sobre una
> superviviente real. Manual: `docs/manual/54-atr-calculator.md`. Es el **paso 24** del WORKFLOW.

**Tu oficio:** Python numérico sobre operaciones y barras M1, más la fábrica de variantes y un
retest en SQX sobre el custodio. Es el **paso 24 del `WORKFLOW.md`**: se corre sobre una estrategia
que ya pasó la secuencia entera, nunca sobre una población.

Lee `CLAUDE.md` · `CODESTYLE.md` · `studies/CLAUDE.md` · `core/study/CONTRACT.md` ·
`docs/AgentPDFs/WORKFLOW.md` §«El paso 24» · `knowhow/research/research-lessons.md` ·
`knowhow/export/orderstocsv-schema.md` · `knowhow/export/exits-and-m1-library.md` ·
`knowhow/sqx-format/writing-a-variant.md` · el skill `/variants`.

---

**Dónde va:** `studies/closing/atrCalculator/`, junto a `exposure/` y `blindJoint/`. Forma de
módulo: `studies/CLAUDE.md`; contrato del resultado: `core/study/CONTRACT.md`; página de manual
nueva en `docs/manual/` en la misma tarea (regla 8). La parte de SQX (el injerto, §3) va en
`sqx/variants/`, no dentro del estudio.

## 0 · Qué es — y qué NO es

El dueño construye **sin stop a propósito**: un stop es un parámetro más, y cada parámetro es sitio
para el sobreajuste. Pero para operar la estrategia necesita uno.

> *«No quiero que sea una optimización ni nada.»* — el dueño, 2026-09-26

**El stop es un colchón.** Tiene dos trabajos y ninguno es ganar más:

1. **Cortar las pérdidas largas innecesarias** — las operaciones que se fueron tan lejos en contra
   que ya no se recuperan.
2. **Dejar aire a la estrategia** — no saltar con el ruido normal del mercado, que es por donde
   pasan también las operaciones ganadoras.

`SL = X · ATR(20)`, fijo al entrar. **X se lee de las operaciones con una regla fijada antes de
mirar.**

**Prohibido:** barrer X buscando el mejor PF, Ret/DD o neto; elegir entre los sub-estudios el que más
gana; ajustar X mirando el resultado; tocar la lógica de entrada o de salida. Si aparece la
tentación de «probar un par de valores más», el encargo se ha convertido en otra cosa: parar y
preguntar.

## 1 · Decisiones del dueño — 2026-09-26

| | decisión |
|---|---|
| paso | el **24**, tras la exposición y antes de la cartera |
| ATR | **ATR(20) siempre**, en el timeframe de la estrategia, de la barra cerrada antes de la entrada |
| percentil | **parámetro de entrada** con cuatro valores: **80, 85, 90, 95**. Cada uno es un sub-estudio |
| ventana | X se lee **sólo del IS**; `oos1` y `oos2` sirven para ver si se transfiere (§2.3) |
| costes | spread y slippage **los que use SQX**: el coste lo mide el backtest de SQX, no Python (§3) |
| estabilidad | por cada X, variantes un poco por encima y por debajo, con la fábrica de variantes (§3) |
| MT5 | **fuera por ahora**: nada de `StopsLevel` ni restricciones del broker |
| después | qué tests anteriores se repiten sobre la versión con stop lo decide el dueño; este encargo no relanza la cadena |

## 2 · La parte de Python — leer X

Todo en unidades de ATR(20) y por estrategia. Los hechos de partida:

- 🔬 MAE/MFE vienen de `-tools action=orderstocsv`, medidos sobre el camino M1, **en dólares**:
  `precio = abs(MAE_$) / (Size · pointValue)`, con el `Size` de cada operación
  (`knowhow/export/orderstocsv-schema.md`).
- 🔬 Las estrategias de la cadena salen por `Exit After X Bars` (75 %), `Exit Signal` (20 %) y
  `End Of Friday (Time)` (5 %), sin SL ni TP (`knowhow/export/exits-and-m1-library.md`). Una salida
  por barras ya acota lo que una operación puede irse en contra: es probable que el stop casi nunca
  salte. **Es el resultado esperado y bueno**: el stop se pone sin cambiar la estrategia, y el
  estudio lo demuestra con números.
- `archive/studies/atr_stop_study.py` ya calculaba `MAE/ATR`. Reescribirlo sobre `core/`, **no
  portarlo**, y **no heredar su conclusión**: elegía X como el máximo de una rejilla en in-sample,
  justo lo prohibido aquí (`OPEN.md` §13).

### 2.1 · El aire que necesitan las ganadoras → X

La distribución del MAE/ATR de las **operaciones ganadoras del IS**. Para cada percentil de
entrada (80, 85, 90, 95), su valor es la X de ese sub-estudio.

**Con su incertidumbre.** Con 60 ganadoras en el IS, el percentil 95 lo deciden las tres más
extremas: otro puñado de operaciones daría otra X. Cada X sale con su **intervalo por bootstrap**
sobre las ganadoras del IS, y el informe marca las estrategias en las que el intervalo es tan ancho
que la X no significa nada. Confirmado por el dueño (§5).

### 2.2 · El punto sin retorno — la comprobación

Para cada distancia `x`, entre las operaciones del IS que llegaron a ir `x` ATR en contra:

- qué fracción acabó ganando;
- cuál fue su resultado final medio.

Mientras muchas se recuperan, cortar ahí es cortar ruido. Cuando casi ninguna se recupera y el
resultado final medio es peor que `−x`, cortar ahí ahorra dinero sin quitar nada. **No elige X**:
dice en qué zona cae cada una de las cuatro.

### 2.3 · ¿Se transfiere la X del IS? — la pregunta del dueño

> *«¿Será transferible ese valor de X del IS al resto?»*

Hay razones para esperar que sí y una para dudar:

- **A favor:** X está en unidades de ATR, no de precio. Si el oro se vuelve el doble de volátil, el
  ATR se dobla y el stop se aleja solo. Una distancia fija en dólares no se transferiría; una en ATR
  está hecha para eso.
- **En contra:** lo que el ATR no normaliza. Si en `oos1` las operaciones se comportan distinto —más
  recorrido en contra *relativo* a la volatilidad, por un cambio de régimen—, la misma X corta
  proporcionalmente más ganadoras.

Se mide **sin tocar X**, sólo describiendo:

1. **El percentil efectivo.** La X del IS al p90, ¿a qué percentil de las ganadoras de `oos1` y de
   `oos2` corresponde? Si sigue cerca del 90, se transfiere. Si en `oos1` es el p75, esa X corta allí
   un cuarto de las ganadoras en vez de una décima, y el informe lo dice.
2. **La forma entera.** La distribución de MAE/ATR de las ganadoras de IS contra la de `oos1` y la
   de `oos2`, superpuestas, con un test de dos muestras (Kolmogorov-Smirnov o Anderson-Darling) y el
   tamaño del efecto al lado, no sólo la p.

Si no se transfiere, **no se recalcula X en `oos1`**: se informa, y decide el dueño.

## 3 · La parte de SQX — el coste real y la estabilidad

El coste del stop lo mide **SQX con sus propios spread y slippage**, no Python. Python propone las
cuatro X; SQX las pone a prueba.

### 3.1 · El injerto — el primer problema técnico, sin investigar

🔬 La fábrica de variantes (`sqx/variants/build/rewrite.py`) **sólo cambia valores de parámetros que
la estrategia ya declara**. Estas estrategias llevan `SQ.Formulas.SLPT.None`: **no hay parámetro de
stop que variar.** Antes de nada hay que saber **añadir** un stop ATR a un `.sqx` que no lo tiene:

- qué bloque escribe SQX en `strategy_Portfolio.xml` cuando una estrategia *sí* lleva `SL = X·ATR(20)`
  — sacarlo de una estrategia construida con el stop encendido en un proyecto propio del conductor,
  **nunca** cambiando el build de un proyecto del dueño;
- sustituir el `SLPT.None` por ese bloque con X como parámetro declarado, de modo que después la
  fábrica de variantes lo pueda mover como cualquier otro;
- verificar que SQX carga el resultado y que, con X enorme (el stop nunca salta), el retest
  reproduce **operación a operación** el de la estrategia original. Esa es la prueba del injerto.

Lo que se averigüe va a `knowhow/sqx-format/` en la misma tarea. El encargo 12 (editar la lógica
del `.sqx`) ya investigó la ruta XML: leerlo antes de empezar.

### 3.2 · La estabilidad alrededor de cada X

Por cada una de las cuatro X, variantes **un poco por encima y un poco por debajo** —por defecto `±20 %`,
parámetro de entrada—, más la original sin stop como referencia. Todo en **un** custom project
(regla 10), en el custodio, con los costes del activo, sobre IS, `oos1` y `oos2`.

Lo que se lee es la **forma**, no el máximo: alrededor de cada X, ¿el resultado es una meseta o cae
por un lado? Una X en meseta es robusta; una en borde de precipicio no, aunque gane más. Nunca se
elige «la variante que mejor sale».

### 3.3 · Lo que SQX ve y Python no

- **Entradas nuevas:** si el stop cierra antes, la estrategia queda plana antes y puede entrar en
  una señal que en el original ignoró por estar dentro.
- **Convención intrabarra:** si el stop y la salida se tocan en la misma barra, cuál fue primero.

Por eso, si Python y SQX discrepan, manda SQX y se explica la diferencia.

## 4 · Lo que devuelves

Por estrategia y por cada percentil (80, 85, 90, 95):

- X y su intervalo (2.1), y en qué zona cae del punto sin retorno (2.2);
- si se transfiere a `oos1` y a `oos2` (2.3);
- el retest de SQX con esa X contra la original sin stop: cuántas ganadoras mata, cuánta pérdida
  ahorra, la peor operación antes y después, en las tres ventanas;
- la estabilidad alrededor de X (3.2): meseta o borde.

Un resultado según `core/study/CONTRACT.md` que la ventana pueda pintar, con cada estadística
explicada. **El informe no elige percentil**: pone los cuatro uno al lado del otro y el dueño decide.

Cuando esté hecho y verificado, **este encargo se borra** (`README.md` de esta carpeta).

## 5 · Decisiones cerradas — 2026-09-26

1. **Intervalo de X:** sí. Cada X con su intervalo por bootstrap, y las estrategias con intervalo
   demasiado ancho, marcadas. El dueño casi nunca usará una estrategia de pocas operaciones, pero
   lo quiere igual.
2. **Rejilla de estabilidad:** parámetro de entrada, **por defecto `±20 %`** alrededor de cada X.
3. **Ganadora:** P/L **neto** de costes > 0.
4. **Transferencia IS → OOS:** si no se transfiere, se informa y ya —*«es la magia del trading»*—;
   el método de 2.3 (percentil efectivo más forma de la distribución) es el acordado.
