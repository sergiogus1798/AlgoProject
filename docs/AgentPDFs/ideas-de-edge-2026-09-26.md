# Ideas de edge — lo que le falta al proyecto para estar al nivel de una mesa quant

**Dossier del dueño, 2026-09-26.** Sale de una revisión del proyecto entero (WORKFLOW, `OPEN.md`,
`engines/`, `studies/`, `ledger/`, `pipeline/`, `assets/` y el índice de datos) con una pregunta:
aparte de la UI, la cartera y MT5, ¿qué falta y qué habría que hacer diferente para que la
herramienta esté al nivel de la investigación cuant de una casa grande?

**Estado: las catorce ideas de este dossier están aceptadas por el dueño (2026-09-26), sin encargo todavía.** La búsqueda por internet de la misma noche es otro dossier: `ideas-de-internet-y-libros-2026-09-27.md`. Ninguna está construida. Cuando una
se convierta en trabajo, sale de aquí y entra en `docs/encargos/` como encargo autocontenido; lo que
se aprenda al hacerla va a `knowhow/`. Las ideas que el dueño no eligió (costes, backtester propio,
reglas de muerte) quedan en la conversación del día y no aquí, salvo que las pida.

Lo que ya está al nivel y **no** hay que rehacer: la disciplina anti-sobreajuste. Ledger global de
búsquedas, puerta de un solo sentido sobre `oos2`, paso 20 ciego forzado por código, nulo de mono con
escalera de canales, SPA/StepM, CSCV, DSR con sigma acumulada, costes por tarea, identidad por hash.
Lo que falta está **antes** de esa cadena (de dónde salen las hipótesis) y **alrededor** (qué se
aprende de correrla).

---

## Las seis de la primera tanda

### 1 · Un pase completo antes de ninguna pieza nueva

**Qué.** La cadena de 25 pasos no ha producido ninguna superviviente real: el paso 24 espera «una
superviviente real» y el control con población nula (`docs/encargos/9-monos-de-punta-a-punta.md`)
está escrito y aparcado. `OPEN.md` §43: de 23 puntos de entrada de Python se han ejercitado 7.
`OPEN.md` §45: el nulo no es reproducible entre corridas (227 y 229 supervivientes sobre los mismos
ficheros).

**Por qué es edge.** Hasta que una población nula y una real hayan cruzado la cadena entera, no se
sabe si la cadena filtra o tritura, y cada paso que se añade antes de ese pase se ajustará después
mirando el resultado. La complejidad ya es un riesgo: 76.000 líneas de Python y un `OPEN.md` de
1.300 líneas sin un resultado que valide el conjunto.

**Orden propuesto.** (a) Fijar el seed (§45, una línea, cambia los p almacenados una vez: decisión
del dueño). (b) Ejercitar los 23 puntos de entrada sobre el proyecto de ejemplo, uno a uno, hasta
que ninguno muera por prerrequisito. (c) Correr la población nula entera (encargo 9). (d) Correr
una población real. Con esos cuatro números el resto de este dossier se ordena solo.

**Coste.** Días de máquina, casi nada de código nuevo. **Congelar estudios nuevos mientras tanto.**

### 2 · Controles positivos: medir la potencia, no sólo el falso positivo

**Qué.** El mono dice cuántas estrategias **sin** edge pasan cada filtro (error de tipo I). Nada dice
cuántas **con** edge mueren en ellos (error de tipo II). Se construyen estrategias sintéticas con un
edge plantado de tamaño conocido sobre barras reales, se pasan por la cadena y se mide qué fracción
recupera cada paso, por tamaño de edge.

**Cómo plantar el edge.** Sobre las entradas de un mono, desplazar el P&L por operación una cantidad
`δ` en unidades de ATR (0,02 · 0,05 · 0,10 · 0,20), o sesgar la elección de la barra de entrada hacia
las que tienen recorrido a favor con probabilidad `1/2 + ε`. Las dos formas ya las soporta
`engines/nulls/` (la escalera fija canales y da otros al azar; aquí se fija el canal con sesgo). El
resultado es una **curva de potencia por paso**: con `δ = 0,05` ATR el paso 8 recupera el 60 %, el 14
el 40 %, la cadena entera el 12 %.

**Por qué es edge.** Un filtro que mata el 90 % de los edges pequeños es una trituradora, y los edges
reales a M30/H1 son pequeños. Sin esta curva, un «cero supervivientes» no distingue entre «no hay
nada» y «lo había y lo matamos». Es lo que separa un protocolo de un ritual.

**Dónde.** `studies/screening/falsePositives/` ya existe para el control negativo; el positivo es su
hermano y comparte el motor. **Depende de la idea 1**: sin el pase nulo no hay línea base.

### 3 · El espacio de hipótesis, no el filtro, es donde vive el edge

**Qué.** Hoy toda hipótesis nace de la búsqueda genética de SQX sobre indicadores técnicos en OHLC de
un solo activo, con una condición fija del dueño y un hueco aleatorio. Los filtros quitan falsos
positivos; **no crean edge**. Si la búsqueda ocurre donde no hay nada, salen cero supervivientes con la
mejor cadena del mundo.

**Familias con prior estructural que hoy no existen como plantilla.** Cada una es una razón
económica de por qué debería haber algo, no un indicador:

| familia | prior | qué bloque haría falta |
|---|---|---|
| sesión y hora | la liquidez y la volatilidad no son uniformes en el día; el solape Londres/NY y las aperturas concentran el movimiento | condición de sesión (pendiente de las horas UTC del dueño, paso 22) |
| calendario | rollover, fin de mes, día de vencimiento, viernes; flujos que se repiten por obligación, no por opinión | día del mes / semana como condición |
| lead-lag entre activos | el oro sigue al dólar y a los tipos reales; los índices arrastran a los cruces de yen | condición sobre un **segundo símbolo** (SQX soporta cartas adicionales) |
| régimen de volatilidad como generación | hoy el mapa condicional (paso 22) lo lee como diagnóstico; la idea es **generar** ya condicionado al tercil de volatilidad, porque un edge de régimen diluido en toda la muestra no pasa ningún filtro | percentil de ATR como condición fija |
| estacionalidad intradía de la volatilidad | el mismo breakout vale distinto según la hora; una plantilla que sólo entra en la hora en que el rango histórico se abre | hora + rango relativo |

**Por qué es edge.** La ventaja de una casa grande no es testar mejor: es buscar donde otros no
buscan. El generador de SQX busca donde busca todo el que tiene SQX.

**Primer paso barato.** Una plantilla por familia (`/sqx-strategy-template`), el mismo build, y la
idea 4 dice qué familia rinde por encima del mono. No hace falta construir las cinco: dos bastan
para saber si la vía vale.

### 4 · El ledger como tablero de rendimiento de la fábrica

**Qué.** `ledger/` registra cada búsqueda y cuenta el embudo por estudio. Nadie lo lee **entre**
estudios. Falta una vista: por familia de plantilla × activo × timeframe, cuántas entraron, cuántas
cruzaron cada paso, y **a qué tasa respecto al mono** de esa misma celda.

```
familia            activo  TF   entran  paso 8  paso 14  paso 20  mono@20  ratio
keltnerUpperCrossUp XAUUSD M30  10 000   1 200      310        5      4    1,25
emaCloseAbove       XAUUSD M30  10 000     900      150        0      4    0,00
sesión-LondresNY    EURUSD H1   10 000   2 100      800       19      4    4,75
```

**Por qué es edge.** Esa tabla decide a dónde va la CPU la semana siguiente. Es la diferencia entre
una fábrica con métricas de rendimiento y una colección de experimentos. Una casa grande gestiona
sus hipótesis como una cartera: asigna presupuesto de búsqueda a las familias que rinden.

**Coste.** Casi nada: es una consulta sobre lo que `ledger/` ya guarda, más una columna
`family` consistente (ya existe en `study.py`) y el mono por celda (idea 1). Un `ledger.yield`
que imprima esa tabla, y una zona en la ventana cuando toque.

### 8 · Un segundo proveedor de datos, y un calendario económico

**Qué.** Los 13 feeds son M1 de un proveedor por activo (Dukascopy vía the5ers/Infinox, FTMO para el
Brent), sin bid/ask ni calendario. Se propone (a) un segundo histórico M1 por activo principal de
otro origen, y (b) el calendario económico (NFP, FOMC, CPI, BCE, BoJ) como tabla en `AlgoData`.

**«Arbitrarlas» quiere decir esto.** `feedQuality` hoy detecta anomalías (picos, precios congelados,
huecos) pero **no puede decidir** si una barra rara es un dato malo o un movimiento real: sólo tiene
un testigo. Con dos proveedores, una barra que los dos tienen es real y se deja; una que sólo tiene
uno es un tick malo y se marca. Y se puede medir algo más importante: **qué parte del P&L de una
estrategia se gana en barras en las que los dos proveedores discrepan**. Si el edge vive ahí, es
edge del proveedor, no del mercado, y no se cobrará en MT5.

**El calendario responde otra pregunta.** Sin él no se puede saber si un edge es un efecto de
noticias: una estrategia que gana en las 12 horas alrededor del NFP y pierde el resto está apostando
al evento, y eso tiene otro riesgo (deslizamiento, spread, gaps) que el backtest a spread fijo no
cobra. Se usa como corte del mapa condicional (paso 22), no como filtro.

**Coste.** Datos, no código: el dueño decide el proveedor. Dukascopy da ticks con bid y ask, que
además alimentarían un modelo de spread por hora si algún día se quiere.

### 9 · La multiplicidad **entre** estudios

**Qué.** El ledger corrige la búsqueda **dentro** de un estudio (un activo, un timeframe, una
familia). Cuando se hayan hecho cuarenta estudios, el número de estudios es otro nivel de búsqueda:
el mejor de cuarenta estudios nulos también parece bueno. `trials.accumulated` ya sabe acumular
momentos entre búsquedas; falta que se acumule **entre estudios** y que el DSR de una superviviente
se calcule contra el N de toda la fábrica, no sólo el de su estudio.

**Por qué es edge.** Es la misma corrección que el proyecto ya aplica, un nivel más arriba. Sin ella,
la fábrica se engaña exactamente igual que un generador sin ledger, sólo que más despacio.

**Coste.** Una tabla global de estudios y una línea más en `ledger.report`: «esta superviviente es 1
de K estudios; su DSR global es X». La sigma sí hay que pensarla: la dispersión del Sharpe entre
estudios de activos distintos no es la de dentro de uno (`knowhow/research/`, la tarjeta del pool de
varianzas).

---

## Las ocho de la segunda tanda — aceptadas también (dueño, 2026-09-26)

Ordenadas por lo que creo que dan por lo que cuestan. Mismo estado que las seis: aceptadas, sin encargo.

### A · Los datos nuevos son el único OOS renovable

`oos2` se gasta una vez y ya está. Pero cada mes llegan barras que **no existían** cuando se
seleccionó ninguna estrategia: son OOS virgen para todas las supervivientes pasadas, gratis y sin
sesgo de selección posible. Se propone que `sync_bars` dispare un retest automático de cada
superviviente sobre el tramo nuevo y escriba una fila en el ledger: «paper OOS». Al cabo de un año
cada superviviente tiene doce meses que nadie miró al elegirla. Es el test más honesto que existe y
no cuesta nada más que esperar. Esto no es el holdout que el dueño rechazó (§24): no reserva nada de
lo que ya se tiene.

### B · Operar la meseta, no la madre

El paso 16.5 fabrica la nube de variantes y la sección E del PDF del dueño prohíbe sustituir la
madre por el mejor clon. La idea es la contraria: **operar el promedio equiponderado de la región
estable** (las variantes de la meseta que la nube ya identifica), en vez de un punto. Un punto lleva
la varianza de la elección; el promedio de veinte vecinos la reduce sin elegir. En SQX es una
cartera de variantes con el lote repartido; en MT5, N órdenes pequeñas. Se mide con la CSCV: si la
meseta promediada tiene menos PBO que la madre, se opera la meseta.

### C · La varianza de semilla del generador

Ya está anotado que el generador da resultados distintos según la semilla
(`knowhow/research/`, la tarjeta de la GA). Falta medirlo como diagnóstico: el mismo build con
`k` semillas, y el **solape del decil superior** entre semillas. Si dos semillas dan poblaciones
disjuntas, la «búsqueda» es ruido y lo que manda es el número de estrategias, no su calidad; y la
familia entera debería tratarse como una sola tirada grande, no como diez búsquedas. Un build de
cada uno de los `k`, una tabla, y una decisión: cuántas semillas por estudio.

### D · El ledger como conjunto de entrenamiento

Con decenas de miles de estrategias generadas y su suerte OOS conocida, se puede ajustar un
meta-modelo: **qué rasgos IS y qué estructura** (indicadores, número de parámetros, operaciones,
familia, activo) predicen sobrevivir. `studies/screening/isOos` ya hace la versión de un estudio
(«qué proxies IS valen dentro del decil superior»). La versión de fábrica cruza estudios. **Se usa
como prior de a dónde buscar y qué generar, nunca como filtro de selección**: un filtro aprendido
sobre supervivientes es la selección múltiple otra vez. Depende de la idea 4 y de tener varios
estudios completos.

### E · Métricas en unidades de riesgo, no en dólares

Un lote fijo sobre el oro, que va de 800 a 3.500, pondera los años recientes en todo lo que se mide
en dólares: beneficio neto, drawdown, R Expectancy. Los dos spreads por segmento arreglan el coste,
no el tamaño. Se propone medir en **R por operación** (P&L / ATR de entrada × valor del punto) o
con un tamaño por volatilidad congelado antes de mirar, y que la puerta, el SPP y el paso 20 lean esa
columna. El mono ya tiene el canal de tamaño por ATR; la idea es que la estrategia real se mida igual
que su nulo. Cambia números en los pasos 8 a 20, así que es una decisión del dueño.

### F · El feed del broker que va a operar

Las estrategias se construyen sobre Dukascopy y se operarán sobre el feed del broker de la cuenta.
Los nombres de los feeds (`_the5ers`, `_Infinox`, `_ftmo`) ya llevan el broker; la idea es un
cross-check explícito **antes** de MT5: la superviviente retesteada sobre el histórico del broker
real, y la diferencia de P&L como número en el certificado de la estrategia. Si el 30 % del edge
desaparece al cambiar de feed, se sabe antes de arriesgar dinero, y se sabe cuánto de la idea 8 (los
dos proveedores) hace falta.

### G · La cadencia de la fábrica

`studies/screening/decay` mide cuánto se degrada una población de IS a OOS, y `profitShape` si la
media cambió dentro de la muestra. Ninguno responde a **cada cuánto hay que regenerar**. La vida
media del edge por familia, leída de las supervivientes en paper OOS (idea A), da ese número: si el
edge dura dos años, la fábrica corre cada seis meses y una superviviente se retira a los dieciocho.
Hoy ese número no existe y se opera «hasta que deje de funcionar».

### H · Reproducibilidad como propiedad, no como costumbre

Cada informe lleva su manifest, pero no hay **un comando** que reconstruya un informe desde él y
compruebe que sale igual. Se propone `tools/reproduce.py <informe>`: lee el manifest, vuelve a correr
el estudio sobre los mismos ficheros con el mismo config y compara el JSON. Los tests golden lo
hacen sobre fixtures; esto lo hace sobre resultados reales, y es lo que hace que una cifra del
ledger sea una afirmación y no un recuerdo. Barato, y detecta a la primera casos como §45.

---

## Lo que este dossier no verifica

- Ningún número de la tabla de la idea 4 es real: es la forma de la tabla, no un resultado.
- Los tamaños de edge plantado de la idea 2 (0,02 a 0,20 ATR) son una primera rejilla, no una
  calibración: la rejilla buena sale del edge por coste medido en la cosecha de la puerta.
- Que SQX admita una condición sobre un segundo símbolo en el hueco aleatorio (idea 3, lead-lag) no
  está probado en este proyecto; sí que admite cartas adicionales en una estrategia.
- Las cinco familias de la idea 3 son priors, no evidencia: la evidencia la dará la idea 4.
