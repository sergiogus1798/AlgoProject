---
name: variants
description: Run the variant factory in SQX — turn one mother's SPP design brief into a batch of parameter variants, load and retest them on the custodian, and harvest the metrics panel and the per-day equity the WFC and the CSCV read. Use when the owner asks to fabricate, run or retest variants, to prepare the walk-forward correlation, or about step 16.5 of the workflow.
---

# /variants

Paso 16.5 del workflow: **de un diseño a una población de variantes medida**. Cuatro comandos en
orden, tres de ellos sin tocar SQX y uno que ocupa el custodio durante horas. Lo que sale de aquí es
lo que leen el WFC (paso 17) y el CSCV (paso 18) — y esos dos no se miran hasta que el 19 también
esté hecho.

## Por qué existe

**Ningún verbo de `sqcli` cambia los parámetros de una estrategia.** Ninguno. La única forma de
puntuar una combinación es escribir un `.sqx` con ese valor dentro y retestear ese fichero. Eso es
la fábrica.

Y hace falta porque los dos SPP del paso 15 **no se pueden emparejar**: comparten 6 tuplas de
~11.600. Para tener la misma combinación medida dentro y fuera de muestra hay que fabricarla.

## ⚠️ Antes de nada: en qué proyecto corre

`sqx/variants/config.yaml` lleva `execute.project`. Si pone **`Retester`**, eso incumple la regla
dura 10 (todo run en un custom project) y hay que migrarlo antes de lanzar nada:

```bash
python3 -m sqx.projects.builder <SIMBOLO>_variantes --template <plantilla> --symbol <SIMBOLO> \
    --role custodian --timeframe M30 --tasks Retest --only Retest-Task1.xml
```

y poner ese nombre en `execute.project`. Está anotado en `OPEN.md` §38. Si el dueño dice que corra
igual, se corre y se dice en el informe por dónde ha corrido.

⚠️ **Y ya no es una tarea, son tres** (dueño, 2026-09-24). El retest que alimenta el WFC y el CSCV
corre `build`, `oos1` y `oos2` en tareas separadas, cada una a su spread y su slippage y con los
mercados adicionales dentro. La doctrina está en `wfc:` de `assets/_build.yaml` y quien escribe las
tareas es:

```bash
python3 -m sqx.projects.wfc <SIMBOLO> --cfx <install>/user/projects/<P>/project.cfx \
    --timeframe M30 --tasks Retest-Task1.xml,Retest-Task2.xml,Retest-Task5.xml
```

Manual: `docs/manual/37-wfc-retest.md`. **La cosecha ya lee los tres databanks**: `execute.py`
exporta un panel por tramo, `equity.py` une las curvas diarias de los tres (y guarda las de cada
mercado adicional aparte) y `collect.py` deja en C3 las métricas por tramo, por mercado y las
uniones. De ahí salen las dos lecturas del WFC — `build` vs `oos1+oos2`, y la estricta `build+oos1`
vs `oos2` — sin volver a correr nada.

## El suelo duro: 50 operaciones

`wfc.min_trades_total` en `assets/_build.yaml` (dueño, 2026-09-24). Un backtest con menos de 50
operaciones sumando `build`+`oos1`+`oos2` **no entra en ninguna estadística**: `collect.py` no lo
escribe en `metrics.parquet`. Se cuenta por variante **y por mercado**, la evidencia completa se
queda en `segments.parquet` con `usable=False`, y el recuento se canta por pantalla y en
`collected.json`. Al informar, di cuántos cayeron: un lote donde la mitad no llega al suelo no es un
lote con menos puntos, es un diseño que fabricó variantes que no operan.

No confundirlo con `min_trades: 30` del `config.yaml` del WFC, que mira cada lado de la partición
por separado y actúa después.

## Los cuatro comandos

```bash
python3 -m sqx.variants.make --brief <design_brief_<Estrategia>.json> --project <PROYECTO> \
    [--out <work>] [--sample N | --limit N] [--design-only]
python3 -m sqx.variants.execute --work <work>     # ⏰ el único que ocupa el custodio
python3 -m sqx.variants.collect  --work <work>
python3 -m sqx.variants.equity   --work <work>
```

| comando | qué deja | toca SQX |
|---|---|---|
| `make` | `plan.csv`, `design.json`, `sqx/` con las N variantes, `manifest.parquet` | no |
| `execute` | `retest.csv`, `ran.json`, el databank volcado a disco | **sí** |
| `collect` | `metrics.parquet` — el panel unido al manifiesto | no |
| `equity` | `equity.parquet` — el P&L **por día** de cada variante | no |

`--sample N` fabrica N filas **repartidas** por todo el plan (los controles y luego picks
espaciados de cada estrato); `--limit N` coge las N primeras y sesga el lote hacia un estrato. Para
una prueba de humo, `--sample`.

El brief sale del paso 16: `strategies/sppUltra/report.py`. Si su veredicto es `noise`, la familia
no se distingue del azar y fabricar variantes de ella es medir ruido — el comando no lo impide, lo
enseña en la primera línea. Decírselo al dueño antes de gastar la tarde.

## Los tres contratos, y por qué son tres

**design** decide y no escribe ningún fichero. **build** escribe y no decide nada. **manifest** lee
los ficheros de vuelta del disco y describe lo que **hay**, no lo que se quería que hubiera. Ese
tercer límite es lo único que detecta un fichero cuyo contenido no es la tupla que le dio nombre, y
ese fallo es silencioso en cualquier otro montaje.

## Los cinco controles del lote

Están para fallar, no para analizarse: `P00000` (el origen refabricado), tres canarios con resultado
ya conocido tomados en los **extremos** de la rejilla SPP, y un par inerte por parámetro congelado.
Si `collect` dice que todos los controles devolvieron el mismo número, la cadena está rota y se para
ahí. Un canario en el extremo delata una cadena rota; uno del medio devuelve un número plausible.

⚠️ La expectativa de un canario es sobre el resultado **dentro de muestra** y sólo vale mientras la
ventana IS del retest sea la que corrió el SPP.

## Las trampas medidas

- **Un `.sqx` reteseado lleva TRES curvas de equity** — `Portfolio`, `Main:` y una por mercado
  cruzado — y `Portfolio` va primero en el archivo. Leer la primera da oro más plata: 10.476 contra
  35.328 en `P00000`. `equity.py` las llama por su nombre, nunca por posición.
- **`synctofiles` escribe con retraso**: 962 de 2.000 estaban en disco cuando el retest dijo que
  había acabado. `execute` espera, pero el cap es `sync_tries` en el config.
- **`-project action=startOnlyTask` dice que sí y no testea nada** en esta instalación. Sólo
  `action=start` corre la tarea.
- **Nunca dejar el worker arriba**: un sync borra los `.sqx` que no tiene en memoria (regla dura 1).
  `execute` lo para si fue él quien lo levantó.
- Antes de tocar W2: `ListAgents`, `ls -lt user/projects` y el log. El `stop` mata lo de cualquiera.

## Qué mirar

- `make`: `planned N de un target M` con el shortfall. Un hueco grande no es un fallo — una tupla
  nunca se repite para llegar al target.
- `execute`: `n_loaded` contra `n_returned` contra `n_on_disk` en `ran.json`. Si bajan, falta gente.
- `collect`: los controles. Si fallan, no se sigue.
- `equity`: 962 variantes en 1,5 s y 5,9 MB de Parquet — contra ~90 minutos si se exportaran sus
  trades. Si tarda mucho más, está leyendo lo que no debe.

Manual: `docs/manual/18-variantes.md` (fabricar) y `docs/manual/19-wfc.md` (ejecutar, recoger y el
paso 17). El encadenador de las ~100 madres es `docs/manual/17-pipeline.md`.
