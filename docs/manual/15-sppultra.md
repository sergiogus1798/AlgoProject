# 15. SPP Ultra — ¿merece esta estrategia las 5.000 variantes?

### Qué pregunta responde

Cuando pasas una estrategia por el cross-check **Sys. Param Permutation**, SQX prueba miles de
combinaciones de sus parámetros y te enseña unos histogramas. Este comando lee esa tirada entera y
contesta tres cosas que la pantalla de SQX no dice:

1. **Qué parámetros mueven de verdad el resultado** y cuáles están muertos.
2. **Dónde está la meseta** de cada parámetro — la zona ancha donde funciona, que no es lo mismo que
   el punto donde funciona mejor.
3. **Si toda la familia es ruido.** Si pruebas 3.000 combinaciones de algo que no sirve para nada,
   la mejor de las 3.000 va a parecer buena igualmente. Esto calcula cuánto de buena parecería por
   pura suerte, y compara.

Y deja preparado el **diseño de las 5.000 variantes** para la siguiente etapa.

### Cuándo lo usas, y cuándo no

Úsalo con un databank en el que hayas corrido el cross-check SPP **con la opción *"Don't store data
for 3D charts in Optimization profile"* desactivada**, y después de haber sacado los datos con
`python3 -m sqx.export.export_spp`.

**No sirve para comparar dentro y fuera de muestra.** Y no es una limitación del programa: es que
los datos no dan para eso. Dos tiradas SPP, una en IS y otra en OOS, **no se pueden emparejar**.
Medido el 2026-09-19 sobre `Strategy 17.9.39`, con la misma estrategia y ajustes idénticos: de unas
11.600 combinaciones en cada tirada, **solo 6 coinciden**. El muestreador sortea, y sortea distinto
cada vez. Ésa es exactamente la razón por la que existen las 5.000 variantes fabricadas a mano.

### Antes de empezar

- **No toca SQX.** Lee archivos ya exportados, así que puedes lanzarlo con la GUI abierta y mientras
  haya un build corriendo.
- Tiene que existir el export: `~/Desktop/AlgoData/raw/<proyecto>/<databank>/<fecha>/spp/` con sus
  cinco CSV. Si no está, córrelo antes:

```bash
python3 -m sqx.export.export_spp --project XAUUSD --databank "SPP IS"
```

### Cómo se ejecuta

```bash
python3 -m strategies.sppUltra.report --project XAUUSD --databank SPP_IS
```

| flag | obligatorio | qué hace |
|---|---|---|
| `--project` | sí | nombre del proyecto tal y como aparece en SQX |
| `--databank` | no | carpeta del export, **con guiones bajos en vez de espacios**. Por defecto `SPP_IS` |
| `--day` | no | fecha del export a leer. Por defecto, el más reciente que tenga tabla SPP |
| `--strategy` | no | se puede repetir. Por defecto, todas las estrategias del export |

Tarda unos segundos por estrategia.

### Qué produce

Todo va a `~/Desktop/AlgoData/reports/<proyecto>/<databank>/<fecha>/`:

- **`sppultra.md`** — el informe, una sección por estrategia.
- **`design_brief_<Estrategia>.json`** — uno por estrategia. Es el archivo que lee la etapa de
  fabricación de variantes. No lo edites a mano: se regenera cada vez que corres el comando.

Los informes **se acumulan** (una carpeta por fecha) y no se borra nada.

### Cómo se lee el resultado

En pantalla te sale una línea por estrategia:

```
Strategy 1.19.29         proceed  n_eff= 4,283  max 17.01 vs nulo 10.04  vivos=10 congelados=0
Strategy 17.9.39         proceed  n_eff= 3,381  max 14.64 vs nulo  5.11  vivos=7  congelados=1
Strategy 23.16.37        proceed  n_eff= 4,300  max  8.44 vs nulo  5.35  vivos=10 congelados=1
Strategy 4.33.46         proceed  n_eff= 4,002  max 13.93 vs nulo  8.01  vivos=9  congelados=0
Strategy 41.5.25         proceed  n_eff= 4,320  max  7.58 vs nulo  4.85  vivos=12 congelados=0
```

- **`max` contra `nulo`** es el veredicto. `nulo` es lo que habría sacado la mejor de esas mismas
  combinaciones si ningún parámetro hiciera nada. `proceed` es que lo supera; `noise` es que no, y
  entonces **no hace falta seguir con esa estrategia**: te ahorras las 5.000 variantes.
- **`n_eff`** son las combinaciones con un resultado *distinto*. Siempre es menor que el número de
  filas, porque los parámetros muertos repiten el mismo backtest muchas veces. Es este número el que
  se usa para el umbral, no el de filas.
- **`congelados`** son los parámetros que el test de duplicados demostró que no hacen nada. Salen
  del diseño de variantes.

Dentro del informe, la tabla que más se mira:

```
| parámetro          | ReturnDDRatio | NetProfit | NumberOfTrades | grupos | idénticos | inerte |
|--------------------|---------------|-----------|----------------|--------|-----------|--------|
| DICrossPeriod1     | 0.2929        | 0.4702    | 0.2698         | 224    | 0         |        |
| DICrossShift1      | 0.2359        | 0.0763    | 0.7847         | 189    | 0         |        |
| ExitAfterBars1     | 0.0264        | 0.0238    | 0.0691         | 184    | 0         |        |
| CBlock_SqzMmnInt21 | 0.0173        | 0.0193    | 0.0197         | 217    | 217       | sí     |
| IsBars1            | 0.0016        | 0.0007    | 0.0103         | 188    | 1         |        |
```

Léela así, y en este orden:

- **`grupos` e `idénticos`** es la prueba. `grupos` son los pares de combinaciones que solo se
  diferencian en ese parámetro; `idénticos` son los que además dieron **exactamente el mismo
  resultado**. `CBlock_SqzMmnInt21`: 217 de 217. Ese parámetro no hace nada, está demostrado, y se
  congela.
- **Las columnas de números (η²)** son "qué porcentaje de la variación explica este parámetro". Y
  hay que leerlas con cuidado: fíjate en que `DICrossShift1` explica el **7,6 %** del beneficio neto
  pero el **78,5 %** del número de operaciones. **El mismo parámetro, dos respuestas muy distintas
  según qué métrica mires.** Por eso la tabla enseña varias y no una.
- **Por qué no se congela por η²**: mira `CBlock_SqzMmnInt21` otra vez. Está demostrado que no hace
  nada, y sin embargo su η² es 0,0173, más alto que el de `IsBars1` (0,0016), que sí hace cosas. Eso
  pasa porque el SPP sortea desequilibrado: a cada valor de un parámetro muerto le tocaron mezclas
  distintas de los demás, y esa diferencia se cuela en el η². **Fiarse del η² para congelar habría
  dejado dentro un parámetro muerto y fuera uno vivo.**

Y la tabla de mesetas:

```
| parámetro      | from | to   | width | center | argmax | original |
|----------------|------|------|-------|--------|--------|----------|
| DICrossPeriod1 | 40.0 | 46.0 | 3     | 43.0   | 43.0   | 67.0     |
| ExitAfterBars1 | 9.0  | 13.0 | 5     | 11.0   | 12.0   | 13.0     |
```

`center` es el **punto medio de la meseta**, no el mejor punto. Es lo que hace el `BestValue` del
propio SQX. Cuando `width` es 1 no hay meseta: hay un pico, y el brief lo marca con `"spike": true`.
Un parámetro que hay que acertar clavado no es un parámetro que puedas poner en real.

### Un ejemplo completo

```bash
$ python3 -m strategies.sppUltra.report --project XAUUSD --databank SPP_IS --day 2026-09-10
Strategy 1.19.29         proceed  n_eff= 4,283  max 17.01 vs nulo 10.04  vivos=10 congelados=0
Strategy 17.9.39         proceed  n_eff= 3,381  max 14.64 vs nulo 5.11  vivos=7 congelados=1
Strategy 23.16.37        proceed  n_eff= 4,300  max 8.44 vs nulo 5.35  vivos=10 congelados=1
Strategy 4.33.46         proceed  n_eff= 4,002  max 13.93 vs nulo 8.01  vivos=9 congelados=0
Strategy 41.5.25         proceed  n_eff= 4,320  max 7.58 vs nulo 4.85  vivos=12 congelados=0

-> /home/sergioguslw/Desktop/AlgoData/reports/XAUUSD/SPP_IS/2026-09-21
```

Las cinco pasan el filtro de ruido. `Strategy 17.9.39` es la que lo pasa más holgada (14,64 contra
5,11, casi tres veces) y además es la única con un parámetro congelado además de `23.16.37`.

El brief que deja para esa estrategia dice, en resumen: siete parámetros vivos, uno congelado
(`CBlock_SqzMmnInt21` fijo en 20), y los niveles a probar en cada eje — por ejemplo
`DICrossPeriod1` en `[40, 43, 46, 49, 52, 58, 61, 64, 67]`, que es un abanico centrado en la meseta
(43) pero **estirado hasta 67 para que quepa el valor original de la estrategia**. Eso es a
propósito: si la meseta se ha movido, tiene que poder verse.

### Qué NO te dice

- **No dice que la estrategia funcione.** Dice que su superficie de parámetros contiene más de lo
  que contendría buscando en ruido. Es un filtro para no gastar cómputo, no una aprobación.
- **No compara dentro con fuera de muestra**, por lo de las 6 combinaciones en común. Cualquier cosa
  que leas aquí es dentro de muestra.
- **El η² no es una medida limpia** en esta tirada, por el muestreo desequilibrado. Sirve para
  repartir niveles entre los parámetros vivos. No lo uses para decidir que algo no importa: para eso
  están las columnas `grupos` e `idénticos`.
- **La meseta es una estimación hecha con un solo tramo de historia.** Que un parámetro tenga una
  meseta ancha en 2008-2017 no significa que la tenga en 2018-2022. Precisamente eso es lo que va a
  medir la etapa siguiente.
- **`Ret/DD` crece con la longitud de la ventana.** Aquí da igual porque nunca se comparan dos
  ventanas, pero **no reutilices esta configuración para leer dos periodos distintos** sin cambiar
  la métrica.

### Si algo falla

- **`IndexError` al buscar el export** — no hay ninguna carpeta con `spp/` dentro de
  `raw/<proyecto>/<databank>/`. Corre `sqx.export.export_spp` primero, o revisa que el databank
  lleve guiones bajos (`SPP_IS`, no `SPP IS`).
- **`KeyError` con el nombre de una estrategia** — el nombre tiene que ser exactamente el que usa
  SQX, espacios y puntos incluidos: `Strategy 17.9.39`.
- **Una estrategia con `congelados=0` y todos los `grupos` a 0** — el muestreador no llegó a generar
  pares que se diferencien en un solo parámetro. No es que no haya parámetros muertos: es que no hay
  pruebas. Hace falta más presupuesto de permutaciones.
