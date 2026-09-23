# 21. Vocabulario — qué sabe expresar una instalación de SQX

### Qué pregunta responde

Antes de diseñar una estrategia hay que saber si SQX conoce la idea. "Quiero que el cierre cruce el
canal de Keltner" solo se puede construir si esta instalación tiene bloques de Keltner, y —esto es
lo que casi nadie comprueba— si alguno de sus **grupos aleatorios** los contiene.

Son dos preguntas distintas y la segunda es la que rompe las tardes. **Una plantilla no referencia
bloques: referencia grupos.** Un bloque que no está en ningún grupo existe, se ve en el listado, y
es inalcanzable desde una plantilla. Esta herramienta contesta las dos de un tirón, y además
compara instalaciones: si autoras en el conductor y construyes en el custodio, lo que no esté en
los dos no existe.

### Cuándo lo usas, y cuándo no

Úsalo **antes** de diseñar una plantilla o de encargar un bloque nuevo, y cuando llegue una
plantilla de otro ordenador y quieras saber si aquí se puede construir.

No sirve para saber si una idea es buena, ni si un bloque hace lo que su nombre promete. Solo dice
qué se puede expresar. Tampoco mira dentro de las plantillas ya escritas: eso es
`sqx/inspect/template_check.py`.

### Antes de empezar

Nada. Lee tres ficheros XML del disco, no arranca SQX y no necesita ningún worker levantado. Se
puede correr con la GUI del maestro abierta y trabajando, porque no escribe en ninguna instalación.

### Cómo se ejecuta

```bash
python3 -m sqx.inspect.vocabulary                          # resumen del conductor
python3 -m sqx.inspect.vocabulary keltner                  # buscar un indicador
python3 -m sqx.inspect.vocabulary --role master            # mirar otra instalación
python3 -m sqx.inspect.vocabulary --diff custodian         # qué le falta al custodio
python3 -m sqx.inspect.vocabulary --snapshot               # guardar el inventario
```

| flag | obligatorio | qué hace |
|---|---|---|
| `TERM` | no | subcadena a buscar, sin distinguir mayúsculas. Sin él, imprime el resumen |
| `--role` | no | `master`, `conductor` o `custodian`. Por defecto el conductor |
| `--diff ROLE` | no | dice qué le falta a esa instalación **contra** la de `--role` |
| `--snapshot` | no | además escribe el inventario bajo `AlgoData/templates/vocabulary/` |

Tarda menos de un segundo. Son 2,6 MB de XML y nada más.

### Qué produce

Por consola, siempre. Con `--snapshot`, además:

```
~/Desktop/AlgoData/templates/vocabulary/<instalacion>-<AAAA-MM-DD>.json    (~180 KB)
```

El fichero lleva la fecha en el nombre y **no se sobreescribe**: el valor está en la comparación
—qué le falta al custodio, qué cambió desde la semana pasada— y un único fichero "actual" no
contesta ninguna de las dos.

### Cómo se lee el resultado

El resumen sin argumentos, tal cual sale hoy:

```
SQX_w1: 849 native + 171 own blocks, 20 groups
  Condition pools (15): BookTriggers, BreakoutLong, CrossMAsAbove, CrossMAsBelow,
    DirectionalMomentumFilters, EntropyFilter, EntropyFilter2, GroupIBS, GroupRSIs, HurstLarger,
    MeanReversionFilters, PeriodsFastMABelow, StructuralBreakFilters, TrendRegimeFilters,
    VolatilityRegimeFilters
  Value pools     (4): BollingerBands_Lower, BreakoutRand, GroupMAs, RandomPrices
  EMPTY, unusable (1): RandConditions
```

Tres cosas que leer ahí:

- **849 nativos + 171 propios.** Los nativos vienen con SQX; los propios los autoraste tú y viven
  en `customBlocks.xml`.
- **Los pools son lo que una plantilla puede usar.** 15 de condición y 4 de valor. Los de valor son
  el cuello de botella: todas las formas de entrada por stop necesitan uno, y solo hay cuatro.
- **`EMPTY, unusable`.** `RandConditions` tiene cero items. Una plantilla que apunte un hueco ahí
  **no da error**: construye y no muestrea nada. Es un fallo mudo, y por eso sale en línea aparte.

### Un ejemplo completo

La pregunta real: *"quiero una estrategia en la que el cierre de una barra cruce por encima del
canal de Keltner"*. ¿Se puede?

```
$ python3 -m sqx.inspect.vocabulary keltner
KCBarClosesAboveUpper  [native/Conditions/Keltner Channel] -> boolean
    Bar closes above Keltner Channel(@Chart@#Period#, #Deviation#).Upper[#Shift#]
    pooled by: NO GROUP POOLS IT — unusable in a template
KCBarClosesAboveLower  [native/Conditions/Keltner Channel] -> boolean
    Bar closes above Keltner Channel(@Chart@#Period#, #Deviation#).Lower[#Shift#]
    pooled by: NO GROUP POOLS IT — unusable in a template
...
KeltnerChannel  [native/Values/Indicators] -> price
    Keltner Channel(@Chart@#Period#, #Deviation#).#Line#[#Shift#]
    pooled by: BollingerBands_Lower
MTKeltnerChannel  [native/Values/Indicators] -> price
    MT Keltner Channel(@Chart@#Period#, #Deviation#).#Line#[#Shift#]
    pooled by: BollingerBands_Lower
```

Salen **18 bloques**, y cada línea decide algo:

1. Hay una categoría nativa entera, `Conditions/Keltner Channel`, con 16 condiciones ya hechas.
   `KCBarClosesAboveUpper` es literalmente la idea. **No hay que autorar ningún bloque.**
2. Pero las 16 dicen `NO GROUP POOLS IT`. Existen y son inalcanzables: hace falta crear un grupo de
   condición que las contenga, con `sqx-random-group`. Ese, y no el bloque, es el trabajo real.
3. El indicador como **valor** sí está pooled, por `BollingerBands_Lower` — un grupo cuyo nombre
   engaña, porque contiene once bandas distintas, Keltner entre ellas. O sea que como *nivel de
   precio* el Keltner ya se puede usar hoy; como *condición de entrada*, todavía no.
4. `#Line#` en el display es un hueco tipado del propio bloque: banda superior, media o inferior.
   La ambigüedad no es del diseñador, la impone SQX, y hay que resolverla antes de generar.

Y la comparación entre instalaciones:

```
$ python3 -m sqx.inspect.vocabulary --diff custodian
SQX_w2 lacks, against SQX_w1:
  custom blocks (0): none
  groups (0): none
```

Las tres instalaciones de esta máquina tienen hoy el mismo vocabulario. Cuando eso deje de ser
cierto —y dejará de serlo en cuanto se autore algo en una sola— esta salida es la que evita
construir en el custodio una plantilla que solo existe en el conductor.

### Qué NO te dice

- **No dice si un bloque hace lo que su nombre dice.** `KCBarClosesAboveUpper` se lee y se cree;
  nadie ha verificado su cálculo.
- **No dice si una plantilla construirá.** Que los bloques existan y estén pooled es necesario y no
  suficiente: lo único que lo prueba es una construcción real que saque estrategias.
- **No mira dentro de las plantillas.** Si quieres saber si las estrategias que un proyecto
  construyó llevan de verdad los bloques que su plantilla fija, eso es `template_check.py`.
- **Un grupo con items no es un grupo bueno.** Cuenta cuántos hay, no si tienen sentido juntos:
  `BollingerBands_Lower` mezcla once bandas y la herramienta lo da por bueno.

### Si algo falla

`KeyError: 'custodian'` — `config/machine.yaml` no define ese rol. Es la respuesta honesta en una
máquina con solo dos instalaciones; usa `--role conductor`.

`FileNotFoundError` en `internal/web/SQWIZARD/...` — la ruta de `machine.yaml` no apunta a la
carpeta raíz de un SQX, la que contiene `internal/` y `user/`.
