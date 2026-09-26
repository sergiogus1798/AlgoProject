# Calidad del feed M1 — lo que el módulo necesita que decidas, con mi propuesta para cada cosa

**Fecha:** 2026-09-26 · **Encargo:** `docs/encargos/17-calidad-del-feed.md` (paso 4 aviso, paso 8
criba) · **Sustituye a** la consulta del mismo día, que preguntaba lo mismo a un agente externo.

**Qué es esto.** El módulo de calidad del feed no se puede construir hasta que alguien tome
dieciséis decisiones: números y criterios. La consulta los preguntaba en abstracto. Aquí van **medidos sobre el
propio feed** —XAUUSD, USDJPY y EURUSD, sin mirar ninguna estrategia, como exige la regla— y con una
propuesta concreta para cada uno. Tú sólo tienes que decir **sí, o cambia esto**.

---

## 0 · Tu hoja de respuestas — una línea por decisión

| # | qué hay que decidir | mi propuesta | ¿de acuerdo? |
|---|---|---|---|
| 1 | qué movimiento se mira | **el cierre y la mecha, por separado** | ☐ |
| 2 | contra qué se mide «grande» | **la volatilidad típica de esa hora de esa semana, en las últimas 52 semanas** | ☐ |
| 3 | `K`, cuántas veces esa volatilidad | **20** | ☐ |
| 4 | `m`, en cuántos minutos tiene que volver | **3** | ☐ |
| 5 | cuánto tiene que volver | **80 % del salto** | ☐ |
| 6 | picos que no vuelven | **se cuentan aparte, no entran en la atribución** | ☐ |
| 7 | `L`, minutos seguidos idénticos = congelado | **10**, igual para todos los símbolos | ☐ |
| 8 | horas que no cuentan para congelado | **fuera de sesión y la franja 23:00–01:59 del feed** (rollover) | ☐ |
| 9 | hueco mínimo | **5 minutos, dentro de sesión** | ☐ |
| 10 | festivos | **deducidos del feed**: si todos los símbolos callan el día entero, es cierre | ☐ |
| 11 | cuándo una operación «toca» una anomalía | **las velas de su timeframe que usa**: señal, entrada y salida | ☐ |
| 12 | cuándo salta la alarma | **test de permutación, p < 0,01, con al menos 10 operaciones marcadas** | ☐ |
| 13 | métricas recalculadas sin las marcadas | **no se enseñan**: sólo «% del beneficio en riesgo» | ☐ |
| 14 | qué hace la alarma en el paso 8 | **configurable, `marcar` por defecto** (como el edge por coste) | ☐ |
| 15 | umbrales por símbolo o globales | **globales** en unidades relativas | ☐ |
| 16 | cómo se comprueba que el detector funciona | **picos sintéticos inyectados (imprescindible) + revisar a mano los 20 más extremos** | ☐ |

Si marcas todo, el módulo se puede construir tal cual. Lo que no marques, dime el número que
quieres; la sección 2 dice qué cambia con cada opción.

---

## 1 · Lo que dice el feed — cinco hallazgos que deciden casi todo

Medido hoy sobre las velas M1 de `~/Desktop/AlgoData/bars/`, de 2003-05 a 2026-09
(7,9 M velas del oro, 8,7 M de cada par).

### 1.1 · Las colas son tan gordas que la campana de Gauss no sirve para nada

| cuántas veces la volatilidad típica | lo que esperaría una normal | XAUUSD | USDJPY | EURUSD |
|---|---|---|---|---|
| 5 | 4 | 228.011 | 138.910 | 120.531 |
| 8 | 0 | 54.287 | 33.538 | 26.410 |
| 10 | 0 | **22.660** | **17.012** | **12.515** |
| 20 | 0 | **1.379** | **2.251** | **1.291** |
| 30 | 0 | 325 | 822 | 343 |

*Cierre contra cierre de velas M1 contiguas; la escala es la desviación mediana (MAD × 1,4826) de su
hora de la semana, sobre toda la historia.*

**Qué significa.** Elegir `K` «para que sólo salte una vez en mil años con datos normales» no vale:
con `K` = 10 salen 22.660 velas del oro, casi 1.000 al año. Hay que elegir `K` mirando **cuántas marca
al año**, no una probabilidad teórica.

### 1.2 · Casi todo lo extremo es real, no un error

Los doce movimientos más grandes de USDJPY son, casi todos, días de la historia: el terremoto de
Japón (16-03-2011), la intervención del BoJ (31-10-2011), los tipos negativos (29-01-2016), el
Brexit (24-06-2016) y el *flash crash* del yen (03-01-2019). En el oro, el desplome de abril de 2013,
el *flash crash* del 09-08-2021 y la volatilidad de principios de 2026.

**Sólo uno tiene toda la pinta de tick malo:** USDJPY el **01-01-2009 a las 19:43**, −1,90 % y
+1,92 % tres minutos después, en Año Nuevo, con el mercado vacío.

**Qué significa.** El detector encontrará, sobre todo, **sucesos extremos reales**, y no hay forma
de separar un *flash crash* auténtico de un tick malo por su forma: los dos saltan y vuelven (el
Brexit en USDJPY volvió el 87 % en tres minutos; el *flash crash* del oro, el 79 %). **Y no hace
falta separarlos:** una estrategia que gana su dinero en esos minutos no tiene un edge repetible,
venga el pico de un error o de un pánico. El módulo mide *cuánto beneficio depende de minutos
anómalos*, sean de la causa que sean.

### 1.3 · Una escala fija confunde un año volátil con un año de errores

Con la escala calculada sobre toda la historia, el oro marca 33 picos (`K` = 10) en 2018 y
**2.758 en los nueve meses de 2026**. No es que 2026 tenga 80 veces más errores: es que el oro está
mucho más volátil. De ahí la propuesta 2: la escala de cada hora tiene que ser **la de las últimas
52 semanas**, no la de 23 años.

### 1.4 · Los primeros años del oro son otro feed

| | 2003–2005 | 2006–2012 | 2013–2025 |
|---|---|---|---|
| huecos de ≥ 5 min entre semana, XAUUSD, por año | **5.800–11.600** | 540–2.100 | **~210** |

Los ~210 huecos al año desde 2013 son **uno por día de mercado**: la pausa diaria del oro, no un
fallo. Antes de 2006 el feed del oro tiene agujeros por todas partes. **Esto ya es un resultado:**
cualquier tramo de construcción que empiece antes de 2006 en el oro se está construyendo sobre
datos peores. Hoy XAUUSD construye desde 2008 (`assets/_policy.yaml`), así que no le afecta.

### 1.5 · La hora del feed es UTC+2, y su hora 0 es el rollover

El *flash crash* del yen fue a las 22:35 UTC del 2 de enero de 2019, y en el feed sale a las 00:35
del 3 de enero. Las velas planas (`H == L`) se concentran justo ahí: el **10 %** de las velas de la
hora 0 de USDJPY son planas, contra el 0,4 % a media sesión europea. Son el mercado parado en el
rollover de Nueva York, no un feed caído. De ahí la propuesta 8.

---

## 2 · Cada decisión, con lo que cambia según elijas

### 1 · Qué movimiento se mira — cierre y mecha, por separado

Un tick malo muchas veces sólo estira la **mecha**: el cierre queda normal. Con `K` = 10, en el oro
la mecha marca 8.456 velas y el cierre 22.660; no he medido cuántas coinciden, y el módulo debe
informar las dos columnas y su solape. Si
sólo miras el cierre, se te escapan los ticks que tocan un stop o disparan una orden stop sin cambiar
el cierre — y en el paso 24 las estrategias llevarán stop.

### 2 · La escala — la hora de la semana, últimas 52 semanas

Por qué la hora: el oro no se mueve igual a las 14:30 de Nueva York que a las 3 de la
madrugada, y una escala única marcaría las noticias de la tarde y nunca la madrugada. Por qué 52 semanas: con 60 velas por hora, son ~3.100 observaciones por casilla, bastante
para una mediana estable, y lo bastante corto para seguir un cambio de régimen como el de 2026
(hallazgo 1.3). **Si prefieres 26 semanas**, el detector se adapta antes, pero es más ruidoso en
las horas muertas.

### 3 · `K` = 20

Con `K` = 20 el oro da unos **60 picos al año** (1.379 en 23 años), el yen unos 100 y el euro unos 55.
Con `K` = 10, de 500 a 1.000 al año cada uno: demasiados para que la atribución signifique algo,
porque casi toda operación tocaría alguno. Con `K` = 30, de 15 a 35 al año: se pierde el tamaño de
suceso que aún puede decidir una operación. **El criterio que propongo para fijarlo**, y no a ojo: el
menor `K` con el que la mediana de picos por año de los años tranquilos (2013–2019) quede por
debajo de **uno por semana** en los tres símbolos:

| mediana de picos al año, 2013–2019 | `K` = 10 | 12 | 15 | **20** | 25 |
|---|---|---|---|---|---|
| XAUUSD | 215 | 121 | 63 | **24** | 11 |
| USDJPY | 310 | 187 | 94 | **38** | 26 |
| EURUSD | 199 | 117 | 55 | **20** | 11 |

Con `K` = 15 los tres aún pasan de 52 al año; con `K` = 20 los tres quedan por debajo. **Sale 20.**

### 4 y 5 · Pico-y-vuelta: `m` = 3 minutos, 80 % del salto

| picos de `K` = 20 que vuelven ≥ 80 % en… | XAUUSD | USDJPY | EURUSD |
|---|---|---|---|
| 1 minuto | 69 | 188 | 82 |
| **3 minutos** | **239** | **447** | **209** |
| 5 minutos | 356 | 603 | 281 |
| total de picos | 1.379 | 2.251 | 1.291 |

No hay meseta: cuanto más esperas, más vuelven, y a partir de unos minutos lo que vuelve ya es
mercado, no error. Tres minutos es el punto en que un tick malo ya se ha corregido en cualquier feed
razonable; es una convención, y lo digo como tal. Eso deja en el oro **unos 10 picos-y-vuelta al
año**: una cantidad que se puede revisar a mano.

### 6 · Picos sin vuelta — aparte

Un pico que no vuelve es, casi siempre, una noticia (hallazgo 1.2). Se cuenta en el informe del
símbolo como «movimiento extremo» y no entra en la atribución. **Si prefieres que entren**, el
módulo medirá «beneficio que depende de noticias», que es otra pregunta.

### 7 y 8 · Congelado: 10 minutos idénticos, fuera del rollover

| rachas de OHLC idénticos, en velas seguidas | XAUUSD | USDJPY | EURUSD |
|---|---|---|---|
| ≥ 5 minutos | 161 | 978 | 654 |
| **≥ 10 minutos** | **16** | **77** | **109** |
| ≥ 30 minutos | 1 | 2 | 0 |

Con `L` = 10 quedan pocas rachas en los tres, así que no hace falta un `L` por símbolo. **Un dato que
llama la atención:** en EURUSD, 85 de las 109 rachas caen en 2021–2023 (23, 20 y 42 al año, contra
0–5 los demás años). Eso huele a un episodio del proveedor, y es justo lo que el detector debe
enseñar. Las velas planas sueltas **no** cuentan como congelado: se concentran en el rollover
(hallazgo 1.5) y son mercado quieto.

### 9 y 10 · Huecos: 5 minutos en sesión, festivos deducidos del feed

Desde 2013, entre semana, el oro tiene ~210 huecos de ≥ 5 minutos al año, uno por día: la pausa
diaria. USDJPY y EURUSD, 50–80 al año. La regla que propongo distingue tres cosas:

- **todos los símbolos callan el día entero** → cierre de mercado (festivo), no se marca;
- **todos callan un rato, en hora de sesión** → caída del proveedor: **se marca**, porque es
  justo el fallo común que un calendario deducido del feed escondería;
- **calla uno solo ≥ 5 minutos en su sesión** → hueco de ese símbolo, se marca. La pausa diaria del
  oro tiene que quedar fuera de su sesión declarada (`XAUUSD_ftmo`); si no lo está, saldrán
  ~210 falsos huecos al año y el primer uso del módulo lo delatará.

### 11 · Cuándo una operación «toca» una anomalía — las velas de su timeframe

La estrategia no ve velas M1: ve velas H1 o M30 construidas con ellas. Un pico a las 10:37 cambia el
máximo de la vela de las 10:00 y puede **decidir la entrada** aunque ocurra 23 minutos antes. Por eso
se marca la operación si la anomalía cae dentro de **la vela de la señal, la de la entrada o la de la
salida**. Además, en una columna aparte, **durante** la operación; esa columna sólo cuenta cuando la
estrategia lleve stop (paso 24). Mirar la ventana entera de los indicadores (una media de 200 velas)
marcaría casi todo y no distinguiría nada.

### 12 · Cuándo salta la alarma — permutación, p < 0,01, mínimo 10

La pregunta es: ¿las operaciones marcadas ganan más que un grupo cualquiera del mismo tamaño? Se
barajan las etiquetas 10.000 veces y se cuenta cuántas veces un grupo al azar gana tanto como el
marcado. Por qué así y no con el cociente «cuota de beneficio / cuota de operaciones»: el cociente
explota cuando el beneficio total es casi cero, y con 3 operaciones marcadas cualquier cociente es
ruido. El listón es p < 0,01 porque esto se corre sobre cientos de estrategias: con 0,05, una de cada
veinte saltaría por azar. Con menos de 10 marcadas, el informe dice «insuficiente» y no juzga. Se usa
el beneficio **neto**.

### 13 · Métricas sin las operaciones marcadas — no se enseñan

Un Sharpe «sin las operaciones malas» es una invitación a quedarse con él, y eso es justo la limpieza
prohibida. El informe dice **qué parte del beneficio está en riesgo** y si la alarma salta; nada más.
El encargo original pedía recalcularlas: **esto lo decides tú**, y si las quieres, saldrán rotuladas
«diagnóstico, no es el resultado».

### 14 · Qué hace la alarma en el paso 8 — configurable, `marcar` por defecto

El mismo criterio que el edge por coste. Descartar sin remedio sería tentador (una estrategia que
gana con ticks malos no debería seguir nunca), pero el hallazgo 1.2 dice que casi todo lo que el
detector marca es **real**: descartar automáticamente mataría estrategias que ganaron en un día
histórico de verdad. Que lo decidas tú en cada corrida.

### 15 · Globales en unidades relativas

`K` se mide en múltiplos de la volatilidad de la propia hora; `m` y `L` en minutos. Con eso, los tres
símbolos dan recuentos del mismo orden (tablas de arriba), así que sirven los mismos números para
todos. Un símbolo se sale de la regla sólo si su tabla de sensibilidad lo pide, y se escribe como
excepción declarada.

### 16 · Cómo se sabe que funciona — inyección sintética, y los 20 peores a mano

- **Inyección sintética — imprescindible.** Se meten picos y rachas de tamaño conocido en una copia
  del feed y se mide cuántos encuentra y cuántos inventa. Es la única forma de saber qué se le
  escapa.
- **Revisar a mano los 20 más extremos** contra la historia (ya he hecho una primera pasada, §1.2):
  sirve para comprobar que no marca tonterías, pero no dice qué se le escapa.
- **Un segundo proveedor**: no lo hay. El Brent viene de FTMO y no está en Dukascopy.

---

## 3 · Lo que el planteamiento no tenía, y conviene añadir

1. **Los primeros años del oro** (hallazgo 1.4) no son un problema de anomalías sueltas: son un feed
   distinto. Propongo que el aviso del paso 4 diga el **año a partir del cual el feed es estable**, y
   que el preflight avise si la ventana de construcción de un símbolo empieza antes.
2. **Los episodios del proveedor** (EURUSD 2021–2023) se ven mejor contando **por mes**, no por año:
   el informe debería tener esa tabla.
3. **La mecha y las órdenes stop.** Hoy las estrategias entran a mercado. Si una plantilla usa órdenes
   stop o límite, un tick malo en la mecha **llena la orden**: esas estrategias deberían mirar la
   columna de la mecha antes que la del cierre.

## 4 · Cómo se midió

Script de un solo uso sobre `core.barstore.source`, velas M1 contiguas (ningún retorno cruza un
hueco), escala por hora de la semana calculada sobre toda la historia. Es la versión de exploración:
el módulo usará la de 52 semanas (propuesta 2), que dará recuentos más bajos en los años volátiles.
Ninguna estrategia, ninguna operación y ningún resultado se ha mirado para escribir esto.
