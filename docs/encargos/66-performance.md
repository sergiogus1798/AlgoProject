# 66 · Performance: errores y velocidad del Python del workflow

**Qué es.** Plan **vivo**. Es el resultado de una auditoría del Python del workflow hecha el
2026-10-12 en cuatro pasadas (lectura por carpetas → verificación adversaria → presupuesto real de
tiempo y diseños → segunda verificación con datos reales). Recoge **todo lo encontrado**: los
errores, lo que corre en serie pudiendo ir en 48 núcleos, y los rediseños que hacen falta para
que un millón de sorteos por mono sea asequible. La auditoría **no cambió una línea de código**:
cada hallazgo de aquí está por construir.

**La evidencia** — los 22 ficheros de hallazgos y los prototipos con los que se midió cada cifra —
está en `AlgoData/audit/performance-2026-10-12/` (`findings-<FRENTE>.md` y las carpetas de scripts).
Cada sección dice qué fichero leer. Lee el de tu frente antes de tocar nada: trae el `file:line`,
el esbozo de código y la prueba de equivalencia.

**Para la sesión que lo retome.** Lee `CLAUDE.md`, la tabla de estado y **sólo la sección de la
primera fila que no esté ✅**. Cada fila la ejecuta un subagente (modelo en la tabla) con el brief
«ejecuta la sección N del encargo 66; lee `CODESTYLE.md`, el `README.md` de la carpeta y el fichero
de hallazgos que la sección nombra; no toques nada fuera de los ficheros que nombra; si algo admite
dos lecturas, para y dilo». La sesión verifica la entrega y **actualiza la fila y la bitácora antes
de lanzar la siguiente**. Regla 12: un solo árbol, `master`, sin commits por tu cuenta.

## Estado (2026-10-13)

Estados: ⬜ sin empezar · 🟡 en curso · ✅ hecho (fecha y cifra medida) · 🔴 espera al dueño.
Modelo: **O** = Opus (diseño de núcleos, estadística, autoría Java) · **S** = Sonnet · **H** = Haiku.

| # | frente | modelo | depende de | necesita SQX vivo | estado |
|---|---|---|---|---|---|
| 1 | Errores: lo que da un número mal, pierde datos o rompe una reanudación | S | — | no | 🟡 2026-10-13: `draws` por estrategia plegado en diferido (candado por hilo, zstd 9, igual al plegado viejo por `assert_frame_equal`); 16.5 con marcador `.done` (0 llamadas a `wire` con madres acabadas); `ledger/tried.py` con candado; `stopexit` con recorte declarado. probado sin SQX; falta en vivo (16.5 sin sync §7.3). Queda D27 (ledger único) sin diseñar. Tanda 3 (D2, §1.5): los lanzadores de la ventana resuelven una raíz por ejecución (`ui/daemon/runner/rootseed.py`) y la pasan como `--seed`; `ui/daemon/runs.py` ya pasa `--timeframe`. probado sin SQX |
| 2 | Control de falsos positivos (37 % de la corrida) | S | 1 (`draws`) | no | 🟡 2026-10-13: 79,5 → 11,6 s (NIKKEI M30, 200 monos, 2.000 sorteos, 4 pasadas, máquina cargada); `funnel` y `rules` bit a bit; D11 (`z_mono`): 3 columnas de peldaño vacías en `facts`. Revisión independiente: ninguna reutilización inválida. Falta comparar la pasada de la población real completa contra el código viejo |
| 3 | Los sorteos: núcleos del mono y del gate para 1 M | O | 2 | no | 🟡 2026-10-13: mono 3c con núcleo de tabla + PCG64 en numba, bit a bit (1 M × 4 peldaños por estrategia: 111 → 10,8 s con 385 ops; 406 → 48,5 s con 1.532 ops); escalera sin `argsort` (500 ops × 200k sorteos: 5,63 → 1,64 s a 1 hilo, 0,50 s a 4); `drawdowns` ×9-11, `q_null` ×1,6-2,1, `_resampled` pico 128 → 24 MB, `footprint` 87 → 4 MB. probado sin SQX; falta en vivo. No hecho: 3.9d (mueve el último bit en 506 de 3.600 formas; pregunta 3) |
| 4 | Anchura: un comando por test y 48 núcleos donde hoy hay 1, 4, 8 o 16 | S | 1 | no | 🟡 2026-10-13: crossTF, crossmarket, blindJoint, exposure, decay y spread scan sobre `core/fanout.py`; lanzador con reserva de RAM por peso (estudios anchos de uno en uno), `python_step` pliega 16 subprocesos en 1, «FALLARON n de N» llega a `estado.txt`. probado sin SQX; falta en vivo. Tanda 3: mono `--only` (§4.1) reutiliza la raíz guardada y fusiona en `nulls.csv`; se niega sin ejecución previa o con otra semilla, sorteos, peldaños, timeframe, feed, ajustes o export. §4.3 ya cubierto por la tanda 2. forkserver (§4.5) descartado: fork 0,15 s, forkserver 15,5 s con 48 procesos. probado sin SQX |
| 5 | Cruce SQX ↔ Python sin SQX vivo: una pasada, lecturas en paralelo, un proceso | S | — | no | 🟡 2026-10-13: exports tras un paso sólo de los databanks del paso, una pasada de `orderstocsv` (`--exports` + `lineage.csv`), manifiesto con `since`; corte con `refilter` tras el veredicto (`sqx/curate/aftercut.py`). probado sin SQX; falta en vivo (sesión 3: la ruta parada anda, la ruta en vivo falla en la cosecha: `orderstocsv` rechazado, ver bitácora). Tanda 3 (§5.6/§5.7): las tres esperas ciegas (`kill` + `sleep 2` ×2, `sleep 1` tras Xvfb) esperan a la condición real con tope; sondeos a 1 s; `stop` sale en cuanto el proceso se ha ido; paso 26 espera «Strategies loaded». Los bucles que mandan `count` no se acortan. probado sin SQX |
| 6 | `AlgoBank`: el binario por databank | O | 5 | **sí** (conductor) | 🟡 2026-10-13: snippet Java escrito, compilado e instalado SÓLO en el conductor (`install --check` ok); lector `core/bankfile.py`, disparador `sqx/export/membank.py`, carpeta `/dev/shm/algobank/<rol>/<proyecto>`. Sesión en vivo 2: los 11 tests en vivo pasan con la tercera versión del snippet (3 cambios Java, 1 de orden de lectura en `bankfile.trades`). 2 databanks 73.359 operaciones: 1,15-1,19 s frente a 2,95 s de AlgoTrades y 16-27 s por banco de `orderstocsv`; 10.000 estrategias (7,27 M órdenes): 7,8 s frente a 38,6 s; 905 MB de `/dev/shm` por 10.000 y nadie borra el `.abk` aún. AlgoTrades y `orderstocsv` intactos y siguen siendo las rutas en uso: ningún consumidor lee el `.abk`. Falta el conversor/consumidor, el borrado del `.abk` y instalarlo en los otros dos **Tanda E (2026-10-13):** cosecha, otros mercados, `export_trades` y la ruta viva leen operaciones del `.abk`, atado al resultado en disco; AlgoTrades y `memtrades` borrados. Falta la sesión L1 del conductor y, si sale bien, el custodio (Q15 = B). |
| 7 | Esperas de SQX: reaperturas y custodio con un solo proyecto | S | — | **sí** | 🟡 2026-10-13: D6 contestada (medir A y B en el conductor, la mejor). Sin empezar la sesión del conductor: presave 7.1, exports en una JVM, arrancar sólo el proyecto, Build que para solo (D24), recorte de `Results` (D16), 16.5 sin sync 7.3. Tanda 3: presave 7.1 (variante B, `ALGO_PRESAVE=1`) y arranque esperando sólo al proyecto de la ejecución (variante A, `ALGO_AGED_EMPTY=1`) escritos y APAGADOS por defecto; se miden en el conductor y se borra la perdedora. Sesiones en vivo 1 y 2 (conductor, 2026-10-13): presave variante B medida (S15, 3.877 ficheros/79 bancos: parada 52,4 → 7,0 s, +6,6 s en segundo plano = 38,8 s netos, 74 %); variante A NO medida (pide sesión de ≥ 2 h). §7.4a exports en una JVM DESCARTADO: `orderstocsv` no admite varios databanks. §7.4b arrancar sólo el proyecto: sin ganancia a esta escala. Sesión en vivo 3: presave variante B 15,2-15,8 s netos en sesión nueva; la sesión envejecida paró en 12,0 s SIN variante (auto-sync horario de SQX); `ALGO_AGED_EMPTY` no afecta a una parada, la «variante A» de D6 nunca fue de parada; defecto de presave, pendiente del dueño. D24 RESUELTA (`databank-full` para solo 5/5 con `start` tras la carga), pendiente de que `live.start` espere a «APP LOADED». D16 construido, sin probar en SQX vivo. Esperas de `load()` arregladas tras la sesión 1. D16, 7.3 y 7.4d sin medir **Después:** D24 resuelta (5/5 si `start` va tras la carga), guardado previo siempre activo (52,4 → 15,2-15,8 s), arranque que espera a APP LOADED, recorte de `Results` construido sin probar en vivo. Falta 7.3. |
| 8 | Almacén de población sin copia, y el motor por corrida | O | 4, 6 | no | 🟡 2026-10-13: caché de listado con la hora del listado, `_READ`/`_PARTS` con candado y `release()`. D13 no (gorilla es instalación independiente): cae §8.6. probado sin SQX; falta en vivo. Falta lo que depende de 6. Tanda 3: caché de reprecio (§8.5) medida y retirada: 0,49 s sin caché, 0,08 s con ella, ~4 s por madre (el encargo estimaba 12-16 s) **Q16 = A:** 8.2 y 8.3 medidos y descartados (empate; 1,3 %). 8.1 espera a su consumidor. |
| 9 | Velocidad puntual fuera del camino crítico | S | — | no | 🟡 2026-10-13: `atr`, `originals`, `depmap`/`checks`, `inputs.wide` y, nuevo: null de etapa B compilado (1,372 → 0,0004 ms/candidato), `family_d` ventanas 102,5 → 4,4 s, cosido pico 8,18 → 0,26 GB, volteo semanal pico ~8,5 → ~4,5 GB, `entryQuality` a 10.000 sorteos (D14), `sqxretest.stored`, mt5 compare/reconcile, `core/assetdata`. 9.19 borrada por muerta. probado sin SQX; falta en vivo. Tanda 3: CSCV (§9.23) con núcleo numba bit a bit, ×1,8 con 30 variantes y ×1,24-1,32 con 200-1.000 (la fila prometía ×1,33-1,44); lector de ticks en paralelo (§9.8, `core/tickparallel.py`) bit a bit, EURUSD 9,47 → 1,61 s y XAUUSD 20,44 → 3,28 s; `marketProfile` espejo perezoso (§9.9) pico 1.491 → 1.400 MB. probado sin SQX |
| 10 | Que el catálogo de `perf/` mida bien | S | D8 | no | 🟡 2026-10-13: D8 contestada. PSS por `smaps_rollup`, `tracemalloc` sólo con `memtop`; `history.csv` viejo movido a `AlgoData/profiling/_antes-2026-10-13/`. Re-medida del catálogo al cierre |
| ✓ | Cierre: tarjetas de `knowhow/`, manual, dependencias, presupuesto remedido | H | 1-10 | una corrida | ⬜ |

**Orden.** 1 primero (arregla pérdidas de datos y es condición de 2 y 4). Después 2, 4 y 5, que son
Python puro y entre los tres se llevan la mayor parte del tiempo que no es SQX calculando. 3 y 8 son
los que hacen viable el millón de sorteos. 6 y 7 esperan a un hueco del conductor.

### Bitácora

- 2026-10-12 — auditoría cerrada (seis pasadas). Seis preguntas de `AlgoBank` ya contestadas por
  el dueño (§6). Tres vías descartadas por él (§«Descartado»).
- 2026-10-12, noche — **construido sin SQX y sin commit**, sólo lo que se pudo probar idéntico o
  era un bug; tests en `tests/test_perf66_bugs.py`, `test_perf66_cruce.py`, `test_perf66_p6.py`
  (34 pasan), `depmap` y `checks` en 0 problemas. Lo que sigue ya **no** está pendiente:
  - **Errores (§1):** `draws.merge` con candado (16 estrategias en 8 procesos: quedan las 16; el
    coste cuadrático sigue, §1.1) · Drawdown de `united` · `plan.reopen` tras una corrida cortada
    y con carpetas sin `estado.txt` · `screened` nunca baja · `keep.keep` que lanza marca la celda
    `failed` y la campaña sigue · `varianttrades` ya no depende de la medianoche · `monkey/many`
    dice cuántos pares descarta y sale claro si no queda ninguno · `sharpe_std` con un candidato ·
    escrituras atómicas en `ledger/cells.py`, `core/barstore.py` y `core/study/output.py` ·
    candado en `cells.note` y `look_oos2` (8 procesos: 8 miradas, 8 filas) · `excursions.rebuild`,
    `plateau.above_half_max`, `touch.bars`, `attempts.NAME` (`Research_`) · tres caminos de fallo
    del almacén · docstrings de `simulate.py` y `cascade.py`.
  - **Cruce (§5), MEDIDO con 8 núcleos sobre `.sqx` reales:** `sqxview.frame` 2,99 → 0,40 s ·
    `collect` (métricas, curva y timeframe en una lectura) 1,75 → 0,48 s · identidades en
    paralelo con la caché del padre llena (`core/identities.py`) · `neighbourbatch.write`
    15,3 → 2,5 s, bytes idénticos · `store/extra._mask` por categorías 125,6 → 2,4 s ·
    `fanout` cancela la cola al primer fallo (4,0 → 0,01 s) y deja numba a un hilo en los hijos ·
    `spp` ya no revienta si falta «Total tested» (**sin probar en vivo**).
  - **Esperas (§7):** `chain.load` no exporta las operaciones de los MCR (~30 s por corrida) ·
    la fase `execute` partida en `execute.sqx` y `execute.sync` para que `fases.csv` no cuente
    sync como cálculo.
  - **Gate y demás:** `inputs.wide` en vez del `pivot` de la equity, 15,7 → 4,2 s,
    `DataFrame.equals` sobre 30 M de filas reales · un solo `draws.save` en crossTF ·
    `originals.read` con filtro 1,36 → 0,47 s · `atr` con `njit` (×30, `array_equal`) ·
    `depmap` + `checks` 10,6 → 7,9 s · `ZipFile` cerrados.
  - **Resultados que cambian con estos arreglos:** el Drawdown de las uniones del 16.5 sube
    cuando la curva empieza perdiendo; `above_half_max` cuando el máximo es ≤ 0; `touch.bars` en
    operaciones de la primera barra; los `Research_` entran en el mapa de intentos; `screened`
    por celda deja de encogerse al re-juzgar.
  - **No hecho de lo pedido:** ningún código muerto borrado (todo candidato sigue citado en el
    manual, una tarjeta o un test → D23); `tradestore.py:134,152` (no demostrable idéntico);
    el fan-out del 3ab, el núcleo de tabla y todo `falsePositives/` quedan para los frentes 2 y 3.
  - **Tests que ya fallaban en `HEAD` y siguen fallando** (no son de esta noche):
    `test_close_curve` (`blindJoint.inputs.moves` no existe), `test_mt5verify`,
    `test_portfolio_build` («ningún miembro concilia»), `test_strategymeta` (sha de la ficha de
    XAUUSD). Como script o como pytest, también en `HEAD`: `test_portfolio_stageb`,
    `test_portfolio_stopread`, `test_research_memory`, `test_ui_sqxconfig_studies`
    (`KeyError: 'categories'`), `test_ui_strategy` (`KeyError: 'backtest'`). `test_taxonomy`
    falla sólo en el árbol, por el `sqx/blocks/taxonomy.yaml` sin commit de otra sesión (8
    bloques fuera de esquema). Comparación hecha contra un `git archive HEAD` limpio. Y `pytest tests` entero no se puede lanzar: varios `test_*.py` son scripts que
    llaman a `sys.exit` al importarse; se corren fichero a fichero
    (`scratchpad/impl/alltests.sh`).
- 2026-10-13 — **construido sin commit**; `depmap` y `checks` en 0 problemas, los once
  `tests/test_perf66_*.py` en verde. SQX sólo se tocó en el conductor, para la prueba de §7.1.
  - **Código muerto borrado (D23):** `engines/nulls/filter.py`, `engines/nulls/placement/kernel.py`
    y `bootstrap.py`, `pipeline/run.py`, `pipeline/stages/`, `pipeline/verify/`,
    `tests/test_pipeline_verdict.py`, con sus citas en READMEs, tarjetas, `OPEN.md`, el mapa de
    carpetas y los capítulos 12 y 17 del manual (PDF regenerados). **De más:** el agente borró
    también `pipeline/stubs/` (se recupera con `git checkout pipeline/stubs`) y dejó
    `pipeline/recipe.yaml` sin lector → **D29**.
  - **Lo que ya no se escribe (D17, D18):** el `.html` por estrategia (`output.member` escribe
    sólo el JSON) y `marketSurfaces_detalle.json` (`contract/grids.py` y `words.py` borrados).
    **D20 no se hizo:** el JSON de las caídas del gate lo leen `ui/daemon/results/store.py`,
    `hits.py`, `matrix.py`, `ui/daemon/databank/cells.py`, `core/archive/collect.py`,
    `core/store/late.py` y `pipeline/autopilot/facts.py` → **D30**.
  - **BLAS a un hilo en el 18.5: no aplicado.** Sobre las tres madres reales ρ, p y veredicto
    salen idénticos, pero los vectores del nulo guardados de USATEC difieren hasta 4,4e-6: más
    que «el último bit» que se prometió → **D31**.
  - **D21 y D28 en código:** `core/store/save.py::cell_of` (`…_simple_long` / `_short`, con
    test); `bin/workflow.sh` retira el proyecto si la paleta o el recorte fallan a medio crear.
  - **Skills y tarjetas:** ocho skills de paso y `workflow-simple` corregidas (regla 19, el
    `action=count` de `oos-gate`, tiempos, T2/T3); catorce tarjetas de `knowhow/` nuevas o
    corregidas (§7 bis).
  - **Prueba en vivo de §7.1 (conductor, `Test_` retirado):** `synchronizeDatabank` antes de
    salir deja las líneas de guardado de la salida en 0 y la parada en 5,8 s contra 10,9. A
    escala (175 databanks, custodio), sin medir.
  - **Caza de bugs Python ↔ SQX** (dueño: «quiero que no haya ningún bug en la conexión»): dos
    cazadores, dos arregladores con ficheros disjuntos y una revisión independiente de sus
    diffs. Informes en `AlgoData/audit/performance-2026-10-12/findings-BUG1.md`, `-BUG2.md` y
    `-REVIEW.md`. Arreglado, con test en `test_perf66_sqx.py`, `test_perf66_sqxprojects.py` y
    `test_perf66_launch.py`:
    - `bin/sqx-worker.sh stop` borraba, tras minutos de export, el candado que un `start`
      concurrente acababa de escribir; ahora sólo quita el que capturó al entrar. `_WHERE` leía
      un warning de Python como ruta del master; `run` devolvía el código de `grep`.
    - `live.sync` no sincronizaba un databank reescrito con el mismo número de estrategias
      (`force`, espera la línea «saved» de SQX); `live.cut` falla si un nombre se quedó;
      `live.start` nombra los databanks que no cargaron; `exiting.stop` sigue el log pasada la
      medianoche.
    - `execute.run` (ruta `--restart`) acaba con «Project finished» y comprueba las respuestas;
      tope por tarea también en esa ruta y en los dos lanzadores de la ventana (`sqxlog.watch`).
    - `export_retest` arrastraba `_staging` de una corrida rota; `varianttrades` se niega sin
      export del lote o con el de otro lote; `export_trades` falla antes de escribir con un
      databank vacío; `export_metrics` ya no borra subcarpetas.
    - `taskcap.note`, `sessiondb.copy`, `patch.install_template`: escrituras enteras.
      `crosstfload.refill` copia antes de borrar. `retire` no pisa el archivo de un retiro del
      mismo día. `registry.NAME_OK.fullmatch` (un `\n` final pasaba). `harness.spp` falla si a
      la tarea le falta una etiqueta (era silencioso con `--kind retest --spp`).
    - Un solo autopiloto por worker (`pipeline/autopilot/entry.py`, `flock`), y no adopta una
      sesión GUI que no arrancó él. `afterrun` sale con error si una pieza falla; un fallo en la
      parada y export final escribe su FALLO en `estado.txt`. El paso 26 ya no lee una carga o
      un sync fallido como «SQX no operó».
    - **La carrera export ↔ corte:** el manifest se fecha al empezar el export
      (`core.manifest.write(since=)`), así un databank cortado mientras se exportaba se lee
      `stale` y no queda firmado como fresco.
  - **Queda abierto de esa caza:** tras un `live.start` fallido la sesión se deja arriba con
    memoria incompleta: resuelto, D32. El paso 26 supone que un retest
    con la aceptación silenciada deja siempre su estrategia en el databank de salida: comprobarlo
    en el conductor. 
    `bin/clone-sqx-worker.sh:21` mezcla stderr en `_WHERE` como hacía el worker. Y
    `bin/sqx-worker.sh:401` sigue con `afterrun … || true`: el `stop` no falla por un export.
  - **Decidido y sin construir:** D24, D16, D27, el PCG64 en el núcleo, el retiro automático del
    `Test_` al final de `bin/workflow.sh`, y `presave` a escala.
- 2026-10-13 — **tandas 1 y 2.** Construido sin SQX vivo y sin commit.
  - **Qué se hizo.** Por fila de la tabla:
    - 1: `draws` por estrategia plegado en diferido (candado por hilo, zstd 9); 16.5 con marcador `.done`
      (hash de brief, config de variantes, patas, ficha de costes e identidad de la madre); `ledger/tried.py` con candado; `stopexit` con recorte declarado.
    - 2 y 3: control de falsos positivos; mono 3c con núcleo de tabla y PCG64 en numba; escalera sin `argsort`
      con hilos sobre bloques sembrados; `drawdowns`, `q_null`, `_resampled` y `footprint` sin matriz.
    - 4: crossTF, crossmarket, blindJoint, exposure, decay y spread scan sobre `core/fanout.py`; lanzador con
      reserva de RAM por peso; `python_step` pliega 16 subprocesos en 1; «FALLARON n de N» llega a `estado.txt`.
    - 5: exports tras un paso sólo de los databanks del paso, una pasada de `orderstocsv`, manifiesto con `since`
      (se borra antes de reescribir); `refilter` tras el veredicto, sin interrumpir el corte.
    - 6: snippet Java **sin compilar**, `core/bankfile.py`, `sqx/export/membank.py`, `/dev/shm/algobank/<rol>/<proyecto>`.
    - 8: caché de listado con la hora del listado; `_READ`/`_PARTS` con candado y `release()`.
    - 9 y cartera: pares rodantes, días, redundancia; null de etapa B compilado; `family_d`; cosido; volteo semanal;
      semillas de caminos sin repetidas (numba guarda 32 bits); `entryQuality` a 10.000 sorteos; `sqxretest.stored`; mt5 compare/reconcile; `core/assetdata`.
    - 10: PSS por `smaps_rollup`; `tracemalloc` sólo con `memtop`; `history.csv` viejo movido a `AlgoData/profiling/_antes-2026-10-13/`.
    - `bin`: `workflow.sh` retira el `Test_` al acabar bien (`--own`; no con `--until`; no tras un fallo);
      `sqx-worker.sh stop` sin `|| true` (FALLO a stderr y a `user/log/FALLO-export.txt`); `clone-sqx-worker.sh:21` sin `2>&1`.
    - Tests que fallaban de antes, arreglados: `test_close_curve`, `test_mt5verify` (dos afirmaciones contrarias a la regla escrita), fixtures de `strategymeta` y `ui_strategy`, y los tres de cartera (el código estaba bien: datos archivados antes del cambio de reloj y comisión; pool `Test_nikkei_ref` regenerado en la raíz de pruebas). `test_taxonomy` sin tocar.
    - Código borrado (regla 21): `pcg.integers`, la rama de niveles por operación de la escalera (`_priced`, `barrier.exits`), `consolidate_reports`, `_per_bar`; 9.19 por muerta.
  - **Qué se verificó** (máquina cargada por otros agentes: las cifras son pesimistas):
    - `python3 tools/depmap.py && python3 tools/checks.py` → «1596 files checked, 0 problems».
    - Todos los `tests/test_perf66_*.py` uno a uno, más los de la zona: 337 tests de pytest pasan, 0 fallan.
    - Scripts con rc=0: `test_worker_lifecycle`, `test_strategymeta`, `test_ui_strategy`, `test_oracle_rungs`, `test_nulls_seed`, `test_mt5verify`, `test_portfolio_build`, `test_portfolio_stageb`, `test_close_curve`, `test_portfolio_search`.
    - Control de falsos positivos 79,5 → 11,6 s (NIKKEI M30, 200 monos, 2.000 sorteos, 4 pasadas); `funnel` y `rules` bit a bit.
    - Mono 3c bit a bit y mismo estado del generador: 1 M × 4 peldaños por estrategia 111 → 10,8 s (385 ops), 406 → 48,5 s (1.532 ops).
    - Escalera, 500 ops × 200k sorteos: 5,63 → 1,64 s (1 hilo), 0,50 s (4 hilos).
    - `drawdowns` ×9-11; `q_null` ×1,6-2,1; `_resampled` pico 128 → 24 MB; `footprint` 87 → 4 MB.
    - Null de etapa B 1,372 → 0,0004 ms/candidato; `family_d` ventanas 102,5 → 4,4 s; cosido pico 8,18 → 0,26 GB; volteo semanal pico ~8,5 → ~4,5 GB.
    - **Nada de esto se ha probado en SQX vivo.**
  - **Qué deja de reproducir lo guardado:** los caminos T1/T2, los nulls de etapa B (y lo que `funded_b` sortea después). `worst_path` pasa a ser reproducible (semilla fija en `stitch.py`). En `facts` quedan vacías las 3 columnas de peldaño (D3 sí, D11 `z_mono`).
  - **Qué no se hizo y por qué:**
    - 3.9d (`measure` del wfc en bloques): mueve el último bit en 506 de 3.600 formas → pregunta 3.
    - Todo lo que necesita SQX vivo: sesión del conductor sin empezar (presave 7.1, exports en una JVM, arrancar sólo el proyecto, Build que para solo D24, recorte de `Results` D16, 11 tests de `AlgoBank`, comprobación del retest silenciado del paso 26, 16.5 sin sync 7.3).
    - D27 (ledger único): sin diseñar; se presenta al dueño antes de construir.
    - Medidas a escala en el custodio (N9 A, con aviso), re-medida del catálogo `perf/` y capítulo 12 del manual: al cierre.
  - **Incidente.** Un agente ejecutó `git stash` y `git stash pop` por error sobre el árbol compartido. Comprobado después: sin conflictos, todo compila, los tests pasan.
  - **Tres revisiones independientes** (Opus, sólo lectura): `/dev/shm/tmp66/review-sqx.md`, `review-data.md`, `review-2.md` y `review-3.md`. Todos sus hallazgos corregidos salvo los que quedan abiertos en las preguntas nuevas 1-6.
- 2026-10-13 — **tanda 3.** Construido sin SQX vivo y sin commit.
  - **Hecho.**
    - 1: mono con una raíz por ejecución en los lanzadores de la ventana; `runs.py` pasa `--timeframe` o se niega.
    - 4: mono `--only` (§4.1) con raíz guardada; capítulo `26-nulos.md` de las fuentes del manual actualizado (PDF sin regenerar).
    - 5: esperas ciegas sustituidas por esperas a la condición con tope; paso 26 espera «Strategies loaded»; `mt5/reconcile/config.yaml` con las claves nuevas.
    - 7: presave (variante B) y arranque esperando sólo al proyecto (variante A), apagados por defecto.
    - 9: CSCV con núcleo numba (32 tests); lector de ticks en paralelo (bit a bit en EURUSD, 306 M ticks, y XAUUSD, 651 M); `marketProfile` espejo perezoso.
  - **Medido (cifras).**
    - CSCV: ×1,8 con 30 variantes, ×1,24-1,32 con 200-1.000. El coste mayor queda en el Sharpe.
    - Ticks: EURUSD 9,47 → 1,61 s; XAUUSD 20,44 → 3,28 s; 2,91 s la primera lectura de cada proceso, por compilar. Sin caché de numba en disco: se quedaba obsoleta.
    - `marketProfile`: pico 1.491 → 1.400 MB (−6 %), CPU 71 → 68 s (la fila estimaba 15-30 %).
  - **Descartado tras medir.** Caché de reprecio §8.5: 0,49 s sin caché, 0,08 s con ella, ~4 s por madre (estimado 12-16 s); retirada, `engines/variants/excess.py` sin cambios. forkserver §4.5: fork 0,15 s, forkserver 15,5 s con 48 procesos; no se construye. §4.3: ya satisfecho por la tanda 2. `marketProfile` por trozos (D12): no construido, pregunta 8.
  - **No hecho y por qué.**
    - Exports de un paso en una sola JVM (§7.4a): no consta que `orderstocsv` acepte varios databanks por lanzamiento; experimento del conductor.
    - D24 (Build que para solo): `databank-full` y `passed-count` tienen tarjetas que dicen que no pararon como se esperaba; se miden los dos en el conductor.
    - D16: pregunta 7.
    - Esperas de `load()` en `sqx/variants/execute.py` (4 × 2 s y 8 s): no hay señal por databank que no sea `count`; conductor.
    - `memtrades` en una sola tarea: necesita el snippet Java; va con AlgoBank.
  - **Cuarta revisión** (Opus, sólo lectura, `/dev/shm/tmp66/review-4.md`): 17 hallazgos, todos corregidos. 8 puntos sólo se resuelven en vivo (lista del conductor). Tarjetas nuevas de `knowhow/`: `perf/numba-cache-ignores-inlined-dependencies.md` y `research/cscv-four-deviations-from-the-published-statistic.md`.
  - **Qué se verificó.**
    - `python3 tools/depmap.py && python3 tools/checks.py` → «1606 files checked, 0 problems».
    - Los 39 `tests/test_perf66_*.py` uno a uno, más `test_sqx_bridge` y los de la zona: 435 tests de pytest pasan, 0 fallan; 13 scripts de test con rc=0.
    - **Nada de esto se ha probado en SQX vivo.**

- 2026-10-13 — **sesiones en vivo 1 y 2 (conductor).** Informes: `/dev/shm/tmp66/live-session-1.md` y `live-session-2.md`. Sólo conductor (5060), proyectos `Test_Perf66_*` XAUUSD H1 retirados todos; worker parado por el script, sin OWNER ni `sqcli`. Sin commit.
  - **Medido, sesión 1.**
    - Base: arranque→listo 16,6 s, parada 5,9 s (17 ficheros, 1 banco). Modo CLI: 10,6 s al arrancar, parada 2,1 s, 0 líneas de guardado.
    - Salida de SQX sin presave: lineal en bancos cargados. S1 (177 ficheros/5 bancos) 13,0 s; S5 (1.477/31) 27,1 s; S15 (3.877/79) 52,4 s. Serie, ~0,3-0,6 s por banco de 50.
    - Presave variante B: S15, 77 bancos en 6,6 s (en paralelo; 5,4 s son de `Retester/Results`), parada 7,0 s: 52,4 → 7,0 s, 38,8 s netos (74 %). Se queda B. Interferencia con la primera tarea: 3,49 s frente a 1,42 s, confundida con el arranque en frío; no hay motivo para retrasarla.
    - §7.4b sólo el proyecto: 24,7 frente a 24,9 s (177 ficheros), 27,8 frente a 28,2 (1.477), 31,0-31,8 frente a 30,7 (3.877). Sin ganancia: los 84 s del custodio no se reproducen con 3,9 k ficheros; ni confirmados ni refutados.
    - `orderstocsv` sin sintaxis multibanco: un banco 14,3-14,6 s; `file="A;B"` y la carpeta madre fallan (rc 1); `file=A file=B` da rc 0 y exporta SÓLO el último.
    - `clear` síncrono (8-16 ms); `load` asíncrono, línea «Strategies loaded» 0,26 s después para 50 ficheros; `synctofiles` síncrono (0,4-0,7 s por 50).
    - D24: `databank-full` (Max 50) paró solo a los 50 (105,6 s CLI / 110 s GUI); `passed-count` 30 paró en 30 (97 s).
    - Retest con 0 operaciones: un retest silenciado deja en la salida las estrategias sin operaciones (30 → 30 `.sqx`, 10 con 0 operaciones) mientras el estado dice «Failed 30, Passed 0».
    - Regla 1: ningún recuento ni nombre de ficheros cambió en ningún ciclo.
  - **Medido, sesión 2 (AlgoBank).** Los 11 tests en vivo pasan (compila a la primera en 3 instalaciones; operaciones, métricas de 116 claves, identidad, equity, otros tipos de tarea, banco vacío, banco en escritura, 10.000 estrategias, tras parada y arranque).
    - 2 bancos, 73.359 operaciones: AlgoBank 1,15-1,19 s; AlgoTrades 2,95 s; `orderstocsv` 16-27 s por banco. 4 bancos pequeños: 1,04-1,11 s frente a 4,5 s. 17 estrategias WF (472.733 órdenes): `orderstocsv data=all` 168,3 s, AlgoBank ~1 s.
    - 10.000 estrategias (7,27 M órdenes): `membank.run` 7,8 s; carga 1,5 s + operaciones 4,9 s; AlgoTrades 38,6 s. El plan estimaba 30-50 s para `export.trades` (569 s).
    - 905 MB de `/dev/shm` por 10.000 estrategias; nadie borra el `.abk` todavía.
    - Cambios: tres en `AlgoBank.java` (la excepción `StatsDontExistException` se captura; `getDouble(name, NaN)`; cabecera XML y CRLF para que el hash de identidad coincida) y uno en `core/bankfile.py` (`trades()` ordena por nombre de fichero).
  - **Descartado tras medir.** Exports de un paso en una sola JVM (§7.4a): no existe sintaxis multibanco; sólo cabría reunir todo en una carpeta plana con renombrado por banco (~14 s por banco ahorrados). §7.4b: sin ganancia a esta escala. Variante A: no descartada, no medida.
  - **Arreglado tras la sesión 1.**
    - Presave (`sqx/projects/presaving.py`): `_work` espera, con tope `LOAD_S`, a que un banco «Auto-sync never» tenga tantos registros como ficheros antes de listarlo (`Retester/Results` se saltaba por seguir cargando).
    - `load` sin esperas ciegas: espera la línea «Strategies loaded»; `loadwait` también; sin los `sleep` tras `clear`.
    - `KeyError: 'DoFRatio'` en `studies/screening/gate/collect.py`: conserva el valor de SQX cuando la columna existe (los snippets DoFRatio/ParameterCount se quitaron de SQX el 2026-10-06).
  - **Sigue sin medir.** Variante A de presave (sesión ≥ 2 h: SPP/WFM envejecida, log de GC); D16; 7.3; 7.4d; escala por encima de 3,9 k ficheros; hueco en el borrado del `.abk`; 7.4b en el custodio. Un sync de un banco ya limpio no escribe línea: `live.sync(force=…)` y el presave esperarían hasta el tope (seguro hoy; sin parchear).
  - **Tres puntos abiertos (no resueltos).**
    - (i) D24 contradictoria: la sesión 1 vio parar solo un Build `databank-full` a los 50; la sesión 2 vio el mismo tipo de parada repetirse (63+ «Build finished because databank is full», sin «Task finished») hasta cerrar la sesión. No se sabe qué las distingue. D24 sigue ABIERTA; tarjeta 🤔 en `knowhow/sqx-drive/live-chain-without-restart.md`.
    - (ii) Incumplimiento de la regla 18 en la sesión 1: un bucle propio de sondeo a 1 s durante 112 s en vez de `wait.sh`.
    - (iii) `Retester/Results` del conductor ya no es idéntico byte a byte a la instantánea `AlgoData/snapshots/conductor-2026-10-13-encargo66`: SQX reescribe las estrategias cargadas al salir. Identidad, estadísticas y órdenes iguales en las 17. Tarjeta `knowhow/databanks/sqx-rewrites-loaded-files-at-exit.md`.
  - **Hallazgos fuera de lo tocado.** NPE interno de SQX tras acabar un retest (`wait.sh` lo da por fallado); `wait.sh` no distingue proyectos; un arranque GUI colgado en el diálogo de licencia; el decodificador offline de `orders.bin` lee mal las filas WF.
  - **Tarjetas.** Nuevas: `export/orderstocsv-no-multi-databank.md`, `sqx-drive/retest-zero-trades-stays-in-output.md`, `sqx-drive/snippet-stats-api-traps.md`, `databanks/sqx-rewrites-loaded-files-at-exit.md`, `perf/algobank-vs-algotrades-vs-orderstocsv.md`. Editadas: `databanks/databank-verbs.md`, `sqx-drive/retire-own-and-wait-per-task.md`, `sqx-drive/live-chain-without-restart.md`. Instantáneas `...-encargo66` y `...-encargo66-abk` en `AlgoData/snapshots/` (borrables).

- 2026-10-13 — **sesión en vivo 3 (conductor) y decisiones del dueño.** Informes: `/dev/shm/tmp66/live-session-3.md` y `review-6.md`. Sólo conductor (5060), 11 proyectos `Test_Perf66_*` retirados, worker parado, sin OWNER; recuento de `.sqx` por banco idéntico a la instantánea `conductor-2026-10-13-live3`. Sin cambios de código en la sesión. Commits `f55ad52` y `64d9300`, subidos.
  - **D24 resuelta.** 🔬 `databank-full` para solo **5/5** si `start` se manda tras la carga (1 línea «full», «Task finished» 2-7 ms después, «Project finished» ~1,5 s); **0/5** si se manda 6-7 s antes de «APP LOADED»: bucle de 52-104 líneas, sin «Task finished», `project action=stop` contestado pero inútil, sólo la salida de la app lo corta. `passed-count` 30: 3/3. Es lo que distingue las sesiones 1 y 2. Dueño: **N7a = A** (el ajuste existe), **N7b = A** (el paso 8 recibe las primeras 10.000 aceptadas). Se está haciendo que `live.start` espere a «APP LOADED». Tarjeta `sqx-drive/build-full-loop-needs-app-exit.md`.
  - **Export acotado al paso.** 🔬 Ruta parada: anda (30,8 s la primera llamada con un `orderstocsv`; 1,8 s la segunda, ninguno). Ruta EN VIVO: **falla**: la pieza `harvest` lanza `orderstocsv`, rechazado mientras la sesión GUI tiene la instalación («REFUSING: another sqcli already holds»). Las operaciones sí salieron de memoria (`memtrades`). **Abierto:** en sesión viva la cosecha debe leer de AlgoBank (tanda E). Tarjeta `export/orderstocsv-refused-in-live-session.md`.
  - **Recorte de `Results` tras el paso 8 (D16; dueño P1 = A, P2 = A).** Construido con tests; la sexta revisión lo corrigió: la negativa es una línea de informe «RESULTS SIN RECORTAR:» y nunca mata el paso 8; el export previo al recorte se vuelve a firmar; se niega sin la cosecha completa de `Results`. **NO probado en SQX vivo**: no hay entrada de un solo paso para el 8 (`judge.judge` pide `facts.gather`, los 12 estudios) y `bin/workflow.sh` está fijado al custodio.
  - **Presave.** 🔬 Parada normal 52,4 s ×3 en sesión nueva (18 proyectos, 3.233 ficheros). Variante B: parada 8-9 s + 6,7-7,8 s en segundo plano = **15,2-15,8 s netos** (ganancia ~37 s). La sesión envejecida (131,5 min) paró en **12,0 s sin variante**: el auto-sync horario de SQX guardó 120 bancos a las 14:41. `ALGO_AGED_EMPTY` no afecta a una parada (sólo vacía la reapertura antes de SPP/WFM envejecidas): la «variante A» tal como la define D6 nunca fue una variante de parada. **Pendiente del dueño: defecto de presave.** Tarjeta editada: `databanks/exit-regrabs-loaded-databanks-by-session-age.md`.
  - **Construido hoy con las respuestas del dueño.**
    - Los cuatro peldaños comparten un flujo de sorteos (N12 = B): varianza de la diferencia pareada 0,14-0,43 de la independiente; los resultados guardados antes de hoy no son comparables.
    - Nulo del `wfc` por bloques: pico 788 → 48 MB en el caso de prueba, igual a 1e-12.
    - CSCV rechaza un número impar de bloques (P8 = B).
    - `Param Count` y `DoF Ratio` salen siempre de Python (P9 = A); OPEN #86 anotada, no cerrada.
    - Reloj y comisión del miembro congelados en el manifiesto del archivo (Q5 = A, Q6 = B): construido; simulacro del relleno de los ya archivados: 38 de 73 miembros rellenables, 35 USDJPY con el feed viejo de the5ers no rellenables, pendiente del dueño.
    - Encargo 67 redactado (filtro mínimo calibrado con datos sintéticos); no existe generador sintético en el repo.
  - **Otras respuestas del dueño:** P4 A, P7 A, P10 B, P15-P17 A.
- 2026-10-13 — **tanda E: las operaciones de una sesión viva salen del `.abk`, y dos rutas nada más.** Plan en el scratchpad (`plan/tanda-E.md`), revisión independiente en `/dev/shm/tmp66/review-7.md`. **Nada de esto está probado contra SQX vivo todavía** (sesión L1 del conductor, abajo).
  - **Construido (probado sin SQX).**
    - `core/bankfile.py`: `trades()` y `pack()` devuelven lo mismo que `tradepack.pack` (test permanente: el mismo banco escrito como `.abk` y como CSV de `orderstocsv` da el mismo parquet, en modo principal, todos los mercados y subconjunto).
    - `sqx/export/membank.py`: `run(role, project, bancos)` y `take(...)`, que sólo acepta un `.abk` si carga, su modo es el pedido, sus nombres son los pedidos, su identidad coincide (`core.sqxfile._hashed`) y **cuadra con el resultado en disco** (`core.bankframes.unbound`: nº de órdenes = «# of trades», suma de Profit/Loss = Net profit con tolerancia `0,01 + 1e-6·|Net profit|`). Medido sobre 1.114 estrategias reales: 100 % cuadran, diferencia máxima 0,0037. `take` borra el fichero al cargarlo.
    - Consumidores: la cosecha (`studies/screening/gate/collect.py`, `harvest.py`), `sqx/export/export_retest.py` (otros mercados), `sqx/export/export_trades.py` y la ruta viva `ui/daemon/launch/liverun.py` (`dump` vuelca sólo los bancos sin leer; `export` lanza `afterrun --live` y borra la carpeta del banco al terminar, pase lo que pase).
    - Un `.abk` que no vale cae a `orderstocsv` con la razón escrita; en sesión viva del conductor eso es un fallo con mensaje, no un silencio.
  - **Borrado (regla 21; Q14 = A, dos rutas).** `sqx/export/memtrades.py`, `tests/test_memtrades.py`, el snippet `AlgoTrades.java` y sus citas (7 tarjetas, manual 111). `sqx/snippets/install.py` ahora quita de la instalación los snippets que ya no están en el repo.
  - **Arranque.** `live.start` vuelve sólo tras «BrowserGUI - APP LOADED» (`loadwait.booted`, tope 300 s; una sesión que no terminó de cargar se mata por PID y se dice) y se niega si la instalación ya tiene un proceso.
  - **Guardado previo a la salida: siempre (Q12 = A, Q13 = A).** Sin interruptor: fuera `ALGO_PRESAVE` y `ALGO_AGED_EMPTY`, fuera `tests/test_perf66_liverun_aged.py`. Cifra medida en la sesión 3: 52,4 → 15,2-15,8 s.
  - **Revisión 7 (Opus, sólo lectura), arreglada antes de seguir.** Un `.abk` viejo se podía aceptar y uno bueno rechazar por la hora del fichero → sustituido por el cuadre con el resultado; `booted` podía matar una sesión ya cargada → `live.start` se niega si hay proceso; faltaba un `mkdir` en `export_retest`.
  - **Revisión 8 (Opus, sólo lectura; `/dev/shm/tmp66/review-8.md`), arreglada.** Crítico, sin llegar a ejecutarse: la poda de `install.py` comparaba toda `user/extend` con los 3 ficheros del repo y habría borrado ~800 ficheros de SQX y del dueño (bloques, columnas, plantillas de código) → ahora borra sólo lo nombrado en `install.DROPPED`, y `pending` lo lista (el conductor y el custodio aún tienen `AlgoTrades.java`: sale en L1). Un `.abk` con dos lectores (cosecha y operaciones) lo borraba el primero → `take` ya no borra; lo quitan `run`, el fin del export y la parada. Un banco pedido en dos modos a la vez se rechaza por nombre.
  - **Sesión en vivo L1 (conductor, `Test_Perf66_L1_A`, XAUUSD, 28 estrategias; `/dev/shm/tmp66/live-session-L1.md`).** 🔬 Ruta viva: `liverun.export` 4,7 s, **0 llamadas a `orderstocsv`**, carpeta del `.abk` borrada al acabar. Ruta parada sobre los mismos bancos: 18 s, 1 llamada. **Los 24 ficheros iguales**: 6 parquets exactos (`check_exact=True`), 18 byte a byte. La parada (13,2 s, con guardado previo) no reexportó nada. `live.start` 23,7 s hasta APP LOADED y el Build paró solo. El instalador quitó sólo `AlgoTrades.java` (833 → 832 ficheros). Arrancar la tarea de `Trade_AlgoTools` no movió los bancos del proyecto (28 en memoria y en disco antes y después). **Sin probar:** banco con otros mercados en modo «all» y estrategia sin operaciones (no salieron en este proyecto). Fixture dorada con `.abk` real: no se hace — no hay cortador de `.abk` y el test sintético más esta igualdad medida cubren lo mismo.
  - **Sesión en vivo L2 (conductor, `Test_Perf66_L2_A`; `/dev/shm/tmp66/live-session-L2.md`).** 🔬 Banco con otros mercados en modo «all» (29 estrategias × 4 mercados, 144.380 operaciones): el `.abk` se acepta y se ata, `liverun.export` 7,5 s con 0 `orderstocsv`; ruta parada 37 s con 2 llamadas; **31 ficheros iguales** (6 parquets exactos, 25 byte a byte). Estrategia sin operaciones (8 de 29 en un banco hecho a propósito, una la primera por nombre): `load`, `trades`, `pack` y `unbound` no fallan y el resultado es igual al de `orderstocsv`. Sin probar: una estrategia sin operaciones dentro de un banco «all».
  - **AlgoBank en el custodio (Q15 = B).** Instalado con el custodio parado e instantánea previa (`AlgoData/snapshots/custodio-2026-10-13-algobank`): 26.176 `.sqx` antes y después, `user/extend` 836 → 836 (sale `AlgoTrades.java`, entra `AlgoBank.java`), `--check` limpio.
  - **7.3, decidido (V1 = A, V2 = B).** El «sin sync» completo no compensa (~95 s más por madre, 1,9 % de una corrida, a cambio de reescribir 5 piezas, perder 36 columnas de `results.parquet` y una igualdad de equidad sin probar). Se hace sólo que las operaciones del 16.5 salgan de memoria (`membank.run` en modo «all» antes de `export_retest`, `pipeline/autopilot/variants.py`): estimado 141 → ~35 s por madre, a medir en la corrida completa. El `.abk` «all» se ata mercado a mercado, no sólo en el principal.
  - **Sesión en vivo L3 y revisión 9.** 🔬 El atado mercado a mercado sobre un banco real (30 estrategias × 4 mercados): etiquetas iguales en `.abk` y `.sqx`, 0,078 s, diferencia máxima 0,015, un P/L alterado en XAGUSD rechazado por nombre. Revisión independiente (sólo el diff, `CODESTYLE.md` y el objetivo): ningún fallo cierto; añadida la comprobación de «sin resultado Main».
  - **Falsos positivos, código viejo (`f55ad52^`) contra nuevo (6b).** 🔬 Sobre `Test_NIKKEI225_M30_simpleL_ref` (sólo 10 estrategias reales, las 10 suspenden): embudo, reglas y columnas no aleatorias iguales; `z_mono` se mueve ≤ 0,0069 (N12 = B); 0 veredictos cambian en las reales; en los monos cambian tantos como al cambiar sólo la semilla. **Prueba floja**: falta sobre una población de 10.000, tras la corrida de cierre.
  - **Catálogo de `perf/` (frente 10).** Parado: `sample.trades_databank` es `null` y no hay en `AlgoData/raw` ninguna exportación con `trades/` y `strategies/` juntos. Dueño: A1 (exportar con SQX un banco de XAUUSD de hasta 10.000) y B2 (una sola pasada completa cuando exista). Sale de la corrida de cierre.
  - **Corrida de cierre lanzada** (dueño: «dale todo»): `bin/workflow.sh simple Test_XAUUSD_H1_ruptura_perf66 XAUUSD H1 long breakout ruptura_base_v3 … 10000 30 --until wfm --smoke`, los mismos argumentos que la de referencia del §0 (`Test_XAUUSD_H1_ruptura_wf4s`, 2026-10-11). Las dos medidas de escala del guardado previo y del export salen de ella.
  - **Cartera.** `source.py` y `universe._commission` leen reloj y comisión del manifiesto del miembro, sin recurso al valor vivo. Relleno de los archivados: `python3 -m portfolio.common.construct.inputs.backfill --yes` → 68 rellenados, 5 sin rellenar (ficha anterior al 2026-09-29, sin tramos). **Q18 = A:** los 30 miembros USDJPY del feed antiguo llevan `Asia/Jerusalem` (medido: 0,3-3 $ de hueco contra 430-2.000 $ con EETUS); copia de los manifiestos de antes en `/dev/shm/tmp66/manifests-before/`.
  - **Decisiones del dueño de esta tanda.** Q1-Q3 A (encargo 53 §5c, en la sesión L1) · Q5 A · Q6 B · Q7 A · Q8 A (un limbo que no es medoide se descarta) · Q9 A · Q11 C · Q14 A · Q15 B (AlgoBank al custodio sólo si L1 sale bien) · **Q16 A: 8.2 (`prange`) y 8.3 (motor por corrida) medidos y descartados** (empate 16,06 / 16,16 s; 1,3 %) · Q17 A (se comitea sin preguntar, sólo en este encargo, con pathspec y push).
  - **Queda.**
    - Sesión L1 del conductor: Build + OOS y export por `.abk` con cero `orderstocsv`; igualdad fichero a fichero con la ruta parada; frescura; banco con otros mercados; segundos por fase; fixture dorada; estrategia sin operaciones; `booted` y el recorte de `Results` en vivo; corpus del encargo 53 §5c.
    - Después: AlgoBank en el custodio (aviso previo), 7.3 «16.5 sin sync», 8.1 con su consumidor, D27 (diseño al dueño antes de construir), y el cierre (dos medidas de escala, catálogo `perf/`, manual, corrida completa contra §0).
    - Tarjeta ajena caducada: `knowhow/sqx-drive/unselected-build-population.md` dice «nunca dejarlo llenar», y D24 lo contradice. Es de otra sesión: se corrige cuando esa sesión cierre.

## Tu oficio

Eres un programador de Python de rendimiento: numba, paralelismo por procesos con `fork`, formatos
binarios y `numpy` sin copias. Sabes que un cambio de velocidad que mueve un resultado en el último
bit es un cambio de resultado, y lo dices. Modelo por frente en la tabla (regla 17).

## Tu encargo

Construir, frente a frente, lo que la auditoría encontró, y devolver al dueño **una corrida del
workflow más corta con los mismos números**: cada cambio lleva su prueba de igualdad contra el
código de hoy (bit a bit donde la sección lo dice, con tolerancia declarada donde no) y su tiempo
medido antes y después. Lo que cambie un resultado no se construye sin su decisión (§«Decisiones»).

## §0 De dónde sale

**El dueño, 2026-10-12:** «revisar todo el código buscando posibles errores y mejoras en la
optimización, aplicar paralelismo si no lo hay». «La performance es fundamental. Tenemos 48 cores
físicos, o 96 hilos, los usamos. Si quiero poner 1 millón de runs por mono, las pongo, porque la
performance ha de ser cojonuda». «Todo lo que no sea corrida de SQX, a la velocidad de la luz». Y
del binario del databank: «me parece una idea fantástica… soluciones drásticas como esa quiero».

**El presupuesto real** (MEDIDO: media de las 5 corridas completas más recientes, cada una un build
de 10.000 que el paso 8 corta a 3; `AlgoData/autopilot/<P>/<sello>/fases.csv` plegado con
`pipeline/autopilot/timing.py`; detalle en `findings-BUDGET.md`):

| de una corrida de ~9.000 s | segundos | % |
|---|---|---|
| SQX calculando | 2.477 | 27,5 |
| Python | 4.118 | 46 |
| cruce SQX ↔ Python (exportar, sincronizar) | 1.234 | 14 |
| esperas (arranque, reaperturas, parada) | 1.176 | 13 |

**El 72,5 % de una corrida no es SQX calculando** — y con el log del propio SQX delante es más:
en la corrida unida línea a línea (§7) SQX calcula 2.360 de 10.034 s, el **23,5 %**, porque la fase
`execute` del 16.5 cuenta como cálculo lo que es sync. Lo que más pesa, en orden:

| # | qué | s | dónde | frente |
|---|---|---|---|---|
| 1 | control de falsos positivos del paso 8 | 3.337 | `studies/screening/falsePositives/report.py:48` | 2 |
| 2 | reaperturas de SQX (pasos 15 y 19) | 586 | `ui/daemon/launch/liverun.py:102` | 7 |
| 3 | exportar operaciones | 504 | `ui/daemon/loader/afterrun.py:133` | 5, 6 |
| 4 | parada final | 500 | `pipeline/autopilot/run.py:217` | 7 |
| 5 | cosecha | 210 | `studies/screening/gate/collect.py:113` | 5, 6 |
| 6 | gate del paso 8 | 207 | `studies/screening/gate/report.py:19` | 2, 3 |
| 7 | `export_retest` del 16.5 | 197 | `pipeline/autopilot/variants.py:94` | 6 |
| 8 | sync tras el build | 111 | `ui/daemon/launch/liverun.py:139` | 6 |
| 9 | crossTF (11.5 y 12) | 106 | `studies/transfer/crossTF/report.py:48` | 4 |
| 10 | lectura ciega 18.5 | 97 | `pipeline/autopilot/tail.py:10` | 4 |

Con miles de supervivientes en vez de 3 el reparto cambia: manda el mono tras el corte (§4.1), que
`ui/daemon/jobs.py:26` anota en 6 h 30 para 1.352.

**La máquina** (MEDIDO): AMD EPYC 7413, 2 zócalos × 24 núcleos, 96 hilos; 125 GB, de ellos 20 para
Python (regla 3); `/tmp` tiene 3,9 GB. numba 0.67. Escalado del núcleo del mono, procesos fijados a
una CPU: 8 núcleos ×8,07 · 24 ×24,10 · **48 ×47,96**; dos hilos del mismo núcleo +20 %.

## Cómo leer cada hallazgo

- **MEDIDO** = cronometrado o reproducido en esta máquina; **ESTIMADO** = escalado o razonado. Casi
  todo lo medido es con ≤ 4 núcleos (regla 19: había que no estorbar); a 48 es estimación salvo el
  escalado de arriba.
- **Verificado** = un segundo agente intentó refutarlo y no pudo. **Sin verificar** se dice.
- **Cambia resultados: no** = bit a bit igual, comprobado. **Últimos bits** = igual hasta ~1e-12
  por el orden de una suma. **Sí** = decisión del dueño, está en §«Decisiones».
- Una cifra de ahorro es siempre «por corrida de 10.000 estrategias» salvo que diga otra cosa.

---

## 1 · Errores

Fichero de evidencia por hallazgo entre paréntesis. Ninguno necesita SQX.

### 1.1 `draws.merge` pierde distribuciones y cuesta cuadrático — ALTA, verificado

`core/study/draws.py:83-100`. `merge` lee el `distribuciones.parquet` de la carpeta, sustituye las
filas de su estrategia y reescribe el fichero entero. Lo llaman a la vez los subprocesos
`--strategy` de `studies/readings/monkey/report.py:105`, `entryQuality/report.py:33`,
`spp/report.py:53`, `wfm/report.py:34` y `mcRetest/report.py:65` (8 de mono y 16 de entryQuality
desde `ui/daemon/launch/chain.py:174`, hasta 44 desde `ui/daemon/runner/batchrun.py`).

- **Se pierden filas** (MEDIDO, `clr3.py` y `bench_draws.py`): 8 procesos fusionando 16 estrategias
  dejaron 2 de 16; 8 × 6 dejaron 6 de 48. `os.replace` hace atómica la escritura, así que el fichero
  nunca queda roto: gana el último que escribe y los demás desaparecen en silencio. El veredicto no
  se rompe (los p salen de `estrategias/<nombre>.json`); lo que queda incompleto es el registro.
- **Coste cuadrático** (MEDIDO): cada fusión recomprime todo con zstd nivel 19 (`draws.py:77`).
  0,04 s con 1 estrategia dentro, 1,07 s con 50, 3,16 s con 150; con filas crudas, 5,9 s con 40.
  A 1.352 supervivientes son ~5 h acumuladas (EXTRAPOLADO). Es plausible que sea parte de las
  «6 h 30»: `merge` entró el 2026-10-09 (commit 2ec6c57), el día de esa corrida. No demostrado.
- **Arreglo:** en modo `--strategy` escribir `distribuciones/<estrategia>.parquet` y consolidar una
  vez al final de la fase (un `flock` arreglaría la pérdida, no el coste). Y bajar el nivel de zstd:
  23,8 s / 66,0 MB a nivel 19 contra 1,6 s / 70,0 MB a nivel 9 y 0,9 s / 71,6 MB a nivel 3 (MEDIDO,
  6.000 filas reales). Datos idénticos, fichero +6 %.
- Evidencia: `findings-VERIF-A.md` (CLR-1), `findings-ENG.md` (ENG-1), `findings-VERIF-B-DMN.md`.

### 1.2 El control de falsos positivos no puede terminar a 100.000 sorteos — ALTA, verificado

`studies/screening/falsePositives/chain.py:114` abre un `TemporaryDirectory` y
`gate/level3c.py:45,86` guarda en él los sorteos crudos de cada mono (`draws.record` con `raw=True`
por defecto): 20.000 filas × 400 KB = **8 GB por pasada**, cinco pasadas, en un `/tmp` de 3,9 GB.
Nadie los lee; la carpeta se borra al salir. Desde que `gate/config.yaml` pasó de 5.000 a 100.000
sorteos (commit ccaf226, 2026-10-12) el control no cabe salvo con `TMPDIR` apuntando a AlgoData,
que es como se relanzó la corrida nula del encargo 65 (fila 5.4, «~10 h»). El arreglo es el punto A
de §2. Evidencia: `findings-VERIF-A.md` (SCR-1), `findings-FP.md`.

### 1.3 El Drawdown de las uniones del 16.5 sale bajo — MEDIA, verificado, **cambia resultados**

`sqx/variants/united.py:130`: `(cum.cummax() - cum).max()` arranca el máximo en el primer valor de
la curva y no en 0. Una estrategia que empieza perdiendo no cuenta ese tramo: `[-100, -200, -200,
+50]` da 400 y son 500. El resto del repo recorta el pico a 0 (`wfm/measure/equity.py:61`,
`analysis/resample.py:126`, `ui/daemon/databank/segments.py:32`, `mt5/verify/judge.py:57`). Arreglo:
`cum.cummax().clip(lower=0)`. Sube el Drawdown de build+oos1, oos1+oos2 y ALL de las variantes que
empiezan en pérdida; la magnitud sobre datos reales no está medida → **D1**.

### 1.4 Reanudar una corrida: cinco agujeros — verificado por lectura de código, no reproducido

- **`pipeline/autopilot/plan.py:33-45`** — `reopen` sólo reabre si la carpeta más reciente acaba en
  «FALLO en el paso N». No cubre (a) la carpeta vacía que deja un intento rechazado por
  `advance.busy`, que pasa a ser la más reciente, ni (b) un proceso muerto sin `except` (OOM,
  SIGKILL), cuya última línea es «[k/n] paso N». Es la trampa de `OPEN.md` #111: un estudio a medias
  contado como hecho. Arreglo: la carpeta más reciente **con** `estado.txt`, y reabrir si su última
  línea no empieza por FIN.
- **`pipeline/autopilot/judge.py:237-239`** — reanudar con el 8 hecho y el 9 sin hacer repite el
  juicio del 8 sobre el databank ya cortado; `ledger/cells.py:78-80` es un upsert y sustituye
  `screened` (10.000) por el tamaño del databank cortado. **El contador de pruebas múltiples queda
  subestimado.** Arreglo: `note(project, max(len(pop), previo))` y no firmar otra fila si ya existe.
- **`pipeline/autopilot/variants.py:85-99`** — un fallo a mitad del 16.5 lo rehace entero: ~290 s
  por madre (MEDIDO en `fases.csv`). Arreglo: marcador por madre con el hash de su brief.
- **`pipeline/campaign/run.py:96`** — si `keep.keep` lanza, el bucle muere con la celda en
  `running`; `following()` la vuelve a coger y vuelve a fallar: cola atascada. `shelf.py:38` hace
  `mkdir(parents=True)` sin `exist_ok`. Arreglo: `try/except` que marque `kept_failed`.
- **`sqx/variants/varianttrades.py:41`** — `date.today()` frente a la fecha de
  `sqx/export/export_retest.py:56`: un 16.5 que cruza la medianoche da `FileNotFoundError`.

Evidencia: `findings-PIPE.md`, `findings-VERIF-C.md`.

### 1.5 El mono por estrategia no es reproducible — MEDIA, por lectura de código

`engines/nulls/inputs.py:33-34` convierte `seed: null` en entropía fresca **por proceso** y los
lanzadores no pasan `--seed` (`ui/daemon/runner/readings.py:30-33`, `ui/daemon/runs.py:89`). Con un
subproceso por superviviente son N raíces distintas, distintas en cada corrida; la ruta de población
usa una y la escribe en `nulls.csv` (`monkey/report.py:131`). Además `runs.py:89` no pasa
`--timeframe` y cae en M30 por defecto (`report.py:67`). Arreglo: una raíz por corrida, guardada y
pasada a todos. Se arregla sola con §4.1. → **D2** (qué raíz). Evidencia: `findings-BUDGET.md` §3.

### 1.6 Fallos que se callan

| dónde | qué pasa | arreglo |
|---|---|---|
| `core/fanout.py:36-40` | una tarea que lanza (o un OOM) no cancela la cola: el `with` espera a todas las demás (reproducido: la excepción sale a los 6,02 s en vez de a los 0,3) | `try/except BaseException: pool.shutdown(wait=False, cancel_futures=True); raise` |
| `ui/daemon/runner/batchrun.py:88` | sale 0 si fallan **algunas** estrategias; el paso siguiente sigue con menos, en silencio | salir ≠ 0 y nombrar las que faltan |
| `studies/readings/monkey/many.py:47,51` | descarta sin avisar las de < 30 operaciones; si quedan todas fuera, `IndexError` en `keys[0]` | contar y decir cuántas; salida limpia |
| `sqx/variants/spp.py:76` | `TESTED.search(status).group(1)` → `AttributeError` si el estado no trae «Total tested» | lo que ya hace `banks.tested` |
| `ui/daemon/launch/chain.py:121` | mide la RAM libre antes de que el hijo la consuma: 16 hebras pasan a la vez | reservar por peso (`jobs.weight`) |
| `ledger/record.py:20-37` | `sharpe_std` NaN con un candidato → `json.dumps` escribe `NaN`, JSON inválido | `None` |
| `ledger/cells.py:79-90`, `ledger/tried.py:96-119` | leer-modificar-reescribir sin bloqueo; `write_text` trunca y un lector ve el fichero vacío. Sólo con dos workflows a la vez | `.tmp` + `os.replace`, `flock` |
| `core/barstore.py:99-104` | caché por marco escrita directa al nombre final: con caché fría y fanout, un parquet truncado lanza `ArrowInvalid` hasta borrarlo a mano | `.tmp` + `os.replace`, como `core/store/write.py:40` |
| `portfolio/common/construct/equity/excursions.py:30-40` | operación abierta antes de la primera barra M1 → `ValueError` que tira el panel entero (reproducido) | acotar y contar |
| `core/surface/plateau.py` (`above_half_max`) | `values > values.max()/2` falla con máximo ≤ 0; `plateau_fraction` ya usa `abs()`. **Cambia resultados** sólo en ese caso | `abs()` |
| `studies/research/feedQuality/touch.py` | operación en la primera barra → índice −1 = última barra | `np.maximum(k, 1)` |
| `portfolio/common/monteCarlo/simulate/stitch.py` (`worst_path`) | `np.random.default_rng()` sin semilla: no reproducible | semilla de la configuración |
| `studies/research/memory/attempts.py:14,48` | la regex no acepta `Research_` (regla 6); sólo es respaldo | añadirlo |

### 1.6 bis · Pasada 6: bugs en lo que nadie había abierto

- **La celda del almacén sale mal nombrada en los proyectos simples** —
  `core/store/save.py:71-75` (`cell_of`). El registro guarda `simple:long` / `simple:short`, y
  `Path("simple:long").parent.name == ""`: la celda sale `DAX40_H1_` en vez de `…_simple`, y
  largos y cortos comparten celda y `runs.json`. Verificado: 24 filas `simple:` en `registry.csv`
  y carpetas `DAX40_H1_`, `DAX40_M30_`, `DJ30_H1_`, `EURUSD_H1_`, `GBPUSD_H1_` en el almacén.
  Arreglar el nombre es una línea; **mover lo ya guardado es decisión del dueño → D21.**
- **`draws.save` sin candado** (`core/study/draws.py:62-82`; `merge` sí lo tiene desde esta noche):
  dos procesos que guardan tests distintos en la misma carpeta pierden uno. Latente — hoy no hay
  dos escritores a la misma carpeta. Si le pones candado, que `merge` no lo tome dos veces.
- `portfolio/common/construct/equity/stopexit.py:62`: `searchsorted(...) - 1` vale −1 si el cierre
  es anterior a la primera barra y `Open[-1]` coge la última barra sin avisar.

### 1.7 Lo escrito que no dice la verdad

- `engines/nulls/simulate.py:145-148` — el docstring promete que subir `nulls.draws` sólo añade
  bloques. Falso en el último bloque parcial de `timing_holds` y `free` (MEDIDO: 1.000 frente a
  1.500). **Corrige el docstring, no el código:** arreglarlo cambiaría el último bloque de toda
  corrida con semilla fija. Y `:90` dice «identidad» donde la clave es el nombre.
- `studies/screening/gate/cascade.py:74-80` — dice que sin cascada los hechos son los mismos; no lo
  son en R5/R5d (`level1b_centred.py:33-53` centra en quien pasó el nivel 0). `falsePositives/chain.py`
  ya lo declara decidido (dueño, 2026-10-07): es el docstring el que falta.
- `knowhow/perf/falsepositives-cost-scales-with-monkey-trades.md` atribuye el coste al 3c «por
  lectura»; lo medido a 5.000 sorteos dice 3ab en serie + `draws.save` (§2). Reescríbela.
- `core/store/README.md:52-56` y la skill `store-open` describen sorteos crudos que §3.1 deja de
  guardar.

---

## 2 · El control de falsos positivos

Evidencia: `findings-FP.md` (prototipos `fp/s1.py`…`s4.py`). Es el **37 % de la corrida**.

**Qué hace.** De la cosecha real elige 100 donantes y sortea 50 monos por donante: 5.000 listas de
operaciones con entrada al azar. Las pasa por el gate entero con la cascada apagada
(`chain.facts8`) cuatro veces — población nula y ventajas plantadas 0,05, 0,10 y 0,15 — y una
quinta con la población real (10.000). Mismos monos y misma semilla en todas las pasadas.

**Dónde se iba el tiempo.** Los 3.330 s se midieron con **5.000 sorteos**, no con 100.000. Medido
por unidad en la cosecha real de NIKKEI y escalado a la corrida:

| pieza | corre en | en la corrida |
|---|---|---|
| nivel 3ab (`q_null` 18,6 ms + `drawdowns` 26 ms por estrategia) | serie, en el padre | ~1.475 s (44 %) |
| `draws.save` de 3ab y 3c (zstd 19; el de 3c relee y recomprime lo de 3ab) | serie, en el padre | ~900 s (27 %) |
| nivel 3c, el Monte Carlo del mono | 48 procesos | ~290 s (9 %) |
| niveles 0, 1a, 1b, 2 y medidas | serie, pandas | ~286 s (9 %) |
| carga, sorteo de monos, salidas | serie | ~40 s |

A 5.000 sorteos el Monte Carlo era el 9 %. **A 100.000 se invierte:** el 3c pasa a ~5.740 s las
cinco pasadas (ESTIMADO) y los sorteos crudos no caben (§1.2).

**Qué construir**, en este orden. A-D no cambian ningún número:

- **A. No registrar ni guardar sorteos en el control.** `chain.facts8` pone
  `data["keep_draws"] = False`; `gate/level3c.py:45,86` y `gate/level3ab.py:49,57,61` hacen
  `if keep: kept.append(draws.record(...))`. −900 s, y es lo que permite terminar a 100.000.
- **B. Paralelizar el nivel 3ab.** `gate/level3ab.py:40-60`: el cuerpo del bucle pasa a
  `_one(identity)` con `_SHARED` y `fanout.run`, igual que el 3c. Los flujos ya son
  `resample.stream(seed, str(identity))`, independientes del orden. MEDIDO con 4 procesos: 11,1 ms
  por estrategia contra 50,7; `q_p`, `dd_p` y `dd_esperado_r` **bit a bit**. ~1.475 → 30-40 s.
  También acelera el gate real (20.000 vivas ≈ 18 min hoy). Ordena `kept` por identidad para que el
  parquet salga determinista.
- **C. Calcular el 3c una vez para las cuatro pasadas de monos.** La ventaja plantada sólo suma una
  constante a lo observado; los sorteos son idénticos (MEDIDO: 36 vectores iguales, z y p bit a
  bit). No hace falta guardar sorteos: en la pasada nula se evalúa cada peldaño en
  `mean(pnl + add)` para las tres ventajas y se guardan 15 números por mono. **Ojo:** tiene que ser
  la media de `pnl + add`; con `mean(pnl) + add` la z se va 9e-16. Esbozo en `findings-FP.md`.
- **D. Lo invariante a la ventaja no se recalcula:** `q_p` (MEDIDO idéntico; 41 % del 3ab
  plantado); el nivel 2, que corre dos veces por pasada plantada (`chain.py:85`) — pasarle el exceso
  movido de la nula con `delay.measure(..., moved=cache)` en `analysis/delay.py:74` (por lectura,
  sin prototipo: pruébalo); y los niveles 0 y 1a, iguales en las cuatro.
- **E. Calcular en el control sólo el peldaño juzgado** → **D3**. `criteria.yaml:109` juzga sólo
  `z_mono`; las otras tres z no las lee ningún código. Divide el 3c por 4.
- **F. El núcleo nuevo del 3c** es §3.2.

**Prueba de igualdad (A-D):** con la cosecha sintética de `tests/test_false_positives.py` y semilla
fija, guarda `facts`, `funnel` y `rules` de `many.run` antes; después
`pd.testing.assert_frame_equal(check_exact=True)` sobre los tres. Repítelo en una cosecha real con
`--seed 233239783 --set population.per_level=200`.

**Proyección** (ESTIMADO, 48 núcleos, 5.000 monos + 10.000 reales; ~245 s son fijos):

| estado | 5.000 sorteos | 100.000 | 1.000.000 |
|---|---|---|---|
| hoy | 3.330 s (MEDIDO) | no termina en `/tmp` | no cabe |
| A + B + C + D | ~390 s | ~52 min | ~8 h |
| + núcleo de tabla (§3.2) | — | ~10 min | ~1 h |
| + sólo el peldaño juzgado (D3) | — | ~5 min | ~15 min |

Las dos últimas filas son ESTIMADAS a partir del ×14 (`timing`) y ×6 (con hold) medidos con
operaciones reales. Dos tercios de lo que queda son la pasada de la población real, que no tiene
nada que reutilizar.

---

## 3 · Los sorteos: que un millón sea asequible

Evidencia: `findings-MONO.md`, `findings-VERIF-MONO.md`, `findings-MCBARATO.md` (prototipos `mono/`,
`verify/`, `ex/`). **El Monte Carlo se queda** (dueño): aquí sólo se abarata cada sorteo.

Hay **dos monos distintos**, con el mismo modelo de coste — tiempo = sorteos × operaciones × c:

| | escalera | ventanas |
|---|---|---|
| código | `engines/nulls/simulate.py` → `kernel.runs` | `engines/nulls/windowed.py` → `reprice.pnl` |
| quién lo usa | `readings/monkey`, `crossTF/cells.py` | gate 3c, el de miles de estrategias |
| qué calcula | 5 estadísticos por sorteo | la media por operación |
| hoy | numba, serie; c = 48-73 ns | **numpy puro, sin compilar**; c = 62-168 ns |

### 3.1 No guardar ni acarrear sorteos crudos — OBLIGATORIO, verificado, no cambia resultados

`gate/level3c.py:45` y `studies/transfer/crossTF/cells.py:85` llaman a `draws.record` con `raw=True`
por defecto, y `level3c.py:85-86` lo junta todo en el padre. Hoy, a 100.000 sorteos, son **32 GB con
20.000 estrategias**; a un millón, 320 GB en una máquina de 125. Con `raw=False` (como ya hace
`monkey/one.py:109`) cada fila conserva histograma de 200 cajas, 100 extremos por lado, `n_ge`,
`n_le`, media y desviación: z y p siguen reproducibles desde la fila, en ~3 KB.

Verificado que **nadie lee los crudos**: ni `ui/` (`gateview.py:79-103` lee scorecard, métricas y
equity), ni `core/store`, ni ningún test de `gate.3c` o `crossTF.cell`. **No toques** el `raw=True`
de otros registros: `test_draws.py`, `test_draws_late.py:35` (wfc) y `test_draws_transfer.py:24`
(crossmarket) sí exigen la columna. El dueño (2026-10-12): no hace falta «exactamente las métricas
de todos los runs full, sino al menos los histogramas y demás para luego poder verlos en la UI» —
que es justo lo que `raw=False` conserva. Comprueba en la ventana que el histograma del 3c se sigue
pintando igual antes de darlo por hecho (**D4**).

### 3.2 Núcleo del gate 3c: precio una vez, sorteo = índice a una tabla — verificado con datos reales

Evidencia: `findings-VERIF-TABLA.md` (prototipo `v4a/common.py`), `findings-MCBARATO.md` §2.1.

Cada operación sólo puede caer en las barras de su hora dentro de su ventana (`year`,
`gate/config.yaml:58`: 175-259 barras en H1). Se precia **una vez**, con `reprice.pnl` tal cual,
cada terna (operación, hold recortado, barra elegible); un sorteo es entonces un índice a esa tabla
(núcleo `gather`, 12 líneas). Como la tabla la hace `reprice.pnl`, cortos, comisión porcentual y
swap en puntos salen bien por construcción.

- **Bit a bit** si el núcleo rellena la matriz (sorteos, n) y la media la hace `mean(axis=1)` como
  `windowed.py:176`: `array_equal` en 120 de 120 (30 estrategias reales de NIKKEI M30, USATEC H1 y
  DAX40 H1 × 4 peldaños × 100.000 sorteos), y `z_mono` y `mono_p` idénticos. Cuesta +0,4-0,5 ns.
  **Construye esta variante:** el test es `array_equal` y D5 deja de hacer falta.
- **16 casos adversarios** × 4 peldaños, 60 de 60 iguales: cortos, lados mezclados, PercentageBased,
  swap en puntos, operaciones en la primera y la última barra, hold 0, hold mayor que el hueco, una
  hora con una sola barra elegible, máscara de sesión, ventanas trimestrales, n = 2.896.
- **Velocidad con operaciones reales** (MEDIDO, ns por valoración, tabla incluida):

  | peldaño | hoy | tabla | factor |
  |---|---|---|---|
  | `timing` | 63,6 | 4,45 | ×14,3 |
  | `timing_sizing` | 61,3 | 4,42 | ×13,9 |
  | `timing_holds` | 71,7 | 12,3 | ×5,9 |
  | `free` | 67,6 | 12,4 | ×5,5 |

  (El ×27-39 de la primera medición era con operaciones sintéticas, donde el camino de hoy cuesta
  el doble.) **El suelo ya es el generador:** 3,15 ns por uniforme, el 75 % de `timing`. Bajar de
  ahí exige cambiar el flujo de aleatorios (float32, o compartir uniformes entre peldaños) → D9.
- **Memoria: comparte la tabla por (hora, ventana, lado), no por operación.** Por operación llega a
  107 MB (NIKKEI M30, n = 1.006); compartida, 17 MB como máximo, mismos valores bit a bit y se
  construye 2,4× más rápido. Y **precia por trozos** (2 M de valores): `reprice.pnl` sobre la tabla
  entera crea temporales de ~10× su tamaño, y `level3c.py:85` lanza `os.cpu_count()` = 96 procesos.
- **Fallo latente del repo, de paso:** una hora sin ninguna barra elegible da `IndexError` en
  `engines/nulls/windowed.py:131`; el respaldo `.get(int(hour), ok)` de `:126` nunca actúa porque
  `grid` crea las 24 claves (`:72`). No se alcanza con datos reales hoy.
- Sin verificar: cortos reales (sólo largos volteados), una ficha con comisión porcentual ≠ 0,
  estrategias con muchos holds distintos (SL/PT), M15 y H4, y el pico de memoria con 96 procesos.

El núcleo compilado que precia en el bucle (MONO-4, `findings-MONO.md`; 16,9-20,5 ns, diferencia
≤ 6,3e-13) queda como alternativa descartada: es 4× más lento que la tabla y no es bit a bit.

### 3.3 Núcleo fundido de la escalera, sin `argsort` — verificado, **bit a bit**

`engines/nulls/kernel.py:33-46`, `model.py:17-31`, `simulate.py:144-148`. El `argsort` por sorteo es
el 68-78 % del núcleo. Las salidas son enteros casi uniformes en la ventana: un conteo por cubetas
estable más una inserción los ordena en O(n), y recibiendo los uniformes del mismo `default_rng`
sobran las matrices `int64` de entradas. MEDIDO: 14,6-18,7 ns contra 48-73 (**×3,0-4,5**; ×4,9-5,4
con empates masivos). `array_equal` en los 5 estadísticos, 4 peldaños, y en **11 casos adversarios**
(empates masivos, holds a 0, una sola barra de salida, cortos, n = 1, 2, 3, un hold de 55.000
barras, bloques parciales): 0 discrepancias.

**Límite:** sólo sustituye la rama `not kept["levels"]` de `simulate._priced` (`simulate.py:65`); con
stop o target sigue la ruta numpy (`barrier.exits`). Esbozo en `findings-MONO.md` (MONO-3).

### 3.4 El resto del gate 3

Evidencia: `findings-VERIF-3AB.md` (prototipos `v4b/kern.py`, `j2a.py`, `j2b.py`, `fixguard.py`).

- **3a, drawdown en flujo — bit a bit, verificado.** `analysis/resample.py:129` construye la matriz
  de índices, la copia, el `cumsum` y el `maximum.accumulate`. Un núcleo que recorre los bloques con
  tres escalares (`dd_stream`) da lo mismo en 332 de 335 casos (vector, `dd_p`, `dd_esperado_r` y
  estado del generador): rejilla de 320 tamaños, bloque mayor que la serie, un solo elemento, todo
  positivo, todo negativo, magnitudes de 1e15. **Los 3 que difieren son NaN e inf:** el `max()` de
  numba no propaga NaN y `np.maximum` sí, así que el núcleo daría un drawdown esperado 0,0 con
  apariencia de dato válido. **Usa la versión con guarda** (`bad |= d != d`, devolver NaN), medida
  idéntica también en esos casos. Velocidad: ×7,1 (build 1.500 / oos 300) a ×13,2 (5.000 / 1.000);
  en el caso grande 1,22 de los 1,72 µs son ya `rng.integers`.
- **3b, `q_null` por tandas — bit a bit, verificado.** `rng.permuted` consume el flujo fila a fila,
  así que barajar en un búfer de 4.096 filas da exactamente las mismas permutaciones (525
  combinaciones, 0 diferencias). **La ganancia es de memoria, no de tiempo:** a un millón de
  permutaciones, 4,78 GB → 0,32 GB (n = 300) y **15,72 GB → 0,32 GB** (n = 1.000); en tiempo, ×1,1-1,4.
  Con la forma de hoy, a un millón no caben dos procesos en los 20 GB.
- **`q_null` es correcto.** La discrepancia de 6,9 errores estándar que vio la pasada 3 era del
  oráculo (pasaba 12 × 83 = 996 operaciones como tamaños para 1.000). Enumerando todas las
  permutaciones (n ≤ 9) y con 2 M a n = 1.000 la media coincide; `rng.permuted` es uniforme (chi²,
  p = 0,42). Endurecimiento barato: `assert sizes.sum() == len(values)` al entrar — hoy unos tamaños
  cortos se tragan en silencio.
- **Reparto del 3ab por identidad: idéntico** con 1, 2 y 4 procesos, `fork` y `spawn`, orden
  barajado. **Condición:** `resample.root(None)` (`level3ab.py:35`) sortea una raíz nueva — sortéala
  una vez en el padre y pásala; si cada trabajador la llama, cada uno tendrá la suya.
- **`analysis/improvement.py:104-108`** — matriz 2.000 × k entera: 660 MB por proceso con k = 10.000
  (MEDIDO), ~31 GB con 48 procesos. Trozos de 250 filas; el `rng` da los mismos índices (MEDIDO).
  Sólo importa con poblaciones de 20.000.
- **`engines/nulls/footprint.py:50-56`** (paso 20) no está troceado: a un millón, matrices
  sorteos × operaciones de 6,4 GB. Trocear.

### 3.5 Una sola estrategia: hilos sobre los bloques

Para `--strategy` y las celdas de crossTF. numpy suelta el GIL al generar y el núcleo es `nogil`:
4 hilos sobre los bloques ya sembrados dan ×3,84 e **idéntico** con 1 o 4 hilos (MEDIDO, `b6.py`).
**Nunca `parallel=True` dentro de un `fanout`:** serían 96 hilos × 48 procesos, `threadpool_limits`
no cubre numba y hacer `fork` con la capa de hilos de numba arrancada no es seguro. Añade a
`core/fanout.py` un `initializer` que haga `numba.set_num_threads(1)` si numba está cargado: hoy
los `prange` de `portfolio/` los llama el proceso principal, pero nada lo impide — y reproducido en
la pasada 4: si el padre ya ejecutó un `prange`, un trabajador del `fanout` que ejecute otro **muere
con `BrokenProcessPool`**.

### 3.6 Oráculos exactos — sólo como test

La media y la varianza del mono de ventanas se pueden enumerar (cada operación se sortea
independiente). **No sustituyen al Monte Carlo** (dueño); sirven para un test que afirme que el
núcleo converge: `abs(got.mean() - mu) < 5 * sd / sqrt(N)`. Verificado válido en los 4 peldaños,
también en cortos, PercentageBased y swap en puntos; **no vale para la escalera** (sus estadísticos
no son medias). Esbozo en `findings-MCBARATO.md` §2.5; coste 0,02-2,3 s.

### 3.7 Lo que cambia el flujo de sorteos — decisiones del dueño, no se construye sin su sí

- **Variable de control en la escalera** (D9). `verdict.attribute` informa medias del nulo por
  peldaño; con `net` como control (su media exacta se enumera) la varianza de la media baja ×18
  (sharpe), ×18-52 (pf), ×3,4-6 (retdd), ×2,4-3 (dd) — MEDIDO. Sigue siendo Monte Carlo sobre los
  mismos sorteos, pero la media informada pasa a ser la corregida. Para los p apenas ayuda.
- **Parada secuencial de los p** (D10, Besag-Clifford): sortear hasta `h` excedencias o N máximo;
  el p sigue siendo válido. Con h = 1.000 y N = 1 M, ~7.900 sorteos de media bajo la nula. No sirve
  para la z del gate, y las de p pequeño pagan el millón entero.
- **Entradas compartidas entre peldaños gemelos**: ×4,5-7 en las diferencias, ~×1,5-2 de coste.
- Descartado tras medir: colocación estratificada (×1,39 en z) y antitética (×0,77-1,15).

### 3.8 ¿Es normal el nulo de `z_mono`? — medido con operaciones reales → **D11**

El gate juzga `z_mono ≥ Φ⁻¹(1 − 0,05/B)` (`pipeline/autopilot/criteria.py:68-70`,
`criteria.yaml:109`), es decir, lee la z como si el nulo fuera normal. Con el Monte Carlo del repo,
30 estrategias reales largas × 100.000 sorteos (`findings-VERIF-TABLA.md` §4):

| B | umbral z | cola real del nulo | nominal |
|---|---|---|---|
| 1 | 1,645 | 0,04889 ± 0,00013 | 0,0500 |
| 2 | 1,960 | 0,02410 ± 0,00009 | 0,0250 |
| 4 | 2,241 | 0,01187 ± 0,00006 | 0,0125 |

**En largos sobre índices, juzgar por z es un 2-5 % más estricto que el α/B declarado, no más
laxo** (la primera medición, con operaciones sintéticas, decía lo contrario: refutada). Las mismas
operaciones volteadas a corto dan 0,0131-0,0133: ahí sería un 5-6 % más laxo. Oro H1 largo,
0,01267: nominal. En las 30 estrategias, `z ≥ umbral` y `mono_p ≤ α/B` dan **el mismo veredicto**
para B = 1, 2 y 4. `mono_p` es exacto en los dos sentidos pero con B = 4 necesita los 100.000
sorteos para resolver 0,0125.

### 3.9 Tres vueltas más al millón — pasada 5, las tres bit a bit (`findings-PY5.md`, `p5py/`)

- **El generador dentro del núcleo.** Con la tabla de 3.2, `rng.random` de numpy es 3,15 de los
  4,07 ns por valoración. Reproducir su PCG64 en numba (lee `rng.bit_generator.state`, deja el
  generador donde numpy lo dejaría con `advance()`; `p5py/pcg.py`, 40 líneas): **4,07 → 2,24 ns**
  en `timing` y `timing_sizing`, 10,9 → 6,8 en los dos peldaños con hold. `array_equal` contra el
  núcleo de 3.2. A 1 M × 4 peldaños: 9,0 → 5,4 s por estrategia y núcleo (ESTIMADO).
- **La tabla, por (ventana, hora) y no por operación.** El P/L de los peldaños con hold sólo
  depende de (ventana, hora, hold, barra). n = 2.000: 59,3 → 2,1 MB y construirla 2,20 → 0,04 s;
  con 4 procesos, 13,3 → 8,7 ns por valoración (la caché deja de pelearse). Las cifras de 3.2 a un
  núcleo son optimistas para n grande a máquina llena. Exige un lado por estrategia (regla 13).
- **`q_null` en sitio.** ×1,5-2,1 (no los ×3-5 que estimaba 3.4: el rechazo de Fisher-Yates manda)
  y, lo que importa, desaparece la matriz permutaciones × operaciones (2,4 GB por estrategia a
  1 M × 300). Para el bit a bit hay que sumar como numpy: `reduceat` es `a[0] + pairwise(resto)`.
- **`wfc/measure/reading.py:48-65`:** a 1 M materializa tres matrices sorteos × variantes (~4 GB
  cada una). Trocear `measure` entero por bloques de sorteos, no sólo `signs`.

Medido y descartado: `out=` con búfer (igual), el generador de numba (más lento, 5,86 ns), cuatro
cadenas intercaladas (igual), la tabla en céntimos `int32` (igual), el PCG en la escalera de 3.3
(×1,05). float32 y SFC64 ganan menos que el PCG propio y además cambian los sorteos. NUMA: un
solo nodo, nada que fijar.

### Proyección a 1 M de sorteos, 4 peldaños (ESTIMADO sobre lo medido; escalado lineal verificado a 48)

| ruta | por estrategia y núcleo | 1.000 estrategias | 20.000 |
|---|---|---|---|
| gate 3c hoy | 130-340 s | 45 min - 2 h | 15-39 h, y no cabe en RAM |
| gate 3c con tabla (§3.2) | 9-16 s | 3-5 min | 1,1-1,8 h |
| escalera hoy | 120 s | 42 min | 13,9 h |
| escalera fundida | 33 s | 11 min | 3,8 h |

**Precisión que compra:** el error de la z en el umbral 1,645 es 0,0049 a 100.000 y 0,0015 a 1 M;
veredictos que cambian con la semilla, ~0,2 % a 100.000 y ~0,06 % a 1 M (ESTIMADO).

---

## 4 · Anchura: 48 núcleos donde hoy hay menos

Evidencia: `findings-PAR.md`, `findings-VERIF-B-DMN.md` (DMN), `findings-ARCH.md` §0-1.

### 4.1 Un comando por test tras el corte, no uno por superviviente — lo que más paga con miles

`pipeline/autopilot/run.py:176-179` pasa una orden por superviviente y `ui/daemon/launch/chain.py:
166-179` lanza un subproceso `--strategy` por cada una, 8 a la vez para el mono
(`ui/daemon/jobs.py:33`, `PICKED = {"monkey": 8}`). Son ~10 núcleos de 48.

MEDIDO, un mono real (294 operaciones, 100.000 sorteos × 4): 7,47 s, de ellos 6,2 de cálculo y
~1,2 de coste fijo (intérprete 0,25, imports 0,77, caché de numba 0,18). **No se pierde en el
arranque: se pierde en la anchura.** La ruta de población ya existe
(`studies/readings/monkey/report.py:53-62,111-120` → `many.run`, con `simulate.warm/prime` una vez y
fanout a 48) pero sólo corre sin `--strategy`.

- **Arreglo:** `--only <fichero de nombres>` que filtre la muestra antes de `many.run` (mono,
  entryQuality, edgeCost, exposure) y que `python_step` lance **un** comando por test.
- **Ganancia** (ESTIMADO): 1.352 supervivientes, de ~21 min a ~3 min; a 1 M de sorteos, de ~2,9 h a
  ~29 min, y a 6,5-10 min con §3.3 dentro.
- **Lo que cambia por esa ruta** → **D2**: descarta las de < 30 operaciones (`many.py:47`);
  `draws.save` **reemplaza** el fichero (`report.py:127`); y escribe `nulls.csv`, que es lo que lee
  `monkeyExcess` (`ui/daemon/runner/screening.py:62-63`) — con `--only` el panel traería sólo las
  supervivientes y cambiaría el «cuántas baten al azar».
- **Prueba:** `nulls.csv` idéntico por los dos caminos con la misma raíz, antes de retirar el viejo.
- `entryQuality` no tiene ruta de población (`eratio.py:87` crea su `rng` por banda con semilla 0:
  un bucle en un proceso da lo mismo). Hoy cada subproceso relee `read_bars`, el M1 y el parquet.

### 4.2 Dos implementaciones del mismo paso

El botón de la ventana (`ui/daemon/workflow/run.py`) usa `batch.fold`: un proceso, 44 trabajadores
por `fork`. «Correr workflow» y el autopiloto (`chain.python_step`) lanzan `SLOTS // 3` = 16
subprocesos para lo ligero y **1** para lo pesado salvo el mono: crossmarket, mcRetest, feedQuality,
cscv y monteCarlo con supervivientes elegidas van en serie (`PICKED.get(key, 1)`). Arreglo:
`python_step` usa `batch.fold`. Y los tests independientes de un mismo paso van uno tras otro
(`chain.py:166`): repartir por peso (`jobs.weight`); `monkeyExcess` va después de `monkey`.

### 4.3 Estudios en serie dentro de su proceso

| dónde | qué | arreglo |
|---|---|---|
| `studies/transfer/crossTF/cells.py:149-151`, `tf/table.py:67-93` | celda tras celda, el mono de escalera a 100.000 sorteos en un núcleo | `fanout` por celda y madre; semilla `strategy\|block`, mismos sorteos |
| `studies/transfer/crossmarket/travel/run.py:157`, `many.py:72` | en serie; `--workers` ya no hace nada | `fanout.run` con `_SHARED`, como `cscv/measure/queue.py` |
| `studies/closing/blindJoint/many.py:132`, `exposure/many.py:36` | por madre, en serie | `fanout` |
| `pipeline/autopilot/closing.py:19-21` | `for argv in jobs: call.run(argv)` | `ThreadPoolExecutor`, tras comprobar que `exposure` no escribe un fichero compartido |
| `wfc/one.py:42,142`, `wfm/many.py:149`, `oos2Reading/report.py:42`, `spp/run.py:36,104` | 1 núcleo cada uno, 16 a la vez → 32 libres | subir `SLOTS` mientras haya RAM |
| `sqx/variants/neighbourbatch.py:62-81` | 500 vecinos por madre en serie (1,8 ms cada uno) | `fanout`, como `fabricate.batch` |
| `studies/data/spread/scan.py:76-86` | 29 activos en serie, 13-25 s por `.dat` con caché caduca | `fanout` de 8 |

**Medido en la pasada 4** (`findings-COSTES.md`, `v4d/`; ≤ 4 núcleos, máquina con carga 3,5-5,7):

| fase Python (media de 3 corridas completas) | s | dónde se va | con el arreglo (ESTIMADO a 48) |
|---|---|---|---|
| 16.5 variantes | 487 | ~126 s son Python (`equity` 37, `make` 23, `varianttrades` 18, `execute.clear` 16, `mothertrades` 14, `collect` 12); el resto SQX y su export | §6 y §7.3 |
| 13 vecinos | 76 | sin perfilar: sus entradas ya no existen | — |
| gate | 72 | `inputs.load` 16 s; 3ab **52 ms por estrategia en serie**; `one.run` de 10.000 miembros 8,7 s; escribirlos 3,3 s | 3ab con `fanout`: 13 → ~1 s |
| crossTF (11.5 y 12) | 50 | `cells.numbers` 0,75 s por celda, 30 celdas en serie; `engines/nulls/kernel.runs` 2.061 llamadas, 18,4 s | `fanout` por celda: 23 → 2-3 s |
| decay | 46 | 10.000 `.sqx` × 2 leídos en serie (0,9 + 0,5 ms) y `decay.table` 1,9 ms por estrategia | `fanout` de la lectura: ~4 s |
| 18.5 a ciegas | 37 | cómputo real ~7 s; **~40 s sin explicar** (ni import ni lectura: mide `look.admit`, el ledger y la escritura) | — |
| feedQuality | 36 | sin perfilar | — |
| crossmarket | 20 | `tensor.build` 10,9 s en un proceso; `assetdata.symbol_for` 3,3 s (1.495 llamadas con un `deepcopy` cada una) | `fanout` por mercado: ~2 s; memoizar `symbol_for` |

Dos lecturas de esa tabla. **El gate de 386-447 s que aparece en algunas corridas no es un problema
de rendimiento: son corridas `--smoke`**, donde sólo juzga el nivel 0 y las 3.400-4.100 estrategias
llegan vivas al 3ab en serie (3.422 × 52 ms ≈ 178 s). Y `entryQuality` no tiene ruta de población:
`--strategy` paga 0,8 s fijos por llamada (imports, parquet, M1) para 0,9 s de cómputo.

`marketProfile`: los 1,4 GB por celda de su README no vienen de las entradas (MEDIDO: 676 MB tras
cargar, +140 MB privados por celda). Una tarea por (activo × timeframe) con las barras cargadas en
el padre antes del `fork`, como ya hace `sweep_all`: 48 de ancho en ~8 GB (ESTIMADO), no 67.

### 4.3 bis · Las fases que quedaban sin explicar — pasada 6 (`findings-P6.md`, `p6/`)

Medido con 4 núcleos sobre las cosechas reales de USATEC, NIKKEI wf3 y DAX wf2.

**a) El 18.5 tarda 40-60 s para 7 s de cálculo porque dos madres se pisan los hilos de BLAS.**
`pipeline/autopilot/blind.py:102-105` lanza una madre por hilo; cada subproceso llega a
`studies/optimisation/marketSurfaces/report.py:97` (`one.measure`) con OpenBLAS a 64 hilos, y el
producto `c @ gross` de `measure/reading.py:70` se ahoga:

| `one.measure` de una madre (MEDIDO) | pared | CPU |
|---|---|---|
| un proceso solo | 3,1 s | 11,8 s |
| **dos a la vez, hilos por defecto** | **33 s cada uno** | 58 s |
| dos a la vez, `OPENBLAS_NUM_THREADS=1` | 4,1 s cada uno | 4,1 s |

En producción cuadra: 9,0 s con una madre (DAX), 32-42 s con dos (NIKKEI, USATEC). No son ni el
ledger ni la escritura (< 0,1 s). Arreglo: `with threadpool_limits(1):` alrededor de
`one.measure`, o `OPENBLAS_NUM_THREADS=1` en `chain.command` (`ui/daemon/launch/chain.py:93`) como
ya hace `ui/daemon/runner/batchrun.py:13`. **~50-60 s por corrida.** Puede mover el último bit de
los productos del nulo; ρ, p y veredicto no cambian salvo empate exacto: compruébalo sobre las
tres madres reales antes de dejarlo. Y busca el mismo patrón en todo lo que `chain` y `blind`
lanzan en paralelo: cualquier `@` grande en el proceso padre de un estudio lo sufre.

**b) `marketSurfaces_detalle.json`: rejillas de 982 × 929 vacías al 99 %.** Un parámetro continuo
(932 valores distintos en 1.004 variantes) da una rejilla de ~1000 × 1000 por par y mercado
(`contract/grids.py:33-36,55-56`, `core/study/blocks.py:40`): en DAX, 432 rejillas, 26,1 M de
celdas con valor en el 0,9 %, **159 MB y 36 s de los 50,7** de esa madre. Ningún `.py` lee el
fichero. Depende de la plantilla (USATEC: 1,5 MB). Arreglo: agrupar en ≤ 12 cuantiles un eje con
más de 12 niveles antes del `pivot_table`, o no escribirlo → **D18**.

**c) feedQuality: el 66 % es el sorteo de subconjuntos de la alarma**
(`studies/data/feedQuality/alarm.py:24-28`, `argpartition` sobre sorteos × operaciones): 70 de
106 ms por estrategia, 1.064 s de CPU por 10.000. Claves `float32` con umbral: 86 → 33 ms por
10.000 sorteos (MEDIDO), pero **cambia el flujo de sorteos** (p se mueve dentro del ruido; puede
voltear una estrategia pegada a 0,01) → **D19**. La parada secuencial a 50 excedencias dejaría el
14 % de los sorteos, pero adelgaza los histogramas guardados de las no-alarmas: no se propone.

**d) Gate.** `inputs.load`: el `pivot` de la equity (30 M de filas) son 13,2 de 15,5 s; dispersar
por códigos de diccionario, 3,8 s con `DataFrame.equals` cierto (hecho esta noche si la prueba lo
confirma, ver bitácora). `one.run` construye y escribe un miembro para las 10.000 aunque 9.701
cayeron en los niveles 0 y 1a: es función pura de `scorecard.parquet`; hasta 12 s. No comprobado
si la ventana abre directamente el JSON de una caída → **D20**.

**e) crossTF:** lo que no es `many.run` son dos `draws.save` seguidos sobre el mismo fichero
(`report.py:42`, `tf/run.py:57`): el segundo relee y recomprime a zstd-19 lo que acaba de escribir
el primero. 3,5 s por llamada, 7 por corrida.

**f) Paso 13 y «14 python»:** el Python de las vecinas son ~5 s de 69; el resto es SQX y dos
`orderstocsv`. Los 32 s del 14 eran 29,7 s de exportar operaciones de los MCR que nadie lee
(§7.2, quitado esta noche).

**g) El almacén (`/store-save`, fuera de las fases del autopiloto), medido por lectura y prototipo:**

| dónde | qué | cifra |
|---|---|---|
| `core/archive/collect.py:186-205` `harvest_rows` | relee `equity.parquet` (30,6 M filas) **por cada superviviente** | 2,0-4,5 s cada vez: 13-25 min para 394 (ESTIMADO) contra ~3 s en una pasada con `("identity","in",[…])` |
| `collect.freeze`, `_names` | reparsea cada CSV y parquet de informes por superviviente | 2,7-3,0 s cada uno |
| `core/store/write.py:36` `folder()` | un `glob` de todo el almacén en cada llamada | `audit.held`: 11,4 s para 394, 9,6 en `pathlib`; un diccionario identidad → ruta por proceso |
| `core/archive/read.py:23-40` `listing` | parsea 331 MB de `view.json` para leer un campo | 2,2 s por llamada del demonio |
| `core/store/write.py:125-133` `packed` | zip a nivel 9: 0,46 s contra 0,19 a nivel 6 (+2 % de tamaño) | bajar el nivel cambia el sha256 y duplicaría al re-guardar: memoriza el hash, no toques el nivel |
| `studies/optimisation/wfm` `tradelevel.drift_term`, `annual_sharpe` | bucle Python por clave; `bdate_range` repetido por celda | 2,7 de 5,3 s; 21 ms por celda |

### 4.4 Techos fijos sin razón escrita

`marketSurfaces/config.yaml:57` (12) · `gate/collect.py:15` y `core/tradepack.py:15` (8) ·
`sqx/export/export_spp.py:23`, `wfc/calibrate/__main__.py:28` y `equity/closecurve.py:13` (16; a
0,25 GB por proceso caben 48 en ~12 GB) · feedQuality (6, 8, 13) · `funded/sim/config.yaml:20`
(8 hilos; subirlo puede cambiar el orden de una reducción en coma flotante: mídelo).
`portfolio/common/monteCarlo/simulate/engine.py:71` usa **96** procesos, el único por encima de 48:
una tarjeta midió que más de 48 es peor (48 → 44,6 s, 96 → 59,4 s). Y
`portfolio/common/construct/config.yaml:6,7,57` declara `max_ram_gb: 80` contra los 20 GB de Python
de la regla 3 → **D7**.

**Con razón escrita, no los subas sin medir:** `mcRetest` (16, medido) y los 4 de `marketProfile`,
`profilePower` y `pooledProfile` (1,4 GB por trabajador; 19 ocuparon 21,5 GB el 2026-10-02,
`marketProfile/README.md:46`). Para estos tres el arreglo es otro: **cargar las barras en el padre y
repartir por `fork`** (como ya hace `sweep`), y trocear por (símbolo, marco, trozo de sorteos) con
semilla `default_rng([seed, crc32(f"{symbol}/{tf}"), trozo])`. Un mapa entero son hoy 10,9
horas-núcleo para 19 activos (MEDIDO) en 2,7 h de pared. **Cambia el flujo de sorteos** → **D12**.

### 4.5 `fanout` con `fork` desde un proceso con hilos

`ui/daemon/loader/state.py:114` hace `fork` dentro del demonio FastAPI;
`portfolio/common/monteCarlo/simulate/engine.py:66` documenta un bloqueo real por eso mismo.
Arreglo: `forkserver` o un subproceso. Tareas diminutas (`sqxfile.identity` por fichero en
`gate/collect.py:20`): agrupar en bloques de 100, como `sqx/variants`.

---

## 5 · Cruce SQX ↔ Python sin tocar SQX

Evidencia: `findings-CRUCE.md` (prototipos `ob3.py`, `ob4.py`). Todo esto es Python puro y **no
espera a `AlgoBank`**; lo que `AlgoBank` vuelva innecesario se borra entonces.

- **Una sola pasada de `orderstocsv` en 6+7.** Hoy son tres sobre los mismos ficheros:
  `ui/daemon/loader/afterrun.py:124` lanza los dos `export.trades` y después la cosecha vuelve a
  exportar. `harvest --exports` ya escribe los dos `trades.parquet`, pero
  `ui/daemon/loader/state.py:223` no le pasa el flag. **206 s por corrida (MEDIDO).**
- **Métricas, curvas, identidad y estructura en paralelo.** `gate/collect.py:86,134`,
  `core/sqxview.py:50`, `gate/harvest.py:141` recorren 20.000 `.sqx` en serie: 54 s (MEDIDO; otra
  medición sobre 150 `.sqx` reales da 6,2 ms por fichero sólo en `sqxview.frame`, ~124 s). Las
  cinco lecturas de 10.000 ficheros con 24 procesos: **2,5 s** (MEDIDO). La palanca es el `fanout`,
  no «abrir el zip una vez» (las aperturas son ~15 %).
- **Un proceso para todo el export del paso.** `afterrun.py:128,135` lanza ~50 subprocesos por
  corrida, cada uno con sus imports y su huella en frío. 40-60 s ESTIMADO; cachear la huella por
  (ruta, mtime, tamaño).
- **`core/sqxfile.py:45-65`** — `identities()` calcula en los hijos del `fanout` y el padre no
  recibe `_SEEN`: `curate`, `export_trades`, `finalists` y `locate.py:28` lo recalculan.
  `sqx/curate/apply_verdict.py:229` reconstruye `set(on_disk)` en cada vuelta: 3,54 s con 5.000
  nombres contra 20.000 (MEDIDO); y `:97-103` hashea el databank dos veces.
- **Esperas fijas:** `sqx/variants/execute.py:79-86` duerme 4 × 2 s + 8 s de `SETTLE` **por lote**, y lo
  usan `spp.py:128,141`, `pilot.py:68` y `neighbourbatch.py:156`: sustituir por el conteo de
  registros (necesita SQX vivo para probarlo).
- **Esperas con `sleep`** (suma ~15 s por corrida): `sqx/projects/live.py:81,146` (1 s por tarea,
  ~30 esperas → `inotify` sobre el log), `bin/sqx-worker.sh:348-364,431,438`, `core/worker.py:154`,
  `ui/daemon/launch/chain.py:122`. Bien como están: `live.py:209,244`, `livexec.py:51`.

---

## 6 · `AlgoBank`: un binario por databank, escrito desde la memoria de SQX

Evidencia: **`findings-ABK.md`** — el snippet Java entero, el formato, el lector Python, los sitios
que cambian y el plan de prueba. Léelo completo: aquí va sólo lo decidido y el contrato.

**La idea.** Hoy cada databank cruza así: SQX sincroniza a disco → se copian los `.sqx` →
`orderstocsv` escribe CSV → Python los parsea → parquet; y aparte Python abre los 10.000 zips para
métricas, equity, identidad y estructura. `AlgoBank` es un snippet de CustomAnalysis (hermano de
`sqx/snippets/Snippets/SQ/CustomAnalysis/AlgoTrades.java`) que recorre el databank **en memoria** y
escribe **un fichero `.abk`**: órdenes en registros fijos de 64 bytes, equity diaria, métricas, el
XML de cada estrategia e índice. Python lo abre con `np.memmap`. Ni CSV, ni 10.000 zips, ni esperar
al sync para leer.

**Decidido por el dueño (2026-10-12):**

1. **Un fichero por databank.**
2. En **`/dev/shm/algobank/<proyecto>/`** (ruta nueva en `core/paths.py`), borrado al convertir.
3. **Transitorio:** los consumidores siguen leyendo `trades.parquet`, `metrics.csv` e
   `identity.csv`; el almacén no cambia.
4. **Reserva nº 2 = leer `orders.bin` directamente** (propuesta de la auditoría, aceptada «lo que
   tú propongas»). Contradice la tarjeta `knowhow/sqx-format/sqx-zip-members.md` («Never parse
   orders.bin»): **reescríbela en la misma tarea.** Condiciones: test dorado contra `orderstocsv`;
   un código de tipo, muestra o cierre sin etiqueta **rechaza el fichero** y cae a la reserva
   siguiente; decimales de precio de la ficha del activo; redondeo half-up (con el de numpy salen
   48.091 balances a ±0,01). El prototipo midió 10.000 estrategias en 0,89 s contra 120 s, con 0
   diferencias sobre 4,54 M de operaciones de 5 databanks.
5. **`AlgoTrades` se quita — pero sólo después de comprobar que el binario funciona
   PERFECTAMENTE.** «MUY IMPORTANTE» (sus palabras). Hasta entonces sigue de reserva nº 3.
6. **La equity de todos los resultados** (Main, mercados adicionales, los 30 del WF, Portfolio).

**Cadena de reserva**, cada caída dicha en una línea del log del paso: `.abk` válido (magia,
versión, tamaño, mismos nombres que el databank) → `orders.bin` + lecturas en paralelo de §5 →
`memtrades` (`AlgoTrades`) → `orderstocsv`.

**«Perfectamente» quiere decir esto** — el plan de 11 pruebas de `findings-ABK.md` §5, en el
conductor, en un proyecto `Test_` (reglas 5, 6 y 10), y **todas** con igualdad exacta
(`assert_frame_equal(check_exact=True)`, categorías incluidas):

- operaciones contra `orderstocsv` y contra el decodificador de `orders.bin`, campo a campo;
- identidad (`sqxfile._hashed` del XML igual a `sqxfile.identity` del fichero), estructura y
  `param_count`; las 152 métricas en cada muestra; la equity día a día en cada resultado;
- **en cada tipo de databank:** Results, OOS, cross-market en modo `all` (con `block`, `Symbol` y
  `torn_blocks`), SPP IS y OOS, los ocho MCR, WFM, CrossTF, un build corto, uno con SL/PT y uno con
  una orden pendiente sin llenar al final;
- databank vacío; databank que se está escribiendo (nunca un `.abk` a medias bajo el nombre final);
- tras parar y arrancar SQX, el `.abk` nuevo igual al anterior salvo la marca de tiempo.

Si una sola falla, `AlgoTrades` se queda y se dice cuál.

**Lo que no se sabe hasta compilar** (el snippet no se ha ejecutado; los nombres de API salen de
los fuentes del install, sin `javap`): los tipos de `Ticket`, `PL`, `Size`, `AccountBalance`, `MAE`
y `MFE` — el snippet escribe sin `cast` a propósito: si uno es `double`, no compila y el error lo
nombra; que `XMLUtil.elementToString` dé los mismos bytes que el miembro del zip (si no, la
identidad se sigue leyendo del `.sqx`); `getDouble` sobre una clave entera o ausente; y cómo
iterar las claves de un `SQStats` (por eso Python le pasa la lista).

**Fuera de la v1:** el `optimizationProfile.bin` del SPP, la matriz del WFM y las simulaciones del
MC Retest. Un solo hilo en Java: `parallelStream` fue 3,6× más lento en `AlgoTrades`.

**Ganancia** (ESTIMADO): el cruce baja de ~2.740 s a ~1.600-1.700 s; operaciones 569 → 30-50,
cosecha 213 → 10-20, retests y vecinos 236 → 10-20, métricas 71 → ~5. Y el paso 8 deja de esperar
los ~110 s del sync (el sync sigue siendo obligatorio para persistir: regla 1).

---

## 7 · Esperas de SQX — 🔴 espera a D6

Evidencia: **`findings-SQXPY.md`** (pasada 5: `fases.csv` unido al log del propio SQX, prototipos
`p5sqx/`) y `findings-CRUCE.md`. **Sin matar SQX antes de tiempo** (dueño). Es el frente con más
segundos por línea de código después del control de falsos positivos.

**Línea de tiempo real** (MEDIDO, `Test_USATEC_H1_ruptura_leaseWeb`, 10.034 s; el log de SQX da
2.360 s de cálculo, **23,5 %**, no los 2.514 de `fases.csv`: la fase `execute` del 16.5 mezcla
cálculo y sync):

| paso | total | SQX calcula | SQX guarda | arranque / reapertura / parada | cruce | estudios |
|---|---|---|---|---|---|---|
| 6+7 | 2.445 | 1.871 | 116 | — | 449 | — |
| 8 | 4.408 | — | — | — | — | 4.366 |
| 9 a 16 | 645 | 76 | 7 | 105 | 253 | 108 |
| 16.5 | 627 | 68 | 136 | — | 389 | 8 |
| 19 | 1.191 | 346 | 1 | 606 | 221 | 5 |
| arranque + parada | 613 | — | — | 604 | 10 | — |

### 7.1 Por qué SQX tarda 8 minutos en salir — explicado, y es evitable

SQX marca como pendiente de guardar **todo databank que carga de fichero**. Al salir («Save all
strategies before exiting») los regraba **en serie**: 175 databanks, 33.223 ficheros, 10 proyectos,
487-515 s. Pero su «Periodical sync … every 1 hour» los guarda todos **en paralelo** una hora
después del arranque: 161 databanks en **76 s**.

En 27 sesiones del 10 y el 11 de octubre: las 7 que vivieron **más de una hora salen en ~4 s**; las
20 de menos de una hora tardan 6-8 minutos, incluidas tres que no hicieron nada.

La reapertura antes de SPP y WFM (`ui/daemon/launch/liverun.py:101-104`) crea justo eso: dos
sesiones cortas. Cuesta 105 + 606 s **y además** los ~510 s de la parada final, que sin reabrir
serían ~4. **~1.220 s por corrida.**

- **A. No reabrir** (`AGED = set()`). Con la penalización de sesión vieja que anota `liverun.py:26`
  (WFM ×1,44, SPP ×2) quedan ~850-1.000 s netos por corrida (ESTIMADO). Experimento que lo zanja,
  en el conductor: el mismo WFM recién abierto y tras 2 h, con `-Xlog:gc:file=…` (la hipótesis de
  la lentitud es GC completo sobre 43.000 estrategias vivas; `liverun.py:27` dice «cause not known»).
- **B. Guardar antes, en paralelo — PROBADO EN VIVO el 2026-10-13 (conductor): funciona.** Tras
  `live.start`, un `synchronizeDatabank` por la API sobre un databank **donde memoria == disco**
  limpia la marca: la salida ya no lo regraba.

  | ciclo (conductor, 17 `.sqx` en un databank) | líneas «Save all strategies before exiting» | stop → fuera |
  |---|---|---|
  | arrancar y parar | 1 (`saved 17 … in 5.46 s`) | 10,9 s |
  | réplica | 1 (`in 5.50 s`) | 10,9 s |
  | arrancar, `synchronizeDatabank`, parar | **0** | 5,8 s |

  La llamada es la de `sqx/projects/live.py:201` (`live.call(role, "synchronizeDatabank",
  projectName=…, databankName=…)`); responde al instante («Synchronization started») y el fin se
  lee en el log (`Sync triggered by 'API request project/synchronizeDatabank …'`). Nada se
  perdió: nombres y recuento idénticos en las 41 carpetas (los tamaños cambian ±0,07 % en cada
  regrabado: un hash de tamaño no sirve de invariante). **Sin medir:** el paralelismo y la escala
  — con un solo databank el guardado por API cuesta lo mismo que al salir (5,44 s), así que la
  ganancia en el custodio (~990 s por corrida, ESTIMADO) depende de que 16 a la vez rindan como
  el sync horario (161 en 76 s), y de cuánto estorba ese guardado a la tarea que arranca después.
  **Ojo con el filtro:** el esbozo excluía `syncType == "Auto-sync never"` y los proyectos de
  serie, y justo `Retester/Results` (de serie, «never») es lo que la salida sí regraba. Regla 1:
  nunca sobre un databank con estrategias sólo en memoria. Evidencia: `scratchpad/live/`.
- **C. El custodio con un solo proyecto** (regla 6: retirar los `Test_` al acabar): menos que cargar
  (57-60 s de los ~90 del arranque son databanks ajenos) y menos que regrabar.

Escribe la tarjeta en `knowhow/databanks/` cuando lo pruebes: resuelve lo que la tarjeta de
reaperturas dejaba sin explicar.

### 7.2 Exportaciones que se rehacen sin que nada cambiara

- **La huella no sobrevive a «cargar y regrabar»** (`ui/daemon/loader/state.py:149`). En 4 de 4
  corridas, `Results` (10.000, intacto) se re-exporta en el paso 19, justo tras la reapertura que
  lo regrabó: ~155 s, más ~30 de OOS y Retest, más 43 s en los pasos 11 y 13. **Arreglo sin SQX:**
  que `liverun.export` exporte sólo las salidas del paso y los databanks rellenados
  (`liverun.py:141` ya tiene `outputs`), no todo lo «stale» del proyecto (`afterrun.py:127`). Con
  7.1 A desaparece solo. Qué miembro del zip cambia no se sabe: copiar un databank, arrancar y
  parar, y comparar miembro a miembro con `state._entries`.
- **Tras un corte se re-exporta con dos JVM** lo que es un subconjunto del export vigente
  (`ui/daemon/launch/chain.py:130-142` tras `live.cut`; paso 8, 10.000 → 3: 33 s). Arreglo: si los
  nombres nuevos ⊂ los exportados y los ficheros no cambiaron, filtrar `trades.parquet` y
  `metrics.csv` por nombre. Test dorado contra un re-export real (orden de filas y tipos).
- **`chain.load` exportaba las operaciones de los MCR**, que nadie lee (dueño, 2026-10-01;
  `afterrun.py:32-36` ya las excluía): 32 s por corrida, ~120 con los 8 MCR.

### 7.3 El 16.5: SQX calcula el 11 % de lo que tarda

Por madre (MEDIDO): SQX calcula 32 s; el sync de 3 × 1.004 ficheros, 66 s; `export_retest`, 141 s;
`equity` 19; `varianttrades` 16; `clear` 8. ~296 s. **Esos databanks se vacían al acabar: el sync
sólo existe para alimentar el export.** Con `AlgoBank` leyendo de memoria (§6), `synced()` deja de
llamarse y `clear` es sólo `removeReports`: ~60-70 s por madre (ESTIMADO). Lo mismo en vecinos
(`sqx/variants/neighbourbatch.py:170`) y en el piloto (`pilot.py:68`). Hay que probarlo en vivo:
300 variantes, volcado de memoria sin sync contra `orderstocsv` con sync, y que la salida no guarde
nada. Además: `sqx/variants/livexec.py:30-39` borra y carga banco a banco (7,9 s para 0,3 s de SQX,
tres veces por madre → en hilos); y madres en lote en un solo `WFC_Variants` (~35-45 s por madre
extra, sin probar).

### 7.4 Lo demás

| dónde | qué | segundos por corrida | necesita SQX |
|---|---|---|---|
| `core/exportdrv.py:31-33` | la JVM de un tiro paga 7,4 s de arranque y 3,5 s de cola: 30 lanzamientos, 23 de ellos para ≤ 50 estrategias con 0,31 s de trabajo | ~320 | sí (¿acepta `/call` un `-tools`?) |
| `sqx/projects/live.py:76-81` | `start` espera a los databanks de **todos** los proyectos del install | 84 | sí; `stop()` tendría que esperar la carga entera antes de salir (regla 1) |
| `bin/sqx-worker.sh:364` | de «Exit app - ok» al siguiente paso: 12,6 · 20,2 · 14,3 s (un `sleep 15`) | ~35 | sí |
| `sqx/export/memtrades.py:29-34` | una tarea de SQX por databank; el snippet podría recibir `b1;b2;…` | 20-30 ESTIMADO | sí |
| `mt5/verify/sqxside.py:72,83` | paso 26: 8 s fijos tras `load` y 5 s por firma antes de mirar | ≥ 8 + 5 × firmas | sí |
| `pipeline/autopilot/variants.py:87` | la fase `execute` mezcla cálculo y sync: falsea el presupuesto | — | no |

**Decisión del dueño (D16):** recortar `Results` a las supervivientes tras el paso 8 (ya está en
parquet y en el almacén): 113-116 s menos por cada parada corta y 45 s menos por cada carga. El
paso 19 ya recorta OOS igual.

---

## 7 bis · Lo que el workflow le pide a SQX y nadie lee — skills y know-how (`findings-SKILLS.md`)

Base: `fases.csv` de las cinco corridas completas del 10 y el 11 de octubre.

- **El 16.5 calcula 11 mercados de más en casi todas las madres.** Sólo `marketSurfaces` (18.5)
  los lee; `wfc`, `cscv` y `cloud` filtran por el mercado principal. Y el 18.5 sólo corre si el
  descuadre es < 0,01 (`pipeline/autopilot/blind.py:36-50`): **10 de las 12 madres** de los cinco
  proyectos más recientes tienen descuadre entre 0,0129 y 0,8675 y se lo saltan.
  `pipeline/autopilot/variants.py` ya tiene `wire(markets=False)` y su comentario dice «11 others
  were 81 s of its 86». Arreglo: patas sin mercados, y los mercados sólo para la madre que pasa el
  descuadre. **300-600 s por corrida** (ESTIMADO, 150-200 por madre saltada). Prueba en vivo: una
  madre con y sin mercados da lo mismo en el mercado principal.
- **El Build sigue 15-24 minutos después de llenar el banco** → **D24**. Con el ritmo de aceptadas
  del ledger las 10.000 se alcanzan a los 362-1.119 s de los 1.800 (ESTIMADO, ritmo constante); el
  resto sólo sustituye peores por Ret/DD IS, orden que el paso 8 no lee. En campaña el tope son
  180 min.
- **El WFM es la única tarea a M1** (`assets/_build.yaml:452`, `precision: 2`) contra
  `:95-99` («selected timeframe en todo», dueño 2026-10-02) → **D25**.
- **MCR 1, 4 y 7 y T1 no alimentan ninguna regla** (`criteria.yaml:187-193`, `rules: []`):
  70-100 s por corrida. Quitarlos exige reconectar la entrada de SPP IS, que hoy es `MCR 7 OHLC`
  → **D26**. El perfil de SPP OOS tampoco alimenta regla, pero su banco sí es el corte del 19.5 y
  el 20: se queda.
- **Una sesión de SQX viva para toda la campaña** (arranque ~90 s + parada ~500 s por celda): sin
  probar; `knowhow/sqx-drive/live-chain-without-restart.md` sólo cubre el modo GUI. Experimento:
  crear y retirar un `Test_` en una sesión viva y ver si el siguiente proyecto arranca limpio.
- **Los dos servidores:** partir el Build o correr celdas en gorilla choca con que el ledger es
  por servidor y partiría el número de lotes B de la z del paso 8 → **D27**, antes de medir nada.
- Quitar `MonteCarloManipulation` del Build no daba rendimiento (323-339 gen/s con él, 334 sin).

**Skills y tarjetas** (corregidas el 2026-10-13 salvo la primera): `workflow-simple/SKILL.md:85`
(«never retire the project unless the owner says so») contradice la regla 6 → **D28**;
`oos-gate/SKILL.md:89` mandaba un `action=count` (regla 1); siete skills de paso describían la ruta
manual sin nombrar la regla 19; tiempos viejos en `spp`, `wfm` y `mcretest`; `steps.md` paso 14
con T2 y T3 ya borrados; siete tarjetas de `knowhow/perf` y `knowhow/sqx-drive` con cifras que las
corridas desmienten. Los tres reintentos de `workflow-simple` §4 gastan un turno de agente cada
uno: un bucle en `bin/workflow.sh` hace lo mismo sin releer la conversación.

---

## 8 · Almacén de población sin copia, y el motor por corrida

Evidencia: `findings-ARCH.md` (prototipos `arch/`).

**La pregunta del dueño — «¿no requeriría una memoria inmensa?» — tiene respuesta medida: no.**
Hoy cada proceso carga su copia privada; el motor cuenta cada dato una vez.

| | memoria |
|---|---|
| un mercado en M15 + M30 + H1 + H4 | 26 MB (MEDIDO) |
| los 12 mercados del cross-market en M30 | ~106 MB |
| operaciones de una población de 10.000 | 242-544 MB (MEDIDO) |
| **48 trabajadores leyendo las 7,2 M de operaciones** | **684 MB en total** (MEDIDO, PSS) |
| peor caso: el M1 de los 12 mercados | ~3,6 GB |
| hoy: 8 carriles de mono | 2,6-4,8 GB |
| hoy: 16 procesos leyendo cada uno el parquet entero | ~26 GB (EXTRAPOLADO de 4) — no cabe en los 20 |

Con 48 trabajadores el motor queda en 1-4 GB más la salida de cada estudio: **el reparto de RAM no
hay que rehacerlo.**

- **8.1 Almacén.** Una carpeta por (databank, export) con un `.npy` por campo, ordenado por
  estrategia, más `ptr.npy` (índice CSR). Abrir: 3,5 ms; una estrategia: 5,4 µs, contra 193-364 ms
  de `read_parquet(filters=…)` (`engines/nulls/inputs.py:87`). En **NVMe con `np.memmap`, no en
  tmpfs:** tras el primer toque va igual de rápido, el núcleo lo desaloja solo si falta RAM y no
  cuenta como memoria retenida. Operaciones: se borran al acabar la corrida; barras: persistentes,
  con la huella de `barstore.fingerprint`. Lo escribe el export (el lector de `.abk` ya da arrays).
- **8.2 Núcleo de población con `prange`.** Un prototipo con PCG64 dentro del núcleo, sembrado con
  el mismo `SeedSequence` de `simulate.py:144`, da **bit a bit** lo que `simulate.nulls` en 40
  estrategias reales — y **empata** en velocidad con el `fanout` de hoy (16,06 s contra 16,16). No
  se construye por velocidad: se construye como vehículo de §3.3 y para reducir dentro del núcleo
  (histograma, colas, conteos), que deja la memoria por estrategia en KB a un millón de sorteos.
  Riesgos: la siembra en Python son ~4 min en serie a 1 M (paralelizarla); `prange` reparte
  estático (intercalar por coste); sólo está prototipado `timing`.
- **8.3 Motor por corrida.** Un proceso hijo del autopiloto (no del demonio: §4.5) con los módulos
  importados y los almacenes abiertos, que recibe los estudios como llamadas. Ahorra ~120 s por
  corrida (1,3 %): **va el último.** `ui/daemon/runner/batchrun.py` ya es medio motor.
- **8.4 Un artefacto por estudio — PROBADO, NO LLEGA AL 30 %: se queda como está.** El dueño
  (2026-10-12) puso la condición: «si mejora considerablemente (al menos un 30 % más rápido) y los
  resultados guardados son los mismos o incluso más, adelante». Prototipo fuera del repo
  (`v4d/writer.py`, 500 y 2.000 miembros reales del gate): una tabla parquet con el JSON entero
  por fila escribe 10.000 miembros en ~0,45 s contra 3,3 s, y la ida y vuelta es idéntica byte a
  byte. Pero son **2,9 s de una fase de 76 s: el 3,8 %**. Y leer UNA estrategia pasa de 47 µs a
  2-5 ms, y los estudios `--strategy` escriben un fichero cada uno desde procesos distintos: una
  tabla única les metería una carrera. **No se construye.** Lo que sí queda: el `.html` por
  estrategia son 2,5 de esos 3,3 s y 4,4 MB de cada 5,3, y ningún código lo lee
  (`core/store/late.py:12`: «never stored») → **D17**. §1.1 (los sorteos) es otra cosa y sí se
  arregla.
- **8.5 Caché por madre — PROBADA: no es la palanca.** El dueño: «prueba». Las barras remuestreadas
  ya tienen caché en disco (0,02 s). Las operaciones de la madre cuestan 0,36 s por lectura; con
  caché, 12 ms (`v4d/cache.py`): ~4 s por madre. El reprecio de las mismas 1.001 variantes se
  repite en 17, 18, 18.5 y `cloud` (~4 s cada vez, 12-16 s por madre): ésa sí merece un parquet
  por madre, con clave (identidad, tamaño y `mtime_ns` de la entrada, versión de las barras,
  huella de la tarjeta de costes, hash de la configuración, semilla). **Lo que de verdad se
  recalcula es el 16.5 entero tras un fallo** (577 s, sin salto por fase hecha:
  `pipeline/autopilot/variants.py:73-99`): es §1.4, no una caché.
- **8.6 El control de falsos positivos en gorilla** → **D13**. No condiciona el paso 9 (el corte
  del 8 sólo nombra hechos de `gate`), así que la corrida no tendría que esperarlo.

---

## 9 · Velocidad puntual

Ninguno necesita SQX. «Igual» = comprobado idéntico.

| dónde | qué pasa | arreglo | medido | resultado |
|---|---|---|---|---|
| `studies/screening/analysis/tradelevel.py:130-134` (`drift_term`) | `inside[pool == group]` sobre un array de cadenas por cada par (año, duración). Lo pagan el gate, `delay.py`, `wfm/measure/excess.py:62`, `wfc/inputs/batch.py:60`, `marketSurfaces/inputs/batch.py:79`, `mcRetest/neighbours/t1.py:136` | cada grupo es un tramo contiguo de barras: rebanar. `b = max(a, min(b, L-h))`, NaN para el grupo vacío, `assert` de contigüidad | 3,08 s → 0,053 s (×58) | igual, 6 casos de borde |
| `core/store/extra.py:17,34-45,119-141` | `astype(str)` de la columna entera por superviviente y parquet; `lru_cache` sin tope | comparar categorías y filtrar por códigos | 0,49 s → 0,0033 s por millón; 4-5 s por superviviente a 9,7 M | igual |
| `core/store/late.py:30-52` | recorre todos los `lineage.csv` tres veces por superviviente | calcular una vez (`save.py:31` ya lo hace) y pasarlo | sin medir | igual |
| `mt5/compare.py:5-32` (`pair`) | filtra el DataFrame entero de MT5 por cada operación de SQX; 8 veces por verificación | listas ordenadas + `bisect`, **candidato izquierdo `bisect_left(ts, ts[j-1])`** — con `j-1` falla en empates (85 de 600) | 6,06 s → 0,011 s (5.000 ops) | igual con ese candidato |
| `mt5/reconcile/judge.py:62-67` | mide toda la historia y recorta la semana después | recortar antes, con ~2 días de margen | 15-40 s ESTIMADO | igual |
| `portfolio/common/construct/pairs/rolling.py:21-22` | `apply_along_axis(rankdata)` ventana a ventana, y los rangos de cada serie se recalculan por pareja, dos veces (`pairs/table.py:63,64`) | `rankdata(axis=1)` **una vez por serie** | ×14-25 por pareja (22,3 → 0,87 ms); N en vez de 2·parejas | igual |
| `portfolio/common/construct/search/stageb_null.py:20-34`, `greedy.py:20-31` | cada candidato nulo construye su clique en un bucle Python | `@njit(parallel=True)` con semilla por fila | 1,35 ms → 0,018 ms | **flujo de sorteos** → D12 |
| `core/tickfile.py:104-165` | decodifica en serie: 10,9 s EURUSD, 22,5 s XAUUSD | por trozos en paralelo: cada bloque empieza con un registro absoluto (**comprobado en 1,81 M de bloques de 4 feeds**). Pase de esqueleto (~13 %) o índice de bloques guardado; fundir el minuto que cruza dos trozos | ~1-3 s ESTIMADO | `assert_frame_equal` contra el serie |
| `studies/research/marketProfile/higher.py:147-160`, `series.py:107-120` | `mirror` materializa ~60 arrays negados por sorteo; `evaluate` calcula las dos direcciones | perezoso; `evaluate(directions=…)` | 15-30 % ESTIMADO | igual |
| `studies/readings/entryQuality/eratio.py` (`matched`) | recalcula la partición por hora en cada sorteo | precalcular | 3,66 s → 0,013 s (400.000 barras, 800 entradas, 200 sorteos) | igual |
| `core/tradestore.py:134,152` | dos máscaras sobre el paquete entero por llamada | `groupby.indices` | 3,9 → 0,6 ms | igual |
| `core/assetdata.py:230` | `load()` de 29 activos con `deepcopy` | caché | 14,3 → 2,4 ms | igual |
| `engines/weekly/flip.py` | matriz `float64` entera | `int8` por trozos | 8 GB a 1 M × 520 semanas | igual |
| `engines/market/feed/scale.py:49` | 6-7 s por feed de 15 años | `njit` + `prange` sobre las 168 horas | — | igual |
| `portfolio/common/monteCarlo/simulate/family_d.py`, `stitch.py:34-37` | ~40 conjuntos por ventana en serie; matriz (sims, n) + `argsort` para 4 cuantiles: 16 GB por segmento a 1 M | mandar las ventanas al `pool`; tiras + `np.partition` | 11 min por estrategia a 1 M | igual |
| `studies/breakage/mcRetest/inputs/tasks.py:104` | decodifica ~1.000 simulaciones para contarlas | `namelist()` | ×1,3-1,5 ESTIMADO | igual |
| `studies/optimisation/oos2Reading/inputs.py:38-40` | lee `variant_trades.parquet` entero por madre | `filters=` | — | igual |
| `studies/screening/gate/redundancy.py:66-74` | Jaccard por pares dos veces, O(m²) | — | sólo con grupos > ~500 | igual |

**Código muerto** (verificado): `engines/nulls/placement/kernel.py`, `placement/bootstrap.py` y
`engines/nulls/filter.py`, ~185 líneas que sólo tocan los tests (`free_models` y `holdfit` **sí** se
usan, desde `crossmarket/travel/shift.py:6`); y `pipeline/run.py` con `pipeline/stages/gates.py`
(`room` recorre los 907.000 ficheros de AlgoData por madre vía `perf/disk/inventory.py:48`): nada
de producción lo importa. Bórralo si sigue sin llamador.

**Latente:** la rama de niveles de `engines/nulls/simulate.py:70-80` está muerta (`:38` fija
`"levels": {}`) y rota si se activa: `stop` y `target` van por operación y `entries` aplanado.

**Pasada 5, sin cambio de resultados** (`findings-PY5.md`):

| dónde | qué | medido |
|---|---|---|
| `portfolio/common/construct/equity/days.py:15-73`, `universe.py:91-97` | `server_days` monta por estrategia un marco de 1,9 M minutos y hace ocho `groupby`; el día de cada minuto es el mismo para todo el feed, y cada zona tira la caché | 188 → 6,4 ms con los bordes de día calculados una vez y `reduceat` (prototipo sólo UTC→UTC) |
| `tools/depmap.py:49,68,90`, `tools/checks.py:52,109,200` | el árbol de 1.566 ficheros se parsea ~7 veces en el comando que cierra cada tarea | ~13 → ~4 s con un `lru_cache` sobre el parseo |
| `studies/optimisation/cscv/measure/cscv.py:125-137` | argmax, rango e histograma por fila fundidos en un núcleo | ×1,33-1,44, cinco salidas idénticas |
| `studies/breakage/mcRetest/measure/originals.py:73` | lee el `trades.parquet` de las 10.000 para quedarse con las supervivientes | `filters=` y `columns=`: 2-4 s y ~0,5 GB (ESTIMADO) |
| `engines/market/atr.py:44-47` | bucle Python por barra | 50 → 4 ms con `njit`, idéntico |
| `core/sqxretest.py:70,86,111,180`, `core/wfmatrix.py:84,97`, `core/store/verify.py:47` | el mismo `.sqx` abierto cuatro y dos veces; `ZipFile` sin cerrar | milisegundos |

Los `default_rng()` sin semilla de `portfolio/common/monteCarlo/simulate/tiles.py:40-49` y
`fan.py:48,67` son **a propósito** («deliberately not reproducible — stability.py measures the
run-to-run spread»): no los siembres, y el de `stitch.worst_path` de §1.6 pregúntalo antes.

**Semillas a un millón de caminos:** `portfolio/common/construct/mc/paths.py:110,137` saca semillas
de `rng.integers(0, 2**32)`: ~116 pares repetidos esperados. `uint64` o `SeedSequence`.

---

## 10 · Que el catálogo de `perf/` mida bien — 🔴 espera a D8

- `perf/measure/runner.py:64` — `tracemalloc` siempre encendido, con el cronómetro dentro: ×1,83 en
  código de objetos pandas, ×0,98 en numpy (MEDIDO). **Todo el catálogo está inflado de forma
  desigual.** `alloc_peak_mb` es columna (`perf/store.py:17`): arreglarlo es decidir si se pierde o
  se mide en pasada aparte, y las cifras viejas dejan de ser comparables.
- `perf/measure/harness.py:20-77` — suma el RSS del árbol: con `fork` cuenta N veces las páginas
  compartidas. Es de donde salen cifras como «1,9 GB por mono» (hoy se miden 0,3-0,6) y «0,9 GB por
  trabajador», que a su vez fijan los techos de §4.4. Medir **PSS** (`/proc/<pid>/smaps_rollup`).
- `perf/measure/scaling.py:12-27` — la primera escritura de páginas entra en el cronómetro (12-13 %).

---

## Descartado

**Por el dueño (2026-10-12) — no se proponen otra vez:**

- **Sustituir el Monte Carlo** por z exacta, convolución o fórmulas cerradas: «no creo que
  sustituir el monte carlo sea opción». Lo exacto queda como oráculo de test (§3.6).
- **Matar SQX antes de que termine de salir:** «solo hará que las estrategias de otros proyectos no
  se guarden».
- **Repartir núcleos a la vez entre Python y SQX** en esta máquina: la regla 19 se queda.

**Refutado en la verificación — no son hallazgos:** lectura fuera de rango en los núcleos `njit`
(`engines/nulls/inputs.py:135-143`: se indexa con numpy fuera de `njit` justo después, lanza
`IndexError`); métrica que desaparece por un NaN (`analysis/metrics.py:76`: 40 cosechas sin un solo
no-finito; latente).

**Medido y no compensa:** proyectos de SQX en tmpfs (el límite es SQX serializando, no el disco, y
un corte de luz con la regla 1 es pérdida real); polars; generador propio (xoshiro); un `prange`
plano en `funded/sim/table.py` (~1 min de un estudio raro); pasadas del control en paralelo.

**Bajado de gravedad:** la «maldición del ganador» de `portfolio/funded/sim/table.py` (rejilla de
3 niveles, caminos compartidos: medir con el test de 100 semillas antes de tocar).

## Decisiones ya tomadas por el dueño (2026-10-13)

- **BLAS a un hilo en el 18.5 (§4.3 bis a): sí**, comprobando ρ, p y veredicto sobre las tres
  madres reales; si algo cambia más allá del último bit, se deshace. **Se deshizo: ver D31.**
- **El conductor (`SQX_w1`, 5060) queda autorizado** para las pruebas en vivo de §6, §7 y §7 bis,
  con un `Test_` que se retira al acabar. Nunca el master ni el custodio.
- **D23 — código muerto: se borra todo**, los tres módulos sueltos **y** `pipeline/run.py`,
  `pipeline/stages/`, `pipeline/verify/` con la línea de la receta, sus tests y sus citas.
- **D17, D18, D20 — se dejan de escribir** el `.html` por estrategia, `marketSurfaces_detalle.json`
  y el JSON de las caídas en los niveles 0 y 1a del gate (su ficha, bajo demanda desde el
  `scorecard`). **D17 y D18 hechos; D20 no, tiene siete lectores: ver D30.**

**Segunda tanda, mismo día:**

- **D24 — el Build para al llenarse el banco: sí.** Es authoring: `python3 -m core.assets
  <SYMBOL>` antes (regla 5), y una corrida de prueba en el conductor que confirme que para solo.
  Corrige después `knowhow/sqx-drive/unselected-build-population.md` («never let it fill»).
- **D27 — un ledger único para leaseWeb y gorilla: sí.** Diseño pendiente (quién escribe, cómo
  viaja); es la condición para repartir celdas entre los dos servidores.
- **D16 — `Results` recortado a las supervivientes tras el paso 8: sí**, «lo que sea más rápido y
  eficiente».
- **El PCG64 dentro del núcleo (§3.9): sí.**
- **Una sesión viva por campaña: no. Patas del 16.5 sin mercados: no** — se quedan como están.
- **D25 — el WFM sigue a M1** (precisión 2). **D26 — MCR 1/4/7 y T1 se siguen calculando.**
- **D28 — manda la regla 6:** el `Test_` se retira al acabar la corrida (skill corregida el
  2026-10-13). Falta que `bin/workflow.sh` lo haga solo al final, con el worker parado, y que
  falle claro si `retire` se niega por supervivientes sin guardar.
- **D22 — la fila del re-juicio se queda** («da igual que aparezca»): `judge.py` firma como hoy.
- **D21 — sólo lo nuevo:** `cell_of` da `…_simple_long` / `…_simple_short` desde el 2026-10-13
  (hecho, con test); lo ya guardado en `…_H1_` no se mueve. Largos y cortos, nunca juntos.

**Tercera tanda, mismo día (todas hechas, con test donde hay lógica):**

- **D29 — fuera**, y regla nueva: «todo código viejo se elimina» (`CLAUDE.md`, regla 21). Borrados
  `sqx/variants/spp.py`, `pipeline/recipe.yaml`, `pipeline/config.yaml` (sin lector) y las claves
  `execute.input/output` y `spp:` de `sqx/variants/config.yaml`; `pipeline/stubs/` se queda
  borrado. `pipeline/ledger/` y `cleanup.py` tienen llamadores vivos: se quedan.
- **D30 — el JSON de las caídas del gate se queda como está.**
- **D31 — BLAS a un hilo en el 18.5: aplicado** (`marketSurfaces/report.py`, siempre, también con
  una sola madre: el resultado ya no depende de cuántas coincidan). El 18.5 lanza hasta 16 madres
  a la vez (`blind.look`): con 30, dos tandas de ~4 s por madre (ESTIMADO, sin medir a esa anchura).
- **D32 — la sesión que no terminó de cargar se mata por PID** (`liveapi.kill`, desde
  `live.start`), nunca con `exitapp`. Sólo ese caso: una sesión GUI que el autopiloto no arrancó
  se sigue rechazando sin tocarla (puede ser de la ventana).
- **D33 — fuera de toda paleta:** `SessionClose`, `VolumeProfileCustomHours` y
  `…MultiSession` entran en `buildcensus.CLOCK_NAMES`; quitadas además las entradas
  `SessionHigh/Low/Open` que seguían escritas (y apagadas) en `ruptura_base`, `sesion_base` y
  `timeRangeBreakout`. El texto de `sesion_base.yaml` aún las describe.

## Decisiones del dueño — pregúntalas (regla 11)

| # | pregunta | lecturas | qué cuesta cada una | respuesta del dueño (2026-10-13) |
|---|---|---|---|---|
| D1 | ¿Se corrige el Drawdown de las uniones del 16.5 (§1.3)? | sí · sí, y se remide lo ya juzgado · no | sube el DD de las variantes que empiezan perdiendo; lo ya juzgado deja de ser comparable | **no se vuelve a medir** |
| D2 | El mono tras el corte por la ruta de población (§4.1): ¿qué raíz y qué panel? | raíz fija por corrida, guardada · la del `config.yaml`; y `nulls.csv` sólo de supervivientes · de toda la población | con sólo supervivientes cambia el «cuántas baten al azar» de `monkeyExcess` | **raíz fija por ejecución guardada (el panel, sin respuesta)** |
| D3 | ¿El control calcula sólo el peldaño juzgado (§2 E)? | sí · no | ÷4 en el 3c del control; tres columnas de `hechos_monos.parquet` vacías; ninguna cifra de `reglas.csv` cambia | **sí** |
| D4 | ¿Se dejan de guardar los sorteos crudos del 3c y de crossTF (§3.1)? | sí (histograma + extremos) · no | sin esto no cabe en RAM a 100.000 con 20.000 estrategias | **sí (que no pete la RAM)** |
| D5 | — retirada: la variante de tabla de §3.2 es bit a bit — | | | — |
| D6 | Las reaperturas (§7.1): ¿no reabrir, guardar antes en paralelo, o las dos pruebas en el conductor y decidir con la cifra? Y ¿se retiran los `Test_` del custodio antes de cada corrida? | A · B · probar ambas · nada | ~1.220 s por corrida en juego; A alarga SPP y WFM (×2 y ×1,44 anotados, por remedir) | **medir A y B en el conductor y quedarse con la mejor (retirar los `Test_` del custodio antes de cada corrida, sin respuesta)** |
| D7 | `portfolio/common/construct/config.yaml` declara 80 GB contra los 20 de la regla 3 | es su presupuesto propio (corre sin SQX) · se baja | — | **80 GB de Python sólo con SQX parado** |
| D8 | `tracemalloc` del catálogo de `perf/` (§10) | sólo con `memtop > 0` · pasada aparte para la memoria · se queda | las cifras viejas dejan de ser comparables | **`tracemalloc` sólo con `memtop`; las cifras viejas fuera** |
| D9 | ¿Media del nulo corregida por variable de control en la escalera (§3.7)? | sí · no | precisión de 1,8 M de sorteos con 100.000; la media informada cambia de definición | **no** |
| D10 | ¿Parada secuencial para los p (§3.7)? | sí, con qué `h` y por cuál de los 5 estadísticos · no | ×126 menos sorteos bajo la nula; histograma y media del nulo con menos sorteos | **no** |
| D11 | ¿El gate juzga por `z_mono` o por `mono_p ≤ α/B` (§3.8)? | z (hoy) · p | medido con operaciones reales: con z el listón es 2-5 % más estricto en largos y 5-6 % más laxo en cortos; hoy los dos dan el mismo veredicto en 30 de 30 | **`z_mono`** |
| D12 | Cambios que mueven el flujo de sorteos sin mover la distribución: `marketProfile` troceado (§4.4), `stageb_null` compilado (§9) | sí · no | los resultados guardados dejan de reproducirse bit a bit | **sí, las dos** |
| D13 | ¿El control de falsos positivos corre en gorilla mientras esta máquina sigue con SQX (§8.6)? | sí, con una puerta nueva para copiar la cosecha y traer el informe · no | hasta 3.330 s menos aquí; `bin/remote.sh` sólo ejecuta y `bin/mirror-data.sh` sólo copia datos de mercado | **no: gorilla es instalación independiente (cae §8.6; D27 sigue por diseñar)** |
| D14 | `entryQuality`: 200 sorteos para un p95 (`config.yaml`, `eratio.draws`) | subir (cuánto) · dejar | cambia la banda | **10.000 sorteos** |
| D19 | feedQuality: ¿sorteo de la alarma con claves `float32` (§4.3 bis c)? | sí · no | 12-15 s de 34; cambia el flujo de sorteos, p dentro del ruido | **no** |
| D15 | ¿96 procesos en `core/fanout.py:13` para los núcleos del mono? | medir a máquina llena y decidir · dejar 48 | +20 % medido a media máquina; una tarjeta midió lo contrario en otro estudio | **más pruebas a máquina entera** |

**Respuestas N1…N14 (2026-10-13).** La pregunta de cada una está en la sesión del dueño; aquí sólo la respuesta:
N1 A · N2 B · N3a B · N3b A · N4 B · N7a A (el ajuste existe) · N7b sí, más una idea nueva (calibrar el
filtro mínimo con datos sintéticos; tres preguntas mías sin responder) · N8a B · N9 A (permiso para las dos
medidas a escala en el custodio parado, avisando antes) · N10a B, y si no está roto A · N10b B · N10c B ·
N10d código y test · N11 A · N12 no se construye salvo «N12 sí» · N13 A (el Objetivo pasa a
`tests/test_perf66_*.py`) · N14 arreglar hasta que pasen los 11; AlgoTrades sigue mientras. Council: no.

**Respuestas posteriores (2026-10-13, sesión en vivo 3):** N7a A · N7b A · N12 B · P1 A · P2 A · P4 A · P7 A · P8 B · P9 A · P10 B · P15-P17 A · Q5 A · Q6 B (numeración de la sesión del dueño). Hechas en la bitácora.

**Preguntas nuevas (2026-10-13):** contestadas: 1 (Q5 A, Q6 B: congelados al archivar), 7 (D16: P1 A, P2 A), 9 (CSCV rechaza bloques impares, P8 B). Abiertas: el alcance de 53 §5c (4), el limbo que no es medoide tras el paso 8 (7), el relleno de miembros archivados (tres preguntas, 1), el defecto de presave, y el resto sin respuesta.

1. Comisión y reloj de un miembro de cartera: ¿congelados al archivar o leídos en vivo de la ficha (hoy)?
2. El gate real 3c ya no guarda los sorteos crudos (`raw=False`, pieza 3.1): ¿vale o se devuelve?
3. 3.9d: ¿se acepta mover el último bit de `rho` y `p_nivel` a cambio de ~4 GB por matriz?
4. `barrier.intrabar` en `config`: ningún código lo lee ya (el encargo 53 §5c lo tiene pendiente de calibrar). ¿Se borra la clave?
5. N7b (tres preguntas), N12, el fixture de 291 KB en el repo y `sample.trades_databank`.
6. `docs/AgentPDFs/criterios-implementados-2026-10-12.md:2297` cita `_per_bar` (borrado). Es fichero de otra sesión: ¿se corrige?
7. D16: ¿el recorte de `Results` se niega sólo si falta guardar algún superviviente o limbo (los rechazados se pierden a propósito)? ¿Y se añade un guardado en el almacén tras el paso 8?
8. `marketProfile` por trozos (D12): ¿se mide la lectura que cambia el flujo de sorteos, o se deja? El null ya hace un sorteo cada vez, así que no hay memoria que acotar.
9. CSCV: ¿se corrige alguna de las cuatro desviaciones (p. ej. rechazar bloques impares)? Cambiaría números guardados.

## Lo que no tocas

- El master (`~/Desktop/SQX`, 5050) y sus proyectos. Los workers, sólo por `bin/sqx-worker.sh` y con
  `.claude/skills/sqx-wait/preflight.sh` antes; el custodio en marcha recibe sólo `action=status`.
- `criteria.yaml`, `ledger/thresholds.yaml` y cualquier umbral: aquí se cambia cuánto tarda un
  número, no cuál es. `oos2` sigue reservado.
- El `raw=True` de `wfc` y `crossmarket/travel` (§3.1). Los techos con razón escrita (§4.4).
- Nada pesado junto a un workflow en marcha (regla 19): los cronometrajes a 48 núcleos, con la
  máquina libre.
- Los ficheros del encargo 65 mientras su bloque C esté abierto: `criteria.yaml`, `gate/level3c.py`
  y `falsePositives/` los toca también; coordina por su tabla de estado antes de editar.

## Objetivo — un comando

```
python3 tools/depmap.py && python3 tools/checks.py && for f in tests/test_perf66_*.py; do PYTHONPATH=. python3 -m pytest -q "$f" || exit 1; done
```

Cubre `tests/test_perf66_*.py`, fichero a fichero (N13 = A, dueño, 2026-10-13); cada frente escribe
el suyo con las pruebas de igualdad que su sección nombra. No se usa `pytest tests`: varios
`test_*.py` son scripts que llaman a `sys.exit` al importarse y tumban la recogida; se corren aparte,
uno a uno. Los frentes 6 y 7 se verifican además a mano en el conductor (plan de §6): eso no cabe en
un comando.

## Cómo cierras

Cada frente: **qué hizo · qué verificó, con la salida pegada · el tiempo antes y después, medido en
la misma máquina · qué dejó sin hacer y por qué · qué descubrió para `knowhow/`.**

El cierre (fila ✓): una corrida entera del workflow y su `fases.csv` contra la tabla de §0; las
tarjetas de `knowhow/perf/` y `knowhow/sqx-format/` que este encargo contradice, reescritas; el
capítulo del manual de `AlgoBank` (regla 8); la lista de ficheros cambiados y **¿Quieres hacer el
commit?**

## Sin verificar

- Casi todo lo medido es con ≤ 4 núcleos y, en §3, con operaciones sintéticas.
- `AlgoBank` no se ha compilado ni ejecutado.
- Nada de §7 se puede probar sin un SQX vivo.
- No se leyeron: `mt5/fleet/`, `sqx/blocks|groups|templates|views|structural/`,
  `portfolio/funded/catalog|deals|live/`, `portfolio/incubation/`, `mcRetest/verdict|contract/`,
  `wfc/calibrate/rehearsal.py`, `ui/daemon/loader|mt5bridge|research/`.

```
/loop Lee docs/encargos/66-performance.md y ejecútalo entero. Tras cada iteración corre el
Objetivo; si sale 0, para el bucle; si no, arregla lo que falló y vuelve a correrlo.
```
