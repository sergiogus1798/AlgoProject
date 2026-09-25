# 33. Configurar los SPP en SQX — las dos tareas de permutación

> **Ojo con el nombre.** Esta página es la mitad de SQX del paso 15: **dejar las tareas `SPP IS` y
> `SPP OOS` configuradas** dentro de un custom project. Sacar el perfil que producen es
> `08-spp.md`, el diccionario de sus columnas es `09-diccionario-spp.md`, y leerlo para decidir si
> una estrategia merece 5.000 variantes es `15-sppultra.md` (paso 16).

### Qué pregunta responde

El SPP —*System Parameter Permutation*— mueve **cada parámetro de la estrategia** arriba y abajo y
vuelve a correr el backtest en cada combinación. Lo que queda es un mapa: si el beneficio sólo
existe en el valor exacto que salió del generador, la estrategia está clavada en un pico y no hay
nada debajo; si la vecindad entera gana dinero, hay una meseta.

Ese mapa es el `optimizationProfile.bin` que cada `.sqx` del databank de salida se lleva dentro, y
es lo único que `studies/breakage/spp/` sabe leer.

### ⚠️ El SPP es `OptProfileSysParamPermutation`, no `SequentialOptimization`

Los dos viven **en el mismo bloque** de crosschecks, los dos hablan de permutar parámetros, y sólo
uno es el SPP. Encender el otro costó 47 núcleos durante 91 minutos y no produjo perfil ninguno
(medido el 2026-09-22, está en `knowhow/sqx-drive/spp-task-type.md`). El comando enciende el correcto y no
te deja elegir: ésa es media razón de que exista.

### Cuándo lo usas, y cuándo no

**Úsalo** cuando ya tienes un custom project con una población cribada dentro — lo que sobrevive al
MC Retest— y quieres el mapa de parámetros de cada superviviente.

**No lo uses** sobre una población sin cribar. Un SPP son miles de backtests **por estrategia**: es
con diferencia el paso más caro de la cadena, y sobre diez mil estrategias no termina nunca.

**No lo uses** para filtrar. Este comando apaga los cuatro chequeos de aceptación del propio SPP
(`ProfitOptPct` y compañía) a propósito: si SQX borra lo que no le gusta, `sppUltra` está leyendo la
superficie de una población ya seleccionada, sin saberlo.

### Las dos tareas, y por qué no se comparan entre sí

| tarea | ventana | qué es |
|---|---|---|
| `SPP IS` | `build` (2008–2017 en XAUUSD) | la vecindad en la muestra con la que se construyó |
| `SPP OOS` | `oos1` (2018–2022) | la misma vecindad leída fuera de muestra |

Parecen un antes y un después y **no lo son**: medido el 2026-09-19 sobre `Strategy 17.9.39`, el SPP
de IS y el de OOS de la misma estrategia, con ajustes idénticos, comparten **6 tuplas de ~11.600**.
SQX no recorre la misma rejilla dos veces. Son dos lecturas del mismo entorno, y ése es exactamente
el motivo de que exista la fábrica de variantes del paso 16.5: para comparar hay que fabricar las
tuplas uno mismo.

### Antes de empezar

- El proyecto tiene que existir y ser **custom** (`sqx.projects.builder`), clonado del donante
  congelado, que es el que trae las tareas `SPP IS` y `SPP OOS` con esos títulos. Una tarea que no
  esté se reporta con `⊘` y no se inventa.
- El `.cfx` **no puede estar abierto** por una instancia de SQX: la reescribe al salir y se lleva el
  cambio por delante sin decir nada (regla dura 4). El comando lo comprueba y se niega.
- Costes pactados: `python3 -m core.assets <SIMBOLO>` tiene que salir en verde (regla dura 5).

No toca SQX ni ningún worker: sólo lee y reescribe un fichero. Tarda menos de un segundo.

### Cómo se ejecuta

```bash
python3 -m core.assets XAUUSD                       # preflight, BLOQUEANTE
python3 -m sqx.projects.spp XAUUSD \
    --cfx ~/Desktop/SQX_w2/user/projects/XAUUSD_estudio/project.cfx \
    --input "MCR 8 Stress"
```

| flag | obligatorio | qué hace |
|---|---|---|
| `<SIMBOLO>` | sí | el activo, para sus costes y sus ventanas |
| `--cfx` | sí | el `project.cfx` del custom project |
| `--input` | sí | el databank que lee la **primera** tarea. No hay valor por defecto: son los supervivientes del paso anterior, y adivinarlo es correr el paso más caro sobre la población equivocada |
| `--json` | no | la misma información como JSON, para encadenar |

La segunda tarea lee lo que escribió la primera. Con la aceptación apagada no se cae nadie, así que
la población entera llega también a la lectura de fuera de muestra.

### Qué produce

Reescribe **en el sitio** el `project.cfx` que le des: las dos tareas quedan activas, con el
crosscheck encendido, la rejilla escrita, las condiciones apagadas y sus databanks encadenados.
No escribe nada más y no crea copia de seguridad — el `.cfx` es del proyecto, y para volver atrás se
clona otra vez del donante.

### Cómo se lee el resultado

```
XAUUSD  XAUUSD  <- MCR 8 Stress
  ✓ SPP IS   build 2008.01.01→2017.12.31  ±35 % en 18 pasos, tope 15,000 permutaciones, precision 1
      MCR 8 Stress → SPP IS   19 condicion(es) y 2 chequeo(s) del SPP apagados
  ✓ SPP OOS  oos1 2018.01.01→2022.12.31  ±35 % en 18 pasos, tope 15,000 permutaciones, precision 1
      SPP IS → SPP OOS   19 condicion(es) y 2 chequeo(s) del SPP apagados

El perfil lo guarda cada .sqx del databank de salida: sacalo con sqx/export/export_spp.py y leelo
con studies/breakage/spp/.
⚠️ Una SPP a la vez por instalacion: el perfil ocupa decenas de GB mientras se construye.
```

Qué mirar, línea a línea:

- **`±35 % en 18 pasos`** — cuánto se mueve cada parámetro y con qué finura. Un paso son ~4 %, que es
  el default del dueño. Los 12 pasos sobre ±30 que trae el donante son 5 % por paso y son gruesos.
- **`tope 15,000 permutaciones`** — ⚠️ la línea más importante. El donante trae `1000000001`, que es
  el centinela de SQX para **exhaustivo**: todas las combinaciones de todos los parámetros. Eso no es
  una tarea larga, es una tarea sin final. El comando lo escribe siempre, nunca lo hereda.
- **`19 condicion(es) ... apagadas`** — si sale `0` en las dos, el proyecto ya venía con ellas
  apagadas; merece comprobarlo, porque lo normal en un clon del donante es 19.
- **`2 chequeo(s) del SPP apagados`** — los `Eval*Check` del propio crosscheck, que son su aceptación
  interna. Con ellos vivos, SQX borra las estrategias cuyo mapa no le gusta.
- **`precision 1`** — el backtest corre al timeframe de la tarea, no a 1 minuto. ⚠️ Esto **diverge**
  de `precision.default: 2` de la doctrina, y es a propósito: son miles de backtests por estrategia y
  a 1 minuto no acaba. Es lo que llevan las tareas del maestro. Está anotado en `OPEN.md` como
  decisión pendiente del dueño.
- Un **`⊘`** en vez del `✓` significa que el proyecto no lleva esa tarea: se clonó sin ella.
- Un **`⚠️ esta tarea corre ademas: …`** significa que ese `.cfx` no pasó por la doctrina y va a
  correr otros crosschecks a la vez. Se arregla clonando con `sqx.projects.builder`.

### Un ejemplo completo

```bash
# 1. el proyecto ya existe, con su población cribada en "MCR 8 Stress"
python3 -m core.assets XAUUSD
python3 -m sqx.projects.spp XAUUSD --cfx ~/Desktop/SQX_w2/user/projects/XAUUSD_estudio/project.cfx \
    --input "MCR 8 Stress"

# 2. correrlo en el custodio, UNA sola cosa a la vez
bin/sqx-worker.sh --role custodian start
python3 -c "from core import worker; worker.call('-project action=start name=XAUUSD_estudio','custodian')"
# ... termina ...
bin/sqx-worker.sh --role custodian stop

# 3. sacar los perfiles y leerlos (pasos 15→16)
python3 -m sqx.export.export_spp --project XAUUSD_estudio --databank "SPP IS" --role custodian
python3 -m studies.breakage.spp.report --project XAUUSD_estudio --databank SPP_IS
```

### Qué NO te dice

- **No dice si la estrategia es buena.** Dice cómo se comporta su vecindad de parámetros. Una
  estrategia mala puede tener una meseta preciosa de resultados malos.
- **No compara IS con OOS.** Las dos rejillas no coinciden (6 tuplas de 11.600); quien compare
  columna con columna entre los dos databanks está comparando estrategias distintas.
- **No filtra nada**, por diseño. El veredicto lo da `studies/breakage/spp/` y se aplica con
  `/curate`.
- **El conteo `permutations` del perfil no es el número de filas.** Medido: un perfil que dice 2.533
  exporta 3.940 filas. Para saber cuántas hay de verdad, `len(results)`.

### Si algo falla

| lo que sale | qué significa |
|---|---|
| `el custodian tiene este proyecto abierto…` | hay una instancia levantada sobre ese `.cfx`. Párala y repite; si no, SQX se come el cambio al salir |
| `⊘ SPP IS NO configurada — el proyecto no lleva la tarea SPP IS` | el clon se hizo sin esa tarea. Vuelve a clonar con `--tasks Retest` y el `--only` que la incluya |
| `XAUUSD: … sin valor pactado` | falta un coste en `assets/symbols/`. Pregúntale al dueño (regla dura 5) |
| el run termina en segundos y no hay perfil | señal clásica de que se corrió sobre una variante fabricada sin parámetros reales. Un SPP de verdad tarda media hora larga por estrategia y **no dice nada** mientras tanto: la señal honesta de que trabaja es la memoria de la JVM subiendo |
