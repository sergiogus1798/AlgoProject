# 6. Quitar estrategias descartadas — aplicar un veredicto dentro de SQX

> Para **escribir** el veredicto con un filtro o con un nombre suelto: `27-curar.md`. Esta página
> es el paso que lo aplica.

### Qué pregunta responde

Ninguna. Este no analiza nada: **ejecuta una decisión que ya tomaste**. Coge el `verdict.csv` que
produjo un análisis y saca de SQX las estrategias marcadas como `DESCARTAR`, para que la databank
de trabajo quede sólo con las que siguen vivas. **Las descartadas se borran**; antes queda anotado
qué había, con la identidad y las métricas de cada una. Con `--into` en vez de borrarlas van a
otra databank del mismo proyecto, y entonces SQX las vuelve a cargar al arrancar: cuestan RAM.

Es el único comando del proyecto que **cambia lo que contiene una databank**. Cada `.sqx` pesa
unos 5 MB; guardar 8.000 descartadas de 10.000 serían 40 GB por una estrategia que nadie va a
recuperar. Se anota y se borra (decisión del dueño, 2026-09-23).

### Cuándo lo usas, y cuándo no

**Lo usas** cuando ya has leído el informe, estás de acuerdo con el veredicto, y quieres que la
databank refleje esa decisión sin ir estrategia por estrategia en la interfaz.

**No lo usas** para "limpiar" una databank por criterios que no estén en un `verdict.csv`. El fichero
es la traza de por qué se movió cada una; sin él no queda constancia de nada.

**No lo usas** con la interfaz de SQX abierta. Se niega a funcionar, y hace bien: las bases de datos
del master están bloqueadas mientras la interfaz las tiene, y un cambio hecho por debajo de una
instancia en marcha se pierde en silencio en la siguiente sincronización.

### Antes de empezar

1. **Para la instalación.** `--role master` exige la interfaz cerrada; `--role conductor` o
   `--role custodian`, el worker parado (`bin/sqx-worker.sh --role custodian stop`). Se niega si
   está viva: SQX tiene los registros en memoria y reescribe los ficheros desde ella, así que un
   movimiento hecho por debajo se deshace en la siguiente sincronización.
2. **La databank de destino no hace falta crearla a mano.** Se crea sola si no existe, y el
   arranque siguiente la recoge — verificado en el custodio el 2026-09-23. La nota anterior, que
   decía que había que crearla desde la interfaz, no se sostiene.
3. Ten a mano la ruta del `verdict.csv`. Si trae la columna `identity` (la escribe `verdict.py` y
   cualquier módulo que pueda calcularla), el comando comprueba que el fichero que va a mover es la
   estrategia que se juzgó, y no otra que SQX haya puesto bajo el mismo nombre. Esa comprobación se
   hace ya en seco, con la instalación viva, porque sólo lee.

> **Actualizado el 2026-09-23.** Antes esto llamaba a `-databank action=move` con la lista de
> nombres. **Ese selector no funciona**: por la API HTTP el nombre se corta en su primer espacio, y
> un `sqcli` de un disparo ni siquiera carga los registros — los dos informan de éxito y no hacen
> nada, y `move` sin selector se lleva la databank entera. Ahora mueve los ficheros `.sqx` con la
> instalación parada, y es el arranque siguiente el que hace que la memoria coincida. Medido y
> escrito en `knowhow/02-databanks.md`.

### Cómo se ejecuta

**Siempre dos veces: primero en seco, y sólo después de leer lo que sale, en serio.**

```bash
# En seco. No toca absolutamente nada. Puedes lanzarlo con SQX abierto
python3 -m sqx.curate.apply_verdict --project XAUUSD --databank RetestMarkets \
    --verdict ~/Desktop/AlgoData/reports/XAUUSD/RetestMarkets/2026-09-08/randomentry/verdict.csv \

# En serio. Con la instalación parada
python3 -m sqx.curate.apply_verdict --project XAUUSD --databank RetestMarkets \
    --verdict ~/Desktop/AlgoData/reports/XAUUSD/RetestMarkets/2026-09-08/randomentry/verdict.csv \
    --role custodian --apply
```

| flag | obligatorio | qué hace |
|---|---|---|
| `--project` | sí | proyecto en esa instalación |
| `--databank` | sí | databank de la que salen |
| `--verdict` | sí | ruta del `verdict.csv` |
| `--into` | no | databank del mismo proyecto a la que moverlas **en vez de borrarlas**. SQX la carga al arrancar, así que cuestan RAM |
| `--role` | no | `master` (por defecto), `conductor` o `custodian` |
| `--apply` | no | **sin él no se toca nada.** Con él, se borra |

Instantáneo: mueve ficheros, no arranca SQX. Lo que tarda es el arranque posterior, que es el que
hace que la memoria coincida con lo que quedó en disco.

**Y ese arranque es parte del procedimiento, no un detalle.** Hasta que no lo hagas, SQX sigue
teniendo en memoria lo que había antes:

```bash
bin/sqx-worker.sh --role custodian start
python3 -c "from core import worker; print(worker.call('-databank action=list project=<P>','custodian'))"
```

El recuento que imprime ahí es la única verificación que vale: es lo que va a leer la tarea
siguiente.

### Qué produce

Tres cosas, en este orden:

1. **El registro**, en `~/Desktop/AlgoData/reports/<proyecto>/<databank>/<fecha>/curate/`, junto
   al veredicto: `before-HHMMSS.csv` con nombre, identidad, tamaño, veredicto **y el motivo** de
   cada estrategia que había en disco, y `rejected-HHMMSS.csv` con la fila de métricas de cada
   descartada, con el motivo como primera columna, si la databank tiene métricas exportadas. El
   motivo es la columna `reason` del veredicto: el filtro que no pasó (`failed: sharpe_ratio_is >
   0.93`), `dropped by name`, o el nombre del fichero de veredicto cuando el módulo que juzgó no
   escribió motivo — entonces ese fichero es la prueba. Kilobytes. Copiar los `.sqx` costaría 50 GB por corte con
   10.000 estrategias.
2. **El borrado** de los `.sqx` descartados (o el movimiento, con `--into`).
3. **Un `manifest.json`** junto al registro, diciendo qué veredicto lo produjo y cuántas se quitaron.

### Cómo se lee el resultado

En seco, te dice cuántas se quedan, cuántas se mueven, y en cuántas ha podido comprobar la
identidad. Salida real del 2026-09-23 en el conductor:

```
SQX_w1 · Retester/Results: 66 strategies on disk
  the verdict drops 32, keeping 34
  identity checked on 32 of 32

dry run. Re-run with --apply, with the conductor stopped.
```

Si un fichero no es la estrategia juzgada, se para ahí y no mueve nada. Probado cambiando un
fichero por otro bajo el mismo nombre:

```
  ✗ 1 carry a different strategy than the verdict judged: Strategy 11.10.85(1). The databank
  changed under that name since the verdict was written; re-export and judge again. Nothing was moved.
```

En serio, las líneas que importan son estas:

```
  metrics of the dropped kept in /home/sergioguslw/Desktop/AlgoData/reports/Retester/Results/2026-09-23/curate/rejected-073842.csv
  what was here is listed in /home/sergioguslw/Desktop/AlgoData/reports/Retester/Results/2026-09-23/curate/before-073842.csv
Results: 34 → 33   deleted 1
start the conductor and the sync from files makes memory match: the next task reads 33.
```

Y tras arrancar, SQX contó **33**. Ese es el número que lee la tarea siguiente.

Los números se cuentan **volviendo a mirar los ficheros en disco**, no creyéndose la respuesta de
SQX. Si no cuadran con lo que decía el veredicto, el comando se para y te dice contra qué lista
comparar el directorio.

### Qué NO te dice

- **No te dice que la decisión fuera buena.** Aplica un fichero. La calidad del veredicto es la del
  análisis que lo escribió.
- **No conserva las operaciones de las descartadas.** Con el fichero se van sus trades y su XML.
  Lo que queda de la población completa son sus métricas en `rejected-HHMMSS.csv`, que es lo que
  leen los estudios de población; un estudio sobre trades de una estrategia descartada ya no es
  posible. Es la contrapartida de no guardar 40 GB.

### Si algo falla

- **"the master is running"** — la interfaz de SQX sigue abierta. Ciérrala del todo y repite.
- **Los números no cuadran al final** — el comando se para solo y no ejecuta nada más. Compara el
  directorio con `before-HHMMSS.csv` antes de tocar nada.
- **"N had no file"** con los números cuadrando — el veredicto nombraba una estrategia que ya no
  estaba, porque las métricas se exportaron antes de un corte anterior. Lo demás se aplicó bien;
  vuelve a exportar las métricas antes del siguiente veredicto. En seco ya lo avisa:
  `⚠️ 1 named by the verdict are not here`.
- **"carry a different strategy than the verdict judged"** — la databank cambió bajo ese nombre
  desde que se escribió el veredicto. No se movió nada: vuelve a exportar las métricas, vuelve a
  juzgar, y aplica el veredicto nuevo.
