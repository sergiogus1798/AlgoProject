# Mapa de carpetas — qué era qué antes de la refactorización del 25-09-2026

El 25-09-2026 los estudios estadísticos salieron de `strategies/`, `tasks/`, `nulls/` y `gate/` y se
ordenaron por **la pregunta que contestan**, siguiendo los pasos del `WORKFLOW.md`. Esta página es
la tabla de traducción: si un transcript, un informe viejo, un encargo o tu memoria nombra una
ruta antigua, aquí está en qué se convirtió. Nada se perdió; los números salen idénticos (regresión
completa el 25-09, ver el final).

## La idea en una línea

```
core/study/   el contrato: qué forma tiene un resultado, cómo se escribe y cómo se pinta
engines/      motores que CALCULAN y nunca juzgan (nulos, remuestreo, regímenes, inferencia…)
studies/      un estudio por pregunta, agrupados en familias; un estudio nunca importa otro
portfolio/common/monteCarlo/   el Monte Carlo de operaciones, que es una pregunta de cartera
```

| familia | la pregunta | pasos del WORKFLOW |
|---|---|---|
| `studies/screening/` | de miles, ¿cuáles merecen seguir? | 7–8 |
| `studies/transfer/` | ¿funciona lejos de donde se construyó? | 9–12 |
| `studies/breakage/` | si el mundo fuese un poco distinto, ¿qué la rompe? | 13–16 |
| `studies/optimisation/` | ¿optimizar compra algo, o elegir parámetros es sobreajustar? | 16.5–19 |
| `studies/closing/` | la decisión final y la forma del filo | 20–21 |
| `studies/readings/` | de qué está hecho el resultado de una estrategia; sin paso fijo | — |
| `studies/data/` | ¿los datos son de fiar? `feedQuality/`, el encargo 17 | — |

## Módulos de Python: ruta vieja → ruta nueva

### Estudios

| antes | ahora | manual |
|---|---|---|
| `gate` | `studies.screening.gate` | `29-puerta.md` |
| `tasks.analysis` (las matemáticas compartidas de la criba) | `studies.screening.analysis` | — |
| `tasks.reports.is_oos` | `studies.screening.isOos.report` | `01-analisis-is-oos.md` |
| `tasks.reports.filters` | `studies.screening.filters.report` | `02-filtros.md` |
| `tasks.reports.compare` | `studies.screening.replication.report` | `03-comparar-muestras.md` |
| `tasks.reports.decay` | `studies.screening.decay.report` | `04-decaimiento.md` |
| `tasks.reports.nulls` | `studies.screening.monkeyExcess.report` | `26-nulos.md` |
| `tasks.reports.summary` | **borrado** (lo sustituye el `.md` de cada estudio) | — |
| `strategies.crossmarket` | `studies.transfer.crossmarket` | `05-retest-mercados.md` |
| `strategies.crossTF` | `studies.transfer.crossTF` | `31-crosstf.md` |
| `strategies.retest` | `studies.breakage.mcRetest` | `11-retest-mc.md`, `32-mcretest.md` |
| `strategies.sppUltra` | `studies.breakage.spp` | `15-sppultra.md`, `33-spp.md` |
| `strategies.parameterCloud` | `studies.optimisation.cloud` | `39-nube-de-parametros.md` |
| `strategies.walkForwardCorrelation` | `studies.optimisation.wfc` | `19-wfc.md`, `37-wfc-retest.md` |
| `strategies.walkForwardCorrelation.pbo` y su `measure/cscv`, `measure/rules`, `verdict/` | `studies.optimisation.cscv` (`report`, `measure.cscv`, `measure.rules`, `verdict`) | `25-cscv.md` |
| `strategies.walkForwardMatrix` | `studies.optimisation.wfm` | `14-walkforwardmatrix.md`, `34-wfm.md` |
| `strategies.exposure` | `studies.closing.exposure` | `38-exposicion.md` |
| `nulls` (el estudio de entrada aleatoria) | `studies.readings.monkey` | `26-nulos.md` |
| `strategies.profitShape` | `studies.readings.profitShape` | — |
| `strategies.entryQuality` | `studies.readings.entryQuality` | `42-calidad-de-la-entrada.md` |
| `strategies.monteCarlo` | `portfolio.common.monteCarlo` | `07-montecarlo.md` |

### Motores (lo que antes vivía dentro de un estudio y usaban varios)

| antes | ahora |
|---|---|
| `nulls.kernel`, `nulls.model`, `nulls.simulate`, `nulls.stats`, `nulls.filter`, `nulls.barrier`, `nulls.verdict`, `nulls.inputs` | `engines.nulls.<lo mismo>` |
| `nulls/config.yaml` | `engines/nulls/config.yaml` |
| `nulls.calibrate` | `engines.market.calibrate` (y además `atr`, `point_value` y `CONVENTIONS`, que crossmarket tenía copiados) |
| `strategies.crossmarket.model` (colocación de operaciones sintéticas) | `engines.nulls.placement` |
| `strategies.crossmarket.simulate.kernel` | `engines.nulls.placement.kernel` |
| `strategies.monteCarlo.model.draws` | `engines.resample.draws` |
| `strategies.monteCarlo.model.regime` | `engines.regimes.regime` |
| `tasks.analysis.excess` | `engines.inference.excess` |
| `discoveries` de `tasks.analysis.correlations` | `engines.inference.fdr` |
| la lectura del panel de variantes, repetida en wfc y cscv | `engines.variants.panel` + `engines/variants/config.yaml` (`min_trades`, `split_mode` compartidos) |

### El contrato

| antes | ahora |
|---|---|
| cada módulo con su `render/` y su forma de resultado | `core/study/` (`blocks`, `result`, `config`, `output`, `verdicts`, `identity`) y `core/study/render/` (HTML y markdown) |
| los CLAUDE.md de `strategies/` y `tasks/` | `studies/CLAUDE.md` |

### Lo que se retiró

| antes | por qué |
|---|---|
| `strategies/monteCarlo/explorer/`, `strategies/crossmarket/explorer/`, `strategies/retest/explorer/` (los paneles Flask, puertos 8765–8767) | la ventana de escritorio (`ui/`) pinta el `.json` del contrato. Lo que ofrecían sigue dentro del resultado: los desplegables son `selectors` con los bloques ya calculados, el cajón de ajustes es `--set` y los `tooltips.py`, y «re-ejecutar una sub-prueba» / «correr un mercado suelto» son `one.run(..., only=...)` en Monte Carlo y crossmarket |
| los `render/` de cada módulo | `core/study/render/` los dibuja todos |
| `tasks/reports/summary.py` | cada estudio escribe su propio `.md` |

Se conserva `studies/screening/isOos/panel.html`: es el explorador estático (`explorer.html`) que se
abre con doble clic, no un servidor.

## Carpetas de informes en `AlgoData/`

Antes, cada módulo dejaba sus ficheros como quería: unos en una subcarpeta, otros sueltos en la
carpeta del día. Ahora **todos** los estudios escriben en `reports/<proyecto>/<databank>/<día>/<estudio>/`
lo mismo: `<estudio>.html/.md/.json` para la población, `estrategias/<nombre>.html/.json` por
estrategia, `verdict.csv` (`strategy`, `identity`, `verdict`) y `manifest.json`.

| antes (en `reports/P/D/<día>/`) | ahora |
|---|---|
| `retest/` (`retest.md`, `retest.html`) | `mcRetest/` (`mcRetest.*`) |
| `montecarlo/` (`montecarlo.html`, `montecarlo.md`) | `monteCarlo/` (`monteCarlo.*`) |
| `montecarlo_portfolio/` | `monteCarlo_portfolio/` |
| `montecarlo_panel/` (lo escribía el panel) | ya no se escribe |
| `nulls/` (`nulls.csv`, `rungs.json`) | `monkey/` (los mismos, más `monkey.*`) |
| `explorer.html`, `summary.md` sueltos (IS/OOS) | `isOos/` (`explorer.html`, `isOos.*`) |
| `filters/improvement.md` | `filters/filters.md` (+ `.html`, `.json`) |
| `_comparison/<día>/comparison.md` | `_comparison/<día>/replication/replication.md` |
| `decay.csv`, `decay.md` sueltos (columna `name`) | `decay/verdict.csv` (columna `strategy`), `decay/decay.*` |
| `excess.md` suelto | `monkeyExcess/monkeyExcess.*` |
| `exposure.csv`, `exposure.json`, `exposure_<E>.csv/.json` sueltos | `exposure/verdict.csv`, `exposure/exposure.*`, `exposure/estrategias/<E>.*` |
| `walkforwardmatrix.md`, `cell_correlations.csv` sueltos | `wfm/wfm.*`, `wfm/cell_correlations.csv` |
| `sppultra.md`, `design_brief_<E>.json` sueltos | `spp/estrategias/<E>.*`, `spp/design_brief_<E>.json` |
| `gate/resumen.md` | `gate/gate.md` (+ `.html`, `.json`); `scorecard.parquet`, `funnel.csv`, `verdict*.csv` igual |
| `crossmarket/` (`verdict.csv`, `crossmarket.*`) | igual, más `estrategias/` con el estudio completo de una estrategia (`--strategy`) |
| `crossTF/` | igual, más `crossTF.*` |

**Los informes anteriores al 25-09 ya están movidos** a su subcarpeta (66 movimientos, sin colisiones),
pero **conservan el nombre de sus ficheros**: `mcRetest/retest.md`, `decay/decay.csv`,
`spp/sppultra.md`, `isOos/summary.md`… Dentro llevan el formato antiguo, y renombrarlos habría
hecho pasar un informe viejo por uno del contrato nuevo. Los `design_brief_*.json` sí están donde
el pipeline los busca ahora (`{reports}/spp/`). Un `manifest.json` suelto se movió sólo cuando la
carpeta del día tenía un único estudio; si tenía varios, sigue en la raíz.

En una carpeta de lote de variantes (`AlgoData/pipeline/<proyecto>/<estrategia>/`):

| antes | ahora |
|---|---|
| `wfc.html` | `estudios/wfc.html` (+ `.md`, `.json`) |
| `cscv.html` | `estudios/cscv.html` (+ `.md`, `.json`) |
| la página de la nube de parámetros | `estudios/cloud.*` |
| `wfc.json`, `cscv.json` | **igual, en la raíz**: el pipeline lee de ellos sus escalares |

`cache/montecarlo/` y `cache/crossmarket/` eran de los paneles; ya no los escribe nadie y se pueden
borrar.

## Lo que viene (encargos)

Carpetas creadas vacías, con su README, para los encargos que todavía no están hechos:

| encargo | va a |
|---|---|
| 9 — falsos positivos | `studies/screening/falsePositives/` |
| 10 — data snooping | `engines/inference/snooping/` (el motor), `studies/screening/snoopingScreen/` (la criba), `studies/closing/blindJoint/` (la prueba conjunta del paso 20) |
| 11 — coste del filo | `studies/readings/edgeCost/` |
| 12 — estructura | `studies/readings/structure/` (la mitad estadística; la del XML va a `sqx/structural/`) |
| 13 — alfa y beta | dentro de `studies/closing/exposure/` (nota en su README) |
| 14 — mapa condicional | `studies/readings/conditionalMap/` |
| 15 — superficies de mercado | `studies/optimisation/marketSurfaces/` |
| 16 — repetición de mercado | `engines/market/replay/` |
| 17 — calidad del feed | `studies/data/feedQuality/` |

## Informes de los agentes: `audit/` → `AlgoData/audit/` (30-09-2026)

Los informes diarios y semanales (auditoría, `-mechanical`, `-fixes`, `-fondeo`, `-proyectos`) y el
`state.json` del auditor salieron del repositorio y de git: ahora viven en `AlgoData/audit/`
(`core.paths.AUDIT`). Un informe que cite `audit/AAAA-MM-DD.md` está ahí, con el mismo nombre.

## Cómo se comprobó que nada cambió

Todos los comandos se corrieron con el código viejo y con el nuevo sobre los mismos exports, y se
compararon las salidas: veredictos de mcRetest, crossmarket, exposure, decay y la puerta (con su
scorecard y su embudo), los briefs de SPP (salvo el campo `source`, que es la ruta), las 48 celdas
de crossTF, el panel de nulos, las celdas de WFM, `wfc.json`, `cscv.json` y la nube — idénticos. En
Monte Carlo, las columnas deterministas idénticas y los niveles de las 36 estrategias iguales.
