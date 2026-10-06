# Paso 8 — Estudios 4.2, 4.3 y 4.4: decisión y propuesta

**Fecha:** 2026-10-06 · **Alcance:** estudios `snoopingScreen` + criba familia (4.2), `profitShape` (4.3) y `entryQuality` (4.4) del paso 8.
**Referencia:** `criterios-paso-08-puerta-oos-2026-10-06` (apartados 4.2, 4.3 y 4.4). Complementa las demás propuestas del paso 8.

---

## 0. Resumen

| estudio | decisión |
|---|---|
| **4.2** espionaje de datos (`snoopingScreen`) y criba familia | **SE ELIMINA** del paso 8 |
| **4.3** forma del beneficio (`profitShape`) | **SE ELIMINA** del paso 8 |
| **4.4** calidad de la entrada (`entryQuality`) | **SE MANTIENE**: el e-ratio anota; **la prueba del retraso de una barra pasa a ser regla** |

---

## 1. Estudios eliminados

### 1.1 4.2 — Espionaje de datos y criba familia: SE ELIMINA

Motivo: como regla por estrategia no puede decir nada en esta cadena. La mejor t de la población (3,14) está por debajo del máximo que da el ruido con 10.000 estrategias (≈ 3,7), así que ninguna prueba de comparaciones múltiples va a nombrar a nadie, y su lift medido es nulo.

### 1.2 4.3 — Forma del beneficio: SE ELIMINA

Motivo: lo que medía ya está cubierto en otras reglas:

| lo que medía `profitShape` | dónde queda |
|---|---|
| concentración en las mayores ganadoras | $t_{-3}$ de R8 |
| autocorrelación de las operaciones | $n$ efectivo de R3 |
| rotura de la curva | pendiente de degradación de R5d |

**Nota de implementación:** $t_{-3}$, $t_{-Q^*}$ (R8) y la pendiente de R5d tienen que calcularse en algún sitio. Al eliminar `profitShape`, se calculan en la propia puerta (`studies/screening/gate/measures.py`), junto a `drift_excess_t`, con la que comparten el exceso por operación.

---

## 2. 4.4 — Calidad de la entrada: SE MANTIENE

### 2.1 Por qué

Es el único estudio que mide algo que ninguna otra regla mide, y además responde a un riesgo real de operativa:

- Las cuentas de fondeo y los brókers tienen **feeds distintos**: barras con otro horario de cierre, otros huecos, otros máximos y mínimos, a veces desplazadas. La misma señal puede dispararse una barra antes o después.
- **Si la estrategia se rompe sólo por mover una barra, no es operable**: su ventaja depende de un detalle del histórico que en real no se va a reproducir.

Por eso la prueba del retraso **puede descartar**, aunque una barra de M30 o H1 sea un desplazamiento grande.

### 2.2 Dos partes

| parte | qué mide | papel |
|---|---|---|
| **e-ratio** | si, tras la entrada, el precio se mueve más a favor que en contra, frente a entradas al azar a las mismas horas, a horizontes fijos y sin depender de la salida | **anota** (diagnóstico) |
| **retraso de una barra** | si la ventaja sobrevive a mover la operación una barra | **regla** |

---

## 3. La prueba del retraso: cómo se hace

### 3.1 Variantes

Sobre cada operación de oos1 se construyen tres versiones desplazadas, todas en el timeframe de la estrategia:

| variante | entrada | salida | qué simula |
|---|---|---|---|
| **E+1** | apertura de la barra siguiente a la entrada original | la original | la señal de entrada llega una barra tarde |
| **S+1** | la original | apertura de la barra siguiente a la salida original | la señal de salida llega una barra tarde |
| **ES+1** | una barra tarde | una barra tarde | toda la operación desplazada (feed con las barras corridas) |

Opcional: **E−1** (entrada una barra antes). No es una mirada al futuro: con otro feed, la señal puede dispararse antes. Sirve para ver si el desplazamiento castiga por igual en las dos direcciones.

### 3.2 Repreciado

- Precio de entrada y salida: **apertura de la barra** correspondiente, con el **mismo repreciado común** que R3, el spread y el mono (spread real de Darwinex + slippage; ver la propuesta del mono, sección 0).
- **Lotes:** los de la operación original. El cambio de tamaño por una barra de diferencia en la volatilidad es despreciable frente al efecto del precio.
- **Deriva:** se recalcula con la nueva duración (las barras cambian), igual que en R3.

**Limitación:** en Python se desplazan las marcas de tiempo, pero no se vuelve a ejecutar la lógica de la estrategia. Si la salida depende de reglas sobre el precio (un objetivo, un trailing), la salida desplazada es una aproximación. La versión exacta es un retest en SQX con la ejecución retrasada una barra. Recomendación: la aproximación en Python para toda la población que pasa R3, y la versión exacta en SQX sólo para las que lleguen a los pasos finales.

### 3.3 Medidas

Para cada variante $v$, con el exceso por operación de R3 ($e_i$ original, $e_i^{(v)}$ desplazado):

**Retención de la ventaja:**

$$\text{ret}_v = \frac{\bar{e}^{(v)}}{\bar{e}}$$

1 = la ventaja no cambia; 0,5 = pierde la mitad; ≤ 0 = desaparece.

**¿La caída es real o ruido?** Como son las mismas operaciones desplazadas, la comparación es **pareada**: la diferencia por operación $\Delta_i = e_i - e_i^{(v)}$ tiene mucha menos variabilidad que cada exceso por separado.

$$t_{\Delta,v} = \frac{\bar{\Delta}}{\text{sd}(\Delta)/\sqrt{n}}$$

$t_{\Delta,v} > 1{,}65$: la pérdida de ventaja al desplazar es significativa, no ruido.

**t de R3 desplazada**, anotada: $t^{(v)}$ = `drift_excess_t` calculada sobre $e_i^{(v)}$.

**Se juzga con la peor variante** (la de menor retención).

### 3.4 Por qué no exigir simplemente $t^{(v)} \ge 1{,}65$

Con una t original de 2,33, retener el 60 % de la ventaja da $t^{(v)} \approx 1{,}4$. Exigir $t^{(v)} \ge 1{,}65$ obligaría a tener t ≥ 2,75 de partida: PASA sería casi imposible, y el retraso estaría juzgando otra vez la ventaja, que ya juzga R3. La retención y el test pareado aíslan la pregunta: *¿cuánto de la ventaja depende de la barra exacta?*

---

## 4. Criterio propuesto

Se aplica a estrategias que pasan R3 (para las demás no aporta).

| estado | condición (peor variante) |
|---|---|
| PASA | $\text{ret} \ge 0{,}60$ |
| LIMBO | $0{,}25 \le \text{ret} < 0{,}60$, o $\text{ret} < 0{,}25$ con $t_\Delta \le 1{,}65$ (caída grande pero no distinguible del ruido) |
| **NO PASA** | $\text{ret} < 0{,}25$ **y** $t_\Delta > 1{,}65$: pierde más de tres cuartos de la ventaja al mover una barra, y la caída es real |
| sin dato | LIMBO |

Lectura del NO PASA: «si la estrategia se rompe sólo por mover una barra, apaga y vámonos».

### 4.1 Ejemplo ilustrativo (números inventados, para leer la tabla)

Estrategia con exceso medio original 172 USD y $n = 196$:

| variante | $\bar{e}^{(v)}$ | ret | $t_\Delta$ | lectura |
|---|---|---|---|---|
| E+1 | 140 | 0,81 | 1,2 | apenas cambia |
| S+1 | 155 | 0,90 | 0,7 | apenas cambia |
| ES+1 | 118 | 0,69 | 2,0 | pierde algo, de forma real, pero conserva dos tercios |
| **peor** | | **0,69** | | **PASA** |

Si en E+1 el exceso cayera a 30 USD (ret = 0,17) con $t_\Delta = 3{,}5$: **NO PASA**. Toda la ventaja estaba en entrar en esa barra exacta.

---

## 5. Cómo usarlo

1. **Paso 8 (puerta):** calcular las tres variantes sobre oos1 para las que pasan R3, con el repreciado común. Guardar como hechos `retraso_ret_min`, `retraso_t_delta` (de la peor variante), la variante que la produce y las $t^{(v)}$. Aplicar el criterio de la sección 4.
2. **Diagnóstico (anota):** e-ratio frente a entradas al azar a las mismas horas, a varios horizontes (1, 3, 5, 10 barras). Si el e-ratio es alto en las primeras barras pero la retención en E+1 es baja, la ventaja está concentrada en el primer movimiento tras la señal, la parte más frágil en real.
3. **Pasos finales:** para las supervivientes, retest exacto en SQX con la ejecución retrasada una barra, para confirmar la aproximación de Python.
4. **Módulo de fondeo:** prueba complementaria con el **feed real del bróker o de la fondeadora** (sus propias barras), para ver si la estrategia se dispara en los mismos momentos. Es la versión «real» de este test.

---

## 6. Decisiones abiertas

1. **Umbrales de retención** (0,60 / 0,25): calibrar con la población (distribución de `retraso_ret_min` entre las que pasan R3).
2. **Incluir E−1** o sólo los retrasos.
3. **Aplicarlo también al build:** una estrategia sobreajustada a la barra exacta suele delatarse ya en el build. Sería un diagnóstico adicional, no la regla.
4. **Comprobar por qué `entryQuality` no dejó datos** en la corrida de ejemplo antes de activarlo.
5. **Retest exacto en SQX:** definir en qué paso y cómo configurar la ejecución retrasada.
