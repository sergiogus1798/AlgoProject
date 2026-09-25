## 25. Actualizar los datos — el botón "Update all", automatizado y con red

### Qué pregunta responde

Ninguna: esto no analiza nada. Hace una cosa y la hace con cuidado — descarga histórico nuevo en el
maestro, igual que el botón **"Update all"** de la GUI, y después deja `assets/_policy.yaml`
diciendo la verdad sobre hasta dónde llega cada feed.

Las dos mitades van juntas a propósito. Actualizar sin refrescar las fechas deja el proyecto
creyendo que tu histórico acaba donde acababa hace meses.

### Cuándo lo usas, y cuándo no

**Lo usas** cuando quieras la descarga desatendida — de madrugada, sin nadie delante — o cuando
prefieras que el refresco de fechas vaya encadenado y no se te olvide.

**No lo uses** si sólo quieres refrescar las fechas sin descargar nada. Para eso está
`python3 -m core.assets --dataranges`, que pregunta al conductor, no toca el maestro y **es seguro
con tu GUI abierta**.

Y no lo uses con la GUI del maestro levantada, porque no te va a dejar.

### Antes de empezar

**Cierra StrategyQuant en el maestro.** No hay forma de saltárselo y es deliberado. Si está abierto:

```
SQX está corriendo desde /home/sergioguslw/Desktop/SQX (PID 234724, 235060, 235064, …).
Ciérralo tú y vuelve a lanzarlo: la regla dura 2 prohíbe sqcli en el maestro
con la GUI levantada, y este comando acaba en un sync que borra .sqx de disco.
```

Sale con 1 y no toca nada. **Nunca mata el proceso**: lo cierras tú.

### Cómo se ejecuta

```bash
python3 -m sqx.data.update              # ENSAYO: te dice qué haría y no hace nada
python3 -m sqx.data.update --apply      # descarga de verdad
python3 -m sqx.data.update --apply --symbol XAUUSD_DukasM1_Infinox
```

| flag | obligatorio | qué hace |
|---|---|---|
| `--apply` | no | sin él es un ensayo. Es lo único que descarga |
| `--symbol` | no | un solo símbolo. Por defecto, todos los que el maestro tenga configurados |

El ensayo imprime el comando exacto que lanzaría y cuántas estrategias hay en juego:

```
7546 .sqx en disco bajo /home/sergioguslw/Desktop/SQX/user/projects
ENSAYO. Lanzaría: ./sqcli -data action=update  (cwd /home/sergioguslw/Desktop/SQX)
Añade --apply para hacerlo de verdad.
```

### Por qué cuenta los `.sqx` — esto es lo importante

Toda ejecución de `sqcli` termina así, la mires o no:

```
Synchronizing databanks to files
```

Y la **regla dura 1** dice qué significa eso: *cada sync de SQX borra los `.sqx` de disco que el
databank no tiene en memoria*. En tu maestro eso son **7.546 estrategias y 3,4 GB** expuestos cada
vez que se lanza cualquier comando.

Por eso el comando fotografía `user/projects` entero antes y después, guarda las dos fotos en
`AlgoData/backups/data-update/` y compara:

```
foto guardada en …/AlgoData/backups/data-update/2026-09-22T213045Z.json
…
regla 1 ok: los 7546 .sqx siguen en disco
```

Si algo desapareciera lo dice con nombre y tamaño, y tienes la foto para saber exactamente qué era.
Un informe vacío es el único resultado aceptable.

### Por qué en el maestro y no en un worker

Porque una descarga hecha en un worker **se pierde**. `bin/sqx-worker.sh` hace esto en cada arranque:

```bash
rsync -a --exclude='History/' "$MASTER/user/data/" "$WORKER/user/data/"
```

Maestro → worker. El `History` es un enlace compartido, así que los ficheros de barras nuevos caerían
bien, pero las tres bases H2 que un backtest lee de verdad son copias por instalación: la copia
fresca del worker la machaca la vieja del maestro en el siguiente arranque, y tu GUI sigue
construyendo con barras antiguas. Silencioso. Por eso la descarga va donde va.

### Qué hace al terminar

Encadena el refresco de fechas él solo, así que no hay un segundo paso que olvidar:

```
XAUUSD: data: {from: 2003-05-05, to: 2026-01-16}   # …, 7.708.823 barras M1
     →  data: {from: 2003-05-05, to: 2026-09-22}   # …, 7.949.285 barras M1
```

### Qué NO hace

- **No cierra SQX por ti**, ni lo mata. Se niega y te lo dice.
- **No toca ningún proyecto.** Sólo descarga datos y reescribe las fechas de `_policy.yaml`.
- **No decide ventanas.** Que un tramo `oos2` llegue más allá de los datos es un aviso del
  preflight, no algo que esto arregle. Ver `24-costes.md`.

### Ojo

⚠️ **La descarga en sí no está probada de punta a punta.** El verbo `-data action=update` existe en
la referencia de `sqcli` y el verbo `-data` despacha —comprobado con `action=timezones`—, pero
ejecutarla requiere tu GUI cerrada, así que la primera vez que corra de verdad será contigo. Las
guardas, el inventario y el refresco de fechas sí están probados. Haz el ensayo primero.

### Dónde está el detalle

- `sqx/data/README.md` — el porqué del maestro y del rsync.
- `knowhow/costs/refreshing-sqx-costs.md` — la referencia de verbos y el flujo de datos entre instalaciones.
- `docs/manual/24-costes.md` — el refresco de fechas por separado, sin descargar nada.
