# La puerta OOS — dossier de diseño

**Qué es este documento.** Un *design dossier* en el sentido de `docs/AgentPDFs/README.md`: el
diseño completo del módulo que decide **qué estrategias sobreviven a su periodo fuera de muestra**,
con lo que ya está construido marcado como tal y lo que falta especificado con detalle suficiente
para implementarlo contra los contratos de la §4 sin que exista el módulo anterior.

**Para quién.** Para el dueño, y para el agente que lo implemente.

**Regla que hereda de esta carpeta.** El dossier guarda la narrativa y el plan; `knowhow/` guarda
los hechos. **Donde los dos discrepen, manda `knowhow/`.**

Generado el 2026-09-23. Se sitúa **antes** de `protocolo-robustez-2026-09-21.md` en el orden de
ejecución: la puerta cierne una población entera de miles de estrategias, y el protocolo de
robustez coge de una en una las que salgan vivas y les dedica días de máquina.

**Estado: construido y corrido el mismo día.** `gate/` existe, sus siete cribas corren, y la
primera cosecha real es `AlgoData/harvest/XAUUSD/OOS/2026-09-23` (231 estrategias, 307.593 trades,
906.675 días de equity, 11 MB). El primer veredicto está en
`AlgoData/reports/XAUUSD/OOS/2026-09-23/gate/`. Dos cambios sobre lo diseñado, ambos del dueño el
2026-09-23: **`redundancia` es `soft`** —agrupa y nombra, no elimina— y **todos los umbrales salen
deliberadamente laxos**, para ver cuánta población mata cada criba antes de apretar ninguno.
Lo que ese primer pase midió está en `knowhow/research/post-selection-bias.md`.

**Revisión del mismo día — la cosecha lee DOS databanks.** SQX solo admite un spread y un slippage
por backtest, y estas ventanas son de años sobre un activo que se mueve mucho, así que la
construcción y el retesteo son dos tareas y dos databanks. La cosecha los **empareja por identidad**
—🔬 estable entre databanks, 5 de 5 en `SPP IS`/`SPP OOS`; el nombre no, porque dos databanks de
este proyecto tienen estrategias distintas bajo un mismo nombre— y una estrategia que está en el
build y no en el retesteo **se descarta**: SQX ya decidió por sus banderas rojas (dueño, 2026-09-23).
Eso añade la criba `presencia` como primera de la cascada, y como el emparejamiento ocurre antes de
exportar nada, no se gasta máquina en ellas: en `XAU_ISOOS_ejemplo`, 5 de 120 murieron ahí y solo se
exportaron los 115 pares. Los contratos de la §4 quedan así: `metrics.parquet` indexado por identidad con cada
métrica dos veces (`[IS]`/`[OOS]`), `trades`/`equity` con columna `sample`, `missing_oos.csv`, y
**dos** veredictos, uno por databank.

---

## 1 · Contexto y hueco

La cadena que hoy existe llega hasta aquí:

```
proyecto propio ─▶ tarea build (IS) ─▶ tarea retest (OOS1) ─▶ databank OOS
                                                                   │
                                                              ¿y ahora qué?
```

Las condiciones de aceptación de SQX ya han filtrado por métricas estáticas durante el build. Eso
es un filtro, no un juicio: **una métrica estática sobre el periodo OOS no distingue una estrategia
que sobrevivió de una que fue seleccionada por haber sobrevivido**. Lo que falta es una puerta que
pregunte cuatro cosas más, en este orden: ¿esto es un dato válido?, ¿cuánto se degradó respecto a
IS?, ¿bate a un mono con la misma oportunidad?, ¿es distinguible de sus hermanas?

**Casi todas las piezas existen y ninguna se junta con las otras.** Cada test es hoy un comando
suelto que escribe su propio informe fechado en su propia carpeta, y la decisión la toma un humano
leyendo cuatro markdowns. El hueco no es matemático: es de orquestación y de coste.

## 2 · Decisiones del dueño — 2026-09-23

Tomadas antes de escribir código, y son las que fijan la forma del módulo:

| # | decisión | consecuencia |
|---|---|---|
| D1 | **Cascada dura**: cada rung elimina | el `reason` del veredicto dice en qué rung murió cada una |
| D2 | El módulo vive en **`gate/`, en la raíz** | `tasks/` y `pipeline/` lo importan; él no importa de ellos |
| D3 | El test del mono corre **solo sobre los supervivientes** de los rungs baratos | acota el coste; renuncia al exceso-sobre-azar de la población entera (§8) |
| D4 | La puerta **escribe `verdict.csv`, no aplica nada** | borrar sigue siendo un paso explícito con `--apply` |

## 3 · Arquitectura

`gate/` en la raíz, paralelo a `nulls/` y por el mismo motivo: lo llaman `tasks/`, `pipeline/` y las
skills, y meterlo dentro de `tasks/` obligaría a `pipeline/` a importar de `tasks/`, que apunta la
flecha al revés.

```
gate.yaml ─▶ harvest ─▶ rungs ─▶ scorecard ─▶ verdict ─▶ report
 los tests    una sola  la       todos los    el corte   el panel
 como datos   cosecha   cascada  números      y el       y el
                                 por          motivo     porqué
                                 estrategia
```

| fichero | qué hace | correrlo | en → sale |
|---|---|---|---|
| `harvest.py` | La cosecha única: métricas, trades y equity diaria de un databank en una sola pasada, con un manifest | `python3 -m gate.harvest --project P --databank OOS --role custodian` | databank → tres `.parquet` fechados |
| `rungs.py` | Un rung = una función pura `frame → (pasa, valor, motivo)`. Nada de I/O, nada de SQX | importado | cosecha → columnas del scorecard |
| `cascade.py` | Corre los rungs en el orden del yaml, cada uno sobre los supervivientes del anterior | importado | cosecha + yaml → scorecard |
| `report.py` | **La puerta entera sobre un databank** | `python3 -m gate.report --project P --databank OOS` | cosecha → `scorecard.parquet` + `verdict.csv` + `gate.html` |
| `gate.yaml` | Los rungs como datos: orden, umbral, `why`, y si elimina o solo mide | editado | — |
| `README.md` | Este diseño, en inglés, como el resto de carpetas de código | — | — |

**Los tests son datos, no código** — la misma regla que `pipeline/recipe.yaml`. Añadir el séptimo
rung es añadir una fila más una función en `rungs.py`. Y el veredicto es `recompute: true` por
construcción: la puerta **guarda números, nunca juicios**, así que cambiar un umbral re-juzga sin
recomputar nada que cueste máquina.

## 4 · Los contratos

### G1 · La cosecha — `harvest/<P>/<D>/<día>/`

Tres ficheros y un `manifest.json`, escritos **con una sola parada del custodio**. A partir de aquí
ningún rung vuelve a tocar SQX.

| fichero | filas | de dónde sale hoy |
|---|---|---|
| `metrics.parquet` | una por estrategia, columnas `<métrica>_IS` / `<métrica>_OOS` | `sqx.export.export_metrics` (hoy escribe CSV) |
| `trades.parquet` | una por trade, las 12 columnas de C4 + `strategy` | `sqx.export.export_trades`, ya probado a 757 estrategias / 960.705 trades |
| `equity.parquet` | una por (estrategia, día), P&L acumulado | `core.sqxstats.equity(path, result="Main")` sobre cada `.sqx` — lectura de zip, sin SQX |

⚠️ `equity()` se llama **siempre con el resultado nombrado**, nunca por posición: un `.sqx`
reteseado con cross-check lleva tres curvas y `Portfolio` va primero en el archivo
(`knowhow/sqx-format/result-sections.md`).

### G2 · `scorecard.parquet` — una fila por estrategia

`strategy` · `identity` (SHA-256 del XML interno) · y por cada rung tres columnas:
`<rung>_value`, `<rung>_p` (nula donde el rung no produce una p) y `<rung>_pass`. Más
`died_at` — el nombre del rung que la mató, o nulo si sobrevivió entera.

**Esto es el artefacto**, y es lo que hace la cascada barata sin ser opaca: una estrategia que muere
en el rung 1 tiene nulos de ahí en adelante, y se ve en la tabla que nunca se le gastó un mono.

### G3 · `verdict.csv` — **ya existe, no se inventa nada**

`strategy,verdict,identity,reason`, exactamente como lo lee `sqx/curate/apply_verdict.py`. El
`reason` es `died_at` más el valor que lo mató: `rung2_degradacion retention=0.18`.

### G4 · `gate.yaml`

```yaml
rungs:
  - name: sanidad
    kind: hard
    checks: [min_trades, cobertura_oos, sample_type, dedup_trades]
    min_trades: 100          # PENDIENTE de decisión (apéndice A)
    why: >-
      una estrategia con 30 trades fuera de muestra no tiene error estandar que leer
```

## 5 · La escalera

| # | rung | la pregunta | lee | coste | qué ya existe |
|---|---|---|---|---|---|
| 0 | `sanidad` | ¿esto es un dato válido? | trades | segundos | `core.trades`, `core.tradestore` |
| 1 | `estaticas` | ¿pasa los umbrales sobre OOS? | métricas | ~0 | `sqx.curate.verdict` (filtro pandas), `tasks.reports.filters` mide qué compra cada umbral |
| 2 | `degradacion` | ¿cuánto del filo IS sobrevivió, y lo que queda bate a su propio error? | equity | segundos | **`tasks/analysis/decay.py` entero**: retención de Sharpe, t de Lo (2002), años positivos, concentración trimestral |
| 3 | `forma` | ¿el drawdown OOS cabe en lo que IS hacía esperar? ¿es estable en el tiempo? | equity | segundos | `core.significance` (PSR, longitud mínima de track record) |
| 4 | `mono` | ¿bate a un aleatorio con la misma oportunidad? | trades + barras | **minutos por estrategia** | **`nulls/` entero** — `nulls.report` ya barre un export completo |
| 5 | `familia` | de los que pasan, ¿cuántos daría el azar? | p del rung 4 | ~0 | `engines.inference.excess`, `discoveries()` (Benjamini-Hochberg) |
| 6 | `redundancia` | ¿son N estrategias o una repetida N veces? | equity | segundos | nada — **es el único rung sin pieza previa** |

**El rung 0 no es burocracia.** Tres trampas ya documentadas viven ahí: el último trade puede ser
una orden pendiente sin llenar (`Close type=EndTest`); el `Sample type` depende de cómo se reteseó
esa estrategia y no se puede asumir; y **45 de 231 estrategias resultaron tener trades
byte-idénticos bajo hashes distintos** (`tasks/CLAUDE.md`). Deduplicar por trades antes del rung 4
es lo que evita pagar el mono cuatro veces por la misma estrategia.

**El rung 6 es el que hace la salida usable.** Sin él sales de la puerta con 200 primos hermanos, y
`portfolio/` no puede construir nada con eso. Agrupar por correlación de la equity diaria y quedarse
con un representante por clúster convierte «200 supervivientes» en «11 estrategias distintas».

### Por qué el orden es ese y no otro

El coste de cada rung difiere en **cuatro órdenes de magnitud**, y el más caro es el más informativo.
Corriendo los seis sobre todo, el mono domina el gasto entero del módulo; corriéndolo al final ve
decenas en lugar de miles. Ese es todo el argumento, y es la decisión D3.

## 6 · Qué se escribe nuevo

Muy poco, y es deliberado:

- `gate/harvest.py` — envuelve tres exportadores que ya existen en una sola pasada con un manifest.
- `gate/rungs.py` — los seis rungs; cinco son llamadas a módulos existentes, uno (redundancia) es nuevo.
- `gate/cascade.py`, `gate/report.py`, `gate/gate.yaml`, `gate/README.md`.
- `docs/manual/NN-puerta.md` — en español, con capturas de salida real. **Regla dura 8: la página de
  manual va en la misma tarea que el comando.**
- La skill `/puerta`, o una fila más en la skill `curate` existente.

Nada de `nulls/`, `tasks/analysis/` ni `sqx/curate/` se toca. Si un rung necesita algo que un módulo
existente no da, se amplía ese módulo, no se copia aquí.

## 7 · Lo que la puerta NO hace

- **No aplica nada** (D4). Escribe el `verdict.csv` y para.
- **No juzga el generador, solo las estrategias.** Ver §8.
- **No decide umbrales.** Los lee del yaml; medir qué compra cada uno es trabajo de
  `tasks/reports/filters.py`, que ya barre 210 candidatos con intervalo bootstrap y corrección BH.
- **No sustituye al protocolo de robustez.** Lo que sale vivo de aquí es lo que *entra* en
  `pipeline/`, que le dedica 5.000 variantes a cada una.

---

## Apéndice A · Umbrales — todos pendientes de decisión

Ni uno solo de estos números está decidido. Se listan aquí, separados del diseño, porque
`docs/AgentPDFs/README.md` lo exige y porque `OPEN.md` issue 19 ya registra qué pasa cuando un
umbral provisional se cuela en un módulo y se lee como si fuera una respuesta.

| rung | umbral | valor de arranque | cómo decidirlo de verdad |
|---|---|---|---|
| 0 | trades mínimos OOS | 100 | la longitud mínima de track record de `core.significance` sobre el Sharpe observado |
| 1 | métricas estáticas OOS | ninguno | barrido de `tasks.reports.filters` sobre el propio databank |
| 2 | retención mínima | 0.30 | distribución de retención sobre una población NO filtrada por OOS |
| 2 | t mínima | 1.65 | ya es el valor que usa `decay.py`; es un 5% a una cola |
| 2 | años positivos | 4 de 5 | `decay.py` ya documenta que 3 de 5 es lo que da una moneda |
| 2 | concentración máxima | 0.40 | ídem |
| 4 | p del mono | 0.05, y **sobre qué estadístico** | medido: en XAUUSD el 51,0 % bate al nulo en `sharpe` y el 21,5 % en `net`. **El estadístico mueve el veredicto más que el nulo**, y `nulls/` imprime todos y no elige ninguno. Esta es la decisión más importante del apéndice |
| 6 | correlación de corte | 0.70 | medida sobre la matriz real de una población superviviente |

## Apéndice B · Lo que NO se ha verificado

- **El coste real de `gate.harvest` sobre un databank grande no está medido.** `export_trades` sí lo
  está (757 estrategias, 960.705 trades); la extracción de equity vía `sqxstats.equity` está medida
  por variante en `sqx/variants/equity.py`, no por databank.
- **El rung 4 nunca ha corrido sobre estrategias con stop y target.** `nulls/barrier.intrabar` viene
  como `pessimistic` y `nulls/verify.py` prueba que el barrido es *correcto*, no que el convenio sea
  el de SQX. El día que una estrategia lleve barreras, calibrarlo contra SQX va primero.
- **El rung 6 no tiene implementación previa ni medición.** Es el único trozo realmente nuevo.
- **La contaminación por preselección no se resuelve, solo se declara.** Si el build llevaba
  condiciones de aceptación sobre OOS, la población ya está filtrada por la muestra que se juzga, y
  `tasks/reports/nulls.py::contamination()` avisa de ello. La puerta debe registrar **qué espacio de
  búsqueda** produjo la población; no puede deshacerlo.
