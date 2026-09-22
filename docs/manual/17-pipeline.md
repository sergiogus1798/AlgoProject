# 17. Pipeline — mete cien estrategias, vuelve al cabo de unos días y lee los veredictos

### Qué pregunta responde

El estudio de robustez de una estrategia son siete pasos encadenados: leer su SPP, diseñar las
variantes, fabricarlas, correrlas en SQX, recoger los resultados, medir si la superficie aguanta
fuera de muestra, y dictar un veredicto. Hacer eso a mano para **una** estrategia es una tarde.
Para las ~100 madres de un databank son días de máquina.

Este comando lo hace solo. Le dices el proyecto, te vas, y cuando vuelves cada estrategia tiene su
veredicto escrito, y los gigas de variantes que hicieron falta para llegar a él ya no ocupan disco.

Y mientras corre **te deja mirar**: hay un fichero por estrategia que dice, en todo momento, en qué
paso va, por qué porcentaje y qué está haciendo. No tienes que adivinar si se ha colgado.

### Cuándo lo usas, y cuándo no

Úsalo cuando ya has corrido los **SPP en SQX** y los tienes exportados: ése es el punto de partida
de la cadena, y es lo único que tienes que hacer tú a mano.

**No lo uses para una sola estrategia que estás mirando con lupa.** Para eso corre cada etapa por
separado — están pensadas para poder lanzarse sueltas, y cada una te enseña su informe. El pipeline
es para cuando no quieres mirar.

**No es un sustituto de las etapas.** No calcula nada por su cuenta: las llama en orden, apunta lo
que pasa y se niega a seguir cuando falta algo. Si borras `pipeline/run.py`, todo lo demás sigue
funcionando a mano.

⚠️ **Hoy solo la primera etapa es de verdad.** Las otras cinco (diseño, fabricación, ejecución,
recogida y walk forward correlation) están siendo programadas por otros; mientras tanto, la cadena
corre con **marcadores de posición** que escriben cifras inventadas. Sirven para probar que el
encadenado funciona, **no para decidir nada**. Todo lo que escriben lleva dentro la marca
`"placeholder": true`. Cuando cada módulo real esté listo, se cambia **una línea** en
`pipeline/recipe.yaml` y esa etapa pasa a ser la de verdad.

### Antes de empezar

- **Los SPP, corridos y exportados.** Tiene que existir
  `~/Desktop/AlgoData/raw/<proyecto>/<databank>/<fecha>/spp/`. Si no:
  ```bash
  python3 -m sqx.export.export_spp --project XAUUSD --databank "SPP IS"
  ```
- **Sitio en disco.** Antes de cada estrategia el pipeline mira lo que pesa `AlgoData` y **se para
  si algo está por encima de su presupuesto**. Es aposta: lo que tiene que frenar una corrida de
  días es el presupuesto, no el disco lleno — cuando el disco se llena, la etapa que estaba
  escribiendo ya ha dejado medio fichero a medias. Para ver cómo estás:
  ```bash
  python3 -m perf.disk.report
  ```
  Los techos están en `perf/config.yaml`, en `disk.budget_gb`.
- **No toca SQX directamente.** Las etapas que sí lo harán todavía no existen. Hoy puedes lanzarlo
  con la GUI abierta.

### Cómo se ejecuta

```bash
python3 -m pipeline.run --project XAUUSD --databank SPP_IS
```

| flag | obligatorio | qué hace |
|---|---|---|
| `--project` | sí | nombre del proyecto tal y como aparece en SQX |
| `--databank` | no | carpeta del export, **con guiones bajos en vez de espacios**. Por defecto `SPP_IS` |
| `--strategy` | no | se puede repetir. Por defecto, **todas** las estrategias del export |
| `--day` | no | fecha del export a leer. Por defecto, la más reciente |
| `--report-day` | no | carpeta de informes en la que escribe sppUltra. Por defecto, hoy. Si reanudas una corrida al día siguiente, **pon aquí el día en que empezó**, o no encontrará los informes que ya hizo |
| `--asset` | no | nombre en `assets/`. Por defecto, el del proyecto. De ahí sale el sello de costes provisionales |
| `--sweep` | no | borra los datos de variantes al terminar cada madre. **Sin él no se borra nada** |

Puedes pararlo cuando quieras con Ctrl-C, o apagar el ordenador. Al volver a lanzarlo **continúa
donde estaba**: se salta lo que ya estaba hecho y retoma la etapa que quedó a medias.

### Qué produce

Una carpeta por estrategia en `~/Desktop/AlgoData/pipeline/<proyecto>/<estrategia>/`:

- **`state.json`** — el registro. En qué paso va, con qué porcentaje, qué dijo cada etapa y cuándo
  terminó. Pesa kilobytes y **no se borra nunca**, ni siquiera cuando se borran los datos que
  describe. Es lo que convierte el borrado en algo auditable en vez de en un agujero.
- **`state.json`** guarda además, de cada etapa, lo que esa etapa haya declarado: cuántas variantes
  salieron, cuántos canarios fallaron, y la **huella del diseño** (`brief_hash`) con la que se
  fabricaron. Esa huella es la que permite darse cuenta de que el diseño cambió por el camino.
- **`verdict.json`** — el veredicto, con los números en los que se apoya y, si sale `reject`, qué
  umbral falló y por qué existe ese umbral.
- Los ficheros que va dejando cada etapa.

El informe de la primera etapa va donde siempre:
`~/Desktop/AlgoData/reports/<proyecto>/<databank>/<fecha>/`.

### Cómo se lee el resultado

Esto es una corrida real sobre `Strategy 17.9.39`:

```
1 estrategias madre en XAUUSD/SPP_IS

[1/1] Strategy 17.9.39
  sppultra   python3 -m strategies.sppUltra.report --project XAUUSD --databank SPP_IS --strategy Strategy 17.9.39
   | Strategy 17.9.39         proceed  n_eff= 3,381  max 14.64 vs nulo 5.11  vivos=7 congelados=1
   | -> /home/sergioguslw/Desktop/AlgoData/reports/XAUUSD/SPP_IS/2026-09-21
  design     python3 -m pipeline.stubs.placeholder --stage design --work .../Strategy_17-9-39
   | PROGRESS 20 paso 1 de 5 (marcador de posición de design)
   | PROGRESS 40 paso 2 de 5 (marcador de posición de design)
   ...
  verdict    python3 -m pipeline.stages.verdict --work .../Strategy_17-9-39 --brief .../design_brief_Strategy_17-9-39.json
   | PROGRESS 20 leyendo los números de 4 umbrales
   | PROGRESS 60 13 cifras reunidas
   | PROGRESS 100 proceed
  -> verdict
```

Cada línea con sangría es **una etapa**, y debajo va lo que esa etapa imprime. Las líneas
`PROGRESS` son el porcentaje: van a parar al registro mientras la etapa corre, no al acabar.

Si quieres mirar desde otra terminal cómo va, sin tocar nada:

```bash
cat ~/Desktop/AlgoData/pipeline/XAUUSD/Strategy_17-9-39/state.json
```

```json
{ "strategy": "Strategy 17.9.39", "stage": "verdict",
  "stages": {
    "sppultra": { "progress": 100, "status": "-> .../reports/XAUUSD/SPP_IS/2026-09-21",
                  "done_at": "2026-09-21T18:31:13" },
    "build":    { "progress": 100, "status": "paso 5 de 5", "n": 5000, "bytes": 56500000,
                  "done_at": "2026-09-21T18:31:15" } },
  "costs_provisional": true }
```

**`progress` nunca baja.** Si lo ves parado, la etapa está tardando; si ves que retrocede, es un
fallo y el programa se para solo.

**`costs_provisional: true`** quiere decir que los costes con los que se ha calculado todo son los
que trae SQX por defecto, no los reales de tu bróker. Sale de `assets/XAUUSD.yaml`, y dejará de
salir cuando pongas ahí las cifras buenas.

Y el veredicto, cuando falla:

```json
{ "verdict": "reject",
  "failed": [ { "number": "wfc.rho", "value": 0.41, "limit": 0.9, "bound": "min",
                "why": "below this the in-sample surface does not order the out-of-sample one" } ] }
```

### Los umbrales son tuyos, y cambiarlos es gratis

Están en `pipeline/config.yaml`, bajo `verdict.rules`. Cada regla es un número, un límite y la
razón por la que ese límite existe.

**No todo número con un límite es un umbral.** Los canarios, por ejemplo, no están ahí: un canario
fallido no quiere decir que la estrategia sea mala, quiere decir que la medición no vale. Eso es
una **puerta**, vive en `pipeline/recipe.yaml` y para la corrida, en vez de producir un veredicto
que nadie debería leer. La diferencia es siempre la misma pregunta: ¿el número dice *esta
estrategia no da la talla*, o dice *esta medición no significa nada*?

**Cambiar un umbral no obliga a repetir nada.** El pipeline guarda los números, no los juicios: al
volver a lanzarlo, las seis primeras etapas se saltan y solo se vuelve a dictar el veredicto. Así
se ve:

```
  sppultra   hecho, se salta
  design     hecho, se salta
  build      hecho, se salta
  ran        hecho, se salta
  collected  hecho, se salta
  wfc        hecho, se salta
  verdict    python3 -m pipeline.stages.verdict ...
   | PROGRESS 100 reject, falla wfc.rho
```

Puedes dictar el veredicto suelto, sin pasar por el pipeline:

```bash
python3 -m pipeline.stages.verdict \
  --work ~/Desktop/AlgoData/pipeline/XAUUSD/Strategy_17-9-39 \
  --brief ~/Desktop/AlgoData/reports/XAUUSD/SPP_IS/2026-09-21/design_brief_Strategy_17-9-39.json
```

### Borrar las variantes, con red

Las 5.000 variantes de una estrategia pesan gigas y no sirven para nada una vez medidas. El
pipeline las borra si se lo pides con `--sweep`, o después, a mano:

```bash
python3 -m pipeline.cleanup --project XAUUSD --strategy "Strategy 17.9.39"
```

```
liberaría      1.204.531.200 B  pipeline/XAUUSD/Strategy_17-9-39/variants
1.204.531.200 B en 1 rutas  (nada borrado: falta --apply)
```

**Sin `--apply` no borra nada**, solo te dice cuánto liberaría. Y antes de borrar comprueba tres
cosas, y si falla cualquiera se niega:

1. Que la etapa de recogida haya **terminado**.
2. Que cada fichero exportado **siga siendo exactamente el que se exportó** — lo vuelve a hashear.
   Si no coincide:
   ```
   Strategy 0.0.1: el export ya no coincide con su hash: .../metrics_placeholder.json
   ```
3. Que lo que va a borrar esté **dentro de la carpeta de esa estrategia**. Si el registro propone
   otra cosa, se para:
   ```
   Strategy 0.0.1: el registro propone borrar fuera de su carpeta: .../raw/XAUUSD/SPP_IS
   ```

⚠️ **La estrategia madre no se borra nunca.** No es una promesa: la madre vive en el databank de
SQX y en `raw/`, y el barrido no puede salir de `pipeline/<proyecto>/<estrategia>/`. No hay ruta
por la que pueda llegar hasta ella.

Lo borrado queda apuntado en el registro, con su tamaño y la hora. El registro sobrevive; los datos
no. Y `python3 -m perf.disk.report` lee esos registros para decirte qué más se puede soltar.

### Un ejemplo completo

```bash
# 1. Mira cómo está el disco antes de empezar
python3 -m perf.disk.report

# 2. Lanza las cinco madres del databank, borrando según termina cada una
python3 -m pipeline.run --project XAUUSD --databank SPP_IS --sweep

# 3. Al día siguiente, mira los veredictos
grep -h '"verdict"' ~/Desktop/AlgoData/pipeline/XAUUSD/*/verdict.json
```

Si se corta a mitad, se relanza el mismo comando y sigue donde estaba.

### Qué NO te dice

- **No te dice que la estrategia sea buena.** Dice que pasó unos umbrales que has puesto tú. Los
  números de los que salen esos umbrales están en `verdict.json`, y son lo que hay que mirar.
- **Hoy no te dice casi nada**, porque cinco de las siete etapas son marcadores de posición con
  cifras inventadas. Un `proceed` de hoy no significa nada; lo que hoy está probado es el
  encadenado.
- **`costs_provisional: true` invalida cualquier cifra de dinero.** Mientras esté ahí, los costes
  son los de por defecto de SQX.
- **No vigila SQX.** Si SQX se queda colgado durante una etapa, el pipeline se queda esperando; el
  registro seguirá diciendo el último porcentaje que le llegó.

### Si algo falla

**`AlgoData 7.2 GB de 60 GB. snapshots 4.8/2 GB. Libera espacio o sube el presupuesto`**
El pipeline se ha negado a empezar porque una rama de `AlgoData` está por encima de su techo.
Mira qué se puede soltar con `python3 -m perf.disk.report`, o sube el número en `perf/config.yaml`.
Es la puerta que existe para que una corrida de días no acabe con el disco lleno.

**`sppultra: falta la entrada raw/XAUUSD/SPP_IS`**
No está el export. Córrelo (ver *Antes de empezar*) y relanza.

**`design: terminó sin escribir pipeline/XAUUSD/.../design.json`**
La etapa acabó sin error pero no dejó lo que tenía que dejar. El pipeline no la da por buena: un
código de salida cero no es prueba de nada.

**`build: progress went 80 -> 40, it is monotonic`**
Un fallo de la etapa, no tuyo. Apúntalo y dilo.

**`sppultra: design_brief_….json ha cambiado desde que se registró (brief_hash d081df20… -> e6d1be4a…)`**
El diseño de las variantes ha cambiado **después** de haberlas fabricado. Todo lo que viene detrás
estaría midiendo un diseño contra los números de otro, y eso no da error: da resultados que parecen
buenos. Por eso se para. O borras la carpeta de esa estrategia en `~/Desktop/AlgoData/pipeline/`
para rehacerla entera, o recuperas el brief anterior.

**`ran: canaries_failed = 3. un canario fallido significa que las variantes que corrió SQX no son
las que se escribieron…`**
No es que la estrategia sea mala: es que el experimento no vale. Las variantes que volvieron de SQX
no son las que se le dieron — renombrado en colisión, un databank que se sincronizó por medio, algo
así. Se para ahí aposta, para no gastar horas midiendo algo que no significa nada.

**`assets/XAUUSD.yaml: spread, commission sin valor acordado`**
El activo no tiene costes decididos y no se arranca sin ellos. Corre
`python3 -m core.assets XAUUSD` para ver qué falta. Ojo: un valor **provisional** no bloquea —
es una decisión tuya, y el registro la sella con `costs_provisional: true`.

### Comprobar que el pipeline sigue siendo un pipeline

```bash
python3 -m pipeline.verify.selftest
```

Monta una estrategia de mentira, la corre entera, y comprueba dos cosas: que el progreso se escribe
**mientras** la etapa corre y nunca baja, y que si matas el proceso a mitad el registro no se
corrompe y al relanzar continúa donde estaba. Tarda unos 15 segundos y termina en `0 problemas`.
