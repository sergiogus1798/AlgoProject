# 35 · La flota de MT5 en la VPS: ver las cuentas y desplegar los EAs sin clicar — encargo autocontenido

**Tu oficio:** Python sobre `mt5/` y `ui/`, MQL5 y un poco de Windows.
**Tu encargo:** que el dueño pueda llevar decenas de cuentas de fondeo repartidas en instancias de MT5
de una VPS Windows sin abrir cada terminal: verlas todas desde la ventana de su Linux, y montar los
EAs de cada cuenta a partir de una carpeta de `.mq5` y un Excel.

Lee `CLAUDE.md` · `CODESTYLE.md` · `mt5/README.md` (sobre todo `live.py` y `winside/query.py`, que ya
leen un terminal con el Python de Windows) · `OPEN.md` #78 · `ui/README.md` ·
`docs/encargos/33-economia-del-fondeo.md` · `docs/encargos/34-validacion-mt5-pool.md`.

---

## 0 · De dónde sale

El dueño, 2026-09-29. Tiene una VPS Windows 10 modesta con 4-5 instancias de MT5 operando con EAs, y
prevé que el estudio del fondeo (encargo 33) concluya que hay que llevar **muchas cuentas a la vez, y
quemar muchas**: por ejemplo 10 instancias, 5 de Hantec y 5 de FTMO. Montar a mano cada EA en cada
terminal le da «una pereza impresionante».

Hechos de partida, contestados en la conversación:

- **Un terminal MT5 = una cuenta conectada.** Varias cuentas en vivo exigen varias instancias, que
  es lo que ya hace. Un EA no puede operar otra cuenta que la del terminal, y el paquete Python
  `MetaTrader5` tampoco.
- Que la VPS sea Windows y el proyecto Linux no estorba: la VPS **recoge y envía**, el Linux
  **calcula, guarda y enseña**.

## 1 · Lo que decidió el dueño

| # | decisión |
|---|---|
| 1 | **Se ve en la ventana de su Linux** (`ui/`), por ahora. Nada de web ni de móvil. |
| 2 | **El código vive en este repo**, en una carpeta propia (propuesta: `mt5/fleet/`). A la VPS va sólo su subcarpeta `vps/`, autocontenida, copiada por un script de despliegue — ni git ni el repo entero. |
| 3 | **La traducción de símbolos:** el Excel lleva el nombre **de SQX** (`XAUUSD`, `GER40`…), y una tabla del repo lo traduce por empresa: columnas `SQX \| Hantec \| FTMO`, una por empresa nueva. Un activo que no esté en la tabla **para el despliegue** y lo dice; nunca se adivina. |
| 4 | **Cada EA ya trae su riesgo por operación en USD**, programado para una fondeada concreta (un EA de 10k no arriesga lo mismo que uno de 50k). El despliegue **no toca el riesgo**: sólo encuentra el EA en la carpeta por su nombre y le pone el activo y la temporalidad del Excel. |
| 5 | **El Excel sigue sus tablitas:** por cada cuenta, los EAs que tiene. El dueño pasará la plantilla que ya usaba; el lector se adapta a ella, no al revés. |
| 6 | **Magic number: uno por combinación estrategia × activo × temporalidad, el mismo en todas las cuentas**, sacado de un registro y nunca reutilizado. Así nunca chocan dentro de una cuenta y cualquier operación del vivo dice qué combinación la abrió en cualquier cuenta, que es lo que lee la conciliación. **Cortito**, como pidió el dueño: secuencial de 4 cifras (1001, 1002…). |
| 7 | **El «play» es suyo:** el dueño se loguea y pulsa AutoTrading. Las contraseñas no pasan por el sistema. |

## 2 · Las piezas

### A · Ver: el estado de la flota

- **En la VPS**, preferiblemente un **servicio de MQL5** en cada terminal: un programa que vive dentro del
  terminal sin ocupar un gráfico ni tocar a los EAs, y que cada 30-60 s envía un resumen: equity,
  balance, margen, posiciones, operaciones cerradas, estado del AutoTrading y de la conexión, último
  error del diario. Coste casi nulo en una VPS justa. La alternativa es un agente Python único
  (~50 MB) que visita los terminales por turnos con `mt5.initialize(path=…)`: puede además reiniciar
  un terminal caído, pero hay que probar antes que el paquete convive con 10 instalaciones portables.
  **Lo decide la RAM libre de la VPS, que el dueño aún no ha pasado.**
- **Un terminal caído no envía:** el Linux lo detecta por el silencio. Una tarea programada de
  Windows vuelve a abrirlo.
- **Red:** Tailscale entre las dos máquinas, ningún puerto de la VPS abierto a internet. Si se corta,
  los datos esperan y se envían después.
- **En el Linux:** un colector que guarda el histórico en `AlgoData` (nunca en el repo), y una zona
  de la ventana con el estilo terminal: una fila por cuenta, con semáforo 🟢 operando · 🟡
  AutoTrading apagado o desconectado · 🔴 cerca del límite diario o total de su empresa (los límites
  los da `portfolio/funded/catalog/`).
- **Datos sensibles** (números de cuenta, IP de Tailscale, ruta de cada instancia) en
  `config/machine.yaml`, que no está en git.

### B · Desplegar: de la carpeta y el Excel a los gráficos montados

1. El dueño deja la carpeta de `.mq5` y el Excel.
2. En el Linux, sin tocar la VPS: se compila cada `.mq5` a `.ex5` con el MetaEditor de Wine
   (`mt5/metaeditor.py`); se comprueba que compila, que el activo existe en la tabla de su empresa y
   que el EA es para la fondeada de esa cuenta (§1 #4, por el nombre del archivo, §3); se asigna el
   magic del registro.
3. Por cada instancia se genera un paquete: los `.ex5`, un `.set` por EA con su magic, y **un perfil
   de gráficos** (`profiles/charts/<perfil>/chartNN.chr`), un gráfico por EA con su símbolo, su
   temporalidad y el EA enganchado. **El formato del `.chr` depende de la versión de MT5: se valida
   primero con el terminal de Wine en una cuenta demo**, antes de acercarse a la VPS.
4. El paquete viaja por Tailscale; un script de `vps/` lo copia a la instancia y la reinicia con ese
   perfil.
5. El dueño se loguea y pulsa AutoTrading.

Crear la instancia de una cuenta nueva también entra: copiar una instalación portable limpia,
nombrarla y registrarla.

### C · Actuar desde la ventana

| acción | riesgo | entra |
|---|---|---|
| desplegar o cambiar los EAs de una cuenta | bajo: el play sigue siendo del dueño | sí |
| crear una instancia nueva, retirar una cuenta quemada | bajo | sí |
| reiniciar un terminal colgado | bajo | sí |
| pausar una cuenta (el EA no abre operaciones nuevas) | medio | preguntar antes |
| cerrar todas las posiciones de una cuenta | alto, dinero real | **no**, salvo que el dueño lo pida; el MCP de MT5 del proyecto tiene las órdenes prohibidas a propósito |

### D · Conciliar: el vivo contra SQX

Con el magic de §1 #6, cada operación del vivo sabe de qué combinación viene. La conciliación semanal
SQX ↔ vivo deja de ser a mano y se alimenta de las 10 cuentas. Comparte la traducción de reloj y
costes del encargo 34 §2.

## 3 · El exportador de carteras: agente o skill (idea del dueño, entra aquí)

El dueño no exportará los `.mq5` a mano. Dirá **«me gusta esta cartera, exporta las estrategias»** y
un agente o una skill, por cada estrategia × cuenta de destino:

1. **asigna el magic** del registro (§1 #6);
2. **pone el riesgo por operación en USD** que toca al tamaño de la fondeada de destino;
3. **pone un filtro de noticias, si procede**;
4. **cambia el comentario de las operaciones** para que salga el nombre de la estrategia (el
   comentario de MT5 cabe en 31 caracteres, y hay brokers que lo recortan o lo sobrescriben: el
   magic es la llave, el comentario es para leerlo);
5. **nombra el archivo `.mq5`** de modo que el despliegue (§2 B) sepa para qué fondeada es.

Depende de exportar el `.mq5` de SQX sin la interfaz: `OPEN.md` #78 punto 3, todavía sin resolver.

## 4 · Lo que falta por decidir: pregúntalo, no lo supongas (regla 11)

1. **Specs de la VPS:** RAM, CPUs y RAM libre con todos los terminales abiertos. Decide servicio
   MQL5 o agente Python (§2 A).
2. **La plantilla de Excel** del dueño (§1 #5).
3. **El patrón del nombre del archivo** que liga un EA a su fondeada (§3 punto 5), por ejemplo
   `Est17_FTMO100k.mq5`. ¿Para una empresa y un tamaño, o para una cuenta concreta?
4. **El filtro de noticias:** qué noticias (impacto alto, de qué divisas), qué ventana antes y
   después, qué hace el EA dentro (no abrir, o cerrar también), de dónde sale el calendario. FTMO y
   Hantec tienen reglas propias sobre operar en noticias: se leen del catálogo.
5. **El riesgo por tamaño:** qué USD por operación para cada tamaño de cuenta. Lo más probable es
   que salga del encargo 33.
6. **Pausar una cuenta:** si entra, cómo (un archivo de control que lea el servicio, o cerrar el
   terminal).

## 5 · Orden de trabajo propuesto

1. Tabla de símbolos `SQX | Hantec | FTMO` y registro de magics.
2. Generar un perfil `.chr` y validarlo en el terminal de Wine, en demo.
3. El lector del Excel, con la plantilla del dueño.
4. El colector y el servicio MQL5, primero contra el terminal de Wine, después en la VPS.
5. La zona de la ventana.
6. El exportador de §3, cuando #78.3 esté resuelto.

Cada comando nuevo sale con su capítulo del manual (regla 8).
