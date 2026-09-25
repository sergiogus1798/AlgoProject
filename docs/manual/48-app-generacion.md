# 48. La aplicación de escritorio — generación, o por dónde va el proyecto

La zona que responde a «¿por dónde va lo que está corriendo?» sin abrir SQX ni molestarlo. Elige
un install y un proyecto y enseña, cada tres segundos, qué tarea está en marcha, qué porcentaje
lleva, cuántas estrategias ha procesado de cuántas, cuánto tarda cada una, cuánto lleva la tarea
y cuánto lleva el workflow del día. **No arranca, no para, no reconfigura.** Lee ficheros del
install y, solo mientras corre en un worker, le pide su línea de estado: el único comando que la
regla del dueño permite al custodio a mitad de trabajo, porque no sincroniza nada.

### Qué pregunta responde

- **¿Está corriendo, y qué?** La línea de estado: `CORRIENDO · tarea MCR 6 Exits · 4 / 20
  estrategias · 13,0 s por estrategia · la tarea lleva 1 min 41 s · workflow de hoy: 23 min`.
  O `terminado`, `otro proyecto corre` (el install está con otro) o `parado`. Al final, hace
  cuántos segundos creció el log: si ese número sube y sube, SQX no escribe.
- **¿Qué tareas tiene el proyecto y en qué estado?** La tabla, en el orden en que SQX las corre:
  tipo, si está activa en este `start` (lo que decide `stage`, manual `47-proyecto-workflow.md`),
  su estado, **hechas / total**, el tiempo que tardó o que lleva, el tiempo por estrategia, su
  databank de salida y cuántos ficheros hay ya en él.
- **¿Qué está haciendo exactamente ahora?** Las últimas líneas de progreso del log, tal cual las
  escribe SQX: «Loading backtest data…», «All backtest data prepared», «Task finished in 19 s».

### Cuándo lo usas, y cuándo no

**Lo usas** mientras corre un paso largo en el custodio, para no abrir SQX y no mandarle nada; y
al volver a una sesión, para ver qué acabó y qué no.

**De dónde salen los números.** El *total* de una tarea es lo que había en su databank de
entrada cuando empezó, escrito por SQX en el log propio del proyecto (`user/projects/<P>/log/`);
un build no tiene total. Las *hechas* mientras corre son «Strategies generated» del estado del
worker; al acabar, «Total tested» del mismo log. El tiempo por estrategia es el que SQX declara;
si mientras corre dice cero, lo que lleva la tarea entre las hechas. El workflow del día va desde
el primer `TASK STARTED` de hoy hasta el último `TASK FINISHED`, o hasta ahora.

**No lo usas** para lanzar ni parar: no hay botón, a propósito. Arrancar y parar sigue siendo
`bin/sqx-worker.sh` y las skills, con las reglas de carriles de `sqx/CLAUDE.md`. Tampoco es un
recuento exacto del databank en curso: SQX escribe los `.sqx` al sincronizar, así que la salida de
la tarea que corre va con retraso hasta que guarda.

### Antes de empezar

Nada. Vale con el maestro abierto (a él no se le pide nada nunca) y con el custodio en mitad de
un trabajo (solo `status`). Los installs son los de `config/machine.yaml`: conductor, custodio y
maestro.

### Cómo se ejecuta

```bash
bin/algoui --zone "Generación"
```

O desde la barra lateral. Elegir el install y el proyecto; la zona se refresca sola cada tres
segundos mientras está a la vista y deja de leer cuando cambias de zona.

| control | qué hace |
|---|---|
| install | `custodian` (SQX_w2), `conductor` (SQX_w1) o `master`. El maestro solo se lee |
| proyecto | cualquier carpeta de `user/projects` de ese install con `project.cfx` |

### Qué produce

Nada. No escribe ni un fichero.

### Cómo se lee el resultado

![La zona con el proyecto de la prueba del workflow, recién acabado un start](assets/app-generacion.png)

Cada `start` de un proyecto es **un paso del workflow**: `stage` deja activa solo la tarea del paso
y SQX marca las demás como `SKIPPED, inactive task`. Por eso los estados son estos:

| estado | qué significa |
|---|---|
| **en curso** | la última tarea que escribe en el log; en negrita, y con su porcentaje arriba cuando SQX lo da |
| **hecha** | el log vio `Task finished` en este start |
| **hecha antes** | inactiva en este start, pero su databank tiene estrategias: la hizo un start anterior |
| **en cola** | activa en este start y aún no empezada |
| **saltada** | inactiva en este start y con el databank vacío |
| **inactiva** | apagada, sin start en marcha |

La columna «en disco» son ficheros: SQX los escribe al sincronizar, no según los produce. En la
captura, el custodio va por las tareas del MC Retest sobre las 20 estrategias que dejó el retest
de mercados: cada una tarda entre 1 y 16 segundos según la perturbación.

### Un ejemplo completo

1. Otra sesión lanza el paso 13 en el custodio con `/mcretest`.
2. `bin/algoui --zone "Generación"`, install `custodian`, proyecto `USDJPY_emaCross_H1`.
3. Arriba: `CORRIENDO · tarea MCR 3 Slippage · 7 / 20 estrategias · 16,0 s por estrategia · la
   tarea lleva 1 min 52 s · workflow de hoy: 18 min`. En la tabla, `MCR 1 Bar` y `MCR 2 Spread`
   en verde como hechas con su `10 / 20` y su tiempo, `MCR 3` en negrita, `MCR 4` a `MCR 8` en
   cola. Debajo, el log diciendo «Loading backtest data for Main test».
4. Cuando la línea pase a `terminado`, los ocho databanks MCR tendrán su recuento.

### Qué NO te dice

- **Cuánto falta, con exactitud.** Hechas × tiempo por estrategia es una estimación: las
  estrategias no tardan lo mismo, y un build no tiene total conocido. El porcentaje del
  nombre del hilo solo lo escriben las tareas walk-forward.
- **De quién es el start.** El log nombra el proyecto solo cuando el start llega por la API
  (`Starting project '…'`); un start desde la GUI del maestro no se atribuye hasta que guarda un
  databank (`knowhow/locations/log-names-project-only-via-cli.md`).
- **Si el resultado es bueno.** Solo cuenta ficheros.

### Si algo falla

- **«sin log de hoy»**: el install no ha escrito nada hoy; o no ha corrido nada o el log está en
  otra fecha. La zona solo lee el fichero del día.
- **«otro proyecto corre»**: no es un error. El install está ocupado con el proyecto que nombra.
- **El recuento no sube aunque corre**: normal hasta que SQX sincroniza el databank.
