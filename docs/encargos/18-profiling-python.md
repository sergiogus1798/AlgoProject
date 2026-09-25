# 18 · Perfilar la capa de análisis de Python

**Para una instancia que va a hacer profiling de nuestros módulos de Python.** Todo lo que necesitas
está aquí o en las rutas que se nombran; no hace falta leer el resto de `docs/encargos/`.

El trabajo de campo ya está hecho una vez: el 2026-09-24 se construyeron 500 estrategias a propósito
para medir, y se midió el escalado de los módulos alcanzables. **Este fichero es ese estado.** Lo que
falta está en la sección «Lo que queda por perfilar», y hay cinco trampas abajo que ya costaron
tiempo: leerlas antes de medir cualquier cosa.

---

## 1 · Lo que heredas, con rutas exactas

**La población.** Proyecto `PerfUSDJPY_Python_v1` en el custodio (`~/Desktop/SQX_w2`), USDJPY H1,
plantilla `emaCloseAbove`, construido sobre el tramo `build` (2008–2017) y retesteado en `oos1`
(2018–2022). Existe **para medir**: no es un estudio y sus números no valen para juzgar nada.

| databank | `.sqx` en disco |
|---|---|
| `Results` (build) | 500 |
| `OOS` (retest `oos1`) | 500 |
| `Retest Markets - Family` (9 pares the5ers) | 500 |

**Los datos ya extraídos** — todo esto existe y no hace falta volver a tocar SQX para usarlo:

| qué | ruta | tamaño |
|---|---|---|
| operaciones de los 10 mercados | `AlgoData/raw/PerfUSDJPY_Python_v1/Retest_Markets_-_Family/2026-09-24/trades.parquet` | 365 MB, **12.010.976 operaciones** |
| cosecha IS/OOS emparejada | `AlgoData/harvest/PerfUSDJPY_Python_v1/Results/2026-09-24/` | 32 MB (`metrics`, `trades`, `equity`, `missing_oos.csv`) |
| las medidas crudas | `AlgoData/reports/perf-python-2026-09-24/` | `py_perf.csv`, `py_perf2.csv`, `tiempos.csv` |
| barras M1 de los 13 feeds | `AlgoData/bars/` | 1,6 GB, hasta 2026-09-22 |

**La máquina**: 96 núcleos, 125 GB. **Todo lo medido usa UN núcleo.**

---

## 2 · Cómo se midió, para que tus números sean comparables

Reloj de pared y RSS pico con `/usr/bin/time`, un envoltorio de tres líneas que añade una fila CSV:

```bash
# timeit.sh OUT NOMBRE comando...
/usr/bin/time -f "%e,%M" -o /tmp/_t.$$ "$@" >/tmp/_o.$$ 2>&1
read -r LINE < /tmp/_t.$$; echo "$NAME,$LINE,$?" | tee -a "$OUT"
```

Desglose por función con `python3 -m cProfile -s tottime -m <modulo> <args>`. **`-s tottime` para
encontrar el punto caliente, `-s cumtime` para encontrar quién lo llama**: los dos hacen falta y
dicen cosas distintas (en el gate, `cumtime` señala `monkey.mono` y `tottime` señala `calibrate.atr`,
que es el que hay que arreglar).

⚠️ **Esto NO va al catálogo de `perf/`.** Su regla es no tocar SQX nunca y comparar por unidad de
trabajo sobre ficheros fijos; esto es reloj de pared de comandos completos. Si añades un objetivo al
catálogo, que sea un kernel aislado, no un comando.

---

## 3 · Lo medido, y la unidad correcta

### La unidad es la OPERACIÓN, no la estrategia

🔬 En una misma corrida, las 8 estrategias llevaban entre **5.338 y 43.109** operaciones en los nueve
mercados ajenos: un factor de 8. Cualquier «segundos por estrategia» sobre una población así es
ruido. **Normaliza por operación y cuéntalas antes de lanzar nada:**

```bash
python3 -c "import pandas as pd; print(len(pd.read_parquet('<trades.parquet>')))"
```

### `gate.report` — el paso 8. Lineal y barato

| N | segundos | RSS |
|---|---|---|
| 25 | 3,52 | 505 MB |
| 50 | 5,19 | 545 MB |
| 100 | 8,22 | 636 MB |
| 250 | 15,93 | 819 MB |
| 500 | 32,28 | 1,32 GB |

**~60 ms por estrategia** de coste marginal sobre un fijo de ~2 s. Incluye las 8 cribas y el mono de
cada superviviente a 2.000 sorteos (`gate/config.yaml`, `monkey.draws`).

`gate.harvest` (la mitad que conduce SQX): **112,37 s y 4,56 GB** con 1.000 ficheros (500+500),
contra 58,29 s y 1,60 GB con 67. El tiempo lo domina el arranque de la JVM; **la memoria sí escala**.

### `crossmarket.report` — el paso 10. El cuello de botella

Tres medidas con SQX **parado** y 500 sorteos:

| N | operaciones | segundos | ms/operación | RSS |
|---|---|---|---|---|
| 2 | 44.660 | 170,63 | 3,82 | 6,0 GB |
| 4 | 133.240 | 507,40 | 3,81 | 6,8 GB |
| 8 | 158.415 | 630,10 | 3,98 | 6,8 GB |

Y con población fija (122.045 operaciones) variando los sorteos: 511,86 s a 500 y 614,26 s a 1.000.
De ahí:

> **coste ≈ (3,36 + 0,00168 × sorteos) ms por operación, un núcleo**

| sorteos | las 500 (12,0 M ops), 1 núcleo | con 90 núcleos |
|---|---|---|
| 500 | 14 h | 9 min |
| 2.000 | 22 h | 15 min |
| 10.000 (su `config.yaml`) | **67 h** | **45 min** |

⚠️ Los dos puntos de sorteos se midieron **con SQX corriendo a la vez**: el término de sorteos es
orden de magnitud, no promesa. **Remídelo limpio si vas a prometer algo.**

### Los demás, a la escala a la que se pudieron medir

| comando | población | segundos | RSS |
|---|---|---|---|
| `variants.scale` | 12 → 12 | 0,72 | 125 MB |
| `crossTF.report` | 24 celdas | 29,33 | 583 MB |
| `retest.ingest` | 36 corridas, 35.972 sims | 9,79 | **3,18 GB** |
| `retest.report` | 4 | 3,43 | 1,06 GB |
| `sppUltra.report` | 4 perfiles, 49.226 filas | 16,58 | 910 MB |
| `variants.make` | 1 madre, 60 variantes | 1,26 | 302 MB |
| `tasks.reports.is_oos` | 17 | 0,57 | 94 MB |
| `export_metrics` | 8 | 14,58 | 20 MB |
| `export_spp` | 4 perfiles | 15,31 | 1,41 GB |
| `export_retest` | 8 × 9 | 17,38 | 1,86 GB |
| `export_retest` | **500 × 9** | **154,24** | **6,30 GB** |

---

## 4 · Los puntos calientes ya localizados, con línea

### En el gate (cProfile, N=500, total 33,4 s)

| | tottime | % |
|---|---|---|
| `monkey.mono` (cumtime) | 29,5 | 88 |
| ↳ `engines/nulls/simulate.py:nulls` | 15,1 | 45 |
| ↳ `engines/nulls/simulate.py:fixed` | 9,9 | 30 |
| ↳ ↳ **`engines/market/calibrate.py:atr`** | **9,2** | **28** |
| `comp_method_OBJECT_ARRAY` | 4,2 | 13 |
| `engines/nulls/stats.py:profit_factor` | 3,6 | 11 |

1. 🔬 **`engines/nulls/simulate.py:fixed()` recalcula el ATR sobre las MISMAS barras, una vez por
   estrategia.** `calibrate.atr(frame, cfg["barrier"]["atr_bars"])` y `frame` es idéntico en las 500
   llamadas: 234 llamadas × 39 ms = **9,2 s de 33**. Depende sólo de `(frame, atr_bars)`. Cachearlo
   lo deja en 39 ms totales. **No cambia ningún número.**
2. 🔬 **`gate/monkey.py:31` filtra la tabla entera por identidad una vez por estrategia**
   (`oos[oos["identity"] == name]`) y la columna es `object`: 4,2 s en 236 comparaciones de cadenas.
   Un `groupby("identity")` una sola vez lo elimina.

Juntas, **~40 % del paso 8**, y las dos son la misma cuenta repetida.

### En el crossmarket (cProfile, 8 × 9 mercados, 500 sorteos)

| | tottime | cumtime |
|---|---|---|
| `simulate/metrics.py:46 paths` | 64,8 | **184,1** |
| `simulate/metrics.py:27 _losing_run` | 65,8 | — |
| `verdict/stress.py:13 degraded` | 65,4 | 65,5 |
| **`np.add.at` ← `mechanics/equity.py:42`** | 52,6 | — |
| `model/holdfit.py:37 fit` | 38,7 | — |
| `cumsum` · `ufunc.reduce` (1,78 M llamadas) | 28,5 · 28,1 | — |
| `numpy.partition` (121.904 llamadas) | 20,4 | — |

---

## 5 · Lo que YA se probó y NO funciona — no lo repitas

1. 🔬 **`np.add.at` → `np.bincount` en `mechanics/equity.py:42`: sólo 1,6x–2,5x**, no el 10x-50x que
   se suele suponer. Medido con el mismo resultado verificado (`np.allclose`):

   | runs | `add.at` | `bincount` | ganancia |
   |---|---|---|---|
   | 500 | 6,5 ms | 3,7 ms | 1,8x |
   | 2.000 | 12,9 ms | 8,2 ms | 1,6x |
   | 10.000 | 63,3 ms | 25,0 ms | 2,5x |

2. 🔬 **`_losing_run` NO es código ingenuo.** El bucle recorre **operaciones**, no caminos, y cada
   paso es una operación vectorial sobre todos los caminos. Es el coste inherente del barrido. Si lo
   atacas, atácalo por el número de temporales (`(run + 1) * (pnl[:, j] < 0) * live[:, j]` crea tres
   por columna), no por «vectorizarlo», que ya está.

3. 🤔 **Conclusión del que midió: en el crossmarket no hay micro-optimización que salve el día.** El
   coste es `operaciones × sorteos × mercados × modelos` y está donde debe estar. Lo que sobra es que
   **corre en 1 de 96 núcleos**, y el bucle exterior sobre estrategias (`report.py`, `for name in
   got["strategies"]`) es independiente por construcción. **Eso es el 90x, y no toca ninguna
   fórmula.** Si sólo vas a hacer una cosa, haz esa.

---

## 6 · Las cinco trampas que ya costaron tiempo

1. ⚠️ **Nunca midas con SQX corriendo.** El custodio usa los 96 núcleos. Dos de las medidas de
   sorteos están contaminadas por eso y hay que repetirlas. Comprueba antes:
   `ps aux | grep -c "[s]qcli"` → **tiene que dar 0**.
2. ⚠️ **`ps aux | grep StrategyQuant` NO encuentra el worker.** El proceso se llama `./sqcli`. Por
   ese error se leyó «la JVM murió» cuando estaba viva y sincronizando.
3. ⚠️ **Una tubería retiene la salida.** `python3 -m x | tail` no muestra nada hasta que termina, y
   un lote de una hora se vuelve indistinguible de un cuelgue. Usa `python3 -u` y **no canalices**.
   Para saber si trabaja: `ps -o etime,time -p <pid>` — si el tiempo de CPU sube, trabaja.
4. ⚠️ **No extrapoles SQX linealmente: es MÁS eficiente con lotes grandes**, al contrario que
   nuestro Python. Build 0,32 s/estrategia con 50 y **0,06 con 500**; crossmarket sobre 9 mercados
   4,9 s/estrategia con 17 y **0,59 con 500**. Una extrapolación lineal desde población pequeña
   **sobreestima SQX 4x-8x** (predije 41 min para un retest que tardó 293 s).
5. ⚠️ **`bin/sqx-worker.sh stop` puede tardar minutos** en databanks de 500, porque la
   sincronización de cierre es la que los escribe a disco. Ya espera hasta 5 min y avisa si sigue
   vivo; **no leas un databank hasta que diga `stopped`**.

---

## 7 · Lo que queda por perfilar, y qué necesita cada cosa

De **23 puntos de entrada** de análisis en Python se han medido **11**. Lo que falta:

| módulo | qué necesita para poder medirse |
|---|---|
| `walkForwardCorrelation/report.py` (paso 17) | 🔴 gasta `oos2` — **no se corre sin permiso del dueño** |
| `walkForwardCorrelation/pbo.py` (CSCV, paso 18) | 🔴 idem |
| `walkForwardMatrix/report.py` (paso 19) | 🔴 idem |
| `nulls/report.py`, `nulls/one.py`, `nulls/verify.py` | un export con `Sample type = OOS1`; el de crossmarket sólo lleva `IST` — ver abajo |
| `strategies/exposure/report.py` | un `trades.parquet` del **mismo** databank que las métricas |
| `strategies/monteCarlo/report.py` | un export de operaciones + `--asset` + `--export` |
| `strategies/entryQuality`, `parameterCloud`, `profitShape` | son paneles; hay que ver si tienen ruta de lote |
| `tasks/reports/{compare,decay,filters,nulls}` | `decay` pide `--split`/`--end`; `nulls` pide la salida de `nulls/report.py` primero |

🔬 **Y ojo: probando cinco de ellos a mano, cuatro fallaron, ninguno por un fallo de cálculo.** El
patrón y los cuatro modos están en `knowhow/eng/missing-input-not-traceback.md`, «El patrón que se repite». El peor es
**`nulls.report`, que escribe "0 estrategias" y sale con código 0** cuando `--sample` no casa con el
export. Si mides ese módulo, **comprueba que el informe no está vacío antes de creerte el tiempo**.

El MC Retest y el SPP no se midieron a 500 porque el trabajo de SQX no cabe: ~1.955 s por cada 8
estrategias en el MCR son **~34 h para 500**, y el SPP a ~20 s por madre son **2,8 h**.

---

## 8 · Reglas que este encargo no negocia

- **No toques el maestro** (`~/Desktop/SQX`) y no arranques builds en él. El custodio `SQX_w2` es
  tuyo, un trabajo a la vez, y **antes de pararlo o arrancarlo**: `ListAgents`, `ls -lt
  <install>/user/projects` y el log — el `stop` mata lo de cualquier sesión.
- **`oos2` no se toca.** Los pasos 17, 18 y 19 lo gastan y es una puerta de un solo sentido.
- **Perfilar no cambia resultados.** Cualquier optimización tiene que devolver el mismo número, y
  hay que demostrarlo, no suponerlo: `np.allclose` contra la implementación anterior sobre los
  mismos datos, en el commit.
- **Si optimizas, va en su rama** con la medida antes/después en el mensaje del commit
  (`perf-optimizer` es el agente que ya tiene ese contrato).
- `python3 tools/depmap.py && python3 tools/checks.py` antes de decir que has acabado.

## 9 · Dónde está escrito lo demás

| qué | dónde |
|---|---|
| las tablas completas, con el desglose de SQX | `docs/manual/12-rendimiento.md` |
| lo que cambia una decisión, en tres párrafos | `knowhow/perf/` y `knowhow/costs/` |
| los cuatro modos de fallo por entrada vacía | `knowhow/eng/missing-input-not-traceback.md` |
| el estado del workflow que produjo esta población | `docs/encargos/ejemplo-workflow-USDJPY.md` |
| lo abierto: §39 paralelizar, §40 el ATR y el filtro, §43 la mitad sin ejercitar | `OPEN.md` |

---

## Apéndice · Los dos troceadores, para reproducir el escalado

No están en el repositorio a propósito: son sondas de medición, no código del proyecto, y viven aquí
para que el encargo sea autocontenido. Las carpetas que crean (`perfN*`, `cmN*`) **se borran al
acabar** — no son datos del proyecto.

**Trocear la cosecha** (para `gate.report` a N estrategias). Crea proyectos sintéticos `perfN<N>` que
`gate.report --project perfN<N>` lee sin tocar nada más. ⚠️ Hay que arrastrar **todos** los ficheros
laterales, no sólo los parquet: sin `missing_oos.csv` el gate muere con `FileNotFoundError`.

```python
"""Cut a harvest down to its first N strategies, as a synthetic project the gate can read."""
import shutil, sys
from pathlib import Path
import pandas as pd

src = Path("/home/sergioguslw/Desktop/AlgoData/harvest/PerfUSDJPY_Python_v1/Results/2026-09-24")
for n in (int(x) for x in sys.argv[1:]):
    dst = Path(f"/home/sergioguslw/Desktop/AlgoData/harvest/perfN{n}/Results/2026-09-24")
    shutil.rmtree(dst.parent.parent, ignore_errors=True)
    dst.mkdir(parents=True)
    metrics = pd.read_parquet(src / "metrics.parquet")
    keep = list(metrics.index[:n]) if metrics.index.name == "identity" else \
           list(metrics["identity"].unique()[:n])
    metrics = metrics.loc[keep] if metrics.index.name == "identity" else \
              metrics[metrics["identity"].isin(keep)]
    metrics.to_parquet(dst / "metrics.parquet")
    for name in ("trades", "equity"):
        f = pd.read_parquet(src / f"{name}.parquet")
        f[f["identity"].isin(keep)].to_parquet(dst / f"{name}.parquet")
    for extra in list(src.glob("*.json")) + list(src.glob("*.csv")):
        shutil.copy2(extra, dst / extra.name)
    print(f"perfN{n}: {len(keep)} estrategias")
```

**Trocear el export de operaciones** (para `crossmarket.report` a N estrategias):

```python
"""Cut a trades export down to its first N strategies, as a synthetic project."""
import shutil, sys
from pathlib import Path
import pandas as pd

src = Path("/home/sergioguslw/Desktop/AlgoData/raw/PerfUSDJPY_Python_v1/"
           "Retest_Markets_-_Family/2026-09-24")
full = pd.read_parquet(src / "trades.parquet")
names = sorted(full["strategy"].unique())
for n in (int(x) for x in sys.argv[1:]):
    dst = Path(f"/home/sergioguslw/Desktop/AlgoData/raw/cmN{n}/"
               f"Retest_Markets_-_Family/2026-09-24")
    shutil.rmtree(dst.parent.parent, ignore_errors=True)
    dst.mkdir(parents=True)
    full[full["strategy"].isin(names[:n])].to_parquet(dst / "trades.parquet")
    for extra in src.glob("manifest.json"):
        shutil.copy2(extra, dst / extra.name)
    print(f"cmN{n}: {n} estrategias")
```

Con eso, una medida de escalado es:

```bash
python3 slice_trades.py 2 4 8 16
for n in 2 4 8 16; do
  timeit.sh salida.csv "crossmarket,$n" python3 -u -m strategies.crossmarket.report \
      --project cmN$n --databank Retest_Markets_-_Family --asset USDJPY \
      --export 2026-09-24 --set nulls.draws=500
done
```

⚠️ **Cuenta las operaciones de cada trozo y normaliza por ellas**, no por N: los trozos de 4 y 8
estrategias tenían 133.240 y 158.415 operaciones — 2x en estrategias, 1,19x en trabajo real. Sin
normalizar, el escalado parece roto y no lo está.
