# Consulta · Calidad del feed M1 — qué es una vela «mala» y cuándo pesa en una estrategia

**Fecha:** 2026-09-26 · **Estado:** abierto, nada implementado · **Encargo de origen:**
`docs/encargos/17-calidad-del-feed.md`

> **Para el agente consultado.** Este documento es autocontenido: no necesitas acceso al
> repositorio. Se te pide **opinión razonada** sobre un conjunto de decisiones de diseño que hay que
> cerrar **antes** de construir nada y, sobre todo, antes de mirar ningún resultado. Contesta en el
> formato de la §6. Si una pregunta está mal planteada, dilo: es tan útil como una respuesta.

---

## 1 · El contexto, en diez líneas

- Un generador genético (StrategyQuant X) construye miles de estrategias automáticas sobre datos
  **M1** y se queda con las que mejor backtest dan. Luego una cadena de ~25 pasos intenta matar las
  que tienen suerte en vez de ventaja.
- Los datos M1 vienen de **un único proveedor, Dukascopy**, para todo salvo el Brent. **No hay un
  segundo feed** con el que cruzar: si una vela está mal, nada fuera del propio fichero lo delata.
- Símbolos en uso: **XAUUSD** (oro, M30), **USDJPY** (H1), y como mercados de contraste XAGUSD y
  ocho pares de forex (EURUSD, GBPUSD, USDCHF, AUDUSD, USDCAD, EURJPY, GBPJPY, AUDJPY, CADJPY).
  Brent sale de otro proveedor (FTMO).
- Las estrategias actuales **no llevan stop ni target**: salen por número de velas (~75 %), por
  señal (~20 %) o al cierre del viernes (~5 %). En el paso 24 del flujo se les añadirá un stop fijo
  en unidades de ATR.
- Las estrategias operan en su timeframe (M30, H1), pero **SQX simula sobre el M1** y ejecuta a la
  apertura de la vela siguiente a la señal (medido: correlación 0,999985 con esa convención).

**El riesgo que motiva todo esto:** un buscador genético es un detector excelente de anomalías.
Si en 2011 hay un tick erróneo que dispara el oro 30 $ durante un minuto, la búsqueda puede
encontrar la regla que entra justo antes — y esa estrategia pasará el backtest con nota.

## 2 · Lo ya medido — el punto de partida

🔬 Sobre `XAUUSD_DukasM1_Infinox`, 2026-09-24:

| | |
|---|---|
| barras M1 | **7.949.285**, de 2003-05-05 a 2026-09-22 |
| inconsistencias OHLC (`H < max(O,C)`, `L > min(O,C)`, `H < L`) | **0** |
| barras planas (`High == Low`) | **40.097** — el **0,50 %** |

Consecuencia: la comprobación de consistencia OHLC no va a encontrar nada. El valor está en **picos,
precios congelados y huecos**, y en **atribuirlos** a las operaciones.

Sin medir todavía: la distribución de retornos M1 por símbolo y por hora, cuántas velas planas caen
en horario activo frente a madrugada o fin de semana, y la calidad por año (se sospecha que los
primeros años de Dukascopy son peores).

## 3 · Lo que se va a construir

Dos mitades, en dos sitios distintos del flujo — **esto ya está decidido**:

| mitad | qué hace | dónde va |
|---|---|---|
| **Detección** | marca las velas sospechosas de un símbolo; no depende de ninguna estrategia | se calcula una vez por símbolo al actualizar datos, y el **paso 4 (preflight)** avisa: «este símbolo tiene N anomalías por año» |
| **Atribución** | para cada estrategia, qué parte de su beneficio sale de operaciones que tocan una anomalía | **paso 8**, junto a la criba fuera de muestra, **antes** de gastar CPU en los pasos caros; mira el tramo de construcción (IS) y el fuera de muestra (OOS) |

**Principio no negociable.** Marcar operaciones y recalcular sin ellas es un **diagnóstico**, nunca
una limpieza: quedarse con el backtest «sin las operaciones malas» es sobreajuste con otro nombre.
Lo que el informe dice es *cuánto de lo que ves podría no ser real*.

**Y la regla que da sentido a esta consulta:** todos los umbrales se fijan **antes** de ver qué
operaciones tocan anomalías, y se justifican con **la estadística del propio feed**, no con los
resultados de las estrategias. Un umbral elegido después de ver cuánto beneficio se va es un
umbral ajustado hasta que dé lo que uno quería.

## 4 · Las preguntas

Cada una lleva: qué decide · las opciones que vemos · una propuesta de partida (**no** decidida) ·
lo que te pedimos.

### 4.1 · Picos — el umbral `K`

**Qué decide.** Cuándo un movimiento de una vela es «demasiado grande»: `|r_t| > K · escala_local`.

**Sub-decisiones:**

a. **Qué retorno.** Cierre contra cierre, o el **rango de la vela** (`H − L`, o `H − max(O,C)` y
   `min(O,C) − L`). Un tick malo muchas veces sólo deforma la **mecha**: el cierre queda normal y
   un detector de cierre a cierre no lo ve.
b. **Qué escala.** MAD × 1,4826 (robusta) sobre una ventana móvil — ¿de cuántas velas? — o una
   escala **por hora del día**, porque la volatilidad del M1 a las 14:30 de Nueva York no es la de
   las 03:00 de Asia. Una escala global confundiría noticias con errores y madrugadas con picos.
c. **Qué `K`.** Con colas gruesas (curtosis alta en M1), `K` = 5 marca muchísimo; `K` = 10 puede
   dejar pasar errores reales.

**Propuesta de partida:** mecha y cuerpo por separado, escala MAD por hora del día y día de la
semana sobre una ventana expansiva, `K` a fijar con la tabla de §4.9.

**Te pedimos:** qué retorno, qué escala y qué criterio para fijar `K` a partir de la propia
distribución (no un número a ojo).

### 4.2 · Pico-y-vuelta — la ventana `m`

**Qué decide.** La firma del tick malo no es el pico: es **el pico que se deshace enseguida**. Un
movimiento real de noticias se queda; un error vuelve.

**Sub-decisiones:**

a. **`m`**: en cuántas velas tiene que volver (1, 3, 5 minutos).
b. **Cuánto tiene que volver**: ¿el 80 % del salto? ¿el 100 %?
c. **Un pico sin vuelta**, ¿se marca como anomalía de otra clase, o no se marca?

**Propuesta de partida:** `m` = 3, vuelta ≥ 80 %, y los picos sin vuelta en una clase aparte que
se informa pero no entra en la atribución.

**Te pedimos:** valores y el argumento. En especial: ¿cómo se distingue un pico-y-vuelta erróneo de
un *flash crash* real (que también vuelve) — y, si no se puede distinguir, importa?

### 4.3 · Precio congelado — la racha `L`

**Qué decide.** Cuántas velas seguidas iguales hacen un precio «congelado» (feed caído que repite
el último valor).

**Sub-decisiones:**

a. **Qué es «igual»**: OHLC idénticos entre velas consecutivas, o vela plana (`H == L`), o las dos.
b. **`L`**: 5, 10, 30 minutos.
c. **«Horario activo»**: cada activo declara su sesión (`XAUUSD_ftmo`, `USDJPY_ftmo`). ¿Basta con
   excluir fuera de sesión, o hay que excluir también la hora del rollover diario (~17:00 Nueva
   York), cuando el mercado real está casi parado?

**Propuesta de partida:** OHLC idénticos, `L` = 10, dentro de sesión y fuera de la hora de rollover.

**Te pedimos:** valores, y si `L` debería depender del símbolo (el EURUSD se congela menos que el
CADJPY).

### 4.4 · Huecos — minutos que faltan

**Qué decide.** Qué ausencia de velas es un fallo y cuál es el mercado cerrado.

**Sub-decisiones:**

a. **Calendario de festivos**: ¿de dónde? No tenemos uno declarado. Opciones: una librería de
   calendarios de mercado, inferirlo del propio feed (días en que *todos* los símbolos callan), o no
   usarlo y aceptar falsos positivos en festivos.
b. **Hueco mínimo**: 1 minuto suelto sin velas es normal en madrugada de un par poco líquido.
c. **Zona horaria del servidor**: el feed va en hora del broker; los festivos, en hora local de cada
   mercado.

**Propuesta de partida:** inferir los cierres del propio feed (si ningún símbolo tiene velas, es
cierre), hueco mínimo de 5 minutos en sesión.

**Te pedimos:** si inferir el calendario del feed es aceptable o esconde fallos comunes a todos los
símbolos (una caída del proveedor también calla a todos a la vez).

### 4.5 · Cercanía — la ventana `w`

**Qué decide.** Cuándo una operación «toca» una anomalía.

**El matiz que complica esto:** la estrategia no lee velas M1, lee velas H1 construidas con ellas.
Un pico a las 10:37 cambia el máximo de la vela H1 de las 10:00, y si la señal usa ese máximo, la
anomalía **decide la entrada** aunque caiga 23 minutos antes de ella.

**Opciones:**

a. `±w` velas **M1** alrededor de la entrada y de la salida (lo que dice el encargo original).
b. Las velas **del timeframe de la estrategia** que intervienen: la de la señal, la de la entrada y
   la de la salida.
c. Toda la ventana de lectura de sus indicadores (una media de 200 velas H1 abarca 8 días): exacto
   pero casi todo quedaría marcado.
d. Además, **durante** la operación: un pico en contra a mitad de camino no cambia nada sin stop,
   pero con el stop del paso 24 sí.

**Propuesta de partida:** (b), más «durante la operación» en una columna aparte que sólo se usa si
la estrategia lleva stop.

**Te pedimos:** cuál, y si (b) deja fuera algún caso que importe.

### 4.6 · Cuándo la atribución es una alarma

**Qué decide.** El resultado del estudio: comparar la **cuota del beneficio** de las operaciones
marcadas contra su **cuota del número de operaciones**. Un 2 % de operaciones que aporta el 40 % del
beneficio es un hallazgo; un 2 % que aporta un 2 %, no.

**Sub-decisiones:**

a. **La métrica**: el cociente `cuota de beneficio / cuota de operaciones`, la diferencia, o un test
   (¿son las marcadas significativamente mejores que las no marcadas? — permutación de etiquetas).
b. **Mínimo de operaciones marcadas** para decir nada: con 3 marcadas, cualquier cociente es ruido.
c. **Beneficio neto o bruto**, y qué hacer si el beneficio total es negativo o casi cero (el cociente
   explota).
d. **Qué pasa con las métricas sin ellas** (Sharpe, PF, Ret/DD recalculados): ¿se informan, o
   invitan justo a la limpieza que está prohibida?

**Propuesta de partida:** test de permutación (¿las marcadas ganan más de lo que ganaría un
subconjunto aleatorio del mismo tamaño?), mínimo 10 marcadas, P/L neto.

**Te pedimos:** la métrica y el listón, con su argumento.

### 4.7 · La acción en el paso 8

**Qué decide.** Si una estrategia salta la alarma de §4.6, ¿se **descarta** o sólo se **marca** y
sigue?

Precedente en este mismo proyecto: el estudio de edge por coste (paso 8 también) lo deja como
**parámetro de configuración** — `marcar` o `descartar` —, que decide el dueño en cada corrida.

**Te pedimos:** si hay un argumento para que aquí no sea configurable (p. ej. porque una estrategia
que gana por ticks malos no debería seguir nunca).

### 4.8 · Umbrales globales o por símbolo

Si `K`, `L` y `m` se expresan en unidades de la propia distribución (múltiplos de MAD, percentiles),
pueden ser **globales**. Si se expresan en unidades absolutas, tienen que ser **por símbolo**. El oro,
el yen y los índices tienen microestructuras distintas.

**Te pedimos:** global en unidades relativas, por símbolo, o global con excepciones declaradas.

### 4.9 · Cómo se fijan los números sin mirar resultados

La propuesta de procedimiento es: para cada símbolo, una **tabla de sensibilidad del detector** —
cuántas velas marca cada combinación de `K`, `m`, `L` por año y por hora —, el dueño la ve **sin
ninguna estrategia al lado**, fija los valores, y sólo entonces corre la atribución.

**Te pedimos:** si este procedimiento es suficiente, y qué criterio usarías sobre esa tabla (un
codo en la curva de recuento, una tasa esperada bajo una distribución de colas gruesas, otro).

### 4.10 · Cómo se sabe que el detector funciona

No hay verdad de referencia: no sabemos qué velas están mal.

**Opciones:**

a. **Inyección sintética**: meter picos y rachas conocidos en una copia del feed y medir cuántos
   encuentra y cuántos inventa.
b. **Segundo proveedor donde lo haya**: el Brent viene de FTMO; si existiera también en Dukascopy,
   comparar vela a vela.
c. **Inspección manual** de una muestra de las marcas más extremas, contra la historia conocida
   (el *flash crash* del franco suizo del 15-01-2015, el del yen de 2019).

**Te pedimos:** cuál de estas basta y cuál es imprescindible.

## 5 · Lo que NO se pregunta — ya decidido

- Dónde va cada mitad en el flujo (§3).
- Que es diagnóstico y no limpieza (§3).
- Que los umbrales se fijan antes de mirar resultados de estrategias (§3).
- Que la detección cuenta **por tipo y por año** (lo que cambie con los años es parte del resultado).

## 6 · Formato de respuesta

Por cada pregunta (4.1 a 4.10):

```
4.x · <tu recomendación en una línea>
Argumento: <por qué, en 2-5 líneas>
Riesgo si me equivoco: <qué pasa si esta elección es mala, y en qué dirección sesga>
Confianza: alta / media / baja
```

Y al final, en una sección aparte: **lo que falta en este planteamiento** — una familia de
anomalía que no hemos contemplado, una trampa en la atribución, o una pregunta que debería estar
aquí y no está.
