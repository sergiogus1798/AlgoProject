# Cómo guardar lo que las pruebas producen — análisis y propuesta (2026-09-23)

> **Aplicado el mismo día** (decisión del dueño): `export_spp`, `export_retest`, `export_wfm` y
> `export_trades` escriben ya el árbol de la sección 5, los lectores de `sppUltra`, `variants`,
> `crossmarket` y `walkForwardMatrix` leen parquet, las exportaciones existentes se migraron con
> verificación de filas y sumas de P&L, y `raw/` pasó de 346 MB y 270 ficheros a 112 MB y 123.
> Sin hacer: `wfc_pairs` (5 MB, sin lector en código) y `retest.csv` de las variantes (0,6 MB).

**Alcance.** Las pruebas de SQX y los estudios de Python que las leen, y qué CSV y parquet
necesita cada uno para funcionar. Fuera: las barras (`bars/`, decisión ya tomada: M1 en parquet y
el resto calculado) y los informes (`reports/`, que acumulan y son pequeños).

**Respuesta corta.** Hoy conviven tres formas de guardar lo mismo. Dos de ellas ya son la buena
(`trades.parquet` de `core/tradestore.py` y el parquet particionado del MC Retest) y la tercera,
CSV sueltos por estrategia o tablas CSV, es la herencia de los primeros exportadores. No hace falta
un formato nuevo: hace falta que las tres pruebas que aún exportan a CSV usen el patrón que las
otras dos ya usan. El ahorro medido es de 346 MB a unos 130 MB en `raw/`, y en memoria la tabla
más leída pasa de 62 MB a 6 MB cuando el lector solo necesita cuatro columnas.

## 1. El mapa: cada prueba de SQX y quién la lee en Python

El `.sqx` es la fuente de verdad. Cada prueba de SQX deja su resultado **dentro del `.sqx`** de la
estrategia (un ZIP con XML y blobs binarios) y Python lo saca de dos maneras: pidiendo a SQX que
exporte (`orderstocsv`, Data View) o leyendo el ZIP directamente sin SQX (`core/optprofile.py`,
`core/wfmatrix.py`, `core/sqxretest.py`, `core/sqxstats.py`). Lo exportado es una **proyección**:
se puede regenerar mientras el `.sqx` exista, y por eso el snapshot de `user/projects` es la única
copia que de verdad importa.

| prueba en SQX (tarea del proyecto base) | qué deja en el `.sqx` | cómo sale | formato hoy | quién lo lee | disco | RAM al leer | lectura |
|---|---|---|---|---|---|---|---|
| **Build + Retest OOS** (tareas 1-2) | `SQStats`: 152 estadísticos IS/OOS | `export_metrics` (Data View) | `metrics/<P>/<DB>/metrics.csv`, 37 col | `tasks/reports/*`, `sqx/curate` | 2,9 MB × 5 | 4,7 MB | 0,14 s |
| **trades de un databank** (MC Trades, Results) | la lista de órdenes | `export_trades` → `orderstocsv` → `tradestore.pack` | **`trades.parquet` tipado**, 13 col, `strategy` categórica | `strategies/monteCarlo`, `nulls/` | 20 MB / 960.705 filas | 74 MB | 0,06 s |
| **Retest Markets - Family** (tarea 3, `data=all`) | las órdenes en oro, plata y Brent | `export_retest` → `orderstocsv` → partido por mercado | **118 CSV** `;` con 7 columnas de texto: `raw/` (30) + `trades/<feed>/` (88) | `strategies/crossmarket` (lee un CSV por estrategia y mercado) | 30,6 MB | 1-4 MB por fichero, 7 columnas objeto | 0,02-0,05 s por fichero |
| **MCR 1-8** (tareas 5-12, Monte Carlo Retest) | 1.000 simulaciones × 30 métricas y su P&L | `strategies/retest/ingest` lee el ZIP | **parquet particionado** `task=/strategy=`, `int32` en céntimos, zstd, categóricas | `strategies/retest` | 76 MB / 35 M filas de P&L | 5 MB la tabla de simulaciones | 0,02 s por partición |
| **SPP IS / OOS** (tareas 13-14) | el perfil de permutaciones (`optprofile`) | `export_spp` lee el ZIP | **5 CSV**: `permutations` (21.205 × 154), `permutation_params` en forma larga (213.642 × 4), `runs`, `metrics`, `histograms` | `strategies/sppUltra`, `sqx/variants/inputs` (4 columnas), `walkForwardCorrelation` (`wfc_pairs`) | 49 MB | **27,5 + 34,3 MB** | 0,47 + 0,09 s |
| **WFM** (tarea 15) | la matriz: 30 celdas × 12 tramos, 152 estadísticos IS y OOS por tramo | `export_wfm` lee el ZIP y pide los trades con `orderstocsv` | **66 CSV**: `cells`, `steps` (720 × 314), `params` largo, `check`, más `raw/` (2 CSV, 17 MB) y `trades/<estrategia>/<celda>.csv` (14 MB) | `strategies/walkForwardMatrix` | 34 MB | 1,9 MB `steps`, 30 MB un `raw/` | 0,1 s |
| **variantes** (pipeline: el retest del custodio sobre 2.000-5.000 `.sqx` fabricados) | `SQStats` y `dailyEquity.bin` de cada variante | `collect` (Data View) y `equity` (lee el ZIP) | `retest.csv` (2.000 × 44), `metrics.parquet`, `equity.parquet` (3.925 días × 962), `plan.csv`, y **2.000 `.sqx`** en `sqx/` | `walkForwardCorrelation` (WFC y CSCV) | 39 MB, de los que 32 son los `.sqx` | 30 MB `equity` | 0,07 s |
| **Sequential optimisation** (fuera del proyecto base) | pares IS/OOS por parámetro | a mano → `wfc_pairs/*.csv` | CSV **ancho** (11.600 × 14) | `walkForwardCorrelation/trials` | 5 MB | 3,4 MB | 0,08 s |

Medido el 23-09-2026 sobre lo que hay en `~/Desktop/AlgoData` con pandas; "RAM" es
`memory_usage(deep=True)` del DataFrame tal como lo carga el lector actual.

## 2. Lo que el mapa dice

1. **Las dos pruebas mejor guardadas son las dos que ya son parquet tipado.** `trades.parquet`
   guarda 960.705 operaciones en 20 MB con `strategy` categórica, y el MC Retest guarda 35 millones
   de P&L en 76 MB como `int32` en céntimos con zstd. Ninguna de las dos necesita cambios.
2. **Las tres que exportan a CSV son las tres que más ficheros y más memoria gastan por dato útil.**
   El cross-market son 118 ficheros para 30 estrategias. El WFM son 66. El SPP es un solo fichero
   grande, pero su tabla de parámetros está en forma larga: 213.642 filas × 4 columnas de las que
   dos son texto, **34 MB en RAM para 21.205 × 8 números** que en forma ancha ocupan 6 MB en RAM y
   0,17 MB en disco. Y el lector de variantes solo necesita 4 de las 154 columnas de
   `permutations.csv` pero un CSV obliga a leerlas todas (0,47 s cada vez).
3. **Cada exportación de trades guarda dos copias intermedias que ningún estudio lee:** `raw/`
   (lo que escribió `orderstocsv` antes de partirlo) y `strategies/` (los `.sqx` copiados al worker
   para exportar). Son 33 MB y 140 MB hoy. `perf.disk.report` ya lista `strategies/`; no conoce
   `raw/`.
4. **El único CSV que tiene sentido que siga siendo CSV es `metrics.csv`:** lo lee el dueño, lo
   filtra `curate` con una expresión pandas, y son 2,9 MB. Convertirlo ahorraría 2 MB y le quitaría
   la lectura directa.
5. **`wfc_pairs` es la prueba de que el formato ancho ya se eligió una vez:** es exactamente la
   forma que la tabla de parámetros del SPP debería tener.

## 3. Los cinco principios que salen de ahí

1. **El `.sqx` es la fuente y lo exportado es una proyección.** Nada exportado necesita ser
   inmutable por sí mismo: necesita un `manifest.json` que diga de qué `.sqx` salió y con qué
   commit. La regla "`raw/` es inmutable" sigue valiendo para no pisar exportaciones citadas por un
   informe, no porque no se puedan regenerar.
2. **Un fichero por prueba y exportación, no uno por estrategia.** Un parquet con columna
   `strategy` categórica se filtra en memoria más rápido de lo que se abre un CSV, y 118 ficheros
   son 118 manifiestos que no existen. `tradestore.pack(per_market=True)` ya hace esto para
   `data=all`; `export_retest` simplemente es anterior a él.
3. **Ancho para parámetros y estadísticos, largo para operaciones.** Una permutación es una fila
   con sus 8 parámetros y sus 152 estadísticos; una operación es una fila con su estrategia. La
   forma larga de `permutation_params` multiplica por diez las filas para nada.
4. **Tipos: `strategy`, `task`, `Symbol`, `Sample type` categóricas; dinero en `int32` céntimos o
   `float32`; fechas como timestamp, no texto.** Es lo que ya hacen `tradestore` y `retest/store`;
   es de donde sale que 35 millones de filas quepan en 76 MB.
5. **Los intermedios no sobreviven a la exportación que los produjo.** `raw/` se borra cuando
   `check.csv` cuadra (WFM) o cuando el `pack` termina (trades y cross-market); `strategies/` se
   borra cuando el `manifest.json` está escrito. El fichero final y el manifiesto son la prueba.

## 4. La propuesta, prueba por prueba, con el ahorro medido

| prueba | hoy | propuesta | disco | RAM del lector | qué se toca |
|---|---|---|---|---|---|
| **SPP** | 5 CSV, 49 MB; parámetros en largo | un `spp.parquet` ancho por exportación: `strategy` (categórica), `permutation`, las columnas de parámetro, los 152 estadísticos; `histograms.parquet` aparte (es el binning de SQX, no se deriva); `runs` y `metrics` se derivan del ancho y desaparecen | 49 → **6 MB** | sppUltra: 62 → 26 MB; variantes: 62 → **6 MB** (lee 4 columnas) | `export_spp.py` (5 escritores → 2), `sppUltra/inputs/export.py`, `sqx/variants/inputs.py`, `pipeline/recipe.yaml` (`produces`), 4 páginas del manual |
| **cross-market** | 118 CSV, 30,6 MB | un `trades.parquet` con `Symbol` vía `tradestore.pack(per_market=True)`; `raw/` borrado al terminar | 30,6 → **~3 MB**, 1 fichero | por estrategia: 1-4 MB con texto → una selección sobre categóricas | `export_retest.py` (usa `pack` en vez de `split`), `crossmarket/explorer/{work,serve,oos_run,analysis}.py` (4 puntos que hoy abren `<feed>/<nombre>.csv` → `tradestore.read` + filtro) |
| **WFM** | 66 CSV, 34 MB | `cells`, `steps`, `params` (ancho), `check` en parquet; los trades por celda en **un** `trades.parquet` con columnas `result` y `step`; `raw/` borrado cuando `check` cuadra | 34 → **~3 MB** | `steps` 1,9 → 0,7 MB; `params` deja de pivotarse en cada lectura | `export_wfm.py`, `walkForwardMatrix/inputs/export.py` |
| **trades de databank** | `trades.parquet` ✅ | sin cambio; borrar `strategies/` al escribir el manifiesto | −119 MB (MC Trades) | — | `export_trades.py`: una línea |
| **MC Retest** | parquet particionado ✅ | sin cambio | — | — | nada |
| **variantes** | `retest.csv` + `sqx/` | `retest.parquet`; `sqx/` lo barre `pipeline.cleanup` en cuanto se resuelva el asunto 33 de `OPEN.md` (una etapa reescribe `metrics.parquet` después de que `collect` lo firme) | −32 MB por madre | — | `sqx/variants/collect.py`, `execute.py`; el asunto 33 |
| **metrics** | CSV | sin cambio | — | — | nada |
| **wfc_pairs** | CSV ancho | parquet, misma forma | 5 → 0,6 MB | 3,4 → 1 MB | el que lo escribe es manual; `walkForwardCorrelation/verdict/trials.py` |

`raw/` pasaría de 346 MB a unos **130 MB** (76 MC Retest, 20 trades, 6 SPP, 3 WFM, 3 cross-market,
y el resto kilobytes), con **7 ficheros de datos donde hoy hay 270**, y cada uno con manifiesto.

## 5. El árbol que resulta

```
raw/<proyecto>/<databank>/<fecha>/
    manifest.json                 siempre: origen, commit, comando, recuentos
    trades.parquet                trades, cross-market (con Symbol) y WFM (con result, step)
    spp.parquet · histograms.parquet
    cells.parquet · steps.parquet · params.parquet · check.parquet
    sims/ levels/ pnl/ original/ returns/     el MC Retest, tal como está
metrics/<proyecto>/<databank>/metrics.csv     el único CSV, porque lo lee una persona
pipeline/<proyecto>/<madre>/                  ledger + retest.parquet + equity.parquet; sqx/ efímero
```

Nada de `raw/`, `strategies/`, ni `<feed>/<estrategia>.csv` dentro de una exportación.

## 6. Orden de ejecución y coste

1. **SPP** (3-4 h, la mayor parte en el manual: `08-spp.md`, `09-diccionario-spp.md`,
   `18-variantes.md`). Es la tabla que más se lee y la que más memoria desperdicia. Cambia el
   contrato del pipeline (`produces`), así que se hace antes de que corra sobre las 100 madres.
2. **Cross-market** (2-3 h). `tradestore.pack` ya existe; es sustituir `split` y cuatro lecturas.
3. **WFM** (2 h). Solo dos estrategias hoy; se hace por coherencia y para que la próxima
   exportación no vuelva a dejar 66 ficheros.
4. **Intermedios** (30 min): `export_trades` y `export_retest` borran `strategies/` y `raw/` al
   escribir el manifiesto; `perf/disk/retention.py` gana la regla `raw/`.

Cada paso en su rama, con la medida antes y después en el commit, y la re-exportación verificada
contra el CSV viejo antes de borrarlo (mismo número de filas, mismas sumas de P&L).
