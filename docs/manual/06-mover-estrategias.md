# 6. Mover estrategias descartadas — aplicar un veredicto dentro de SQX

### Qué pregunta responde

Ninguna. Este no analiza nada: **ejecuta una decisión que ya tomaste**. Coge el `verdict.csv` que
produjo un análisis y mueve dentro de SQX las estrategias marcadas como `DESCARTAR` a otra databank,
para que la databank de trabajo quede sólo con las que siguen vivas.

Es el único comando del proyecto que **cambia lo que contiene una databank**. Por eso no borra: mueve.

### Cuándo lo usas, y cuándo no

**Lo usas** cuando ya has leído el informe, estás de acuerdo con el veredicto, y quieres que la
databank refleje esa decisión sin ir estrategia por estrategia en la interfaz.

**No lo usas** para "limpiar" una databank por criterios que no estén en un `verdict.csv`. El fichero
es la traza de por qué se movió cada una; sin él no queda constancia de nada.

**No lo usas** con la interfaz de SQX abierta. Se niega a funcionar, y hace bien: las bases de datos
del master están bloqueadas mientras la interfaz las tiene, y un cambio hecho por debajo de una
instancia en marcha se pierde en silencio en la siguiente sincronización.

### Antes de empezar

1. **Crea la databank de destino desde la interfaz de SQX** (por ejemplo `Rejected`), en el mismo
   proyecto. Una creada por API no la recoge la sincronización de arranque, y el movimiento
   informaría de éxito hacia una databank que en realidad no está.
2. **Cierra la interfaz de SQX del master por completo.**
3. Ten a mano la ruta del `verdict.csv`.

### Cómo se ejecuta

**Siempre dos veces: primero en seco, y sólo después de leer lo que sale, en serio.**

```bash
# En seco. No toca absolutamente nada. Puedes lanzarlo con SQX abierto
python3 -m sqx.curate.apply_verdict --project XAUUSD --databank RetestMarkets \
    --verdict ~/Desktop/AlgoData/reports/XAUUSD/RetestMarkets/2026-09-08/randomentry/verdict.csv \
    --into Rejected

# En serio. Con la interfaz de SQX cerrada
python3 -m sqx.curate.apply_verdict --project XAUUSD --databank RetestMarkets \
    --verdict ~/Desktop/AlgoData/reports/XAUUSD/RetestMarkets/2026-09-08/randomentry/verdict.csv \
    --into Rejected --apply
```

| flag | obligatorio | qué hace |
|---|---|---|
| `--project` | sí | proyecto en el master |
| `--databank` | sí | databank de la que salen |
| `--verdict` | sí | ruta del `verdict.csv` |
| `--into` | sí | databank a la que van. Créala antes en la interfaz |
| `--apply` | no | **sin él no se toca nada.** Con él, se mueve |

Tarda lo que tarde SQX en arrancar en modo comando, en torno a un minuto, más la copia de seguridad.
Todas las estrategias se mueven en una sola llamada.

### Qué produce

Tres cosas, en este orden:

1. **Una copia de seguridad completa** de la databank de origen en
   `~/Desktop/AlgoData/snapshots/<fecha>/<proyecto>/<databank>/`, **antes** de mover nada. Va fuera
   de la instalación de SQX a propósito: cada sincronización borra del disco las estrategias que no
   estén en memoria, así que una copia dentro de `user/projects` no es una copia de seguridad.
2. **El movimiento** dentro de SQX.
3. **Un `manifest.json`** junto a la copia, diciendo qué veredicto la produjo y cuántas se movieron.

### Cómo se lee el resultado

En seco, te dice cuántas se quedan, cuántas se mueven, y te enseña las diez primeras por su nombre.
Léelas: si un nombre te sorprende, busca esa fila en `by_market.csv` antes de seguir.

En serio, la línea que importa es la última:

```
RetestMarkets: 912 → 631   Rejected: 281
```

Los números se cuentan **volviendo a mirar los ficheros en disco**, no creyéndose la respuesta de
SQX. Si no cuadran con lo que decía el veredicto, el comando se para y te dice dónde quedó la copia
de seguridad. Ahí, no sigas: restaura desde la copia y avisa.

### Qué NO te dice

- **No te dice que la decisión fuera buena.** Aplica un fichero. La calidad del veredicto es la del
  análisis que lo escribió.
- **No borra nada, ni aquí ni nunca.** Las estrategias descartadas siguen en la databank de destino y
  en la copia de seguridad. Una estrategia que falla una prueba sobre ocho mercados es información
  sobre esa prueba, y la población de la que salió es el material de todos los estudios posteriores.

### Si algo falla

- **"the master is running"** — la interfaz de SQX sigue abierta. Ciérrala del todo y repite.
- **Los números no cuadran al final** — el comando se para solo y no ejecuta nada más. La copia de
  seguridad está completa: restaura desde ella antes de tocar nada.
- **`Rejected` aparece vacía en la interfaz** — no la creaste desde la interfaz antes de mover.
  Restaura desde la copia, créala como es debido, y repite.
