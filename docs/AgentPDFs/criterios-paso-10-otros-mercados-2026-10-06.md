# Pasos 9 y 10 — Otros mercados: qué se calcula, con qué estadística y qué criterio hay cargado

**Fecha:** 2026-10-06 · **Para:** el dueño, que va a fijar los criterios él mismo · **Alcance:** sólo los pasos 9 (retest en SQX) y 10 (análisis en Python).

**Qué es:** el documento de consulta del paso 10, con la misma forma que el del paso 8 (`puerta-is-oos-paso-08-especificacion-2026-10-06`). Explica desde cero la estadística que este paso añade, repasa **todos** los números que escribe el estudio (no sólo los dos que hoy lee el criterio), cita el criterio tal como está hoy en `pipeline/autopilot/criteria.yaml`, y cierra con lo que no cuadra y con las decisiones que te quedan.

**De dónde salen los números.** Todos los ejemplos son de la corrida `Trade_NIKKEI225_M30_volatilidadL` del 2026-10-04 (NIKKEI225, M30, largas): diez estrategias retesteadas en once mercados, 39.517 operaciones fuera del NIKKEI. Están **recalculados desde las operaciones y las barras** con el código del estudio y comparados con lo que quedó guardado: los 60 números por estrategia y los de cada mercado coinciden al cuarto decimal. Donde un ejemplo usa sólo el valor guardado, se dice. «Ilustrativo» quiere decir cuenta hecha a mano para enseñar, no medida.

**Ninguna línea de este documento está congelada.** El propio fichero de criterios lo dice en su primera línea de `steps`: provisional hasta que una población sin ventaja haya recorrido la cadena.

---

## 0. En una página

**La pregunta del paso.** ¿La lógica de la estrategia gana también en mercados en los que nunca se ajustó, o sólo ganaba en el suyo?

**Lo que hay cargado hoy** (dos reglas; manda la peor):

| regla (hecho) | Pasa | Limbo | Falla |
|---|---|---|---|
| `excess_t_vs_main_half` | ≥ 0,5 | > 0, o sin dato | ≤ 0 |
| `excess_t_pooled` | ≥ 2,33 | de 1,0 a 2,33 | < 1,0 |

**Lo que sale en la corrida real:** las diez estrategias son **Falla**, por las dos reglas a la vez. La t conjunta va de −6,19 a −1,28.

**Las cinco cosas que conviene saber antes de leer el resto:**

1. **Las diez t conjuntas son negativas por los costes, no por un defecto del estadístico.** La t se calcula sobre el P/L **neto**. En esos once mercados el coste medio cobrado es de 69 USD por operación, y el resultado medio, de −41 USD. Si a cada operación se le devuelve su coste, la t conjunta de las diez queda entre −1,18 y +2,79, con media +0,92 y desviación 1,39: algo por encima de cero, pues el error típico de esa media es 1,39/√10 = 0,44, así que está a unas 2,1 veces de cero, y la desviación supera la de 0,83–0,95 de la calibración. Es compatible con el sesgo de la deriva (+0,4 a +0,6) más un exceso bruto pequeño, pero con diez estrategias de una misma plantilla, que no son independientes, no se pueden separar los dos efectos. La «población nula centrada en cero» con la que se calibró la línea es la de una estrategia que **empata después de costes**; una estrategia sin ventaja que paga costes no empata: pierde el coste, y con miles de operaciones eso son varias unidades de t hacia abajo (apartado 2.11).
2. **Un solo mercado, el cobre (`XCUUSD`), pone entre 0,6 y 2,2 unidades de esa caída.** Su coste es de 192 USD por operación (0,22 desviaciones típicas), entre dos veces y media y cinco veces el de los demás. Aun quitándolo, las diez siguen negativas.
3. **El «número efectivo de mercados» de 9,2–10,1 y el 1,6–1,9 de la evidencia son la misma fórmula con datos distintos.** El 1,6–1,9 sale de las rentabilidades diarias de los índices (lo he reproducido: 1,77 para estos siete). El 9,2–10,1 sale del **exceso semanal de la estrategia** en cada mercado, y ahí la correlación media es de 0,04–0,07, porque estas estrategias están dentro del mercado pocas horas y en momentos distintos (apartado 2.6).
4. **La variante «ciega» que el código recomienda para poner la línea está estropeada en dos mercados de esta corrida** (UK100 y DAX40): un tramo de barras casi planas entre diciembre de 2013 y febrero de 2014 se lleva el 44 % y el 34 % del peso de su cálculo. El criterio lee la variante sin corregir; hoy ninguna de las dos está limpia (apartado 5).
5. **Estas diez estrategias no son un ensayo justo del paso 10.** Salieron de un sorteo del modo de desarrollo; con las reglas del paso 8 de hoy, **las diez fallarían el paso 8** y no habrían llegado aquí. No existe todavía ninguna corrida del paso 10 sobre estrategias que pasen el 8.

---

## 1. Qué son los pasos 9 y 10 y cómo deciden

### 1.1 Dónde están

El paso 8 deja en el databank `OOS` las estrategias que no han fallado la puerta. El **paso 9** las vuelve a probar en SQX en otros mercados. El **paso 10** es Python: lee esas operaciones, calcula sus números y aplica las reglas de `criteria.yaml`. Lo que falla se borra del databank `Retest Markets - Family`, que es el que lee el paso siguiente (los otros timeframes, pasos 10.5 a 12).

Según el Council, este paso y el 12 juntos son la **segunda muestra nueva** de la cadena (la primera es `oos1`, en el paso 8; la tercera, `oos2`, en el 20). Todo lo que hay entre medias relee las mismas operaciones. Y, como otros mercados y otros timeframes comparten el mismo calendario, cuentan como **una sola** evidencia conjunta, no como dos.

### 1.2 El paso 9: la tarea de SQX

Una sola tarea, titulada `Retest Markets - Family`, que lee `OOS` y escribe en el databank del mismo nombre. La escribe `sqx/projects/crossmarket.py` a partir de `assets/`. Es el cross-check «Retest on additional markets» de SQX: la misma estrategia, con los mismos parámetros, en cada mercado de la lista. Cuatro cosas la definen:

- **La lista de mercados está fijada de antemano**, en `assets/_markets.yaml`, por activo principal. No se añade un mercado porque prometía ni se quita porque fue mal: eso convertiría la prueba en una selección.
- **La ventana es la de cada mercado**: de su propio `build` (o su primera barra, lo que llegue más tarde) al final de su propio `oos1`. Nunca las fechas del activo principal, y nunca `oos2`.
- **Los costes son los de cada mercado**, leídos de su ficha en `assets/symbols/`: spread, slippage, comisión y swap. Como una tarea sólo admite un spread y la ventana cubre dos tramos, se cobra el de `oos1`, que es el más caro: «al mercado que tiene que sorprendernos no se le da el precio barato». Si un mercado no tiene ficha, la orden se niega a escribir nada.
- **No filtra nada.** Todas las condiciones de aceptación del cross-check van apagadas (`crossmarket.conditions: []`). Con una viva, SQX no escribiría las estrategias que la incumplen y Python se quedaría sin la mitad de la evidencia: qué mercado mató a qué estrategia.

El timeframe y la precisión son los del test principal; la sesión se hereda, porque `assets/` no declara sesión para un mercado de cross-check. En la corrida real la tarea tardó 929 segundos para 10 estrategias × 11 mercados; el paso 10, 8 segundos.

### 1.3 Qué datos lee el paso 10

Para NIKKEI225 la lista son once mercados en dos grupos:

- **`family`** (familia): comparten motor económico con el principal. Es la prueba fácil: pasarla prueba poco; fallarla dice mucho. Son los siete índices y USDJPY («yen débil y Nikkei al alza son el mismo trade»).
- **`structural`** (estructurales): se parecen en la forma del mercado, no en el motor. Es la prueba difícil. Son el oro, el EURUSD y el cobre.

| mercado | grupo | ventana leída | operaciones (10 estr.) |
|---|---|---|---|
| USA500 | familia | 2012-01 → 2023-12 | 2.750 |
| USATEC | familia | 2012-01 → 2023-12 | 3.013 |
| DJ30 | familia | 2013-09 → 2023-12 | 2.686 |
| DAX40 | familia | 2013-09 → 2023-12 | 3.025 |
| UK100 | familia | 2011-09 → 2023-12 | 2.884 |
| HK50 | familia | 2012-03 → 2023-12 | 2.093 |
| AUS200 | familia | 2013-10 → 2023-12 | 2.474 |
| USDJPY | familia | 2008-01 → 2022-12 | 5.161 |
| XAUUSD | estructural | 2008-01 → 2022-12 | 5.711 |
| EURUSD | estructural | 2008-01 → 2022-12 | 5.276 |
| XCUUSD | estructural | 2012-03 → 2023-12 | 4.444 |

Dos detalles que importan más adelante:

- **El bloque del activo principal sólo cubre `oos1`.** Las operaciones de NIKKEI225 que trae el export van de enero de 2020 a diciembre de 2023 (1.162 operaciones entre las diez). Los otros mercados cubren de 10 a 15 años. Es decir: «el original» con el que se compara cada mercado son 4 años; cada mercado, tres veces más.
- **El activo principal nunca cuenta como evidencia.** Se usa sólo como referencia (`main_…`).

### 1.4 Los tres estados y el corte

| estado | qué significa | qué hace el workflow |
|---|---|---|
| **Pasa** | cumple la línea exigente de las dos reglas | sigue al paso 10.5 |
| **Limbo** | ni prueba ni condena | sigue, **marcada** |
| **Falla** | alguna regla la da por mala | se **borra** de `Retest Markets - Family` |

### 1.5 Cómo se combinan las reglas

Igual que en el paso 8: cada regla lee un hecho y da Pasa, Limbo o Falla, y el resultado de la estrategia es el de **su peor regla** (`pipeline/autopilot/criteria.py:99`). Con las dos reglas de hoy:

- **Pasa** sólo si la mitad de los mercados llega a 0,5 veces el original **y** la t conjunta es ≥ 2,33.
- **Falla** si la mitad de los mercados no llega ni a cero **o** la t conjunta es < 1,0. Basta una.
- **Limbo** en todo lo demás.

Un hecho que falta es Limbo. La primera regla lo dice expresamente (`missing: limbo`); la segunda no dice nada, y sin decirlo también es Limbo.

### 1.6 Tres avisos

1. **En la corrida real el paso 10 no juzgó.** El resumen del piloto dice «ninguno: el paso no tiene criterio»: el 2026-10-04 el paso aún no tenía reglas. Las de hoy se cargaron después. Los veredictos de este documento los he calculado **en memoria** con `pipeline.autopilot.criteria` sobre los hechos de aquella corrida.
2. **Las diez estrategias son un sorteo.** El paso 8 de aquella corrida fue «10.000 → 10 por sorteo de 10», sin mirar el veredicto. Con las reglas del paso 8 que hay hoy en disco, las diez son Falla allí (ocho por tener una t del exceso inferior a 1,65; las otras dos, `3.11.426` y `10.11.484`, por operar menos de 20 veces al año en el build). Esta población enseña cómo se comporta el paso 10 con estrategias **sin ventaja demostrada**, que es útil, pero no cómo trata a las que llegan con mérito.
3. **El modo de desarrollo sigue encendido** (`dev.on: true`), pero sólo sortea en el paso 8 (`at: ["8"]`). En el paso 10 no hay sorteo: se quedan todas las que no fallan.

### 1.7 Las tres estrategias que nos acompañan

De las tres del documento del paso 8 (A `4.9.301`, B `16.11.437`, C `14.3.479`), sólo **C** salió del sorteo y está en esta población. La mantengo con su letra y añado la mejor y la peor de las diez por t conjunta.

| | **C** | **E** | **F** |
|---|---|---|---|
| nombre | `Strategy 14.3.479` | `Strategy 3.11.426` | `Strategy 15.9.352` |
| operaciones en NIKKEI225 (oos1) | 98 | 92 | 167 |
| t del exceso en NIKKEI225 | 0,70 | 2,05 | 0,16 |
| operaciones en los 11 mercados | 4.253 | 2.954 | 5.785 |
| neto en los 11 mercados (USD) | −117.963 | −28.934 | −448.581 |

No hay una de cada veredicto porque no existe: las diez son Falla.

---

## 2. Fundamentos de este paso

### 2.0 Lo que ya sabes del paso 8, en seis líneas

El documento del paso 8 (apartado 2, «La estadística mínima») enseña lo que aquí se da por sabido:

```
error estándar = desv / √n
t = media / (desv / √n) = s × √n            s = media / desv (Sharpe por operación)
n efectivo = n × (1 − ρ) / (1 + ρ)           ρ = autocorrelación de orden 1
p = 1 − Φ(t)                                  Φ(1,65) = 0,95 · Φ(2,33) = 0,99
potencia = Φ( s × √n − línea )
```

La **t** dice a cuántos errores estándar está la media de cero. El **p-valor** es la probabilidad de que una estrategia sin ventaja llegue ahí por suerte; no es la probabilidad de que la estrategia sea buena. La **potencia** es la probabilidad de que una estrategia con ventaja real supere la línea. El **exceso** de una operación es su P/L menos lo que el mercado le habría pagado a cualquiera por estar dentro (la deriva). El resto de conceptos generales —el máximo de N pruebas, la regla de Bayes con tasa base, el «lift» y el «PF de suerte»— están en el glosario del informe `criterios-pasos-6-a-19-explicados-2026-10-06`.

Lo que sigue es lo **nuevo** de este paso.

### 2.1 Otro mercado como muestra nueva: qué prueba y qué no

El generador de SQX probó miles de combinaciones sobre el `build` del NIKKEI225 y se quedó con las que mejor salían. Una parte de lo que vio era estructura real del mercado; otra, coincidencias de ese histórico concreto. Las coincidencias **no viajan**: la racha que hizo ganar a una regla en el NIKKEI en 2015 no está en el oro. Si la regla gana también en el oro, hay dos explicaciones posibles —captura algo general de cómo se mueven los precios, o ha tenido suerte otra vez— y la segunda se puede medir con una t, porque el oro no participó en la selección.

Eso es lo que hace de otro mercado una **muestra nueva**: datos que el proceso de búsqueda no tocó.

**Lo que puede probar.** Que la ventaja no es un ajuste a un histórico concreto. Y, de paso, multiplica las operaciones: C tiene 98 operaciones en `oos1` del NIKKEI y 4.253 en los once mercados. Es el único punto de la cadena donde la prueba gana potencia de verdad.

**Lo que no puede probar, y por qué.**

- **Que funcionará en el futuro.** Los otros mercados están en los mismos años. Si la ventaja dependía de una época (tipos a cero, poca volatilidad), todos los mercados la comparten.
- **Con los de familia, casi nada si pasa.** Los siete índices se mueven juntos: su correlación semanal media en estos datos es 0,68 (la cifra que usa el cálculo del apartado 2.7; antes decía 0,69). Ganar en el DAX los mismos días que en el NIKKEI puede ser el mismo trade contado dos veces. Peor: el `build` del DAX (2013–2019) coincide con el `build` que el generador vio en el NIKKEI, así que para un pariente cercano ni siquiera los años son nuevos.
- **Que una estrategia que falla esté rota.** Una lógica que explota algo propio del NIKKEI (su sesión, su subasta) es legítima y no tiene por qué viajar. Kaufman lo dice así: un especialista de un solo mercado puede hacerlo mejor.
- **Nada sobre un mercado concreto.** La prueba es de grupo. Katz: con los mismos parámetros en una cesta, que fallen uno o dos mercados de nueve es lo esperado; no se usa para elegir mercados.

### 2.2 Escalar: por qué una estrategia hecha en un mercado no se puede leer tal cual en otro

El NIKKEI cotiza a 30.000; el EURUSD, a 1,10; el oro, a 1.300. Tres cosas tienen que estar escaladas para que la comparación tenga sentido.

**1. El tamaño de la posición.** La doctrina dimensiona por riesgo dividido por la volatilidad (ATR): más lotes cuando el mercado está tranquilo, menos cuando se agita. Así una operación arriesga más o menos lo mismo —1R, 1.000 USD nominales— en cualquier mercado. En C se ve:

| mercado | lotes medios | valor del punto | resultado medio absoluto (USD) |
|---|---|---|---|
| NIKKEI225 | 69,85 | 0,0631 | 369 |
| USA500 | 68,38 | 0,988 | 315 |
| XAUUSD | 1,00 | 99,76 | 340 |
| EURUSD | 1,91 | 99.669 | 314 |

Lotes que van de 1 a 70 y un «valor del punto» que va de 0,06 a casi 100.000, y aun así la operación típica mueve entre 314 y 369 USD en los cuatro. Eso es lo que hace el dimensionado por ATR, y es lo que permite **sumar** dólares de mercados distintos en la t conjunta. Sin él, el mercado con las operaciones más grandes decidiría solo.

**2. El valor del punto.** Es cuántos USD vale un punto de precio por lote. El estudio no lo lee de ninguna ficha: lo **mide** en cada mercado como la pendiente de la recta que relaciona el P/L de cada operación con su movimiento:

```
movimiento = lado × (precio de cierre − precio de apertura) × lotes
valor del punto = pendiente de la recta  P/L ≈ valor × movimiento
```

(`simulate/excess.py:31`). Hace falta para convertir la deriva del mercado, que está en puntos, a dólares.

**3. La unidad común para comparar mercados.** Para poner el oro, el DAX y el EURUSD en un mismo eje, el estudio divide la rentabilidad de cada operación por «lo que se mueve una barra típica» de ese mercado:

```
unidad del mercado = mediana de (ATR / precio)          (mechanics/pricing.py:33)
R media = media de la rentabilidad neta por operación / unidad del mercado
```

En USATEC la unidad es 0,00189 (una barra de M30 mueve un 0,19 % del precio); en EURUSD, 0,00100. Es una constante por mercado, igual para la corrida real y para sus entradas al azar, así que no puede mover un p-valor: sólo hace comparables los mercados.

**Lo que el estudio no comprueba.** Que las reglas internas de la estrategia estén expresadas en unidades que viajan (múltiplos de ATR, porcentajes) y no en puntos fijos. Una estrategia con una distancia fija en puntos del NIKKEI no tendría sentido en el EURUSD. La señal indirecta es `trades_min`: `Strategy 19.2.363` hizo 497 operaciones en el cobre y sólo 15 en USDJPY y 26 en EURUSD.

### 2.3 El exceso y la t de un mercado

Es la misma cuenta del paso 8, mercado a mercado (`simulate/excess.py:12` y `:74`).

```
μ        = media de (cierre − cierre anterior), sobre las barras entre la primera entrada
           y la última salida de la estrategia en ese mercado
deriva   = lado × μ × barras abierta × lotes × valor del punto
exceso e = P/L de la operación − deriva
t        = media de e / desv de e × √(n efectivo)
```

**Los costes están dentro del P/L.** El exceso es «la operación tal como la vio la cuenta» menos la deriva. Esta frase es la clave del apartado 2.11.

**Ejemplo: C en USA500.** La ventana va del 1-02-2012 al 19-12-2023: el índice pasa de 1.325,42 a 4.739,86 en 112.209 barras.

```
μ = (4.739,86 − 1.325,42) / 112.208 = 0,03043 puntos por barra
```

Su primera operación: larga, del 1-02-2012 17:00 al 2-02-2012 16:30 (15 barras), 80,52 lotes, +18,50 USD. Valor del punto medido: 0,98774.

```
deriva = 1 × 0,03043 × 15 × 80,52 × 0,98774 = 36,30 USD
e      = 18,50 − 36,30 = −17,80 USD
```

Ganó 18 USD, pero el mercado «le debía» 36 sólo por estar dentro: frente al mercado perdió 18.

Sobre sus 248 operaciones en USA500: media de `e` = −43,77 USD, desviación = 460,20 USD, ρ = 0,0153.

```
n efectivo = 248 × (1 − 0,0153) / (1 + 0,0153) = 240,5
t = −43,77 / 460,20 × √240,5 = −0,0951 × 15,51 = −1,475
```

Coincide con el hecho guardado (`excess_t` = −1,4749).

### 2.4 La serie semanal y la t conjunta

Hecho: `crossmarket.verdict_csv.excess_t_pooled`

**El problema.** Tienes once t, una por mercado. ¿Cómo se juntan en una sola respuesta? Lo ingenuo sería tratarlas como once pruebas independientes. No lo son: si el S&P y el Nasdaq caen el mismo jueves, la estrategia pierde en los dos a la vez, y eso es **una** mala tarde, no dos.

**La solución.** En vez de combinar las t, se combinan los dólares, por semanas (`simulate/excess.py:121` y `:196`):

1. En cada mercado, el exceso de cada operación se asigna a **la semana en la que se cerró** (semanas que terminan en viernes). Una semana sin cierres vale 0.
2. Se suman los once mercados, semana a semana. Queda **una sola serie**: «lo que ganó la estrategia frente al mercado, en todos los mercados juntos, cada semana».
3. Se calcula la t de esa serie, con su n efectivo:

```
S(w) = suma, sobre los mercados, del exceso cerrado en la semana w
t conjunta = media de S / desv de S × √(n efectivo de semanas)
```

**Por qué esto resuelve la dependencia.** Si dos mercados son el mismo trade, sus ganancias y pérdidas caen en las mismas semanas. Al sumarlos, las semanas buenas son el doble de buenas y las malas el doble de malas: la **media** se dobla, pero la **desviación** también, y la t no sube. Si son independientes, las semanas buenas de uno se cruzan con las malas del otro: la media se dobla y la desviación sólo crece √2, y la t sube √2. La dependencia queda recogida **dentro de la dispersión semanal**, sin tener que suponer ni estimar cuántos mercados independientes hay.

**Por qué semanas.** Hace falta una caja de tiempo común para alinear mercados que operan a horas distintas. El día es demasiado estrecho: Asia, Europa y América cierran en momentos distintos y una misma noticia caería en días diferentes. La semana es la caja más corta que mete dentro esa descoordinación y todavía deja muchas observaciones: 835 semanas en este ejemplo.

**Ejemplo: una semana de C.** La que termina el viernes 2-12-2022, en la que cerró operaciones en los once mercados (exceso en USD):

| mercado | exceso | mercado | exceso |
|---|---|---|---|
| USA500 | +856,9 | EURUSD | −374,9 |
| USATEC | +598,6 | XCUUSD | −402,8 |
| DJ30 | +306,1 | AUS200 | −558,7 |
| DAX40 | +119,3 | UK100 | −900,3 |
| HK50 | +6,0 | USDJPY | −216,4 |
| | | XAUUSD | −221,2 |

Suma: **S = −787,5 USD**. Esa es la observación de esa semana. Fíjate en que los tres índices americanos ganan juntos: esa es la dependencia que la suma absorbe.

**Ejemplo: la t conjunta de C.** La serie tiene 835 semanas, del 4-01-2008 al 29-12-2023. Media de S = −160,81 USD; desviación = 1.335,43 USD; ρ = 0,0023.

```
n efectivo = 835 × (1 − 0,0023) / (1 + 0,0023) = 831,1
t conjunta = −160,81 / 1.335,43 × √831,1 = −0,1204 × 28,83 = −3,47
```

Coincide con el hecho guardado (−3,4715). Las tres estrategias:

| | C | E | F |
|---|---|---|---|
| media semanal (USD) | −160,81 | −88,95 | −627,15 |
| desviación semanal (USD) | 1.335,43 | 2.007,28 | 2.928,37 |
| n efectivo de semanas | 831,1 | 835 | 835 |
| **`excess_t_pooled`** | **−3,47** | **−1,28** | **−6,19** |

**Un detalle del calendario.** La serie empieza en 2008, pero entre 2008 y 2012 sólo hay tres mercados con datos (oro, EURUSD y USDJPY); los ocho restantes entran entre 2011 y 2013. Las primeras semanas pesan lo mismo que las últimas en la media, pero llevan menos mercados. La prueba sigue siendo válida; simplemente no es «once mercados durante dieciséis años».

**Lo medido.** En poblaciones de estrategias que empatan, la t conjunta semanal tiene una desviación de 0,83 a 0,95: algo menos que el 1 teórico, es decir, la prueba es ligeramente conservadora. Con desviación 0,95, la línea de 2,33 la supera el 0,7 % de esas estrategias (`1 − Φ(2,33 / 0,95)`); con 0,83, el 0,25 %.

### 2.5 La variante ciega

Hecho: `crossmarket.verdict_csv.excess_blind_t_pooled`

**Qué cambia.** Sólo el término que se resta. La versión normal resta «la barra media × barras abierta». La ciega resta lo que habría ganado **una operación ciega de la misma duración, dimensionada como dimensiona la doctrina** (`simulate/excess.py:40`):

```
W(h) = media ponderada, sobre todas las barras j de la ventana, de
       ( apertura de la barra j+h − apertura de la barra j ),  con peso 1 / ATR(j)
exceso ciego = P/L − lado × lotes × valor del punto × W(h)       h = barras abierta
```

**Por qué existe.** La versión normal supone que el tamaño de la operación y el movimiento que viene después no tienen relación. Sí la tienen: la doctrina pone más lotes cuando el ATR es bajo, y en muchos activos a las épocas tranquilas les sigue un movimiento distinto de la media. El resultado, medido, es que la t de una estrategia sin ventaja queda **desplazada según el lado**: entre ±0,02 y ±0,27 por mercado, con signo contrario para largos y cortos. Y al juntar mercados del mismo lado el sesgo se acumula: una estrategia que empata sale con una t conjunta de **+0,4 a +0,6**, y los cortos en listas de índices pasan la línea del 5 % el 9–13 % de las veces. El peso 1/ATR hace que la operación ciega «dimensione» igual que la real, y el sesgo se va (medido: quita cerca del 60 %).

**Ejemplo.** La misma primera operación de C en USA500 (15 barras, 80,52 lotes):

```
versión normal:  μ × 15 = 0,4564 puntos  →  deriva 36,30 USD  →  e = −17,80
versión ciega:   W(15)  = 0,3441 puntos  →  deriva 27,37 USD  →  e = −8,87
```

La operación ciega ponderada por 1/ATR gana menos que «15 barras medias», porque en USA500 los periodos tranquilos (donde la doctrina carga más lotes) subieron menos que la media.

**Cuánto cambia el resultado.** En esta corrida, poco en el conjunto: la t conjunta ciega va de −6,56 a −1,43 (mediana −3,02) frente a −6,19 a −1,28 (mediana −2,93). Pero en dos mercados cambia mucho y **por un mal motivo**, que se explica en el apartado 5.2.

### 2.6 Correlación entre mercados y número efectivo de mercados

Hecho: `crossmarket.verdict_csv.markets_effective`

**La idea.** Once mercados que se mueven igual valen por uno. Once que no tienen nada que ver valen por once. El número efectivo dice dónde estás entre esos dos extremos.

**La correlación**, `ρ`, entre dos series va de −1 a +1: +1 si suben y bajan siempre a la vez, 0 si no tienen relación, −1 si una sube cuando la otra baja.

**La fórmula del código** (`simulate/excess.py:232`), que se llama «razón de participación»:

```
k efectivo = k² / ( suma de ρ(i,j)² sobre todas las parejas, incluidas las de cada mercado consigo mismo )
```

`k` es el número de mercados. La correlación de un mercado consigo mismo es 1, así que la suma siempre vale al menos `k`.

**Comprobación en los extremos.** Con `k` mercados sin relación, la suma es `k` (sólo los unos de la diagonal) y sale `k² / k = k`. Con `k` mercados idénticos, todas las correlaciones son 1, la suma es `k²`, y sale 1.

**Ejemplo a mano con tres mercados.** Dos se parecen mucho (ρ = 0,8) y el tercero va por libre (ρ = 0,2 con cada uno):

```
        M1    M2    M3
M1     1,0   0,8   0,2
M2     0,8   1,0   0,2
M3     0,2   0,2   1,0

suma de cuadrados = 3 × 1²  +  2 × (0,8² + 0,2² + 0,2²)
                  = 3 + 2 × (0,64 + 0,04 + 0,04) = 3 + 1,44 = 4,44
k efectivo = 3² / 4,44 = 9 / 4,44 = 2,03
```

Tres mercados que valen por dos: M1 y M2 son casi uno solo, y M3 es otro.

**Por qué siete índices valen por menos de dos.** Con siete mercados y una correlación de 0,68 entre todos:

```
suma = 7 + 42 × 0,68² = 7 + 19,42 = 26,42          (42 = 7 × 6 parejas ordenadas)
k efectivo = 49 / 26,42 = 1,85
```

**La conciliación que estaba pendiente.** El informe anterior dejó escrito que no había podido casar el 1,6–1,9 de la evidencia para los índices con el 9,2–10,1 que marca el hecho en esta corrida. **Son la misma fórmula aplicada a dos series distintas.** Lo he calculado con las dos:

| de qué se calcula la correlación | 7 índices | los 11 mercados |
|---|---|---|
| rentabilidad **diaria del mercado** (1.626 días comunes, 2013–2022) | **1,77** | 3,43 |
| rentabilidad semanal del mercado (451 semanas) | 1,74 | 3,34 |
| **exceso semanal de la estrategia** (las diez) | 4,8 – 6,2 | **9,2 – 10,1** |

- La primera fila es la de la evidencia (la ficha `knowhow/research/crossmarket-effective-markets.md` dice «rentabilidades diarias»). Reproduce su rango: 1,77 está dentro de 1,6–1,9. Mide **cuánto se parecen los mercados**.
- La tercera es la del hecho `markets_effective`. Mide **cuánto se parecieron los resultados de esta estrategia** de un mercado a otro.

**Por qué sale tan distinto.** La correlación media entre los índices es 0,68 si miras el mercado y 0,09–0,22 si miras el exceso de la estrategia. Tres motivos:

1. **La estrategia está dentro muy poco tiempo.** La duración mediana de las operaciones de C es de 3 a 5 barras de M30: hora y media a dos horas y media. El movimiento conjunto de los índices en una semana ocurre casi todo cuando la estrategia está fuera.
2. **No entra a la vez en todos.** En una semana cualquiera C cierra alguna operación en el 17–24 % de las semanas en cada índice, y en el 42–47 % en oro, EURUSD y USDJPY. Las semanas sin operación valen 0, y dos series llenas de ceros en sitios distintos correlacionan poco.
3. **Se ha restado la deriva**, que era parte de lo común.

Queda parecido donde se espera: en C, USA500–USATEC 0,42 y USA500–DJ30 0,36.

**Cuál vale.** Para saber cuánta evidencia independiente hay en los resultados de una estrategia, lo que cuenta es la correlación de **sus resultados**, o sea, la del hecho. Pero es un número por estrategia, ruidoso, y sólo describe a estrategias como estas, de operaciones cortas. El 1,6–1,9 es el **peor caso**: el de una estrategia que entra a la vez en todos los índices y aguanta días. La propuesta de exigir más a los índices (t conjunta ≥ 2,9) se hizo pensando en ese peor caso.

**Dos advertencias sobre la fórmula.**

- **Usa las correlaciones al cuadrado.** Para la pregunta «¿cuánto crece la t al sumar mercados?» la cuenta exacta usa la correlación sin elevar:

```
k para la suma = k / ( 1 + (k − 1) × ρ media )
```

  En el ejemplo de tres mercados, ρ media = 0,4 y sale 3 / 1,8 = 1,67, no 2,03. Con siete índices a 0,68: 1,38, no 1,85. En las diez estrategias reales: de 6,0 a 8,1, no de 9,2 a 10,1. La razón de participación siempre da un número igual o más alto cuando las correlaciones son positivas. No es un error —mide «cuántas direcciones independientes hay»—, pero es más optimista que la cuenta que rige la t conjunta.
- **Un mercado con pocas operaciones lo deja sin dato.** La correlación entre dos mercados sólo se calcula si coinciden al menos 26 semanas; si alguna pareja no llega, el hecho entero sale vacío. Le pasa a `Strategy 19.2.363` (15 operaciones en USDJPY).

### 2.7 Stouffer: la combinación que no hay que usar

Hecho: `crossmarket.verdict_csv.excess_t_stouffer`

**La fórmula** (`simulate/excess.py:223`):

```
Stouffer = ( t1 + t2 + … + tk ) / √k
```

**La intuición.** Si cada t es una normal de media 0 y desviación 1, y las `k` son **independientes**, su suma tiene desviación √k. Al dividir por √k se vuelve a una normal estándar, y se puede leer con las mismas líneas (1,65; 2,33).

**El supuesto que falla.** «Independientes». Si no lo son, la suma baila más que √k y el resultado ya no es una normal estándar:

```
varianza de Stouffer = 1 + (k − 1) × ρ media de las t
```

**Ejemplo a mano.** Tres mercados con t = 1,2; 1,1 y 1,0. Ninguno llega a 1,65.

```
Stouffer = (1,2 + 1,1 + 1,0) / √3 = 3,3 / 1,732 = 1,91
```

Stouffer dice «significativo al 5 %». Si los tres mercados son independientes, es correcto: tres indicios flojos y distintos suman uno fuerte. Si los tres son el mismo trade (ρ = 1), has visto **una** t de 1,1 tres veces, y no has demostrado nada. La varianza real sería 1 + 2 × 1 = 3, la desviación 1,73, y un 1,91 es un baile corriente (`1,91 / 1,73 = 1,10`).

**Cuánto se infla** (la fórmula, con la línea en 1,65; no son medidas):

| caso | ρ media | desviación real | pasan sin ventaja |
|---|---|---|---|
| lo que Stouffer supone | 0 | 1,00 | 5,0 % |
| 11 mercados, ρ de estas estrategias | 0,05 | 1,22 | 8,9 % |
| 7 índices, ρ de estas estrategias | 0,12 | 1,31 | 10,4 % |
| 13 pares de forex a 0,2 | 0,20 | 1,84 | 18,5 % |
| 7 índices, entrada sincronizada | 0,68 | 2,25 | 23,2 % |

**Lo medido.** Con entradas sincronizadas entre mercados, la varianza de Stouffer sale entre 1,6 y 2,8, y «Stouffer ≥ 1,65» lo pasan entre el **5 y el 24 %** de las estrategias que empatan, según la lista. Una línea que se llama «del 5 %» y deja pasar hasta una de cada cuatro no es una línea. Por eso el Council la vetó como criterio. El hecho se sigue calculando para que puedas compararlo.

**En las tres estrategias:**

| | C | E | F |
|---|---|---|---|
| suma de las 11 t | −14,46 | −5,51 | −23,42 |
| Stouffer = suma / √11 | −4,36 | −1,66 | −7,06 |
| t conjunta semanal | −3,47 | −1,28 | −6,19 |

Stouffer exagera en la misma dirección en las tres. Hay un segundo motivo además de la dependencia: Stouffer da el mismo peso a un mercado con 189 operaciones que a uno con 676; la t conjunta pesa por dólares.

### 2.8 «La mitad de los mercados a 0,5 veces el original»

Hecho: `crossmarket.verdict_csv.excess_t_vs_main_half`, y sus hermanos `trade_t_vs_main_half`, `pf_sqx_vs_main_half`, `net_per_trade_vs_main_half`, `sharpe_sqx_vs_main_half`.

**La pregunta.** No «¿gana en conjunto?», sino «¿se parece lo de fuera a lo de casa, en la mayoría de los sitios?». Es tu formulación: que la mitad de los mercados llegue al menos a la mitad de lo que hizo el original.

**Cómo se calcula** (`simulate/excess.py:158` y `:173`):

1. Para cada mercado, el cociente `estadístico en el mercado / estadístico en el original`.
2. Se ordenan los cocientes de mayor a menor.
3. Se toma el que ocupa la posición `techo(k / 2)`: con 11 mercados, el 6.º; con 9, el 5.º; con 8, el 4.º.

```
mitad(valores) = el techo(k/2)-ésimo mayor
«al menos la mitad de los mercados llegan a x»   ⇔   mitad(valores) ≥ x
```

**No es la mediana.** Con un número impar de mercados coincide con ella. Con un número par, la mediana promedia los dos centrales; esto toma **el mayor de los dos**, que es lo que hace exacta la frase «al menos la mitad».

**Ejemplo ilustrativo con 9 mercados.** El original tiene t = 2,0. Las t de los mercados son 2,4; 1,8; 1,5; 1,2; 1,1; 0,6; 0,2; −0,3; −0,9. Los cocientes, ya ordenados:

```
1,20   0,90   0,75   0,60   0,55   0,30   0,10   −0,15   −0,45
                             ↑ 5.º
```

El hecho vale **0,55**: cinco de los nueve mercados llegan al menos al 55 % del original. Como 0,55 ≥ 0,5, pasaría la regla. Si el quinto fuera 0,45, quedaría en Limbo.

**Ejemplo real: C.** Original: t = 0,7016. Las t de sus once mercados divididas por 0,7016, ordenadas:

```
1,52   0,80   0,80   0,51   −0,22   −0,57   −0,73   −2,10   −4,05   −5,30   −11,26
                                      ↑ 6.º
```

El hecho vale **−0,5695** (es HK50: −0,3996 / 0,7016). Sólo cuatro mercados llegan a la mitad del original; el sexto está en negativo.

**Cuándo sale vacío.**

- **Si el original no es positivo.** Dividir por una pérdida no dice nada: un mercado que pierde la mitad que el original daría un cociente de +0,5. El código no calcula el cociente y el hecho queda sin dato, que para la regla es **Limbo**.
- **Si más de la mitad de los mercados no tiene t** (menos de tres operaciones, o todas iguales).

Para el caso del original negativo existe `excess_t_minus_main_half`: lo mismo sobre la **diferencia** `t del mercado − t del original`, que siempre está definida.

**La trampa del original casi cero.** F tiene t = 0,163 en el NIKKEI. Su sexto mercado tiene t = −1,695, y el cociente es −1,695 / 0,163 = **−10,39**. Ese número no significa «diez veces peor»: significa que el denominador es ruido. Con un original cerca de cero, el cociente no se puede leer; hay que mirar la diferencia. Y al revés: con un original casi cero la regla se cumple sola. Un original de t = 0,05 y un mercado de t = 0,03 dan un cociente de 0,6, que Pasa. Conviene exigir además un mínimo de `main_excess_t`, o leer la diferencia en vez del cociente.

**Los hermanos.** El mismo mecanismo sobre otras cuatro medidas. En C:

| hecho (`…_vs_main_half`) | original | 6.º cociente |
|---|---|---|
| `excess_t` | 0,70 | −0,57 |
| `trade_t` (t sin restar la deriva) | 0,82 | −0,39 |
| `net_per_trade` (USD por operación) | 47,86 | −0,22 |
| `sharpe_sqx` (Sharpe anual) | 0,41 | −0,24 |
| `pf_sqx` (profit factor) | 1,30 | **0,73** |

**Cuidado con el del profit factor.** Un PF nunca es negativo, así que su cociente tampoco. El 0,73 de C corresponde a un PF de 0,94 en el sexto mercado: **pierde dinero**. Con un original de PF 1,9, «la mitad a 0,5 veces» se cumpliría con un PF de 0,95. Nueve de las diez estrategias tienen `pf_sqx_vs_main_half` ≥ 0,5 perdiendo en la mayoría de sus mercados. No sirve como criterio con la escala «0,5 veces».

**Lo medido.** Entre estrategias sin ventaja que tuvieron suerte en el original, la regla «la mitad de los mercados a 1,0 veces» no la pasa ninguna (0 %), y «a 0,5 veces» la pasan **entre el 0,4 y el 6 %**, según la lista (cifra de la calibración del Council, hoy no reproducible: sus ficheros ya no están en disco). Es de las pocas reglas de este tramo con tasa medida.

### 2.9 Amplitud: la fracción de mercados con la esperanza por encima de cero

Hechos: `crossmarket.verdict_csv.cleared`, `…fraction`, `…drop`

**Qué es.** La criba propia del estudio, anterior a `criteria.yaml`: cuenta en cuántos mercados el beneficio medio por operación es positivo **con seguridad estadística**, no sólo positivo.

**El intervalo de confianza por bootstrap.** En vez de una fórmula, se rehace la historia muchas veces:

1. Se toman las rentabilidades netas de las `n` operaciones del mercado, en orden.
2. Se parten en **bloques de 5 operaciones seguidas** (para respetar las rachas).
3. Se sortean bloques **con repetición** hasta juntar otra vez `n` operaciones, y se calcula su media. Eso es «una historia alternativa».
4. Se repite 2.000 veces. Quedan 2.000 medias.
5. El **extremo bajo** del intervalo es el percentil 5 de esas medias: el valor por debajo del cual sólo queda el 5 % de las historias alternativas.

```
esperanza            = media de la rentabilidad neta por operación (logarítmica, del precio de las barras)
esperanza_ci_lo      = percentil 5 de la media en 2.000 remuestreos por bloques de 5
un mercado «despeja» ⇔ esperanza_ci_lo > 0
fracción             = mercados que despejan / mercados
```

(`verdict/significance.py:22`, `verdict/breadth.py:8`, parámetros en `config.yaml`, sección `bootstrap`.) «Despejar el cero» equivale a una prueba a una cola al 5 %: si el extremo bajo del intervalo es > 0, la media remuestreada rara vez (menos del 5 %) cae por debajo de cero. No es la probabilidad de que la ventaja sea real, y con once mercados hay que esperar 0,55 «despejados» por puro azar.

**Ejemplo: C en USATEC** (recalculado desde las operaciones, coincide con lo guardado). 268 operaciones; rentabilidad neta media = 5,01 puntos básicos por operación (0,0501 %); percentil 5 del bootstrap = +1,64 puntos básicos. Como 1,64 > 0, USATEC **despeja**.

Los once mercados de C, en puntos básicos:

| mercado | esperanza | extremo bajo | ¿despeja? |
|---|---|---|---|
| USATEC | +5,01 | +1,64 | sí |
| DJ30 | +2,97 | +0,10 | sí |
| DAX40 | +2,20 | −1,43 | no |
| XAUUSD | +2,04 | −1,27 | no |
| USDJPY | +0,53 | −1,23 | no |
| EURUSD | −0,52 | −2,16 | no |
| USA500 | −1,71 | −4,68 | no |
| HK50 | −4,23 | −10,84 | no |
| AUS200 | −4,36 | −7,67 | no |
| UK100 | −6,98 | −10,00 | no |
| XCUUSD | −20,74 | −25,02 | no |

```
cleared = 2      fraction = 2 / 11 = 0,1818
```

Cinco mercados tienen la esperanza positiva, pero sólo en dos el intervalo entero queda por encima de cero. La diferencia entre «5 ganan» y «2 despejan» es exactamente lo que el intervalo aporta.

**El veredicto propio del estudio.** Si `fraction` ≥ 0,5 (`verdict.breadth_floor`), el estudio escribe MANTENER; si no, DESCARTAR, y el hecho `drop` vale 1. **`criteria.yaml` no lee este veredicto**: es un número más. En la corrida, las diez tienen `drop` = 1.

**Un mercado nunca se excluye.** Si faltan mercados (la estrategia no operó en alguno), cuentan en el denominador como no despejados.

### 2.10 La regla de Katz, en mercados efectivos

**La regla.** Katz prueba los mismos parámetros en una cesta de mercados y observa que **fallar en 1 o 2 de 9 es lo esperado** incluso con una regla buena. La conclusión es de método: se aprueba o se suspende al grupo; no se usa para elegir mercados.

**En proporción:** 1 o 2 de 9 es entre el 11 y el 22 % de fallos tolerados.

**El problema.** Nueve mercados de Katz no son nueve pruebas si se mueven juntos. Lo honesto es aplicar la proporción al número **efectivo**:

```
fallos tolerados = (11 % a 22 %) × k efectivo
```

| lista | k efectivo | fallos tolerados | se lee |
|---|---|---|---|
| 9 mercados independientes | 9 | 1,0 – 2,0 | 1 o 2 |
| 13 pares de forex | 4,1 – 4,7 | 0,5 – 1,0 | como mucho 1 |
| 7 índices (peor caso) | 1,6 – 1,9 | 0,2 – 0,4 | **ninguno** |
| estas diez estrategias (dato del hecho) | 9,2 – 10,1 | 1,0 – 2,2 | 1 o 2 |

La segunda y la tercera fila son la lectura que hizo el Council: en forex cabe un fallo; en índices, ninguno. La cuarta es lo que sale si se usa la correlación de los resultados de estas estrategias en vez de la del mercado.

**Cómo queda la regla cargada frente a Katz.** «La mitad de los mercados a 0,5 veces» tolera que hasta 5 de 11 queden por debajo: en **número** de fallos es mucho más laxa que Katz. En **nivel** es más dura: no pide que el mercado gane, pide que llegue a la mitad de la t del original. Son dos maneras distintas de pedir «anchura», y sólo la segunda tiene tasa de falsos positivos medida.

**En C:** tiene P/L neto positivo en 4 de 11 mercados (esperanza positiva en 5). Con cualquier lectura de Katz, falla.

### 2.11 Por qué la t conjunta de las diez es negativa

**La objeción.** Un revisor señaló que diez t conjuntas entre −6,19 y −1,28, todas negativas, no pueden ser mala suerte si la estadística está centrada en cero con una desviación de 0,83–0,95. Tiene razón en que no es mala suerte. La pregunta es qué la desplaza. He mirado cómo entran los costes y la deriva en la serie de cada mercado.

**Lo que dice el código.** El exceso es `P/L − deriva`, y el P/L es el que escribió SQX: **después** de spread, slippage, comisión y swap. La deriva restada no lleva costes. Por tanto, una operación sin ninguna habilidad no tiene exceso cero: tiene exceso igual a **menos su coste**.

```
exceso esperado de una operación sin ventaja = − coste
desplazamiento de la t de un mercado ≈ − (coste / desv) × √n
```

**Cuánto es el coste.** El estudio lo recupera operación a operación: el resultado bruto reconstruido con los precios de las barras, menos el P/L que dio SQX. Sobre las diez estrategias:

| mercado | P/L medio (USD) | coste medio (USD) | coste / desv |
|---|---|---|---|
| EURUSD | −33,77 | 37,39 | 0,040 |
| DJ30 | +40,36 | 38,73 | 0,041 |
| USDJPY | +6,19 | 40,39 | 0,040 |
| USATEC | +13,52 | 52,17 | 0,052 |
| XAUUSD | −31,55 | 55,42 | 0,061 |
| AUS200 | −63,67 | 58,83 | 0,069 |
| DAX40 | +6,21 | 59,26 | 0,035 |
| HK50 | −53,56 | 67,96 | 0,063 |
| USA500 | −22,02 | 73,36 | 0,078 |
| UK100 | −80,63 | 81,35 | 0,093 |
| **XCUUSD** | **−201,73** | **191,92** | **0,223** |

En el conjunto de las 39.517 operaciones: P/L medio **−40,94 USD**, coste medio **69,33 USD**, deriva restada media **15,96 USD**. Antes de costes, estas estrategias ganan 28 USD por operación, de los que 16 son deriva; lo que queda como exceso bruto son unos 12 USD, 0,012R. Después de costes, pierden 41.

**El coste fija el desplazamiento y el exceso bruto de cada mercado se suma encima (un ruido de ±1 o más).** En el cobre domina el coste (−8,00 previsto, −7,90 real); en los demás el real se aleja hasta 2,4 unidades: UK100 −2,28 previsto / −3,72 real, USA500 −2,27 / −1,47, USDJPY −2,01 / +0,36, DJ30 −0,82 / +1,07. En C:

| mercado | n | coste / desv | desplazamiento previsto | `excess_t` real |
|---|---|---|---|---|
| XCUUSD | 481 | 0,365 | −8,00 | −7,90 |
| UK100 | 303 | 0,131 | −2,28 | −3,72 |
| USA500 | 248 | 0,144 | −2,27 | −1,47 |
| USDJPY | 614 | 0,081 | −2,01 | +0,36 |
| DJ30 | 261 | 0,051 | −0,82 | +1,07 |

En el cobre, el coste explica él solo toda la t: −8,00 previsto, −7,90 real.

**La prueba: devolver los costes.** He recalculado la t conjunta sumando a cada operación su coste (es decir, sobre el exceso **bruto**):

| estrategia | t conjunta (hecho) | sin el cobre | con los costes devueltos |
|---|---|---|---|
| `10.11.484` | −2,12 | −1,20 | +1,79 |
| `13.3.390` | −1,57 | −1,02 | +0,54 |
| `14.3.479` (C) | −3,47 | −1,23 | +2,79 |
| `15.9.352` (F) | −6,19 | −4,56 | −1,18 |
| `16.5.352` | −3,85 | −3,03 | −0,44 |
| `18.5.355` | −3,50 | −2,64 | −0,68 |
| `19.2.363` | −3,05 | −0,92 | +0,26 |
| `3.11.426` (E) | −1,28 | −0,42 | +2,28 |
| `3.9.284` | −2,81 | −0,74 | +2,00 |
| `4.13.338` | −1,66 | −0,78 | +1,83 |

Con los costes devueltos, siete son positivas y tres negativas; media **+0,92**, desviación 1,39. Queda algo por encima de cero: el error típico de esa media es 1,39/√10 = 0,44, así que está a unas 2,1 veces de cero, y la desviación supera la de 0,83–0,95 de la calibración. Es compatible con el sesgo de la deriva (+0,4 a +0,6) más un exceso bruto pequeño, pero con diez estrategias de una misma plantilla, que no son independientes, no se pueden separar los dos efectos. Los costes valen entre 2,1 y 6,3 unidades de t por estrategia.

**Lo que encuentro, en limpio.**

- **El estadístico no está roto.** Hace lo que dice: medir el resultado neto frente a la deriva.
- **La población nula «centrada en cero» era de estrategias que empatan después de costes.** Sirve para saber cuántas de esas pasan la línea (el 0,7 %). No describe a una estrategia real sin ventaja, que paga costes y por eso no empata. La propia ficha de la calibración lo dice: «con costes, una estrategia sin ventaja falla todas las reglas basadas en la t (0–0,6 %)».
- **El sesgo por lado del término de deriva es menor y va en sentido contrario.** Para listas del mismo lado empuja la t conjunta entre +0,4 y +0,6 hacia arriba. La media de +0,92 que queda al devolver los costes es compatible con ese sesgo más un exceso bruto pequeño; con diez estrategias no se pueden separar.
- **El cobre pesa de más.** Su coste recuperado es de 18,7 puntos básicos por operación en C, frente a 0,9–4,4 en los otros diez mercados, y es el único mercado que dispara el aviso `fill_mismatch` del estudio (los precios de las operaciones quedan lejos de los de las barras). Con operaciones de tres barras de M30, ninguna estrategia puede pagar eso. Uno de los tres mercados estructurales lleva a ese coste un suspenso casi seguro, pero el coste recuperado del cobre (192 USD frente a un resultado absoluto típico de unos 340 USD, y con el aviso `fill_mismatch`) es compatible con una ficha de costes errónea o con un desajuste de precios; hasta comprobarlo no se puede decir que el suspenso sea de la estrategia.
- **Lo mismo en todas las corridas guardadas.** En las diez corridas del paso 10 que hay en disco con este hecho (nueve proyectos, 84 filas), la t conjunta va de −6,78 a −1,28, mediana −3,07: **ninguna** es positiva. No son 84 estrategias independientes (varias corridas repiten la misma plantilla de prueba), pero ninguna ha estado cerca de la línea de Limbo.

**La consecuencia para el criterio.** La línea de 2,33 no pide «2,33 de evidencia». Pide que la estrategia, en mercados para los que no se hizo, **cubra primero los costes de todos ellos** y luego saque 2,33 por encima. Es una exigencia legítima —lo que se opera es el neto— pero conviene saber que es esa, porque cambia lo que significa cada banda (apartado 4).

---

## 3. Lo que calcula el estudio, pieza a pieza

El estudio escribe dos ficheros en `reports/<proyecto>/Retest_Markets_-_Family/<día>/crossmarket/`: `verdict.csv` (una fila por estrategia) y `markets.parquet` (una fila por estrategia y mercado). `pipeline/autopilot/facts.py` convierte cada columna numérica en un hecho:

- `crossmarket.verdict_csv.<columna>` — 60 hechos por estrategia.
- `crossmarket.markets.<mercado>.<columna>` — 19 hechos por mercado; con once mercados, 209.

En total, **269 claves** en el `hechos.parquet` de la corrida. Las columnas de texto (el motivo, el grupo, las fechas) no se convierten en hechos.

Los rangos «típicos» son de las diez estrategias de la corrida (para los hechos por mercado, de las 110 parejas estrategia–mercado). Con diez, el percentil 5 y el 95 son casi el mínimo y el máximo; léelos como orientación, no como una distribución.

### 3.1 Los hechos por mercado

Clave: `crossmarket.markets.<mercado>.<hecho>`, con el mercado en minúsculas (`usa500_m1`, `xauusd_m1`…).

Hay dos familias que conviene no mezclar. Una usa **el P/L de SQX en dólares**, sobre todas las operaciones que SQX informó. La otra usa **la rentabilidad logarítmica reconstruida con las barras**, sobre las operaciones que se pudieron situar en la rejilla de barras, y es la que alimenta las entradas al azar.

**Familia del P/L de SQX** (`simulate/excess.py:94`)

| hecho | qué mide | cómo se calcula |
|---|---|---|
| `trades` | operaciones situadas en la rejilla | las que abren y cierran en barras distintas |
| `net_sqx` | neto en USD | suma del P/L |
| `net_per_trade` | USD por operación | media del P/L |
| `pf_sqx` | profit factor | ganancias brutas / pérdidas brutas |
| `sharpe_sqx` | Sharpe anual (tu «Sharpe total») | media / desv del P/L diario × √252 |
| `sharpe_total` | lo mismo | la misma cifra por otro camino |
| `trade_t` | t del P/L sin restar deriva | fórmula de 2.3 sobre el P/L |
| `excess_t` | t del exceso | apartado 2.3 |
| `excess_blind_t` | t del exceso ciego | apartado 2.5 |

**Familia de las barras y las entradas al azar** (`orchestrate/market.py:23` y `:99`)

| hecho | qué mide | cómo se calcula |
|---|---|---|
| `expectancy` | rentabilidad neta media por operación | media de la rentabilidad logarítmica menos el coste recuperado |
| `expectancy_ci_lo` | su extremo bajo | apartado 2.9 |
| `pf` | profit factor sobre rentabilidades | suma de las positivas / suma de las negativas |
| `p` | p frente a entradas al azar | fracción de 10.000 corridas al azar que igualan o superan a la real |
| `z` | distancia a las entradas al azar | (R media real − media de las al azar) / desv de las al azar |
| `edge_r` | ventaja en unidades de ATR | R media real − mediana de las al azar |
| `a` | exceso por barra ocupada | rentabilidad media de las barras con posición − la de todas las barras |
| `a_ci_lo` | su extremo bajo | bootstrap ponderado por duración, percentil 5 |
| `risk_normalised` | `a` por unidad de riesgo | `a` / unidad del mercado |
| `paired_p` | p frente a un pasivo en la misma zona | Wilcoxon a una cola, cada operación contra una ventana de ±3 meses a su alrededor |

**Las entradas al azar, en dos líneas.** El modelo es `block_shift`: toma cada operación real y la **desplaza un número entero de semanas** dentro de su semestre. Conserva el número de operaciones, su duración, su agrupamiento, el día de la semana y la hora; cambia sólo el *cuándo*. Es el único modelo en el que la corrida real y las de azar difieren en una sola cosa, y por eso un p bajo se puede atribuir al momento de la entrada. El sorteo va ligado al calendario para que coincida de un mercado a otro (`simulate/joint.py`).

**Ejemplo: C en USATEC** (recalculado, coincide con lo guardado).

```
R media real          = 0,000501 / 0,001893 = 0,2646      (rentabilidad media / unidad del mercado)
al azar (10.000):     media −0,0326 · mediana −0,0344 · desv 0,1715
z      = (0,2646 − (−0,0326)) / 0,1715 = 1,732
edge_r = 0,2646 − (−0,0344) = 0,2990
p      = 0,0443        (el 4,4 % de las corridas al azar lo igualan o superan)
```

La media de las corridas al azar es negativa (−0,03): es el coste. Aquí sí está descontado, porque las corridas al azar pagan los mismos costes que la real. Por eso `z` y `p` **no** tienen el desplazamiento del apartado 2.11, y `excess_t` sí.

**Cómo leerlos.**

| hecho | p5 | mediana | p95 |
|---|---|---|---|
| `trades` | 116 | 329 | 733 |
| `net_sqx` (USD) | −88.802 | −6.434 | +29.304 |
| `net_per_trade` (USD) | −189,6 | −29,6 | +85,0 |
| `pf_sqx` | 0,55 | 0,91 | 1,30 |
| `pf` | 0,53 | 0,95 | 1,36 |
| `sharpe_sqx` | −1,25 | −0,15 | +0,45 |
| `trade_t` | −4,39 | −0,49 | +1,44 |
| `excess_t` | −4,41 | −1,04 | +1,11 |
| `excess_blind_t` | −5,43 | −0,76 | +1,14 |
| `z` | −1,53 | +0,26 | +1,94 |
| `p` | 0,025 | 0,40 | 0,94 |
| `paired_p` | 0,020 | 0,48 | 0,99 |
| `edge_r` | −0,35 | +0,07 | +0,49 |

- `excess_t`, `trade_t`, `z`: se leen como una t. Alto es bueno. Una `z` alta no implica que la estrategia gane dinero, sólo que supera a una entrada al azar que paga los mismos costes: su mediana aquí es +0,26 mientras la mediana de `net_sqx` es −6.434 USD. Por encima de 1,65 empieza a ser raro por azar. **Fíjate en la diferencia de centro**: la mediana de `z` es +0,26 y la de `excess_t` es −1,04. Es el coste, que `z` descuenta y `excess_t` no.
- `p`, `paired_p`: bajo es bueno. Un p de 0,40 es no decir nada.
- `pf_sqx` y `pf` no siempre coinciden. `pf_sqx` es en dólares (pesa por tamaño); `pf` es sobre rentabilidades (cada operación pesa igual) y con un coste único por mercado. En C sobre el DAX: `pf` = 1,17 y `pf_sqx` = 0,94; la primera dice que gana, la segunda que pierde 3.257 USD.
- `a`, `a_ci_lo`, `expectancy`, `expectancy_ci_lo` están en rentabilidad logarítmica por barra o por operación: números del orden de 0,0001. En una tabla redondeada aparecen como 0,0000. Lo que importa es el signo de los extremos bajos.

**Por mercado, la mediana entre las diez estrategias:**

| mercado | `excess_t` | `z` | `pf_sqx` | `net_sqx` (USD) |
|---|---|---|---|---|
| USDJPY | +0,57 | +0,99 | 1,13 | +13.041 |
| DJ30 | +0,02 | +0,88 | 1,12 | +7.430 |
| EURUSD | −0,21 | +0,57 | 0,96 | −10.608 |
| HK50 | −0,33 | +0,30 | 0,92 | −4.337 |
| DAX40 | −0,51 | +0,70 | 0,98 | −2.368 |
| XAUUSD | −0,68 | +0,52 | 0,94 | −9.118 |
| USATEC | −1,24 | +0,30 | 1,05 | +6.600 |
| USA500 | −1,29 | +0,25 | 0,91 | −6.424 |
| AUS200 | −1,32 | −0,45 | 0,78 | −16.192 |
| UK100 | −1,71 | +0,22 | 0,80 | −24.900 |
| XCUUSD | −4,79 | −0,59 | 0,53 | −88.790 |

### 3.2 La lectura conjunta de las t

Clave: `crossmarket.verdict_csv.<hecho>` (`simulate/excess.py:196`).

| hecho | qué mide | cómo se calcula |
|---|---|---|
| `excess_t_pooled` | todos los mercados como una sola prueba | apartado 2.4 |
| `excess_blind_t_pooled` | lo mismo, término ciego | apartado 2.5 |
| `excess_t_stouffer` | combinación que supone independencia | apartado 2.7 |
| `markets_effective` | mercados independientes | apartado 2.6 |
| `excess_t_max`, `_2nd`, `_3rd` | las tres mejores t | la 1.ª, 2.ª y 3.ª mayor |
| `excess_t_q75` | cuartil superior | percentil 75 de las t |
| `excess_t_half` | la t que alcanza la mitad | la techo(k/2)-ésima mayor |
| `excess_blind_t_half` | lo mismo, ciega | ídem sobre `excess_blind_t` |
| `excess_t_median` | mediana de las t | la mediana corriente |
| `excess_t_min` | la peor t | la menor |

Las t ordenadas sirven para escribir cualquier regla del tipo «al menos k mercados por encima de x»: es «la k-ésima mayor ≥ x». No hay ningún umbral dentro del estudio.

**Ejemplo: C.** Sus once `excess_t`, de mayor a menor:

```
1,07   0,56   0,56   0,36   −0,16   −0,40   −0,51   −1,47   −2,84   −3,72   −7,90
```

`excess_t_max` = 1,07 (DJ30) · `_2nd` = 0,56 · `_3rd` = 0,56 · `_q75` = 0,46 · `_half` = `_median` = −0,40 (HK50) · `_min` = −7,90 (XCUUSD).

**Cómo leerlos** (las diez estrategias):

| hecho | mínimo | mediana | máximo |
|---|---|---|---|
| `excess_t_pooled` | −6,19 | −2,93 | −1,28 |
| `excess_blind_t_pooled` | −6,56 | −3,02 | −1,43 |
| `excess_t_stouffer` | −7,06 | −3,23 | −1,66 |
| `markets_effective` (9 con dato) | 9,15 | 9,72 | 10,06 |
| `excess_t_max` | −0,26 | 1,05 | 3,15 |
| `excess_t_2nd` | −0,77 | 0,69 | 1,32 |
| `excess_t_3rd` | −0,93 | 0,34 | 0,98 |
| `excess_t_q75` | −1,04 | 0,17 | 0,46 |
| `excess_t_half` | −1,69 | −1,04 | −0,23 |
| `excess_blind_t_half` | −1,70 | −0,52 | −0,20 |
| `excess_t_min` | −7,90 | −4,79 | −2,30 |

Un `excess_t_max` de 3,15 (lo tiene `3.9.284`) parece mucho, pero es el **máximo de once**: entre once t sin ventaja, la mayor supera 1,65 en cerca de cuatro de cada diez casos. Una t alta en un mercado suelto no es un hallazgo.

### 3.3 Frente al original

| hecho | qué mide |
|---|---|
| `main_excess_t`, `main_trade_t`, `main_pf_sqx`, `main_net_per_trade`, `main_sharpe_sqx` | las cinco medidas en el activo principal (su bloque del export: `oos1`) |
| `excess_t_vs_main_half` y sus cuatro hermanos | el cociente que alcanza la mitad de los mercados (apartado 2.8) |
| `excess_t_minus_main_half` | lo mismo sobre la diferencia de t |

**Cómo leerlos** (las diez estrategias):

| hecho | mínimo | mediana | máximo |
|---|---|---|---|
| `main_excess_t` | 0,16 | 0,62 | 2,05 |
| `main_trade_t` | 0,50 | 0,81 | 2,29 |
| `main_pf_sqx` | 1,11 | 1,28 | 1,93 |
| `main_net_per_trade` (USD) | 33,69 | 58,60 | 213,80 |
| `main_sharpe_sqx` | 0,25 | 0,40 | 1,12 |
| `excess_t_vs_main_half` | −10,39 | −1,14 | −0,11 |
| `trade_t_vs_main_half` | −2,52 | −0,43 | +0,09 |
| `net_per_trade_vs_main_half` | −1,61 | −0,31 | +0,05 |
| `sharpe_sqx_vs_main_half` | −1,55 | −0,26 | +0,06 |
| `pf_sqx_vs_main_half` | 0,48 | 0,74 | 0,80 |
| `excess_t_minus_main_half` | −2,80 | −1,63 | −0,94 |

`main_excess_t` es casi, pero no exactamente, el `drift_excess_t` del paso 8: en C coinciden (0,7016); en E es 2,052 aquí y 2,056 allí; en F, 0,163 y 0,150. La diferencia es pequeña y viene, con toda probabilidad, de la ventana sobre la que se mide la deriva (aquí, de la primera entrada a la última salida; no lo he comprobado en el código de la puerta).

### 3.4 Amplitud y recuentos

(`verdict/breadth.py:64` y `:87`, `many.py:78`)

| hecho | qué mide | cómo se calcula |
|---|---|---|
| `markets` | mercados valorados | los que tienen operaciones |
| `missing` | mercados ausentes | declarados sin operaciones, o que dieron error |
| `cleared`, `fraction`, `drop` | la amplitud | apartado 2.9 |
| `under_alpha` | mercados con p ≤ 0,05 | recuento sobre `p` |
| `paired_under_alpha` | mercados con `paired_p` ≤ 0,05 | recuento |
| `a_cleared` | mercados con `a_ci_lo` > 0 | recuento |
| `expectancy_positive` | mercados con esperanza > 0 | recuento, sin intervalo |
| `net_positive` | mercados que ganan dinero | recuento sobre el neto |
| `trades_total`, `trades_min` | operaciones en total y en el mercado más flaco | suma y mínimo |
| `net_total` | neto de todos los mercados (USD) | suma |
| `p_median`, `p_min`, `z_median` | resumen de las entradas al azar | mediana y mínimo entre mercados |
| `edge_r` | ventaja mediana | mediana de `edge_r` entre mercados |
| `median_pf`, `worst_pf`, `pf_cv` | PF mediano, el peor y su dispersión | sobre `pf`; `pf_cv` es la desviación típica |
| `warnings` | avisos acumulados | suma de los avisos de todos los mercados |

**Ejemplo: C.** `markets` 11 · `missing` 0 · `cleared` 2 · `fraction` 0,18 · `under_alpha` 2 (XAUUSD con p = 0,004 y USATEC con 0,044) · `paired_under_alpha` 1 · `a_cleared` 4 · `expectancy_positive` 5 · `net_positive` 4 (DJ30, USATEC, USDJPY, XAUUSD) · `trades_total` 4.253 · `trades_min` 189 (HK50) · `net_total` −117.963 · `p_median` 0,27 · `p_min` 0,004 · `z_median` 0,62 · `edge_r` 0,10 · `median_pf` 0,93 · `worst_pf` 0,35 (XCUUSD) · `pf_cv` 0,34 · `warnings` 27.

**Los 27 avisos de C**, que he sacado volviendo a correr sus once mercados: `bad_hold_fit` en los once (la distribución ajustada a las duraciones no las describe; sólo afecta a modelos de azar que el lote no usa), `no_drift` en nueve (el mercado no tiene una deriva distinguible de cero), `short_sample` en seis (el Sharpe observado necesita más operaciones de las que hay) y `fill_mismatch` en uno, el cobre. Un recuento de 27–35 avisos es lo normal aquí y no distingue estrategias.

**Cómo leerlos** (las diez estrategias):

| hecho | mínimo | mediana | máximo |
|---|---|---|---|
| `fraction` | 0 | 0,05 | 0,18 |
| `cleared` | 0 | 0,5 | 2 |
| `net_positive` (de 11) | 0 | 4 | 6 |
| `expectancy_positive` (de 11) | 0 | 5 | 8 |
| `under_alpha` | 0 | 1 | 2 |
| `a_cleared` | 0 | 0,5 | 4 |
| `trades_total` | 1.813 | 3.992 | 5.785 |
| `trades_min` | 15 | 173 | 312 |
| `net_total` (USD) | −448.581 | −105.446 | −28.934 |
| `z_median` | −0,62 | +0,52 | +0,75 |
| `p_median` | 0,23 | 0,30 | 0,73 |
| `median_pf` | 0,80 | 0,96 | 1,06 |
| `worst_pf` | 0,35 | 0,55 | 0,70 |

Con once mercados y la línea en 0,05, por puro azar se espera 0,55 mercados con p ≤ 0,05. Un `under_alpha` de 1 o 2 es lo que da el azar.

### 3.5 Lo mismo, por grupo

Ocho hechos se repiten dentro de cada grupo, con el prefijo `family_` o `structural_`: `markets`, `net_positive`, `excess_t_pooled`, `excess_t_half`, `excess_t_vs_main_half`, `excess_blind_t_pooled`, `excess_blind_t_half` y `net_per_trade_vs_main_half`. Se calculan igual, sólo con los mercados del grupo (`many.py:88`).

| hecho | C | E | F |
|---|---|---|---|
| `family_markets` | 8 | 8 | 8 |
| `family_net_positive` | 3 | 3 | 0 |
| `family_excess_t_pooled` | −1,70 | −0,59 | −3,84 |
| `family_excess_t_vs_main_half` | −0,57 | −0,11 | −9,99 |
| `structural_markets` | 3 | 3 | 3 |
| `structural_net_positive` | 1 | 1 | 0 |
| `structural_excess_t_pooled` | −3,42 | −1,41 | −5,12 |
| `structural_excess_t_vs_main_half` | −0,22 | +0,01 | −19,28 |

**Cómo leerlos.** El grupo estructural es la prueba difícil; el de familia, la fácil. Lo ideal es que el resultado no dependa sólo de la familia. En las diez, la t conjunta de familia va de −3,84 a +0,16 (mediana −1,27) y la estructural de −5,36 a −1,09 (mediana −4,13). La estructural sale mucho peor, pero con sólo tres mercados y siendo uno de ellos el cobre, esa diferencia mide sobre todo el coste del cobre.

Con 8 mercados de familia, «la mitad» es el 4.º mayor; con 3 estructurales, el 2.º.

---

## 4. El criterio cargado y por qué

### 4.1 Tal como está hoy en disco

```
"10":
  cut: Retest Markets - Family
  segment: oos1
  rules:
    # Council: half the markets at >=0.5x the original AND pooled t>=2.33 PASS;
    #          pooled t<1.0 FAIL. Stouffer is never a criterion.
    - {fact: crossmarket.verdict_csv.excess_t_vs_main_half, pass: ">= 0.5", limbo: "> 0", missing: limbo}
    - {fact: crossmarket.verdict_csv.excess_t_pooled, pass: ">= 2.33", limbo: ">= 1.0"}
```

`segment: oos1` es la etiqueta del libro de registro para este corte, no la ventana de los datos: el estudio lee `build..oos1` de cada mercado.

No hay variantes por timeframe ni por clase de activo (`by:`): la regla es la misma para forex, índices y metales.

### 4.2 Regla 1 — La mitad de los mercados a 0,5 veces el original

| Pasa | Limbo | Falla |
|---|---|---|
| ≥ 0,5 | > 0 y < 0,5, o sin dato | ≤ 0 |

**Por qué.**

- **Tasa medida:** «la mitad a 0,5 veces» la pasa entre el 0,4 y el 6 % de las estrategias sin ventaja que tuvieron suerte en el original; «a 1,0 veces», el 0 %.
- **Libro:** es la formulación de grupo que pide Katz (aprobar o suspender la cesta entera).
- **El 0,5:** es la expectativa habitual de los libros para fuera de muestra: la mitad del beneficio (Hill-Pruitt-Hill), un Sharpe por encima de la mitad del de la prueba (Chan), en torno al 50 % (Kaufman).
- **El Falla en ≤ 0:** la línea del comentario del fichero no lo menciona («half the markets at ≥0.5x AND pooled t≥2.33 PASS; pooled t<1.0 FAIL»). En la primera ronda del Council, un miembro propuso expresamente que esta regla **no diera Falla** nunca («amplitud por debajo de 0,5: Limbo; ninguno Falla»). Lo que hay en disco es más estricto que eso. No he encontrado de dónde sale el corte en cero: **convención**.

### 4.3 Regla 2 — La t conjunta

| Pasa | Limbo | Falla |
|---|---|---|
| ≥ 2,33 | de 1,0 a 2,33, o sin dato | < 1,0 |

**Por qué.**

- **El 2,33:** p nominal del 1 % a una cola. Con la desviación medida de 0,95, la pasa el **0,7 %** de las estrategias que empatan (Munger); con 0,83, el 0,25 %.
- **El 1,0:** propuesta de un miembro (Feynman: «Pasa ≥ 2,33, Falla < 1,0»). No tiene una tasa propia medida. Con la fórmula: una estrategia que empata queda por debajo de 1,0 el 85 % de las veces. **Convención.**
- **Stouffer, fuera:** pasa el 5–24 % de las que empatan (cifra de la calibración del Council, hoy no reproducible: sus ficheros ya no están en disco) (apartado 2.7).
- **La potencia** (cálculo del Council, con la fórmula `t esperada = s × transferencia × √(k efectivo × n)`, para forex con 4,4 mercados efectivos y 250 operaciones por mercado):

| ventaja por operación `s` | transferencia completa | media transferencia |
|---|---|---|
| 0,15 (optimista) | 0,15 × √1.100 = **5,0** | **2,5** |
| 0,04 (modesta) | 0,04 × √1.100 = **1,3** | **0,7** |

Y lo que eso supone frente a las dos líneas (fórmula, con desviación 0,95):

| t esperada | probabilidad de Pasa (≥ 2,33) | probabilidad de Falla (< 1,0) |
|---|---|---|
| 5,0 | 99,8 % | 0 % |
| 2,5 | 57 % | 6 % |
| 1,3 | 14 % | 38 % |
| 0,7 | 4 % | 62 % |

**Léelo despacio:** una ventaja real pero modesta (s = 0,04), incluso transfiriéndose **entera** a los demás mercados, se descarta el 38 % de las veces, y con media transferencia, el 62 %. La línea de Falla en 1,0 no es barata.

Aquí `s` es la ventaja **neta** de costes. Si la entiendes como bruta, réstale 0,04–0,09 (lo que vale el coste en desviaciones por operación): la probabilidad de Pasa de las filas modestas cae a casi cero.

**Lo que el Council propuso y no está en disco.**

- Munger pidió para los **índices** una t conjunta ≥ 2,9 y que la prueba sólo anotase, por sus 1,6–1,9 mercados efectivos. No está cargado.
- Feynman propuso la línea sobre la t conjunta **ciega**. La regla lee la versión sin corregir.

### 4.4 Cómo sería el resultado ideal

Una estrategia que:

- tiene una t conjunta ≥ 2,33 **después de pagar los costes de todos los mercados**;
- llega a la mitad de la t del original en al menos la mitad de ellos;
- gana en casi todos: como mucho 1 o 2 de 9 en negativo (Katz), ninguno si la lista es de índices muy correlacionados;
- y no vive sólo de la familia: la t conjunta estructural también es positiva.

En números de esta lista de once mercados: `net_positive` ≥ 9, `fraction` ≥ 0,5, `excess_t_pooled` ≥ 2,33, `structural_excess_t_pooled` > 0, `excess_t_vs_main_half` ≥ 0,5. Estos tres umbrales (`net_positive`, `fraction` y `structural_excess_t_pooled`) no son alcanzables a la vez por una estrategia que apenas llega a 2,33 de t conjunta: con unas 350 operaciones por mercado y una ventaja de 0,046 desviaciones, su t por mercado esperada es 0,046 × √350 = 0,86, y despeja el intervalo (hace falta t > 1,65) con probabilidad Φ(0,86 − 1,65) ≈ 21 %, es decir, unos 2,4 mercados de 11, no 6. Úsalos como descripción cualitativa, no como objetivo numérico.

**El techo honesto** (cuenta ilustrativa, con la fórmula; no es una medida). En esta configuración hay unas 350 operaciones por mercado y, con la correlación que muestran estas estrategias, unos 7 u 8 mercados que cuentan para la suma: del orden de 2.600 operaciones efectivas. Para una t conjunta de 2,33 hace falta una ventaja **neta** por operación de `2,33 / √2.600 = 0,046` desviaciones. El coste ya se lleva entre 0,04 y 0,09 desviaciones por operación en diez de los mercados. Luego la ventaja **bruta** necesaria en mercados para los que la estrategia no se hizo es de 0,09 a 0,13 por operación. La evidencia del Council cifra la dispersión real de la ventaja entre estrategias, medida de `oos1` a `oos2`, en unos 0,02. Conclusión: con costes y operaciones tan cortas, **Pasa es casi inalcanzable para una estrategia media** en esta lista: con la dispersión medida (0,02) una estrategia media no llega; una que esté a 5 o 6 desviaciones de la media sí, pero no sabemos si existen, no está medido. El umbral exige ventajas brutas de 0,09–0,13 por operación, varias veces lo típico, y no porque la línea sea caprichosa sino porque pide, fuera de casa, varias veces la ventaja que se ve en casa.

### 4.5 Si mueves este umbral

Con la población real, la cuenta es breve y hay que decirla tal cual: **cada una de las dos reglas, sola, falla a las diez.**

| regla, sola | Pasa | Limbo | Falla |
|---|---|---|---|
| `excess_t_vs_main_half` (≥ 0,5 / > 0) | 0 | 0 | 10 |
| `excess_t_pooled` (≥ 2,33 / ≥ 1,0) | 0 | 0 | 10 |

Cuántas quedarían **por encima** de otras líneas de Falla:

| hecho | ≥ 1,0 | ≥ 0 | ≥ −1,0 | ≥ −2,0 |
|---|---|---|---|---|
| `excess_t_pooled` | 0 | 0 | 0 | 3 |
| `excess_blind_t_pooled` | 0 | 0 | 0 | 3 |
| `family_excess_t_pooled` | 0 | 1 | 5 | 8 |
| `structural_excess_t_pooled` | 0 | 0 | 0 | 4 |
| t conjunta sin el cobre (no es un hecho) | 0 | 0 | 4 | 7 |

| hecho | ≥ 0,5 | > 0 |
|---|---|---|
| `excess_t_vs_main_half` | 0 | 0 |
| `net_per_trade_vs_main_half` | 0 | 2 |
| `trade_t_vs_main_half` | 0 | 2 |
| `sharpe_sqx_vs_main_half` | 0 | 2 |
| `structural_excess_t_vs_main_half` | 0 | 2 |
| `pf_sqx_vs_main_half` | 9 | 10 |

- **Aflojar la t conjunta** hasta donde tendría sentido (Falla sólo por debajo de 0) no salva a ninguna de estas diez. Lo que se gana es no descartar ventajas modestas reales (el 38–62 % de arriba); lo que cuesta, con esta población, es cero estrategias.
- **Cambiar a la variante ciega** no mueve ni una.
- **Leer la regla 1 sobre USD por operación en vez de sobre la t** dejaría dos en Limbo (`3.9.284` y `4.13.338`): son las dos en las que al menos seis mercados ganan dinero. Seguirían fallando por la regla 2.
- **Mirar sólo la familia** dejaría una por encima de cero (`3.9.284`, con +0,16).

Lo que **no** se puede saber con estos datos: cuántas estrategias buenas se pierden o se salvan con cada línea. Para eso hace falta una población que haya pasado el paso 8, y otra sin ventaja que recorra la cadena.

---

## 5. Lo que no cuadra o no está medido

### 5.1 La regla lee la variante que el propio código desaconseja

`simulate/excess.py:212` dice de `excess_blind_t_pooled` y `excess_blind_t_half`: «las que hay que usar para poner una línea». La ficha del sesgo de la deriva dice que la versión sin corregir no pone a largos y cortos en la misma escala. `criteria.yaml` lee `excess_t_pooled` y `excess_t_vs_main_half`, las dos sin corregir.

### 5.2 Pero la variante ciega está estropeada en UK100 y DAX40

El peso de la operación ciega es `1 / ATR`. Si el ATR de una barra es casi cero, su peso es enorme. En los datos de M30 de UK100 y DAX40 hay un tramo, entre el 24-12-2013 y febrero de 2014, con el ATR más de 50 veces por debajo de su mediana (mínimo 0,0036 puntos frente a medianas de 11,8 y 24,6): 234 barras en UK100 y 362 en DAX40. Son barras casi planas, un defecto del histórico.

| mercado | peso que se lleva el 0,1 % de barras | W(10) | μ × 10 |
|---|---|---|---|
| UK100 | **44 %** | 3,05 puntos | 0,18 puntos |
| DAX40 | **34 %** | −0,16 puntos | 0,78 puntos |
| USA500 | 0,8 % | 0,24 puntos | 0,31 puntos |
| XAUUSD | 0,8 % | 0,059 puntos | 0,054 puntos |

En UK100, la «operación ciega» de diez barras gana 17 veces más que diez barras medias: no describe al mercado, describe lo que pasó después de un puñado de barras muertas. El efecto en las t:

| | `excess_t` UK100 | `excess_blind_t` UK100 | `excess_t` DAX40 | `excess_blind_t` DAX40 |
|---|---|---|---|---|
| C | −3,72 | −5,24 | −0,51 | −0,20 |
| E | −1,30 | −4,93 | −0,18 | +0,83 |
| F | −1,63 | −5,58 | −0,52 | +0,90 |

Los otros nueve mercados no tienen el problema. Hasta que el peso tenga un suelo (o esas barras se excluyan), **cambiar la regla a la variante ciega no es una mejora**. Y es un hallazgo para el estudio de calidad del feed: esas barras afectan a cualquier cálculo con ATR.

### 5.3 La t conjunta mide el neto; la tasa del 0,7 % es de estrategias que empatan

Explicado en 2.11. No es una contradicción, pero las dos cifras se han citado juntas como si hablaran de lo mismo. Una estrategia sin ventaja que paga costes no pasa nunca (0–0,6 %); una que empata después de costes, el 0,7 %. La línea de Falla en 1,0 no tiene tasa medida en ninguno de los dos sentidos.

### 5.4 El cobre

Coste recuperado de 192 USD por operación (0,22 desviaciones), aviso `fill_mismatch`, PF mediano 0,53. Es uno de sólo tres mercados estructurales. Ese coste es compatible con una ficha de costes errónea o con un desajuste de precios (192 USD frente a un resultado absoluto típico de unos 340 USD): hasta comprobarlo no se puede decir que el suspenso sea de la estrategia. La lista de mercados es tuya y se fija **antes** de mirar resultados; lo que se plantea aquí no es quitarlo porque fue mal, sino revisar **antes de la próxima corrida** si su ficha de costes y su sitio en la lista de M30 son los que quieres.

### 5.5 El cociente con el original compara t de longitudes distintas

El original son 4 años de `oos1` (58 a 187 operaciones por estrategia); cada mercado, 10 a 15 años (165 a 526 de media). Una t crece con √n. Con la misma calidad por operación, un mercado con el triple de operaciones tiene una t √3 = 1,7 veces mayor. Así que «0,5 veces la t del original» equivale, en calidad por operación, a unas **0,3 veces**. La regla es más laxa de lo que su nombre dice, y lo es en una cantidad que cambia de un activo a otro. `net_per_trade_vs_main_half` y `sharpe_sqx_vs_main_half` no tienen este problema. No sé si la tasa del 0,4–6 % se midió con estas mismas ventanas: los ficheros de aquella calibración ya no están (5.11).

### 5.6 El cociente estalla cuando el original es casi cero, y desaparece cuando es negativo

F: −10,39 con un original de 0,163. En siete de las diez corridas guardadas la t mediana del original es negativa, y en cuatro de ellas el hecho mediano sale vacío, es decir, Limbo. Una estrategia cuyo original **pierde** en `oos1` no puede fallar por la regla 1.

Y al revés: con un original casi cero la regla se cumple sola. Un original de t = 0,05 y un mercado de t = 0,03 dan un cociente de 0,6, que Pasa. Conviene exigir además un mínimo de `main_excess_t`, o leer la diferencia en vez del cociente.

### 5.7 El Falla de la regla 1 no está en lo que el fichero atribuye al Council

Apartado 4.2.

### 5.8 Los dos profit factors

`pf` (rentabilidades de barra, cada operación pesa igual, un coste único por mercado) y `pf_sqx` (dólares de SQX) discrepan a veces de lado: C en DAX40, 1,17 frente a 0,94. La amplitud (`fraction`, `cleared`), `median_pf` y `worst_pf` usan la primera familia; `net_positive` y los `…_vs_main_half`, la segunda. Por eso C tiene `expectancy_positive` = 5 y `net_positive` = 4.

### 5.9 Hechos duplicados

- `sharpe_total` y `sharpe_sqx` son el mismo número en las 110 parejas.
- `excess_t_half` y `excess_t_median` son iguales siempre que el número de mercados es impar (aquí, 11).

### 5.10 El README dice que el estudio no emite veredicto, y lo emite

`README.md` («It issues no verdict»), `config.yaml` («no verdict») y, a la vez, `verdict.csv` con MANTENER / DESCARTAR, `breadth.judge` y el texto «es la única criba». En la práctica el piloto automático ignora ese veredicto y corta por `criteria.yaml`.

### 5.11 La calibración no se puede volver a comprobar

Las cifras 0,4–6 %, 5–24 %, 0,83–0,95 y 4,1–4,7 / 1,6–1,9 / 3,0–3,6 vienen de `AlgoData/scratch/calib_step10/`. Esa carpeta **ya no está en disco**. Quedan citadas en `knowhow/research/crossmarket-effective-markets.md` y en el paquete de evidencia del Council. He podido reproducir el 1,6–1,9 (sale 1,77) y la aritmética del 0,7 %; el resto, no.

### 5.12 `markets_effective`

Conciliado en 2.6. Quedan dos defectos: usa correlaciones al cuadrado (más optimista que la cuenta que rige la t conjunta: 9,2–10,1 frente a 6,0–8,1), y un solo mercado con pocas operaciones lo deja vacío.

### 5.13 El paso 8 va a cambiar el término de deriva, y este paso lo copia

La especificación nueva del paso 8 cambia su R3: deriva por ventana de calendario, corrección del sesgo por tamaño y error estándar con sesgo y curtosis. `simulate/excess.py` copia a propósito el término de la puerta («cambiar los dos juntos»). Cuando cambie el paso 8, `excess_t` y `main_excess_t` de aquí tendrán que cambiar con él, o el cociente comparará dos definiciones.

### 5.14 Lo que no está medido

- La tasa de falsos positivos de **las dos reglas juntas** sobre una población sin ventaja que haya recorrido la cadena.
- La potencia con una ventaja plantada.
- El paso 10 sobre estrategias que **pasan** el paso 8: no existe ninguna corrida.
- El sesgo por lado del término de deriva para NIKKEI225 largo.
- El efecto de que los primeros cuatro años de la serie semanal lleven sólo tres mercados.
- Si las reglas internas de las estrategias están en unidades que viajan (apartado 2.2).
- La regla por clase de activo: la evidencia da números efectivos muy distintos (forex 4,1–4,7; índices 1,6–1,9; metales y crudos 3,0–3,6) y la regla es una sola.

### 5.15 Dónde este documento corrige al informe anterior

- «No he podido conciliar» el número efectivo: **conciliado** (2.6).
- «Sugiere que la t conjunta no está centrada en cero (costes, sesgo de la deriva)»: **son los costes**, entre 2,1 y 6,3 unidades de t; el sesgo de la deriva es menor y de signo contrario (2.11).
- El informe no decía que las diez estrategias fallarían hoy el paso 8, ni que el original cubre sólo `oos1`.

---

## 6. Cierre

### 6.1 Las reglas, en una tabla

| regla | hecho | Pasa | Limbo | Falla |
|---|---|---|---|---|
| la mitad a 0,5× | `excess_t_vs_main_half` | ≥ 0,5 | > 0, o sin dato | ≤ 0 |
| t conjunta | `excess_t_pooled` | ≥ 2,33 | 1,0 – 2,33 | < 1,0 |

| regla | motivo de la línea | tasa medida |
|---|---|---|
| la mitad a 0,5× | Katz (prueba de grupo) y la mitad fuera de muestra (Chan, Kaufman) | 0,4–6 % de las sin ventaja con suerte (cifra de la calibración del Council, hoy no reproducible: sus ficheros ya no están en disco) |
| t conjunta ≥ 2,33 | p del 1 % a una cola | 0,7 % de las que empatan; 0–0,6 % de las que pagan costes |
| t conjunta < 1,0 | propuesta de un miembro | no medida |
| Falla en ≤ 0 de la primera | no localizado | no medida |

### 6.2 El resultado sobre la población real

Calculado en memoria con `pipeline.autopilot.criteria` sobre los hechos de la corrida:

| | Pasa | Limbo | Falla |
|---|---|---|---|
| las dos reglas juntas | 0 | 0 | **10** |

| estrategia | t conjunta | mitad a 0,5× | resultado |
|---|---|---|---|
| `3.11.426` (E) | −1,28 | −0,11 | Falla (las dos) |
| `13.3.390` | −1,57 | −1,94 | Falla (las dos) |
| `4.13.338` | −1,66 | −0,42 | Falla (las dos) |
| `10.11.484` | −2,12 | −0,66 | Falla (las dos) |
| `3.9.284` | −2,81 | −1,62 | Falla (las dos) |
| `19.2.363` | −3,05 | −0,53 | Falla (las dos) |
| `14.3.479` (C) | −3,47 | −0,57 | Falla (las dos) |
| `18.5.355` | −3,50 | −5,57 | Falla (las dos) |
| `16.5.352` | −3,85 | −8,21 | Falla (las dos) |
| `15.9.352` (F) | −6,19 | −10,39 | Falla (las dos) |

Es el resultado correcto para estas diez: ninguna había demostrado nada en el NIKKEI (las diez fallan el paso 8 de hoy) y ninguna gana fuera. El paso hace lo que tiene que hacer con estrategias sin ventaja. Lo que no sabemos es qué hace con una buena.

### 6.3 Las decisiones que te quedan

Cada una con lo que cuesta y lo que gana. Donde pone «0 de 10», es que en esta población la decisión no cambia ningún veredicto; el coste real sólo se verá con una población que pase el paso 8.

**1. ¿La t conjunta se queda sobre el neto?**
Hoy sí. *A favor:* lo que se opera es el neto. *En contra:* Pasa pide varias veces la ventaja de casa (4.4) y las tasas medidas no hablan de eso. *Alternativa:* dejarla sobre el neto y mover sólo las líneas. *Coste:* 0 de 10 con cualquier línea de Falla ≥ 0. No recomiendo juzgar sobre el bruto: sirve para leer (2.11), no para decidir.

**2. ¿Dónde va la línea de Falla de la t conjunta?**
En 1,0 se pierde el 38 % de las ventajas modestas con transferencia completa y el 62 % con media (fórmula). En 0 se pierde bastante menos y siguen cayendo las que pierden dinero en conjunto. *Coste en esta población:* 0 de 10 en los dos casos. *Ganancia:* no medible aquí.

**3. ¿La regla 1 puede dar Falla?**
Hoy sí, en ≤ 0. Un miembro del Council pidió que no. Si se queda, conviene decidir además **sobre qué medida**: la t (depende de cuántas operaciones tiene cada mercado, 5.5) o USD por operación / Sharpe (no depende). *Coste de pasar a USD por operación:* dos estrategias pasarían de Falla a Limbo en esta regla (seguirían fallando por la otra).

**4. ¿Qué se hace cuando el original es negativo o casi cero?**
Hoy: negativo → sin dato → Limbo; casi cero → cocientes sin sentido. *Alternativa:* leer `excess_t_minus_main_half` (la diferencia) en esos casos. No medido.

**5. ¿Variante ciega o sin corregir?**
El código recomienda la ciega; la ciega está estropeada en dos mercados (5.2). *Orden lógico:* arreglar el peso, medir de nuevo, y entonces decidir. *Coste hoy:* 0 de 10 de diferencia.

**6. ¿El cobre a ese coste, en M30?**
Pone entre 0,6 y 2,2 unidades de t en contra a cada estrategia. Es tu lista. La decisión es **previa** a la próxima corrida, no una corrección de esta. *Sin él:* 0 de 10 pasarían a Limbo (la mejor quedaría en −0,42).

**7. ¿Una línea distinta para índices?**
Munger: ≥ 2,9 y sólo anotar. Se apoya en 1,6–1,9 mercados efectivos (peor caso). Con la correlación real de estas estrategias, los once mercados valen por 6–10. *Coste:* 0 de 10 hoy. Depende de si las estrategias que lleguen son de operaciones cortas, como estas, o de las que aguantan días.

**8. ¿Congelar?**
No todavía. Faltan dos poblaciones: una sin ventaja que recorra la cadena (para la tasa conjunta de las dos reglas) y una que pase el paso 8 (para saber qué le hace este paso a una estrategia con mérito). Hasta entonces, las diez de aquí sólo prueban que el paso descarta lo que no vale.

### 6.4 El límite que no cambia

Este paso es la única prueba de la cadena, antes de `oos2`, que puede decir algo nuevo de una estrategia, y la única que gana potencia. Pero mide una cosa concreta: si la lógica **gana dinero, costes incluidos, en mercados para los que no se hizo**. Una estrategia puede ser buena y no pasarlo —un especialista de su mercado—, y esa es una decisión tuya, no de la estadística: si quieres sólo lógicas que viajan, el paso es una puerta; si aceptas especialistas, es una anotación.
