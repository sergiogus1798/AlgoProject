# 77 — Sacar el motor de `ui/daemon`: la orquestación de SQX a `sqx/` y `pipeline/`

## Estado (plan vivo: cada sesión actualiza su fila y la bitácora)

| paso | mueve | ficheros (aprox.) | estado | commit |
|---|---|---|---|---|
| 1 | `workerguard` → `sqx/worker/guard.py`; `advance/sqxlog` → `sqx/log.py`; `loader/fingerprint` → `sqx/databank/fingerprint.py`; además `daylog` → `sqx/daylog.py` (lo pedía `sqx/log.py`) | ~13 | hecho 2026-10-17 | `9c019fc` |
| 2 | `jobs` → `sqx/jobs.py` (no `core/`: su cancelación para el worker con `winddown`); `progress`, `tasklog`, `projdisk`, `proof` → `sqx/`; `winddown` → `sqx/worker/`; `diskmemo` se queda (huella de las fuentes del demonio) | ~45 | hecho 2026-10-17 | `b83304f` |
| 3 | `loader/find`, `loader/state` → `sqx/databank/`; `advance/preflight` → `sqx/worker/`; la hoja `filters/discards` → `sqx/databank/`; `diskmemo` → `core/` con la huella del código como argumento | ~50 | hecho 2026-10-17 | `c65901e` |
| 4 | `launch/steps` → `sqx/workflow/launchsteps.py`; `workflow/steps`+`sources` y la hoja `records` → `sqx/workflow/` (va antes que el 3: `preflight` los importa) | ~30 | hecho 2026-10-17 | `6ca743a` |
| 5 | `launch/*` y `advance/run`+`buildcap` → `sqx/run/`; `chainplan` se funde en el plan del autopiloto | ~25 | pendiente | |
| 6 | `runner/where` → `studies/run/where.py` (`table` se queda: importa `ui.daemon.runs` y los cuatro `runner/*` de estudios, que no son hojas) | ~20 | parcial 2026-10-17: `where` hecho, `table` pendiente | `486b7e0` |
| 7 | `mt5bridge/runs` → `mt5/verify/`; fuera los `ui → mt5.*` directos | ~6 | hecho 2026-10-17 (más `display` y `strategy/locate`) | `1bea5bc` |
| 8 | `strategy/archive_write` → `core/archive/`; `pipeline.ledger.state.work_dir` → `core`; el escritor de `criteria` | ~10 | parcial 2026-10-17: `work_dir` y el escritor de `criteria` hechos; `archive_write` se queda por decisión del dueño (2026-10-17, A) | `d0c38c1` |
| 9 | `sqxconfig/{write,studywrite,sections,options}` y `projects/sources` → `sqx/projects/`; el lector de campaña → `pipeline/campaign/` | ~25 | hecho 2026-10-17: `projects/sources` movido; `sqxconfig` y el lector de campaña se quedan por decisión del dueño (B) | `bf1db89` |
| 10 | Sueltos: `engines/variants/excess` (mover `tradelevel`), `core/archive/manifest` → `ledger/`, `ui/desktop/launch` | ~8 | hecho 2026-10-17 | `9a95bf7` |
| — | `ALLOW` vacío; `ui.daemon` en `MAY_IMPORT` sin excepciones | — | pendiente | |

**Bitácora:** (cada sesión añade una línea: fecha, paso, qué pasó)

- 2026-10-17, paso 1 (algoproject-df): movidos los tres más `daylog`, que `sqx/log.py` necesitaba para no importar `ui.daemon.progress`; fuera la fila `ALLOW` de `pipeline/autopilot/closing.py`, que ya no se usaba.
- 2026-10-17, paso 2 (algoproject-df): `jobs` a `sqx/` y no a `core/`, porque `core` no puede importar `sqx.worker.winddown`; en `ui/daemon/portfolios/` (congelada) sólo cambian la línea de import y su README.
- 2026-10-17, paso 3 parado sin tocar nada: `find` → `diskmemo` → `ui.daemon.version` y `preflight` → `launch/steps` y `workflow/steps`. Se hace el 4 primero; `diskmemo` va a `core/` y cada llamador le pasa su huella (`find` sólo la de `core/sqxfile.py`).
- 2026-10-17, paso 4 (algoproject-df): `launch/steps` se llama `launchsteps.py` en `sqx/workflow/` porque ya hay un `steps.py`; fuera las filas `ALLOW` de `perf/inputs/workloads.py` y `pipeline/autopilot/facts.py`.
- 2026-10-17, paso 3 (algoproject-df): la memoria `identities` ya no lleva la huella del demonio, sólo la de `core/sqxfile.py`: se recalcula una vez y el pkl viejo se borra. Fuera la fila `ALLOW` de `pipeline/autopilot/judge.py` (quedan 15).
- 2026-10-17, decisión del dueño sobre el paso 8 («tus recomendaciones», opción A): `archive_write` se queda en `ui/daemon/strategy/` (arma el archivo con las vistas de la ventana) y la fila `ALLOW` de `core/archive/cli.py` → `ui.daemon` queda **aceptada**: el comando `python3 -m core.archive archive` del manual no cambia. El objetivo «`ALLOW` vacío» del final excluye esa fila.
- 2026-10-17, decisión del dueño sobre el paso 9 (B): `sqxconfig` se queda en `ui/daemon` — es el editor de ajustes de la ventana (escribe los YAML de estudios y activos con su esquema), no un segundo escritor de `project.cfx`. El esquema no se comparte con `sqx/projects` mientras no se vea un ajuste que llegue mal a SQX; entonces se abre un encargo. El lector de campaña sigue en `ui/daemon/campaign/shelf.py` (lee `archive/shelf` y `results/catalogue`).
- 2026-10-17, paso 7 (algoproject-df): `runs` y su hoja `display` a `mt5/verify/`; `strategy/locate` (hoja de `core`+`sqx`) a `sqx/databank/locate.py` porque `runs` lo importaba. Fuera la fila `ALLOW` de `mt5/verify/autopilot.py` (`layering_allow` 13). Quedan `mt5/verify/{run,sqxside}.py` y `mt5/reconcile/sqxside.py` -> `ui.daemon.launch.run`/`advance.run` (paso 5). Los `ui → mt5.*` (`mt5bridge/api.py`, `archive/shelf.py`) no están marcados por `layering.py` (`ui` no está en `MAY_IMPORT`) y no se tocan: son rutas que llaman a la lógica.
- 2026-10-17, paso 8 (algoproject-df): `work_dir` a `core/datapaths.py` (con `safe` en línea, que sólo usaba él; fuera de `state.py`). `criteria/write` a `pipeline/autopilot/criteria_write.py`, junto a su lector, y con él las hojas `FILES`, `plain` y `sha` que `read.py` ahora importa de allí (`pipeline` no puede importar `ui`); la ruta sigue en `ui/daemon/criteria/api.py`. `criteria.yaml` intacto (sha 7d347e58). **`archive_write` parado:** importa `sqx.databank.find`, `sqx.inspect.feeds` y `ui.daemon.strategy.archive_view`, y `core` sólo puede importar `core`; necesita decidir dónde vive (¿`sqx/databank/`?, y `archive_view` que lo acompañe) antes de moverlo. Sigue la fila `ALLOW` de `core/archive/cli.py` (`layering_allow` 13).
- 2026-10-17, paso 9 (algoproject-df): `projects/sources` a `sqx/projects/sources.py` (sin colisión), y con él `guess_asset`, hoja de `runs` que `sources` necesitaba (`runs` importa `ui.daemon.runner`); los cuatro llamadores de `guess_asset` importan ya de `sqx.projects.sources`. **Parados:** `sqxconfig/{write,studywrite,sections}` dependen de `sqxconfig/studies` (343 líneas), que importa seis `studies/*/tooltips` y `studies.screening.analysis.tradelevel`, y `sqx` sólo puede importar `core`; `options` (con `lists`) saldría solo, pero nadie de fuera lo necesita y `ranges` chocaría con `sqx/projects/ranges.py`. El lector de campaña (`ui/daemon/campaign/shelf.py`) importa `ui.daemon.archive.shelf` y `ui.daemon.results.catalogue`, que a su vez cuelgan de `ui.daemon.runner.table` y `mt5.verify.pool`: no son hojas de la campaña, y `pipeline/campaign/shelf.py` ya existe (otra cosa: archiva las finalistas). Decidir dónde vive `studies` (¿`studies/` con su propia carpeta de configuración?) antes de retomar. Ninguna fila `ALLOW` quedó sin uso (`layering_allow` sigue en 13).
- 2026-10-17, paso 10 (algoproject-df): `tradelevel` entero a `engines/market/tradelevel.py` (hoja: sólo importa `engines.market.calibrate`); de `core/archive/manifest` sólo `ledger()` y su `Ledger` pasan a `ledger/archived.py` — el resto se queda en `core` porque `core/store/save.py` usa `registry` y `asset` y mover todo le daría un `core → ledger` nuevo; `ui/daemon/version` desaparece: `core.diskmemo.code_fingerprint(core.paths.UI_DAEMON)` lo calculan la ventana y el demonio por igual. Fuera 3 filas `ALLOW` (`layering_allow` 13 → 10).
- 2026-10-17, paso 5a (algoproject-df): `assets`, `graceful`, `say`, `ready`, `syncing`, `watch`, `POLL`/`READY_TRIES`/`START_WITHIN` y `buildcap` (tope de minutos del build) a `sqx/worker/session.py`; `snapshot`, `compare`, `restore`, `INTERRUPTED` y `SNAPSHOTS` a `sqx/projdisk.py`. Los duplicados eran idénticos salvo `graceful`, que `advance/run` escribía como lambda (mismo efecto): ahora usa el de `session`. `MAX_HOURS` sólo en `core.worker`. Fuera las filas `ALLOW` de `mt5/verify/{run,sqxside}.py`, `mt5/reconcile/sqxside.py` y `pipeline/autopilot/neighbours.py` (`layering_allow` 10 → 6).
- 2026-10-17, paso 5b (algoproject-df): `session.run(role, project, ...)` es el bucle único (refuse_if_up, start, mark, ready, mark del log, `action=start`, watch, y stop + stopped en un `finally`); `advance.advance`, `launch.execute` y `mt5/verify/sqxside.run` lo llaman y conservan sus extras mediante ganchos (`session.Hooks`: `before`, `between`, `launched`, `after`, `phase`, `export`). Diferencias que el bucle expresa sin cambiar a nadie: el mensaje de «no se paró» (`ending`), el stop sin export de mt5 y los `PROGRESS` de cada uno. Único cambio: la segunda `refuse_if_up` de launch ahora es la del bucle (misma posición, tras `say(15)`); `sqx/variants/execute.py` sin tocar.
- 2026-10-17, paso 5c (algoproject-df): `chainplan` a `sqx/workflow/chainplan.py` (sólo importaba `sqx.workflow`); importadores actualizados (`pipeline/autopilot/plan.py`, `ui/daemon/workflow/api.py`, `ui/daemon/launch/chaincheck.py`, cuatro tests) y sus README. Fuera la fila `ALLOW` de `pipeline/autopilot/plan.py` (`layering_allow` 6 → 5).
- 2026-10-17, paso 5d (algoproject-df): `command` y `CHILDREN` de `chain` a `core/proc.py` (`command(argv, tail=4)`: el `TAIL` de `chain` pasa a ser su parámetro; usa `core.paths.ROOT`, no sólo la biblioteca estándar). **`cancelled` se queda en `chain.py`**: pone `_RUNNING["stop"]` (estado de la cadena) y llama a `sqx.worker.session.graceful`, así que no cabe en `core`; ahora mata `proc.CHILDREN`. `launch/preflight` a `sqx/workflow/launchcheck.py` (hay un `sqx/worker/preflight.py`), `launch/configure` a `launchconfigure.py` (hay un `sqx/projects/configure.py`) y `advance/confirm` a `confirm.py`; sólo importaban `core`/`sqx`. Fuera la fila `ALLOW` de `pipeline/autopilot/blind.py` (`layering_allow` 5 → 4); quedan `core/archive/cli.py`, `pipeline/autopilot/call.py`, `pipeline/autopilot/run.py` y la de `.claude/skills`.

## Tu oficio

Eres el **orquestador, en Opus**: decides los cortes de los ficheros mezclados y el orden dentro de
cada paso. Cada paso lo escribe **un** subagente `general-purpose` con `model: "sonnet"`; los pasos
van **de uno en uno** (cada uno depende del anterior: dentro de `ui/daemon` las carpetas se importan
en círculo, así que primero salen las hojas).

## Tu encargo

Que `ui/daemon` sea lo que dice ser: **rutas HTTP que llaman a la lógica, no la lógica**. Hoy son
27.000 líneas con la orquestación de SQX dentro, y `pipeline/autopilot` (18 imports) y `mt5/verify`
(5) la importan al revés. Devuelves al dueño la lista de excepciones de capas vacía y un solo workflow
donde hoy hay cuatro.

## §0 De dónde sale

Revisión estructural del 2026-10-16, hallazgos `arch-ui-daemon-engine`, `arch-workflow-four`,
`arch-project-config-two`. El mapa de arriba lo sacó el subagente de arquitectura ese día leyendo los
imports; compruébalo con `graphify affected "<símbolo>"` antes de cada paso. Decisión del dueño
(2026-10-16): **10 pasos pequeños, cada uno con su commit**.

## Cómo es cada paso

1. **Antes:** `git status --short <ficheros del paso>`. Si otra sesión tiene cambios sin commitear en
   alguno, **no empieces ese paso**: apúntalo en la bitácora y espera.
2. `git mv` del fichero, y en el mismo paso **todos** sus llamadores actualizados (`grep -rn
   "<módulo viejo>"` en `.py`, `bin/`, `.claude/`, README, `knowhow/`, capítulos del manual). Sin
   reexportaciones ni alias en el sitio viejo (regla 21).
3. En un fichero mezclado (tiene un `APIRouter` y lógica), la ruta se queda en `ui/daemon` y llama a
   la lógica movida.
4. Las filas de `tools/layering.py` `ALLOW` que el paso deja sin uso **se borran**.
5. Pasa el objetivo del paso (abajo), deja la lista de ficheros y **¿Quieres hacer el commit?**.
   Hasta que el dueño diga sí y esté empujado, no se empieza el siguiente.

## El paso 5, aparte

El workflow está en cuatro sitios: `pipeline/autopilot/run.py`, `ui/daemon/launch/chain.py` +
`chainplan.py` (el «Correr workflow» de la ventana, que para en cada decisión),
`pipeline/autopilot/plan.py` («la cadena de la ventana sin sus paradas») y `bin/workflow.sh`. El
canónico es el autopiloto. `chainplan` pasa a ser su plan con un `stop_at_judging`, y el bucle
«arranca SQX, espera, para» de `advance/run`, `launch/run` y `liverun` queda en uno. Comprueba con
`bin/workflow-test.sh` (sin otra cosa pesada al lado, regla 19) que la cadena entera sigue pasando.

## Decisiones del dueño — pregúntalas (regla 11)

- Si un corte cambia lo que hace un botón de la ventana, no solo dónde vive el código.
- `ui/daemon/portfolios` (2.698 líneas) está en `portfolio/`, congelada: queda fuera hasta que la
  reabra.

## Lo que no tocas

El master; `portfolio/` y `ui/daemon/portfolios`; ficheros con cambios sin commitear de otra sesión;
los ficheros de `75` y `76` mientras estén abiertos (si `75` tiene a medias `ui/daemon/databank/`,
el paso 3 espera).

## Objetivo — un comando

Por paso: `python3 tools/depmap.py && python3 tools/checks.py && python3 -m pytest tests -q -x`
(sin SQX corriendo). Al final del encargo, además:

```bash
python3 -c 'import sys; sys.path.insert(0, "tools"); import layering as l; sys.exit(len(l.ALLOW))' && \
python3 tools/depmap.py && python3 tools/checks.py && python3 -m pytest tests -q -x
```

## Cómo cierras

Por paso y al final: qué hizo · qué verificó, con la salida pegada · qué dejó y por qué · qué
descubrió para `knowhow/`. `graphify update . && python3 tools/projectmap.py` en **cada** paso
(regla 22): el mapa cambia en todos. Actualiza `ui/daemon/README.md`, `sqx/README.md` y
`docs/MAPA-DE-CARPETAS.md` con lo que se movió. La lista de ficheros cambiados y **¿Quieres hacer el
commit?**

/loop Lee docs/encargos/77-sacar-el-motor-de-ui-daemon.md y ejecuta el siguiente paso pendiente de su tabla. Tras él corre el Objetivo del paso; si sale 0, para y pregunta por el commit; si no, arregla lo que falló y vuelve a correrlo.
