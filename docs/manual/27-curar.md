# 27. Curar una databank — escribir el veredicto con un filtro o con un nombre

### Qué pregunta responde

Ninguna: **ejecuta lo que tú decides.** Tienes una databank con miles de estrategias y un criterio
en Python, o una estrategia concreta que has visto en tu tabla y quieres fuera. Esto convierte esa
decisión en un `verdict.csv`, que `06-mover-estrategias.md` aplica dentro de SQX.

Dos modos: `--keep` con un filtro sobre las métricas exportadas, y `--drop` con uno o varios
nombres.

### Cuándo lo usas, y cuándo no

**Lo usas** entre dos tareas de SQX: la generación acabó, exportaste las métricas, y quieres que la
tarea siguiente lea sólo las que pasan tu corte. O cuando en tu tabla ves una que no quieres y la
apartas por su nombre. Se puede repetir tantas veces como cortes quieras: cada corte deja su propio
`verdict-HHMMSS.csv`, y al aplicarlo, su propio registro de lo que quitó.

**No lo usas** como sustituto de un análisis. Un filtro sobre métricas es un corte, no una prueba de
robustez; para eso están `02-filtros.md`, `07-montecarlo.md` y compañía, que escriben su propio
veredicto.

### Antes de empezar

1. **Las métricas exportadas.** `verdict.py` juzga
   `~/Desktop/AlgoData/metrics/<proyecto>/<databank>/metrics.csv` y nada más:
   `python3 -m sqx.export.export_metrics --project P --databank Results`. Si el CSV es viejo, el
   veredicto es viejo.
2. **Los ficheros `.sqx` en disco** en la instalación que nombras con `--role`: de ahí lee la
   identidad de cada estrategia. Una databank en `Auto-sync never` tiene el directorio vacío; el
   comando lo avisa (`identity from file on 0 of N`) y el paso siguiente se negará.
3. **No hace falta parar nada**: sólo lee. Para aplicar el veredicto sí
   (`06-mover-estrategias.md`).

### Cómo se ejecuta

```bash
# qué columnas puedes usar en el filtro
python3 -m sqx.curate.verdict --project Retester --databank Results --role conductor --columns

# un filtro: lo que NO lo cumple se marca DESCARTAR
python3 -m sqx.curate.verdict --project Retester --databank Results --role conductor \
    --keep "sharpe_ratio_is > 0.9"

# una estrategia concreta, por su nombre tal y como lo muestra SQX
python3 -m sqx.curate.verdict --project Retester --databank Results --role conductor \
    --drop "Strategy 10.16.68"
```

| flag | obligatorio | qué hace |
|---|---|---|
| `--project` | sí | proyecto tal y como aparece en SQX |
| `--databank` | sí | databank que se juzga |
| `--role` | no | instalación que tiene los ficheros: `master` (por defecto), `conductor` o `custodian` |
| `--keep` | uno de los tres | expresión de pandas sobre las columnas de `--columns`. `and`, `or`, `>`, `<=`, `==` |
| `--drop` | uno de los tres | uno o más nombres, entre comillas porque llevan espacio |
| `--columns` | uno de los tres | imprime los nombres de columna y no escribe nada |

Los nombres de columna son los de la exportación en minúsculas y con guiones bajos: `Net profit
(OOS)` es `net_profit_oos`, `# of trades (IS)` es `n_of_trades_is`. Instantáneo; no toca SQX.

### Qué produce

`~/Desktop/AlgoData/reports/<proyecto>/<databank>/<fecha>/curate/verdict-HHMMSS.csv`, uno por
ejecución, nunca sobrescribe. Columnas `strategy`, `verdict` (`MANTENER` o `DESCARTAR`), `reason`
(el filtro que falló, o `dropped by name`) e `identity` (SHA-256 de la definición de la estrategia,
leído del fichero).

### Cómo se lee el resultado

Salida real del 2026-09-23 sobre el conductor:

```
$ python3 -m sqx.curate.verdict --project Retester --databank Results --role conductor --keep "sharpe_ratio_is > 0.9"
Retester/Results: 66 judged, 34 kept, 32 DESCARTAR
  identity from file on 66 of 66 (/home/sergioguslw/Desktop/SQX_w1/user/projects/Retester/databanks/Results)
  /home/sergioguslw/Desktop/AlgoData/reports/Retester/Results/2026-09-23/curate/verdict-072117.csv
apply it: python3 -m sqx.curate.apply_verdict --project Retester --databank Results --verdict ... --role conductor   # then --apply, stopped
```

La primera línea son los números; la segunda te dice si la identidad se pudo leer de todos los
ficheros (si no es `N of N`, la databank no está en disco); la última es el comando que sigue.

### Un ejemplo completo

El ciclo entero, tal y como se corrió el 2026-09-23 sobre `Retester/Results` en el conductor:

```
$ python3 -m sqx.curate.verdict --project Retester --databank Results --role conductor --drop "Strategy 10.16.68"
Retester/Results: 34 judged, 33 kept, 1 DESCARTAR

$ bin/sqx-worker.sh --role conductor stop
$ python3 -m sqx.curate.apply_verdict --project Retester --databank Results --verdict .../verdict-073842.csv --role conductor --apply
SQX_w1 · Retester/Results: 34 strategies on disk
  the verdict drops 1, keeping 33
  identity checked on 1 of 1
  metrics of the dropped kept in .../reports/Retester/Results/2026-09-23/curate/rejected-073842.csv
  what was here is listed in .../reports/Retester/Results/2026-09-23/curate/before-073842.csv
Results: 34 → 33   deleted 1
start the conductor and the sync from files makes memory match: the next task reads 33.

$ bin/sqx-worker.sh --role conductor start      # SQX cargó 33 estrategias en Results
```

### Qué NO te dice

- **No te dice que el corte sea bueno.** Un filtro sobre métricas dentro de muestra selecciona lo
  que mejor se ajustó al pasado; si eso sobrevive fuera de muestra lo responden los análisis, no esto.
- **No sabe nada de RAM ni de SQX.** El veredicto es un CSV. Quien saca las estrategias de la
  memoria de SQX es `apply_verdict` con la instalación parada y el arranque siguiente.

### Si algo falla

- **`no metrics export at ...`** — no has exportado las métricas de esa databank, o la exportaste
  con otro nombre. `sqx.export.export_metrics` primero.
- **`not in the export: Strategy X`** — ese nombre no está en el CSV. Mira si lleva `(1)` al final:
  SQX renombra así cuando dos estrategias colisionan.
- **`identity from file on 0 of N`** — la databank no está en disco. `06-mover-estrategias.md`,
  sección «Antes de empezar», explica el `Auto-sync never`.
- **Un error de pandas al evaluar `--keep`** — una columna mal escrita. `--columns` te da los
  nombres exactos.
