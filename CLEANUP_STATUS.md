# Limpieza 2026-10 — estado

Encargo: `prompt_limpieza_optimizacion_2026-10-04.md` (mapa → revisión de infraestructura → aplicar →
revisión del cálculo → cierre). Se trabaja en `master`, sin ramas y sin commits (regla 12): los commits
los hace el dueño con la lista de ficheros de cada cambio, abajo.

## Tope de consumo

- `~/.claude/statusline.sh` vuelca el JSON de la statusline a `~/.claude/usage.json`
  (copia previa de la configuración: `~/.claude/settings.json.bak-2026-10-04`).
- La extensión de VSCode no ejecuta la statusline, y `claude` no estaba en el PATH (ahora sí:
  `~/.local/bin/claude`, lanzador al binario de la extensión). **Arreglado el 2026-10-04:**
  `~/.claude/usage-refresh.sh` escribe `usage.json` con la misma forma
  (`rate_limits.five_hour|seven_day.used_percentage`) desde una llamada mínima a Haiku. En cada
  checkpoint: ejecutarlo y leer la línea que imprime. Primera lectura (08:04 UTC): 5 h 0 %, 7 d 72 %;
  el semanal se resetea a las 19:00 UTC.

## Ficheros de otras sesiones — no tocar (preguntado el 2026-10-04)

- **UI (algoproject-10):** `ui/daemon/assets.py`, `ui/daemon/assetprior.py`, `ui/daemon/projects/sources.py`,
  `ui/daemon/projects/README.md`, `ui/daemon/projdisk.py`, `ui/desktop/assets.py`, `ui/desktop/assettraits.py`,
  `ui/desktop/workspace/gallery.py`, `ui/desktop/ops/tasks.py`, `ui/desktop/launch.py`,
  `mt5/fleet/app/health.py`, `mt5/fleet/app/chart.py`, `tests/test_fleet_progress.py`,
  `.claude/skills/ui-shot/SKILL.md`, `knowhow/mt5/`, `knowhow/ui/`.
- **Spread (Fixing spread problem):** `sqx/projects/builder.py` (4 líneas en `main()`), `knowhow/costs/`,
  `assets/` entero, `core/assetdata.py`, `core/assetranges.py`, `core/assetwrite/`,
  `sqx/projects/{ranges,perturbations,mcretest,setups,crossmarket}.py`, `studies/data/spread/`;
  `mt5/verify/` y `mt5/live.py` en uso (no cambiar su interfaz). El conductor `SQX_w1` y el terminal MT5
  son suyos hasta ~08:20.
- **algoproject-a1:** nada hoy; si el dueño aprueba su diseño tocará `core/paths.py`, `bin/sqx-worker.sh`,
  `config/machine.example.yaml`, `.claude/skills/sqx-wait/wait.sh` — avisarle antes de cambiarlos.

## Fase 1 — Mapa · HECHA

- `tools/projectmap.py` (nuevo): genera `PROJECT_MAP.md` desde `graphify-out/graph.json`, sin LLM —
  55 módulos, clase INFRA/CALC/MIXED, dependencias e interfaces, puntos calientes (46 ficheros pegados
  al límite de 250 líneas, módulos más acoplados, nombres de función repetidos en 3+ módulos).
- `tools/README.md`: su fila. `python3 tools/checks.py`: 0 problemas.
- Cron: Graphify ya se refresca cada noche (02:20); añadido `25 2 * * 1` (lunes) que regenera
  `PROJECT_MAP.md`. Cuesta 0 tokens; semanal basta porque el mapa sólo orienta.
- Ficheros: `tools/projectmap.py`, `tools/README.md`, `PROJECT_MAP.md`, `CLEANUP_STATUS.md`.

## Fase 2 — Revisión de infraestructura · HECHA

- `INFRA_REVIEW.md`: 76 hallazgos verificados en cuatro grupos — A (22) alto impacto y bajo riesgo, sin
  solape; B (28) limpieza y duplicados; C (16) tocan ficheros de otra sesión; D (10) los decide el dueño.
- Los informes de cada área, con el detalle y las mediciones, están en `scratch/cleanup/*.md` (no en git).
- Tiempos medidos ANTES (base para la Fase 3): Datos 7,2 s por visita (7,7 s con la ventana congelada);
  Activos 7,1 s la primera vez y 3,0 s después; abrir un proyecto 1,4-2,6 s (`panels`) + 0,55-1,7 s
  (`funnel`); arranque `Shell()` 0,98 s, de ellos 0,55 s de HTTP en el hilo de la GUI.
- La lista de «funciones muertas» del grafo resultó un 89 % falsos positivos (rutas FastAPI, callbacks):
  se quitó de `PROJECT_MAP.md`; el código muerto real está en el grupo B.
- Ningún fichero de código cambiado en esta fase.

## Fases 3, 4 y 5 · HECHAS (2026-10-04)

Resultado, mediciones, riesgos y recomendaciones: `CLEANUP_REPORT.md`. Revisiones: `scratch/cleanup/review-{infra,calc,final}.md`.
Último consumo leído: 5 h 57 %, 7 d 80 %.

- Fase 3: grupo A entero; B salvo B6, B8, B12; del C sólo C1, C8, C9, C11, C12, C15; del D: D1-D4, D6, D9.
- Fase 4: `CALC_REVIEW.md` (48 hallazgos) y, por «Arregla TODO», 42 arreglados con test.
- Fase 5: suite 168 ejecutados / 153 bien / 3 fallan / 12 apartados; `checks.py` 0 problemas; `uiwalk` 17 zonas, 0 excepciones.

## Lo que queda

1. Recalcular los resultados guardados que quedaron viejos (tabla del §4 del informe); 27 ingestas de MC Retest.
2. Grupo C restante, cuando cierre la sesión del spread (`core/assetyaml.py`, `core/paths.py`, `sqx/projects/builder.py`).
3. Operación arrastrada de fondeo: contabilidad exacta dentro de los recorridos (`portfolio/EXECUTION.md` §D).
4. Decisiones del dueño: `min_days` de 44 planes candidatos; texto de `ledger/thresholds.yaml:63`; botón «Recargar» en Datos; D7, D10.
5. Del cálculo sólo queda m30 (spread: de la otra sesión, el dueño dijo no tocar). m29 y m33-m36 hechos; sus tres preguntas, en `CLEANUP_REPORT.md` §7 bis.

Cómo retomar: `~/.claude/usage-refresh.sh` (parar si 7 d ≥ 95 % o 5 h ≥ 90 %), `ListAgents` para saber qué
ficheros tiene cada sesión, y seguir por la lista de arriba.

## Ficheros para el commit

El árbol lo comparten otras sesiones: en `ui/`, `sqx/projects/`, `tests/README.md`, `docs/DEPENDENCIES.md` y
`knowhow/*/INDEX.md` hay cambios suyos mezclados en los mismos ficheros — revisar con `git add -p`.

- **Informes y mapa:** `PROJECT_MAP.md` `INFRA_REVIEW.md` `CALC_REVIEW.md` `CLEANUP_REPORT.md` `CLEANUP_STATUS.md`
  `tools/projectmap.py` `tools/README.md` `tools/layering.py` `docs/DEPENDENCIES.md` `requirements.txt` `bin/audit-prune.sh`
- **core:** `core/{worker,symbols,exportdrv,buildfilters,fleetpaths,commission,sqxstats,tradestore,wfmatrix}.py`
  `core/surface/{plateau,dedupe}.py` `core/archive/{cli.py,README.md}` y el borrado de `core/archive/{view,write}.py`
- **sqx:** `sqx/variants/{execute,spp,curves}.py` `sqx/variants/config.yaml` `sqx/projects/{stage,cfxio,retire,sweep}.py`
  y los sitios de `cfxio.members()` en `sqx/projects/` y `sqx/inspect/` · `sqx/data/update.py`
  `sqx/inspect/keep_tasks.py` `sqx/curate/apply_verdict.py`
- **mt5:** `mt5/server.py` `mt5/newsfilter/reading.py` `mt5/reconcile/sqxside.py`
- **pipeline, perf:** `pipeline/stages/recipe.py` `pipeline/autopilot/judge.py` `pipeline/verify/fixture.py`
  `perf/inputs/config.py` `perf/store.py`
- **ui (demonio):** `ui/daemon/data/catalogue.py` `ui/daemon/{palettes,assetapi,projdisk}.py` `ui/daemon/sqxconfig/sections.py`
  `ui/daemon/databank/{metrics,cells}.py` `ui/daemon/strategy/{api,archive_view,archive_write}.py` y las rutas
  quitadas en `ui/daemon/{filters,assets}` · `ui/daemon/{launch,advance}/preflight.py` `ui/daemon/launch/run.py`
- **ui (ventana):** `ui/desktop/{shell,coverage,assets,assetpage,jobsfeed,theme}.py` `ui/desktop/datazone/zone.py`
  `ui/desktop/sqxconfig/zone.py` `ui/desktop/ops/jobsbar.py` `ui/desktop/portfolios/imported.py`
  `ui/desktop/mt5bridge/forceclose.py` `ui/text/numbers.py`
  `ui/desktop/workspace/{funnel,ficha,fichajobs,fichastats,fichacurves,columnsview,filters,filterrow,gallery,rail,railrun,railwatch,railwords}.py`
- **engines, ledger:** `engines/inference/{fdr,excess}.py` `engines/nulls/{verdict,stats,kernel,model}.py`
  `engines/nulls/placement/kernel.py` `engines/regimes/regime.py` `engines/README.md` `engines/nulls/README.md`
  `ledger/{record,report}.py` `ledger/README.md`
- **studies:** `studies/screening/{analysis/decay.py,gate/{monkey,inputs,report,measures}.py,snoopingScreen/measure.py,isOos/many.py,filters/report.py}`
  `studies/closing/{exposure/{one,occupancy,benchmark,compare}.py,blindJoint/measure.py}`
  `studies/readings/{edgeCost/{spread_share,one}.py,entryQuality/inputs.py,conditionalMap/regime.py}`
  `studies/breakage/mcRetest/{run.py,model/{recon,drawdown}.py,measure/{originals,store}.py,verdict/{scoring,gates,fragility}.py}`
  `studies/breakage/spp/{run,report,contract}.py` `studies/breakage/spp/model/{combine,profile}.py` `studies/breakage/spp/verdict/{noise.py,README.md}`
  `studies/optimisation/{cloud/{contract.py,measure/stability.py,model/surrogate.py,verdict/call.py},marketSurfaces/verdict/call.py,wfc/measure/correlation.py,wfm/measure/{equity,correlation}.py}`
  `studies/transfer/{crossmarket/{simulate/metrics.py,verdict/breadth.py},crossTF/{cells,verdict}.py}`
- **portfolio:** `portfolio/funded/rules/{floors,machine,catalog}.py` `portfolio/funded/sim/{kernel,account}.py`
  `portfolio/common/construct/{mc/judge.py,search/genetic.py,equity/excursions.py}`
  `portfolio/common/monteCarlo/{model/stress.py,simulate/{kernel,metrics}.py}` `portfolio/EXECUTION.md`
- **tests:** `tests/README.md` `tests/test_{deadlines,mt5_server_exit,calc_engines,exposure,entry_location,mcretest_psr,mcretest_edges,spp_noise,spp_sharpe,cloud_underdetermined,optimisation_calc,crossmarket_calc,portfolio_fixes,isoos_constant_column}.py` (nuevos)
  `tests/test_{sqx_bridge,worker_lock,archive,edgecost,gate_measures,blindjoint,crosstf_facts,funded_bank}.py` (cambiados)
- **knowhow:** `knowhow/eng/{graphify-cannot-list-dead-code,tests-are-scripts-run-via-audit-tests,vscode-has-no-statusline-usage-json}.md`
  `knowhow/research/{regime-atr-is-lagged-one-day,spp-noise-gate-centred-no-floor,fdr-raises-on-nan-p,gate-t-scales}.md`
  `knowhow/perf/window-waits-off-gui-thread.md` `knowhow/sqx-format/{result-sections,metric-formulas}.md`
  `knowhow/locations/report-csv-conventions.md` `knowhow/authoring/project-skill.md` `knowhow/{eng,research}/INDEX.md`
- **Tanda m29, m33-m36:** `studies/screening/analysis/{improvement,replication}.py` `studies/screening/analysis/README.md`
  `studies/screening/filters/report.py` `studies/screening/replication/report.py` `portfolio/funded/rules/{catalog,machine}.py`
  `portfolio/funded/rules/README.md` `portfolio/funded/sim/haircut.py` `portfolio/common/construct/{funded,funded_b,universe}.py`
  `portfolio/common/construct/README.md` `portfolio/common/construct/equity/{matrix.py,README.md}`
  `portfolio/common/construct/search/stageb_run.py` `portfolio/common/construct/verdict/decide.py`
  `portfolio/common/monteCarlo/{verdict/scoring.py,simulate/family_d.py}` `tests/test_{filter_sweep,portfolio_fixes_latent}.py`
  `knowhow/research/stageb-selector-p-reads-high.md` `docs/manual/{05-cribado-oos,11-cartera}.pdf`
- **Fuera del repo:** `AlgoData/manual-fuentes/{02-filtros,87-cartera-etapa-b-y-veredicto}.md`, crontab (mapa semanal; aviso de `archive_logs`), `~/.claude/statusline.sh`, `~/.claude/settings.json`,
  `AlgoData/manual-fuentes/PENDIENTE.md` (una línea quitada).
