# 50 · Pasos 6 a 8: terminar la puerta IS/OOS y medir la receta del IS — plan que cruza sesiones

> Consolidado el 2026-10-09 desde los encargos 44 (la puerta, paso 8) y 42 (recalibrar 6-7-8). Los
> originales siguen legibles en git: `git show c923d10:docs/encargos/44-puerta-is-oos-paso-8.md` y
> `…/42-recalibracion-pasos-6-7-8.md`. Aquí sólo está **lo que falta**.

**Tu oficio:** estadístico e ingeniero de la puerta IS/OOS. Diseño, estadística y medidas: **Opus**.
Lo mecánico (cargar líneas ya decididas, regenerar documentos, comprobaciones, retirar proyectos):
**Sonnet** (regla 17). Un subagente por paquete, en `~/Desktop/AlgoProject` sobre `master` (regla 12).

**Tu encargo:** dejar el paso 8 con **líneas de Pasa / Limbo / Falla medidas y congeladas por el dueño**
(cada una con su coste en estrategias al lado), la documentación al día y una corrida entera de
verificación; y entregar la **receta del IS del paso 6** (qué pedir en el Build de SQX), también medida.
La puerta ya está construida; lo que queda es medir, decidir, cargar y documentar.

## Estado — lo actualiza cada sesión

| frente | qué | modelo | depende de | estado |
|---|---|---|---|---|
| 1 · K-m | embudo de las poblaciones de prueba (nula y ventaja plantada), tarjeta `gate-chain-false-positives` | Opus | máquina libre (`preflight.sh`) | pendiente |
| 2 · Parada 2 | el dueño fija las líneas, el tope de R5d, H1/H4, el suelo de R1b y los argumentos de V | dueño | 1 | pendiente |
| 3 · Z1 | cargar las líneas en `criteria.yaml` (paso "8"), `ledger/thresholds.yaml`, `gate/config.yaml` | Sonnet | 2 | pendiente |
| 4 · M | documentación de la puerta nueva | Sonnet | 3 | pendiente |
| 5 · V | una corrida entera de `bin/workflow.sh` en un `Test_` | Sonnet | 3 | pendiente |
| 6 · Parada 3 | el dueño apaga `dev.on` | dueño | 5 | pendiente |
| 7 · Receta del IS (ex 42) | paso 6: dosis-respuesta, A/B dentro/fuera del Build, familia contra gemela, flotante, equipo rojo | Opus (+ Sonnet para lanzar) | D1 (el carril) | sin empezar |
| 8 · Nulos de la t (ex 42 §3) | nulos sobre `drift_excess_t` y `trade_t` | Opus | — | **cubierto en parte por K**: ver §7.2 |

Orden que se mantiene (es el del encargo 44): 1 → 2 → 3 → 4 → 5 → 6. El frente 7 es independiente de
1-6 salvo por la máquina (regla 19: nada pesado junto a un workflow) y por la decisión D1.

**Bitácora** (una línea por sesión: fecha, qué frentes, qué quedó a medias):

- 2026-10-09 · consolidado desde los encargos 44 y 42. De 44 están hechas las oleadas 0 a 6 salvo K-m (ver §0); 42 no se ejecutó nunca.

---

## §0 De dónde sale

- **Dueño, 2026-10-06:** revisó el paso 8 regla a regla; «deja la mayoría de cosas como parámetros
  configurables», editables **en la ventana**, y las pruebas con repeticiones llevan **al menos 5.000**
  por defecto. Sus seis propuestas y su índice: `docs/AgentPDFs/criterios-implementados-2026-10-12*-2026-10-06.md`
  (abrirlas por tramo, regla 16). El diseño completo, con fórmulas: la especificación
  `docs/AgentPDFs/puerta-is-oos-paso-08-especificacion-2026-10-06.md`. **Cuando especificación y este
  encargo no coincidan, manda este encargo**; el paso 8 se rige por `WORKFLOW.md` en el orden.
- **Dueño, 2026-10-02 (origen de 42):** «qué criterios he de poner, sobre todo en el IS de SQX, y en el
  primer cribado de OOS en la aplicación, para que (1) me salga un OOS robusto — esto depende mucho del
  IS — y (2) los tests del mono y demás cosas del paso 8 salgan aceptables». Y para el IS: «cuántos
  trades he de pedir (suelo de 35 por año), si he de pedir un PF mínimo, un KER, un Sharpe, o qué
  métricas he de usar».
- **Por qué la receta del IS está sin medir.** La primera calibración (2026-10-01/02) rompía las reglas
  14 y 15; la segunda (2026-10-04, 203 poblaciones) corrió con el spread mal y el dueño la borró entera
  (`OPEN.md:764`). No queda nada reutilizable en disco. Las cifras de los pasos 6 y 8 de
  `assets/_study.yaml` y de los dossiers `criterios-implementados-2026-10-12.md` y
  `criterios-implementados-2026-10-12.md` **no valen** (ambos llevan ya la cabecera «cifras no valen»,
  2026-10-09); se leen por su método. `OPEN.md` §93 (`grep -n '^## 93' OPEN.md`) es el expediente vivo.
- **Ya decidido por el dueño, no se reabre:** suelo de construcción de 35 operaciones al año en M15,
  M30 y H1 y 20 en H4, sin techo (2026-10-09, commit `445d29a`). Reglas 14 y 15 (condiciones y paleta).
  Todo lo de «Lo que sólo vivía en los encargos de origen» al final.

### Lo ya hecho de 44 (no se copia; dónde vive)

| bloque | dónde |
|---|---|
| R2b y R4b retiradas | commit `9a3b60d` / 2026-10-06 |
| A inventario, B identidades (R1a), C repreciado común, D R3 con deriva por ventana (variante **d**) | `pipeline/autopilot/judge.py` (`resolve`), `studies/screening/gate/harvest.py` (`set_aside`), `engines/market/reprice.py`, `studies/screening/analysis/tradelevel.py`, `gate/level1a.py`; tarjetas `knowhow/research/monkey-reprice-audit.md`, `drift-term-biased-by-side.md`, `gate-t-scales.md`, `trade-t-vs-frequency-and-skew.md` |
| E, F, G (R5, R5b-d, R8, R9b, calidad de datos, retraso, R7, R6, mono) | `studies/screening/gate/{level1b_centred,level1b_onepass,level1b_data,level2,level3ab,level3c}.py`, `studies/screening/analysis/{centred,onepass,dataquality,delay,resample}.py`, `engines/nulls/windowed.py`; tests `tests/test_gate_*.py` |
| H borrados (spread del paso 8 y 25.5, `snoopingScreen`, `profitShape`; `edgeCost` a la definición nueva) | commit `90d516d` |
| I cascada y juez (16 reglas, `dev.on` sin tocar) | `studies/screening/gate/{levels,cascade}.py`, `pipeline/autopilot/criteria.yaml` paso "8"; commit `210a549` |
| J parámetros y reglas en la ventana | `ui/daemon/sqxconfig/`, `ui/desktop/criteria/`, `ui/desktop/workspace/funnel.py`; commits `90d516d`, `7203f4c` |
| K: `falsePositives` por la cadena nueva, ventaja plantada **neta de costes** | `studies/screening/falsePositives/` (README); `python3 -m studies.screening.falsePositives.report --project P --databank Results --feed F [--harvest <carpeta>] [--seed N] [--set population.per_level=500]` |
| L datos para fondeo al pasar el WFM | `pipeline/autopilot/kept.py`, `tests/test_autopilot_kept.py` (formato descrito en el README de la carpeta; lo lee el encargo 54) |
| P objetivos `gate.*` en el catálogo de rendimiento | `perf/inputs/`, `perf/config.yaml` |

---

## 1 · K-m — el embudo de las dos poblaciones de prueba (Opus, máquina libre)

Lo único pendiente de la oleada 6. **Pesado en CPU**: `.claude/skills/sqx-wait/preflight.sh` antes; si
hay un workflow corriendo, se espera (regla 19). Es Python sobre cosechas ya hechas: no toca SQX.

**Qué se corre.** `falsePositives` con la cascada **apagada** (`cascade.on: false` en
`studies/screening/gate/config.yaml`; es sólo para medir), por la cadena entera, con 5.000
estrategias por nivel (`population.per_level`) y ventaja plantada Sharpe 0,05 / 0,10 / 0,15
(`population.edges`). Poblaciones: **todas las cosechas completas (≥ 30 estrategias, con MAE y curva)
que existan al llegar** (dueño, 2026-10-06, P.7-1: «habrá más»), más USA500 H1 largo
(`Test_USA500_H1_indicesIBS`, 3.000, ya con 150.000 monos) y las 10.000 de NIKKEI225 M30 largo
(`harvest/Test_NIKKEI225_M30_*`, sólo operaciones: **R9b y el flotante no se miden ahí**). **Lista
primero qué cosechas hay** (`ls ~/Desktop/AlgoData/harvest`, `AlgoData/INDEX.md`) y cuáles tienen
`Close type` (las poblaciones enteras viejas no lo llevan: no se rehacen, «no se repite ningún
retest», dueño 2026-10-07; las poblaciones con stop del embudo anterior están invalidadas, ver
«Lo que sólo vivía»). **Si no hay ≥ 1 población nueva completa, K-m espera a que la haya**: no se
rellena con las viejas.

**Qué se entrega** (a la tarjeta nueva `gate-chain-false-positives` de `knowhow/research/`, que **no
existe todavía**, y a la respuesta al dueño):

1. Por regla y por nivel de ventaja (nula, 0,05, 0,10, 0,15): proporción en Pasa / Limbo / Falla
   (`reglas.csv`), y el embudo de la cadena.
2. Por línea, la frase del dueño: «a X pierde el A % de las de 0,10 y deja pasar el B % de las nulas».
   Ocho reglas que pierdan cada una un 5 % de las buenas se llevan un tercio: el coste acumulado
   cuenta tanto como el de cada regla.
3. El **tope de R5d** (`centring.cap_slope`, hoy vacío en `gate/config.yaml:74`) propuesto con los
   números, y si el ±0,35 de R5 se mantiene.
4. **R7 con las dos ventanas** de D.1 (año y semestre: parte de la diferencia entre trimestres ya está
   restada) y **cuánto efecto común le queda a R5d** tras la deriva por ventana.
5. **H1 frente a M30**: si una regla se comporta distinto por timeframe, se le *propone* al dueño; no
   se carga ninguna excepción por timeframe (R3 y las reglas nuevas nacen sin `by`; la única que queda
   es R4a en H4).
6. Si **R1b** pide el suelo absoluto de 60-80 operaciones en oos1 (opcional del índice).
7. Qué reglas **heredan** su resultado del donante (la frecuencia: en K los monos de un donante
   comparten frecuencia y una plantilla es una sola idea) y por tanto **no se miden**: se entregan
   «no medidas» y no se les propone línea. Y cuáles se midieron sólo sobre las de **exceso medio
   positivo** (`ret_datos` y `retraso_ret_min` dividen por el exceso medio: con media ≤ 0 el hecho
   queda vacío, y con la cascada apagada K-m lo dice).
8. Lo que el plantado **no** mide: es un exceso constante que no depende de la entrada; en el retraso
   y la calidad de datos mide rechazos por ruido, no potencia. Escríbelo en la tarjeta.
9. El coste de cada nivel (segundos por estrategia; mono a 5.000 sorteos). Si 20.000 estrategias no
   caben en una noche, di la cifra y propón menos estrategias por nivel o el mono sólo sobre las que
   pasan R3 (la decisión es del dueño).
10. Datos a `AlgoData` (regla 7); resultados como filas de la memoria de investigación
    (`python3 -m studies.research.memory.report --close <run_dir>`).

**Verificación del frente:** la población nula da en R3 una tasa de falsos positivos compatible con el
5 % (con ventaja plantada neta de costes: R3 deja pasar 0,9 % de nulos, 13 %, 34 % y 62 % de
0,05 / 0,10 / 0,15 en el caso sintético de 196 operaciones — la referencia que K-m debe reproducir en
orden de magnitud sobre poblaciones reales); `python3 -m pytest -q tests/test_false_positives.py`.

## 2 · Parada 2 — el dueño fija las líneas (no se salta)

Entrega al dueño la lista de ficheros y las tablas de K-m, y le pides **cada línea con su coste**:
la línea de cada regla de la tabla 1.2 de abajo, el tope de R5d y el ±0,35 de R5, el comportamiento de
H1 y H4, el suelo de R1b y los argumentos de la corrida V (activo, timeframe, plantilla o simple,
cuántas estrategias). Hasta que responda, **`dev.on` sigue encendido** y las líneas de partida de la
tabla son provisionales (Principio: se mide antes de congelar — cambiar el dato de una regla invalida
la tasa de falsos positivos con la que se fijó su línea).

### Tabla 1.2 — las líneas de partida (cargadas hoy en `criteria.yaml` paso "8")

`e` = exceso por operación de R3 (P/L de la operación menos lo que habría ganado una operación ciega
del mismo lado, duración y tamaño). El nivel de una regla se deduce de su hecho. Estados: Pasa /
Limbo / Falla, manda la peor; un hecho que falta es Limbo (dueño, 2026-10-01); un hecho «no calculado
porque la estrategia ya cayó» no es «falta».

| nivel | regla | hecho | Pasa | Limbo | Falla |
|---|---|---|---|---|---|
| 0 | R1a presencia | `presencia_passed` | sí | — | no |
| 0 | R1b sanidad y clones | como hoy | como hoy | como hoy | como hoy |
| 0 | R2 neto de oos1 | como hoy | > 0 | — | ≤ 0 |
| 0 | R4a operaciones/año en el build | `is_trades_per_year` | ≥ 35 | 20-35 (H4: desde 15) | < 20 (H4: < 15) |
| 0 | R5b operaciones en oos1 | `sanidad_value` | ≥ 100 | < 100 | nunca |
| 1a | R3 t del exceso | `drift_excess_t` | ≥ 1,65 | no tiene | < 1,65 |
| 1b | R5 estabilidad de la frecuencia | `z_frec` | \|z\| ≤ 1,5 | hasta 3,5 | > 3,5 |
| 1b | R5c ventaja frente al coste | `edge_mean_oos`, `t_exceso_k` (k = 1,25) | t(k) ≥ 1,65 y edge ≥ 2 | t(k) < 1,65, o edge 1,25-2 | edge < 1,25 |
| 1b | R5d degradación en oos1 | `t_b`, `e_fin` | t_b ≥ −1,65 | t_b < −1,65 | t_b < −1,65 y e_fin ≤ 0 |
| 1b | R8 concentración | `t_sin_mejor_trimestre`, `t_sin_3_mejores` | las dos ≥ 1,65 | alguna entre 0 y 1,65 | alguna ≤ 0 |
| 1b | R9b MAE | `mae_p95_r` | ≤ 1,5R | hasta 2,5R | > 2,5R |
| 1b | Calidad de datos | `ret_datos`, `t_A` | ret ≥ 0,60, o ninguna afectada | 0,25-0,60, o < 0,25 con t_A ≤ 1,65 | < 0,25 y t_A > 1,65 |
| 2 | Retraso de una barra | `retraso_ret_min`, `retraso_t_delta` | ret ≥ 0,60 | 0,25-0,60, o < 0,25 con t_Δ ≤ 1,65 | < 0,25 y t_Δ > 1,65 |
| 3a | R7 homogeneidad | `q_p` | > 0,05 | ≤ 0,05 | nunca |
| 3b | R6 drawdown | `dd_p` | > 0,10 | 0,01-0,10 | ≤ 0,01 |
| 3c | Mono | `z_mono` | ≥ 1,65 | < 1,65 | nunca |

Fuera del paso 8: R2b, R4b, R9a, R9c (estas dos al módulo de fondeo: hasta que exista nada juzga el
peor día ni el drawdown sobre el neto, aceptado por el dueño). **Verifica contra el YAML vivo** antes
de presentar la tabla: es la de 2026-10-06 y el código la cargó en el paquete I.

## 3 · Z1 — cargar las líneas congeladas (Sonnet, tras la parada 2)

Posee: `pipeline/autopilot/criteria.yaml` (paso "8"), `ledger/thresholds.yaml` (filas nuevas **al
final de su sección**, leídas como `ledger:<clave>`), `studies/screening/gate/config.yaml`.
Prueba: `python3 -m pytest -q tests/test_gate_rules.py tests/test_thresholds.py
tests/test_autopilot_criteria.py`. Cabecera de `criteria.yaml`: su texto «Fallo = R1, R2, R2b o R9»
quedó obsoleto en la conmutación (comprobar `sed -n 1,50p pipeline/autopilot/criteria.yaml`; si aún
lo dice, se reescribe aquí). **`dev.on` no se toca** (parada 3). La firma de los criterios es del dueño.

## 4 · M — documentación de la puerta nueva (Sonnet, en la misma tarea que Z1)

Re-verifica cada punto antes de editar (algunos pueden haberse arreglado ya):

| qué | estado verificado el 2026-10-09 |
|---|---|
| `docs/AgentPDFs/puerta-is-oos-paso-08-especificacion-2026-10-06.md` + PDF (`/dossier-pdf`) | sigue diciendo `dd_esperado_p95_r` en `:945` y `:1219`; el dato se llama `dd_esperado_r` y el percentil es el parámetro `drawdown.percentile` (95). Meter las líneas congeladas y lo que K-m cambie |
| `docs/AgentPDFs/criterios-implementados-2026-10-12.md` (+ PDF) | su parte del paso 8 describe reglas viejas: reescribirla para que apunte a la especificación |
| `~/Desktop/AlgoData/manual-fuentes/29-puerta.md` (`/manual-chapter`, después `python3 tools/manual.py`) | describe la puerta vieja (`degradacion`, `familia`, `mono.max_p`, `--set degradacion.min_t`, embudo `degradacion … familia`) |
| `studies/screening/gate/README.md` | a medias: aún habla de «screens» y `config.yaml` como cribas (`:4`, `:42`, `:71`) |
| `.claude/skills/workflow-simple/steps.md` (paso 8) | la fila lista `gate, edgeCost, feedQuality, spread, isOos, …, profitShape` y dice «rules R1-R9»: ya no es así |
| `.claude/skills/oos-gate/SKILL.md` | habla de «seven screens» (`:13`, `:44`) |
| fila del paso 8 de `docs/AgentPDFs/WORKFLOW.md` (`:33`) | enumera el spread real de Darwinex (#76), `maeDepth`, etc.; reescribir con la puerta por niveles |
| `pipeline/autopilot/README.md`, `ui/text/glossary.py`, `studies/research/memory/config.yaml` | el bitácora de 44 los marcaba como puerta vieja: comprobar |
| tarjetas `knowhow/research/drift-term-biased-by-side.md` y `gate-t-scales.md` | editar (no añadir) con la variante d, la ventana elegida y la t con sesgo-curtosis |
| `manual-fuentes/59-spread-real.md` | **comprobar** si debió borrarse con el paquete H1 (sigue en disco) y, si es así, quitar su stem de `tools/manual.py` |
| `knowhow/*/INDEX.md` | los regenera quien cierra |

Cierre: `python3 tools/manual.py && python3 tools/depmap.py && python3 tools/checks.py`.

## 5 · V — corrida de verificación (Sonnet, tras Z1)

Una corrida **entera** de `bin/workflow.sh` en un proyecto `Test_` (regla 19, regla 10), **nunca
`--smoke`** (bajo `ALGO_SMOKE` el juez sólo lee las reglas del nivel 0), con los argumentos que dio el
dueño en la parada 2, el custodian libre (`preflight.sh`), y la espera por `/sqx-wait` (regla 18).
Pega el embudo (`funnel.csv`) y retira el proyecto al acabar (regla 6: `python3 -m sqx.projects.retire
<P> --role custodian --yes`, worker parado). Si falla: las tres tentativas de la skill y un informe,
nunca un paso a mano ni editar `criteria.yaml` para pasar.

## 6 · Parada 3 — apagar `dev.on`

Sólo cuando el dueño lo diga, con V a la vista. `dev.on: true` hoy en `criteria.yaml:52-56` (sortea 5
supervivientes al azar en el paso 8). Entrega la lista de ficheros y **¿Quieres hacer el commit?**.

---

## 7 · Receta del IS del paso 6 (ex 42, nunca ejecutada; Opus + equipo)

**Entregable (a) del 42**: qué pedir en el *in-sample* del Build de SQX, medido, **cada umbral con lo
que gana y lo que cuesta en estrategias**, por activo × marco × familia donde los datos obliguen a
separarlo y global donde no. «Este filtro apenas ayuda» es una respuesta válida. **El entregable (b)
del 42 (reglas Pasa/Limbo/Falla de los pasos 7-8) lo sustituyó el encargo 44: no se hace aquí** (es el
frente 1). Todo el frente 7 necesita SQX para construir poblaciones: respeta las reglas 3, 10, 14, 15,
18, 19. Antes de gastar una hora de CPU: `python3 -m core.assets <SYMBOL>` de cada activo (regla 5),
enseñar al dueño el spread por tramo de cada activo (una calibración ya se tiró por el spread),
`.claude/skills/sqx-wait/preflight.sh`, y una población de prueba de cinco minutos por activo nuevo
(**ninguno de los 17 activos nuevos ha corrido todavía en SQX**, `OPEN.md` §93): cuenta estrategias y
operaciones, no lo supongas.

### 7.1 El carril — bloqueado por la decisión D1

La población debe ser **sin seleccionar** (aceptación mínima ≥ 100 operaciones en la ventana del build
y beneficio > 0; nada que lea el OOS; el databank **nunca lleno**, porque lleno reemplaza por Ret/DD
del IS y eso ya es una selección) y, en un subconjunto, su **gemela de generación aleatoria**. Las
piezas existen (`sqx.projects.builder --acceptance calibration`, `core/buildfilters.py:65-68`,
`assets/_study.yaml:65-71`; `--random`, `sqx/projects/builder.py`) pero `bin/workflow.sh` no las pasa
y la regla 19 prohíbe conducir los pasos a mano. **No la tomes tú: es D1.** *Reescribir contra el
código actual:* comprobar `grep -n "acceptance\|--random" bin/workflow.sh sqx/projects/builder.py
core/buildfilters.py`, porque el 42 citaba líneas (`workflow.sh:55-56`, `builder.py:184`) que pueden
haberse movido.

Reglas del carril: un trabajo a la vez en el custodio, arranque y parada sólo por
`bin/sqx-worker.sh`; proyectos `Test_Calib_<ACTIVO>_<TF>_<familia><L|S>[_rnd]` (nombre `Test_`, regla 6),
cada uno retirado al completarse; tras aplicar una paleta, **cuenta los bloques encendidos** y las
condiciones de cada estrategia (ninguna pasa de 2 entradas y 2 salidas; si una pasa, para); mide la
caja de tiempo (con 250 × 20 islas una generación son 5.000 individuos) y dile al dueño cuánto dura una
población **antes** del barrido; datos a `AlgoData`, borra el `raw/` de una población cuando su cosecha
esté escrita; como mucho 8-12 procesos de Python y 25 GB libres. Por población: Build → retest OOS
(paso 7, costes de `oos1`, 1 minuto, sin aceptación) → cosecha → la puerta (frente 1) y el mono con
semilla fija (`--seed`); no feedQuality, profitShape ni entryQuality (dueño, 2026-10-02: los dos
primeros ya están borrados).

### 7.2 El diseño — qué medir

Celdas: activo (≥ 10-12) × marco (M30, H1) × dirección (largo y corto, poblaciones separadas, regla 13)
× familia (sólo las que `assets/FAMILIAS.md` lista para ese activo y marco) × generación (genética con
el bloque del dueño, `sqx/projects/buildmode_model.xml`, que no se toca; aleatoria en el control).
Sin plantilla: Simple Strategy, 1..2 entradas y 1..2 salidas (`assets/_build.yaml`). Prioridad si el
tiempo aprieta: ruptura y momentum, largo, H1 y M30 (DJ30, XAUUSD, GBPJPY, USDJPY, EURJPY); después lo
que el prior recomienda sin medida; las «medido en contra» sólo si el dueño lo dice (D4). «Buena» se
define con datos que la regla no lee, se comprueba con dos o tres etiquetas alternativas, **tasas, no
recuentos**.

1. **Paso 6, dosis-respuesta.** Para cada métrica del IS que SQX pueda poner como condición del Build
   (`knowhow/columns/`): operaciones por año (prueba 20, 25, 30, 35, 40 y 50; di qué cuesta y qué compra
   el 35), PF, KER, Sharpe, Ret/DD, SQN, estabilidad, estancamiento, % de aciertos, operación media
   contra el coste. Cuáles predicen un OOS robusto, cuáles no, cuáles son el mismo eje con otro nombre.
   Si el mejor predictor no es una columna de SQX, dilo y da la más cercana. (PF del IS no es hecho
   todavía: una regla `PF >= 1.10` en el paso 8 lo necesita, `OPEN.md` §93.)
2. **A/B dentro y fuera del Build**, con réplicas: cada filtro recomendado puesto como condición del
   Build y como corte después en Python. La vez anterior, dentro perdía estrategias buenas, con un solo
   build por brazo.
3. **La prueba que nadie ha corrido:** un build largo que llena el databank y sigue reemplazando por
   Ret/DD todo su tiempo (180 min) contra uno corto (6 min).
4. **La familia:** ¿la que `FAMILIAS.md` recomienda da más supervivientes OOS que el azar en ese
   activo, contra su gemela aleatoria y su nulo? ¿Cambian los umbrales por familia (frecuencia,
   duración, riesgo flotante en R)? Las celdas sin enriquecimiento son un hallazgo: se listan. Los
   índices, contra comprar y mantener a la misma exposición, no contra cero.
5. **Riesgo flotante** como eje propio (peor día, peor MAE y drawdown sobre neto anual, en R): las
   cuentas de fondeo se juzgan por el flotante.
6. **Equipo rojo.** Un agente con contexto limpio recalcula la propuesta por su cuenta y devuelve
   CONFIRMADO / FALSO / EXAGERADO / SIN APOYO por afirmación. Cuenta con que cambie cifras.
7. **Por el camino real del código** (`facts.per_strategy` → `criteria.resolved` → `criteria.outcomes`)
   en cada población: el embudo por población y agrupado.

**Nulos de la t (ex 42 §3, punto 1.5 del plan 49).** Estrategias sin ventaja simuladas con la doctrina
y los costes de cada activo, más su gemela a coste cero (el punto muerto), sobre las que se calcula
**exactamente** lo que el pipeline calcula (`drift_excess_t`, `trade_t`, misma contabilidad, mismo
ajuste de deriva, mismo n efectivo): una tasa de falsos positivos medida sobre otra estadística no
vale. **Qué cubre ya K (frente 1):** la tasa de falsos positivos de la cadena entera y de cada regla
sobre monos de las poblaciones reales, a los costes de la ficha, con `drift_excess_t` (D-m midió 240.000
estrategias sin ventaja: ~405 en bruto y ~87 netas de costes oos1 por 10.000 a 1,65). **Qué no cubre y
queda aquí:** la **gemela a coste cero** como punto muerto, las líneas de la t **por marco**, la suerte
del PF según el número de operaciones, y `trade_t` (K mide `drift_excess_t`). Antes de lanzar nada,
confirma con el dueño cuánto de esto sigue haciendo falta tras K-m (pregunta Q5). Cierra `OPEN.md`
#91 y #88 en `docs/encargos/49` (punto 1.5) según corresponda.

### 7.3 Lo que entrega el frente 7

El dossier en castellano en `docs/AgentPDFs/` con su PDF (`/dossier-pdf`): la receta del IS, cada
umbral con ganancia y coste, qué varía por activo/marco/familia y qué es global, las celdas sin ventaja
y qué segmento gastó cada cifra; sustituye a los dos dossiers de criterios anteriores (que ya llevan la
cabecera de «no valen»). Las reglas escritas en `assets/_study.yaml` y `criteria.yaml` marcadas como
**propuesta de un agente**, provisionales hasta que el dueño firme. Las poblaciones como filas de la
memoria (`python3 -m studies.research.memory.report --close <run_dir>`). Una ficha de `knowhow/` por
hecho no obvio, `OPEN.md` §93 anotado con `/open-close`, y el capítulo del manual de cualquier comando
que cambie (regla 8). Si el dueño decide (Q6) que los criterios varían por familia, se añade la clave
`by:` de familia a `criteria.yaml` (hoy sólo marco, símbolo y clase de activo), con su test.

---

## Decisiones del dueño — pregúntalas (regla 11)

**De la puerta (ex 44) — se llevan con números, tras K-m (parada 2):**

- **Q1 (ex 44, D / Parada 1).** Ya cerrada: variante **d** (2026-10-07). *Sin respuesta:* la ventana
  (año o semestre; hoy `drift.window: year`) y el AR(1) (dentro o fuera de la fórmula; hoy fuera) — el
  dueño no dijo nada y siguen como estaban. Llévale año y semestre lado a lado con K-m. La ventana
  nunca baja de un trimestre.
- **Q2 (ex 44, Parada 2).** La línea de cada regla de la tabla 1.2, cada una con «a X pierde el A % de
  las de 0,10 y deja pasar el B % de las nulas».
- **Q3 (ex 44).** El tope de R5d (`centring.cap_slope`) y si el ±0,35 de R5 se mantiene.
- **Q4 (ex 44).** H1 y H4: R3 y las reglas nuevas sin excepción por timeframe «por ahora»; sólo queda la
  de R4a en H4. Si K-m enseña que una regla se comporta distinto en un timeframe, se *propone*; no se
  carga. ¿Se propone alguna?
- **Q4b (ex 44).** R1b: el índice deja como opcional un suelo absoluto de 60-80 operaciones en oos1.
  No decidido; pregúntalo sólo si los números de K-m lo piden.
- **Q4c (ex 44, V).** Argumentos de la corrida V: activo, timeframe, con plantilla o simple, cuántas.
- **Q4d (ex 44, P.6).** Si K-m no cabe en una noche: ¿menos estrategias por nivel, o el mono sólo sobre
  las que pasan R3?
- Cualquier punto donde la especificación admita dos lecturas al implementarla: se pregunta, no se
  elige la común.

**De la receta del IS (ex 42, D1-D8) — antes de lanzar el frente 7:**

- **Q5 (ex 42 §3).** ¿Cuánto de los nulos de la t (gemela a coste cero, líneas por marco, suerte del PF,
  `trade_t`) sigue haciendo falta tras K-m, o K ya lo cubre?
- **Q6 (ex 42 §5).** ¿Los criterios han de variar por familia? Si sí: clave `by:` de familia en
  `criteria.yaml`; si no, no se añade.
- **D1 · El carril.** (a) `bin/workflow.sh` aprende a construir poblaciones de calibración (aceptación
  mínima, gemela aleatoria, parada antes de llenar el databank) y todo pasa por él; o (b) autoriza para
  este estudio la llamada directa al builder con `--acceptance calibration` y `--random`, fuera de la
  regla 19. Son dos fábricas distintas: (a) deja una pieza que se mantiene. **Bloquea el frente 7.**
- **D2 · Las paletas.** Tres juegos en `sqx/blocks/palettes/`: los originales (148-180 bloques, con
  bloques de reloj y de stop/limit), los `_v2` (6-13 bloques, «la familia y nada más») y los `_v3`
  (99-127, con `pullback_base_v3`). ¿Cuál usa la calibración? Ninguno consta como aprobado.
- **D3 · La familia `sesion`.** ¿`SessionHigh/Low/Open`, `HighD/LowD/OpenD` y el VWAP anclado cuentan como
  leer el reloj (regla 15)? Hasta que responda, esa familia no se corre.
- **D4 · Celdas «medido en contra»** de `FAMILIAS.md` (7): ¿se gastan builds en ellas?
- **D5 · Operaciones por año en índices × reversión.** El suelo de 35 quita justo la reversión diaria
  de índices que la literatura documenta (5-8 operaciones al año). ¿Excepción, agrupar por clase de
  activo, o se asume la pérdida? Llévale el coste medido. (El suelo mismo, 35/20, ya está decidido.)
- **D6 · La salida.** ¿Toda estrategia debe llevar regla de salida (`exits.condition_required`) también
  con plantilla? Hoy sólo es obligatoria en Simple Strategy.
- **D7 · El presupuesto de máquina.** El 2026-10-02 dijo que 40 horas de builds eran aceptables:
  confírmalo con la duración por población que midas en §7.1.
- **D8 · `oos1` ya fue leído** dos veces para elegir umbrales en USDJPY y XAUUSD. ¿Se vuelve a leer,
  sabiéndolo y diciéndolo en el dossier?

## Lo que no tocas

El master (`~/Desktop/SQX`), ni para leer su configuración de tareas. **`oos2`**: reservado (la
calibración del día 4 lo usó de validación; ésta no), salvo celdas que el dueño autorice para la tarea.
`dev.on` y la firma de los criterios: son del dueño. El bloque genético del dueño
(`sqx/projects/buildmode_model.xml`). La campaña y sus ficheros (`pipeline/campaign/`). El paso 4 de
`studies/data/spread/` (escaneo, `/asset-onboard`, bandas del MC Retest, swap de fondeo). Los criterios
de los demás pasos (10, 12, 14, 20…: encargos 49 y 51). `portfolio/funded/` (encargo 54).
`ledger/thresholds.yaml` sólo gana filas, al final de su sección. La clave
`snoopingScreen.stepm.fwer` del ledger **se queda**: la lee el paso 20. Nada pesado junto a un
workflow en marcha (regla 19). El dueño hace los commits.

## Objetivo — un comando

**Este encargo no tiene un comando que lo cierre:** su final son decisiones del dueño (paradas 2 y 3) y
corridas de SQX (V, y el frente 7), no una salida de test. No se despacha con `/loop`. En su lugar,
`Verificación`:

- `python3 -m pytest -q tests/test_gate_rules.py tests/test_gate_cascade.py tests/test_gate_r3.py
  tests/test_gate_centred.py tests/test_gate_onepass.py tests/test_gate_dataquality.py
  tests/test_gate_delay.py tests/test_gate_resample.py tests/test_gate_mono.py
  tests/test_gate_measures.py tests/test_gate_harvest.py tests/test_false_positives.py
  tests/test_thresholds.py tests/test_autopilot_criteria.py tests/test_ui_gate.py` en verde (por fichero:
  el `-k` sobre `tests/` entero tropieza con `tests/test_oracle_draws.py`, anterior a este encargo).
- la tarjeta `gate-chain-false-positives` de `knowhow/research/` existe y trae las tablas de §1.
- Con la cascada encendida y apagada, el mismo veredicto sobre una población real (ya probado en I, 3.000
  de USA500; se repite sobre cada población de K-m).
- Cada parámetro de la tabla J (`drift.window`, `centring.*`, `cost_stress.k`, `concentration.*`,
  `mae.percentile`, `homogeneity.*`, `drawdown.*`, `monkey.*`, `cascade.on`, `population.*`),
  cambiado desde la ventana, cambia el resultado (`/ui-shot`; J3 lo probó el 2026-10-07).
- V: `funnel.csv` pegado de una corrida de `bin/workflow.sh` sin `--smoke`, proyecto retirado
  (`ls ~/Desktop/SQX_w2/user/projects | grep -c Test_` → 0 de los tuyos).
- `python3 tools/manual.py && python3 tools/depmap.py && python3 tools/checks.py`.

## Cómo cierras

Cada sesión: la tabla de estado y la bitácora de arriba actualizadas · qué hizo · qué verificó, con la
salida pegada · qué dejó sin hacer y por qué · qué descubrió para `knowhow/` (una ficha por hecho no
obvio, editando la que exista) · la lista de ficheros cambiados y, como última línea, **¿Quieres hacer
el commit?** Un encargo cumplido se borra: lo aprendido está en `knowhow/`, el manual y el código.

---

## Lo que sólo vivía en los encargos de origen

**Decisiones del dueño ya tomadas (no se reabren).**
- 2026-10-06: R5 sin dato falla (`missing: fail`); el estado Limbo/Falla de las reglas de dos hechos y
  los bordes de las bandas, como en el fixture; `phi_min/phi_max` iguales a las líneas de z; calidad de
  datos sin variantes propias; semillas **nuevas en cada corrida** y anotadas en el scorecard
  (`q_seed`, `dd_seed`, `mono_seed`; `knowhow/eng/nulls-seed-fresh-per-run.md`); `retraso_t_delta` es la
  t pareada de la misma variante que da el `ret` mínimo; las filas del ledger de las cribas borradas
  salieron (única excepción a «el ledger sólo gana filas»); `feedQuality` sale del paso 8 (el
  inventario sigue saliendo del `scan` del paso 4); `edgeCost` cambió entero (sólo oos1, denominador =
  coste realmente pagado); con la mitad del spread se fueron el paso 25.5, el encargo 36 y `OPEN.md`
  #76 (cerrado, no se reabre).
- 2026-10-07: variante **d** del término de deriva (ventana año y AR(1) fuera de la fórmula, sin
  cambiar); lecturas del mono: tamaño con el ATR de la **barra anterior** (la propia sería mirar al
  futuro), escalones con tamaño de doctrina (ATR o lote medio, nunca los lotes del donante), el mono
  paga los costes de la estrategia, y las duraciones se sortean de todo el oos1; R5 y R5d se centran
  sobre las que llegan a ese nivel (la cascada apagada es sólo diagnóstico); que no pase ninguna de IBS
  es normal; **el mono sin stop vale**; la ventaja plantada de `falsePositives` es **neta de costes**;
  la curva de fondeo (L) se queda como equity desde 0 en R; el percentil del drawdown esperado es
  parámetro (`drawdown.percentile`, 95; dato `dd_esperado_r`); `cpu_s` del catálogo cuenta todo el árbol
  de procesos (`perf/measure/runner.py`); «las poblaciones a medias se olvidan y se harán otras (no se
  repite ningún retest)».
- Principios: 5.000 repeticiones como mínimo por defecto; el trader al azar sólo en OOS (ningún nulo de
  entrada aleatoria toca el build); «Se elimina» = borrar del todo (código, fila de la ventana, paso en
  `plan.py`, objetivo de `perf/`, tests y capítulo del manual); la cascada sale en el primer Falla y
  registra nivel y regla; la t de R3 es **una** sobre todas las operaciones de oos1 (una t por ventana
  no tiene potencia: descartado); un hecho `ret_*` con exceso medio ≤ 0 queda vacío.

**Hallazgos de 2026-10-07 que invalidan datos (comprueba cada uno en su tarjeta antes de usarlo).**
- El repreciado **inflaba los stops**: SQX sella un stop con la apertura de su barra y lo llena al
  precio del stop; `reprice` lo llenaba a la apertura (+290 a +370 USD por operación parada, 30-37 % de
  las operaciones de toda población con stop). Corregido en `reprice.real` (reproduce SQX en NIKKEI225
  y USA500); los 35 sellos fuera de rejilla eran salidas a la apertura de una barra sin sus primeros
  minutos de M1 (`knowhow/export/off-grid-stamps-and-stop-exits.md`, que sí lo recoge). **Invalidados:**
  los pases de estrategias reales de D-m (parada 1) y el embudo de USA500 de I en poblaciones con stop;
  no se rehacen porque las poblaciones enteras guardadas no llevan `Close type` (sólo las cosechas, que
  son de supervivientes). La elección de la variante d se midió con monos sin stop y sigue en pie.
- Operaciones de oos1 cerradas dentro de una barra (stop o target) rompían `level1a.py` y
  `edgeCost/costs.py` (0,04-0,14 % en donchian, emaCloseCross, timeRangeBreakout): estaba preguntado al
  dueño el 2026-10-07 y resuelto en el commit `90d516d`; si reaparece, `git log -S` sobre esas líneas.
- USDJPY: la ficha estaba bien (`tick_size` es el pip de SQX); el repreciado redondeaba el fill de forex
  al pip y no al paso del precio (`tick_step`); corregido (973 operaciones de doubleROC a 0,01 USD de
  SQX); recogido en `knowhow/export/off-grid-stamps-and-stop-exits.md`.
- USA500 con la cascada: 0 supervivientes de 3.000 (358 caen por operaciones/año en IS, 2.248 por R3,
  cuyo máximo es 1,11) — dato de I, medido antes del arreglo de los stops: tómalo como orden de magnitud
  sólo en poblaciones sin stop.
- R3 sobre 240.000 estrategias sin ventaja (D-m): ~405 pasan en bruto y ~87 netas de costes oos1 por cada
  10.000 (3,9 % con el dato de antes de D-m); la variante d deja 0,017 de t de sesgo por lado
  frente a 0,09 de hoy; b es peor que hoy. La t con sesgo y curtosis (sobre operaciones independientes) bajó los
  falsos positivos de USA500 H1 indicesIBS de 6,9 % a 5,1 % a 1,65
  (`knowhow/research/trade-t-vs-frequency-and-skew.md`). B1 reproducido: 1.557 de 10.000 caían por
  presencia, 29 de 169 en la corrida de ejemplo (17 %); arreglado, 0 veredictos movidos en 28 pasos
  guardados.

**Las 25 lecturas del dueño (P.5 bis, 2026-10-06), aplicadas en `reprice.py`, `level1a.py`,
`centred.py`, `delay.py` y el fixture.** Las que NO constan en una docstring que haya podido verificar
(grep antes de borrar nada): «el coste» es la fórmula spread + 2 × slippage + swap + comisión **sin
redondeos**; en cortos el spread va **en la entrada**; el signo del swap es el de la ficha y el de MT5
(negativo = paga el que tiene la posición; comprobado contra Hantec en USDJPY, EURUSD, XAUUSD y JP225);
comisión por tamaño **una vez, en la apertura**; forex en puntos con `tick_step` = tick / 10 (swap por
noche en su orden: USDJPY 0,4-0,8; EURUSD 0,2-0,4); **desviación con n (ddof 0)**, la lectura con la que
la fórmula con sesgo y curtosis se reduce exactamente a la t clásica; la cascada **corta de verdad** (1a
sólo precia a las que pasan el 0; 2 y 3 sólo a las vivas, de lo más ligero a lo más pesado); cuentan
**todas** las anomalías del inventario; `e_fin` con la pendiente centrada y a **mitad** de periodo; las
caídas que llegaron al nivel 1b **llevan** `t_b` y `e_fin`; la que opera los dos lados va a una población
**«ambos»**; una operación más corta que el retraso **no existe** en esa variante (sale de las dos
medias); la ventana de deriva de la movida es la de su apertura movida; `delay.on_build` sólo anota; el
P/L del build para R6 es el del repreciado común a los costes del build; el trimestre de R7, por
apertura; los bloques de R6 nunca dan la vuelta; R6 sobre el P/L. (Nota: `tradelevel.py:71` usa
`ddof=1` para la t clásica `iid`, que es otra cosa: no confundir. Si `ddof 0` de la fórmula con sesgo y
curtosis no está en `analysis/tradelevel.py`, es una divergencia a resolver como pregunta, no a
corregir en silencio.)

**Contratos que otros leen.** `gate.scorecard.*` por nivel: 0 `presencia_passed`, `sanidad_passed`,
`sanidad_value`, `estaticas_value`, `is_trades_per_year`; 1a `drift_excess_t`; 1b `z_frec`, `t_b`,
`e_fin`, `edge_mean_oos`, `t_exceso_k`, `t_sin_mejor_trimestre`, `t_sin_3_mejores`, `mae_p95_r`,
`ret_datos`, `t_a`, `n_afectadas`; 2 `retraso_ret_min`, `retraso_t_delta`; 3 `q_p`, `dd_p`,
`dd_esperado_r`, `z_mono`, `mono_p`, `mono_seed`, y `cayo_nivel`/`cayo_regla`. Sin regla (módulo de
fondeo): `oos_worst_day_r`, `oos_dd_over_net_year`, `oos_net_per_year_r`. `cayo_regla` es texto y
`facts.number()` lo descarta: el juez lo lee del scorecard. Un hecho mal nombrado **no falla, se lee
como Limbo**: `tests/test_gate_rules.py` afirma que los hechos de los niveles cubren los de las reglas.

**Riesgos del plan original que siguen vivos.** Una sola población grande (H1 largo) domina K: nada
sobre H4 ni cortos se propone con ella. El plantado es un exceso constante (frente 1, punto 8). La que
pasa el WFM puede no ser la fila del paso 8 (variantes de 16.5): lo resolvió L, pero comprueba
`pipeline/autopilot/kept.py` si una variante entra.

**Dejado fuera (a propósito).** Del 44: el mono en mercados adicionales, Stouffer y `oos2` («sólo
comentario: fuera de este encargo»); el retest exacto en SQX con ejecución retrasada para finalistas y
la prueba con el feed real de la firma (encargo 54). Del 42: su entregable (b) y sus reglas
Pasa/Limbo/Falla (sustituido por 44), la cola/toolkit/nulos antiguos (borrados), y el texto previo a las
correcciones de costes de `3b71384`.
