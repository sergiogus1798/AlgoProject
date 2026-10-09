# Criterios de los pasos 6, 8, 10 y 12 — recalibración por activo, marco y familia

**2026-10-04 · propuesta de agente, PROVISIONAL hasta que la apruebes.** Sustituye a
`criterios-pasos-6-y-8-2026-10-02.md`, cuyas poblaciones incumplían las reglas 14 y 15. Qué filtros
poner en el Build de SQX (paso 6), qué exigir tras el retest fuera de muestra (paso 8), y qué
exigir a los mercados adicionales (paso 10) y a los otros marcos (paso 12).

Las reglas están escritas, como propuesta, en `assets/_study.yaml` (paso 6) y
`pipeline/autopilot/criteria.yaml` (pasos 8, 10 y 12). Nada está en commit.

---

## 1. Lo que hay que decidir

| # | decisión | mi recomendación | lo que cuesta la alternativa |
|---|---|---|---|
| 1 | **Filtros de IS en el Build.** | Sólo el mínimo: ≥ 100 operaciones y beneficio > 0. Gastar los minutos en build, no en filtros. | Cualquier filtro probado da entre un 70 y un 98 % menos de estrategias robustas por minuto de build (§4). |
| 2 | **Suelo de 35 operaciones al año.** | No como descarte. Mantenerlo sólo como línea de Pass, si lo quieres por significancia. | Como descarte pierde el 81 % de las robustas, en H1 y en M30 por igual, sin mejorar la calidad por operación (§4.2). |
| 3 | **Techo de operaciones al año.** | Poner un techo de ~75 al año. | Por encima, las poblaciones dan 0,4 veces lo que da el azar. |
| 4 | **Paso 8 como limpieza, no como prueba.** | Fallo sólo por lo que es claramente malo; la t decide entre Limbo y Pass (§5). | Las reglas de hoy dejan 997 Fallos por cada 1.000 y 0,04 Pass: casi nada llega a los pasos que sí prueban. |
| 5 | **Dónde construir.** | Priorizar cruces del yen, metales y pares mayores; índices en M30, no (§6). | Es el factor que más pesa: más que cualquier filtro. |
| 6 | **Pasos 10 y 12.** | PENDIENTE §7 y §8 | PENDIENTE |
| 7 | **Corregir el término de deriva de la puerta.** | Sí: la versión actual favorece a los cortos (§5.3). | Sin corregir, 45 de 115 umbrales parecen depender del lado; corregido, 8. |

---

## 2. Qué se ha medido

- **203 poblaciones, 990.820 estrategias**, construidas en el custodio entre el 2 y el 3 de octubre
  como **Simple Strategy** (sin plantilla), con **entrada 1..2 y salida 1..2 condiciones**, **una
  dirección por build**, todo a mercado, con tu configuración genética (250 por isla, 20 islas) y
  una paleta por familia de 99 a 127 señales con nombre, sin reloj ni niveles stop/limit.
- **116 celdas base** (405.866 estrategias): 17 activos × M30 y H1 × la familia que tu prior
  permite en cada activo × largo y corto. 89 celdas con caja de build de 2 minutos, 25 con 10
  minutos (las que aceptaban menos de 300 estrategias en 2) y 2 con 5.
- **Tres tramos:** construcción (IS), `oos1` y **`oos2`, que autorizaste como zona de validación**
  para esta calibración. Los criterios se eligen mirando sólo `oos1`; `oos2` se lee una vez por
  criterio para ver si lo que aprueba sigue funcionando. Ventana de `oos2` fija para todo el estudio:
  hasta el 30 de agosto de 2026 (31 en índices).
- **Todo a timeframe elegido**, sin retest a 1 minuto (tu decisión del 2 de octubre).
- **Un bucle de aprendizaje de siete rondas** (unas 16,5 horas de custodio): builds con filtros
  dentro, cada uno contra su control sin filtrar de la misma celda y la misma caja, con 10 celdas
  reservadas que el bucle nunca usó para aprender.
- **Nulas:** 11,9 millones de estrategias de entrada al azar (pasos 6-8), 81.600 con hermanas en
  otros marcos (paso 12) y 136 celdas con mercados adicionales (paso 10).
- **Un crítico independiente** que recalculó los titulares desde los datos primarios y corrigió
  seis (§10).

**Comprobado en cada población, no supuesto:** costes, ventanas y sesión contra la ficha del
activo; la configuración genética; y, sobre 992.682 estrategias, que ninguna pasa de 2 condiciones
de entrada ni de 2 de salida y que todas las órdenes son a mercado.

**Lo que no se ha medido:** builds largos (de 60 y 180 minutos, con el databank lleno), gemelas de
generación aleatoria y réplicas del mismo build. Se cortaron para llegar a los pasos 10 y 12.

---

## 3. Las seis conclusiones que mandan

1. **La estrategia media que sale del builder pierde.** Profit factor mediano fuera de muestra
   entre 0,8 y 0,9, en `oos1` y en `oos2`. Las poblaciones dejan 1,9 veces más supervivientes que un
   trader al azar que paga costes, pero entre 0,16 y 0,35 veces las de una estrategia que ni gana
   ni pierde.
2. **Manda dónde se construye, no qué filtro se pone.** Frente al azar: cruces del yen 4,0 veces,
   metales 2,9, pares mayores 1,8, índices 1,3 (en M30, 1,04).
3. **Los filtros de IS dentro del Build no dan más estrategias buenas; dan menos estrategias.**
   Poner el filtro dentro o aplicarlo después da lo mismo.
4. **El suelo de 35 operaciones al año no selecciona mejores estrategias.** La calidad por
   operación es la misma a cualquier frecuencia; el suelo quita el 81 % de las robustas.
5. **Lo que pasa bien `oos1` va algo mejor en `oos2`, pero poco.** La correlación del resultado
   por operación entre los dos tramos es 0,06 (0,02 en H1, 0,08 en M30). El paso 8 enriquece; no
   prueba. La prueba tienen que darla los pasos que leen datos independientes.
6. **La prueba central de la puerta está sesgada por el lado.** Restaba mal la deriva del mercado
   y favorecía a los cortos. Corregida, la diferencia entre largos y cortos casi desaparece.

---

## 4. Paso 6 — filtros del Build en SQX

### 4.1 Lo que queda escrito

| condición en «Ranking» del Build | valor | por qué |
|---|---|---|
| Número de operaciones, mínimo | 10 por año × años del build (≈ 100) | sólo para que haya estadística |
| Beneficio neto | > 0 | idem |
| Número de operaciones, máximo | 75 por año × años del build | por encima, peor que el azar |
| Profit factor, Ret/DD, SQN, % de aciertos, estabilidad | **ninguno** | no dan más estrategias robustas (§4.3) |

### 4.2 El suelo de operaciones al año

Cortando después del build, sobre las 116 celdas base. «Robusta» = pasa la línea central del paso 8
con beneficio en `oos1`.

| suelo en el IS (ops/año) | 20 | 25 | 30 | 35 | 40 | 50 |
|---|---|---|---|---|---|---|
| robustas perdidas, H1 | 51 % | 63 % | 74 % | 81 % | 86 % | 92 % |
| robustas perdidas, M30 | 55 % | 68 % | 76 % | 81 % | 87 % | 92 % |

- **En M30 cuesta lo mismo que en H1** (diferencia a 35: −0,4 puntos, intervalo de −8 a +7). Las
  poblaciones de M30 no operan tanto como cabría esperar: la mediana de los controles va de 21 a 62
  operaciones al año.
- **La calidad por operación no cambia con la frecuencia:** profit factor mediano de 0,88 a 0,91
  en todos los tramos.
- **Por qué las de pocas operaciones pasan más:** la estrategia media pierde por operación; con más
  operaciones esa pérdida se acumula y hunde la prueba. Es aritmética de costes.
- **Dentro del build** (9 celdas, misma caja): 2,3 robustas por cada 1.000 con el suelo frente a
  7,4 sin él, y 0,18 veces por minuto.
- **Un matiz del crítico:** las robustas que el suelo quita vuelven a serlo en `oos2` 17,1 veces de
  cada 1.000, igual que las no robustas de su misma franja (16,8). El coste del suelo está probado
  en número de estrategias, no en edge.
- **El techo sí:** frente al azar, entre 1,4 y 2,8 veces hasta 75 operaciones al año, y 0,41
  veces por encima.

### 4.3 Los filtros probados dentro del Build

Mismo activo, misma familia, mismo lado y misma caja de build; filtro dentro contra control sin
filtrar.

| filtro | robustas por minuto (filtro / control) | robustas por cada 1.000 (filtro / control) | veredicto |
|---|---|---|---|
| ≥ 35 ops/año | 5,4 / 32,4 | 2,2 / 7,6 | no |
| PF ≥ 1,2 y Ret/DD ≥ 2 | 7,1 / 33,6 | 8,7 / 9,4 | no aporta |
| % de aciertos ≥ 55 | 10,6 / 32,4 | 6,8 / 7,6 | no |
| PF ≥ 1,3 y Ret/DD ≥ 3 | 4,8 / 35,8 | 7,8 / 7,3 | opcional (abajo) |
| PF ≥ 1,5 y Ret/DD ≥ 5 | 0,6 / 35,8 | 4,9 / 7,3 | no |
| PF ≥ 1,8 y Ret/DD ≥ 8 | no llega a 300 estrategias en 4 minutos | — | no |

- **PF ≥ 1,3 y Ret/DD ≥ 3**, sobre las celdas reservadas: 15,2 robustas por cada 1.000 frente a 7,8,
  y 6,4 por minuto frente a 21,9. En las 10 celdas donde se probó, 1,54 veces más pura (intervalo
  de 0,86 a 2,43, que incluye «ningún efecto»), casi todo por una celda. En `oos2` sale 3,3 veces
  más pura (de 1,6 a 4,6). **Veredicto: opcional.** Sirve para revisar menos estrategias; si se usa,
  dentro del Build y nunca junto al suelo de 35 (elige estrategias de 17 a 27 operaciones al año).
  Para un build que llena su databank, la cuestión queda abierta.
- **SQX respeta todos estos filtros** como condición del Build, Ret/DD y % de aciertos incluidos:
  el 100 % de lo aceptado los cumple.
- **La caja de build pesa más que cualquier filtro.** El genético tarda unos 2 minutos en empezar a
  producir: la misma celda acepta de 600 a 3.800 estrategias en 2 minutos y de 12.000 a 20.000 en 6.
  Y con más evolución el profit factor del IS sube mientras el de fuera se queda igual.

### 4.4 La condición de salida

Con «Exit rule» al 50 %, cada población trae estrategias con y sin condición de salida. Comparadas
dentro de las 116 poblaciones:

| | con condición de salida | sólo salida por barras |
|---|---|---|
| Duración de la operación | 14,0 h | 16,8 h |
| Drawdown máximo | 12,9R | 14,6R |
| Peor día | −2,8R | −3,0R |
| Tasa de robustas | igual | igual |

Compra menos riesgo flotante, no más robustez. Para fondeo conviene; no hace falta obligarla.

### 4.5 Qué varía y qué es global

- **Global:** todo lo anterior. Una receta por familia, clase de activo o lado no mejora a la
  global al aplicarla a un activo que no se usó para ajustarla.
- **Lo que parecía variar por el lado era el sesgo de la prueba** (§5.3).
- **Lo que sí varía es la tasa de aceptación del build**, y mucho: de un 1 % a un 34 % de lo
  generado, según la celda.

| grupo | aceptación mediana |
|---|---|
| índices / metales | 8,7 % / 7,0 % |
| pares mayores / cruces del yen | 4,5 % / 3,7 % |
| largo / corto | 7,0 % / 4,2 % |
| H1 / M30 | 6,7 % / 5,4 % |

---

## 5. Paso 8 — tras el retest fuera de muestra

### 5.1 Qué vale cada criterio, medido en `oos2`

Dentro de cada celda, lo que el criterio aprueba en `oos1` frente a lo que rechaza. Cada celda pesa
igual. La última columna compara estrategias con parecido número de operaciones.

| criterio sobre `oos1` | ganan en `oos2` por cada 1.000 (aprobadas / rechazadas) | diferencia a igual nº de operaciones |
|---|---|---|
| t descontando la deriva ≥ 1,65 | 396 / 322 | +52 (de +24 a +83) |
| t descontando la deriva ≥ 2,33 | 481 / 364 | +103 (de +31 a +175) |
| Beneficio en `oos1` > 0 | 338 / 281 | +34 |
| Profit factor en `oos1` ≥ 1,2 | 357 / 290 | +35 |
| Edge por coste ≥ 2 | 344 / 279 | +34 |
| PF al spread real ≥ 1 | 330 / 282 | +28 |
| Supera al buy & hold | 342 / 289 | +30 |
| p del mono ≤ 0,05 | 301 / 296 | +5 (no separa) |

- **Todos separan menos el mono.** Un tercio de cada diferencia es sólo que lo aprobado opera menos.
- **Separan en M30 (+81) y casi nada en H1 (+19, no se distingue de cero).**
- **Lo aprobado sigue perdiendo de media:** alrededor del 60 % de lo que pasa la línea de 1,65
  acaba en negativo en `oos2`.
- **A 2,33** sólo 18 celdas tienen 10 aprobadas o más: la cifra descansa en pocas.

### 5.2 Las reglas que propongo

| veredicto | condición |
|---|---|
| **Fallo** | no está en el databank OOS · operaciones escasas o clonadas · beneficio en `oos1` ≤ 0 · PF al spread real < 1 · peor día o peor operación flotante más allá de −5R |
| **Pass** | no falla, y t descontando la deriva (corregida) ≥ 2,33 |
| **Limbo** | todo lo demás; por encima de 1,65 va marcado como «Limbo+» |

Sobre las 116 celdas base:

| grupo | por cada 1.000 | ganan en `oos2` | neto por operación en `oos2` | drawdown mediano |
|---|---|---|---|---|
| Pass | 0,9 | 48 % | −0,013R | 3,3R |
| Limbo+ | 6,2 | 37 % | −0,028R | 4,6R |
| Limbo | 259 | 39 % | −0,031R | 9,0R |
| Fallo | 734 | 32 % | −0,055R | 17,0R |

- **Las reglas de hoy** dejan 0,04 Pass, 3,1 Limbo y 997 Fallos por cada 1.000; lo que las hace tan
  estrictas es la franja de operaciones por año.
- **Quitar de las reglas:** la p del mono (no separa en `oos2`) y el drawdown dividido entre el neto
  anual como Fallo (sólo el 12 % de las limpias lo cumple).
- **Riesgo flotante de las robustas:** drawdown máximo mediano de 3,1R a 5,1R y peor día de −1,8R a
  −2,3R, parecido en todas las familias.

### 5.3 El sesgo de la prueba central

La puerta resta a cada operación lo que habría ganado el mercado por sí solo, suponiendo que el
tamaño de la posición no tiene que ver con lo que el precio hace después. Pero el tamaño se fija
como 1/ATR, y sí tiene que ver. El resultado es un desplazamiento de la t de una estrategia sin
edge de entre ±0,02 y ±0,27 en H1 y M30, de signo distinto según el activo y el lado. En EURUSD H1
el azar pasaba la línea de 1,65 el 2,6 % de las veces en largo y el 5,8 % en corto.

La corrección (restar la operación «a ciegas» de la misma duración, con su tamaño) lo reduce a unos
+0,05 a favor de los largos. Con la prueba sin corregir, 45 de 115 umbrales parecían depender del
lado; corregida, 8. **Propongo cambiar el término en la puerta**; no lo he tocado.

---

## 6. Dónde construir

Supervivientes frente a un trader al azar que paga costes y opera con la misma frecuencia:

| grupo | celdas | veces el azar |
|---|---|---|
| cruces del yen | 32 | 4,00 |
| metales | 16 | 2,85 |
| pares mayores | 38 | 1,84 |
| índices | 30 | 1,32 (en M30: 1,04) |
| volatilidad | 10 | 3,67 |
| momentum | 26 | 2,42 |
| ruptura | 30 | 1,85 |
| pullback | 30 | 1,54 |
| reversión | 20 | 1,36 |
| H1 / M30 | 61 / 55 | 1,94 / 1,85 |

- **47 de las 116 celdas** están enriquecidas tras corregir por el número de pruebas: 18 de cruces
  del yen, 11 de pares mayores, 11 de índices y 7 de metales.
- **Ninguna celda** llega a la referencia de «ni gana ni pierde».
- **La persistencia de `oos1` a `oos2`** va al revés que el enriquecimiento: índices 0,14, metales
  0,09, pares mayores 0,04, cruces del yen 0,03.
- Las celdas de caja de 10 minutos salen más enriquecidas (2,87 frente a 1,63), pero son justo las
  que aceptaban poco: caja y celda están mezcladas.

---

## 7. Paso 10 — mercados adicionales

PENDIENTE

---

## 8. Paso 12 — otros marcos

PENDIENTE

---

## 9. Lo que es firme y lo que es provisional

PENDIENTE

---

## 10. Lo que corrigió el crítico independiente

Recalculó los titulares desde las operaciones y métricas por estrategia (201 poblaciones), sin usar
las tablas ni el código que auditaba.

| afirmación | veredicto | qué cambió |
|---|---|---|
| «El paso 8 no elige lo que aguanta en `oos2`» | exagerada | pesando cada celda igual, sí separa (+60 por cada 1.000) |
| «El suelo de 35 cuesta menos en M30» | errónea | con las celdas reconstruidas, igual que en H1 |
| «El efecto de PF y Ret/DD se encoge con la evolución» | no se reproduce | retirada |
| «Los cruces del yen no persisten» | exagerada | persisten igual que los pares mayores; retirada |
| «La corrección elimina el sesgo» | exagerada | lo reduce |
| «Poner PF ≥ 1,3 y Ret/DD ≥ 3 dentro del build» | errónea | es opcional; la tabla comparaba mal |
| Persistencia, coste del suelo en H1, cifras del bucle, sesgo de la deriva, máximo 2 condiciones, integridad de datos | confirmadas | — |

**No llegó a revisar:** el contraste de «los cinco tests juntos», el enriquecimiento frente a la
nula por franja de frecuencia y las 47 celdas enriquecidas.

---

## 11. Avisos

1. **Cajas de build cortas.** 89 celdas son de 2 minutos: evolución temprana. Tus builds reales
   duran 180 minutos con el databank lleno y sustituyendo por Ret/DD. La receta del paso 6 no está
   probada para eso.
2. **Sin gemelas aleatorias ni réplicas.** La única referencia del azar es la nula simulada, y no
   se sabe cuánto varía un build de otro.
3. **`oos1` y `oos2` quedan gastados** para las estrategias de esta calibración, que son de
   desarrollo y no se van a operar. `oos2` no tiene una nula propia: los largos de índices ganan el
   51 % de las veces con cualquier regla.
4. **Sólo un 52-58 % de las estrategias son estructuras distintas;** el resto son variantes. Las
   conclusiones valen por celda, no por estrategia.
5. **Un 7-11 % de las estrategias cambia de identidad** entre el build y el retest; se emparejan
   por nombre, y el crítico comprobó que el emparejamiento acierta en el 99,7-100 %.
6. **Costes de la plata y los crudos:** provisionales.

---

## 12. Lo que ha cambiado en el código

PENDIENTE

**Dónde está la evidencia:** `AlgoData/scratch/calib2/` — `synth_final/` (la síntesis),
`adaptive/RECIPE.md` y `LOG.md` (el bucle de filtros), `redteam/review.md` (el crítico), `out/`
(un informe por población), `STATE.md` (el diario del estudio); `calib_step10/` y `calib_step12/`
(los pasos 10 y 12).
