# 14. Walk-Forward Matrix — ¿reoptimizar sirve de algo?

### Qué pregunta responde

El cross-check **Walk-Forward Matrix** de SQX hace esto: coge un tramo de historia, optimiza los
parámetros ahí, y luego corre esos parámetros en el tramo siguiente, que no ha visto. Repite
avanzando. Y lo hace con 30 combinaciones distintas de "en cuántos tramos parto la historia" y "qué
porcentaje de cada tramo dejo fuera de muestra".

Este comando lee todo eso y contesta **una sola pregunta, que es la que justifica reoptimizar**:

> Cuando el optimizador encuentra unos parámetros que van muy bien en el tramo de optimización,
> ¿van también mejor en el tramo siguiente?

Si la respuesta es que sí, reoptimizar tiene sentido. Si es que no, estás gastando cómputo para
nada. Y si la respuesta es que **van peor**, reoptimizar te está eligiendo activamente lo que va a
fallar.

De paso mide la **deriva del óptimo**: cuántos parámetros cambia el optimizador de un tramo al
siguiente.

### Cuándo lo usas, y cuándo no

Úsalo con un databank donde hayas corrido el cross-check **Walk-Forward Matrix**, y después de
sacar los datos con `python3 -m sqx.export.export_wfm`.

**No te dice si la estrategia funciona.** Te dice si el *procedimiento de reoptimizarla* funciona.
Son cosas distintas: una estrategia puede ganar dinero con parámetros fijos y salir `blind` aquí.

**No sirve para sacar conclusiones generales con pocas estrategias.** El export de ejemplo tiene
dos. Dos no son una población.

### Antes de empezar

- **No toca SQX.** Puedes lanzarlo con la GUI abierta.
- Tiene que existir `~/Desktop/AlgoData/raw/<proyecto>/<databank>/<fecha>/wfm/` con sus cuatro CSV.
  Si no:

```bash
python3 -m sqx.export.export_wfm --project XAUUSD --databank WFM
```

### Cómo se ejecuta

```bash
python3 -m strategies.walkForwardMatrix.report --project XAUUSD --databank WFM
```

| flag | obligatorio | qué hace |
|---|---|---|
| `--project` | sí | nombre del proyecto tal y como aparece en SQX |
| `--databank` | no | carpeta del export, **con guiones bajos**. Por defecto `WFM` |
| `--day` | no | fecha del export. Por defecto, el más reciente |

Tarda unos segundos.

### Qué produce

En `~/Desktop/AlgoData/reports/<proyecto>/<databank>/<fecha>/`:

- **`walkforwardmatrix.md`** — el informe.
- **`cell_correlations.csv`** — la correlación de cada una de las 30 celdas, por si quieres mirarlas
  a mano.

### Cómo se lee el resultado

```
Strategy 1.19.29       blind     rho=+0.076 [-0.034, +0.193]  celdas= 30  deriva=70%
Strategy 4.33.46       perverse  rho=-0.505 [-0.683, -0.339]  celdas= 30  deriva=78%
```

**El veredicto** es una de tres:

| veredicto | qué significa | qué hacer |
|---|---|---|
| `predicts` | el intervalo está **por encima de cero**: lo que optimiza mejor va mejor después | reoptimizar sirve |
| `blind` | el intervalo **cruza cero**: la optimización no dice nada de lo que viene | reoptimizar no hace daño, pero es tirar cómputo |
| `perverse` | el intervalo está **por debajo de cero**: lo que optimiza mejor va **peor** después | reoptimizar te está eligiendo lo que va a fallar |

**El intervalo es lo importante, no el ρ.** Está calculado remuestreando **celdas**, no tramos. La
razón: las 30 celdas parten la *misma* historia de formas distintas, así que no son 30
observaciones independientes. Si se agruparan los 660 tramos en un solo número, el intervalo saldría
varias veces más estrecho y sería mentira.

**La deriva** es qué porcentaje de los parámetros cambia el optimizador de un tramo al siguiente. Un
70-78 % significa que cada reoptimización elige una estrategia sustancialmente distinta.

Y las dos cosas se leen juntas: si la superficie no tiene señal fuera de muestra, no hay nada que
sujete al optimizador en su sitio, y por eso salta tanto. No son dos hallazgos, es uno.

**La tabla de otras métricas** es el control:

```
| strategy         | metric        | rho    | low    | high   | share_negative |
| Strategy 4.33.46 | ReturnDDRatio | -0.505 | -0.683 | -0.339 | 0.933          |
| Strategy 4.33.46 | NetProfit     | -0.112 | -0.191 | -0.035 | 0.667          |
| Strategy 4.33.46 | SharpeRatio   | -0.213 | -0.306 | -0.124 | 0.733          |
| Strategy 4.33.46 | ProfitFactor  | -0.241 | -0.331 | -0.153 | 0.8            |
```

Negativa en las cuatro, y el 93 % de sus celdas negativas en la principal. Si solo saliera negativa
en una, sería una propiedad de esa métrica y no de la estrategia. **Mira siempre esta tabla antes
de creerte el veredicto.**

### Un ejemplo completo

```bash
$ python3 -m strategies.walkForwardMatrix.report --project XAUUSD --databank WFM --day 2026-09-10
Strategy 1.19.29       blind     rho=+0.076 [-0.034, +0.193]  celdas= 30  deriva=70%
Strategy 4.33.46       perverse  rho=-0.505 [-0.683, -0.339]  celdas= 30  deriva=78%

-> /home/sergioguslw/Desktop/AlgoData/reports/XAUUSD/WFM/2026-09-21
```

Lectura: **ninguna de las dos estrategias mejora reoptimizándose.** `1.19.29` es ciega — la
optimización no aporta información. `4.33.46` es peor que ciega: de sus 30 celdas, 28 dan
correlación negativa, en las cuatro métricas. Con esos números, el walk-forward sobre esta
estrategia no es un filtro de robustez: es una forma sistemática de elegir mal.

El informe empieza, antes de cualquier número, diciendo qué permite afirmar el export: cuántas
celdas, que las ventanas de ejecución dentro de una celda **no se solapan**, que las de optimización
se solapan un 79 %, y que todas las celdas reparten la misma historia. Eso está arriba a propósito:
quien lea el ρ primero va a interpretar el intervalo como un error estándar, y no lo es.

### Qué NO te dice

- **No dice si la estrategia gana dinero.** Dice si reoptimizarla ayuda.
- **No sabe lo que el optimizador descartó.** SQX guarda solo el ganador de cada tramo; las miles de
  combinaciones que probó dentro no se almacenan en ninguna parte. Así que no se puede saber si el
  segundo clasificado estaba pegado o lejísimos.
- **`perverse` tiene una explicación inocente que este módulo no puede descartar**: si el mercado
  alterna entre dos regímenes a un ritmo parecido al del tramo, optimizas en el régimen A y corres
  en el B, una y otra vez. Eso sería una propiedad del calendario, no de la estrategia. Para
  separarlo harían falta los regímenes clasificados o una estrategia de control conocida.
- **El intervalo es un suelo, no una medida.** Remuestrear celdas sigue tratando como independientes
  cosas que comparten historia. Lo que sostiene el veredicto no es el intervalo: es que el signo
  aguante en 28 de 30 celdas y en cuatro métricas.
- **`Ret/DD` crece con la longitud de la ventana**, y la matriz varía esa longitud a propósito en el
  eje `runs`. El informe avisa encima de esa tabla. Cualquier tendencia a lo largo de ese eje es en
  parte el propio eje.

### Si algo falla

- **`IndexError` buscando el export** — no hay carpeta con `wfm/` dentro. Corre `export_wfm` antes,
  o revisa los guiones bajos del databank.
- **Un ρ que sale `nan`** — casi seguro que estás leyendo `Fitness`. SQX lo guarda a **cero en todos
  los tramos**; solo existe de verdad a nivel de celda. Usa otra métrica.
- **Una celda que no aparece en el informe** — tenía menos de 5 tramos utilizables tras quitar los
  que corren más allá de los datos. Es correcto: no se correlaciona.
