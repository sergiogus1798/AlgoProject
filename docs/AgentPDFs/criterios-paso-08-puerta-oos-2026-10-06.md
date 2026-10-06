# Paso 8 — La puerta OOS en Python: cada criterio, con sus matemáticas y un ejemplo numérico

**Fecha:** 2026-10-06 · **Para:** el dueño, que va a fijar él mismo los criterios · **Alcance:** sólo el paso 8. Es el primero de la serie «un documento por paso»; amplía la sección «Paso 8» de `criterios-pasos-6-a-19-explicados-2026-10-06` y no la contradice salvo donde se dice expresamente.

**Qué es:** un documento para aprender y consultar. Primero enseña, desde cero, la estadística que usa el paso 8. Después recorre **cada regla** del paso tal como está hoy en `pipeline/autopilot/criteria.yaml`, y cada estudio que corre en el paso aunque sólo anote. De cada cosa dice qué mide, cómo se calcula de verdad (sacado del código), un ejemplo con una estrategia real rehecho a mano, el criterio cargado y su porqué, cómo sería un resultado ideal y qué cuesta mover el umbral.

**Todos los números de los ejemplos están calculados**, no estimados: salen de los hechos guardados de la corrida `Trade_NIKKEI225_M30_volatilidadL` del 2026-10-04 y de sus listas de operaciones. Donde un dato de entrada ya no existe en disco, se dice.

---

## 1. Qué es el paso 8 y cómo decide

### 1.1 Qué hace

El paso 6 construye estrategias en SQX mirando sólo el tramo `build`. El paso 7 las vuelve a probar en un tramo que el generador no vio, `oos1`. El **paso 8** es Python: lee los dos databanks (el del build y el del retest), calcula unas decenas de números por estrategia y aplica las reglas de `criteria.yaml`. Lo que no pasa se borra del databank `OOS`, que es el que lee la siguiente tarea de SQX (el paso 9).

Los tramos, según `assets/symbols/`:

| activo | `build` | `oos1` (lo que juzga el paso 8) | `oos2` |
|---|---|---|---|
| XAUUSD y forex | 2008–2017 (10 años) | 2018–2022 (5 años) | 2023–sept. 2026 |
| NIKKEI225 | 19-09-2011–2019 (8,28 años) | 2020–2023 (4 años) | 2024–sept. 2026 |

El paso 8 **no toca `oos2`**. Las cifras de «lo que pasó después en `oos2`» que verás en este documento vienen de la calibración del 2026-10-02/04, que tú autorizaste sólo para eso.

### 1.2 Los tres estados

| estado | qué significa | qué hace el workflow |
|---|---|---|
| **PASA** | cumple la línea exigente de todas las reglas | sigue al paso 9 |
| **LIMBO** | ni prueba ni condena | sigue al paso 9, **marcada** |
| **NO PASA** | alguna regla la da por mala | se **borra** del databank `OOS` |

### 1.3 Cómo se combinan las reglas: manda la peor

Cada regla lee **un dato** de la estrategia (un «hecho») y da PASA, LIMBO o NO PASA. El resultado de la estrategia es el de **su peor regla**. Basta una sola regla en NO PASA para sacarla; basta una en LIMBO para que no pueda ser PASA.

Ejemplo real, `Strategy 14.3.479`: de las 16 reglas pasa 11, cuatro le dan LIMBO (opera 22,8 veces al año en IS, tiene 98 operaciones en oos1, concentra el 64 % del beneficio en un trimestre y su peor caída cuesta 4,3 años de beneficio) y una le da NO PASA (su t es 0,70, por debajo de 1,65). Resultado: **NO PASA**.

*Código:* `pipeline/autopilot/criteria.py:99-120` (la función `outcomes`: «a strategy's outcome is its worst rule»).

### 1.4 La gramática de una regla, con ejemplos del fichero real

**Una regla normal** tiene una línea de PASA y, si quiere, una de LIMBO. Lo que no llega a ninguna es NO PASA:

```
- {fact: gate.scorecard.oos_trades_per_year, pass: ">= 15", limbo: ">= 10"}
```

Con 24,5 operaciones al año: PASA. Con 12: LIMBO. Con 8: NO PASA.

**`by:`** cambia las líneas según lo que sea el proyecto (su timeframe, su símbolo, o `forex` / `no_forex`). Se aplica la **primera** entrada que encaje; si ninguna encaja, la regla queda como está escrita:

```
- {fact: gate.scorecard.drift_excess_t, pass: ">= 2.33", limbo: ">= 1.65",
   by: {H4: {pass: ">= 2.5", limbo: ">= 1.65"}, H1: {pass: ">= 1000", limbo: ">= 1.65"}}}
```

Un proyecto M30 (como el del ejemplo) usa 2,33 y 1,65. Uno H4 usa 2,5. Uno H1 tiene la línea de PASA en 1.000, que nadie alcanza: es la manera de escribir «en H1 esta regla, como mucho, da LIMBO».

**`missing:`** dice adónde va una estrategia a la que le **falta** el dato. Si la regla no dice nada, un dato que falta es LIMBO:

```
- {fact: gate.scorecard.presencia_passed, pass: ">= 1", missing: fail}
```

Aquí, sin dato es NO PASA. En cambio la regla de `forma_value` no dice nada, y a las 6.021 estrategias de la corrida de ejemplo que no tienen ese número les da LIMBO.

**`else: limbo`** convierte el «no cumple» en LIMBO en vez de NO PASA. Es una regla que nunca descarta:

```
- {fact: spread.verdict_csv.operaciones_oos, pass: ">= 100", else: limbo}
```

Con 98 operaciones: LIMBO, nunca NO PASA. El fichero consigue lo mismo de otra forma en varias reglas, con un LIMBO imposible de incumplir (`limbo: "<= 1000"`).

*Código:* `pipeline/autopilot/criteria.py:19-41` (una regla), `:44-64` (`by`), `:92-96` (dato que falta).

### 1.5 Dos cosas que se llaman parecido

- **La cascada propia de la puerta** (`studies/screening/gate/config.yaml`): ocho cribas en orden, con umbrales laxos a propósito (tu decisión del 2026-09-23). Da su propio veredicto, que el piloto automático **no usa**.
- **Las reglas de `criteria.yaml`**, que leen los números que la puerta deja escritos (`gate.scorecard.*`) y son las que cortan.

Esto importa por una razón práctica: en la cascada, una estrategia que muere en una criba no entra en las siguientes, así que **los números de las cribas posteriores no existen para ella**. En la corrida de ejemplo, de 10.000 estrategias llegan vivas a la criba `degradacion` 5.946 y a la criba `forma` 3.979. A las demás les falta ese dato, y la regla correspondiente les da LIMBO (no NO PASA). En cambio las catorce columnas «medidas» (`drift_excess_t`, operaciones por año, riesgo flotante) se calculan para **todas**.

### 1.6 Tres avisos antes de leer números

1. **El modo de desarrollo está encendido** (`dev: on: true`, `sample: 3`, `at: ["8"]`). Mientras lo esté, el piloto automático no se queda con todas las que no fallan: **sortea 3** entre ellas y borra el resto. En la corrida de ejemplo el sorteo era de 10. Sirve para probar el workflow, no para seleccionar.
2. **En la corrida de ejemplo, 1.557 de las 10.000 estrategias fueron a NO PASA por un problema de contabilidad, no por sus números.** La puerta guarda sus hechos bajo la identidad que la estrategia tenía en el build; el juez busca los hechos por la identidad del fichero del databank `OOS`; en el 15,6 % de las estrategias las dos identidades no coinciden, el juez no encuentra el dato `presencia_passed` y la regla R1 (`missing: fail`) las descarta. El detalle está en el apartado 3.1. No es un umbral que decidir: es un fallo que arreglar antes de fiarse del recuento.
3. **La regla del «edge por coste» no mide lo que su comentario dice** en este activo. Un `edge_mean` de 2 no significa «aguanta el doble de coste»: por cómo está construida la cuenta, significa «gana por operación un 30 % del spread declarado». El detalle está en el apartado 3.10.

### 1.7 Las tres estrategias que nos acompañan

Las tres son de la misma corrida (NIKKEI225, M30, largas). Las llamaremos A, B y C.

| | **A** | **B** | **C** |
|---|---|---|---|
| nombre | `Strategy 4.9.301` | `Strategy 16.11.437` | `Strategy 14.3.479` |
| resultado con las reglas de hoy | **PASA** | **LIMBO** | **NO PASA** |
| por qué | pasa las 16 | t = 2,15 (entre 1,65 y 2,33) | t = 0,70 (< 1,65) |
| operaciones en oos1 | 196 | 193 | 98 |
| neto en oos1 (USD) | 38.465 | 31.862 | 4.690 |

A es una de las dos únicas que pasan todas las reglas. B es un LIMBO «limpio»: sólo la retiene la t. C es el caso más corriente de NO PASA: ganó dinero en oos1, pero no lo bastante como para distinguirlo del azar.

Una cuarta hace de invitada en dos sitios: **D**, `Strategy 8.4.275`, la de mejor t de toda la población (3,14), que es NO PASA porque opera muy poco.

**Qué datos de entrada siguen en disco.** Las operaciones de las 10.000 estrategias, una a una, están guardadas (las dejó el estudio del spread). Con ellas se rehacen exactamente la t, la t descontada la deriva, las operaciones por año, los netos y el edge por coste de A, B y C. La curva diaria de equity y el MAE de las operaciones de oos1, en cambio, sólo se conservan para las diez estrategias que salieron del sorteo de aquella corrida; C está entre ellas, A y B no. Por eso los cinco datos que dependen de la curva diaria o del MAE se rehacen paso a paso **con C**, y de A y B se enseña el valor guardado.

---

## 2. Fundamentos: la estadística que usa el paso 8

Este capítulo va en orden; cada apartado usa el anterior. Los ejemplos pequeños se pueden rehacer con una calculadora.

Usaremos una estrategia de juguete con **diez operaciones**, en dólares:

```
+300  −100  +200  −200  +400  −150  +250  −50  +350  0
```

### 2.1 Media y desviación típica

**Fórmulas.**

```
media = (x1 + x2 + … + xn) / n

desv  = √( suma de (xi − media)²  /  (n − 1) )
```

`xi` es el resultado de la operación número i; `n` es el número de operaciones; `desv` es la desviación típica.

**Intuición.** La media dice cuánto gana una operación «normal». La desviación típica dice cuánto se aparta de esa media una operación cualquiera, hacia arriba o hacia abajo. Una estrategia con media 100 y desviación 20 es un reloj; con media 100 y desviación 2.000 es una lotería que casualmente salió bien. Se divide entre `n − 1` y no entre `n` porque la media también se ha sacado de esos mismos datos, y eso gasta una observación.

**Ejemplo.** Suma de las diez: 1.000. Media = 1.000 / 10 = **100**.

Distancias a la media: +200, −200, +100, −300, +300, −250, +150, −150, +250, −100. Sus cuadrados suman 450.000.

```
desv = √(450.000 / 9) = √50.000 = 223,6
```

En la estrategia A, sobre sus 196 operaciones de oos1: media = 196,25 USD, desv = 951,32 USD. La desviación es casi cinco veces la media: lo normal en trading.

### 2.2 R: el resultado en unidades de riesgo

**Fórmula.**

```
resultado en R = resultado en dinero / 1R
```

`1R` es el riesgo por operación que fija la doctrina del proyecto: **1.000 USD** (`assets/_build.yaml`, `money_management.params.Amount`).

**Intuición.** Medir en R permite comparar estrategias y activos sin pensar en el tamaño de la cuenta. Si arriesgas el 1 % de la cuenta por R, «−5R en un día» es perder el 5 %: el límite diario típico de una cuenta de fondeo. Un aviso: aquí R es **nominal**. La doctrina no lleva stop, así que una operación puede perder más de 1R; de hecho eso es justo lo que miden dos reglas del paso 8.

**Ejemplo.** La media de A, 196,25 USD, son 0,196R por operación. Su peor día, −2.213 USD, son −2,21R.

### 2.3 Error estándar: por qué más operaciones dan más certeza

**Fórmula.**

```
error estándar = desv / √n
```

**Intuición.** La media que has medido no es «la» media verdadera de la estrategia: es la de las operaciones que le tocaron. Si repitieras la historia saldría otra. El error estándar dice cuánto bailaría esa media de una repetición a otra. Baila menos cuantas más operaciones hay, pero **con la raíz**: para tener la mitad de baile hacen falta cuatro veces más operaciones, no el doble. Por eso los años de datos son tan caros.

**Ejemplo.** En el juguete: 223,6 / √10 = 223,6 / 3,162 = **70,7**. La media es 100 «más o menos 70,7».

En A: 951,32 / √196 = 951,32 / 14 = **67,95 USD**. Con las mismas operaciones pero sólo 49 de ellas, el error sería 951,32 / 7 = 135,9: el doble.

### 2.4 El estadístico t y el Sharpe por operación

**Fórmulas.**

```
s = media / desv                      (Sharpe por operación)

t = media / (desv / √n) = s × √n      (estadístico t)
```

**Intuición.** La t dice **a cuántos errores estándar está la media de cero**. Si la estrategia no tuviera ninguna ventaja, su media verdadera sería cero (o algo negativo, por los costes) y la media medida bailaría alrededor de ahí. Una t de 0,5 es un baile corriente. Una t de 3 es un baile muy raro: o hay algo, o has tenido mucha suerte.

La segunda forma, `t = s × √n`, separa las dos cosas que hacen grande una t: **calidad** por operación (`s`) y **cantidad** de operaciones (`√n`). Una estrategia mediocre con muchísimas operaciones y una estrategia buena con pocas pueden dar la misma t.

**Ejemplo.** Juguete: s = 100 / 223,6 = 0,447; t = 0,447 × 3,162 = **1,41**.

Estrategia A, oos1:

```
s = 196,25 / 951,32 = 0,2063
t = 0,2063 × √196 = 0,2063 × 14 = 2,888
```

Ese 2,888 es exactamente el hecho `gate.scorecard.trade_t` de A.

### 2.5 Cuando las operaciones no son independientes: n efectivo

La fórmula anterior supone que cada operación es una tirada independiente. Si una operación buena tiende a ir seguida de otra buena (rachas), en realidad hay **menos información** que operaciones.

**Fórmulas.**

```
ρ = suma de (xi − media) × (x(i−1) − media)  /  suma de (xi − media)²

n efectivo = n × (1 − ρ) / (1 + ρ)      (nunca más que n, nunca menos que 2)

t corregida = t × √(n efectivo / n)
```

`ρ` (ro) es la autocorrelación de orden 1: cuánto se parece cada operación a la anterior, entre −1 y +1.

**Intuición.** Con ρ = 0 no cambia nada. Con ρ positiva, n efectivo baja y la t se encoge. Con ρ negativa (una buena, una mala, una buena…) la fórmula daría **más** operaciones de las que hay; el código lo impide y deja n como está, «para que la autocorrelación negativa no fabrique observaciones».

**Ejemplo.** En la estrategia D, ρ = +0,032 sobre 96 operaciones:

```
n efectivo = 96 × (1 − 0,032) / (1 + 0,032) = 96 × 0,968 / 1,032 = 90,04
t corregida = 3,2396 × √(90,04 / 96) = 3,2396 × 0,9685 = 3,137
```

En A, ρ = −0,139: la fórmula daría 259, se queda en 196 y la t no cambia.

*Código:* `studies/screening/analysis/tradelevel.py:43-64`.

### 2.6 p-valor y umbral unilateral

**Definición.** El **p-valor** de una t es la probabilidad de ver una t así de grande **o mayor** en una estrategia sin ninguna ventaja. Se saca de la curva normal:

```
p = 1 − Φ(t)
```

`Φ` (fi mayúscula) es la función que da, para un número z, la probabilidad de que una variable normal estándar quede por debajo de z. Φ(0) = 0,5; Φ(1,65) = 0,95; Φ(2,33) = 0,99.

**«Unilateral»** quiere decir que sólo miramos un lado: nos interesa que la estrategia gane, no que pierda mucho.

| línea de t | p nominal | se lee |
|---|---|---|
| 1,65 | 5 % | 1 de cada 20 sin ventaja llega aquí por suerte |
| 2,00 | 2,3 % | 1 de cada 44 |
| 2,33 | 1 % | 1 de cada 100 |
| 3,00 | 0,13 % | 1 de cada 740 |

**Ejemplo.** La t de 2,888 de A tiene p = 1 − Φ(2,888) = 0,0019: dos de cada mil estrategias sin ventaja la alcanzarían.

**Por qué aquí la tasa NOMINAL no es la tasa MEDIDA.** El 5 % y el 1 % son lo que dice la teoría si las operaciones fueran independientes, de forma normal y de media exactamente cero. El proyecto no se fió y lo **midió**: fabricó poblaciones de estrategias sin ventaja y contó cuántas pasaban cada línea.

| línea | nominal | medido (celda mediana) | medido (peor celda) |
|---|---|---|---|
| t ≥ 1,65 | 5 % | **3,9 %** | 5,8 % |
| t ≥ 2,33 | 1 % | **0,6 %** | 1,1 % |

Las dos difieren por cuatro motivos, y conviene tenerlos en la cabeza:

1. **Los costes.** Una estrategia sin ventaja no tiene media cero: paga spread, así que su media es algo negativa y le cuesta más llegar a la línea. Por eso lo medido queda por debajo de lo nominal.
2. **La forma de las operaciones.** Colas gordas y rachas hacen que la t no siga exactamente la curva normal.
3. **El sesgo del término de deriva** (apartado 3.5): desplaza la t de una estrategia sin ventaja entre ±0,02 y ±0,27 según el activo y el lado. En EURUSD H1, a 1,65, pasan el 2,6 % de las largas sin ventaja y el 5,8 % de las cortas.
4. **Las propias poblaciones nulas exageran**: según el paquete de evidencia, sobrestiman la tasa de falsos positivos entre 2 y 4 veces. La tasa real podría ser del 1–2 % a 1,65 y del 0,15–0,3 % a 2,33.

H4 es más ruidoso: en su peor celda pasan el 8,9 % a 1,65 y el 1,7 % a 2,33.

### 2.7 Potencia: cuántas buenas se pierden

**Definición.** La **potencia** es la probabilidad de que una estrategia **con** ventaja real supere la línea. Es el espejo de la tasa de falsos positivos: aquella mide la basura que entra, esta mide lo bueno que se queda fuera.

**Fórmula.**

```
potencia = Φ( s × √n − z )
```

`s` es el Sharpe por operación **verdadero** de la estrategia; `n`, sus operaciones; `z`, la línea (1,65 o 2,33).

**Intuición.** Una estrategia con ventaja verdadera `s` tiene una t que baila alrededor de `s × √n`, con un baile de tamaño 1. Si `s × √n` cae justo en la línea, la supera la mitad de las veces: potencia del 50 %. Para superarla casi siempre hace falta que `s × √n` quede bastante por encima.

**Ejemplo a mano.** s = 0,15, n = 250, línea 2,33:

```
s × √n = 0,15 × 15,81 = 2,372
potencia = Φ(2,372 − 2,33) = Φ(0,042) = 51,7 %
```

**Tabla.** Potencia para la línea de PASA (2,33) y la de LIMBO (1,65):

| operaciones en oos1 | s = 0,15, línea 2,33 | s = 0,15, línea 1,65 | s = 0,04, línea 2,33 | s = 0,04, línea 1,65 |
|---|---|---|---|---|
| 100 | 20,3 % | 44,0 % | 2,7 % | 10,6 % |
| 175 | 36,5 % | 63,1 % | 3,6 % | 13,1 % |
| 250 | 51,7 % | 76,5 % | 4,5 % | 15,4 % |
| 375 | 71,7 % | 89,5 % | 6,0 % | 19,1 % |

Cómo leerla: 100 operaciones son 20 al año durante cinco años; 175 son 35 al año; 250 son 50; 375 son 75, el techo permitido.

Tres conclusiones que salen de la tabla y que el Council repitió:

- **Con una ventaja buena (0,15), el paso 8 pierde a la mayoría de las buenas** que operan poco: cuatro de cada cinco a 20 operaciones al año. (El paquete de evidencia da 18 % y 50 % para 20 y 50 al año; la fórmula da 20 % y 52 %. Es la misma cuenta con redondeos distintos.)
- **El paso 8 no puede llegar al 80 % de potencia con ninguna frecuencia permitida.** Para el 80 % hace falta `s × √n = 2,33 + 0,84 = 3,17`, es decir n = (3,17 / 0,15)² = 447 operaciones: 89 al año con cinco años de oos1. El techo es 75. Con los cuatro años de NIKKEI225 harían falta 112 al año.
- **0,15 es optimista.** La dispersión medida de la ventaja real entre estrategias es de unos 0,02. Con una ventaja de 0,04 la potencia a 2,33 no pasa del 6 % ni en el techo: la prueba casi no distingue una ventaja pequeña de ninguna.

### 2.8 El problema de buscar entre muchas

**El hecho.** Si pruebas muchas estrategias sin ventaja, **la mejor de todas tendrá una t alta sólo por ser la mejor**. No es un defecto de la estrategia: es aritmética.

**Fórmulas (dos aproximaciones).**

```
máximo esperado de N t's de puro ruido  ≈  √(2 × ln N)        (regla rápida, algo alta)

nivel que supera 1 de cada N            =  el z con  1 − Φ(z) = 1/N
```

`ln` es el logaritmo natural; `N`, el número de estrategias **independientes** probadas.

| N | √(2 ln N) | z que supera 1 de cada N |
|---|---|---|
| 100 | 3,03 | 2,33 |
| 500 | 3,53 | 2,88 |
| 1.000 | 3,72 | 3,09 |
| 10.000 | 4,29 | 3,72 |
| 118.235 | 4,83 | 4,30 |

**Intuición.** Con 10.000 estrategias sin ventaja, una de ellas llegará a t = 3,7 por pura suerte. Si tu mejor estrategia tiene 3,1, no has encontrado nada que el azar no explique.

**Ejemplo 1: la mejor de 118.235.** En la calibración del 2026-10-02 la t más alta entre 118.235 estrategias fue **3,57**. Sola, su p-valor es 0,00018 (1 de cada 5.600): parece una barbaridad. Pero se buscó entre 118.235. Aun descontando que muchas son casi copias unas de otras, tras «cientos de intentos independientes» harían falta unos **3,7** para afirmar algo. 3,57 no llega. La frase del dossier de calibración: «ninguna estrategia es significativa por sí sola después de la búsqueda; el paso 8 enriquece, no certifica».

**N efectivo (N_eff).** Las 118.235 no son independientes: comparten bloques, mercado y años. `N_eff` es el número de estrategias **independientes** que darían el mismo máximo. Se saca dándole la vuelta a la regla rápida:

```
N_eff ≈ e^(t máx² / 2) = e^(3,57² / 2) = e^6,37 ≈ 585
```

Es decir: en cuanto a suerte, las 118.235 se comportan como unas 500–600 tiradas independientes (cálculo del Council; es una regla de bolsillo, no una medida).

**Ejemplo 2: la población de NIKKEI225.** De 9.999 estrategias con t, la mejor es D con **3,14**, por debajo de los ≈ 3,7 que da el azar como máximo de 10.000 sin ventaja. Y hay 44 con t ≥ 2,33: con la tasa medida del 0,6 % se esperarían 60 por azar, y entre 15 y 30 si esa tasa está exagerada 2–4 veces. **44 cae dentro de lo que da el azar solo** (15–60). No hay nada en esta población que obligue a creer que alguna de las 44 tiene ventaja.

**Qué se puede decir entonces.** Sólo una estrategia con t por encima de ≈ 3,7 se sostendría sola. Con s = 0,15 eso pide (3,7 / 0,15)² = 608 operaciones: doce años a 50 al año. Nada de lo que produce la cadena llega.

### 2.9 Tasa base y Bayes: de «pasó la prueba» a «es buena»

**La pregunta que de verdad te importa** no es «¿qué probabilidad tiene una mala de pasar?», sino la contraria: «de las que pasan, ¿cuántas son buenas?». Depende de tres cosas, y la tercera se olvida siempre: cuántas buenas había **antes** de la prueba (la tasa base).

**Fórmula (Bayes).**

```
P(real | pasa) =            potencia × base
                  ─────────────────────────────────────
                  potencia × base  +  FPR × (1 − base)
```

`base` es la fracción de estrategias con ventaja real antes de mirar; `potencia`, la de 2.7; `FPR`, la tasa de falsos positivos de 2.6; `P(real | pasa)` se lee «probabilidad de que sea real, sabiendo que ha pasado».

**Intuición.** Si casi todo lo que entra es basura, casi todo lo que sale también lo es, aunque el filtro sea bueno: el 0,6 % de un montón enorme de basura es más que el 37 % de un puñado de buenas.

**Ejemplo a mano.** De 100.000 estrategias, supón que 1 de cada 500 es buena (base 0,2 %): 200 buenas y 99.800 malas. Línea 2,33, potencia 37 %, FPR 0,6 %.

```
buenas que pasan = 200 × 0,37     = 74
malas que pasan  = 99.800 × 0,006 = 599
P(real | pasa)   = 74 / (74 + 599) = 11,0 %
```

De cada nueve que pasan, una es buena.

**Tabla.** Con potencia 37 % (lo medido para s = 0,15 con suelo de 20 operaciones al año):

| tasa base | FPR 0,6 % (medida) | FPR 0,15 % (si exagera ×4) |
|---|---|---|
| 1 de cada 500 | 11 % | 33 % |
| 2 % (Eckhardt: «el 98 % de las ideas no funciona») | 56 % | 83 % |
| 10 % | 87 % | 97 % |

Nadie sabe cuál es la tasa base. Por eso el Council habló de un PASA como «una afirmación del 10 al 35 %», no como una certeza.

### 2.10 El «lift por cada 1.000»: lo que un criterio enriquece

**Definición.** Coges todas las estrategias de la calibración, las separas en «pasan el criterio en oos1» y «no lo pasan», y miras cuántas de cada grupo acaban con neto positivo en `oos2`, por cada 1.000. El **lift** es la diferencia, corregida para comparar a igual número de operaciones.

**Por qué se corrige.** Las que pasan un criterio suelen operar menos, y una estrategia que opera menos paga menos costes y acaba en positivo más a menudo por eso solo. Un tercio de cada diferencia bruta es ese efecto.

**Ejemplo a mano, t ≥ 1,65.**

```
rechazadas que ganan en oos2:        322 de cada 1.000
aceptadas que ganan en oos2:         396 de cada 1.000    → diferencia bruta +74
a igual número de operaciones:       322 + 52 = 374       → lift +52
```

El intervalo de confianza del +52 va de +24 a +83. Con t ≥ 2,33: 481 contra 364, lift **+103** (intervalo de +31 a +175, apoyado en sólo 18 celdas).

**Cómo leerlo.** Un lift de +52 dice que el criterio **funciona un poco**: la lista aceptada es mejor que la rechazada. También dice que funciona **poco**: de cada 1.000 aceptadas, 626 siguen acabando en negativo. El paso 8 limpia; no prueba.

**De lift a «cuántas son reales».** Si las que tienen ventaja real ganan en oos2 con probabilidad `w` y las que no, el 32,2 % de las veces, la fracción `f` de reales entre las aceptadas cumple:

```
0,322 + f × (w − 0,322) = 0,374      →     f = 0,052 / (w − 0,322)
```

Con w entre 0,68 y 0,90, f sale entre el **9 % y el 14 %** (cálculo de un miembro del Council en la primera ronda). Para la línea 2,33, entre el 19 % y el 33 %. Cuadra con la tabla de Bayes de arriba.

### 2.11 Profit factor y «PF de suerte»

**Fórmula.**

```
PF = suma de las operaciones ganadoras / suma (en positivo) de las perdedoras
```

**Ejemplo.** Juguete: ganadoras 300 + 200 + 400 + 250 + 350 = 1.500; perdedoras 100 + 200 + 150 + 50 = 500; PF = 1.500 / 500 = **3,0**. Estrategia A en oos1: 87.060 / 48.595 = **1,79**.

**Por qué un PF ≥ 1 significa poco con pocas operaciones.** El PF y la t son primos: los dos miden «gana más de lo que pierde», pero el PF no dice con cuántas operaciones. Para operaciones de forma normal hay una relación aproximada:

```
PF ≈ 1 + 2,5 × s
```

Una estrategia **sin ventaja** llega, una vez de cada veinte, a t = 1,65, es decir a un Sharpe por operación de `s = 1,65 / √n`. Su PF en ese golpe de suerte es el **PF de suerte**:

| operaciones al año (build de 10 años) | n | s de suerte = 1,65 / √n | PF de suerte (fórmula normal exacta) | PF de suerte medido |
|---|---|---|---|---|
| 20 | 200 | 0,116 | 1,34 | **1,36** |
| 30 | 300 | 0,095 | 1,27 | **1,29** |
| 50 | 500 | 0,074 | 1,20 | **1,21** |
| 75 | 750 | 0,060 | 1,16 | **1,17** |

La fórmula y lo medido coinciden a dos centésimas. Lectura: con 20 operaciones al año, **una de cada veinte estrategias sin ninguna ventaja enseña un PF de 1,36 en diez años**. Un filtro «PF ≥ 1,2» a esa frecuencia deja pasar ruido a puñados. Con 98 operaciones (las de C en oos1) el PF de suerte sube a 1,52: el 1,30 de C está por debajo.

### 2.12 Percentiles e intervalos de confianza

**Percentil.** El percentil 25 (p25) de una lista es el valor que deja por debajo al 25 % de los datos. La **mediana** es el p50. Ordenando el juguete: −200, −150, −100, −50, 0, 200, 250, 300, 350, 400. La mediana es el punto medio entre el 5.º y el 6.º: (0 + 200) / 2 = **100**.

En la población de NIKKEI225, el hecho `drift_excess_t` tiene p25 = −0,71, mediana = −0,05 y p75 = +0,60: la mitad central de la población vive entre −0,7 y +0,6, pegada a cero. El p95 es 1,45 y el p99, 2,06.

**Intervalo de confianza (IC) al 95 %.** Es el rango donde, con un 95 % de seguridad, está el valor verdadero:

```
IC 95 % = media ± 1,96 × error estándar
```

**Ejemplo.** Media por operación de A: 196,25 ± 1,96 × 67,95 = de **63 a 329 USD**. No incluye el cero, pero el extremo bajo es un tercio de la media medida.

**La regla de lectura.** Si un intervalo incluye el cero, no se ha demostrado nada. Y un intervalo ancho es una confesión de que hay pocos datos: el lift de la línea 2,33 es +103 «de +31 a +175», o sea, entre «poca cosa» y «muchísimo».

---

## 3. Las reglas del paso 8, una a una

Van en el orden del fichero. Son 16. Cada una lleva los mismos seis apartados.

Los recuentos «en la población» son sobre las **10.000 estrategias** de la corrida de ejemplo, cada una con sus hechos (emparejados por el nombre de la estrategia, para que el fallo de contabilidad del aviso 2 no ensucie la cuenta regla a regla). «La única que la descarta» cuenta las estrategias a las que esa regla da NO PASA y **ninguna otra** se lo da: es lo que de verdad cuesta la regla.

### 3.1 R1a — Sigue en el databank del retest

Hecho: `gate.scorecard.presencia_passed`

**Qué mide.** Si la estrategia del build sigue existiendo en el databank del retest. SQX tira una estrategia del retest cuando salta una de sus propias banderas rojas (demasiadas operaciones ambiguas, entre otras).

**Cómo se calcula.** Vale 1 si la identidad de la estrategia del build aparece entre las del retest, y 0 si no. La «identidad» es la huella (SHA-256) del XML interno de la estrategia, normalizado; el emparejamiento build–retest se busca por el nombre del fichero y a partir de ahí todo se guarda bajo la identidad **del build**.

*Código:* `studies/screening/gate/screens.py:27-44`; el emparejamiento, `studies/screening/gate/README.md` («The join is on identity, found by the strategy name»).

**Ejemplo numérico.** A, B y C valen 1. En esta corrida la puerta emparejó las 10.000: su embudo dice «presencia: entran 10.000, pasan 10.000».

Y sin embargo el juez dio «sin dato» en esta regla a **1.557** estrategias. La cuenta:

```
ficheros en el databank OOS (los que se juzgan):                 10.000
  su identidad coincide con la que usó la puerta:                 8.443
  su identidad es otra (cambió entre el build y el retest):       1.548
  su identidad no aparece en ningún hecho:                            9
                                                                 ──────
  sin el dato presencia_passed  →  missing: fail  →  NO PASA      1.557
```

De esas 1.557, por sus propios números 1.528 habrían sido NO PASA igualmente y **29 habrían sido LIMBO**. Ninguna habría sido PASA.

**El criterio cargado y por qué.** `pass: ">= 1"`, `missing: fail`. No tiene LIMBO. Es anterior al Council y este no la examinó; viene de tu decisión del 2026-09-23: si SQX la tiró, esa decisión ya está tomada y la estrategia se va. El `missing: fail` es coherente con eso (una estrategia que no está no tiene dato), pero convierte en NO PASA cualquier fallo de emparejamiento.

**Cómo sería el resultado ideal.** 1 en todas las que SQX conservó, y que el juez encuentre el dato en todas. Hoy se cumple lo primero y no lo segundo.

**Si mueves este umbral.** No hay umbral que mover. La decisión es arreglar la búsqueda (que el juez encuentre los hechos por el nombre cuando la identidad cambió). Ganas 29 LIMBO en esta población; no cuesta nada. `OPEN.md` ya recoge que entre el 7 y el 11 % de las estrategias cambian de identidad entre el build y el retest; aquí es el 15,5 %, y lo que no estaba escrito es que el juez las descarta.

### 3.2 R1b — Tiene operaciones suficientes y no es un clon

Hecho: `gate.scorecard.sanidad_passed`

**Qué mide.** Dos cosas mínimas: que haya algo que medir en oos1, y que la estrategia no sea la misma lista de operaciones que otra.

**Cómo se calcula.** Cuenta las operaciones de oos1 (ese recuento es `sanidad_value`). Vale 1 si hay **al menos 20** y la lista de operaciones no es idéntica a la de otra estrategia; de un grupo de clones sobrevive la primera. El 20 está en `ledger/thresholds.yaml` (`gate.sanidad.min_trades`, tuyo, 2026-09-23). Los clones se buscan en las operaciones mismas, no en el nombre ni en la huella del fichero.

*Código:* `studies/screening/gate/screens.py:47-70`.

**Ejemplo numérico.** A tiene 196 operaciones en oos1, B 193 y C 98: las tres pasan de 20 y ninguna es clon. Valen 1.

Por qué 20: con 20 operaciones el error estándar es `desv / √20 = desv / 4,47`. Con 4 operaciones sería `desv / 2`: la media bailaría la mitad de una desviación típica entera y la t no diría nada.

**El criterio cargado y por qué.** `pass: ">= 1"`, `missing: fail`. Anterior al Council, no examinada por él. Convención: «una estrategia con cuatro operaciones fuera de muestra no tiene error estándar que leer, y una que repite las operaciones de otra no es una segunda observación».

**Cómo sería el resultado ideal.** 1. Y cuantos menos clones, mejor: cada clon es tiempo de máquina gastado dos veces.

**Si mueves este umbral.** En la población descarta 142: **129 clones** y 13 con menos de 20 operaciones. Es la única regla que descarta a 7 de ellas (clones que, si no lo fueran, quedarían en LIMBO). Subir el mínimo de 20 no hace falta: de eso se ocupa, sin descartar, la regla de las 100 operaciones (3.9).

### 3.3 R2 — Ganó dinero en oos1

Hecho: `gate.scorecard.estaticas_value`

**Qué mide.** El beneficio neto de la estrategia en oos1, en dólares, tal como lo da SQX con los costes de la tarea de retest.

**Cómo se calcula.** Es la métrica `Net profit [OOS]` que SQX guarda en el fichero de la estrategia del retest. Es la suma del resultado de todas sus operaciones de oos1:

```
neto = x1 + x2 + … + xn = n × media
```

Sólo existe para las que pasaron la criba anterior de la cascada (9.858 de 10.000).

*Código:* `studies/screening/gate/screens.py:73-89`; la criba, `studies/screening/gate/config.yaml` (fila `estaticas`).

**Ejemplo numérico.**

```
A:  196 × 196,25 = 38.465 USD   (38,5R en cuatro años)
B:  193 × 165,09 = 31.862 USD
C:   98 ×  47,86 =  4.690 USD
```

Las tres ganan. La suma de las operaciones de A da 38.465,41, que es el hecho guardado.

**El criterio cargado y por qué.** `pass: "> 0"`. Sin LIMBO: con neto cero o negativo es NO PASA; sin dato, LIMBO. Es anterior al Council, y el Council la mantuvo («NO PASA: t por debajo de 1,65 o neto ≤ 0»). Lo medido: ganar en oos1 da un lift de **+34 por cada 1.000** en oos2 a igual número de operaciones. Es un criterio débil: en esta población el 59 % de las estrategias (5.946) acaba oos1 en positivo, y son largas en un índice que subió de 23.470 a 33.290.

**Cómo sería el resultado ideal.** Positivo, y sobre todo positivo **por la t** y no por el mercado: la regla de verdad es la 3.5.

**Si mueves este umbral.** Descarta 3.912 y deja 142 sin dato. **No es la única que descarta a ninguna**: toda estrategia con neto ≤ 0 tiene también una t por debajo de 1,65. Quitarla hoy no cambiaría el resultado (2 / 167 / 9.831 igual). Sirve de red por si la regla de la t se afloja.

### 3.4 R2b — Sigue ganando al spread real

**Regla retirada el 2026-10-06 (dueño).** Su «spread real» era la referencia anterior a la recalibración de costes del 2026-10-04 (ticks de Darwinex y slippage a la mitad del spread, frente al 35 % y al spread de las firmas de fondeo que lleva hoy la ficha), y no descartaba nada que la t no descartase ya. Lo que sigue es cómo funcionaba; ya no juzga.

Hecho: `spread.verdict_csv.neto_con_slippage_real_oos`

**Qué mide.** El mismo neto de oos1, pero cobrando a cada operación el spread que **de verdad** había en el mercado en ese minuto (el de los ticks de Darwinex) y un slippage que lo acompaña, en lugar del spread plano y el slippage plano que cobró SQX.

**Cómo se calcula.** Operación a operación. Sólo cambian los costes; la operación, su entrada y su salida son las mismas.

```
P/L al spread real  = P/L de SQX + (spread SQX − spread real) × lotes × valor del punto

P/L con slippage real = P/L al spread real
                      + (2 × slippage SQX − (spread entrada + spread salida) / 2) × lotes × valor del punto
```

- `spread real` es el que paga la operación: el de la entrada si es larga, el de la salida si es corta. Se toma del primer tick de Darwinex en la apertura de esa barra; si no hay tick cerca (antes de 2017), se usa un modelo y la operación lo dice.
- `slippage SQX` es el plano que cobró la tarea en cada uno de los dos rellenos; se sustituye por **la mitad del spread real** en cada relleno (tu convención).
- `valor del punto`: 0,063137 USD por punto de precio y lote en NIKKEI225.

El hecho es la suma de la segunda línea sobre las operaciones de oos1.

*Código:* `studies/data/spread/reprice.py:58-71` (spread) y `:74-92` (slippage).

**Ejemplo numérico.** La segunda operación de A en oos1: larga, abierta el 5-02-2020 a las 11:00, 70,89 lotes, resultado en SQX +550,85 USD. SQX cobró un spread plano de 4,7491 puntos de precio; en ese minuto Darwinex tenía 11,0 a la entrada y 6,0 a la salida. El slippage plano de la tarea era 1,6622 por relleno.

```
lotes × valor del punto = 70,89 × 0,063137 = 4,4758

al spread real  = 550,85 + (4,7491 − 11,0) × 4,4758 = 550,85 − 27,98 = 522,87
con slippage    = 522,87 + (2 × 1,6622 − (11,0 + 6,0)/2) × 4,4758
                = 522,87 + (3,3244 − 8,5) × 4,4758 = 522,87 − 23,16 = 499,71
```

Sumando las 196 operaciones de A:

| | A | B | C |
|---|---|---|---|
| neto según SQX | 38.465 | 31.862 | 4.690 |
| al spread real | 35.908 | 29.201 | 3.459 |
| con slippage real (el hecho) | **32.195** | **25.493** | **1.574** |
| spread real medio (puntos de precio) | 7,85 | 8,00 | 7,60 |

A pierde el 16 % de su neto; C pierde dos tercios y se queda en 1.574 USD: 16 USD por operación.

**El criterio cargado y por qué.** `pass: "> 0"`. Sin LIMBO; sin dato (un activo sin escaneo de spread), LIMBO. Anterior al Council y no examinada por él regla a regla. Lo medido: «PF al spread real ≥ 1» da un lift de **+28 por cada 1.000**.

En esta población el spread plano de SQX queda, de mediana, en el **percentil 10,5** del spread real: nueve de cada diez veces el mercado cobraba más que el backtest. Por eso la mediana del neto baja de +2.673 USD (SQX) a **−1.672 USD**, y el PF mediano de 1,06 a 0,97.

**Cómo sería el resultado ideal.** Que el neto apenas cambie al pasar al spread real: quiere decir que la estrategia no vive del margen que le regala un coste optimista. A conserva el 84 %.

**Si mueves este umbral.** Descarta 5.646; de ellas, **1.689 ganaban según SQX** y dejan de ganar al coste real. No es la única que descarta a ninguna (todas caen también por la t). Quitarla no cambia el resultado de hoy. Lo que sí dice esta regla, y es una decisión tuya aparte, es que en NIKKEI225 el spread que lleva la tarea de SQX está por debajo del real de Darwinex.

### 3.5 R3 — La t de la operación, descontada la deriva del mercado

Hecho: `gate.scorecard.drift_excess_t`

**Qué mide.** Si el beneficio medio por operación en oos1 se distingue del azar **después de quitarle lo que el mercado habría pagado a cualquiera por estar dentro**. Es la regla central del paso: la única de toda la cadena con tasa de falsos positivos medida.

**Cómo se calcula.** En cuatro pasos.

*Paso 1: la deriva del mercado por barra.* Se toman todas las barras del timeframe de la estrategia en el tramo oos1 del activo y se calcula el cambio medio de cierre a cierre:

```
μ = media de (cierre de la barra − cierre de la barra anterior), sobre todo oos1
```

`μ` (mu) es la deriva: lo que el precio sube, de media, en una barra. En NIKKEI225 M30, 2020–2023: el índice pasó de 23.470 a 33.290 (+9.819 puntos) en 45.979 barras, así que **μ = 0,2136 puntos por barra**.

*Paso 2: lo que la deriva le pagó a cada operación.*

```
deriva de la operación = lado × μ × barras que estuvo abierta × lotes × valor del punto
```

`lado` es +1 si es larga y −1 si es corta. Es lo que habría ganado una operación «ciega» del mismo lado, la misma duración y el mismo tamaño, si cada barra hubiera sido una barra media.

*Paso 3: el exceso.*

```
exceso de la operación = P/L de la operación − deriva de la operación
```

*Paso 4: la t del exceso, con n efectivo.* Media, desviación y t como en 2.4, y la corrección de 2.5:

```
drift_excess_t = (media del exceso / desv del exceso) × √n × √(n efectivo / n)
```

**Por qué se resta la deriva.** Un largo en un índice que sube gana aunque la entrada no valga nada: «los largos en índices ganan el 51 % de las veces con cualquier regla». Sin restarla, la t premiaría a las estrategias por estar mucho tiempo dentro de un mercado alcista. Aronson y Katsanos dan el ejemplo: un p-valor de 0,0002 contra cero se convirtió en 0,216 contra comprar y mantener.

**El sesgo conocido de ese término.** El paso 2 supone que cada barra que la operación estuvo abierta fue una barra media. Pero la doctrina dimensiona las operaciones **en proporción inversa a la volatilidad** (más lotes cuando el mercado está tranquilo, menos cuando está agitado). En A se ve: 75,04 lotes en enero de 2020 y 21,50 en marzo de 2020. Si en un activo las épocas tranquilas van seguidas de movimientos distintos de la media, una operación sin ninguna habilidad se queda con un resto positivo o negativo que el término no descuenta. Ese resto tiene el signo contrario para largos y cortos. Medido: desplaza la t de una estrategia sin ventaja entre **±0,02 y ±0,27** (EURUSD largo −0,19; USDCAD largo +0,18, a 50 operaciones al año). Consecuencia: un largo y un corto, o dos activos, **no están en la misma escala de t**. La corrección propuesta («la operación ciega de la misma duración») quita cerca del 60 % del sesgo y **no está aplicada**: el dato que juzga hoy es el de la puerta sin corregir. Para NIKKEI225 largo el tamaño del sesgo no está medido en las fuentes que he leído.

*Código:* `studies/screening/analysis/tradelevel.py:7-19` (μ), `:22-40` (deriva), `:43-64` (t y n efectivo); `studies/screening/gate/measures.py:25-36`. El sesgo: `knowhow/research/drift-term-biased-by-side.md`.

**Ejemplo numérico.** La primera operación de A en oos1: larga, del 9-01-2020 a las 07:30 al mismo día a las 21:00 (27 barras), 75,04 lotes, resultado −41,70 USD.

```
deriva = 1 × 0,2136 × 27 × 75,04 × 0,063137
       = 5,766 × 75,04 × 0,063137 = 432,68 × 0,063137 = 27,32 USD
exceso = −41,70 − 27,32 = −69,02 USD
```

El mercado, sólo por subir, «le debía» 27 USD a esa operación; perdió 42, así que frente al mercado perdió 69.

Las 196 operaciones de A, juntas:

```
media del P/L        = 196,25 USD
deriva media         =  23,92 USD   (25,2 barras de media × 70,2 lotes de media)
media del exceso     = 196,25 − 23,92 = 172,33 USD
desv del exceso      = 949,76 USD
s                    = 172,33 / 949,76 = 0,1814
t                    = 0,1814 × √196 = 0,1814 × 14 = 2,540
ρ = −0,139 (negativa) → n efectivo se queda en 196 → drift_excess_t = 2,540
```

La deriva explica 4.689 de los 38.465 USD de A: el 12 %. Su t baja de 2,89 a 2,54.

| | A | B | C |
|---|---|---|---|
| operaciones (n) | 196 | 193 | 98 |
| media del P/L (USD) | 196,25 | 165,09 | 47,86 |
| deriva media (USD) | 23,92 | 24,92 | 7,04 |
| media del exceso (USD) | 172,33 | 140,17 | 40,82 |
| desv del exceso (USD) | 949,76 | 903,96 | 575,90 |
| error estándar = desv / √n | 67,84 | 65,07 | 58,18 |
| **`drift_excess_t`** | **2,540** | **2,154** | **0,702** |
| `trade_t` (sin descontar) | 2,888 | 2,529 | 0,819 |

C apenas tiene deriva (7 USD) porque sus operaciones duran poco: 6,9 barras de media. No es la deriva lo que la hunde; es que 41 USD de media con 576 de desviación y 98 operaciones no se distinguen de cero.

Las tres cifras en negrita coinciden con el hecho guardado hasta el sexto decimal.

**El criterio cargado y por qué.**

| | PASA | LIMBO | NO PASA |
|---|---|---|---|
| M30 (y cualquier otro) | ≥ 2,33 | 1,65 a 2,33 | < 1,65 |
| H4 | ≥ 2,5 | 1,65 a 2,5 | < 1,65 |
| H1 | inalcanzable | ≥ 1,65 | < 1,65 |

Es **del Council** (2026-10-04) y es la regla con más evidencia detrás:

- **Falsos positivos medidos.** t ≥ 1,65 la pasa el 3,9 % de las estrategias sin ventaja (5,8 % en la peor celda); t ≥ 2,33, el 0,6 % (1,1 %). Y esas cifras exageran de 2 a 4 veces.
- **Lift medido.** +52 por cada 1.000 a 1,65 (IC +24 a +83); +103 a 2,33 (IC +31 a +175, sobre 18 celdas). A igual número de operaciones, el grupo pasa de 322 a unas 374 ganadoras por cada 1.000 (la cifra bruta es 396).
- **H1.** El lift se reparte así: +81 en M30 y **+19 en H1, que es prácticamente cero**. La persistencia de oos1 a oos2 dice lo mismo: 0,084 en M30 y 0,026 en H1. Por eso una H1 no puede PASAR sólo con el paso 8: la promueve una muestra nueva (pasos 10, 12 o 20). Se escribió con una línea de PASA inalcanzable (`>= 1000`). Munger pidió atarlo a «tener una muestra nueva» y no a la etiqueta del timeframe, porque el +19 no tiene intervalo publicado y el +81 de M30 descansa en pocas celdas.
- **H4.** Es más ruidoso (peor celda: 8,9 % y 1,7 %), de ahí el 2,5. El propio paquete de evidencia la da por dudosa y proponía 1,9 para el LIMBO; en disco el LIMBO de H4 está en 1,65. H4 no se ha recalibrado.

Una discrepancia dentro del fichero: el comentario de la regla (líneas 80-81) todavía dice «nunca da Fallo: 2,33 es la línea de Pass y por debajo es Limbo». Eso era la propuesta anterior. La regla escrita debajo sí descarta por debajo de 1,65, que es lo que acordó el Council (línea 85). Manda la regla, no el comentario.

**Cómo sería el resultado ideal.** t ≥ 2,33 en M30, con 100 operaciones o más. El techo honesto:

- En esta población, las 44 que llegan a 2,33 **caben dentro de lo que da el azar solo** (15–60 esperadas). La mejor, D con 3,14, está por debajo del máximo esperado del ruido (≈ 3,7).
- La potencia es baja (2.7): con s = 0,15 y las 196 operaciones de A, 41 %; con s = 0,04, 4 %.
- Pasar no es validar: de las que pasan 1,65, el 60 % acaba en negativo en oos2, y el neto por operación en oos2 es negativo en **todos** los grupos (de −0,013R en PASA a −0,055R en NO PASA).

A, con 2,54, es una **candidata**. No es un hallazgo.

**Si mueves este umbral.** Es la regla que más pesa: descarta **9.674** de 10.000 y es **la única que descarta a 2.472**. Deja 281 en LIMBO (más una sin dato) y 44 por encima de 2,33.

Cuántas hay por encima de cada línea: 1.333 con t ≥ 1,0; 738 con ≥ 1,28; 325 con ≥ 1,65; 112 con ≥ 2,0; 44 con ≥ 2,33; 21 con ≥ 2,5; 3 con ≥ 3,0.

| si la línea de NO PASA fuera | PASA | LIMBO | NO PASA |
|---|---|---|---|
| 1,65 (hoy) | 2 | 167 | 9.831 |
| 1,28 (p nominal 10 %) | 2 | 425 | 9.573 |
| 1,0 | 2 | 807 | 9.191 |
| 2,0 | 2 | 52 | 9.946 |
| ninguna (propuesta de agente anterior) | 2 | 2.639 | 7.359 |

| si la línea de PASA fuera | PASA | LIMBO | NO PASA |
|---|---|---|---|
| 2,33 (hoy) | 2 | 167 | 9.831 |
| 2,0 | 9 | 160 | 9.831 |
| 1,65 | 19 | 150 | 9.831 |
| 3,0 | 0 | 169 | 9.831 |

Lo que se gana y se pierde: bajar la línea de NO PASA a 1,28 mete 258 estrategias más en el paso 9 (tiempo de máquina) con una tasa de falsos positivos nominal del doble; lo medido dice que el lift baja con la línea, pero no hay cifra medida para 1,28. Subirla a 2,0 deja 52 y ahorra máquina, a costa de potencia: con s = 0,15 y 175 operaciones, de 63 % a 49 %. Mover la línea de PASA no cambia qué sigue adelante (LIMBO también sigue): sólo cambia la etiqueta.

### 3.6 R4a — Opera lo bastante en el build (suelo)

Hecho: `gate.scorecard.is_trades_per_year`

**Qué mide.** Cuántas operaciones al año hace la estrategia en el tramo `build`. Es la frecuencia «de diseño» de la estrategia.

**Cómo se calcula.**

```
operaciones por año en IS = operaciones en el build / años del tramo build
```

Los años son **los del tramo del activo en el calendario**, no el tiempo entre la primera y la última operación: días entre el principio y el final del tramo, divididos por 365,25. Para NIKKEI225 el build va del 19-09-2011 al final de 2019: **8,2847 años**. Para XAUUSD y forex son 10.

*Código:* `studies/screening/gate/measures.py:38`; los años, `studies/screening/gate/inputs.py:57-76`.

**Ejemplo numérico.**

```
A:  329 / 8,2847 = 39,71   → PASA  (≥ 35)
B:  307 / 8,2847 = 37,06   → PASA
C:  189 / 8,2847 = 22,81   → LIMBO (entre 20 y 35)
D:  138 / 8,2847 = 16,66   → NO PASA (< 20)
```

D es la de mejor t de la población (3,14) y cae aquí.

**El criterio cargado y por qué.**

| | PASA | LIMBO | NO PASA |
|---|---|---|---|
| M30, H1 | ≥ 35 | 20 a 35 | < 20 |
| H4 | ≥ 35 | 15 a 35 | < 15 |

Es **del Council**. Las piezas:

- **Tu suelo de trabajo de 35** quedó como línea de PASA, **no de descarte**. Usado como descarte, un suelo en el build pierde este porcentaje de las estrategias robustas, en H1 y en M30 por igual:

| suelo (operaciones/año) | 20 | 25 | 30 | 35 | 40 | 50 |
|---|---|---|---|---|---|---|
| robustas que se pierden | 51 % | 63 % | 74 % | 81 % | 86 % | 92 % |

- **Y no compra calidad.** Las robustas que el suelo quita pasan oos2 igual que el resto de su banda: **17,1 contra 16,8 por cada 1.000**. La calidad por operación no cambia con la frecuencia. El coste del suelo está en el número de estrategias, no en su ventaja.
- **El suelo duro de 20** (15 en H4) viene de Tharp (un mínimo de 100 operaciones: 20 al año por cinco años) y de la potencia: a 20 al año una ventaja buena pasa la línea 2,33 una de cada cinco veces (2.7).
- **No es redundante con la t** (Kahneman). Con una ventaja pequeña y realista (s = 0,04), la probabilidad de llegar a 2,33 es 2,7 % con 100 operaciones y 6,0 % con 375: la misma t «vale la mitad» a 20 al año que a 75. Por eso entre 20 y 35 es LIMBO aunque la t sea alta.
- **El PF no sirve de sustituto**: a 20 al año el PF de suerte es 1,36 (2.11).

Disidencia que quedó en el acta: Munger dejaría PASAR a una estrategia de 20 a 35 al año si su t llega a 2,33; los otros cuatro la mantienen en LIMBO (Taleb, además, a un cuarto del riesgo).

**Cómo sería el resultado ideal.** Entre 35 y 75 al año. Cuanto más cerca de 75, más potencia tiene la prueba de la t.

**Si mueves este umbral.** En la población: 4.202 pasan, **3.557 quedan en LIMBO** y **2.241 son NO PASA**. Es la única que descarta a **127**.

| si el suelo duro fuera | PASA | LIMBO | NO PASA |
|---|---|---|---|
| 20 (hoy) | 2 | 167 | 9.831 |
| 15 | 2 | 270 | 9.728 |
| 10, o ninguno | 2 | 294 | 9.704 |
| 25 | 2 | 93 | 9.905 |
| 30 | 2 | 64 | 9.934 |
| 35 (tu suelo, como descarte) | 2 | 47 | 9.951 |

Poner tu suelo de 35 como descarte dejaría 49 estrategias vivas en vez de 169: pierdes 120 (el 71 %) sin ganar calidad medida. Quitar el suelo recupera 127, entre ellas D.

Y la variante de Munger (PASA con t ≥ 2,33 desde 20 al año): **14 PASA** en vez de 2, con las mismas 9.831 descartadas. No cambia qué sigue adelante; cambia doce etiquetas.

### 3.7 R4b — No opera demasiado (techo)

Hecho: `gate.scorecard.is_trades_per_year` (el mismo; es una segunda regla sobre él)

**Qué mide.** Que la estrategia no opere por encima de una frecuencia a partir de la cual las poblaciones dejan de contener ventaja.

**Cómo se calcula.** El mismo número de 3.6.

**Ejemplo numérico.** A, 39,7; B, 37,1; C, 22,8. Las tres por debajo de 75: PASA.

**El criterio cargado y por qué.** M30 y H1: `pass: "<= 75"`, sin LIMBO: por encima de 75 es NO PASA. H4: PASA hasta 50, LIMBO hasta 65, NO PASA por encima. El 75 es **del Council** («por encima de 75, NO PASA, sin limbo») y está medido: por debajo de 75 al año las poblaciones dan entre 1,4 y 2,8 veces las estrategias robustas que da el azar; por encima, **0,41 veces**: menos de la mitad de lo que saldría al azar. Las líneas de H4 son anteriores al Council y no se han recalibrado.

**Cómo sería el resultado ideal.** Por debajo de 75, que es también el techo que ya lleva el build en `assets/_study.yaml`.

**Si mueves este umbral.** En esta población no descarta a **ninguna**: el máximo es 74,96, porque el build ya traía el techo puesto. Bajarlo sí costaría: a 60, seis LIMBO menos (2 / 161 / 9.837); a 50, dieciocho menos (2 / 149 / 9.849). No hay medida de que 60 o 50 sean mejores que 75.

### 3.8 R5 — La frecuencia no se hundió fuera de muestra

Hecho: `gate.scorecard.oos_trades_per_year`

**Qué mide.** Cuántas operaciones al año hace en oos1. Si una estrategia hacía 40 al año en el build y hace 6 en oos1, sus reglas han dejado de dispararse: el mercado cambió o las reglas estaban ajustadas a algo que ya no pasa.

**Cómo se calcula.**

```
operaciones por año en oos1 = operaciones en oos1 / años del tramo oos1
```

Años del calendario del tramo: 4,0 en NIKKEI225; 5 en XAUUSD y forex.

*Código:* `studies/screening/gate/measures.py:38`.

**Ejemplo numérico.**

```
A:  196 / 4 = 49,0     B:  193 / 4 = 48,25     C:  98 / 4 = 24,5
```

Las tres pasan (≥ 15). Las tres operan **más** en oos1 que en el build (A: 49,0 contra 39,7).

**El criterio cargado y por qué.** `pass: ">= 15"`, `limbo: ">= 10"`; por debajo de 10, NO PASA. Anterior al Council y no examinada por él. Es una convención («por debajo de 10 no hay estadística»), no una línea medida.

**Cómo sería el resultado ideal.** Parecida a la del build. Una caída o una subida fuerte merecen una mirada.

**Si mueves este umbral.** 9.695 pasan, 210 LIMBO, 95 NO PASA; no es la única que descarta a ninguna. Subir el descarte a 15 mueve una sola estrategia. Un detalle: la línea de PASA (15 al año) es **más laxa** que la regla siguiente: 15 al año son 60 operaciones en cuatro años, y la siguiente pide 100.

### 3.9 R5b — Tiene al menos 100 operaciones en oos1

Hecho: `spread.verdict_csv.operaciones_oos`

**Qué mide.** El número de operaciones de oos1, sin dividir por años. Es un suelo de «legibilidad»: por debajo, la t existe pero no se puede leer con confianza.

**Cómo se calcula.** Cuenta las operaciones de oos1 de la estrategia. Sale del estudio del spread, que las cuenta al repreciarlas; coincide con `sanidad_value` de la puerta.

*Código:* `studies/data/spread/one.py:34`.

**Ejemplo numérico.** A, 196: PASA. B, 193: PASA. C, 98: **LIMBO** por dos operaciones.

Por qué 100: el error estándar con 100 operaciones es `desv / 10`. Y hace falta una muestra con cola: en 100 operaciones caben unas pocas de las que hacen daño; en 30, quizá ninguna.

**El criterio cargado y por qué.** `pass: ">= 100"`, `else: limbo`. **Nunca descarta.** Es **del Council**, propuesta de Feynman: con menos de 100 el resultado «no es negativo, es ilegible». Feynman retiró su propuesta anterior de exigir 200, porque la t ya lleva dentro el número de operaciones. Los libros van en la misma dirección: Tharp pide 100 o más; Fitschen recuerda que «30 operaciones bastan» es falso.

**Cómo sería el resultado ideal.** 175 o más (35 al año en cinco años). Con 375 (el techo), la potencia a 2,33 con s = 0,15 llega al 72 %.

**Si mueves este umbral.** 7.735 pasan y **2.265 quedan en LIMBO**; cero descartes. Si en vez de LIMBO fuera NO PASA: 2 / 161 / 9.837 (pierdes 6). Si la línea fuera 200: **A dejaría de ser PASA** (tiene 196) y el resultado sería 1 / 168 / 9.831. Con cuatro años de oos1, 200 operaciones son 50 al año: una línea de 200 es en la práctica un suelo de frecuencia.

### 3.10 R5c — La ventaja bruta frente al coste

Hecho: `edgeCost.verdict_csv.edge_mean`

**Qué mide.** Cuántas veces cabe el coste de una operación en lo que la operación gana **antes de costes**. La idea es de Kaufman: si la ventaja bruta es sólo un poco mayor que el coste, cualquier empeoramiento del coste se la come.

**Cómo se calcula.**

```
bruto de la operación  = P/L de SQX + comisión + coste de spread que SQX le cobró
coste de hoy           = (spread declarado hoy + comisión) × lotes × valor del punto

edge_mean = media del bruto / media del coste de hoy
```

Tres cosas que conviene saber, porque cambian cómo se lee el número:

1. **Se calcula sobre todas las operaciones de la estrategia, build y oos1 juntas.** No es una medida de oos1. El hecho `n` que lo acompaña es ese total (525 en A: 329 + 196).
2. **El «coste que SQX cobró» no se lee de la configuración: se mide** en los rellenos, comparando el precio de entrada con el de la barra. En NIKKEI225 sale 8,07 puntos de precio en oos1, que es el spread declarado (4,7491) **más dos veces el slippage** (2 × 1,6622).
3. **El «coste de hoy» del denominador lleva sólo el spread declarado** (la comisión en índices es 0). No lleva el slippage.

La consecuencia de 2 y 3: arriba se devuelve spread más slippage, abajo se divide sólo por el spread. En NIKKEI225 el coste real que se devolvió es **1,70 veces** el del denominador. Así que:

```
neto por operación = (edge_mean − 1,70) × coste de hoy
```

- `edge_mean = 1,70` es el punto en que la estrategia **ni gana ni pierde**. No es 1.
- `edge_mean = 1,25` (la línea de NO PASA) ya es una estrategia que pierde.
- `edge_mean = 2` (la línea de PASA) deja un neto de 0,30 veces el spread declarado.
- El múltiplo de verdad sobre el coste que pagó es `edge_mean / 1,70`.

*Código:* `studies/readings/edgeCost/one.py:32-60` (el cociente, línea 48); `studies/readings/edgeCost/costs.py:68-109` (bruto, línea 96; coste de hoy, línea 107).

**Ejemplo numérico.** A, sus 525 operaciones:

```
media del P/L              = 129,35 USD
coste medido medio         =  37,12 USD
media del bruto            = 129,35 + 37,12 = 166,47 USD
coste de hoy medio         =  21,84 USD
edge_mean                  = 166,47 / 21,84 = 7,62

múltiplo real sobre lo pagado = 166,47 / 37,12 = 4,48
```

| | A | B | C |
|---|---|---|---|
| operaciones (build + oos1) | 525 | 500 | 287 |
| media del P/L (USD) | 129,35 | 121,00 | 62,47 |
| coste medido (USD) | 37,12 | 37,50 | 36,71 |
| bruto medio (USD) | 166,47 | 158,50 | 99,18 |
| coste de hoy (USD) | 21,84 | 22,06 | 21,60 |
| **`edge_mean`** | **7,62** | **7,18** | **4,59** |
| múltiplo sobre lo pagado | 4,48 | 4,23 | 2,70 |

Las tres pasan con holgura. Los tres valores coinciden con el hecho guardado.

**El criterio cargado y por qué.** `pass: ">= 2"`, `limbo: ">= 1.25"`, `missing: limbo`; por debajo de 1,25, NO PASA. **Es la banda del paso 25** (el margen de Kaufman para el coste real), leída aquí por decisión de quien coordinó el Council; el Council no la calibró para el paso 8. Lo medido es un lift de **+34 por cada 1.000** para «ventaja/coste ≥ 2», igual que el de «neto > 0»; Munger lo resumió en «esta prueba anota». Los libros: Kaufman pone 1,25 como multiplicador mínimo del coste y avisa de que exagerar el coste también hace daño; Carver pide no gastar más de un tercio de la ventaja en costes (un múltiplo de 3).

El último comentario del fichero todavía dice que la ventaja por coste queda «SIN regla». Está desfasado: la regla existe unas líneas más arriba.

**Cómo sería el resultado ideal.** Un múltiplo de 3 **sobre el coste realmente pagado**, que en NIKKEI225 es un `edge_mean` de 5 o más. A y B lo cumplen; C (2,70 reales) no.

**Si mueves este umbral.** 8.445 pasan, 902 LIMBO, 653 NO PASA. **No es la única que descarta a ninguna**: de las 1.153 con `edge_mean` por debajo de 1,70 ninguna tiene neto positivo en oos1, así que caen antes por las reglas 3.3 y 3.5. Subir las líneas a 3 y 1,7, o a 3,4 y 2,125 (lo que de verdad sería «×2» y «×1,25» sobre el coste pagado), **no cambia el resultado**: 2 / 167 / 9.831.

Es decir: la regla hoy no cuesta ni decide nada en esta población. Lo que hay que decidir es si quieres que su número signifique lo que dice el comentario («sobrevive a un coste doble»). Hoy no lo significa, por el slippage que entra arriba y no abajo.

### 3.11 R6 — El drawdown no se dispara al pasar a oos1

Hecho: `gate.scorecard.forma_value`

**Qué mide.** Cuánto mayor es el peor drawdown de oos1 comparado con el peor drawdown del build. Una curva sobreajustada suele ser suave en el build y áspera fuera.

**Cómo se calcula.** Se pega la curva diaria del build con la de oos1 (en dólares) y se parte por la fecha de corte.

```
drawdown máximo de un tramo = mayor caída desde un máximo anterior, dentro del tramo
forma_value = drawdown máximo de oos1 / drawdown máximo del build
```

Sólo se calcula para las que llegaron a esa criba de la cascada (3.979 de 10.000); el resto no tiene dato.

*Código:* `studies/screening/gate/screens.py:122-146`.

**Ejemplo numérico.** C, recalculado desde su curva diaria:

```
drawdown máximo en oos1  = 5.065,28 USD
drawdown máximo en build = 5.816,56 USD
forma_value = 5.065,28 / 5.816,56 = 0,871   → PASA (≤ 1,25)
```

A vale 0,538 y B 0,549 (valor guardado; su curva diaria ya no está en disco, ver 1.7). Un 0,54 dice que el peor bache de oos1 fue la mitad del peor bache del build.

Hay que leerlo con un matiz: el build de NIKKEI225 dura 8,3 años y oos1 4. En el doble de tiempo cabe un drawdown mayor sólo por azar, así que un cociente por debajo de 1 es lo esperable y no un mérito.

**El criterio cargado y por qué.** `pass: "<= 1.25"`, `limbo: "<= 1000"`: nunca descarta. El 1,25 es anterior al Council («R6–R8 no recalibradas», dice el fichero). El Council no la tocó en el consenso; un miembro propuso en la primera ronda sustituir 1,25 por ≤ 2 / 2 a 3 / > 3, con este argumento: un cociente tan estricto **selecciona drawdowns pequeños por suerte**. Los datos del paquete van en esa línea: el drawdown al percentil 95 de un Monte Carlo es 1,95 veces el observado.

**Cómo sería el resultado ideal.** Por debajo de 1,25 si los dos tramos duran parecido. Con tramos de distinta duración, sirve más mirar el drawdown en R de oos1 (regla 3.16).

**Si mueves este umbral.** 3.421 pasan y 6.579 quedan en LIMBO: 6.021 por no tener dato y sólo **558 por pasar de 1,25**. Cero descartes. Moverla no cambia el resultado: toda estrategia que hoy es PASA ya la cumple.

### 3.12 R7 — Años positivos en oos1

Hecho: `gate.scorecard.degradacion_years_positive`

**Qué mide.** En cuántos años naturales de oos1 la estrategia acabó ganando. Busca que el beneficio no venga de un solo año.

**Cómo se calcula.** Se toma la curva diaria de oos1, se suma el cambio de cada año natural y se cuentan los años con suma positiva.

*Código:* `studies/screening/analysis/decay.py:47` y `:57`; `studies/screening/gate/screens.py:92-119`.

**Ejemplo numérico.** C, desde su curva diaria:

```
2020:  +5.697,5      2021:  +212,8      2022:  −2.086,0      2023:  +865,6
años positivos = 3   → PASA (≥ 3)
```

A tiene 4 de 4 y B 3 de 4 (pierde en 2022). Con las operaciones de A agrupadas por año de cierre: 16.342, 12.117, 4.978 y 5.027 USD.

Lo que vale este dato: una moneda al aire (cada año, cara o cruz) saca 3 o más caras de 4 en 5 de las 16 combinaciones posibles, el **31 %** de las veces, y las 4 en una de 16, el 6 %. Y en C, el año 2021 «positivo» son 213 USD: 0,2R.

**El criterio cargado y por qué.** `pass: ">= 3"`, `limbo: ">= -1000"`: nunca descarta. Anterior al Council, no recalibrada. El «3» no distingue activos: son 3 de 4 años en NIKKEI225 y 3 de 5 en XAUUSD y forex, que es bastante más fácil (una moneda lo consigue el 50 % de las veces).

**Cómo sería el resultado ideal.** Todos los años positivos, o como mucho uno negativo y pequeño.

**Si mueves este umbral.** 3.913 pasan (649 con 4 años, 3.264 con 3); 6.087 en LIMBO (4.054 sin dato, 1.880 con 2 años, 153 con 1). Cero descartes; moverla no cambia el resultado de hoy.

### 3.13 R8 — El beneficio no viene de un solo trimestre

Hecho: `gate.scorecard.degradacion_concentration`

**Qué mide.** Qué parte del beneficio total de oos1 se hizo en el mejor trimestre.

**Cómo se calcula.**

```
concentración = beneficio del mejor trimestre natural / beneficio total de oos1
```

Si el total es cero o negativo no hay dato. Puede valer más de 1: el mejor trimestre ganó más de lo que la estrategia ganó en total, o sea, el resto del tiempo perdió.

*Código:* `studies/screening/analysis/decay.py:46` y `:58`.

**Ejemplo numérico.** C:

```
mejor trimestre (cuarto de 2020) = 3.020,8 USD
total de oos1                    = 4.689,85 USD
concentración = 3.020,8 / 4.689,85 = 0,644   → LIMBO (> 0,5)
```

Casi dos tercios de lo que C ganó en cuatro años lo ganó en tres meses. A vale 0,210 y B 0,222 (valor guardado).

La referencia: con 16 trimestres iguales, cada uno aportaría 1/16 = 0,0625. A, con 0,21, tiene un mejor trimestre de más de tres veces la media, que es normal.

**El criterio cargado y por qué.** `pass: "<= 0.5"`, `limbo: "<= 1000"`. Anterior al Council, no recalibrada. La línea de 0,5 coincide con una bandera roja de Chande (la mayor ganancia por encima del 40–50 % del beneficio). Un miembro del Council propuso medirlo por la mayor **operación** en lugar del mejor trimestre (≤ 0,4 / 0,4 a 0,5 / > 0,5); no entró en el consenso.

**Cómo sería el resultado ideal.** Por debajo de 0,25.

**Si mueves este umbral.** 2.011 pasan; 7.988 en LIMBO (4.060 sin dato; 1.961 con más de 1). Hay **una** estrategia con NO PASA: su concentración es 59.693, porque su beneficio total es de céntimos y el cociente se dispara; cae también por la t. Ese caso enseña que el `limbo: "<= 1000"` no es exactamente «nunca descarta». Moverla no cambia el resultado.

### 3.14 R9a — El peor día, en R

Hecho: `gate.scorecard.oos_worst_day_r`

**Qué mide.** La mayor pérdida de un solo día en oos1, **contando lo que la operación iba perdiendo mientras estaba abierta** (el flotante), no sólo lo que cerró. En fondeo es lo que manda: el límite de pérdida diaria se mide sobre el flotante.

**Cómo se calcula.** De la curva diaria de mínimos de SQX (el peor valor de la cuenta cada día):

```
peor día en R = mínimo de (valor de un día − valor del día anterior) / 1R
```

con 1R = 1.000 USD. Es negativo: −2 quiere decir que el peor día se llevó dos veces el riesgo de una operación.

*Código:* `studies/screening/analysis/floating.py:27-35`.

**Ejemplo numérico.** C. Su peor día fue el 7-06-2021:

```
valor el día anterior  = 21.207,60 USD
valor ese día (mínimo) = 19.464,05 USD
cambio = −1.743,55 USD  →  −1.743,55 / 1.000 = −1,74R   → PASA (≥ −3)
```

A vale −2,21R y B −2,43R (valor guardado).

Lo que significa en una cuenta de fondeo: si arriesgas el 1 % por R, el peor día de A es un −2,2 % de la cuenta; con un límite diario del 5 % queda margen. A −5R no quedaría ninguno.

**El criterio cargado y por qué.** `pass: ">= -3"`, `limbo: ">= -5"`; peor que −5R, NO PASA. La regla existe por tu prioridad (fondeo primero, manda el flotante); las líneas son anteriores a la medición. El Council aportó la referencia: en las estrategias robustas, el peor día mediano está entre **−1,8R y −2,3R**. A 1 % por R, el 15 % de las supervivientes rompería el 5 % diario; a 0,5 %, ninguna.

Disidencia: Taleb defendió en la primera ronda que el peor día y la peor operación deben **anotar** y no descartar, porque 175 operaciones no acotan la cola: que el peor día visto sea −2R no dice que el próximo no sea −6R (la «regla de tres»: si en `n` operaciones no has visto un suceso, su probabilidad puede ser todavía de hasta `3 / n`; con 196 operaciones, 1,5 % por operación, o sea, unas tres veces en las próximas 200). No entró en el consenso.

**Cómo sería el resultado ideal.** Entre −1R y −2,5R. Un peor día de −1R exacto con muchas operaciones merece sospecha en sentido contrario: puede ser que la curva no esté registrando el flotante.

**Si mueves este umbral.** 4.143 pasan, 5.016 LIMBO, 841 NO PASA; no es la única que descarta a ninguna. La mediana de la población es **−3,23R**: más de la mitad no llega a PASA. Bajar el descarte a −4R: 2 / 162 / 9.836 (pierdes 5). Quitarlo: sin cambio.

### 3.15 R9b — La peor operación en flotante, en R

Hecho: `gate.scorecard.oos_worst_trade_mae_r`

**Qué mide.** Lo máximo que una operación llegó a ir perdiendo mientras estaba abierta (su MAE, «máxima excursión adversa»), en R. Si el stop funciona como se diseñó, ninguna operación debería ir perdiendo mucho más de 1R.

**Cómo se calcula.**

```
peor MAE en R = mínimo, sobre las operaciones de oos1, de (MAE en USD) / 1R
```

*Código:* `studies/screening/analysis/floating.py:27-35`.

**Ejemplo numérico.** C. Es la misma operación de su peor día: larga, 7-06-2021 de 03:00 a 10:30, 93,63 lotes.

```
llegó a ir perdiendo  = 1.743,55 USD  →  −1,74R   → PASA (≥ −3)
cerró perdiendo       = 1.381,82 USD  →  −1,38R
```

Una operación dimensionada para perder 1R llegó a −1,74R: el stop se quedó corto en un 74 %, por un hueco o porque la salida no es un stop fijo. A vale −2,62R y B −2,52R (valor guardado).

**El criterio cargado y por qué.** `pass: ">= -3"`, `limbo: ">= -5"`; peor que −5R, NO PASA. Mismo origen y misma disidencia que 3.14.

**Cómo sería el resultado ideal.** Cerca de −1R. Todo lo que pase de −1,5R dice que el riesgo que crees estar tomando no es el que tomas.

**Si mueves este umbral.** 3.201 pasan, 5.087 LIMBO, **1.712 NO PASA**; es **la única que descarta a 18**. La mediana de la población es −3,72R: lo normal aquí es que la peor operación llegue a perder casi cuatro veces lo previsto.

| si el descarte fuera | PASA | LIMBO | NO PASA |
|---|---|---|---|
| −5R (hoy) | 2 | 167 | 9.831 |
| ninguno (Taleb: que anote) | 2 | 185 | 9.813 |
| −4R | 2 | 159 | 9.839 |

Y si la línea de PASA subiera a −2,5R, las dos PASA de hoy (A tiene −2,62R) bajarían a LIMBO: 0 / 169 / 9.831.

### 3.16 R9c — El drawdown frente a lo que gana en un año

Hecho: `gate.scorecard.oos_dd_over_net_year`

**Qué mide.** Cuántos años de beneficio medio se comería el peor drawdown. Es la pregunta del trader: «si mañana empieza el peor bache que he visto, ¿cuánto tardo en recuperarlo?».

**Cómo se calcula.**

```
drawdown máximo en R = mayor caída de la curva diaria desde un máximo anterior / 1R
neto por año en R    = suma del P/L de oos1 / años de oos1 / 1R

oos_dd_over_net_year = drawdown máximo en R / neto por año en R
```

Si el neto es cero o negativo, vale infinito.

*Código:* `studies/screening/analysis/floating.py:27-35`.

**Ejemplo numérico.** C, desde su curva:

```
máximo:  7.969,05 USD (31-05-2021)     mínimo posterior: 2.903,77 USD (19-12-2023)
drawdown máximo = 5.065,28 USD = 5,07R
neto por año    = 4.689,84 / 4 / 1.000 = 1,17R
cociente        = 5,07 / 1,17 = 4,32   → LIMBO (> 1,5)
```

C tardaría más de cuatro años de su ritmo medio en recuperar su peor bache; y ese bache seguía abierto al acabar oos1.

| | A | B | C |
|---|---|---|---|
| drawdown máximo (R) | 6,80 | 7,94 | 5,07 |
| neto por año (R) | 9,62 | 7,97 | 1,17 |
| **cociente** | **0,71** | **1,00** | **4,32** |

**El criterio cargado y por qué.** `pass: "<= 1.5"`, `limbo: "<= 1000"`. El Council la dejó sin descarte: «el drawdown frente al neto ya no falla». La referencia medida: el drawdown máximo mediano de las robustas está entre 3,1R y 5,1R. Hill da una regla parecida de los libros: el beneficio debe ser al menos el doble del drawdown.

**Cómo sería el resultado ideal.** Por debajo de 1: el peor bache se recupera en menos de un año. Y recuerda la cifra del Monte Carlo: el drawdown que debes esperar es cerca del doble del que has visto.

**Si mueves este umbral.** 671 pasan, 5.352 LIMBO y 3.977 NO PASA, de las que 3.957 son infinitos (neto ≤ 0, ya descartadas por 3.3). No es la única que descarta a ninguna. Moverla no cambia el resultado.

---

## 4. Lo que el paso 8 calcula y no juzga

El paso 8 lanza más estudios de los que tienen regla. Sus resultados se guardan y se ven en la ventana, pero **ninguno decide** el estado de una estrategia. Mismos seis apartados; donde digo «sin hechos en esa corrida» es que el estudio no dejó datos en el fichero de hechos del paso 8 de la corrida de ejemplo y no puedo dar un número.

### 4.1 El mono: ¿gana a entrar al azar?

Estudio: `monkey`. También es la criba `mono` de la cascada.

**Qué mide.** Si la estrategia gana más que un «trader al azar» que hace el mismo número de operaciones, del mismo lado, con las mismas duraciones y tamaños, pero **entrando en momentos sorteados**.

**Cómo se calcula.** Se sortean 2.500 traders al azar (2.000 en la criba de la cascada). Para cada uno se calcula la misma estadística que para la estrategia (neto, PF, Sharpe, retorno/drawdown, drawdown). El p-valor es:

```
p = (número de traders al azar que igualan o superan a la estrategia + 1) / (sorteos + 1)
```

Hay cuatro «peldaños», según lo que se le deja al azar: sólo el momento (`timing`), el momento y la duración, el momento y el tamaño, o todo (`free`). Sólo se calcula sobre oos1 (tu regla: trader al azar sólo fuera de muestra).

*Código:* `studies/screening/gate/monkey.py:33-82`; `studies/readings/monkey/README.md`.

**Ejemplo numérico.**

| | A | B | C |
|---|---|---|---|
| p, Sharpe, sólo el momento | 0,0004 | 0,0032 | 0,097 |
| p, neto, todo al azar | 0,0036 | 0,013 | 0,090 |
| p de la criba `mono` | 0,0015 | 0,0025 | 0,0975 |
| neto de los monos, media (USD) | 3.526 | 3.666 | 466 |

A da 0,0004 = 1/2.501: **ningún** mono de 2.500 la igualó; es el p más pequeño que el estudio puede dar. A C la iguala o supera uno de cada diez monos.

Un aviso sobre estas cifras: el mono reprecia las operaciones con su propio motor y le sale un neto de 45.464 USD para A, frente a los 38.465 de SQX. No he investigado esa diferencia.

**El criterio cargado y por qué.** Ninguno en `criteria.yaml`. En la cascada, la criba `mono` deja pasar con p ≤ 0,50, que no filtra nada (pasan las 3.979 que llegan). El Council lo dejó en anotar por lo medido: ganar al mono con p ≤ 0,05 da un lift de **+5 por cada 1.000** (301 contra 296): nada. Davey pide ganar al 70 % de los monos; es una vara distinta y más laxa.

**Cómo sería el resultado ideal.** p por debajo de 0,01 en los cuatro peldaños. Que sea igual de bajo en `timing` y en `free` dice que la ventaja está en **cuándo** entra, no en cuánto dura ni en el tamaño.

**Si mueves este umbral.** Si pidieras p ≤ 0,05 como regla, no cambiaría casi nada: de las 325 con t ≥ 1,65, 318 ya lo cumplen (las otras 7 no tienen dato). Y al revés no vale: 821 estrategias ganan al mono con p ≤ 0,05 y no llegan a t 1,65. El mono es más laxo que la t y no añade información encima de ella.

### 4.2 El espionaje de datos y la criba `familia`

Estudio: `snoopingScreen`; criba `familia` de la cascada.

**Qué mide.** La pregunta de 2.8 hecha a la población entera: habiendo probado miles, ¿hay **alguna** que gane de verdad a comprar y mantener? ¿Y cuáles?

**Cómo se calcula.** Dos pruebas de los libros, sobre toda la cosecha y contra comprar y mantener a igual riesgo: la de Hansen (SPA) contesta «¿hay alguna?» y la de Romano y Wolf (StepM) contesta «¿cuáles?». La criba `familia` hace algo más sencillo con los p-valores del mono, el método de Benjamini y Hochberg: se ordenan los p de menor a mayor y la número `k` se acepta si

```
p(k) ≤ 0,05 × k / m
```

con `m` el número de estrategias que entraron (aquí 3.979).

*Código:* `studies/screening/gate/monkey.py:85-104`; `studies/screening/snoopingScreen/README.md`.

**Ejemplo numérico.** Con m = 3.979, la primera necesita `p ≤ 0,05 / 3.979 = 0,0000126`. Pero el p más pequeño que puede dar un sorteo de 2.000 monos es `1 / 2.001 = 0,0005`: cuarenta veces mayor. Hay 9 estrategias con ese p mínimo; para que la novena entrara haría falta `p ≤ 0,05 × 9 / 3.979 = 0,000113`. No entra ninguna.

**La criba `familia` no puede nombrar a nadie con 2.000 sorteos y 3.979 candidatas**: haría falta que 40 estrategias o más tuvieran el p mínimo. Por eso su resultado en esta corrida es cero, y no dice nada de A, B ni C. De `snoopingScreen` no hay hechos en esa corrida.

**El criterio cargado y por qué.** Ninguno. Ambos anotan. La criba `familia` es «blanda» en la cascada: no corta el embudo.

**Cómo sería el resultado ideal.** Que la prueba de Hansen rechace («hay alguna») y la de Romano y Wolf nombre a unas pocas. En una población donde la mejor t (3,14) queda por debajo de lo que da el ruido (≈ 3,7), lo esperable es que no nombren a ninguna.

**Si mueves este umbral.** Convertirla en regla hoy descartaría las 10.000. Para que la criba pudiera decir algo harían falta unos 80.000 sorteos por estrategia (para que el p mínimo baje de 0,0000126): cuarenta veces el tiempo de máquina actual del mono.

### 4.3 La forma del beneficio

Estudio: `profitShape`.

**Qué mide.** Tres cosas de cómo está hecho el beneficio: si se concentra en pocas operaciones, si las operaciones son independientes entre sí (rachas), y si la curva tiene una rotura.

**Cómo se calcula.** Sobre la lista de operaciones: parte del beneficio que aportan las mayores ganadoras, autocorrelación del resultado (la `ρ` de 2.5) y una prueba de cambio de nivel en la curva. Detalle en `studies/readings/profitShape/README.md`.

**Ejemplo numérico.** Sin hechos en esa corrida. Lo que sí tengo de A: su `ρ` es −0,139 (2.5), o sea, sin rachas.

**El criterio cargado y por qué.** Ninguno. La propuesta de la primera ronda del Council de medir la concentración por la mayor operación (3.13) saldría de este estudio.

**Cómo sería el resultado ideal.** La mayor ganadora por debajo del 40 % del beneficio (Chande); `ρ` cerca de 0; sin rotura.

**Si mueves este umbral.** No medido: sin hechos no puedo contar cuántas caerían.

### 4.4 La calidad de la entrada

Estudio: `entryQuality`.

**Qué mide.** Si, justo después de entrar, el precio se mueve más a favor que en contra, comparado con entrar al azar a las mismas horas. Separa «la entrada es buena» de «la salida lo arregla».

**Cómo se calcula.** El e-ratio: recorrido máximo a favor dividido por recorrido máximo en contra, medido a varias distancias en barras desde la entrada, y lo mismo para entradas sorteadas a las mismas horas. También mide qué pasa si la entrada se retrasa una barra. Detalle en `studies/readings/entryQuality/README.md`.

**Ejemplo numérico.** Sin hechos en esa corrida.

**El criterio cargado y por qué.** Ninguno.

**Cómo sería el resultado ideal.** Un e-ratio por encima del de las entradas al azar desde las primeras barras, y que retrasar la entrada una barra no hunda el resultado (si lo hunde, la estrategia depende de un relleno exacto que en real no tendrás).

**Si mueves este umbral.** No medido.

### 4.5 La calidad de los datos

Estudio: `feedQuality`.

**Qué mide.** Si el beneficio depende de barras con datos defectuosos: huecos, picos, velas imposibles.

**Cómo se calcula.** Marca las operaciones que tocan una anomalía del histórico y compara su resultado con el del resto mediante una prueba de permutación (barajar las etiquetas y ver cuántas veces sale una diferencia igual o mayor). Detalle en `studies/data/feedQuality/README.md`.

**Ejemplo numérico.** Sin hechos en esa corrida.

**El criterio cargado y por qué.** Ninguno.

**Cómo sería el resultado ideal.** Que las operaciones que tocan anomalías sean pocas y no ganen más que las demás.

**Si mueves este umbral.** No medido.

### 4.6 Las otras columnas del spread

Estudio: `spread`. Dos de sus columnas tienen regla (3.4 y 3.9); el resto anota.

**Qué mide.** Cuánto se parece el coste del backtest al del mercado.

**Cómo se calcula.** Con el mismo repreciado de 3.4: el neto y el PF en tres versiones (SQX, al spread real, con slippage real), el spread real medio en las operaciones, el porcentaje de operaciones con tick real, y en qué percentil del spread real cae el spread plano de SQX.

**Ejemplo numérico.**

| | A | B | C |
|---|---|---|---|
| PF según SQX | 1,79 | 1,66 | 1,30 |
| PF al spread real | 1,73 | 1,59 | 1,21 |
| PF con slippage real | 1,63 | 1,49 | 1,09 |
| operaciones con tick real | 100 % | 99,5 % | 99,0 % |
| percentil del spread de SQX | 10,2 | 6,7 | 7,1 |

El spread de SQX (474,91 puntos de MT5) queda en el percentil 10 del real en las operaciones de A: el mercado cobraba más nueve de cada diez veces. El PF de C a coste real, 1,09, está muy por debajo del «PF de suerte» de 98 operaciones (1,52; ver 2.11).

**El criterio cargado y por qué.** Ninguno para estas columnas.

**Cómo sería el resultado ideal.** El spread de SQX en el percentil 50 o por encima (tu doctrina es exagerar el coste, no quedarte corto), y casi todas las operaciones con tick real.

**Si mueves este umbral.** Pedir «PF con slippage real ≥ 1» es la misma regla que 3.4 (lo cumplen las mismas 4.354). La decisión que este cuadro pone delante no es una regla: es subir el spread de la tarea de NIKKEI225. Coste medido de hacerlo con las estrategias ya construidas: 1.689 de las 5.946 que ganan dejarían de ganar; ninguna de las 169 vivas cae por ello.

### 4.7 Las otras columnas de la ventaja frente al coste

Estudio: `edgeCost`. `edge_mean` tiene regla (3.10); `edge_median` y `n` anotan.

**Qué mide.** Lo mismo que 3.10, pero con la mediana: lo que deja la operación **típica**, no la media.

**Cómo se calcula.** `edge_median = mediana del bruto / mediana del coste de hoy`, sobre build y oos1 juntos.

*Código:* `studies/readings/edgeCost/one.py:32-60`.

**Ejemplo numérico.**

| | A | B | C |
|---|---|---|---|
| `edge_mean` | 7,62 | 7,18 | 4,59 |
| `edge_median` | 5,83 | 0,92 | −0,76 |

Aquí A se separa de B. La operación típica de A gana casi seis veces el coste. La de B gana menos que el coste, y la de C pierde: su media sale de unas pocas operaciones grandes. Es el perfil de un sistema que sigue tendencias (muchas pérdidas pequeñas y pocas ganancias grandes), que no es malo en sí, pero hace que el resultado dependa de no perderse las grandes.

**El criterio cargado y por qué.** Ninguno.

**Cómo sería el resultado ideal.** Mediana y media del mismo signo y parecidas.

**Si mueves este umbral.** Si se pidiera `edge_median ≥ 1`: 1.447 de 10.000 no lo cumplen, entre ellas B. No he medido cuántas de las 169 vivas caerían. No lo propongo: castigaría a todo sistema de tendencia.

---

## 5. Cierre

### 5.1 Todas las reglas en una tabla

«Descarta sola» es a cuántas estrategias de las 10.000 da NO PASA esa regla y ninguna otra.

| regla | banda (M30) | descarta | descarta sola | ¿Council? |
|---|---|---|---|---|
| 3.1 `presencia_passed` | ≥ 1 | 0 (1.557 en el juez) | 0 (29) | no |
| 3.2 `sanidad_passed` | ≥ 1 | 142 | 7 | no |
| 3.3 `estaticas_value` | > 0 | 3.912 | 0 | mantenida |
| 3.4 neto al spread real | > 0 | 5.646 | 0 | no |
| 3.5 `drift_excess_t` | ≥ 2,33 / ≥ 1,65 | 9.674 | 2.472 | sí |
| 3.6 suelo en el build | ≥ 35 / ≥ 20 | 2.241 | 127 | sí |
| 3.7 techo en el build | ≤ 75 | 0 | 0 | sí |
| 3.8 operaciones/año oos1 | ≥ 15 / ≥ 10 | 95 | 0 | no |
| 3.9 operaciones en oos1 | ≥ 100, si no limbo | 0 | 0 | sí |
| 3.10 `edge_mean` | ≥ 2 / ≥ 1,25 | 653 | 0 | banda del paso 25 |
| 3.11 `forma_value` | ≤ 1,25, si no limbo | 0 | 0 | no |
| 3.12 años positivos | ≥ 3, si no limbo | 0 | 0 | no |
| 3.13 concentración | ≤ 0,5, si no limbo | 1 | 0 | no |
| 3.14 peor día | ≥ −3R / ≥ −5R | 841 | 0 | referencia medida |
| 3.15 peor MAE | ≥ −3R / ≥ −5R | 1.712 | 18 | referencia medida |
| 3.16 drawdown / neto anual | ≤ 1,5, si no limbo | 3.977 | 0 | sí (sin descarte) |

Tres reglas hacen todo el trabajo: la t, el suelo de 20 y la peor MAE. Las demás, en esta población, no cambian el estado de ninguna estrategia.

### 5.2 El resultado combinado hoy

| | PASA | LIMBO | NO PASA |
|---|---|---|---|
| como juzga el código hoy | 2 | 138 | 9.860 |
| cada estrategia con sus hechos | 2 | 167 | 9.831 |
| lo mismo, si fuera H1 | 0 | 169 | 9.831 |

Las dos PASA son `Strategy 4.9.301` (A) y `Strategy 4.8.266`. La diferencia entre las dos primeras filas son las 29 LIMBO que se pierden por el fallo de contabilidad de 3.1.

**Y con `dev.on: true` nada de esto es lo que sigue adelante.** Hoy el fichero tiene el modo de desarrollo encendido en el paso 8, con `sample: 3`: se sortean **3** estrategias, y sólo ellas pasan al paso 9, **sean PASA, LIMBO o NO PASA**. El sorteo no mira el veredicto. En la corrida de ejemplo el sorteo era de 10, y las 10 que siguieron son NO PASA con las reglas de hoy. Mientras `dev.on` esté encendido, las bandas de este documento se calculan y se anotan, pero no filtran.

### 5.3 Decisiones abiertas

Cada una con lo que cuesta al lado de lo que gana.

1. **Que el juez encuentre los hechos cuando la identidad cambia.** Gana: 29 LIMBO que hoy se descartan sin motivo (el 17 % de las vivas). Cuesta: un cambio de código; ninguna estrategia. No es una decisión de criterio, es un fallo.
2. **Apagar `dev.on` cuando acabes de probar la cadena.** Gana: que las reglas filtren. Cuesta: el paso 9 recibe 169 estrategias en lugar de 3.
3. **La línea de descarte de la t (1,65).** Bajarla a 1,28: +258 LIMBO, con el doble de falsos positivos nominales y un lift no medido. Subirla a 2,0: −115, y la potencia baja de 63 % a 49 % (s = 0,15, 175 operaciones). Mi lectura: dejarla; es la única línea con lift medido.
4. **Aplicar la corrección del término de deriva.** Gana: quitar cerca del 60 % de un sesgo de hasta ±0,27 en la t, que hoy trata distinto a largos y cortos. Cuesta: no medido en estrategias; cambia qué 325 quedan por encima de 1,65.
5. **El suelo duro de 20 al año.** Quitarlo: +127 LIMBO (entre ellas D, la de mejor t). Ponerlo en 35: −120. La calidad medida no cambia con el suelo (17,1 contra 16,8); lo que cambia es la potencia de la prueba. Mi lectura: dejarlo en 20.
6. **La variante de Munger** (PASA desde 20 al año si t ≥ 2,33). 14 PASA en vez de 2. No cambia qué sigue adelante; sólo importa si más abajo tratas distinto a PASA y a LIMBO.
7. **Que el peor día y la peor MAE anoten en vez de descartar (Taleb).** Gana: +18 LIMBO. Cuesta: siguen adelante estrategias cuya peor operación llegó a −5R o peor, que en fondeo a 1 % por R rompen el límite diario. Mi lectura: mantener el descarte mientras el objetivo sea fondeo.
8. **Qué debe significar `edge_mean`.** Hoy mezcla build y oos1, y su «2» no es «sobrevive a un coste doble». Arreglarlo (slippage también en el denominador, o líneas en 3,4 y 2,125) cuesta **cero estrategias** en esta población. Gana: que el número diga lo que dice su comentario, y que no engañe en un activo con costes más altos.
9. **El spread de la tarea de NIKKEI225.** Está en el percentil 10 del real. Subirlo es tu doctrina de costes; con lo ya construido no descarta a ninguna de las 169.
10. **H1 y H4.** H1 no puede PASAR en el paso 8 (el lift medido es +19, casi cero). H4 tiene las líneas sin recalibrar y el LIMBO en 1,65 donde la evidencia proponía 1,9. No hay población H1 ni H4 en esta corrida para ponerles coste.
11. **Las reglas que nunca deciden** (3.3, 3.4, 3.7, 3.8, 3.10 a 3.14, 3.16). Quitarlas no cambia nada hoy. Mi lectura: dejarlas; son redes para otras poblaciones y no cuestan.

Y la advertencia que está por encima de todas: las bandas son **provisionales**. El acuerdo unánime del Council fue que ninguna línea se congela hasta que una población sin ventaja (un nulo) recorra la cadena entera, y que sólo cuentan las muestras nuevas. Con lo medido hoy, PASAR el paso 8 hace a una estrategia candidata: seis de cada diez de las que superan 1,65 acaban perdiendo en oos2.
