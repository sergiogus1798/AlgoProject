# 50 · Paso 8 tras el 65 (corrida V y lo que queda de la puerta) y receta del IS del paso 6 — plan que cruza sesiones

> Consolidado el 2026-10-09 desde los encargos 44 (la puerta) y 42 (recalibrar 6-7-8); **reescrito el
> 2026-10-15 contra el encargo 65**, que cambió el paso 8. Lo anterior sigue en git
> (`git log -- docs/encargos/50-pasos-6-a-8-puerta-y-receta.md`). Aquí sólo está **lo que falta**.

**Tu oficio:** estadístico e ingeniero de la puerta IS/OOS. Diseño y medidas: **Opus**. Lo mecánico
(la corrida V, documentos, comprobaciones): **Sonnet** (regla 17). Todo en `~/Desktop/AlgoProject`
sobre `master` (regla 12).

**Tu encargo:** verificar el paso 8 nuevo en una corrida entera (frente 1, **el siguiente que se
ejecuta**), dejar la documentación de la puerta al día (las decisiones Q2-Q4 las cerró el dueño el 2026-10-15), y entregar
la **receta del IS del paso 6** (qué pedir en el Build de SQX), medida.

## El paso 8 vigente (verificado el 2026-10-15 contra el código)

- **Una sola regla estadística:** «z del mono con horas, por celda» — `z_mono ≥ Φ⁻¹(1 − 0,01/B)`,
  B = lotes cribados en oos1 en la celda (activo × marco × dirección × familia) contando éste:
  **2,326 con B = 1; 2,576 con 2; 2,713 con 3; 2,807 con 4** (`pipeline/autopilot/criteria.yaml`
  paso "8", `alpha: 0.01, per: cell, missing: fail`; B lo da `ledger.cells.batches_for`; commit 9aef247).
- Siguen juzgando: R1a presencia, R1b sanidad, R2 neto de oos1 > 0, R5c ventaja frente al coste
  (`edge_mean_oos` ≥ 2, Limbo ≥ 1,25), R5d degradación (`t_b`, `e_fin`), calidad de datos, retraso de una
  barra, R7 (`q_p`, sólo Limbo) y R6 (`dd_p`). **R3, R4a, R5, R5b, R8 y R9b son columnas**, no juzgan.
- El Limbo sigue en la cadena (P8-L → A); `edge_mean_oos` no se endurece (P8-E → A) — dueño, 2026-10-15.
- Tras el juicio, **una medoide por grupo de estructura, ≤ 4 por lote** (`medoids: 4`). `dev` ya no existe.
- `p_fdr` (fdr local sobre las z, `studies/screening/gate/many.py`) es columna y ordena; el paso 18.5
  está apagado y el 1 también.
- Medido (encargo 65 §5.4, dossier `docs/AgentPDFs/criterios-paso-08-corrida-nula-2026-10-12.md` §4,
  USATEC H1 ruptura largo, 5.000 monos): con α 0,01 sobrevive el **0,78 %** de la nula (IC 0,56-1,06),
  plantas 0,05 / 0,10 / 0,15 R → 23 / 57 / 80 %, y **0 de las 10.000 reales**.

## Estado — lo actualiza cada sesión

| frente | qué | modelo | depende de | estado |
|---|---|---|---|---|
| 1 · V | una corrida entera por `/workflow` con el paso 8 vigente | Sonnet | máquina libre | ✅ 2026-10-15: segunda corrida (Test_USATEC_H1_breakoutL_v8b_leaseWeb) — paso 8 verificado: B=2, línea 2,576, z_mono máx 2,84, embudo 10.000 → 7.356 → 6 → 4 medoides; ledger B 1→2; edits_since_seal = 1 por el α 0,01 del 15-10 (posterior al sello del 12-10, edición contada, no fallo). La primera corrida cayó en el paso 8 por «List index overflow» (arreglado en d52908d). La segunda llegó al 18 y paró en el 18.5 por fichas sin price_rounding (medidas esta noche; causa extra: rollout_hour sin comillas, 1fcb33b). Supervivientes en el almacén; proyectos retirados. |
| 2 · Parada | Q2, Q3 y Q4 | dueño | — | ✅ contestada el 2026-10-15 (todas las recomendaciones) |
| 4 · Z1 + M | cargar lo que decida la parada; documentación de la puerta | Sonnet | 2 ✅ (Z1 sin trabajo: Q2 y Q3 dejan todo como está); M puede empezar ya | ✅ 2026-10-15: documentación de la puerta al día (salvo `criterios-implementados-2026-10-12`, que tiene otra sesión, y la cabecera de `criteria.yaml`, que no se toca) |
| 5 · Receta del IS (ex 42) | paso 6: dosis-respuesta, A/B dentro/fuera del Build, familia contra gemela, flotante, equipo rojo | Opus (+ Sonnet para lanzar) | custodio libre; nada pesado junto a un workflow | 🟡 2026-10-17: fase 0 hecha (3 semillas GBPJPY H1 largo momentum); pendiente L5 (z sólo de quien pasa los niveles 0-2) antes de la fase 1 |

Orden: 1 → 4. El 5 es independiente salvo por la máquina (regla 19).

**Bitácora** (una línea por sesión: fecha, qué frentes, qué quedó a medias):

- 2026-10-09 · consolidado desde los encargos 44 y 42. De 44 estaban hechas las oleadas 0 a 6 salvo K-m; 42 no se ejecutó nunca.
- 2026-10-15 · el dueño contestó «todas las recomendaciones»: QV = A, Q2 = A (las reglas se quedan y se firman como v1), Q3 = A (sin tope en R5d), Q4 = A (sin frente N: V corre en USATEC H1 largo ruptura, la misma celda de la corrida nula), Q7 = A (las poblaciones de la receta suman a la B de sus celdas). Q4c: V lanzada el mismo día (🟡 en curso). El frente 3 (N) se borra.
- 2026-10-15: reescrito contra el 65 (fila 5 del orden). Fuera: K-m (lo hizo la corrida nula del 65 §5.4 para la única regla que pesa), la tabla 1.2 de líneas (R3 ya no juzga), la parada 3 (`dev` borrado), los nulos de la t (Q5: R3 es columna) y la clave `by:` de familia (Q6 → no).
- 2026-10-16 · frente 5: Council (Feynman, Kahneman, Taleb, Ada) sobre el diseño; dueño R1-R7 = A; §5.2 reescrito. Medido en la V: z_mono media 0,82, desviación 0,47 (no N(0, 1)). Siguiente: fase 0 cuando el custodio quede libre.
- 2026-10-17 · frente 5, fase 0: `builder --exit-required` (L1 B, e96ae96d); paleta `momentum_base` (L3 B), 6 min de Build (L4 A). Tres semillas `Test_Calib_GBPJPY_H1_momentumL_s{1,2,3}_leaseWeb` + una de prueba de 5 min: 11.201 / 12.609 / 11.847 estrategias, 22,6 / 24,4 / 22,1 min de punta a punta (SQX ~6 min, export+sync ~4, `falsePositives` ~7,5). Varianza entre builds nula: z_mono media 1,46 en las tres (desviación de las medias 0,005; KS p ≥ 0,67; pasan 2,326 360-470 por 10.000, χ² p 0,14). **Pero la z sólo existe para ~20 %** (2.176 de 11.201): el gate no calcula el mono para quien cae en el nivel 0 (neto OOS, 7.289) o el 1b (1.087) — R1 pide la z de toda la población (L5). `workflow.sh run` exige 15 min de log quieto aunque sea propio: 16 min de espera entre poblaciones.
- 2026-10-15 · frentes 1 y 4: V ✅ (segunda corrida, ver la tabla); M hecho: dossier del paso 8 con cabecera y `dd_esperado_r`, fila 8 de WORKFLOW, README de la puerta, `/oos-gate`, glosario, `memory/config.yaml` (`z_mono` → `not_beyond_random`), `gate-t-scales` y capítulo 29. Pendiente: `criterios-implementados-2026-10-12` (otra sesión) y el párrafo `dev` de la cabecera de `criteria.yaml`.

---

## 1 · V — corrida de verificación (Sonnet; tarea mecánica)

**Qué verifica:** que en una corrida real el paso 8 lee la B de su celda, aplica la línea de la tabla
de arriba, deja ≤ 4 medoides y anota el juicio en el ledger con el hash sellado. Una corrida **entera**
de `bin/workflow.sh`, **siempre a través de la skill `/workflow`** (regla 19), en un proyecto `Test_`
(reglas 6 y 10), **nunca `--smoke`** (con él sólo juzgan las reglas de lectura y el 8 no se verifica),
sin `--until`.

1. **Ya contestado (Q4c, 2026-10-15): V corre en USATEC H1 largo ruptura** (`Test_USATEC_H1_breakoutL_v8_leaseWeb`, paleta `ruptura_base_v3`, 10.000 estrategias, 30 min, sin MT5); si hubiera que relanzarla, pregunta antes: modo (`simple` o `template`), activo, marco, lado, familia,
   paleta (o plantilla `.sqx`), STRATEGIES, MINUTES, y los cuatro parámetros de MT5 o ninguno (sin ellos
   la corrida acaba antes del paso 26). Con la pregunta, enséñale la fila de la celda:
   `python3 -m ledger.cells | grep '<ACTIVO>_<TF>_<long|short>_<familia>'` — su `batches_screened`
   (la línea que va a pisar es la de B + 1) y sus `oos2_looks`. **V gasta una B de esa celda y una mirada
   a oos2** (paso 19.5, aunque sea `Test_`): una celda con 3 miradas rechaza el 19.5 (hoy
   `XAUUSD_H1_long_breakout`), y una familia o dirección `unknown` también. Recomienda una celda con
   B = 0, familia conocida y que no se piense operar pronto.
2. `python3 -m core.assets <ACTIVO>` (regla 5): informa los overrides; si sale distinto de cero, para.
3. Invoca `/workflow` y sigue su §4: `preflight.sh`, y el comando de su §1 en segundo plano con el
   nombre `Test_<ACTIVO>_<TF>_<familia><L|S>_v8_leaseWeb`. Nada más hasta que avise (regla 18).
4. Al avisar, informa como manda su §5 (paso, segundos, corte entrada → salida) y además:
   - paso 8: `python3 -m pipeline.autopilot.facts --project <P> --step 8 --grep z_mono` — la línea
     aplicada es la de la tabla para la B de la celda; las que salen del 8 son ≤ 4;
   - `python3 -m ledger.cells` — `batches_screened` de la celda subió en 1 y `edits_since_seal` no se movió;
   - el `funnel.csv` del paso 8, pegado.
5. **Si el 8 no deja ninguna** («no dejó ninguna superviviente»): es un resultado, no un fallo; V cuenta como
   hecha (QV = A). No se edita `criteria.yaml` para pasar, ni se conduce un paso a mano.
6. Si falla: las tres tentativas de la skill (§6) y un informe. Un `Test_` que acaba bien se retira solo;
   uno fallido o parado, `python3 -m sqx.projects.retire <P> --role custodian --yes`, worker parado.
   Antes de retirar, comprueba que la cosecha del 8 está en `AlgoData/reports/<P>/Results/<fecha>/gate/`

## 2 · Parada — contestada (2026-10-15)

Q2 = A, Q3 = A, Q4 = A: ver «Decisiones del dueño». No hay frente 3 (N): Q4 = A no pide comprobar la tasa de la nula fuera de USATEC H1 largo.

## 3 · Z1 + M — documentar (Sonnet)

**Z1: sin trabajo** (Q2 = A y Q3 = A: nada cambia; las reglas se firman como v1 por el dueño). Si algo cambiara, iría en `pipeline/autopilot/criteria.yaml` (paso "8") y
`studies/screening/gate/config.yaml`; prueba `python3 -m pytest -q tests/test_gate_rules.py
tests/test_thresholds.py tests/test_autopilot_criteria.py`. Si nada cambia, Z1 no tiene trabajo.

**M (puede empezar ya; re-verifica cada punto antes de editar):**

| qué | estado verificado el 2026-10-15 |
|---|---|
| `pipeline/autopilot/criteria.yaml:3-7` | la cabecera aún describe `dev`, que el 65 borró: quitar el párrafo (regla 21) |
| `~/Desktop/AlgoData/manual-fuentes/29-puerta.md` (`/manual-chapter`, luego `python3 tools/manual.py`) | describe la puerta vieja (`degradacion`, `mono.max_p`, `--set degradacion.min_t`: `:98`, `:159`, `:177-218`, `:246`): reescribir con la regla única, las columnas, las medoides y `p_fdr` |
| `docs/AgentPDFs/puerta-is-oos-paso-08-especificacion-2026-10-06.md` + PDF (`/dossier-pdf`) | describe las 16 reglas con R3 de juez y dice `dd_esperado_p95_r` dos veces (el dato es `dd_esperado_r`): cabecera «la regla estadística la sustituyó el 65; vigente: `criterios-paso-08-corrida-nula-2026-10-12`» y el nombre arreglado |
| `docs/AgentPDFs/criterios-implementados-2026-10-12.md` (+ PDF) | lo tiene modificado otra sesión (`git status`): tocarlo sólo cuando esté limpio; su parte del paso 8 apunta a los dos dossiers de arriba |
| fila del paso 8 de `docs/AgentPDFs/WORKFLOW.md` (`:33`) | habla de la criba de edge del encargo 11 y spreads de hoy: reescribir con el paso 8 vigente |
| `studies/screening/gate/README.md` (`:4`, `:13-15`, `:36`) y `.claude/skills/oos-gate/SKILL.md` (`:15`) | «screens» / «seven screens»: una puerta de reglas por niveles |
| `ui/text/glossary.py` (`:8`, `:108`) | «screens» de la puerta |
| `studies/research/memory/config.yaml:126-131` | mapea hechos muertos (`degradacion_*`) y `drift_excess_t` a causas, y no `z_mono`: quitar los muertos y mapear `z_mono` → `not_beyond_random` |
| `knowhow/research/gate-t-scales.md` (`:7`, `:22-24`) | dice que se juzga sobre `drift_excess_t` y que la regla viva es R3: editar (no añadir) — desde el 65 juzga `z_mono` |

Cierre: `python3 tools/manual.py && python3 tools/depmap.py && python3 tools/checks.py`.

---

## 5 · Receta del IS del paso 6 (ex 42, nunca ejecutada; Opus + equipo)

**Entregable:** qué pedir en el *in-sample* del Build de SQX, medido, **cada umbral con lo que gana y lo
que cuesta en estrategias**, por activo × marco × familia donde los datos obliguen a separarlo y global
donde no. «Este filtro apenas ayuda» es una respuesta válida. Necesita SQX: respeta las reglas 3, 10, 14,
15 y 18. Antes de gastar una hora de CPU: `python3 -m core.assets <SYMBOL>` de cada activo (regla 5),
enseñar al dueño el spread por tramo de cada activo (una calibración ya se tiró por el spread),
`preflight.sh`, y una población de prueba de cinco minutos por activo nuevo (de los 17 activos nuevos
sólo DAX40 ha corrido en SQX, `OPEN.md` #93): cuenta estrategias y operaciones, no lo supongas.

### 5.1 El carril (D1 contestada: llamada directa al builder, sólo para este estudio)

La población es **sin seleccionar** (aceptación mínima: ≥ 100 operaciones en la ventana del build y
beneficio > 0; nada que lea el OOS; el databank **nunca lleno**, porque lleno reemplaza por Ret/DD del IS)
y, en un subconjunto, su **gemela de generación aleatoria**: `python3 -m sqx.projects.builder …
--acceptance calibration [--random]` (`core/buildfilters.py`, modo `calibration`; `--random` en
`sqx/projects/builder.py`). Fuera de la regla 19 por decisión del dueño (D1), sólo aquí.

Reglas del carril: un trabajo a la vez en el custodio, arranque y parada sólo por `bin/sqx-worker.sh`;
proyectos `Test_Calib_<ACTIVO>_<TF>_<familia><L|S>[_rnd]_leaseWeb`, cada uno retirado al completarse;
paletas **`_v2`** (D2); sin bloques de reloj, sesión, día ni VWAP anclado (D3, regla 15); toda
estrategia con regla de salida (D6: `exits.condition_required`, hoy `false` en `assets/_build.yaml:50`
— aplicarlo es del encargo 72 / `OPEN.md` #93; si sigue en `false` al llegar, para y avisa). Tras
aplicar una paleta, **cuenta los bloques encendidos** y las condiciones de cada estrategia (ninguna pasa
de 2 entradas y 2 salidas; si una pasa, para). Mide la duración de una población y díselo al dueño
**antes** del barrido (D7: 40 h aceptables, confírmalas con esa cifra). Datos a `AlgoData`; borra el
`raw/` de una población cuando su cosecha esté escrita; como mucho 8-12 procesos de Python y 25 GB
libres. Por población: Build → retest OOS (costes de `oos1`, sin aceptación) → cosecha → el paso 8
vigente con la semilla anotada; nada de `feedQuality`, `profitShape` ni `entryQuality` (borrados).

### 5.2 El diseño — qué medir (Council del 2026-10-16 y R1-R7 = A del dueño)

**Lo que cambió.** Con ~6 de 10.000 que pasan el paso 8 por población, «pasa o no» no mide nada: 10
métricas × 6 umbrales sobre 6 eventos es ruido (Feynman, Kahneman, Taleb y Ada, por separado). Y la z del
mono de una población real no es N(0, 1): en la V vale **media +0,82, desviación 0,47** (7.356
estrategias; 6 sobre 2,326 donde N(0, 1) daría el 1 %) — el desplazamiento común del lote del 65 (D11),
no una población peor que el azar. De ahí las siete reglas:

1. **R1 — el resultado es la z del mono continua** de cada estrategia en oos1, leída **dentro de su
   población** (rango, o z referida a la nula empírica del lote, D11). Pasar el paso 8 es lectura
   secundaria, con su intervalo de Wilson. Etiquetas alternativas: como mucho dos, escritas antes.
2. **R2 — los filtros se miden después del build, en Python**, sobre poblaciones **sin filtrar** (el
   databank nunca se llena: dentro del Build un filtro sólo descarta, no cambia lo que la genética busca).
   Toda la dosis-respuesta (operaciones/año, PF, KER, Sharpe, Ret/DD, SQN, estabilidad, estancamiento,
   % de aciertos, operación media contra el coste) sale gratis de las mismas poblaciones. **Control:** un
   recorte al azar del mismo tamaño de la misma población (1.000 sorteos). **Control negativo:** la
   columna de la métrica permutada — si «funciona», la tubería tiene una fuga. Las métricas que son el
   mismo eje (Sharpe, Ret/DD, SQN, PF) se agrupan antes y se prueba una por grupo; corrección de Holm.
   El A/B dentro/fuera del Build, sólo para el filtro que sobreviva, con 2 semillas.
3. **R3 — dentro del estudio la línea es fija: B = 1 (2,326)**, más la z continua. La B del ledger
   sigue sumando por Q7 = A (es contabilidad: esas celdas llegan a sus corridas reales con B ≥ 2).
4. **R4 — fuera la prueba de 180 min llenando el databank** contra la de 6 min (una sola muestra no
   contesta; lo que preguntaba, si el Ret/DD del IS selecciona para el OOS, sale de R2 gratis).
5. **R5 — ~1/3 de las celdas en corto**, para que un mercado alcista no se lea como ventaja; cada filtro
   se mide también contra comprar y mantener a la misma exposición, en todos los activos.
6. **R6 — el riesgo flotante es veto, no eje:** un filtro que empeore en oos1 el percentil 95 del peor
   MAE en R, el peor día sobre el neto anual o la parte que rompería un 5 % de pérdida diaria, se
   rechaza aunque suba la z.
7. **R7 — descubrimiento y confirmación se reparten por celdas antes del primer build** (~60 / 40 %);
   las de confirmación se leen **una vez**. La unidad de inferencia es la celda (efecto aleatorio o
   bootstrap por celdas, y por grupo de estructura dentro de la población): un filtro se recomienda si
   sube la z en las celdas de confirmación con un intervalo que excluye 0, el mismo signo en ≥ 75 % de
   las celdas, y su coste en estrategias al lado.

**El presupuesto (~40 h, a confirmar con la primera población medida, D7).**

| fase | qué | poblaciones |
|---|---|---|
| 0 | una celda, 3 semillas: duración de punta a punta y varianza entre builds (sin ella no se dimensiona lo demás) | 3 |
| 1 | ~10 celdas × 1 semilla, ruptura y momentum, H1 y M30, ≥ 6 activos fuera de XAUUSD/USDJPY (DJ30, GBPJPY, EURJPY primero), ~1/3 en corto; reparto R7 fijado antes | ~10-14 |
| 2 | gemelas aleatorias (`--random`) en 4-5 celdas de descubrimiento con rendimiento no nulo | 4-5 |
| 3 | A/B dentro/fuera del Build del único filtro que sobreviva, 2 semillas | 2 |
| — | reserva para el equipo rojo y el embudo por el camino real del código (de los datos guardados) | 1-2 |

Antes de cada activo nuevo, cinco minutos de población de prueba (cuenta estrategias y operaciones); una
celda con < 2.000 estrategias se cae. **Si nada pasa la vara, la receta es la mínima** (suelo de
operaciones, beneficio > 0, operación media ≥ k × coste): quitar filtros es más barato que añadir falsos.
**Fuera:** recetas por familia o por celda (Q6), el barrido de 20-50 operaciones/año como builds propios
(el suelo 35/20 está decidido; se lee sobre las mismas poblaciones), el flotante como eje con builds propios.

### 5.3 Lo que entrega

El dossier en castellano en `docs/AgentPDFs/` con su PDF (`/dossier-pdf`): la receta del IS, cada umbral
con ganancia y coste, qué varía por activo/marco y qué es global, las celdas sin ventaja y qué segmento
gastó cada cifra; sustituye a los dossiers de criterios con cabecera «no valen». Las reglas en
`assets/_study.yaml` marcadas como **propuesta de un agente**, provisionales hasta que el dueño firme.
Las poblaciones como filas de la memoria (`python3 -m studies.research.memory.report --close
<run_dir>`). Una ficha de `knowhow/` por hecho no obvio, `OPEN.md` #93 anotado con `/open-close`, y el
capítulo del manual de cualquier comando que cambie (regla 8).

---

## Decisiones del dueño — pregúntalas (regla 11)

**Contestadas (no se reabren):**
- 2026-10-14: Q1 → un año, sin AR(1). Q4b → sin suelo extra en R1b. Q4c → activo, marco y tipo de V se
  preguntan al lanzarla. Q5 → los nulos de la t se borran (R3 es columna desde el 65). Q6 → sin criterios
  por familia. D1 → llamada directa al builder. D2 → paleta `_v2`. D3 → sesión, día y VWAP anclado leen
  el reloj: fuera. D4 → no se gastan builds en las celdas medidas en contra. D5 → asumir la pérdida y
  medirla. D6 → toda estrategia lleva regla de salida. D7 → sí, con la duración medida. D8 → no se
  vuelve a leer oos1.
- 2026-10-15 (65 §5.4): P8-Z → α 0,01; P8-L → el Limbo sigue; P8-E → `edge_mean_oos` no se endurece.

- 2026-10-16 (frente 5, «tus recomendaciones»): R1 z continua · R2 filtros después del build, sobre poblaciones sin filtrar · R3 línea fija B = 1 en el estudio · R4 fuera la prueba de 180 min · R5 ~1/3 en corto · R6 flotante como veto · R7 descubrimiento/confirmación por celdas — todas A (§5.2).
- 2026-10-15 («todas las recomendaciones»): QV = A (V cuenta como hecha cuando el paso 8 está verificado, aunque no deje ninguna) · Q2 = A (las reglas se quedan y se firman como v1) · Q3 = A (sin tope en R5d) · Q4 = A (sin frente N: V corre en USATEC H1 largo ruptura) · Q7 = A (las poblaciones de la receta suman a la B de sus celdas).

## Lo que no tocas

El master (`~/Desktop/SQX`), ni para leer su configuración de tareas. **`oos2`**: reservado, salvo la
única mirada del 19.5 que gasta V. La firma de los criterios: es del dueño. El bloque genético del dueño
(`sqx/projects/buildmode_model.xml`). La campaña (`pipeline/campaign/`). El paso 4 de
`studies/data/spread/` (escaneo, `/asset-onboard`, bandas del MC Retest, swap de fondeo; su capítulo
`59-spread-real` se queda). Los criterios de los demás pasos (10, 12, 14, 20…: encargos 49 y 51).
`portfolio/funded/` (encargo 54). `ledger/thresholds.yaml` sólo gana filas, al final de su sección; la
clave `snoopingScreen.stepm.fwer` **se queda** (la lee el paso 20). Nada pesado junto a un workflow en
marcha (regla 19). El dueño hace los commits.

## Verificación

**No hay un comando que lo cierre:** su final son decisiones del dueño y corridas de SQX. No se despacha
con `/loop`.

- V: el `funnel.csv` del paso 8 pegado de una corrida de `bin/workflow.sh` sin `--smoke`, la línea
  aplicada igual a la de la tabla, ≤ 4 medoides, la B de la celda + 1 y el sello sin tocar; proyecto
  retirado (`ls ~/Desktop/SQX_w2/user/projects | grep -c _v8_` → 0).
- `python3 -m pytest -q tests/test_gate_rules.py tests/test_gate_cascade.py tests/test_gate_mono.py
  tests/test_false_positives.py tests/test_thresholds.py tests/test_autopilot_criteria.py
  tests/test_ui_gate.py` en verde (por fichero: `tests/test_oracle_draws.py` tropieza con un `-k` global).
- - `python3 tools/manual.py && python3 tools/depmap.py && python3 tools/checks.py`.

## Cómo cierras

Cada sesión: la tabla de estado y la bitácora de arriba actualizadas · qué hizo · qué verificó, con la
salida pegada · qué dejó sin hacer y por qué · qué descubrió para `knowhow/` (una ficha por hecho no
obvio, editando la que exista) · la lista de ficheros cambiados y, como última línea, **¿Quieres hacer
el commit?** Un encargo cumplido se borra: lo aprendido está en `knowhow/`, el manual y el código.

---

## Lo que sólo vivía en los encargos de origen

**Decisiones del dueño que siguen en pie (no se reabren).** R5 sin dato falla (`missing: fail`); semillas
**nuevas en cada corrida** y anotadas en el scorecard (`q_seed`, `dd_seed`, `mono_seed`;
`knowhow/eng/nulls-seed-fresh-per-run.md`); `retraso_t_delta` es la t pareada de la variante que da el
`ret` mínimo; `edgeCost` sólo sobre oos1 con el coste realmente pagado; lecturas del mono: tamaño con el
ATR de la **barra anterior**, escalones con tamaño de doctrina, el mono paga los costes de la estrategia,
**el mono sin stop vale**, y se sortea dentro de la ventana `drift.window` (año); la ventaja plantada de
`falsePositives` es **neta de costes**; el percentil del drawdown esperado es parámetro
(`drawdown.percentile`, 95; dato `dd_esperado_r`); «las poblaciones a medias se olvidan (no se repite
ningún retest)»; 5.000 repeticiones como mínimo por defecto; el trader al azar sólo en OOS; la cascada
sale en el primer Falla y registra nivel y regla. Las 25 lecturas de costes del 2026-10-06 están en
`engines/market/reprice.py` y los módulos de la puerta.

**Hallazgos que invalidan datos (comprueba cada uno en su tarjeta antes de usarlo).** El repreciado
inflaba los stops hasta el arreglo de `reprice.real` (`knowhow/export/off-grid-stamps-and-stop-exits.md`):
las poblaciones con stop de antes del 2026-10-07 no valen, y las enteras guardadas no llevan `Close type`.
USDJPY redondeaba el fill al pip y no a `tick_step` (corregido, misma tarjeta).

**Contratos que otros leen.** `gate.scorecard.*`: nivel 0 `presencia_passed`, `sanidad_passed`,
`sanidad_value`, `estaticas_value`, `is_trades_per_year`; 1a `drift_excess_t` (columna); 1b `z_frec`,
`t_b`, `e_fin`, `edge_mean_oos`, `t_exceso_k`, `t_sin_mejor_trimestre`, `t_sin_3_mejores`, `mae_p95_r`,
`ret_datos`, `t_a`, `n_afectadas`; 2 `retraso_ret_min`, `retraso_t_delta`; 3 `q_p`, `dd_p`,
`dd_esperado_r`, `z_mono`, `mono_p`, `mono_seed`, y `cayo_nivel`/`cayo_regla`; más `p_fdr`. Sin regla
(módulo de fondeo): `oos_worst_day_r`, `oos_dd_over_net_year`, `oos_net_per_year_r`. Un hecho mal
nombrado **no falla, se lee como Limbo**: `tests/test_gate_rules.py` lo vigila.

**Dejado fuera (a propósito).** El mono en mercados adicionales, Stouffer y `oos2` en el 8; el retest
exacto en SQX con ejecución retrasada para finalistas y la prueba con el feed real de la firma (encargo
54); el entregable (b) del 42 y sus reglas Pasa/Limbo/Falla.
