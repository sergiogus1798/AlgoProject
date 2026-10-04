# Limpieza 2026-10-04 — informe de cierre

Encargo: `prompt_limpieza_optimizacion_2026-10-04.md`. Todo está en `master`, **sin commit** (regla 12):
la lista de ficheros está al final. El detalle de cada hallazgo vive en `INFRA_REVIEW.md` (76) y
`CALC_REVIEW.md` (48); los informes por área y las tres revisiones, en `scratch/cleanup/` (fuera de git).

## 1. Qué se hizo

| fase | resultado |
|---|---|
| 1 Mapa | `tools/projectmap.py` genera `PROJECT_MAP.md` desde el grafo de Graphify, sin LLM (0 tokens); cron los lunes 02:25 |
| 2 Revisión de infraestructura | 76 hallazgos verificados: A 22 · B 28 · C 16 (ficheros de otra sesión) · D 10 (decisión tuya) |
| 3 Arreglos de infraestructura | grupo A entero; grupo B salvo cuatro filas; del C y el D, lo que no pisaba a otra sesión |
| 4 Revisión del cálculo | 48 hallazgos (3 críticos, 9 mayores, 36 menores); por tu «Arregla TODO», 47 arreglados con test (falta m30, del spread) |
| 5 Cierre | tres revisiones Opus (infraestructura, cálculo, transversal final); lo que pidieron cambiar está aplicado |

## 2. Tiempos de carga, antes y después

| qué | antes | después |
|---|---|---|
| Datos: ventana congelada al entrar | 7,7 s | 0,002 s (el catálogo se pide en segundo plano; 5,4 s en frío, 0,045 s en caché de 5 min) |
| Activos: abrir la zona | 3,0 s (7,1 s la primera vez) | 0,37 s (cada página se lee al entrar en pantalla) |
| Activos: primera ficha (`/api/asset/AUDJPY`) | 2,5 s | 0,9 s |
| Proyectos: `/api/databank/panels` | 1,5 s · 1,4 s | 0,75 s · 0,38 s |
| Proyectos: `/api/databank/funnel` (1.ª lectura) | 0,52 s | 0,25 s |
| Arranque `Shell()` | 0,98 s | 0,21 s |
| Paletas (2.ª llamada) | 0,96 s | 0,06 s |
| Configuración SQX (2.ª llamada) | 0,53 s | 0,007 s |
| `core.symbols.alias()` | 385 µs | 3,3 µs |
| Métricas de variantes (120 `.sqx` reales) | 1,04 s | 0,72 s, 0 diferencias |

El catálogo de rendimiento (`perf.catalogue`) no se volvió a correr: `--only montecarlo.analyse` revienta
en este árbol y no lo investigué.

## 3. Conexión con SQX: lo que era frágil

- `core.worker.wait_ready` esperaba sin fin; ahora se rinde a los 30 min.
- `execute.synced` seguía adelante con una sincronización corta; ahora se para.
- Las exportaciones no tenían plazo; ahora 120 s (símbolos) y 6 h (operaciones).
- `spp.py` no paraba el worker si fallaba a mitad; ahora sí.
- El servidor MCP de MT5 moría con un `SystemExit` de cualquier herramienta; ahora devuelve el error.
- El plazo de las lecturas de noticias en MT5 era de 60 min también con ticks reales; ahora 240 min.
- Un `project.cfx` ilegible ya no se retira nunca.
- La línea de cron de `archive_logs` avisa en el escritorio si falla. Las demás líneas siguen sin aviso.

## 4. Cálculo: lo que cambia en los números

Cada arreglo lleva su test con tolerancia explícita (`tests/test_calc_engines.py`, `test_portfolio_fixes.py`,
`test_mcretest_*.py`, `test_spp_*.py`, `test_cloud_underdetermined.py`, `test_optimisation_calc.py`,
`test_crossmarket_calc.py`, `test_exposure.py`, `test_entry_location.py`, `test_isoos_constant_column.py`).

- **MC Retest:** el PSR se calculaba sin las operaciones reales; el veto ahora dispara (PSR 0,44 en el caso
  de prueba). El drawdown de una simulación vacía ya no hereda el de la siguiente.
- **SPP:** el ruido compara (máximo − media) con σ·√(2 ln N), como elegiste, sin suelo de operaciones. El
  Sharpe combinado da 1,156 contra 1,150 de SQX.
- **Benjamini-Hochberg:** un p-valor NaN ya no pasa en silencio: el motor se para y los estudios filtran
  esas filas antes y las conservan en la tabla.
- **Régimen ATR:** va desfasado un día (el día D usa el ATR al cierre de D−1), sin mirar el futuro.
- **Fondeo:** suelos diario y de arrastre, y la operación arrastrada entre etapas, corregidos en los cinco
  recorridos, que coinciden en 1.500 tablas aleatorias.
- **Sharpe:** se queda en √252, la convención de SQX. Probé a cambiarlo y lo revertí.
- **Factor 10 en spreads:** no encontrado. Las unidades son `tick_size` de principio a fin (AUDJPY: 1,61
  puntos × 0,01 + deslizamiento = 0,0240, medido). `studies/data/feedQuality` y `studies/data/spread` no
  se leyeron línea a línea.

**Resultados guardados que quedan viejos** (hay que recalcularlos para fiarse de ellos):

| paso | qué | cuánto cambia |
|---|---|---|
| cribado OOS (gate, monkey) | drawdown y p-valores | sin medir |
| MC Retest | 27 ingestas sin columna `pnl`: repetir `python3 -m studies.breakage.mcRetest.ingest --project <P>` | el estudio se para y lo pide |
| SPP | unas 14 de 41 pasan a «ruido» | medido |
| nube de optimización | 9 de 12 pasan a `sin_dato` | medido |
| otros mercados y timeframes | amplitud y veredictos | sin medir |
| edgeCost, exposición | cuota de spread, ocupación | sin medir |
| fondeo y cartera | P(pasar) y valor esperado donde una etapa empieza con operación abierta | sin medir |

## 5. Código quitado

- Código muerto: `tradestore.frame/names`, `wfmatrix.axes`, `mc_ranges`, `exportdrv.metrics/prepare_view`,
  `keep_tasks.main`, `theme.state_colour`, `launch/run.counts`, tres rutas del demonio sin cliente
  (`/filters/metrics`, `/strategy/archived`, `/assets/shared/{name}`), cuatro claves de configuración.
- Duplicados unificados: `cfxio.members()` (17 sitios), `worker.listening()` e `installs()`, `theme.clear`
  (cuatro copias), seis parejas hilo+señal → `background.run`, un solo sondeo de trabajos para cinco widgets.
- `core/archive/view.py` y `write.py` pasan a `ui/daemon/strategy/` (una excepción de capas menos).
- En `core/` el saldo es −345 / +81 líneas. No doy una cifra global: el árbol lo comparten otras sesiones
  y `git diff` mezcla su trabajo con este.

## 6. Tests

Suite completa (`tools/audit_tests.py`): **168 ejecutados, 153 bien, 3 fallan, 12 apartados** (anoche: 146 /
132 / 2 / 12). Hay 22 ficheros de test nuevos.

- Los 3 que fallan: `test_ui_blocks.py` y `test_ui_results.py` agotan los 300 s (ya lo hacían);
  `test_crosstf_report.py` falló una vez dentro de la suite y pasa 3 de 3 solo.
- `test_ui_shell.py` falla 1 de cada 3 veces por un YAML que otra sesión está reescribiendo.
- `test_ui_columns.py` y `test_ui_strategy.py` siguen apartados desde el 02-10: no son de esta limpieza.
- `tools/checks.py`: 0 problemas. `tools/uiwalk.py`: 17 zonas, 0 excepciones.

## 7. Riesgos y pendientes

1. **Operación arrastrada en fondeo, límite conocido.** La marca arrastrada sale del balance el primer día
   que cierra sin posiciones. Si una cartera no cierra plana nunca, una ganancia arrastrada de 3.000 sigue
   contando para el objetivo, igual que antes del arreglo. En la única estrategia medida el 85 % de los
   días cierra plano. La contabilidad exacta necesita los tramos de cada operación dentro de los recorridos
   (`portfolio/EXECUTION.md` §D).
2. **`min_days` vacío en 44 planes** de firmas candidatas (FundedNext, FundingPips): falta el dato del
   catálogo; no se rellena con 0.
3. **`ledger/thresholds.yaml:63`:** el `why` dice «familia superviviente» y Benjamini-Hochberg corre ya
   sobre toda la familia probada. El Ledger está sellado: no lo toqué.
4. **Datos puede ir hasta 5 min atrasado** y no tiene botón «Recargar».
5. **Sin arreglar del cálculo:** sólo m30 (dos cuentas de «puntos» del spread y el 1,25 en el rango del MC
   Retest): es de la sesión del spread y no se toca. Ver §7 bis para m29 y m33-m36.
6. **Sin arreglar de infraestructura:** B6, B8, B12, C10, C14, D7, D10 y el resto del grupo C, que toca
   ficheros de la sesión del spread (`core/assetyaml.py`, `core/paths.py`, `sqx/projects/builder.py`…).

## 7 bis. Los cinco menores cerrados después (m29, m33-m36)

Tests: `tests/test_filter_sweep.py` (4) y `tests/test_portfolio_fixes_latent.py` (7); fallaban antes, pasan ahora.

- **m29, barrido de filtros.** Con 2.000 remuestreos el p no bajaba de 1/2000 y Benjamini-Hochberg pedía
  0,05/210 para el primero: un único filtro fuerte no podía nombrarse nunca. Ahora el filtro que no cruza
  el cero se vuelve a sortear hasta 6.000. Coste en un barrido real: 1,3-2,4 s → 2,3 s. `best_filters` de
  la replicación reutiliza el suelo del barrido (200 supervivientes). Manual: `05-cribado-oos.pdf`.
- **m33, plazo de una etapa.** Estaba en días naturales y se comparaba con días de mercado (30 días se
  simulaban como 40). Latente: hoy ninguna etapa del catálogo tiene plazo. Convertido; la primera firma
  con plazo parará la construcción con un error hasta que se le diga cuántos días de mercado tiene el año.
- **m34, meses que cruzan el fin del build.** Latente (todo build acaba en fin de año). Los meses se suman
  ya desde los días del build; con un build que acabe el día 15 la correlación pasaba de +0,17 a +0,9998.
- **m35, P(aprobar) de la etapa B.** Leía alto cuando las finalistas se parecen: +0,0245 ± 0,0012. Ahora se
  informa la cifra recalculada en caminos nuevos (sesgo +0,0019 ± 0,0023) y la del selector va aparte.
  Manual: `11-cartera.pdf`. Los `verdict.json` guardados llevan la cifra vieja.
- **m36, divisiones por cero o por negativo.** Una estrategia perdedora puntuaba 100 en la sub-nota B del
  Monte Carlo (ya la vetaba la puerta B); el recorte del banco daba NaN sin días cerrados. Corregidos.

Preguntas que dejan abiertas:

1. Replicación: con el suelo de 200, una referencia pequeña (XAUUSD/OOS de hoy: 229 estrategias) deja la
   tabla vacía; antes elegía filtros que conservaban unas 12. ¿Vale 200 también ahí?
2. Replicación: «previsto» es el máximo de unas 210 tasas, así que lee 53-56 % donde la verdad es 50 % y
   Δ sale −3 a −7 puntos por construcción. Documentado, no corregido.
3. Fondeo: cuántos días de mercado tiene el año al convertir un plazo (el horizonte de 126 días implica 252).

## 8. Recomendaciones

1. Recalcular los resultados de la tabla del punto 4 antes de decidir sobre supervivientes viejas.
2. Aplicar el grupo C cuando cierre la sesión del spread: lo mayor es el cargador rápido de YAML en
   `core/assetyaml.py`.
3. Arreglar `test_ui_blocks.py` y `test_ui_results.py`: cada uno agota sus 300 s y entre los dos marcan lo que tarda la suite (432 s).
4. Los 46 ficheros pegados al límite de 250 líneas (`PROJECT_MAP.md`, «Hot spots») son donde costará el
   siguiente cambio.

## 9. Ficheros de esta tarea

Ver `CLEANUP_STATUS.md`, sección «Ficheros para el commit».
