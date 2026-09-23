# 12. Catálogo de rendimiento — qué cuesta cada parte del proyecto, y si hoy cuesta más que ayer

### Qué pregunta responde

Este proyecto es caro: miles de estrategias, cientos de miles de simulaciones, y una máquina que
comparte con la GUI de StrategyQuant X. El catálogo mide **cuánto tarda y cuánta memoria pide** cada
parte cara del código, guarda la medida con la fecha y el commit, y la próxima vez te dice si algo
se ha vuelto más lento.

También mide el disco: cuánto ocupa cada rama de `AlgoData`, qué ficheros están duplicados, y cuánto
costaría leer los mismos datos guardados en otro formato.

No es un test. No dice si el código está bien: dice lo que cuesta.

### Cuándo lo usas, y cuándo no

**Úsalo** después de tocar cualquier módulo de análisis, antes de lanzar una corrida larga que tiene
que caber en memoria, y cuando quieras saber dónde merece la pena invertir tiempo de programación.

**No lo uses** para comparar con la medida de otra máquina: los números son de este servidor. Y no
lo uses como prueba de que un cambio es correcto — puede ser tres veces más rápido y estar mal.

**No hace falta cerrar SQX.** Ningún objetivo toca la instalación: todos leen ficheros ya exportados
bajo `~/Desktop/AlgoData`. Pero si la GUI está construyendo estrategias, la máquina está ocupada y
las medidas saldrán peores; el panel guarda la carga del sistema con cada fila para que eso se vea.

### Antes de empezar

Tiene que existir un export de trabajo bajo el raíz de datos. Por defecto el catálogo mide sobre:

| qué | dónde | se cambia en |
|---|---|---|
| operaciones exportadas y sus `.sqx` | `raw/XAUUSD/MC_Trades/<fecha>/` | `sample.trades_databank` |
| batería de retest ya ingerida | `raw/XAUUSD/MCR_All/<fecha>/` | `sample.retest_databank` |
| velas | `bars/XAUUSD_DukasM1_Infinox/M30.csv` | `sample.bars_feed` |

Siempre usa **el export más reciente** de cada uno. Si no tienes alguno, exporta primero
(`docs/manual/00-empezar.md`) o cambia esas claves en `perf/config.yaml`.

### Cómo se ejecuta

```bash
python3 -m perf.catalogue
```

![](assets/perf-catalogo-terminal.png)

Una línea por objetivo. `ahora` es el tiempo de esta medida, `antes` el de la anterior, `tiempo` el
cambio **por unidad de trabajo** y `memoria` el cambio en el pico de memoria.

| flag | obligatorio | qué hace |
|---|---|---|
| `--only` | no | mide sólo esos objetivos o esa área (`core`, `strategies`, `montecarlo.analyse`) |
| `--scaling` | no | vuelve a medir el techo de memoria de la máquina; tarda unos minutos |
| `--hotspots OBJETIVO` | no | en vez de medir todo, perfila uno y dice dónde se le va el tiempo |
| `--set CLAVE=VALOR` | no | cambia cualquier valor de `perf/config.yaml` sólo para esta corrida |

El comando **sale con código 1 si algo ha empeorado**, así que puede ir en cron sin nadie delante.

Los otros dos comandos:

```bash
python3 -m perf.disk.report      # inventario de AlgoData, presupuestos y qué se puede borrar
python3 -m perf.render.panel     # dibuja la página con lo que ya está guardado
```

![](assets/perf-disco-terminal.png)

#### El presupuesto de disco

Desde el 2026-09-21, `perf.disk.report` **también sale con código 1 si alguna rama de `AlgoData` se
pasa de su presupuesto**, o si el total se pasa del suyo. Igual que `perf.catalogue` con las
regresiones: así puede ir en cron y creerte lo que dice.

```
AlgoData: 2.47 GB de 60 GB (4%) en 55 ramas

           ok      1.96 GB /   40 GB      5%  raw
           ok      0.30 GB /    3 GB     10%  bars
           ok      0.11 GB /    1 GB     11%  logs
           ok      0.06 GB /    5 GB      1%  reports
```

Los techos están en `perf/config.yaml`, en `disk.budget_gb`. Se dimensionaron con 2,3 GB en uso y
dejando sitio para el estudio de variantes (~200 MB de operaciones por estrategia madre y mercado,
así que el crecimiento va a caer en `raw/`).

Una rama **sin** presupuesto sale marcada `sin presupuesto`, no aprobada. Que aparezca una rama
nueva y empiece a engordar es justo lo que esta tabla existe para que veas.

#### Qué se puede borrar

Y una última sección dice **qué se podría borrar y cuánto liberaría**:

```
candidatos a borrar: 6, 0.47 GB  (nada se borra aquí)
      331.9 MB  strategy_copies    raw/XAUUSD/WFM_Stability/2026-09-10/wfm/strategies
      118.9 MB  strategy_copies    raw/XAUUSD/MC_Trades/2026-09-19/strategies
        0.9 MB  superseded_export  raw/XAUUSD/Retest_Markets_-_Family/2026-09-09
```

Cinco reglas, y **sólo una de ellas es un veredicto**:

| regla | qué encuentra | cuánto te puedes fiar |
|---|---|---|
| `collected_variants` | databanks que el ledger del pipeline dice que ya se exportaron **y se comprobó el hash** | **veredicto** — está probado que el dato sobrevivió |
| `superseded_export` | un export fechado cuyo hermano más nuevo contiene todo lo que él tiene | candidato |
| `strategy_copies` | ficheros `.sqx` dentro de exports, que duplican lo que ya guarda el databank | candidato |
| `intermediates` | carpetas `raw/` y `trades/` de CSV al lado de un `trades.parquet` que ya las contiene (los exports posteriores al 23-09-2026 las borran solos) | candidato |
| `stale_branch` | nada escrito en 90 días | la más floja — viejo no es lo mismo que sobrante |

⚠️ **Nada del proyecto borra ninguna de estas cosas.** La lista sólo le pone un número a una
decisión que sigue siendo tuya.

Un detalle que importa: `superseded_export` compara **contenidos**, no fechas. La primera versión
comparaba fechas y propuso borrar `raw/XAUUSD/SPP_IS/2026-09-10` porque existe un `2026-09-19` —
pero el del 19 sólo tiene `wfc_pairs/`, mientras que el del 10 tiene las tablas de permutaciones que
lee todo el estudio SPP. Habría propuesto borrar la única copia de los datos de entrada. Ahora un
export sólo cuenta como sustituido si el nuevo lo contiene **entero**.

(`perf/measure/runner.py` también se puede ejecutar, pero es interno: es el subproceso que el arnés
arranca para medir un objetivo aislado. No lo llames a mano.)

### Qué salidas produce, y qué significan

Todo vive en `~/Desktop/AlgoData/profiling/`:

| fichero | qué guarda |
|---|---|
| `history.csv` | una fila por medida, para siempre. **Sólo crece**: nunca se edita ni se borra |
| `scaling.csv` | las curvas de escalado de la máquina |
| `disk.csv`, `duplicates.csv`, `formats.csv` | el inventario del disco |
| `budgets.csv` | cada rama contra su presupuesto, una fila por corrida |
| `reclaimable.csv` | los candidatos a borrar, con sus bytes y su motivo |
| `rendimiento.html` | la página |

#### La tabla de costes

![](assets/perf-panel-costes.png)

Columna por columna:

- **segundos** — lo que tardó la medida mediana de las tres repeticiones.
- **microsegundos/unidad** — lo mismo dividido entre el trabajo hecho. **Ésta es la que decide.** Si
  el export crece de 500 a 3.000 operaciones, los segundos suben y esta columna no: el código no se
  ha vuelto más lento, hay más datos.
- **trabajo** — cuántas operaciones, filas, velas o ficheros procesó, con su unidad.
- **MB pico** — el pico de memoria residente **del árbol de procesos entero**, incluidos los
  trabajadores que el objetivo arranque. Es la cifra que decide si una corrida cabe en la máquina.
- **dispersión %** — cuánto se separaron entre sí las repeticiones de esta misma medida. Es el
  ruido del instrumento.
- **veredicto** — uno de cinco:

| veredicto | qué significa |
|---|---|
| `first` | primera vez que se mide; no hay con qué comparar |
| `regression` | más del 15 % más caro por unidad, o más del 15 % más de memoria |
| `improvement` | más del 15 % más barato |
| `steady` | cambió poco, y ese poco es mayor que el ruido de la medida |
| `noisy` | cambió menos de lo que el instrumento puede distinguir. **No es "igual": es "no lo sé"** |

#### El techo de la máquina

![](assets/perf-panel-escalado.png)

Las dos líneas son el mismo cálculo moviendo los mismos bytes. La única diferencia es si el dato
cabe en la caché del procesador o hay que ir a buscarlo a la memoria principal.

Que la línea `cache` siga subiendo hasta 96 procesos y la `dram` se quede plana desde 16 significa
que **los núcleos que sobran no están calculando: están esperando memoria**. La consecuencia
práctica: en un módulo cuyos datos no caben en caché, pedir más procesos no lo hace más rápido —
sólo gasta más RAM.

#### El disco

![](assets/perf-panel-disco.png)

Las ramas más grandes son sólo las hojas: una carpeta que contiene a otra de la lista no aparece,
porque su barra sería la suma de sus hijas otra vez. Los **duplicados son candidatos, no una
sentencia**: dos ficheros que coinciden en tamaño y en 64 KB de cada extremo son casi seguro el
mismo fichero, pero nada aquí lo confirma y **nada aquí borra nada**.

### Dónde se le va el tiempo a un módulo

```bash
python3 -m perf.catalogue --hotspots core.sqx_stats
```

![](assets/perf-hotspots-terminal.png)

Arriba, las funciones ordenadas por **tiempo propio** — el gastado dentro de su propio cuerpo, sin
contar a quién llaman. Abajo, las líneas que tenían más bytes vivos en el momento de mayor consumo.

Dos avisos:

- Los segundos de un perfilado son más largos que los reales, porque perfilar cuesta. **Lee el orden,
  no los segundos.**
- La lista de memoria sólo ve lo que reservó Python en ese proceso. Los buffers de numpy dentro de un
  trabajador no salen ahí: para eso está la columna `MB pico`, que muestrea el árbol entero.

### Qué se puede tocar

Todo está en `perf/config.yaml`. Lo que de verdad cambia el resultado:

| clave | qué hace |
|---|---|
| `harness.repeats` | repeticiones por medida. Menos repeticiones, más ruido y más veredictos `noisy` |
| `regression.wall_pct` | a partir de qué porcentaje una medida se llama regresión |
| `sample.n_sims` | el presupuesto de simulación del objetivo de Monte Carlo |
| `sample.files` | cuántos ficheros muerden los objetivos de parseo |
| `disk.stale_days` | a partir de cuántos días sin tocar una rama se marca como obsoleta |

**Cambiar `sample.*` rompe la comparación con las medidas anteriores**, porque ya no es el mismo
trabajo. Si lo cambias, la historia previa de ese objetivo deja de valer.

### Las trampas que este módulo existe para evitar

- **`ru_maxrss` miente cuando hay trabajadores.** De los procesos hijos informa del más grande, no de
  la suma. Medido el 2026-09-20: `montecarlo.analyse` da 535 MB por `ru_maxrss` y **2.340 MB**
  muestreando el árbol. La segunda es la buena.
- **El muestreo cada 50 ms puede perderse un pico más corto que eso.** La cifra es un suelo.
- **Una medida con la máquina ocupada no vale.** Por eso cada fila guarda la carga del sistema y la
  memoria libre que había.
- **Un commit `-dirty` no se puede reproducir.** El panel lo enseña tal cual para que se vea.
