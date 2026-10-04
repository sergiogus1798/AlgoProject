# Informe: feedback de UI del 2026-10-03

Ejecutado la noche del 3 al 4 de octubre de 2026, desde las 3:30 (hora del servidor).
Nada está en commit: todo queda en el árbol para que lo revises.

## Resumen

- **Proyectos ya carga.** La lista tardaba 36 s con el demonio recién arrancado (más con el disco frío) y ahora tarda 0,17 s.
- **La app abre en 2,9 s** en lugar de 8,7 s, y **Datos carga en 7 s** en lugar de 354 s.
- **Cobertura es ahora la portada de la Biblioteca**, con las otras cuatro vistas en una tira encima.
- **Hay pestaña Criterios** (Proyecto › Criterios), primera versión.
- **MetaTracker tiene la curva de equity por estrategia y cuenta**, probada con datos sintéticos.
- El resto del pulido está hecho, con las excepciones de la sección «Lo que no se hizo».

**Lo que necesito de ti**, por orden de importancia:

1. Recargar **FleetBeacon v2** en los tres terminales de la VPS. De eso dependen cuatro cosas (ver punto 11).
2. Contestar las **seis preguntas de Criterios** (punto 13).
3. Rellenar las tres hojas nuevas del Excel de la flota, si el beacon v2 no las rellena solo.

## Cómo se probó

- **Recorrido automático de la ventana:** 17 zonas, 0 excepciones. Abre cada zona y mueve sus desplegables, pestañas y tablas.
- **Capturas:** cada zona cambiada se capturó y se miró.
- **Tests nuevos:** uno por cada pieza con lógica (lista abajo, en cada punto).
- **Lo que no se pudo probar:** los clics reales de ratón (las capturas no los ejercitan) y todo lo que necesita SQX corriendo. Se indica en cada punto.

## Punto por punto

### 1. Arranque lento — hecho

| | Antes | Después |
|---|---|---|
| Hasta ver la ventana | 8,7 s | 2,9 s |
| Construir la ventana | 6,67 s | 0,66 s |

La ventana construía y cargaba las ocho zonas antes de mostrarse. Ahora cada zona se carga la primera vez que la abres. «Recargar» relee la zona abierta y marca las demás para releerse.

Queda un coste conocido: **Activos tarda unos 5 s la primera vez**, porque construye las 27 fichas de golpe. Se arregla construyendo cada ficha al seleccionarla; no se hizo esta noche.

### 2. Proyectos no cargan — hecho

La causa: para contar las estrategias de cada databank, la lista abría y calculaba la huella de los 20.887 ficheros `.sqx` uno a uno, en una sola petición. Ahora cuenta ficheros.

- Antes: 36,3 s. Después: 0,17 s. Medido con el demonio recién arrancado.
- Coste: una estrategia duplicada dentro de un databank cuenta dos veces en la tarjeta. Al abrir el databank se sigue viendo sin duplicados.
- La lista tiene 235 tarjetas, de las que 215 son proyectos que ya no existen y sólo conservan informes. No las he quitado; dime si quieres ocultarlas.

### 3. Cobertura, Plantillas, Investigar, Nueva plantilla, Paletas — hecho

![Cobertura como portada](assets/feedback-ui-cobertura.png)

- **Una sola entrada en el lateral:** «Cobertura y plantillas». Encima de la página hay una tira con las cinco vistas en el orden del trabajo: Cobertura, Investigar, Plantillas, Nueva plantilla, Paletas.
- **Cobertura es la portada.** Filas: familias con su número de plantillas. Columnas: timeframes.
  - El fondo de la celda dice cuánto se ha probado, en cuatro escalones con leyenda.
  - Una marca dice el mejor veredicto que hay dentro (✔, ~, ✘).
  - «tablero N» dice en cuántos activos el director admite esa familia ahí. Una celda sin probar con «tablero 15» es un hueco que merece plantilla; una vacía, no.
- **La propuesta del director** aparece en una línea encima de la rejilla, con «Ver propuesta».
- **Desde la rejilla:** el nombre de una familia abre Plantillas filtrada por ella. Una celda activa cuatro botones: «Ver plantillas», «Paleta de esta familia», «Nueva plantilla aquí» e «Investigar esta celda».
- **Nombres unificados:** una sola tabla (`ui/desktop/names.py`) para toda la app: Breakout, Mean reversion, Trend following, Momentum, Volatility, Pattern, Session. Las paletas siguen la misma regla («Breakout — base»). Las claves guardadas en los ficheros no cambian; sólo lo que se muestra.

Lo que se dejó como estaba:

- El interior de cada vista: sólo cambian nombres y enlaces.
- «Nueva plantilla aquí» rellena sólo la familia. El activo y el timeframe se mencionan en la conversación, porque una plantilla no pertenece a un mercado.

Para volver atrás: en `ui/desktop/nav.py`, devolver los cuatro nombres a la lista «Biblioteca» de `GROUPS` y poner `LIBRARY = []`.

Probado con `tests/test_ui_library.py` (la navegación) y capturas. Los clics reales de ratón no están probados.

### 4. Activos — hecho

- «Costes (doble clic para cambiar)».
- Check de Cross Market en una línea.
- «Al día» y la etiqueta de clase (Forex…) más grandes.
- **Características** como lista con guiones a la derecha: «Va muy bien para Trend following», «Va regular para…», «Va mal para…», con la nota en prosa debajo. «Va regular» y «Va mal» son palabras mías: tú sólo dictaste «muy bien».
- **Rangos MC Retest:** decididos en los 15 activos que estaban «sin decidir». Lo que faltaba era sólo el slippage; el rango de spread ya lo había puesto la otra sesión.

| Activo | Spread (ya estaba) | Slippage escrito |
|---|---|---|
| USDCHF | 0,73 / 1,99 | 0,37 / 1,00 |
| AUDJPY | 0,95 / 2,35 | 0,48 / 1,18 |
| GBPJPY | 1,41 / 3,30 | 0,71 / 1,66 |
| GBPUSD | 0,88 / 2,09 | 0,44 / 1,05 |
| DAX40 | 85,11 / 361,53 | 42,56 / 180,77 |
| DJ30 | 118,18 / 566,99 | 59,13 / 283,42 |
| NIKKEI225 | 165,47 / 1206,56 | 82,76 / 603,27 |
| USA500 | 14,45 / 84,11 | 7,23 / 42,06 |
| USATEC | 30,10 / 281,23 | 15,06 / 140,70 |
| CADJPY | 0,95 / 1,90 | 0,47 / 0,95 |
| EURJPY | 0,77 / 1,78 | 0,39 / 0,89 |
| AUDUSD | 0,62 / 1,40 | 0,31 / 0,70 |
| EURUSD | 0,36 / 0,86 | 0,18 / 0,43 |
| USDCAD | 0,65 / 1,32 | 0,33 / 0,66 |
| USDJPY | 0,32 / 0,72 | 0,16 / 0,36 |

Mínimo / máximo, en puntos. El slippage es la mitad del spread, según la regla de la casa. No se cambió ningún valor que ya estuviera puesto: cada fichero cambia en dos líneas.

Dos avisos:

- En los seis últimos de la tabla, el rango de spread que hay en la ficha no coincide con el recién medido (por ejemplo EURUSD: la ficha dice 0,36 / 0,86 y la medición 0,11 / 1,11). Usé el de la ficha. Si la otra sesión vuelve a medir el spread, hay que rehacer el slippage.
- En EURUSD y USDJPY el rango es tan estrecho que SQX, que sortea en pasos de 0,1, dará pocas corridas distintas.

A 1440 px de ancho la página de Activos tiene un pequeño scroll horizontal.

### 5. Configuración SQX — hecho, salvo un texto que no existe

- Quitados todos los nombres de fichero: los de las cabeceras de grupo y el `assets/_build.yaml` de cada sección (lo que dictaste como «Asset Spoil»). Siguen en el tooltip.
- CSCV › Periodo muestra Day, Week, Month. Puntuación muestra Sharpe y Sortino.
- Títulos de sección a 17 px, nombres de campo a 15 px.
- **No hecho:** «Reglas de entrada» con mayúscula. Ese texto no aparece en la zona; sólo existe «Reglas de selección», que ya la llevaba.

### 6. Datos — hecho

- **Carga:** de 353,7 s a 7,3 s. La causa era el cálculo del tamaño de cada carpeta sobre 4,3 millones de ficheros. Quitados la columna «Tamaño» y el total en GB.
- **Histogramas de toda la app:** una regla común recorta el eje X entre los percentiles 0,5 y 99,5, y el pie del gráfico dice cuántos valores quedaron fuera. La usan los tests estadísticos, IS/OOS, SPP, la ficha de estrategia, Cross Market y Monte Carlo.
- **Spread de apertura de cada minuto (2025):** ya sale con barras normales en XAUUSD (3.508 valores fuera). Los demás activos lo mostrarán cuando se regenere su análisis de spread; sólo regeneré XAUUSD.
- Mayúsculas en la tabla Modelo y en los ejes del scatter.
- **Curvas ajustadas:** eje X «Precio del activo (moneda de cotización)», eje Y «Spread (puntos)».

Un detalle: en carpetas con más de 20 ficheros, «Última escritura» sale de la fecha de la carpeta, así que un fichero reescrito en sitio no la mueve.

### 7. Navegación lateral — hecho

MT5 Bridge va antes que Portfolios, y los títulos de grupo son más grandes.

### 8. En marcha no detecta proyectos nuevos — hecho, sin probar en vivo

La vista re-escanea instalaciones y proyectos cada 30 s mientras está visible (coste medido: 10 ms). Si aparece un run nuevo, lo sigue. No se pudo probar con un proyecto arrancando de verdad porque no había SQX en marcha.

### 9. Registro de búsquedas

Sin cambios, como pediste.

### 10. MT5 Bridge › Verificar — hecho, con una duda

- Mayúsculas en tabla y métricas, para FTMO y Hantec.
- Ratio de operaciones emparejadas en porcentaje: «96,73%».
- Resumen con una línea por empresa: «FTMO: validada» en verde, «Hantec: no validada» en rojo.
- La diferencia media por operación emparejada sigue en R.
- **Drawdown máximo:** esa fila no estaba en dólares; es la diferencia relativa entre el drawdown de SQX y el de MT5. Ahora sale como porcentaje con un decimal («6,9%»). Si te referías a otra cifra, dime cuál.

### 11. MetaTracker — hecho; los datos reales esperan a FleetBeacon v2

![Curva de equity por estrategia, con datos sintéticos](assets/feedback-ui-equity.png)

- **Nombres:** FTMO, Hantec Trader, Funding Pips; Fase 1, Fase 2, Funded. En todas las pestañas y en el aviso de escritorio.
- **Curva de equity por estrategia** (pestaña Estrategias): eliges la estrategia, marcas una, varias o todas las cuentas, y «Combinada» añade la suma. Se puede ver en % del tamaño de la cuenta (por defecto, para comparar una de 10k con una de 100k) o en divisa. Debajo, una tabla por cuenta con Trades, Net Profit, Win Rate y Max drawdown. La captura es con datos sintéticos.
- **«Equity si saltan stops»:** la raya sale en las tres cuentas, y no es por los trailing stops. El beacon instalado es la versión 1, que no envía los datos para calcularlo. Ahora dice «— (beacon v1)» con la explicación en el tooltip.
- **Despliegue:** creadas las hojas `FTMO_10k_Funded`, `Hantec_100k_F1` y `FundingPips_10k_F2` en `Flota_de_cuentas.xlsx` y enlazadas a cada cuenta. El aviso «sin hoja en el Excel» ya no sale. **Las hojas tienen sólo la cabecera**, porque el beacon v1 no dice qué EAs lleva cada cuenta. Las hojas antiguas están intactas.

**Recargar FleetBeacon v2 en cada terminal de la VPS** desbloquea cuatro cosas: el historial de cada cuenta, la curva de equity con datos reales, «Equity si saltan stops» y la lista de EAs montados para rellenar las hojas.

### 12. Progreso de la generación genética — hecho en parte

SQX no publica en ningún sitio la generación actual, las islas en curso ni cuánto lleva la población inicial: ni en su log ni en la respuesta de estado. Sólo publica «Strategies generated» e «In databank».

Lo que la vista muestra ahora, cuando corre un Build genético:

- Población × islas (por ejemplo 5.000), que es lo que hay que llenar antes de que nada llegue al databank.
- Generaciones máximas.
- Cuántas estrategias hay en disco en «Initial population» y en «Last generation». Van con retraso, porque SQX las escribe al sincronizar.
- Un «?» que explica por qué el databank está a cero al principio.

Sin probar con un Build en marcha.

### 13. Pestaña Criterios — primera versión hecha

![Pestaña Criterios](assets/feedback-ui-criterios.png)

Es una vista sobre lo que ya existe, no un segundo sistema: lee y escribe `pipeline/autopilot/criteria.yaml`, y el único juez sigue siendo el autopilot.

Qué hace:

- Lista el paso 6 (filtros del Build, sólo lectura) y los pasos 8 a 26 en orden. Cada paso muestra su tabla de criterios, o «Sin criterios: pasan todas».
- Columnas: Criterio, Tipo (Métrica SQX, Test de la app, Veredicto, Compuesto), Condición, Limbo, Excepciones.
- Doble clic en un criterio abre el diálogo para cambiarlo o borrarlo. «Añadir criterio» ofrece umbral numérico, banda alrededor de la mediana, veredicto (pasa / no pasa) y compuesto (todas / alguna, un nivel).
- Cada cambio queda sellado en `ledger/criteria-history.jsonl`: cuándo, en qué paso, la regla antes y después.
- «Congelar» bloquea la escritura. No hay botón para descongelar.
- Avisa en naranja de que el modo desarrollo está activo: en el paso 8 sólo siguen 5 supervivientes elegidas al azar.

Qué no hace todavía:

- Editar las excepciones por timeframe o clase, el modo desarrollo, el databank que se recorta ni el paso 6.
- Añadir criterios a los pasos 17 a 26: no tienen databank de corte definido, y el botón está apagado con el motivo.
- Ofrecer todas las métricas de SQX. Hoy el autopilot sólo conoce las de spread y Cross Market; el selector ofrece esas.

Dos cosas añadidas sin que las pidieras:

- `else: limbo` en una regla: «no cumple» pasa a ser limbo en vez de descarte. Es la forma explícita del truco actual de poner el limbo en `>= -1000`.
- Una línea corregida en `pipeline/autopilot/run.py`, que habría fallado al encontrar una regla compuesta.

El fichero real de criterios no cambió de valores: sólo ganó 12 líneas de comentario en la cabecera. Las pruebas de escritura se hicieron sobre una copia (`tests/test_ui_criteria.py`, `tests/test_autopilot_criteria.py`). Los clics reales y la confirmación de «Congelar» no están probados.

**Preguntas para ti:**

1. ¿Añado las métricas de SQX (Net Profit, Profit Factor, Ret/DD…, IS y OOS) como criterios, leídas del databank que se recorta? Hace falta una fuente nueva en el autopilot.
2. ¿Qué databank recortan los pasos 17 a 25?
3. ¿«Congelar» debe negarse mientras el modo desarrollo esté activo? ¿Y la pestaña debe poder apagarlo?
4. ¿Sustituyo los limbos `>= -1000` por `else: limbo`?
5. ¿Quieres editar desde la pestaña las excepciones y el paso 6?
6. ¿Pongo nombres en español a los criterios? Hoy se leen como «Drift excess t».

## Lo que no se hizo, y por qué

| Qué | Por qué |
|---|---|
| «Reglas de entrada» con mayúscula (punto 5) | El texto no existe en la zona. |
| Generación actual e islas en vivo (punto 12) | SQX no las publica. |
| Hojas del Excel rellenas (punto 11) | El beacon v1 no dice qué EAs hay montados. |
| Histograma de spread recortado en los demás activos (punto 6) | Hay que regenerar su análisis; sólo se hizo XAUUSD. |
| Activos rápido en la primera apertura (punto 1) | Otro cambio tocaba el mismo fichero a la vez. |

## Encontrado por el camino

- `tests/test_ui_research.py` falla con `KeyError: 'measures'` en `studies/research/marketProfile`. Viene de cambios sin commit de otra sesión, no de esta noche. Efecto visible: en Investigar, el detalle de una celda del mapa muestra ese error.
- El recorrido automático de zonas (`tools/uiwalk.py`) se cortaba en «Estrategia» sin decir por qué; corregido.

## Decisión

Lo que desbloquea más con menos esfuerzo es **recargar FleetBeacon v2 en la VPS**: unos minutos tuyos a cambio de cuatro funciones de MetaTracker con datos reales. Después, las seis preguntas de Criterios, que deciden la segunda versión de la pestaña.
