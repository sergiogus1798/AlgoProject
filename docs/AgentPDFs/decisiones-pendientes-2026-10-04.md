# Decisiones pendientes — hoja para responder de una vez

Fecha: 2026-10-04.

- **Decisiones abiertas hoy: 27** (cartera 7, fondeo 6, registro y autopilot 8, estadística 4, paso 20 2).
- **Las tres que más trabajo desbloquean:** archivar el pool de desarrollo (abre toda la cartera), Q11 (contra qué se compara la cartera y qué cuenta como pasar) y Q10 (qué optimiza la búsqueda de la cartera).
- **Tiempo de respuesta:** unos 25 minutos; la mayoría se contesta con una letra.

Regla de lectura: «sin medir» y «sin recomendación» significan que las fuentes no dan la cifra o la recomendación; no se ha inventado ninguna. Los códigos Q.. son las preguntas numeradas del plan de la cartera (`portfolio/PLAN.md`, §12); D4 es la cuarta decisión de la tabla del plan de fases 0 y 1.

---

## Lo que se midió hoy (léelo aunque no decidas nada)

| Resultado | Cifra | Qué significa |
|---|---|---|
| La línea antigua de la t de 1,65 | equivale a 1,92 en la escala corregida (el OOS1 dura 5,16 años) | La **t** mide cuántos errores estándar separa la ventaja de la estrategia de cero; más alta es mejor. Ninguna regla viva lee ya esa t (`min_t = 0,0`). La regla viva es R3 del archivo de criterios (`drift_excess_t ≥ 2,33`, el exceso de deriva medido en t), que nunca estuvo en la escala vieja. |
| Reconstrucción de la equity del motor de cartera | En USDJPY, 0 de 3.732 estrategias cuadran dentro de 1 $; en USA500, el 97 % | En la única estrategia que se abrió, el hueco coincide con la comisión de 5 $ por lote mientras hay una posición abierta: la causa es una inferencia sobre un caso, no está comprobada en el resto. Apunta a `portfolio/common/construct/equity/paths.py`; no es una decisión, pero conviene saberlo antes de fiarse de una equity de cartera en USDJPY. |

---

## Lo que desbloquea la cartera

Contexto: el motor de cartera (`OPEN.md` #87) tiene hechos M0-M2, F1 y el motor F2. M3-M5 y M8 esperan las respuestas de abajo.

### C1. Archivar el pool de desarrollo (desbloquea M0)

**Pregunta:** ¿autorizas archivar los supervivientes de los proyectos de desarrollo (USDJPY y XAUUSD)? El archivo lee los ficheros de instalación de SQX y el demonio.

| Opción | Coste | Desbloquea |
|---|---|---|
| Sí, archivar | sin medir; espera a que termine `Test_USDJPY_donchianUpperCrossUp_H1` (en el paso 16.5 el 2026-09-30); después `candidates.py` lista los comandos | M0 y, tras él, la primera ejecución real de F2 |
| No, esperar | cero | nada de la cartera avanza |

**Recomendación:** sin recomendación escrita; es la puerta de todo lo demás.

Respuesta: ____

### C2. Q10 — qué optimiza la búsqueda de la cartera sobre `build`

**Pregunta:** ¿con qué puntuación elige la búsqueda la combinación de estrategias?

| Opción | Qué es | Coste | Desbloquea |
|---|---|---|---|
| (a) | Rangos con signo e iguales pesos de cuatro métricas: RAR % (rendimiento ajustado por riesgo), R al cubo, gain-to-pain (ganancia entre pérdida total; mayor es mejor) y P(año perdedor) | sin medir | M3 |
| (b) | Una sola métrica: Sharpe diario a mercado, o RAR % entre drawdown anual medio | sin medir | M3 |
| (c) | Reglas 0/1 más una métrica para desempatar | sin medir | M3 |

**Recomendación:** sin recomendación escrita en el plan (la bibliografía del plan, §3.8, defiende combinar métricas por rangos y avisa de que las métricas de suavidad solas seleccionan fragilidad).

Respuesta: ____

### C3. Q11 — contra qué se compara la cartera y qué cuenta como pasar

**Pregunta:** ¿cuál es la referencia del veredicto?

| Opción | Qué es | Coste | Desbloquea |
|---|---|---|---|
| (a) | K combinaciones aleatorias admisibles del mismo pool («cartera mono»): pasa si supera un percentil elegido en OOS1 + OOS2 | CPU de K combinaciones; sin medir | M5, F4 |
| (b) | El pool entero con pesos iguales: pasa si lo supera en las métricas robustas | barato; sin medir | M5, F4 |
| (c) | Barras absolutas (p. ej. Sharpe deflactado > 0, descontando el número de pruebas N del registro) | barato; sin medir | M5, F4 |
| (d) | Combinación de las anteriores | sin medir | M5, F4 |

Además hay que dar el percentil o la barra. **Recomendación:** sin recomendación escrita.

Respuesta: ____

### C4. Q16 — cuándo entra una estrategia candidata en la cartera

**Pregunta:** ¿qué exige la búsqueda para admitir una candidata?

| Opción | Condición | Coste | Desbloquea |
|---|---|---|---|
| (a) | Su incremento de Euler (aporte marginal) al Sharpe de build es mayor que 0 | sin medir | M3 |
| (b) | Sube la puntuación de build de Q10 | sin medir | M3 (depende de C2) |
| (c) | (a) más los filtros de pares contra cada miembro | sin medir; se sabe que en un build de 10 años sólo el 75 % de los pares independientes pasa todos los filtros | M3 |

**Recomendación:** sin recomendación escrita.

Respuesta: ____

### C5. Decisión nº 2 del plan — cuántas estrategias por cartera y por símbolo

| Opción | Coste | Desbloquea |
|---|---|---|
| Que lo fije la economía del fondeo | en la cuenta de 10k el tope es el lote mínimo (ya decidido para fondeo) | M3 (lado real) |
| Que lo fije el riesgo propio de la cartera | sin medir | M3 (lado real) |
| Número fijo tuyo | sin medir | M3 (lado real) |

Decide si manda la correlación o la capacidad. **Recomendación:** sin recomendación; tú dijiste el 2026-09-29 que quizá lo decidan la economía o el riesgo.

Respuesta: ____

### C6. Decisión nº 5 — rebalanceo de la cartera

| Opción | Efecto | Desbloquea |
|---|---|---|
| Nunca | el backtest de la cartera es el de pesos fijos | M8 |
| Calendario fijo | el backtest incluye los reajustes | M8 |
| Por degradación | el backtest depende de la regla de degradación | M8 |

**Recomendación:** sin recomendación; sin medir.

Respuesta: ____

### C7. Decisión nº 12 — categoría «sin explicar, en prueba»

**Pregunta:** ¿se admite una categoría de estrategias sin explicación económica, con capital pequeño?

| Opción | Efecto |
|---|---|
| Sí | como hizo Renaissance; más candidatas, más riesgo de sobreajuste (sin medir) |
| No | el protocolo «hipótesis primero» lo exige; ninguna estrategia sin hipótesis entra |

Según el plan sólo afecta a etiquetas (M5). **Recomendación:** el dossier §1.20 del protocolo dice que no.

Respuesta: ____

---

## Fondeo

Ya decidido y no se pregunta de nuevo: presupuesto de 1.000 €, cuentas de 10k USD como máximo, sólo firmas activas, precios de lista.

### F1. FundedNext (candidata): ¿se activa?

Faltan: el importe de la cuota por usar EAs, aceptar una sola cuenta por cartera (las operaciones idénticas en varias cuentas están prohibidas), y las puertas G3 (España servida) y G4 (historial de pagos).

| Opción | Coste | Desbloquea |
|---|---|---|
| Activar | una cuenta por cartera; cuota sin medir | una firma más en los estudios de fondeo |
| No activar | cero | nada |

**Recomendación:** sin recomendación; ver `docs/AgentPDFs/fondeo-admision-fundednext-2026-09-29.md`.

Respuesta: ____

### F2. FundingPips (candidata, bloqueada)

**Pregunta:** ¿preguntas a su soporte si un EA propio de SQX puede operar? Si responden que sí, hay que confirmar los 8 precios y reglas tipados (`confirmed: false`).

| Opción | Coste | Desbloquea |
|---|---|---|
| Preguntar al soporte | un correo tuyo | la admisión de la firma |
| Dejarla bloqueada | cero | nada |

**Recomendación:** sin recomendación. Detalle: `docs/AgentPDFs/fondeo-admision-fundingpips-2026-09-29.md`.

Respuesta: ____

### F3. FTMO: ¿el reembolso de la cuota del 2-Step es por cuenta?

Hoy se lee como «sí», sin confirmar. Se confirma preguntando al soporte. Si es por cuenta, el coste neto de varias cuentas baja; el efecto está sin medir. **Recomendación:** preguntar al soporte; sin recomendación sobre el efecto.

Respuesta: ____

### F4. Hantec: tres dudas

Si se reembolsa la cuota; si el complemento «Profit Target −2 %» baja el objetivo de todas las fases o sólo de la primera; y su artículo de estrategias prohibidas (el vigilante semanal no lo ha encontrado). Además, la comisión de Hantec en oro está sin confirmar, por lo que la verificación del paso 26 rechaza Hantec en XAUUSD hasta que se rellene en la zona Activos. **Recomendación:** sin recomendación; las tres se resuelven con su soporte o su web.

Respuesta: ____

### F5. Decisión nº 11 — qué valida la combinación elegida cuando `oos2` ya está gastado

| Opción | Coste | Desbloquea |
|---|---|---|
| El periodo de la feed de la firma | sin medir | validación sin reservar más datos |
| Incubación en vivo | tiempo de calendario; sin medir | validación independiente |
| Nada | cero, pero sin validación | nada |

**Recomendación:** sin recomendación.

Respuesta: ____

### F6. Resto del encargo 33 §6: riesgo por fase, política de recompra, qué `h` mostrar

`h` es el recorte (haircut) que se aplica a la ventaja medida en OOS; más alto es más prudente. Opciones y costes: sin medir, no están desglosados en `OPEN.md`. **Recomendación:** sin recomendación; ver encargo 33 §6.4 y §6.7.

Respuesta: ____

---

## Registro y autopilot

### R1. Relleno hacia atrás del registro (punto 1.3 del plan): cuatro preguntas

Hecho: la fila del paso 6 (generadas, aceptadas), las filas de la WFM y N global en el informe del registro. El relleno hacia atrás sólo se ha probado en simulacro: 56 filas, 14 estudios, 118.235 estrategias sobre 28 poblaciones (el encargo decía 23 poblaciones y 87.357).

| Pregunta | Opciones | Coste |
|---|---|---|
| a) ¿Cuáles 23 de las 28 poblaciones? | tu lista, o las 28 | sin medir |
| b) ¿N cuenta las generadas (millones) o las aceptadas? | hoy cuenta generadas; N es el número de pruebas que penaliza los p-valores (mayor N, más exigente) | cambiarlo altera todos los ajustes por pruebas múltiples; sin medir |
| c) ¿«Aceptadas» es el Accepted de SQX (4.600, antes del filtro de similitud) o las que acaban en el databank (4.238)? | 4.600 / 4.238 | sin medir |
| d) ¿Las poblaciones de calibración llevan fila del paso 6 y del paso 8 en OOS1? | sí / no | sin medir |

**Recomendación:** sin recomendación escrita en las cuatro.

Respuesta a) ____  b) ____  c) ____  d) ____

### R2. D4 — ¿la reserva de `oos2` ata al autopilot (`ALGO_AUTONOMOUS=1`)?

| Opción | Coste | Desbloquea |
|---|---|---|
| Sí, el autopilot no puede leer `oos2` | cero | una puerta ciega real para los estudios sin supervisión |
| No, el autopilot lee `oos2` como una persona | gasta `oos2` sin que nadie lo vea | autonomía sin freno |

Dato con fecha: `bin/monthly-oos2-roll.sh` corre por primera vez el sábado 2026-10-03 y alarga `oos2` hasta fin de septiembre. D4 debe decir además si un estudio ya empezado sigue con el `oos2` que tenía al empezar. **Recomendación:** Sí.

Respuesta: ____  (estudio ya empezado: conserva su `oos2` de partida / se actualiza ____)

### R3. Un hecho que falta en un criterio del autopilot: ¿pasa, limbo o fallo?

Cada regla del archivo de criterios admite `missing: pass | limbo | fail`; hoy es `limbo` en todas. **Pregunta:** ¿qué destino por regla? Coste y efecto: sin medir. **Recomendación:** sin recomendación; se contesta regla por regla.

Respuesta: ____

### R4. ¿Qué segmento leen los pasos 10-16?

Sólo el paso 8 declara que lee `oos1`; los pasos 10-16 no declaran segmento. Opciones: `oos1` para todos, o un segmento por paso. Coste: sin medir. **Recomendación:** sin recomendación.

Respuesta: ____

### R5. ¿Un «Project stopped» manual es un fallo?

| Opción | Efecto |
|---|---|
| Fallo | el autopilot aborta si paras el proyecto a mano |
| No fallo | lo trata como parada y espera |

**Recomendación:** sin recomendación.

Respuesta: ____

Nota: queda pendiente de hacer (no es decisión) la prueba real del autopilot: tres corridas a cero supervivientes en un worker y matar la JVM a mitad.

---

## Estadística

### E1. Umbrales por la escala corregida de la t (#91): ¿se aplican?

La tasa de falsos positivos (FPR) es la fracción de estrategias de ruido puro que pasan la regla; más baja es mejor. Espacio de búsqueda: 7 líneas × 4 escalas × 136 celdas. FPR en la celda mediana [peor celda], bajo el nulo, y supervivientes de 51.596 estrategias GA de calibración (entre paréntesis, con al menos 35 operaciones/año).

| Umbral | FPR si se deja | FPR si se corrige | Supervivientes |
|---|---|---|---|
| R8 propuesta: 1,3 → 1,42 | 0,24 % [10,3] | 0,15 % [7,8] | 2.105 → 2.781 |
| `decay.SIGNIFICANT_T`: 1,65 → 1,92 | 0,07 % [5,2] | 0,02 % [2,4] | 467 → 1.142 (179 → 472) |
| R8: 2,0 → 2,55 | 0,02 % [2,5] | 0,00 % [0,24] | 40 → 353 |

La regla viva R3 (`drift_excess_t ≥ 2,33`): FPR 0,00 % [0,23] con costes, 0,58 % [1,08] sin costes; 111 supervivientes (12). A 1,65 daría FPR 0,07 % [1,8] con costes y 3,6 % [5,8] sin costes, con 991 (288). El nulo arrastra un coste 0,84-1,04 veces el de seis poblaciones reales; recostear mueve el FPR como mucho 1,3 veces. Tablas: `AlgoData/scratch/null-fpr-2026-10-04/`.

**Recomendación (la de la sesión):** apenas importa; juzgar con `drift_excess_t` como ya hace R3 y no re-correr nada.

Respuesta: ____

### E2. Tres preguntas anejas a #91

| Pregunta | Opciones | Coste |
|---|---|---|
| a) ¿Sigues usando XAUUSD/OOS? Los informes anteriores al 02-10 aún vivos sólo son de ahí (MANTENER pasa de 4 a 25 de 231 con la escala corregida) | sí: re-correr sólo XAUUSD/OOS / no: nada | sin medir |
| b) ¿Qué nulo mide «tiene ventaja»? | sin costes (FPR 3,6 % / 0,58 %) o con costes (0,07 % / 0,00 %) | sin medir |
| c) XAGUSD no está en la lista de #76 (spread real de Darwinex): ¿su ficha es definitiva? | sí / no | sin medir |

**Recomendación:** sólo para a), re-correr XAUUSD/OOS si todavía se mira; b) y c) sin recomendación.

Respuesta a) ____  b) ____  c) ____

### E3. #88 — la curva diaria de SQX es el mínimo del día: ¿cosechar operaciones por variante en el paso 16.5?

Medido en tres poblaciones (60, 3.786 y 3.732 estrategias) en OOS1. Efectos de reconstruir la curva con barras de un minuto:

| Estudio | Efecto medido | Acción |
|---|---|---|
| `snoopingScreen` (¿gana el mejor por azar?) | benchmark sobredimensionado un 15-26 %; correlación con el activo 0,13-0,28 vista y 0,32-0,46 real; p del SPA 0,72→0,58, 0,95→0,95, 0,79→0,73; StepM nombra 0 en ambos | reconstruir (≈1 s de CPU por estrategia) |
| `blindJoint` | mismo motor; no medido (lee `oos2`) | reconstruir |
| CSCV (PBO: probabilidad de sobreajuste, menor es mejor) | 0,37→0,35, 0,36→0,39, 0,40→0,52 (medido sobre poblaciones, no sobre un lote de variantes) | reconstruir exige cosechar operaciones por variante (exportación de SQX en 16.5) |
| `decay` / `degradacion_t` | t entre 0,78 y 0,88 veces la de cierre; pasan 1,65: 19 frente a 83 y 63 frente a 127; orden igual (ρ 0,99, correlación de órdenes, 1 = idéntico) | no reconstruir; usar `drift_excess_t` |
| WFC, exposición, peor día | Sharpe de exposición 0,97-1,00×; peor día 0,99-1,00× la pérdida real | documentar, nada más |

| Opción | Coste | Desbloquea |
|---|---|---|
| Sí, cosechar operaciones por variante | exportación de SQX por variante en 16.5; sin medir | CSCV reconstruido |
| No | cero | el CSCV sigue leyendo la curva de mínimos |

**Recomendación:** reconstruir (la sesión lo recomienda para `snoopingScreen` y CSCV); para el CSCV el coste real está sin medir.

Respuesta: ____

---

## Paso 20

El paso 20 (`blindJoint`) existe pero no corta a nadie hasta que elijas. Mientras sean nulas, el estudio muestra el veredicto bajo cada lectura y marca MANTENER a todos. Nada de esto cuesta CPU; la elección cambia cuántas madres sobreviven (sin medir).

### P1. Qué significa «pasar» (`joint.pieces`)

| Opción | Significado |
|---|---|
| `unanimidad` | las cuatro piezas (WFC, CSCV, superficies, WFM) pasan |
| `sin_fallo` | ninguna falla; indeciso o ciego se tolera |
| `ninguna` | las piezas son contexto y decide sólo el StepM (prueba escalonada sobre varias hipótesis, que controla el error global) |

**Recomendación:** sin recomendación; se decide con los nulos recalculados delante.

Respuesta: ____

### P2. Sobre quién cuenta el StepM su búsqueda (`joint.population`); K es ese número

| Opción | Significado | Efecto en estrategias |
|---|---|---|
| `supervivientes` | K = las madres que las piezas mantuvieron | sin medir |
| `entrantes` | K = toda madre que llegó al paso 20 (las piezas también eligieron con `oos2`; un test sobre lo que una elección conservó no paga esa elección) | sin medir |

**Recomendación:** sin recomendación escrita.

Respuesta: ____

---

Quedan fuera de esta hoja las decisiones D1, D2, D3 y D5 del plan de fases y los criterios de los pasos 6 y 8: vienen en un documento aparte.
