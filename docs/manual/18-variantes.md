# 18. Variantes — fabricar las 5.000 estrategias del diseño

### Qué pregunta responde

SQX no tiene ningún comando que cambie los parámetros de una estrategia ya hecha. Ni uno. Así que
si quieres saber **qué pasaría si este indicador usara 61 periodos en vez de 67**, la única forma es
escribir un `.sqx` nuevo con ese 61 dentro y volver a testearlo.

Este comando es la fábrica. Le das el **diseño** que salió de SPP Ultra (etapa 15) y te escribe en
disco las cinco mil estrategias que ese diseño pide, más una tabla que dice qué combinación lleva
cada archivo.

No decide nada sobre trading. Decide **qué cinco mil combinaciones de entre cientos de miles** vale
la pena probar, y luego las escribe.

### Cuándo lo usas, y cuándo no

Úsalo cuando ya tienes el `design_brief_<Estrategia>.json` de SPP Ultra y el veredicto es
`proceed`. Si el veredicto es `noise`, la familia entera no se distingue del azar y fabricar cinco
mil variantes de ella es gastar medio giga y una tarde en medir ruido; el comando no te lo impide,
pero te enseña el veredicto en la primera línea.

**No lo uses para nada que tenga que ver con SQX en marcha.** Esto escribe archivos en una carpeta
de datos y ya. No abre SQX, no arranca el worker, no toca ningún databank y no lanza ningún build.
Cargar el lote y retestearlo es la etapa siguiente y hoy está parada.

**No te da ningún resultado.** Un archivo recién fabricado no se ha testeado: lleva dentro los
números del padre hasta que SQX lo vuelva a correr. Si lees el `.sqx` fabricado esperando ver el
resultado de la combinación nueva, vas a leer el del padre. Ver *Qué NO te dice*.

### Antes de empezar

1. **Que exista el diseño.** Es el archivo que escribe la etapa 15:

```bash
python3 -m studies.breakage.spp.report --project XAUUSD --databank SPP_IS
```

   Deja `~/Desktop/AlgoData/reports/XAUUSD/SPP_IS/<fecha>/design_brief_Strategy_17-9-39.json`.

2. **Que exista el export SPP del que salió ese diseño**, con sus CSV. La fábrica lo vuelve a leer,
   pero sólo cuatro columnas: de ahí saca los **centinelas**, que son combinaciones cuyo resultado
   SQX ya calculó.

3. **Sitio en disco.** Con el ajuste por defecto, 5.000 variantes ocupan **unos 505 MB**. Con
   `shape: minimal` bajan a 70 MB y con `full` suben a 631 MB.

4. No hace falta cerrar SQX ni parar nada. El comando no habla con SQX.

### Cómo se ejecuta

```bash
python3 -m sqx.variants.make \
  --brief ~/Desktop/AlgoData/reports/XAUUSD/SPP_IS/2026-09-21/design_brief_Strategy_17-9-39.json \
  --project XAUUSD
```

| flag | obligatorio | qué hace |
|---|---|---|
| `--brief` | sí | ruta del `design_brief_<Estrategia>.json`. De él salen los parámetros, sus niveles, los congelados y el objetivo de 5.000 |
| `--min-variants` | no | el mínimo de variantes distintas por madre; **1.000** si no se pone (`minimum.variants` en `sqx/variants/config.yaml`). Si el ±30 % no da tantas, los parámetros enteros se ensanchan en pasos del 5 % hasta llegar, como mucho a ±60 %, y si aun así no llega lo avisa con ⚠️ |
| `--project` | sí | nombre del proyecto, sólo para decidir la carpeta de salida |
| `--limit N` | no | fabrica sólo las N primeras filas. **El diseño no cambia**: se calculan las 5.000 y se escriben N. Es lo que se usa para probar la cadena con tres archivos antes de comprometerse a un lote entero |
| `--design-only` | no | calcula el diseño, escribe `plan.csv` y para. No escribe ningún `.sqx` |

Tarda **unos 50 segundos** en escribir las 5.000 con el ajuste por defecto (6 segundos con
`minimal`). El diseño en sí es instantáneo.

Los mandos que no son flags están en `sqx/variants/config.yaml`: la semilla, el radio de la
vecindad, cómo se reconstruye el rango de un parámetro congelado, cuántos centinelas, y **la forma
del archivo** (`minimal` / `no_profile` / `full`).

### Qué produce

Todo en `~/Desktop/AlgoData/strategyPermutations/<proyecto>/<Estrategia>/`:

| archivo | qué es |
|---|---|
| `plan.csv` | el diseño completo: una fila por combinación, con su estrato y su identificador. Siempre las 5.000, aunque fabriques 3 |
| `sqx/P00000.sqx` … | las estrategias. Una por fila fabricada |
| `manifest.parquet` | **la tabla que une todo el estudio.** Una fila por archivo que hay de verdad en `sqx/`, leída del archivo, no del plan |

**Se sobrescribe.** Hay un diseño vigente por estrategia y volver a correr el comando lo reemplaza,
para que no pueda existir la pregunta "¿cuál de estas cinco mil carpetas es la buena?". Si borras
`sqx/` a mano y vuelves a lanzar, el manifiesto se reconstruye con lo que haya.

### Cómo se lee el resultado

Lo primero que sale son los costes vigentes del símbolo — es obligatorio y sale siempre:

```
# XAUUSD — overrides to apply

SQX symbol: XAUUSD_DukasM1_Infinox   verified: 2026-09-03

- **spread**: use `10.0` points (SQX default `10.0`) — PROVISIONAL 2026-09-21 — SQX default, not an agreed Infinox figure. Owner will replace it.
- **commission**: use `8.0` $ per lot per side (SQX default `SizeBased 8`) — PROVISIONAL 2026-09-21 — ...
```

Luego el diseño:

```
Strategy 17.9.39  verdict=proceed  live space 3,888 tuples, with the frozen 19,440
  neighbourhood  budget   999  kept    57
  factorial      budget 3,939  kept 3,830
  coverage       budget 1,108  kept 1,108
  controls                    kept     5
  planned 5,000 of a target 5,000 (shortfall 0)
```

Se lee así:

- **`live space 3,888`** — con los niveles que eligió el diseño, **todas** las combinaciones
  posibles de los parámetros vivos son 3.888. Son menos que las 5.000 que se pedían: en esta
  estrategia el diseño no es una muestra, es la rejilla entera. `with the frozen 19,440` es lo
  mismo contando también los parámetros congelados, que sólo mueve el estrato de cobertura.
- **`budget` / `kept`** — lo que se le pidió a cada estrato y lo que aportó de nuevo. Aquí la
  vecindad sólo pudo dar 57 (varios parámetros tienen dos o tres niveles y la bola se acaba), y los
  942 que le sobraron pasaron al siguiente. El factorial pidió 3.939 y dio 3.830 porque 109 de sus
  combinaciones ya las había puesto otro estrato: **nunca se repite una combinación**.
- **`shortfall 0`** — se llegó a las 5.000. Si saliera un número positivo querría decir que el
  espacio de diseño se agotó antes; no es un error, es información.

Y por último la fabricación y la verificación:

```
wrote 3 .sqx as 'no_profile', 0.3 MB
{
  "planned": 3,
  "on_disk": 3,
  "missing": [],
  "unexpected": [],
  "tuple_mismatch": [],
  "duplicate_tuples": 0
}
```

**Esos cinco números son lo importante de todo el comando.** No los calcula mirando lo que quería
escribir: abre los archivos de vuelta, saca de dentro los parámetros que llevan y los compara.

| campo | qué significa si no es cero / vacío |
|---|---|
| `missing` | el plan tenía un identificador que no llegó a ningún archivo |
| `unexpected` | hay un archivo en la carpeta que el plan no pidió — típicamente restos de una tirada anterior |
| `tuple_mismatch` | **el peor de todos.** El archivo `P01234` no lleva dentro la combinación que el plan dice que lleva. El estudio entero se une por ese identificador |
| `duplicate_tuples` | dos archivos con la misma combinación. SQX los puede fundir en uno y quedarte con filas del manifiesto sin archivo detrás |

Si alguno falla, el comando **sale con error** y te dice que no cargues el lote. Todo vacío y a
cero es lo que tiene que salir siempre.

### Un ejemplo completo

Probar la cadena con tres archivos antes de comprometerse a cinco mil:

```bash
$ python3 -m sqx.variants.make \
    --brief ~/Desktop/AlgoData/reports/XAUUSD/SPP_IS/2026-09-21/design_brief_Strategy_17-9-39.json \
    --project XAUUSD --limit 3

[... los costes del símbolo ...]

Strategy 17.9.39  verdict=proceed  live space 3,888 tuples, with the frozen 19,440
  neighbourhood  budget   999  kept    57
  factorial      budget 3,939  kept 3,830
  coverage       budget 1,108  kept 1,108
  controls                    kept     5
  planned 5,000 of a target 5,000 (shortfall 0)

wrote 3 .sqx as 'no_profile', 0.3 MB
{
  "planned": 3,
  "on_disk": 3,
  "missing": [],
  "unexpected": [],
  "tuple_mismatch": [],
  "duplicate_tuples": 0
}

-> /home/sergioguslw/Desktop/AlgoData/strategyPermutations/XAUUSD/Strategy_17.9.39
```

Y mirando el manifiesto, que es lo que leerán todos los análisis de después:

```
variant_id  sqx_name                  stratum  origin  param_DICrossPeriod1  ...  canary_expect_netprofit  canary_expect_trades
P00000      Strategy 17.9.39 P00000   origin   True                    67.0                           NaN                  <NA>
P00001      Strategy 17.9.39 P00001   canary   False                   43.0                  38896.359375                  1077
P00002      Strategy 17.9.39 P00002   canary   False                   94.0                 -37128.390625                   843
```

Las tres primeras filas de cualquier lote son **controles**, no material de análisis:

- **`P00000` es la madre**, la estrategia original reescrita por la fábrica sin cambiarle nada. Si
  la reescritura rompiese algo, es la fila que deja de parecerse a la estrategia de la que salió.
  Y es la única que la etapa de borrado **se niega a tocar**.
- **`P00001` y `P00002` son centinelas**: combinaciones que SQX ya probó en el SPP, con el
  resultado que dio guardado al lado. Están elegidas en los extremos de la rejilla — la de más
  beneficio y la de más pérdida — a propósito: una cadena mal montada devuelve un número
  intermedio creíble, no devuelve el máximo de una rejilla de cuatro mil.
- Y después hay **una pareja por cada parámetro congelado**: la madre con ese parámetro movido a
  tope. Como el diseño lo congeló por haber demostrado que no mueve nada, esas filas tienen que
  volver **exactamente iguales a `P00000`**. Es la única comprobación de que congelarlo estaba bien.

Cuando la etapa siguiente recoja los resultados, si los centinelas no vuelven con lo esperado, la
cadena está rota en algún punto — y te enteras antes de mirar cinco mil resultados.

### Qué NO te dice

- **No dice si una variante es buena.** No hay ni un número de rendimiento aquí. Esto escribe
  archivos; medirlos es la etapa siguiente.
- **Un `.sqx` fabricado lleva dentro los resultados del padre** hasta que SQX lo vuelva a testear:
  las operaciones, la curva de equity y las estadísticas guardadas son las de la madre. Con la
  forma `no_profile` (la de por defecto) y con `full` eso es así. Consecuencia incómoda: **una
  variante que por lo que sea no llegue a correr no se ve vacía, se ve como la madre.** El
  manifiesto no puede detectarlo; los centinelas y el conteo del databank sí.
- **Las expectativas de los centinelas son sobre la muestra IS**, y sólo valen mientras la ventana
  dentro de muestra del retest sea la misma sobre la que corrió el SPP. Un retest configurado con
  otra historia falla todos los centinelas por un motivo que no tiene nada que ver con la fábrica.
- **Los niveles de un parámetro congelado son una reconstrucción, no un dato.** El diseño congela
  un parámetro y da su valor, no un rango; el estrato de cobertura necesita variarlo y el rango se
  rehace igual que lo hace SQX en sus propias permutaciones (±30 %; un *shift* no se mueve nunca). Es la
  suposición más discutible del módulo y está anotada como tal.
- **La rejilla cubre SIEMPRE al menos ±30 % del valor original** (dueño, 2026-09-26). Un parámetro
  entero toma **todos** los valores enteros de su rango (un período 14–26 son 13 valores); uno
  decimal, hasta 9 niveles que el SPP exploró. Y cada madre tiene **al menos 1.000 variantes
  distintas**: si el ±30 % no las contiene, los enteros se ensanchan solos (USDJPY `Strategy
  15.12.75`: de 216 a 1.105, EMA 12–28, salidas 7–19, fractal 3–7). Sobol reparte el estrato de
  cobertura por todo ese espacio. Los *shift* se quedan
  en su valor. Antes se quedaba en la meseta: EMA 20–27 y salidas 12–17, una franja.
- **Que el diseño contenga la combinación buena no está garantizado.** Una meseta que se haya movido
  más allá del ±30 % fuera de muestra se queda fuera.

### Si algo falla

**`not variables of this strategy: ['X']`** — el diseño nombra un parámetro que la estrategia madre
no tiene. Casi siempre es un `--brief` de una estrategia y un `.sqx` de otra: el `.sqx` se coge del
campo `source` del propio diseño, así que si has movido o editado carpetas del export a mano, se
descolocan. Vuelve a correr la etapa 15.

**`settings.xml does not carry both name fields`** — el `.sqx` madre no tiene los dos campos de
nombre donde se esperan. Es señal de que la versión de SQX que lo escribió no es la de esta caja;
no fuerces nada, dilo.

**`the batch on disk is not the batch that was planned`** — la verificación encontró algo. No
cargues ese lote en SQX. Mira cuál de los cuatro campos salió con contenido; lo normal es
`unexpected`, que son restos de una tirada anterior en `sqx/`.

**Un `FileNotFoundError` sobre `spp.parquet`** — falta el export SPP del que salió el diseño.
Los centinelas salen de ahí. Reexpórtalo con `python3 -m sqx.export.export_spp`.
