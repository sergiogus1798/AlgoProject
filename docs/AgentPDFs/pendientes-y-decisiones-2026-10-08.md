# Pendientes y decisiones abiertas tras rehacer las pruebas (pasos 6 a 20)

*2026-10-08 · recopilación de lo que los agentes te preguntaron o dejaron provisional entre el 4 y el 8 de octubre y quedó sin respuesta.*

## Qué es este documento

Entre el 4 y el 8 de octubre se rehicieron los criterios y las pruebas de los pasos 6 a 20 del workflow. Por el camino cada agente fue dejando preguntas para ti, umbrales «provisionales», dudas y trabajo a medias, repartidos por ocho encargos, una veintena de dossiers, `OPEN.md`, las auditorías nocturnas y los comentarios del propio código. Aquí está todo junto, sin duplicados y ordenado por paso.

**De dónde sale.** Cuatro barridos, cada uno sobre una fuente: los encargos 41 a 48; `OPEN.md`, `WORKFLOW.md` y las auditorías de `AlgoData/audit/`; el código y sus ficheros de criterios tal como están hoy en disco (casi todo sin commit); y los dossiers de `docs/AgentPDFs/` con las tarjetas de `knowhow/` tocadas esos días. No se han leído las conversaciones: lo que un agente te dijera de palabra y no dejara escrito en ninguno de esos sitios no está aquí.

**Cómo leerlo.** Cada paso tiene hasta tres bloques:

- **Decisiones tuyas** — lo único que necesita tu respuesta. Cada una lleva un código (`P8-1` es la primera del paso 8; `T-` son transversales; `X-` son de tests) para que contestes con una línea: «P8-1: b».
- **Lo resolverá la calibración** — umbrales que son provisionales solo porque todavía no ha pasado por la cadena una población sin ventaja (los «monos», estrategias de entrada al azar) ni una con ventaja plantada a propósito. No te piden opinión: piden esa corrida.
- **Trabajo pendiente que no necesita tu respuesta** — cosas sin ejecutar o sin verificar. Están para que sepas que existen.

**Por dónde empezar.** No hace falta contestar las decisiones una a una. La mayoría cuelga de seis, y el Council las deliberó hoy: su veredicto va a continuación y es lo primero que conviene leer. Si lo aceptas, buena parte del catálogo queda contestada o aplazada con motivo.

## Por dónde empezar: el veredicto del Council sobre las seis decisiones raíz

Las seis preguntas que se le plantearon: (1) si se congela algún umbral antes de que monos y plantadas recorran la cadena; (2) cuándo se apaga el sorteo `dev.on`, el atajo de desarrollo que tras el paso 8 deja seguir solo a unas pocas estrategias elegidas al azar; (3) la línea de R3 en el paso 8 —la t del exceso de la estrategia sobre la deriva del mercado, 1,65 o 2,33— y el suelo de operaciones por año; (4) si el paso 10 (otros mercados) descarta o solo anota; (5) quién puede leer `oos2`, el bloque de datos ciego que se gasta una sola vez; y (6) cómo combina el paso 20 los veredictos de los pasos 17 a 19.

### Lo que el Council no sabe

- Si existe un «mono» (estrategia de entrada al azar, sin ventaja) capaz de recorrer los pasos 10 a 19. Hoy solo llega al 8.
- Si 2,33 y 35 operaciones/año son buenos números: sus tablas se borraron.
- Cuántas candidatas quedan con ambos. Puede que ninguna.
- Si los pasos 16.5-19 funcionan con un lote real.
- Si el código aguantará quieto una semana.
- La cifra exacta de la regla de viabilidad: el Council no la fijó.

### Veredicto en una frase

Sella `oos2` y apaga el sorteo hoy, calibra ya el paso 8, y deja que una prueba de horas, con regla escrita antes, decida si se calibra la cadena entera o se acorta.

### El orden de las seis decisiones

| orden | decisión | qué hacer | coste | reversible |
|---|---|---|---|---|
| 1.º | 5 · bloque ciego `oos2` | Extender el sello (criterio escrito y calibrado antes de leer) a 18, 18.5 y 19; cerrar el del 17 | Cero CPU; 17-19 sin lotes reales | Sí el sello; leer `oos2`, no |
| 2.º | 2 · sorteo `dev.on` | Apagado al calibrar; encendido solo para probar código; nunca a mano | Corridas más largas | Sí |
| 3.º | 1 · orden de calibración | No congelar números. Lo no medido cuenta LIMBO, nunca PASA. Prueba de viabilidad primero | Horas; después, según la rama | Sí |
| 4.º | 3 · paso 8 | Fijar la tasa: máximo 1 % de monos pasan con costes. R3 en 2,33 provisional, igual en código y documento. Suelo 35. No mirar más `oos1` | Menos candidatas, en cantidad desconocida | Sí, hasta congelar |
| 5.º | 4 · paso 10 | Anotación, no puerta. Quitar P7 | Los especialistas gastan CPU después | Sí |
| 6.º | 6 · paso 20 | Mantener «peor»; elegir al final | Revisar LIMBO a mano | Sí |

### La prueba de viabilidad y su regla

**Qué se corre**, sin tocar `oos2`: se intenta construir un mono para los pasos 10-19 y se pasan estrategias de ventaja plantada por 10-20. **Duración:** horas, no días.

**Regla, escrita antes de correr:**

- **Cadena entera** si el mono existe del 10 al 19, los pasos 16.5-19 separan plantadas de monos y el código lleva siete días sin cambios de criterio. Coste: días de CPU con todo lo demás parado.
- **Cadena corta** si no hay mono posible, o las plantadas mueren en 16.5-19 como los monos. Se congelan los pasos 6-14, se aparcan 16.5-20 como anotación y solo se calibra el paso 8. Las supervivientes van a Monte Carlo y a MetaTrader 5. Coste: horas de CPU, `oos2` intacto, y una sola puerta medida.

### A qué se renuncia

- A estrategias operables hasta la congelación.
- A candidatas: 2,33 y 35 recortan, sin saber cuánto.
- A filtrar especialistas de un solo mercado, por ahora.
- A un paso 20 mecánico: «peor» deja limbos.
- A elegir hoy entre cadena entera y corta.

### Qué invalidaría este veredicto

Fechas del Chairman, a partir de los siete días del Council.

- Si un cambio toca criterios de los pasos 6-20 durante la corrida o antes del 2026-10-15, el veredicto cae y hay que pasar a cadena corta.
- Si algún paso 17-19 lee `oos2` con un lote real antes de cerrar su sello, el veredicto cae y hay que declarar `oos2` gastado.
- Si la calibración del paso 8 deja pasar más del 1 % de monos con costes antes del 2026-10-15, el veredicto cae y hay que subir la línea de R3.
- Si ninguna plantada pasa el paso 8 con 2,33 y 35 antes del 2026-10-15, el veredicto cae y hay que revisar el suelo.
- Si en cadena corta el Monte Carlo deja pasar monos, el veredicto cae y hay que recuperar 16.5-19.

### Siguiente paso, uno solo

Escribir hoy, 2026-10-08, el sello de `oos2` para los pasos 17, 18, 18.5 y 19.

### Dónde no hubo acuerdo

- **Orden final.** Kahneman y Munger: 3 → 4 → 6. Aurelio: 6 → 4 → 3. Su argumento: los pasos 20 y 10 se deciden sin datos; el 8 es el único que necesita la población.
- **«Una sola puerta medida».** Aurelio avisa: si la prueba falla, toda la validación descansa en el paso 8, sobre un `oos1` mirado dos veces. Pide decirlo con esas palabras. Nadie lo rebatió.
- **2,33.** Kahneman lo defiende por conservador; Aurelio: son dos anclas borradas.
- **Paso 20.** Solo Aurelio propone una revisión predeclarada: pasar a `sin_fallo` si «peor» mata a las plantadas.

### Recuento

- «Viabilidad primero»: 2,875 de 3,5. Umbral de dos tercios: 2,333. Superado. Cadena entera: 0. Cadena corta: 0.
- Silla de peso 1,5×: Kahneman, confianza media (1,125). Munger, media (0,75). Aurelio, alta (1,0).
- Panel: Kahneman, Munger, Aurelio; tríada `decision`. Chairman: Opus, mismo proveedor que el panel.
- Modo completo, 3 rondas, 2 envíos de control para la comprobación de acuerdo.
- Diversidad de perspectivas 3/5; de proveedor 1/5. Riesgo de convergencia: alto.

Qué significa: tres sillas de una misma familia de modelo. Su unanimidad vale como una opinión revisada, no tres independientes. Fíate de lo mecánico (sellar es gratis, el sorteo encoge la muestra); trata 2,33 como apuesta.

**Dos cosas que el Council no tenía delante y conviene que sepas al leerlo.** El código de hoy tiene R3 en 1,65 y sin Limbo (`pipeline/autopilot/criteria.yaml:85`); el 2,33 que recomienda mantener mientras tanto es el de la propuesta escrita, así que aceptarlo es un cambio en el código, no dejarlo como está. Y el sorteo `dev.on` está hoy encendido y deja seguir a 3 estrategias.

## Cuántas decisiones hay y dónde

| paso | decisiones tuyas |
|---|---|
| 6 — Build | 11 |
| 8 — Puerta IS/OOS | 15 |
| 10 — Otros mercados | 9 |
| 10.5-12 — Otras temporalidades | 8 |
| 13-14 — MC Retest | 9 |
| 15-16 — SPP | 3 |
| 16.5 — Variantes y nube | 8 |
| 17 — WFC | 5 |
| 18 — CSCV | 4 |
| 18.5 — Superficies por mercado | 7 |
| 19 — WFM | 6 |
| 20 — Veredicto conjunto | 4 |
| Transversal | 9 |
| Tests y código | 7 |
| **Total** | **105** |

Son 105 preguntas, pero no 105 respuestas: las seis del Council arrastran a la mayoría, y casi todos los umbrales del bloque «lo resolverá la calibración» se contestan con una sola corrida.

# El catálogo, paso a paso

## Paso 6 — Build

### Decisiones tuyas

**P6-1 · ¿Qué suelo de operaciones por año exiges: 10, 35 o 40-50, y dónde (en el Build o en la puerta del paso 8)?**
Hay tres cifras vivas a la vez. El Build (el filtro que SQX aplica al generar) admite estrategias desde 10 operaciones al año (13-16 en índices y crudos) con techo de 75 en H1 y M30 y de 100 en H4. La puerta del paso 8 (R4a, el suelo de operaciones al año del tramo de construcción) da «Pasa» con 35 o más, «Limbo» (ni pasa ni falla) de 20 a 35 (15 en H4) y «Falla» por debajo. Tu memoria dice «al menos 35 al año» desde el 2026-10-02 y OPEN #93 recoge 40-50 como tu preferencia. Subir el suelo de 20 a 50 baja el rendimiento de 31,7 a 8,6 por mil; el propio `_study.yaml` dice que un suelo de 35 como descarte pierde el 81 % de las robustas (el descarte de 20 pierde el 51 %). Además, el Build gasta CPU en estrategias de 10-20 al año que el paso 8 descarta por construcción. Otras dos consideraciones de los informes: (1) el suelo de 35 quita justo la reversión diaria de índices que la literatura documenta (5-8 operaciones al año); (2) más operaciones por año no compran más t (la proporción con t ≥ 1,65 cae al subir la frecuencia), y para llegar al 80 % de potencia con Sharpe por operación 0,15 hacen falta 89 operaciones al año (≈112 en NIKKEI225).
- **Opciones:** (a) subir el suelo del Build; (b) bajar el de la puerta; (c) para índices × reversión: una excepción, agrupar por clase de activo, o asumir la pérdida (hay que llevarte el coste medido); (d) la variante de Munger: dejar pasar 20-35 operaciones al año si la t es ≥ 2,33 (no tratada).
- **Hoy el código hace:** Build 10-75 (H4 10-100, índices y crudos 13-16); puerta 35 / 20 (H4 15) con Falla por debajo.
- **De esto cuelga:** cuántas estrategias llegan al OOS y la CPU del build; la firma del paso 8 (P8-4).
- **Fuente:** enc. 41:141; enc. 42:164-166; `assets/_study.yaml:30-42`; `pipeline/autopilot/criteria.yaml:79-81`; OPEN #93 (líneas 702-704, 745); memoria «minimo-operaciones-por-ano»; IND:32,66,69; EXP:278-288,659; K `research/trade-t-vs-frequency-and-skew.md:6-13`.

**P6-2 · ¿Firmas las cifras actuales del paso 6 (techo 75, suelo 10, PF 1,0, beneficio > 0) o pides una calibración nueva?**
Las cifras de `assets/_study.yaml` y el dossier `criterios-implementados-2026-10-12` salen de 203 poblaciones (990.820 estrategias) construidas el 2-3 de octubre. Las borraste el 2026-10-04 («un fiasco», spread equivocado) y la evidencia ya no se puede reproducir. Aun así el constructor las escribe en cada proyecto nuevo. La memoria dice que no se firmen ni se construya sobre ellas sin una calibración nueva con los spreads recalibrados (commit 3b71384) o con tus números. El mirar `oos2` en esa calibración ocurrió igualmente. El dossier del 10-04 tiene además secciones vacías («PENDIENTE»): decisión 6 (pasos 10 y 12), §7, §8, §9 «lo firme y lo provisional» y §12.
- **Opciones:** (a) calibración nueva con spreads recalibrados; (b) tus propios números.
- **Hoy el código hace:** usa las cifras tal cual.
- **De esto cuelga:** todo build nuevo y el criterio de entrada del paso 8.
- **Fuente:** enc. 41:32,151-158; enc. 42:33-36,139-142; OPEN #93 (nota 2026-10-04, línea 747); `assets/_study.yaml:3-6,40-46`; `criterios-implementados-2026-10-12.md:3,23,27-45,260-274,316-318`; WORKFLOW.md:31,245; memoria «oos2-autorizado-para-calibrar-criterios».

**P6-3 · ¿El filtro de calidad en el IS (dentro del período de construcción) va dentro del Build o se aplica después?**
Siete brazos de filtro IS dentro del build rinden un 70-98 % menos de robustas en `oos1` por minuto que el mismo corte aplicado después. Solo «PF ≥ 1,3 y Ret/DD ≥ 3» sube la pureza ×1,54 (intervalo 0,86-2,43, que incluye «ningún efecto»; en `oos2` ×3,3, intervalo 1,6-4,6) y casi todo por una celda. Falta probar builds de 180 min con la databank llena, donde la pureza sí importa. El único filtro que replicó es «Sharpe IS ≥ 0,6 aplicado después del build».
- **Opciones:** dentro del Build (sin decidir) o después.
- **Hoy el código hace:** aceptación mínima en el Build (`NumberOfTrades` ≥ 100, `NetProfit` > 0).
- **De esto cuelga:** la CPU del build.
- **Fuente:** K `research/is-filters-inside-the-build.md:7-12`; C04:13-23,108-110,128-133; EXP:658,675.

**P6-4 · ¿Qué paleta de bloques usa la calibración nueva: los originales, los `_v2` o los `_v3`?**
Hay tres juegos en `sqx/blocks/palettes/`: los originales (148-180 bloques) llevan bloques de reloj y de stop/limit; los `_v2` (6-13 bloques) son «la familia y nada más»; los `_v3` (99-127) incluyen `pullback_base_v3` y los termina otra sesión. Ninguno consta como aprobado. Las 28 poblaciones de la calibración borrada usaron la paleta ancha (842 bloques) y habría que reconstruirlas por familia.
- **Opciones:** originales, `_v2` o `_v3`.
- **De esto cuelga:** la calibración nueva (P6-2) y todo build por familia.
- **Fuente:** enc. 42:158-160; WORKFLOW.md:248; OPEN #93 (líneas 714-717, 742-745).

**P6-5 · ¿Cuentan como «leer el reloj» (regla 15) los bloques `SessionHigh/Low/Open/Close`, `HighD/LowD/OpenD`, VWAP anclado, `HighestInRange` y `CBlock_TimeBreakout*`?**
Hoy solo se rechazan los bloques nativos «Bar And Time». Hasta que respondas, la familia «sesión» no se corre.
- **Opciones:** sí cuentan (se vetan) o no cuentan (se admiten).
- **Hoy el código hace:** rechaza solo «Bar And Time».
- **De esto cuelga:** qué familias de ideas se pueden construir.
- **Fuente:** enc. 42:161-162; OPEN #93 (líneas 739-741); WORKFLOW.md:248; B5 del dossier.

**P6-6 · ¿Se gastan builds en las 7 celdas marcadas «medido en contra» en `FAMILIAS.md`?**
Solo se hace si tú lo dices.
- **Hoy el código hace:** no se gastan.
- **Fuente:** enc. 42:106,163.

**P6-7 · ¿Toda estrategia debe llevar regla de salida obligatoria, también con plantilla?**
Hoy `exits.condition_required` solo es obligatoria en Simple Strategy (la que no usa plantilla); en la Simple Strategy la salida es aleatoria al 50 % (como en su proyecto) y luego 1-2 condiciones.
- **Opciones:** obligatoria siempre, o aleatoria al 50 %.
- **Fuente:** enc. 42:167-168; OPEN #93 (líneas 737-739).

**P6-8 · ¿Confirmas el presupuesto de máquina para la calibración (40 h de builds)?**
El 2026-10-02 dijiste que 40 horas de builds eran aceptables. Hay que confirmarlo con la duración medida por población; la caja de tiempo (250 × 20 islas = 5.000 individuos por generación) está sin medir.
- **Fuente:** enc. 42:80-82,169-170.

**P6-9 · ¿Cómo se construye la población sin seleccionar que pide la calibración (regla 19)?**
Se necesita una población sin seleccionar (≥ 100 operaciones y beneficio > 0, databank nunca lleno) y su gemela aleatoria. `bin/workflow.sh` no pasa `--acceptance calibration` ni `--random` al constructor, y la regla 19 prohíbe conducir los pasos a mano. El encargo dice «no la tomes tú».
- **Opciones:** (a) que `bin/workflow.sh` aprenda a construir poblaciones de calibración (aceptación mínima, gemela aleatoria, parada antes de llenar) y todo pase por él; (b) autorizar la llamada directa al constructor para este estudio, fuera de la regla 19.
- **De esto cuelga:** todo el encargo 42, y por tanto el 43 (pasos 10 a 20).
- **Fuente:** enc. 42:56-70,154-157; README encargos:131-132.

**P6-10 · ¿Qué riesgo por operación asumen las cuentas de fondeo?**
Es una decisión pendiente del dossier de criterios 6 y 8 (§1); OPEN no da cifra.
- **De esto cuelga:** el tamaño de posición que suponen los umbrales de drawdown y supervivencia.
- **Fuente:** OPEN #93 (línea 704).

**P6-11 · ¿Qué objetivo debe optimizar la búsqueda genética (GA)?**
El ruido entre ejecuciones (~16 puntos porcentuales) supera el efecto de cualquier objetivo; con una ejecución por brazo no se puede ordenar. Hacen falta réplicas por brazo o semilla fija antes de poder decidir.
- **Fuente:** K `research/ga-target-choice.md:6-10`.

### Lo resolverá la calibración

| Regla | Valor de hoy | Quién lo puso | Qué falta para fijarlo |
|---|---|---|---|
| Operaciones/año del Build (H1, M30) | 10-75 (índices y crudos: suelo 13-16) | agente (propuesta); evidencia borrada | calibración nueva (P6-2) |
| Operaciones/año del Build (H4) | 10-100 | agente; «H4 no se ha recalibrado» | recalibrar H4 |
| Profit factor mínimo del IS / beneficio neto mínimo | 1,0 / 0 | agente | calibración nueva |
| Hecho «PF IS» | no existe como hecho | — | exponerlo para poder escribir una regla `PF ≥ 1,10` en el paso 8 |

### Trabajo pendiente que no necesita tu respuesta

- Ninguna Simple Strategy se ha arrancado nunca en SQX (solo existen los ficheros); tampoco se ha corrido ninguno de los 17 activos nuevos (DAX40 y USOIL solo se construyeron en un install temporal; DAX40 no está en ningún proyecto de SQX). Falta una población de prueba de cinco minutos por activo y comprobar el spread por tramo con `core.assets`. Fuente: OPEN #93 (713, 730-732), OPEN #28; enc. 42:44-52.
- El lado de plantilla con idea fija se escribe `1..1` (idea + exactamente una aleatoria), no el `0..1` que pediste: SQX tiene un único rango de condiciones por lado. «La idea sola» no se construye desde plantilla hasta que un build corto pruebe si un hueco ligado con mínimo 0 conserva su bloque. Fuente: OPEN #93 (733-736).
- Un hueco libre puede resolverse en un `AND` anidado de dos condiciones (el 39 % en Donchian + libre tiene 3), lo que choca con la regla 14; un hueco ligado a grupo se desvió de su bloque en 180 de 5.026. Fuente: K `sqx-drive/unselected-build-population.md:6-13`.
- Los interruptores de `BuildingBlocks` solo gobiernan huecos libres y la generación genérica; SQX ignora los pesos de la paleta en comparadores y valores genéricos. Todo lo aplicado entre el 2026-10-01 22:41 y el arreglo se construyó ancho. Fuente: K `authoring/builder-block-switches.md:6-13`.
- Una plantilla con bloque en el gráfico 1 aborta la build y el constructor no la rechaza antes de lanzar (fallan `filterMALong`, `filterMAShort` y sus `_withExit`, y `spRSI2`; las otras 56 usan solo el gráfico 0). Fuente: K `authoring/template-second-chart-aborts-build.md:6-12`.
- Un build `Trade_` llena el databank en minutos y luego reemplaza por Ret/DD IS durante el resto de sus 180 minutos: selección que nadie ha medido. Test propuesto: 180 min contra 6 min. Ningún filtro IS se probó con el databank lleno. Fuente: OPEN #93 (714-717).
- La isla es la unidad de azar del build genético: los recuentos por destino se dispersan entre islas con φ ≈ 38× la varianza binomial (19 de 56 supervivientes del paso 8 venían de una isla de 20); hay que comparar builds por islas completas. Fuente: K `research/genetic-build-islands-are-the-sampling-unit.md:6-12`.
- Proxies IS por operación (TRL, SQN, ZScore, R Expectancy): dentro del decil superior de Sharpe IS se inclinan en positivo 5 de 5, pero son un solo eje y contradicen un resultado de nueve candidatos; no son filtro hasta pasar por `improvement.py` y `replication.py`. Fuente: K `research/is-proxies-top-decile.md:6-10`.
- Corpus XAUUSD: 231 estrategias, todas largas con `SLPT.None`; la división «tope de 8 barras» frente a «salida por señal» es 🤔 (n = 11 en un brazo) y las cifras no se reproducen desde la raíz de datos actual. Fuente: K `locations/xauusd-corpus.md:6-13`.
- Perfil de mercado a medias: el top-up se paró el 2026-10-02; solo DAX40 y DJ30 tienen las seis medidas de TR-65; `measures.csv` y `assets/FAMILIAS.md` muestran filas viejas. Completarlo con `--top-up` y `--familias`. Fuente: OPEN #100 (819-825).
- Encargo 42 sin ejecutar en su diseño: dosis-respuesta del paso 6 (suelos de 20, 25, 30, 35, 40 y 50 operaciones al año con PF, KER, Sharpe, Ret/DD, SQN, estabilidad y estancamiento), A/B dentro y fuera del Build con réplicas, build largo con databank lleno frente a corto, familia, riesgo flotante y equipo rojo. Entregable: dossier en castellano con PDF y recalibración de `_study.yaml` y `criteria.yaml`, marcada como propuesta de agente. Fuente: enc. 42:97-134,136-150.
- Los dossiers `criterios-implementados-2026-10-12.md` y `criterios-implementados-2026-10-12.md` deben llevar en cabecera el aviso de que sus cifras no valen. Fuente: enc. 42:139-142.
- La fila 6 de `WORKFLOW.md` sigue diciendo «PF ≥ 1,20, beneficio > 0» y cita un A/B de suelos (`calib_final/ab_build.md`, borrado el 2026-10-04); hoy `_study.yaml` tiene PF 1,0. Fuente: WORKFLOW.md:245; `assets/_study.yaml:44-45`.
- Los 17 activos nuevos exigen comprobar coste/spread por tramo; costes provisionales heredados (XAUUSD `costs_provisional`, OPEN #26; XAGUSD, UKOIL, USOIL con `provisional_costs`) arrastran avisos en todos los estudios y todo número en R de esos activos. Fuente: WORKFLOW.md:33-34; `studies/research/board/config.yaml:45`; `marketSurfaces/inputs/markets.py:33-36`.

## Paso 8 — La puerta IS/OOS

Contexto mínimo: la puerta del paso 8 compara el tramo de construcción (IS) con el primer tramo fuera de muestra (`oos1`) y decide Pasa / Limbo (ni pasa ni falla) / Falla por reglas R1-R9. «Mono» es una estrategia de entradas al azar usada como grupo de control. `dev.on` es el interruptor de desarrollo que, mientras se construye el workflow, tras aplicar las reglas conserva solo unas pocas estrategias elegidas al azar.

### Decisiones tuyas

**P8-1 · ¿Con qué línea pasa la regla R3 (la t del exceso sobre la deriva del mercado): 1,65 sin Limbo, o Pasa a 2,33 con Limbo desde 1,65?**
R3 es la regla principal del paso 8: mide la t del exceso de la estrategia sobre lo que habría ganado solo por la deriva del mercado en oos1. A 2,33 el falso positivo es del 0,6 % y la mejora (lift) de +103 por 1.000 (apoyado en solo 18 celdas con ≥ 10 aprobadas, IC +31…+175); a 1,65 es del 3,9 % y +52 (IC +24…+83). En NIKKEI225 M30 pasan 44 a 2,33 y 325 a 1,65 de 10.000, indistinguibles del azar (15-60 y ≈ 390). La sesión recomendó el 2026-10-04 «apenas importa; juzga con `drift_excess_t`» y la escala de la t se corrigió el 2026-10-02 (viejo 1,3 → 1,42; 1,65 → 1,92; 2,0 → 2,55). La medición del falso positivo bajo el nulo (0,00 % con costes y 0,58 % sin ellos a 2,33; 0,07 % / 3,6 % a 1,65) no se puede reproducir porque las tablas se borraron el 2026-10-06. Preguntas que seguían abiertas en OPEN #91: ¿sigues usando XAUUSD/OOS?, ¿el nulo que define «edge» lleva costes o no?, ¿está final la ficha de XAGUSD? Hecho comprobado en el árbol de trabajo: hoy manda 1,65 (ver «Documentos que se contradicen»).
- **Opciones:** (a) 1,65 sin Limbo y sin excepciones por timeframe (hoy); (b) Pasa ≥ 2,33 con Limbo desde 1,65 (la versión anterior); (c) otra línea con las tablas de la calibración delante.
- **Hoy el código hace:** `drift_excess_t ≥ 1,65` pasa; sin dato falla; sin Limbo.
- **Recomendación del agente:** la sesión de OPEN #91 recomendó juzgar con `drift_excess_t`, Limbo ≥ 1,65 y Pasa ≥ 2,33 (superada por el encargo 44, que pone 1,65 sin Limbo).
- **De esto cuelga:** todos los falsos positivos citados, K-m y la firma de la parada 2.
- **Fuente:** `pipeline/autopilot/criteria.yaml:85`; OPEN #91 (548-560); enc. 41:151-158; enc. 44; EXP:193,657; C04:193; DP:240-268; K `research/gate-t-scales.md:6-13`.

**P8-2 · ¿Ventana de la deriva de R3 (y del mono): año o semestre?**
Elegiste la variante `d` el 2026-10-07 pero no dijiste nada de la ventana. R3 tiene cuatro variantes del término de deriva (a hoy; b por ventana; c operación ciega; d = b + c). Sesgo medio absoluto: a 0,09; b 0,12-0,15 (máx. 0,33); c 0,016; d 0,017 («usa d, o c, nunca b»). El sesgo mueve la t sin ventaja entre ±0,02 y ±0,27 (EURUSD H1 a 1,65: 2,6 % en largos frente a 5,8 % en cortos); para NIKKEI225 largo no está medido. La ventana es también la del mono y su mínimo es un trimestre; K-m depende de ella. Z0 «Cargar la ventana y la variante» está pendiente de esta respuesta.
- **Opciones:** año (provisional, hoy) o semestre. D-m dio las tablas de la variante d: 0,017 de sesgo por lado frente a 0,09 de hoy.
- **Hoy el código hace:** año, con AR(1) (autocorrelación) fuera de la fórmula; el criterio usa hoy la variante (a) según una lectura, y no consta cuál variante está cargada.
- **De esto cuelga:** Z0, K-m (el embudo de las poblaciones de prueba), la tabla de líneas y copias en los pasos 10 y 12.
- **Fuente:** enc. 44:43,89-94,297-303,510-512,762-763; ESP:411-430,1056-1058,1234; MONO:163; K `research/drift-term-biased-by-side.md:6-13`.

**P8-3 · ¿Metes AR(1) y la corrección de sesgo y curtosis (error estándar) en la t de R3?**
«AR(1) dentro o fuera lo decide el dueño en la parada 1, con las cuatro combinaciones de D-m». No dijiste nada y queda fuera de la fórmula. La corrección de sesgo, curtosis y n efectivo se midió «por separado, no juntos»; hay que comprobar que la nula dé una tasa compatible con el 5 % antes de cargarla (los γ3 y γ4 de A no están calculados). Mejora medida: USA500 H1 `indicesIBS` 6,9 % → 5,1 % a 1,65; con sesgo ≈ −1,5 (reversión sin stop) la t por operación rechaza una estrategia sin edge el 6,9 % en vez del 5 %.
- **Opciones:** las cuatro combinaciones de D-m (AR(1) dentro/fuera × corrección de sesgo y curtosis dentro/fuera).
- **Hoy el código hace:** AR(1) fuera; la corrección no está cargada.
- **Fuente:** enc. 44:89-94,308-309,863-865; ESP:458,468-478,1158-1160; K `research/trade-t-vs-frequency-and-skew.md:6-13`.

**P8-4 · ¿Congelas las líneas definitivas de Pasa / Limbo / Falla de cada regla del paso 8 («parada 2»)?**
Las líneas de la tabla 1.2 son «las de partida», no calibradas. Las definitivas salen de K-m y se te entregan en la forma «a 1,65 pierde el X % de las de 0,10 y deja pasar el Y % de las nulas». Cambiar el dato de una regla invalida la tasa de falsos positivos con que se fijó su línea. Con la R3 a 1,65 (p = 0,05, una cola) pasarían unas 405 de 240.000 sin ventaja en bruto (87 netas de costes en `oos1`); en el caso sintético de 196 operaciones R3 deja pasar el 0,9 %, 13 %, 34 % y 62 % de nulos según el nivel plantado (el 62 %, para 0,15, pierde muchas buenas). Con 8 reglas que pierden un 5 % de las buenas cada una se pierde ≈ 34 %. Las líneas de R8 a 1,65 no son p = 0,05 (quitar lo mejor baja la t de cualquiera y deja un sesgo negativo que D.3 corrige; el coste en estrategias buenas lo da K). Cifras vivas: R3 ≥ 1,65; calidad de datos y retraso con `ret` ≥ 0,6 (Limbo ≥ 0,25); R8 t ≥ 1,65 (Limbo > 0); R9b MAE p95 ≤ 1,5 (Limbo ≤ 2,5); R6 `dd_p` > 0,10 (Falla ≤ 0,01); edge por coste ≥ 2 con t ≥ 1,65 (Limbo ≥ 1,25). Detalle de cada una en la tabla siguiente.
- **Opciones:** congelar con los números de K-m delante (cada línea con su coste en estrategias), o seguir con las líneas de partida.
- **Hoy el código hace:** la puerta calcula y anota; toda línea es «convención»; `dev.on` sigue encendido.
- **De esto cuelga:** Z1 (cargar las líneas congeladas en `criteria.yaml` y el ledger), V (corrida de verificación), apagar `dev.on` (P8-8) y lanzar proyectos `Trade_` reales.
- **Fuente:** `criteria.yaml:59-126`; enc. 41:151-158; enc. 44:50,136-137,179-183,314,345-347,463-483,506-512,815-817; IND:84-96; ESP:104-105,1157,1235; WORKFLOW.md:33.

**P8-5 · ¿Tope del centrado de R5d y si se mantiene el ±0,35 de R5?**
R5 mide la estabilidad de la frecuencia de operaciones y R5d la degradación del exceso entre construcción y `oos1`. `centring.cap_slope` no tiene valor y K-m lo propone; el ±0,35 en log de R5 es tuyo (por tu razonamiento de plantillas) pero sigue siendo parámetro. El centrado exige un mínimo de 30 estrategias y con menos no se centra. R5 usa φ acotado a [1,5; 3,5] y bandas de |z| 1,5 / 3,5 (la propuesta hablaba de 2 y 3). Falta calcular el φ̂ real, la mediana poblacional por activo, timeframe y lado (mín. 30) y contar cuántas de las 169 vivas cambian de estado. R5d solo puede dar Falla si el exceso proyectado al final es ≤ 0, porque con 4 años casi no detecta nada (una caída lineal total en `oos1` da t_b = −1,46); se propone una versión con descarte (t_b < −2,33) en los pasos con muestra nueva (10, 12, 20), no implementada.
- **Hoy el código hace:** `cap_slope` sin tope; R5 y R5d «diagnostic only (owner, 2026-10-07)»: Limbo si `t_b` < −1,65; Falla si además `e_fin` ≤ 0.
- **De esto cuelga:** la tasa real de falsos positivos del paso 8.
- **Fuente:** enc. 44:333-339,447-448,513-514,672-678; `falsePositives/README.md:77-84`; `gate/config.yaml:73-75`; ESP:620,693,717,1186,1236; R5:124-131,228-271.

**P8-6 · ¿Añades un suelo duro de 60-80 operaciones en `oos1` (R1b / R5b)?**
Hoy R5b es red sin descarte: menos de 100 operaciones en `oos1` va a Limbo. El índice deja el suelo duro como opcional y solo se pregunta si los números lo piden.
- **Opciones:** red actual (Limbo < 100) o suelo duro de 60-80.
- **Hoy el código hace:** la red (Pasa ≥ 100, si no Limbo; nunca Falla).
- **Fuente:** enc. 44:518-519,814; IND:28,35; ESP:1238; R5:264-271; `criteria.yaml:83`.

**P8-7 · ¿Factor k del coste estresado en R5c: 1,25 (cargado) o 1,5 (propuesto)?**
La propuesta justificaba 1,5 porque «en NIKKEI225 el spread de SQX está en el percentil 10 del real», pero ese hallazgo decae: era contra el spread de Darwinex y el estudio de spread se eliminó. Falta medir el coste pagado solo en `oos1` y confirmar que el denominador sale de los costes calibrados MT5-SQX. El edge por coste ≥ 2 daba lift +34 y no cambia el total en NIKKEI225 M30 (las 653 que mata ya estaban fuera); Carver pediría 3; el lift en H1 es +19 (IC incluye 0) y en M30 +81, y falta el bootstrap de H1 y M30.
- **Hoy el código hace:** k = 1,25, edge ≥ 2 con t ≥ 1,65; Limbo con edge ≥ 1,25.
- **Fuente:** ESP:672,1182; R5:196-207,264-271; E45:65-89; EXP:250,648,660,663; C04:190; IND:71; `criteria.yaml:92-94`.

**P8-8 · ¿Cuándo apagas `dev.on` (parada 3) y qué hace mientras tanto?**
Con `dev.on` encendido, tras aplicar las reglas del paso 8 se conservan solo `sample` estrategias al azar y se borra el resto sin mirar el veredicto (decisión «meanwhile» del 2026-10-01 que no se ha revisado). El comentario del yaml dice «`on: false` once the criteria below are the real ones». Lo apagaste y encendiste a mano 4 veces entre el 10-07 y el 10-08 para los runs de 10.000. La auditoría del 10-05 avisa de que el paso 8 del `WORKFLOW_TIMING_BASELINE` usó `--smoke` (1.000 → 10 «por sorteo») y no debe leerse como un cribado. Mientras `dev.on` esté encendido, el contador de supervivientes que llega al 10 no es el de la puerta. Se apaga «solo cuando el dueño lo diga y con V a la vista».
- **Opciones:** apagarlo ya, tras P8-4 y V, o seguir como está.
- **Hoy el código hace:** `dev: {on: true, sample: 3, at: ["8"], seed: null}` (OPEN #93, línea 704, dice 5: está desfasado).
- **De esto cuelga:** cuántas estrategias llegan al 10 y que todas las supervivientes pasen por 16.5-19.
- **Fuente:** `criteria.yaml:3-8,52-56`; `ledger/criteria-history.jsonl`; enc. 44:19,483,827; OPEN #93 (703), #90 (654-656); audit 2026-10-05:16; IND:84-96.

**P8-9 · ¿Se vuelve a leer `oos1` para elegir umbrales, sabiendo que ya se gastó dos veces?**
`oos1` ya fue leído dos veces para elegir umbrales (USDJPY y XAUUSD). Dado que la calibración se borró, cualquier umbral futuro elegido sobre esos `oos1` hereda esa mirada («freeze them before the next build»).
- **Opciones:** volver a leerlo diciéndolo en el dossier, o no.
- **Fuente:** enc. 42:171-172; OPEN #93 (718).

**P8-10 · ¿Mantienes R3 sin excepciones por timeframe (H1 y H4) «por ahora»?**
Las excepciones por timeframe de R3 se han quitado. Si las poblaciones de prueba enseñan que una regla se comporta distinto por timeframe se te propone, no se carga. Solo existe una población grande (USA500 H1 largo): nada sobre H4 ni cortos se podrá proponer. La calibración por timeframe (H1, H4) sigue abierta.
- **Fuente:** enc. 44:312-313,515-517,886; IND:71.

**P8-11 · ¿Qué umbral marca el criba de MAE profundo (`maeDepth`)?**
`maeDepth` solo mide (k = 3 y 4 ATR; anómalas por duración, media + 2,5 sd) y hoy «no marca a nadie»: `verdict.min_cuota_rec: null`. Los valores `k [3, 4]`, `slippage [0, 0,25, 0,5]` y `action: mark` los puso el agente, «pendiente de confirmar si se leen los dos k o manda uno». Hallazgo: en poblaciones con salida tras X barras o fin de viernes, el corte media + 2,5 sd queda por encima de cualquier operación y `anom*` da 0; lo que lleva señal son las profundas (≥ 3 ATR: 26 % de las operaciones del build y 33 % del neto; en `oos1` 24 % y 8 %). El código no cambia el corte.
- **Opciones:** `mark` o `drop`; uno o dos valores de k.
- **Hoy el código hace:** solo mide.
- **Fuente:** WORKFLOW.md:33; `maeDepth/config.yaml:13-17`; `thresholds.yaml:1162,1172,1190`; K `export/maedepth-duration-cut-exit-after-x.md:6-13`.

**P8-12 · ¿Qué se hace con una operación de `oos1` que se abre y se cierra dentro de la misma barra (stop/target)?**
`level1a.py:38` (assert) y `edgeCost/costs.py:48` se rompen en ese caso. Afecta al 0,04-0,14 % de las operaciones en donchian, emaCloseCross y timeRangeBreakout, y a todas las versiones con stop del paso 25. La bitácora lo dejó como «Roto y preguntado» y las respuestas posteriores no la mencionan. También quedó sin respuesta visible la pregunta «retraso de una parada» del nivel 2 (el mono sin stop sí lo diste por válido y USDJPY quedó resuelto).
- **Fuente:** enc. 44:110-117,125-127,126-139.

**P8-13 · ¿Cómo se dimensiona y qué papel tiene el mono (estrategia de entradas al azar)?**
Quedan abiertas las decisiones 2-6 del documento del mono: tamaño de doctrina, cuántas de las 169 discrepan, recalcular la criba de familia con z, lista de mercados y Z combinado. Hoy el mono es el control de R3 (Pasa exige z ≥ 1,65; Limbo si discrepa; «Falla: nunca»). Con tamaño de donante el MAE flotante queda fuera de cualquier regla de sizing y `oos_worst_trade_mae_r` y `oos_worst_day_r` infraestiman el falso positivo; en USA500 H1 los lotes reales promedian 19,4 y los de sorteo ATR 31,1: la tarjeta pide informar ambos y que elijas. En la prueba pequeña sobre `Test_XAUUSD_donchianUpperCrossUp2_H1` (300 donantes × 10) cruzan el paso 8 entre 14 y 36 de 3.000 según cómo se dimensione el mono. El encargo 44 fijó después el tamaño por ATR de la barra anterior. En USA500 H1 `z_mono` correlaciona 0,971-0,992 con `drift_excess_t` y ninguna de 300 llega a 1,65 (un solo activo y timeframe). Además: el documento del mono propone combinar mercados con Stouffer mientras EXP:329 y P10 dicen que Stouffer está «prohibido como criterio» (deja pasar 5-24 % de estrategias sin edge) y se usa la t conjunta semanal; sin resolver cuál va en el mono.
- **Opciones:** dimensionado de donante o por ATR; informar ambos y elegir; Stouffer o t conjunta semanal.
- **Hoy el código hace:** tamaño por ATR de la barra anterior; mono como control de R3.
- **De esto cuelga:** K-m, el 1.7 (monos por la cadena) y el mono del paso 10.
- **Fuente:** enc. 41:211-220; enc. 44; IND:44,134; MONO:142-170; ESP:1032,1069; EXP:301-303,329; P10:378; K `research/monkey-reprice-audit.md:7-13`, `monkey-size-carries-donor-volatility.md:6-14`, `gate-monkey-z-tracks-drift-t.md:6-7`.

**P8-14 · Estrategias archivadas antes del 2026-10-01 con reloj distinto: ¿congelar al archivar o re-cosechar?**
Las operaciones archivadas están en reloj Asia/Jerusalem y las barras en EETUS (1 h de diferencia en semanas de desfase DST). El universo rechaza el miembro (licencia < 99 %). Producción sigue leyendo en vivo.
- **Opciones:** congelar al archivar, o re-cosechar.
- **Fuente:** K `export/archived-trades-vs-reclocked-bars.md:6-13`.

**P8-15 · ¿Qué valor de «dato ausente» (`missing`) lleva cada regla: Pasa, Limbo o Falla?**
Hoy es `limbo` en todas las reglas salvo las que declaran otra cosa; debes elegir regla por regla. Solo el paso 8 declara segmento (`oos1`); los pasos 10-16 no. Además: ¿un «Project stopped» manual cuenta como fallo o como parada?
- **Fuente:** DP:213-236.

### Lo resolverá la calibración

| Regla | Valor de hoy | Quién lo puso | Qué falta para fijarlo |
|---|---|---|---|
| R1a presencia y R1b sanidad | `presencia_passed ≥ 1`, `sanidad_passed ≥ 1`; sin dato falla | tú (P.5 bis) | nada; es decisión tuya |
| R2 neto de `oos1` | `estaticas_value > 0` | tú | nada |
| R4a operaciones/año del build | Pasa ≥ 35, Limbo ≥ 20 (H4 ≥ 15) | parcial: el 35 es tuyo; la banda sin medir | medir la banda con s_min económico y potencia (depende de los años de `oos1`) |
| R5b operaciones en `oos1` | Pasa ≥ 100, si no Limbo | tú | P8-6 |
| R3 `drift_excess_t` | Pasa ≥ 1,65; sin dato falla | tú (nula del mono: pasa el 0,9 %) | K-m, P8-1, P8-2 |
| R5 `z_frec` | Pasa en [−1,5; 1,5], Limbo en [−3,5; 3,5] | agente; solo diagnóstico | φ̂ real y recuento de las 169 (P8-5) |
| R5c `edge_mean_oos` y `t_exceso_k` | Pasa edge ≥ 2 y t ≥ 1,65; Limbo edge ≥ 1,25 | parcial (la K 1,25 es tuya) | P8-7 |
| R5d `t_b` / `e_fin` | Limbo si `t_b` < −1,65; Falla si además `e_fin` ≤ 0 | agente; diagnóstico, `cap_slope` null | K-m |
| R8 `t_sin_mejor_trimestre`, `t_sin_3_mejores` | Pasa ≥ 1,65, Limbo > 0 | agente | coste en buenas (3 operaciones fijas o ≈ 2 % de n) |
| R9b `mae_p95_r` | Pasa ≤ 1,5, Limbo ≤ 2,5 | agente, «orientativos» | la mediana de la peor MAE de la población es −3,72 R |
| Calidad de datos | `n_afectadas == 0` o `ret_datos ≥ 0,6` (Limbo ≥ 0,25) | agente | distribución de `retraso_ret_min`; `feedQuality` sin datos |
| Retraso de una barra | `retraso_ret_min ≥ 0,6` (Limbo ≥ 0,25) | agente | idem |
| R7 `q_p` / R6 `dd_p` / mono `z_mono` | R7 Pasa > 0,05; R6 Pasa > 0,10, Limbo > 0,01; mono ≥ 1,65; R7 y mono nunca fallan | agente | sensibilidad de R6 a L (hoy L = 8 y 5.000 secuencias; probar 5-10 o √n_IS); R7 con meses (K = 36-60 pero 3-4 operaciones/mes) y las dos ventanas de R3 |
| R9a / R9c (peor día, DD sobre neto) | salieron de la puerta | tú (aceptaste el hueco) | encargo 45 (módulo de fondeo) |
| Tasa de falsos positivos del paso 8 | convención | Council 2026-10-04 | población nula + plantada ≥ 5.000 por nivel (0,05 / 0,10 / 0,15 de Sharpe por operación; EXP añade 0,04) con la cascada apagada |

### Trabajo pendiente que no necesita tu respuesta

- K-m (embudo de las dos poblaciones de prueba) sin ejecutar: debe correr sobre todas las cosechas completas (≥ 30 estrategias, con MAE y curva) más USA500 H1 y las 10.000 de NIKKEI225 M30, y entregar por regla y nivel el Pasa/Limbo/Falla, el embudo, el tope de R5d, R7 con las dos ventanas, H1 frente a M30 y si R1b pide suelo; espera poblaciones nuevas con la máquina libre. Fuente: enc. 44:50,131-132,813,885-886.
- Z0 (cargar ventana y variante), Z1 (cargar líneas congeladas en `criteria.yaml` y `ledger/thresholds.yaml`) y V (corrida de verificación con `bin/workflow.sh` entero, nunca `--smoke`, proyecto `Test_` retirado al acabar, custodio libre) pendientes de P8-2/P8-4. Fuente: enc. 44:817,823,825.
- Parte M (documentación) pendiente: README de la puerta, `pipeline/autopilot/README.md`, skills `oos-gate` y `workflow-simple`, capítulo 29 del manual, `ui/text/glossary.py`, `studies/research/memory/config.yaml`, la especificación y su PDF (renombrar `dd_esperado_p95_r` a `dd_esperado_r`), `criterios-implementados-2026-10-12`, cabecera del paso 8 en `criteria.yaml` y fila 8 de `WORKFLOW.md`. Fuente: enc. 44:52,101-109,144,493-502,824.
- G2-m: medir segundos y GB del mono para 300, 3.000 y 20.000 estrategias (5.000 sorteos; ≈ 19 min para 20.000 en 4 cores) y decir si 20.000 caben en una noche; el paquete P (coste de cada nivel en `perf/`) figura «hecho» sin informe G2-m. Fuente: enc. 44:389,775,882.
- `falsePositives` aplica el paso 8 con 14 de 16 reglas (faltan las dos que piden escaneo de ticks); los pasos 10, 12 y 14 no tienen mono y dejan pasar a todos, por lo que «los monos vivos son un techo, no una medición». Falta la corrida a 10.000 con `--ledger` y la tasa por umbral (corrida a escala «es del dueño»). USDJPY espera una cosecha nueva (las del 27 al 29-09 no reconcilian por el cambio de reloj de los feeds). Fuente: enc. 41:211-220; `falsePositives/README.md:86-95`; README encargos:44.
- Reglas R5/R5d y las de presencia, clones, R4a y R5b se «heredan del donante» y no se midieron: se entregan «no medidas» sin proponerles línea; el plantado es un exceso constante, por lo que retraso y calidad de datos miden rechazos por ruido, no potencia; solo hay tres poblaciones de prueba. Fuente: enc. 44:885,895; `falsePositives/README.md:77-84`.
- El repreciado de stops inflaba +290 a +370 USD por operación parada (30-37 % de las operaciones de toda población con stop) hasta el 2026-10-07: quedan invalidados los pases de estrategias reales de D-m (parada 1) y el embudo de USA500 de I en poblaciones con stop, que no se pueden rehacer porque las poblaciones guardadas no llevan `Close type`. La elección de la variante d se midió con monos sin stop y sigue en pie. Sin medir: cortos, PT, stops con stamps M1. Fuente: enc. 44:118-127; K `export/off-grid-stamps-and-stop-exits.md:6-12`.
- Forex en el repreciado: cortos, comisión ≠ 0 y swap en puntos sin verificar contra SQX (`tick_step = tick_size/10` supuesto); el signo del swap corto «se mira en los swaps de hoy en MT5». La z es robusta a ello, la `e` en R no. Fuente: enc. 44:658-668,858-862; `crossmarket/travel/README.md:104-114`.
- Causa del cambio de identidad build → retest sin nombre: B1 arregló el síntoma (`judge.resolve`: 1.557 fallos de presencia → 0), pero el 7-11 % de las estrategias cambia de identidad (la huella coincide 99,7-100 % en 3 poblaciones); el fallo de identidades descartaba 29 de las 169 vivas (17 %). Fuente: enc. 44:41; IND:62-63,131-139; OPEN #93 (745); K `sqx-format/identity-differs-across-databanks.md:6-13`.
- `entryQuality` y `feedQuality` no dejaron datos en la corrida de ejemplo (`feedQuality` murió por falta de inventario, que hoy no falta; `entryQuality` corre después del corte y el juez no ve sus hechos); con los K de hoy casi toda estrategia sale «insuficiente» (< 10 operaciones marcadas). Abiertos: incluir E−1, aplicarlo al build, retest exacto en SQX con ejecución retrasada. Fuente: enc. 44:352-353,365-366,571,744; IND:47-48; ESP:827,890,1249-1250.
- R9a (peor día) y R9c (drawdown sobre neto) salieron del paso 8 y pasan al encargo 45 (sin empezar): «nada en la cadena juzga el peor día ni el drawdown». Hay que guardar la curva diaria de flotante de `oos1` de las que pasen el WFM, `oos_worst_day_r`, `dd_esperado_p95_r` y el neto anual en R. En NIKKEI225 M30 cortar R9 descartaría 841 y 1.712. Fuente: enc. 44:403, 45:45-48; ESP:1209-1222; R9:144-149.
- Pendiente de OPEN #91: los nulos se calcularon con la fórmula con el fallo y operaciones cerradas; hay que recalcularlos sobre `trade_t` y `drift_excess_t` (el encargo 42 §3 lo absorbe). Las tablas `null-fpr-2026-10-04` y `null2` se borraron el 2026-10-06. Fuente: enc. 41:188-197; OPEN #91.
- La curva diaria de SQX (`dailyEquity.bin`) es el mínimo del día; es exacta en el 100 % de 3.983 días, pero los lectores que la diferencian dan Sharpe, correlaciones y `worst_day_r` «low to low». El 2026-10-04: `snoopingScreen` sobredimensionaba el benchmark un 15-26 % y quedó arreglado leyendo la curva a cierre; `minute_path` toma la comisión (USDJPY reconcilia 3.729 de 3.732). Sigue pendiente `search/stageb_data.py:62` (llama a `minute_path` sin comisión), reconstruir las cachés de universo anteriores al 10-04, verificar la rama PercentageBased y un objetivo de perf para `closecurve`. Fuente: OPEN #88 (526-536).
- Seis puntos abiertos de OPEN #93 en el paso 8: (2) la corrección de deriva propuesta no aplicada en `crossmarket/simulate/excess.py` (borrado después); (3) `wfc.py` da a los mercados extra las fechas del principal; (5) crossmarket y crossTF cablean su ventana y `oos2` se lee de exports crudos; (6) el fin de `oos2` de `_policy.yaml` (2026-09-30) está pasado el último bar de XAUUSD, XAGUSD y HK50, así que una tarea OOS2 no puede arrancar; (7) 31 celdas base H1 no tienen `oos2` (`oos2_job.sh` sin correr). Fuente: OPEN #93 (745).
- Persistencia `oos1` → `oos2`: ρ ≈ 0,059 (IC 0,035-0,084); ~65 % de los que pasan aún pierden en `oos2`; una línea en `oos2` por cada 1.000: t ≥ 1,65 con neto > 0 da +60 (IC +26…+96), t ≥ 2,33 da +122 (frágil), mono p ≤ 0,05 ≈ 0; un control con 428 casi duplicados convirtió +60 en −29 y `oos2` no tiene nulo. La puerta sube la probabilidad de positivo en `oos2` del 29 % al 35 %, la mitad por elegir estrategias de pocas operaciones. Conclusión de los informes: pasar el paso 8 hace candidata, no válida; con 3-5 años de `oos1` la t tiene poca potencia y lo que mueve la aguja es más muestra fuera, no más filtros. Fuente: K `research/oos1-oos2-persistence.md:6-13`; EXP:278-288; IND:125-127.
- Reajuste al spread real de Darwinex (OPEN #76) sin contrastar con un retest DATATICK; el spread real se modela desde Dukascopy antes de oct 2017 sin verificar; XAUUSD pasa de 9 a 63 puntos (2017-2026) frente a 5/10 declarados. Fuente: WORKFLOW.md:33; K `costs/darwinex-real-spread.md:6-12`, `costs/funded-tick-spread-vs-price.md:6-14`.
- El crítico independiente no revisó el contraste de los cinco tests juntos, el enriquecimiento frente a la nula por franja de frecuencia ni las 47 celdas enriquecidas; `oos1` y `oos2` quedan gastados para esas estrategias; solo el 52-58 % son estructuras distintas. Fuente: C04:262-318.
- Cuatro modos de cálculo: `calibrate.charged()` solo mete swap y comisión (nunca spread ni slippage) en el coste de cada operación y los modelos que sortean la duración conservan el swap viejo; cerrado solo para la puerta (`engines/nulls/windowed.py`), mientras la escalera y ~35 importadores no cobran nada. Fuente: `engines/nulls/README.md:127-128`; K del mono.
- Mono en mercados adicionales, Stouffer y `oos2` quedan fuera del encargo 44 («sólo comentario»); el retest exacto en SQX con ejecución retrasada y la prueba con el feed real de la firma pasan al encargo 45. Fuente: enc. 44:229,368-369.
- El ledger decide por parámetros con semilla nueva en cada corrida, anotada en el scorecard; el resultado se reproduce releyéndola. Fuente: enc. 44:897-912.
- `cpu_s` del catálogo de `perf/` cuenta ahora el árbol de procesos: las filas ya medidas se corrigen al volver a medir. Fuente: enc. 44:142-146.
- Una databank llena en memoria y vacía en disco exporta 0 estrategias en silencio (el exporter lee disco): regla 1 del proyecto. Fuente: K `databanks/memory-vs-disk-exporter.md:6-14`.
- Orden de trabajo sugerido por el índice de decisiones del paso 8: arreglar R1a, revisar el repreciado del mono, investigar por qué `entryQuality` y `feedQuality` no dejaron datos, implementar la cascada, pasar las poblaciones de prueba, fijar líneas y apagar `dev.on`. Fuente: IND:78-80.

## Paso 10 — ¿La lógica viaja a otros mercados?

Contexto mínimo: el paso 10 (reescrito el 2026-10-07, encargo 46) retestea la estrategia en otros mercados y juzga con nueve pruebas P1-P9 contra un nulo de «desplazamiento de años» (la misma operación movida de año). `z_conj` es la t conjunta del exceso en los mercados adicionales.

### Decisiones tuyas

**P10-1 · ¿El paso 10 es una puerta (solo pasan lógicas que viajan) o una anotación (se aceptan especialistas de su mercado)?**
Es la única prueba antes de `oos2` que puede decir algo nuevo y gana potencia. Una estrategia buena puede ser especialista de su mercado y no pasar. El informe lo deja explícito: «esa es una decisión tuya, no de la estadística».
- **Opciones:** puerta o anotación.
- **Hoy el código hace:** juzga con P1-P9; el estudio emite `verdict.csv` aunque README y `config.yaml` dicen que no emite veredicto.
- **Fuente:** P10:1145-1147; EXP:338; P10:99-104.

**P10-2 · ¿Confirmas las líneas P1-P9 de la propuesta (z_conj Pasa ≥ 2,33, etc.) o esperas a calibrarlas?**
Las líneas son las de tu propuesta del 2026-10-06 («lo dejo a tu criterio»); el agente las dejó «provisionales» con `dev.on` encendido. Falta pasar las poblaciones nula y de ventaja plantada por el paso 10 (§5 «pendiente antes de fijar las líneas»). El encargo 46 lo marca como decisión tomada por el agente que puedes revocar. Cifras: z_conj ≥ 2,33 (Limbo ≥ 0); P4 ≥ 0 (Limbo > −1,65); P5 ≥ 1,65; P6 `p_breadth` ≤ 0,10; P7 `tau_half` ≥ 0,5; P2 y P8 con 0 / 1-2 / ≥ 3 mercados (25 %); P9 `z_beta` > −1,65, o (> −2,33 y `e_end` > 0).
- **Opciones:** confirmar, revocar o fijar tras la calibración.
- **Hoy el código hace:** aplica esas líneas.
- **De esto cuelga:** congelar el paso 10 y la sección 8.1 de la propuesta.
- **Fuente:** enc. 46:214,278-281; `criteria.yaml:127-184`; OPEN #22 (nota 2026-10-07); WORKFLOW.md:35.

**P10-3 · ¿La línea de Falla de la t conjunta (< 1,0) es la correcta y se mide sobre el neto?**
Un miembro del Council pidió que la regla 1 no diera Falla nunca; el código la da en ≤ 0. La t depende de cuántas operaciones tiene cada mercado: «0,5× la t del original» equivale a ≈ 0,3× en calidad por operación (original 58-187 operaciones, mercados 165-526). Medir en USD/op o Sharpe mueve 2 estrategias de Falla a Limbo. La línea < 1,0 pierde el 38 % de las ventajas modestas con transferencia completa y el 62 % con media, y no tiene tasa medida. Las diez t conjuntas son negativas por costes (cobro medio 69 USD/op; resultado −41).
- **Opciones:** dejar la t sobre el neto y mover solo líneas (lo que propone el informe), o medir en USD/op / Sharpe.
- **Fuente:** P10:26-30,626-628,1013-1015,1021-1031,1121-1131.

**P10-4 · ¿Cuándo el original es negativo o casi cero, cómo se lee el cociente?**
Con original negativo el hecho sale vacío (Limbo): en 7 de 10 corridas guardadas la t mediana del original es negativa. Con original ≈ 0 el cociente estalla (F: −10,39 con 0,163): original t = 0,05 y mercado 0,03 dan 0,6 y Pasa. Se propone exigir un mínimo de `main_excess_t` o leer la diferencia; no medido.
- **Opciones:** mínimo de `main_excess_t`, o leer la diferencia.
- **Fuente:** P10:1025-1029,1130-1131.

**P10-5 · Cobre (XCUUSD) M30: ¿ficha de costes errónea y lista de mercados?**
Coste recuperado de 192 USD por operación frente a un resultado típico de ~340 USD, con aviso `fill_mismatch` y PF mediano 0,53; pone 0,6-2,2 unidades de t en contra. Posible error de ficha de costes o de precios. Sin él, 0 de 10 pasarían a Limbo. Hoy solo cae el cobre con `max_fill_error` 0,58.
- **Fuente:** P10:30,1017-1019,1136-1137; enc. 46:238-241.

**P10-6 · ¿Línea distinta por clase de activo? (mercados efectivos y Stouffer)**
Las listas de mercados son 2-5 tests independientes: forex 4,1-4,7; índices 1,6-1,9; metales y crudos 3,0-3,6. «Stouffer ≥ 1,65» deja pasar 5-24 % sin edge; la regla «mitad de mercados al nivel del original» pasa 0 % de las con suerte y sin edge a 1,0× y ≤ 0,4-6 % a 0,5×. El estadístico usable es la t semanal agrupada (sd 0,83-0,95). Agrupar mercados con el mismo lado multiplica el sesgo de lado (falso positivo 9-13 % en cortos de índices). Munger propone ≥ 2,9 y solo anotar para índices; la corrida da 9,2-10,1 y P10 dice que se conciliaron (6,0-8,1). `markets_effective` usa correlaciones al cuadrado y un solo mercado con pocas operaciones lo deja vacío. Sin nuevo umbral fijado.
- **Opciones:** una línea para todos, una por clase de activo, o solo anotar para índices (Munger).
- **Fuente:** K `research/crossmarket-effective-markets.md:6-13`; P10:1052-1054,1068,1139-1140; EXP:338.

**P10-7 · ¿La t sin corregir o la «ciega», que está estropeada en UK100 y DAX40?**
`simulate/excess.py:212` recomienda `excess_blind_t_*` pero `criteria.yaml` lee `excess_t_pooled`. El peso 1/ATR se rompe con barras casi planas entre 24-12-2013 y febrero de 2014 (234 barras UK100, 362 DAX40): el 0,1 % de barras se lleva el 44 % del peso en UK100; `excess_blind_t` de C en UK100 es −5,24 frente a −3,72. Hay que poner suelo al peso o excluir esas barras, remedir y decidir. Hoy 0 de 10 cambian.
- **Fuente:** P10:988-1011,1133-1134.

**P10-8 · ¿Mantienes las decisiones que tomó el agente en el encargo 46?**
El agente decidió por su cuenta, y tú puedes revocar: (a) sin gancho de P1 en el paso 9 (el paso 9 no hace nada, la estrategia se retestea y el estudio la marca Limbo si `fixed_distance` > 0; son 28 de 6.000); (b) `DeadZonePip` del WAE y `#StopLossInPips#` no cuentan como distancia fija en P1 (lo llevan 350 de 6.000 estrategias reales; con la otra opción esas 350 quedarían «no evaluables»); (c) cinco lecturas del núcleo: lotes sin redondear ni topar (`Decimals: 2`, `MaxLots: 500` no se aplican), operaciones cerradas tras el fin de `oos1` fuera, a las desplazadas no se les reaplica el cierre del viernes ni «plano para entrar», entrada sobre barra defectuosa pasa a la siguiente válida, `shift_step: day` cuenta días hábiles (los resultados guardados de crossmarket se leen como caducados desde esa noche); (d) umbrales de crossmarket en `config.yaml › travel:` y `criteria.yaml` (editables desde la ventana) y no en `ledger/thresholds.yaml`, contra lo que pedía el encargo 43; (e) no encargar aparte la sección 8.1 de la propuesta (la población nula para calibrar, prioridad 1; solo se implementó P9; quedan sin implementar el prior de plantilla, factores, régimen y vecindad); (f) `max_displaced_share` 0,20 (lo puso el agente) y `max_fill_error` 0,25 ATR (cifra del diagnóstico viejo) en `travel.validity`.
- **Opciones:** confirmar cada una o revocarla.
- **Hoy el código hace:** aplica las lecturas del agente.
- **Fuente:** enc. 46:10,211-218,238-241,268-299,274-279,309-312.

**P10-9 · ¿Qué hacer con la media de z_conj de las diez de referencia, que sigue en +1,45?**
Tu propuesta pedía ±0,63. La media bajó de +1,72 a +1,56 y a +1,45 tras quitar dos sesgos del aparato (huecos de los feeds de índices: +0,35 z; coste en R con ATR alto: +0,12), que explican solo +0,3 a +0,45. Quedan ≈ +1,45, atribuidos a las estrategias y concentrados en los años del build. Dos lecturas: (a) es lo que predice §1.1 (estrategias ajustadas a la época); (b) hay un sesgo no visto por la batería sintética. Cinco de las diez dan z_conj ≥ 2,33 aunque fallaban el paso 8. Se aplicó el corte igualmente tras tu segunda respuesta.
- **Opciones:** lectura (a) o (b).
- **Fuente:** enc. 46:12-15,300-309.

### Lo resolverá la calibración

| Regla | Valor de hoy | Quién lo puso | Qué falta para fijarlo |
|---|---|---|---|
| P1 `fixed_distance` y control 7.1 `invalid_fraction` | `fixed_distance ≤ 0`; `invalid_fraction ≤ 0,25` (Limbo si no) | tu propuesta / agente | población nula y plantada |
| P2 `freq_off`, `freq_off_fraction` | Pasa 0 (Limbo ≤ 2); fracción ≤ 0,25 | tu propuesta | idem |
| P3 `z_conj` | Pasa ≥ 2,33; Limbo ≥ 0 | tu propuesta | idem; FPR de las dos reglas juntas y potencia con ventaja plantada |
| P4 `z_conj_v2` | Pasa ≥ 0; Limbo > −1,65 | tu propuesta | idem |
| P5 `z_minus_market`, P6 `p_breadth` | ≥ 1,65 (Limbo si no); ≤ 0,10 (Limbo si no) | tu propuesta | idem |
| P7 `tau_half` | Pasa ≥ 0,5; Limbo > 0; sin dato Limbo (hoy siempre) | tu propuesta | idem; falta un productor de `e_principal` en el paso 8 |
| P8 `worse`, `worse_fraction` | Pasa ≤ 1; Limbo ≤ 2; fracción ≤ 0,25 | tu propuesta | idem |
| P9 `z_beta` y `e_end` | Pasa z > −1,65 o (z > −2,33 y e > 0); Falla z ≤ −2,33 y e ≤ 0 | tu propuesta | idem |
| Juzgar sobre el bruto en R (`travel.judge_on: gross`) | bruto | tú («Sí, tu recomendación») | caveat residual: con ATR alto la población neta +0,98 baja a +0,30 bruto, y con los huecos fuera +0,08; queda un resto que no es coste |
| `max_displaced_share` / `max_fill_error` | 0,20 / 0,25 ATR | agente / diagnóstico viejo | idem |

### Trabajo pendiente que no necesita tu respuesta

- `e_principal` (denominador de P7) queda sin dato → Limbo hasta que el mono del paso 8 lo entregue: hasta entonces ninguna estrategia puede dar PASA en el paso 10 y tú lo aceptaste. Las diez de referencia dan 0 Pasa, 5 Limbo y 5 Falla. El encargo 44 ya entregó `level3c.py` pero no consta el enlace. Fuente: enc. 46:17,40-41,97; OPEN #22; `travel/README.md:148-149`; `travel/run.py:132-133`; `steps.md:16`; WORKFLOW.md:35.
- Los veredictos guardados con el estudio antiguo hay que rehacerlos; el README de `crossmarket` lista un `POSSIBLE_IMPROVEMENTS.md` ya borrado. Fuente: WORKFLOW.md:35.
- El repricer solo está auditado para largos, comisión cero y swap en %; cortos, comisión ≠ 0 y swap en puntos (todas las fichas forex) sin conciliar operación a operación contra SQX; la z es robusta, la `e` en R no (afecta a P7, P9 y todo lo dicho en R en forex). Fuente: `travel/README.md:104-114`; enc. 46:130-132.
- Pestaña Cross Market sin capturar nunca con el estudio nuevo: no hay forma de disparar la pestaña con proyecto elegido en `--shot`; faltan la captura, sustituir el aviso «captura pendiente» en los capítulos 30 y 39, borrar los seis `crossmarket-*.png` viejos y `python3 tools/manual.py`. Fuente: enc. 46:16,332-335,400-404,460-467.
- Lista de adaptación de la ventana (nada de `ui/` se ha tocado): quitar o alimentar la sub-pestaña `oos` (`ficha.py:18,168-178`); `judge_on`, `shift_unit` y `shift_step` como texto libre deben ir a `CHOICES` (`knobs.py:56`); tooltips por hoja heredan una frase larga; el mercado base se excluye de `only_options` pero el estudio lo incluye; la pestaña `mercados` omite z vacías, deja motivos crudos y no marca en color `z <= worse_z`; `catalogue.py:64-65` clasifica crossmarket como «gate» aunque nunca descarta; `many.population` no muestra la lectura Pasa/Limbo/Falla por regla; V0/V1/V2 sin vista lado a lado; faltan «?» para columnas de `markets.parquet` y `strategy`; decidir qué columnas (`breadth_count`, `e_end_ratio`, `beta`, `markets`) se ocultan; 19 carpetas `AlgoData/reports/*/*/*/crossmarket` con esquema viejo marcadas caducadas (dejar, ocultar o reejecutar, 21 s por corrida); textos con ejemplos obsoletos (`verdict.py:50`, `table.py:183`, `databank/README.md`). Fuente: enc. 46:332-413.
- Faltan por medir: FPR de las dos reglas juntas, potencia con ventaja plantada, una corrida sobre estrategias que pasen el paso 8, el sesgo por lado para NIKKEI225 largo, el efecto de que los primeros 4 años lleven solo 3 mercados y si las reglas internas están en unidades que viajan. Las cifras 0,4-6 %, 5-24 % venían de `scratch/calib_step10/`, que ya no existe; solo se reprodujo 1,77 y la aritmética del 0,7 %. Fuente: P10:1048-1050,1056-1068,1142-1143.
- Límites técnicos: HK50, UK100, AUS200, USA500 y USATEC tienen meses sin datos en 2011-2015 (76-180 días; el arreglo es `max_displaced_share` 0,20 y exclusión por celda; un agujero sintético limpio no reprodujo el +0,44 original, así que la causa no está del todo explicada); nulo conjunto por año (un año no es un número entero de semanas; no validar NaN sobre z_conj); dos familias de PF (`pf` / `pf_sqx`) discrepan de lado (C en DAX40: 1,17 frente a 0,94). Fuente: K `research/index-feed-holes-and-the-shift-null.md:6-12`, `research/joint-null-year-shift.md:6-13`; P10:99-104,1035-1046.
- Tabla de estado del encargo 46: quedan la captura de la pestaña, `engines/nulls/placement/*` (candidato a otra pasada), la calibración (P10-2) y `e_principal`. Fuente: enc. 46:17.
- Tests rojos de la ventana ajenos al paso 10 (14 fallos y 8 errores) — ver «Tests y código». Fuente: enc. 46:415-449.
- Las reglas actuales de los pasos 10, 12 y 14 las puso un Council sin datos el 2026-10-04 (punto de partida razonado, no calibración); el 46 y el 47 las sustituyeron o las van a sustituir. Fuente: enc. 43:27-29.

## Paso 10.5-12 — Hermanas por timeframe (fabricación 10.5, corte 11.5, fase 2 11.7, juicio 12)

Contexto mínimo: el paso 10.5 fabrica «hermanas» de la madre en otros timeframes escalando sus periodos; 11.5 es el corte previo y 11.7 la fase 2 en SQX; el paso 12 juzga si el edge es un pico aislado en su timeframe. T0-T4 es la regla nueva («¿pico aislado en su TF?»), construida al lado de la antigua `z_new` (la t combinada de las hermanas).

### Decisiones tuyas

**P12-1 · ¿Das el «corta» a la regla nueva T0-T4 y qué lee el paso 12?**
Hoy `11.5: rules: []` (no corta a nadie y todas las madres corren la fase 2) y la regla viva del 12 es `crossTF.combined.z_new ≥ 2,33` (Pasa; por debajo Limbo; nunca Falla; propuesta de agente 2026-10-02, «pendiente del dueño»). La regla T0-T4 vive solo como texto en el «Paquete del corte», sin aplicar (OPEN #108), y espera una corrida real con las tareas de fase 2 y tu «corta». Qué lee la regla antigua: combinada (cargada), máximo o `n_survives`; a 2,33 las tres dan 0 Pasa y a 1,65 dan 1, 2 y 2; la combinada es la única con falso positivo medido (3,6-5,7 % a 1,65, madres H1 y gemelas a coste cero; sin medición para M30); el máximo lo dobla. Aprobar no cambia ningún estado.
- **Opciones:** (a) mantener `z_new`; (b) sustituir por T0-T4; (c) combinada, máximo o `n_survives`.
- **Hoy el código hace:** mantiene `z_new` y emite T0-T4 en paralelo.
- **De esto cuelga:** el corte del 12, la población que entra al 13 y el borrado de lo viejo (parte B).
- **Fuente:** `criteria.yaml:185-200`; enc. 47:14,58-60,223-226; OPEN #108 (888-906); `crossTF/README.md:62-92`; P12:73-75,911,949-951; EXP:382; WORKFLOW.md:38-41.

**P12-2 · K-1: ¿La R de `ret` es la propia de cada timeframe o la de la madre?**
Los lotes siguen la doctrina sobre las velas de cada hermana, así que 1 R son 4 ATR de su timeframe. Una hermana que gana lo mismo en precio por operación que su madre M30 lee `ret` ≈ 0,7 en H1 y ≈ 1,4 en M15 (medido 0,57 y 1,70). Las z no dependen de la escala, pero `ret` y sus umbrales 0,5 / 0,25 sí.
- **Opciones:** (a) R propia de cada TF (implementado); (b) llevar `e` de la hermana a la R de la madre (× `c`).
- **Fuente:** enc. 47:194-199; OPEN #108.

**P12-3 · K-2: ¿Una sola vecina medida que falla T2a o T2b es Limbo o No Pasa?**
La propuesta §6 dice «decide ella, pero el máximo es LIMBO» y §5 define el pico aislado con las dos vecinas. T1 sí falla con una sola.
- **Opciones:** (a) su NO PASA es el de la madre; (b) sin la otra no hay pico, LIMBO (implementado, con `t2a_lone_fail` / `t2b_lone_fail` en `why`).
- **Fuente:** enc. 47:200-203; OPEN #108.

**P12-4 · K-3: ¿Qué ventana usa T4?**
§5 dice «menos de una vela (de la madre)», pero §0.1 cita el 86 % «a menos de una hora» para una madre M30. En `Trade_NIKKEI225_M30_volatilidadL` la H1 más parecida da 0,44.
- **Opciones:** (a) vela de la madre (implementado); (b) la más lenta de las dos.
- **Fuente:** enc. 47:204-208; OPEN #108.

**P12-5 · `CBlock_CandleBreakoutLong*.Double2` («body > Mult × ATR»): ¿`bar` u `other`?**
Hoy está `unverified` en `sqx/variants/ranges.yaml`. Hay que entregarte la tabla de lo clasificado como `bar` y lo dejado en `unverified`, con el motivo de cada uno, para que la revises; esa tabla de entrega no consta.
- **Opciones:** `bar` (se escala con el periodo) o ratio `other`.
- **Fuente:** enc. 47:10,145-146; OPEN #108.

**P12-6 · ¿Debe el paso 12 descartar alguna vez?**
Hoy el paso nunca da NO PASA. Con «combinada < −1,65» se pierde 1 de 10, con «< 0» 4 y con «< 1,65» 7. Un mínimo de 121 operaciones (Feynman) dejaría solo 5 de 16 hermanas «legibles»; exigir `n_tested` = 2 a 1,65 quita el único Pasa (`3.11.426`). Mover la línea de Pasa no cambia qué madres llegan al 13. El encargo 47 propone en cambio una regla con Falla (T0-T4), lo que contradice el «paso 12 nunca falla» de Council (encargo 43, D4). La combinada tipo Stouffer supone hermanas independientes y no lo son; a 2,33 se espera ≈ 1 % de falsos positivos, sin medir.
- **Opciones:** seguir sin Falla, o Falla con T0-T4 / con umbrales de arriba.
- **Fuente:** P12:456,868,895,905,907,919,953-957,966; enc. 43:96.

**P12-7 · D1 para madres H1: ¿dentro o fuera de las hermanas?**
La doctrina lista D1 para una madre H1 (tarea propia, motor MetaTrader 4, una tarea más por corrida), pero toda hermana D1 de una Simple Strategy H1 queda «clamped». Se calibró sin D1 («quítalo»); D1 solo anota T2a en el encargo 47.
- **Opciones:** `crosstfload --targets M30 H4` (sin D1), o incluirlo.
- **Fuente:** `crossTF/README.md:93-96`; P12:897-917; enc. 47:51,97.

**P12-8 · ¿Mínimo de madres para T1 y percentil del build (`tf.frequency.min_population`)?**
El valor de partida es 5. Por debajo queda sin dato → Limbo. Es decisión tuya, pero el valor es de partida.
- **Fuente:** enc. 47:48-50.

### Lo resolverá la calibración

| Regla | Valor de hoy | Quién lo puso | Qué falta para fijarlo |
|---|---|---|---|
| `crossTF.combined.z_new` | Pasa ≥ 2,33; si no Limbo; sin Falla | propuesta de agente + Council | calibración (`scratch/calib_step12` ya no existe); solo hay medida a 1,65 |
| Cifras T0-T4 | `rounding_shift` 0,25; `min_trades` 30; φ en [1,5; 3,5]; `ret` 0,5; `z_Δ` 1,65; pico aislado 0,25; T2b 1,65 / 0; 5.000 corridas | propuesta | datos reales de una corrida de fase 2 |
| `tf.frequency.min_population` | 5 | tú, valor de partida | corrida real |

### Trabajo pendiente que no necesita tu respuesta

- Parte V (validación con datos reales): una corrida real con las tareas de fase 2; que M15 sea aceptado por los indicadores (periodos duplicados); que `k/c` no pase de `maxValue` (PMax 10,99 pasa a 15,6 en M15); que `z_Δ` y `z_build` salgan centradas en 0 con madres sin ventaja; el coste en tiempo de la fase 2; si las tareas de fase 2 escriben `CrossTF_<TF>_build` y si una relanzada sobrescribe o añade; `apply_verdict` sobre `CrossTF_Input` en 11.5; que una repetición de 11.5 puede leer un export obsoleto. Fuente: enc. 47:14,58-60,223-226; OPEN #108.
- Parte B: borrado de lo viejo (`z_new`, Stouffer, `corr_vs_baseline`, seis lecturas, filas `unscaled` y `control`…) tras V; re-apuntar `many.py` / `report.py`; puede que prefieras quitar el prefijo `tf_*` de las columnas. Fuente: enc. 47:15,260-277.
- Parte D (documentación): README del estudio, skill `crosstf`, `steps.md`, WORKFLOW, `CLAUDE.md`, manual y knowhow (en 10.5 no hay stop; clasificación por vela/ventana; M15 dobla periodos). Fuente: enc. 47:13,181-187.
- `scale.fabricate(..., symbol)` saca el activo de la primera madre si no se pasa (`crosstfload.py:107` puede pasarlo). `tf/inputs.build_banks` lee `build_databanks` de `blocks.json` y los exports `CrossTF_<TF>_build` los hace `afterrun`, solo probado en código y tests. Fuente: enc. 47:9-12.
- Las tareas de fase 2 no existen en proyectos creados antes del encargo 47: quien las busca recibe una lista vacía, 11.7 se salta y el 12 juzga con «sin dato». Fuente: enc. 47:157-158,177-178.
- La combinada premia tener menos prueba (`3.11.426`, una hermana, 1,72, queda por delante de P, dos hermanas, 1,30); el signo «heredada o falla» se lee sobre un Sharpe revalorado sin 807 puntos por operación de coste (dos hermanas con signo cambiado; hoy cambia 0 de 20 lecturas). Fuente: P12:889-893,959.
- `z_new` falla el doble con ρ > 0,9 (10 % de falsos positivos en 39 casos; el código corta en 0,95, afecta a 1 de 16); ρ sale de 48 meses (error ≈ 0,15 cerca de 0); una hermana recortada entra igual en la combinada (23 % H1→H4, 53 % M30→H4); el stop no se escala (≈ 1,4× más ancho en H1, ≈ 2,8× en H4); la z depende de la semilla (2 % con 2.500 monos); comentarios y README desfasados (5 % vs 2,7-6,3 %); promoción y prueba conjunta 10+12 no programadas. Fuente: P12:897-917,961-965; EXP:373.
- Coeficientes por barra escalados `k/c` (NIKKEI225 desde M30: M15 0,704; H1 1,419; H4 2,833); los parámetros `unverified` marcan la hermana para T0; la tabla de distancias fijas no cubre WAE `DeadZonePip`, `#StopLossInPips#` ni `SLPT.ValueFromFormula`. Fuente: K `sqx-drive/crosstf-scaling-coefficients.md:6-12`, `sqx-format/fixed-distance-keys.md:6-12`.

## Paso 13-14 — MC Retest

Contexto mínimo: el MC Retest (MCR) re-ejecuta la estrategia con perturbaciones (spread, slippage, OHLC, barra de inicio…). El rediseño del 2026-10-07 lo recortó a MCR 1, 4 y 7; las tareas MCR 2, 3, 5, 6 y 8 quedan fuera de la etapa.

### Decisiones tuyas

**P14-1 · ¿Qué rangos tiene `min_distance` del MC Retest?**
`core.assets XAUUSD` avisa de que los rangos de `min_distance` están sin decidir; la auditoría del 2026-10-07 lo califica de «decisión del dueño, no un hallazgo».
- **De esto cuelga:** la tarea MinDistance del MCR (solo para poblaciones con stops/límites).
- **Fuente:** `AlgoData/audit/2026-10-07.md:18`.

**P14-2 · ¿«PF p5 del estrés ≥ 1,0» como única muerte? ¿Con banda de Limbo?**
El 1,0 es convención. Hoy pasan 4 y fallan 6 de 10. Alternativas: 0,95 mata 5; 0,90 mata 4; 0,80 mata 2; 1,10 mata 9; proporción de rentables ≥ 70 % (Kaufman) mata 3, ≥ 50 % mata 2. `3.9.284` tiene el intervalo de PF p5 (0,975-1,011) cruzando 1,0; una banda de Limbo es «el cambio más barato». Hay tres umbrales para lo mismo (criterio 1,0, veto del estudio 1,10, Council «< 1»): con 1,0 pasan cuatro, con 1,10 una; la ventana muestra FAIL en estrategias que el piloto deja seguir.
- **Opciones:** 1,0 sin Limbo (hoy); banda de Limbo; las demás líneas de arriba.
- **Fuente:** P14:933-994,1000,1057-1059,1114-1124.

**P14-3 · ¿Añades la segunda muerte del Council (retención < 0,5) y qué dureza tiene el estrés?**
Está en el acta y no en `criteria.yaml`; falta el hecho `tasks.spread.p5/real`. Hoy coste y ganancia son 0 (mataría a F, `19.2.363` y `16.5.352`, que ya mueren). El estrés suma ventana larga, coste de `oos1` (1,56× el del build) y sorteo 0,5-2×: spread medio ≈ 1,95×. Ninguna de las 10 conserva la mitad del beneficio en el p5 (la mejor, `4.13.338`, 0,43). Suavizar exige volver a correr el 13 y no está medido.
- **Fuente:** P14:939,951-953,990,1004-1006,1016-1018,1065,1120-1127.

**P14-4 · ¿Qué multiplicador de drawdown usas para dimensionar (2×, 3×…)?**
Barajando la mediana es 1,9-1,95 (el 2× de Hill/Pruitt); bajo estrés 2,64 en p95 y 3,2 en CVaR (el 3× de Kaufman), rango 2,1-4,9. Con E al 1 % por R el p95 del estrés es 15,7 % de la cuenta; para un 10 % hay que bajar a 0,64 % por R. Medido en 10 sorteadas. No hay regla de drawdown.
- **Fuente:** P14:942,951,1069,1132-1133.

**P14-5 · ¿Debe la guarda de ingesta del MCR depender del tamaño de la población?**
En el run de referencia, 5 de 70 reconstrucciones de RecoveryFactor superaron la tolerancia del 0,2 % (por 1,01× a 1,22×). La regla llama «sistemática» a un fallo desde max(2, 5 %), pensada para poblaciones grandes; con 10 estrategias salta. Se corrió a mano con `--set recon.systematic_share=0.2`. Además el autopiloto no reintenta el aborto transitorio de SQX (NullPointerException en fastutil); el paso 24 se repitió a mano.
- **Fuente:** TB:126,144; AS:144; K `sqx-drive/mcr-nullpointer-fastutil-transient.md`, `transient-abort-automatic-retry.md`.

**P14-6 · ¿Qué haces con T3, que no discrimina?**
T3 (`ret_med ≥ 0,8`, nunca falla) se midió con mediana 1,000 en 24 de 26 estrategias (67-100 % de las repeticiones idénticas al original; solo varía `ret_p5`, 0,91-1,00): es una regla sin efecto. MCR 1 (barra de inicio) no discrimina.
- **Opciones:** retirar T3, redefinirla o calibrarla.
- **Fuente:** `criteria.yaml:201-224`; WORKFLOW.md:42; `mcRetest/README.md:90-95`; `autopilot/README.md:215-219`; K `research/mcretest-original-among-reruns.md:6-12`, `sqx-format/mcr-start-bar-reruns-identical.md:6-9`.

**P14-7 · ¿Borras o calibras los cortes de `gates.py` del veredicto antiguo (`survival_dd_pct`, `exec_keep_frac`, `min_pf`, `collapse_frac`, `psr_gate`)?**
Están «chosen to be plausible, not calibrated»; en la primera batería las cinco estrategias fallaron; el tooltip dice «Sin calibrar contra tu operativa». Hoy no deciden el paso 14, pero la pestaña de veredicto antiguo de la ventana los muestra.
- **Opciones:** borrarlos o calibrarlos con las reglas de la cuenta.
- **Fuente:** `mcRetest/POSSIBLE_IMPROVEMENTS.md:54-60`; `mcRetest/tooltips.py:52`.

**P14-8 · ¿Mantienes que el paso 14 solo mata, aunque los datos digan que además discrimina?**
El Council lo dejó así porque sobrevivir no es evidencia.
- **Fuente:** enc. 43:27-28,94-95.

**P14-9 · ¿Es correcta la precisión 1 (timeframe elegido) en MCR 2, 3, 4, 6, 7, 8 y WFC de `_build.yaml`?**
El cambio de precisión de 2 a 1 está sin commit y el comentario de MCR 2 sigue diciendo «`precision: 1  # un minuto — lento y fino`» (en SQX 1 = timeframe elegido, 2 = 1 minuto). No consta quién lo decidió; dijiste el 2026-10-02 «nada de retest a M1». La próxima corrida no sería comparable con las anteriores.
- **Opciones:** confirmar y corregir el comentario.
- **Fuente:** `assets/_build.yaml:87,153,162,242,249`; P14:1004-1069.

### Lo resolverá la calibración

| Regla | Valor de hoy | Quién lo puso | Qué falta para fijarlo |
|---|---|---|---|
| T1 build | `ret_med ≥ 0,6` (Limbo ≥ 0,3) y `f_pos ≥ 0,9` (Limbo ≥ 0,7) | propuesta, «sin calibrar» (tú, 10-07) | población nula y plantada |
| T1 `oos1` | `ret_med > 0` | idem | idem |
| T2 build | `ret_med_aprox ≥ 0,6` (Limbo ≥ 0,25) | idem; T2 es medida aproximada | idem |
| T3 build | `ret_med ≥ 0,8`, si no Limbo (nunca falla) | idem | no discrimina (P14-6) |
| Cortes de `gates.py` | marcadores de posición | agente | P14-7 |

### Trabajo pendiente que no necesita tu respuesta

- El lote de vecinas por la fábrica de variantes, sus tiempos y el configurador sobre un proyecto sin las cinco tareas no están probados en vivo. Fuente: WORKFLOW.md:42.
- No existe MC Retest de estrategias de edge cero (trabajo del custodio): por eso la regla de corte no se aplica y se muestran diagnósticos fuera de `offered.yaml`; spread/slippage/stress ponen al original sobre la mediana por construcción; remuestrear no crea cola peor que la muestra (Taleb). Fuente: K `research/mcretest-original-among-reruns.md:6-12`; EXP:437-447,662,683.
- MCR 7 cambia el número de operaciones (mediana 0-3 %): T2 asume el drift del original (`ret_med_aprox` 0,73-1,10 en 26); los proyectos ingeridos antes del 2026-10-07 deben re-ingestarse; una ingesta anterior da T2 y T3 «sin dato» (Limbo). Fuente: K `sqx-format/mcr-ohlc-changes-trade-count.md:6-11`; `autopilot/README.md:206-210,229-230`.
- La ventana y «Correr workflow» no ejecutan T1 (solo el autopiloto corre las vecinas): lanzar el 14 desde la ventana da Limbo a todas. Fuente: `pipeline/autopilot/README.md:206-210`.
- Sin decisión ni medición: el hecho `p_beneficio_0` cambiaría de nombre y una regla sobre el viejo dejaría todo en Limbo; hechos guardados anteriores al estudio reescrito; `segment: oos1` engañoso (sale de build..oos1); cómo sortea SQX dentro del rango, unidad de `MaxChange`, si 500 re-ejecuciones bastan (el p5 baila entre la 17.ª y 36.ª peor); hechos duplicados (28+11+3+8); el README dice que corre «tras ser aceptada», no es así. Fuente: P14:1004-1069,1135,1139.
- Los tres umbrales del Monte Carlo (lo de OPEN #19) son provisionales; y el 14 está sin medir con población nula (1.100 «monos seleccionados» para medir una tasa del 1 % con ±0,3 %). Fuente: enc. 41:199-209; EXP:644-648,683-688.
- MC Retest y SPP no se midieron a 500 (su coste es de SQX: ~34 h y ~2,8 h). Fuente: OPEN #42.

## Paso 15-16 — SPP

Contexto mínimo: el SPP permuta los parámetros de la estrategia en una rejilla y dibuja el mapa de rentabilidad; hoy es «un mapa, no un filtro».

### Decisiones tuyas

**P16-1 · ¿El paso 16 corta o no corta?**
`criteria.yaml` tiene `"16": rules: []` con corte en «SPP OOS»: pasan 10 de 10. El Council propuso Falla solo si la solución es un pico aislado o si la media de la rejilla menos 1 desviación es < 0, pero ninguno de los dos se expone como hecho. Opciones medidas sobre las 10 madres: `spp.panel1.net_profit.p10 ≥ 0` falla 3 (F, `16.5.352`, `19.2.363`); `area_de_meseta ≥ 0,70` falla 2; `net_profit.p5 ≥ 0` falla 4. Dijiste que fijarás los criterios tú.
- **Opciones:** (a) que `criteria.yaml` diga por escrito que no corta; (b) alguna de las reglas de arriba, con lo que costaría y ganaría.
- **Hoy el código hace:** ninguna regla.
- **De esto cuelga:** la selección de entrada al 16.5.
- **Fuente:** `criteria.yaml:225-229`; enc. 41:199-209; enc. 43:28-29,91-92; `criterios-implementados-2026-10-12.md:5,9,19-22`; P16:682-688,739-756,789-802,908-912.

**P16-2 · ¿Se juzga el `build` o `oos1` en el paso 16 y qué hechos se exponen?**
Hoy todos los hechos son del build (el `segment: oos1` de `criteria.yaml` engaña). Sobre `oos1`, «media−desv < 0» fallaría 5 de 10 y no las mismas. Faltan por exponer: media, desviación, media−desv, rango del real y distancia en IQR, y percentiles de `oos1`; los 37 hechos `spp.verdict_csv.*` no están en el `hechos.parquet` del 2026-10-04 (114 vs 151 claves).
- **Opciones:** build, `oos1`.
- **Fuente:** P16:694-701,758-775,814-816,838-840,914,916.

**P16-3 · ¿Qué haces con `spp.verdict.pass` (sin suelo de operaciones), `area_de_meseta` y la marca de pico?**
El veredicto no tiene suelo de operaciones: siete de diez máximos tienen < 30 operaciones; aprueba picos y suspende mesetas, por eso aprueba a las 10. Una permutación de 6 operaciones con Ret/DD 554 hincha la sd de `13.3.390` a 44,9. `area_de_meseta` es la fracción de combinaciones con Ret/DD > 0 (`plateau.py:24`), mientras el glosario (`one.py:35`) lo describe como «cerca del mejor nivel» (realmente `above_half_max`, 0,0001-0,044). La marca de pico no tiene definición; la candidata (real > p95 y > 1,5 IQR de la mediana) está puesta justo por encima de lo observado y marca 0 de 10.
- **Opciones:** (a) no leerlo; (b) suelo de 30 operaciones (C pasa a RUIDO); (c) calcularlo sobre Sharpe/beneficio; y renombrar `area_de_meseta`.
- **Fuente:** P16:737,756,810-812,818-824,865,918-922.

### Lo resolverá la calibración

| Regla | Valor de hoy | Quién lo puso | Qué falta para fijarlo |
|---|---|---|---|
| Paso 16 (SPP) | sin regla; `cut: SPP OOS` | Council propuso FAIL-only; tú fijarás | P16-1; pasar una población sin ventaja por 15-16 (26 min por 10) |

### Trabajo pendiente que no necesita tu respuesta

- Vacuidad no probada: pasar una población sin ventaja por 15-16; `n_eff` solo quita duplicados exactos; el tope de 15.000 filas no se alcanza (10.239-14.406), causa no medida; SQX cuenta como rentable la permutación que no opera; el panel 2 mezcla IS y OOS1 en un percentil; el «6 combinaciones comunes de 11.600» del README es de otra estrategia (aquí 0); dos corridas no se emparejan punto a punto. Las métricas de decay no distinguen cero de edge real con OOS1 de 4 años (Sharpe 0 ± 0,5) y ninguna regla las lee. Fuente: P16:826-864,924; EXP:461,485,628,664; K `research/spp-decay-metrics-zero-edge-null.md:6-12`.
- Proyecto viejo: `SPP IS` lee `MCR 8 Stress`, que nada rellena desde que el 13 solo corre MCR 1, 4 y 7; remedio `python3 -m sqx.projects.spp <SÍMBOLO> --cfx <cfx> --input "MCR 7 OHLC"` con el worker parado, nunca ejecutado. Fuente: K `sqx-drive/old-chain-spp-reads-mcr8.md:6-10`; WORKFLOW.md:44.
- El veredicto propio del SPP mide la cola derecha de Ret/DD y el «mejor punto» suele ser una permutación con menos de 30 operaciones; `spp.verdict.area_de_meseta` es el porcentaje de vecinos rentables (no lo que dice el glosario). Fuente: `criterios-implementados-2026-10-12.md:19-22`; `spp/README.md:41-42`.

## Paso 16.5 — Variantes y nube de parámetros

Contexto mínimo: el paso 16.5 fabrica un lote de variantes de parámetros de cada madre, las retestea en SQX y mide la «nube» (cómo cambia el exceso al mover los parámetros). Hoy no decide nada y ningún lote real tiene `variant_trades.parquet`.

### Decisiones tuyas

**P165-1 · ¿Cuenta el 16.5 para el veredicto?**
Hoy no decide nada (`criteria.yaml` sin entrada; 0 de 164 `hechos.parquet` con claves de nube; A1 y A3 sin dato en las 10 madres). De esta pregunta cuelgan las otras 11 del informe; el informe recomienda tomar al menos las preguntas 1, 2 y 9.
- **Opciones:** (a) solo consulta (aplicado); (b) escribe hechos y entra al 20 (hoy 10 a Limbo por «Sin dato»). Regla propuesta: `cut: null`, `rules: []`.
- **Hoy el código hace:** (a).
- **Recomendación del agente:** el informe `criterios-implementados-2026-10-12` recomienda tomar al menos las preguntas 1, 2 y 9.
- **Fuente:** `criteria.yaml:230-233`; P165:932-944,1158-1160,1174-1194; P165p:165-184.

**P165-2 · ¿Alrededor de qué punto y con qué radio se mide la vecindad?**
La nube usa una caja de 2 pasos alrededor de la madre; el diseño fabrica un rombo alrededor del centro de la meseta (`strata.py:42-72`). A1, A3 y C1 quedan vacías en las 10 madres (en `13.3.390` el estrato se perdió entero). «Un paso» no significa lo mismo por parámetro (`levels.py:16-45`): ±2 barras en un periodo de 88 valores frente a ±16 % en un multiplicador de diez niveles. Radio: con 2 hay 0 de 10 con vecinas; con 5, 6 de 10; con 10, 8 de 10 para A1 y solo 4 para A3.
- **Opciones:** (a) la madre: 0 de 10 con dato; (b) centro de la meseta: A1 en 9 de 10, A3 en 5; (c) estrato denso alrededor de la madre (repetir el 16.5, 500 retests por madre).
- **Fuente:** P165:966,1013-1027,1181-1183.

**P165-3 · ¿Qué haces con la lectura por años B2 y con `oos2` dentro de la nube?**
B2 se retiró el 2026-10-02 (motivo no recogido) pero su cálculo y sus columnas siguen; los textos hablan de 4 bloques y el código pinta 3. Opciones: borrar, repintar con «Sin dato» o bajar el suelo de días a 20. `WORKFLOW.md:66-70` dice que la nube corta en `oos2`; el manual dice que mira todo, `oos2` incluido (tú, 2026-09-28); el código solo corta con `ALGO_AUTONOMOUS=1`. C1 y B2 leyeron 2023-11-28 → 2026-09-29 sin cortar y no quedó anotado como mirada (es regla dura). Para la nube, el enc. 48 también pregunta si la lectura de `oos1` usa solo el suelo de dentro (0 para quien no opera allí) o además el suelo de fuera de 10 al año (regla 11).
- **Opciones:** borrar B2 / repintar con «Sin dato» / suelo de días a 20; suelo de dentro o también de fuera.
- **Fuente:** P165:1029-1036,1046-1060,1071-1091,1130-1131,1187-1190; P17p:210-217; WORKFLOW.md:66-70; enc. 48:13.

**P165-4 · ¿Se incluyen en la nube los parámetros congelados (Sobol) y se tratan los `Shf1` como móviles?**
Los parámetros congelados varían en el estrato de cobertura; en F ocupan los dos primeros puestos de Sobol. Sin ellos, Σ primer orden va de 0,13 a 0,92. La regla «un shift nunca se mueve» solo reconoce `…Shift1`; los `Shf1` se varían y pesan (0,051 / 0,069 / 0,100). Afecta a 4 madres y a 16-19 y obligaría a repetir.
- **Opciones:** incluirlos o solo los vivos; reconocer también `Shf1`.
- **Fuente:** P165:1046-1060,1130-1131.

**P165-5 · ¿Cómo se diseña el lote (hipercubo latino o Sobol, top 20 % o 10 %, métrica del mapa) y cuántas variantes por mercado aleatorio?**
Las propuestas lo dejaron abierto y se implementa como parámetro con el valor propuesto: `variants.design` `lhs` (hipercubo latino), `wfc.top_share` 0,20 y métrica = exceso por año. La secuencia de Sobol «queda como decisión abierta» y `variants.design` ya no es una opción en la ventana. Se propone 8 variantes por coeficiente. Cuántas variantes por mercado aleatorio se decide en el 18.5. La nube lee `build`; la posición de la madre cambia mucho a `oos1` en 3 de 6 (`13.3.390` q 0,361 → 0,931); no hay banda de ruido (58-187 operaciones en `oos1`). El ranking de Sobol solo se imprime con R² ajustado > p95 del barajado (≈ 0,06 con 458 variantes y 105 coeficientes; el 0,23 de la propuesta era R² bruto).
- **Opciones:** hipercubo o Sobol; 20 % o 10 %; exceso por año o Sharpe del exceso.
- **Hoy el código hace:** `lhs`, 0,20, exceso por año.
- **Fuente:** enc. 48:96,243-246,15; P165:1104-1128,1191; P165p:165-184; K `research/cloud-sobol-ranking-from-noise.md:6-12`.

**P165-6 · ¿Qué suelo de operaciones usan 16.5, 17, 18 y 18.5, y lo lleva el CSCV?**
Los comentarios dicen una cosa y los valores otra: `config.yaml:6,12` dice 50 en total y «30 es el suelo de SQX»; corren 100 en total (`_build.yaml:368`) y 50 por lado (`config.yaml:19`); `_build.yaml:353` también dice 50. Con 30 por lado, G pasa de ρ 0,009 «No fiable» a 0,283 «Indeciso»; en CSCV `13.3.390` es fail con suelo y pass sin él (0,642 → 0,423). Falta decidir el suelo y si el CSCV lo lleva. Otras cifras de la tabla del encargo 48: `floor_is_per_param` 15, `floor_oos_per_year` 10, `min_variants` 30.
- **Fuente:** P17:775-781,838-842,941; P18:913-915,1074; P185:1217-1221; P165:1097; enc. 48:88-109.

**P165-7 · Madres de la corrida de referencia cuya nube ya leyó `oos2` sin anotarlo: ¿se rejuzgan con el criterio nuevo o se dan por quemadas?**
- **Fuente:** enc. 48:241-242.

**P165-8 · ¿Quitas `n_target` y `strata` del SPP (el lote ya no los lee) y resuelves la capa `engines → studies`?**
`calibrate/tooltips.py` no existe, así que la ventana usa frases de reserva. `checks.py` falla en capas por `engines → studies` (`drift_term` vive en `studies/`): o se mueve a `engines/` o entra en `ALLOW`.
- **Fuente:** enc. 48:9,15.

### Lo resolverá la calibración

| Regla | Valor de hoy | Quién lo puso | Qué falta para fijarlo |
|---|---|---|---|
| `rank_high` 0,95, `plateau_low` 0,15, `rho_low` 0,20 | idem | agente (`set_by: agente`, 2026-09-24) | un lote real |
| Umbrales de la nube 0,35 / 0,35 / 1,0 / 0,20 / 0,50, δ = 0,20, K = 8, 60 días activos, 10 % superior | idem | sin firma | un lote real; el suelo de 60 días no está calibrado para 20-40 op/año |
| «Rugosa» (`or` vs `and`) | `or` (5 de 10 con `or`, 2 con `and`) | código | decisión + lote real; F está en el filo (0,351/0,358 contra 0,35) |
| «Meseta» (q ≥ 0,95, π) | 0 mesetas y 9 «Sin destacar» con q ≥ 0,95; con «estar acompañada» y π > 0,15 serían 9 de 10 | propuesta | idem; π cuenta lo que supera el suelo (mejores incluidas) mientras el glosario dice «a menos de δ» |
| Tamaño del lote | `variants.n_min` 1000, `n_max` 5000, 8 por coeficiente | tú (10-07) | lote real; la fábrica nunca corrió en real |
| Parámetros del §2 del encargo 48 | `null_draws` 2000, `null_block_days` 1, `alpha` 0,05, `rho_strong` 0,30, `shuffles` 200, `shuffle_percentile` 95, `heatmap_pairs` 4 | agente con `set_by: owner`, `set_on: 2026-10-07` | calibración propia (solo hay la del WFC) |

### Trabajo pendiente que no necesita tu respuesta

- Parte V: lanzar un lote nuevo en SQX y el ensayo de calibración de C sobre él (`python3 -m studies.optimisation.wfc.calibrate` sobre un lote real; 20 min con 4 procesos junto a SQX); espera tu «adelante», quema CPU en el custodio; sin eso no hay objetivo en `perf/` para la nube. Fuente: enc. 48:13,14,17.
- Tarjetas de knowhow pendientes: una superficie ajustada a ruido puro reparte igualmente un ranking de Sobol (Σ primer orden ≈ 0,8, Σ total ≈ 1,2); la referencia barajada del R² ajustado ronda 0,06 (no el 0,23); `marketSurfaces/measure/region.py:6-7` y dos tarjetas (`plateau-radius-degenerates-at-six-params`, `cloud-ranking-stability`) nombran módulos retirados; la parte D dice haber escrito «siete tarjetas» pero no consta que estas dos correcciones se hicieran. Fuente: enc. 48:13,16.
- «Día activo» sin definir; ρ entre años legibles consecutivos; el manual cap. 39 enseña B2 y rutas viejas; `WORKFLOW.md:45` dice `Retester` de serie pero usa bancos `WFC_*`; con < 2 vecinas el dibujo pinta toda la nube sin aviso; 400-500 puntos en 5-15 dimensiones son pocos y la superficie es dentro de muestra. Fuente: P165:1093-1103,1129,1198-1210; WORKFLOW.md:45.
- Una carga de 5.000 variantes pierde ~21 % del tramo IS en la ruta de reinicio 🤔 (2.500 es seguro; en sesión viva 5.000 sí); causa desconocida. El export de operaciones de variantes cuesta ~90 min por lote (por eso se revirtió E3 en el encargo 48). Fuente: K `databanks/variants-one-big-load-loses-is-results.md:6-13`, `perf/step-16-5-time-split.md:6-9`, `perf/variant-trades-export-cost.md:6-11`.
- Sin lote real con `variant_trades.parquet`: lectura real de `studies/optimisation/wfc/inputs/batch.py`, exportación en `pipeline/autopilot/variants.py`, ensayo build→oos1 de `wfc.calibrate` (probado solo sintético) y las dos zonas de la ventana (WFC y nube). `batch.py` lee `metrics.parquet` sin `oos2` y no apunta miradas en el ledger porque un lote no guarda su familia. Fuente: OPEN #50 (nota 2026-10-07, 336); enc. 48:12-14; WORKFLOW.md:45-47.
- Hechos retirados que otros ficheros aún nombran (`estudios/wfc_<comp>.*`, `collected.json`, `exceso_persistencia_*`, `mediana_ratio_Sharpe`) en `pipeline/autopilot/offered.yaml`, `ui/text/columnhelp_criteria.py`, `ledger/blind.py:61-67` y `pipeline/recipe.yaml`; `mcRetest/neighbours/excess.py` no se tocó. Con un `drift_span` que deja fuera el año de una operación las derivas `b` y `d` no existen (`per_trade` se niega; W usa `a` o `c`). Fuente: enc. 48:9,12.
- Los hechos de 16.5, 17, 18, 18.5 y 19 no llegan al juez: `facts.gather` solo recoge carpetas (`facts.py:221-222`) y estos estudios escriben `estudios/*.json`; `tail.py:107-124` planifica 17, 18 y 18.5 «a ciegas» y no juzga el 19; `facts.py --step` admite solo 8, 10, 12, 14 y 16. Con «hecho que falta = Limbo» una regla nueva dejaría las diez madres en Limbo. Fuente: P17:813-821,937; P18:967-974; P185:1144-1159,1356-1357; P19:862,870-875; P165:936-944,997-1005.
- `pipeline.run.mothers` toma todas las madres del export SPP y el brief solo lee IS. Fuente: OPEN #90 (684-695).

## Paso 17 — WFC (correlación walk-forward)

Contexto mínimo: el WFC mide si elegir por el pasado sirve fuera: la ρ de Spearman entre el exceso de dentro y el de fuera, contra un nulo de volteo de signos semanal, y la mediana de fuera del top de variantes. Da PASA / LIMBO / NO PASA de la composición que decide (c1: build+oos1 dentro, `oos2` fuera; c2 y c3 se anotan). `abre: true` significa que el sello de `oos2` está abierto porque hay una calibración registrada.

### Decisiones tuyas

**P17-1 · ¿Qué composición es «el» WFC?**
El oficial es `build+oos1 → oos2` (`config.yaml:46`), que gasta `oos2` (3 de 4 particiones lo tocan y solo se anota la pedida). Con «No fiable = fallo» la pedida falla 6 de 10 y `build → oos1` 5, con solo 2 en común. `build → oos1` está contaminada porque la madre se eligió viendo `oos1`. Dos claves colapsan en `build_oos1_oos2`. La propuesta hace las tres composiciones con claves distintas y sellado de `oos2` en el estudio.
- **Opciones:** como hoy (c1 decide, c2 y c3 se anotan), o las tres composiciones con claves distintas.
- **Fuente:** P17:807-811,826,873,927; P17p:18-42,213-216; WORKFLOW.md:47.

**P17-2 · ¿Aceptas el nivel con nulo de signo (a costa de Limbo) y qué `rho_floor` usas: 0,30, 0,15 o 0?**
«Mediana > 0» pasa la mitad de las familias sin edge (0,44-0,49); con nulo de signo (`wfc.level_alpha` = 0,05) el falso PASA baja a 0,02-0,03 a costa de hasta 0,60 de familias con Sharpe 0,5 en LIMBO. Lo decidiste el 2026-10-08; una noche el código siguió la propuesta sin nulo (falso PASA 0,44) y se revirtió. Se retiraron persistencia del top y Sharpe OOS/IS. El corte `rho_floor` 0,30 no está en `ledger/thresholds.yaml`; se propuso 0,15 y se retiró (fuente de Katz no localizada). Con 0,15: 3/3/4 (pedida) y 5/1/4; con 0: 4/4/2 y 6/2/2; aplicado 0,30 (3/1/6 y 2/3/5). La persistencia poblacional `oos1 → oos2` es 0,06.
- **Opciones:** 0,30 (hoy), 0,15 o 0.
- **Fuente:** K `research/wfc-top-persistence-sign-flip-null.md:6-13`; P17:702,763-773,844-846,929-931; EXP:508-518; enc. 48:12-14,45-50.

**P17-3 · ¿Repites y registras la calibración que abre `oos2`, o aceptas la vigente?**
`ledger.gate.seal` ata la calibración solo al hash de la entrada «17» de `criteria.yaml`. Ese hash coincide (815e49…), así que el sello está abierto con `abre: true`, pero el registro (2026-10-07) midió el nulo del nivel con sorteo diario y orden en neto; el código sortea hoy por semanas y lee el orden en bruto. WORKFLOW avisa de que la calibración «midió el nulo del nivel, no el criterio tal como se escribió». Una medición del 10-08 (semilla 48, sin registrar) da falso PASA 0,03, falso NO PASA 0,13 y hasta 0,60 de LIMBO con Sharpe 0,5; registrarla sobrescribe el registro (el README: «Nobody but the owner runs it»). Falso PASA sin nulo en el nivel: 0,49-0,44, por encima del tope. Los topes (`max_false_pass` 0,40 y `max_false_fail` 0,25) los puso el Council (el yaml pone `set_by: dueño`, el texto dice «del Council, provisional hasta que el dueño lo confirme»). Con el nulo del nivel la recalibración dio falso PASA 0,02 y falso NO PASA con Sharpe 0,5 a 2,75 años 0,22. Las casillas de referencia (2,75 años, Sharpe 0,5, `own_noise` 0,4, la peor de con/sin orden) las fijó el agente en `calibrate/config.yaml#reference`. Si en (b) dejan de pasar las que ya no pasan, queda por decidir si van a LIMBO o a NO PASA. El criterio anterior daba PASA al 49 % de las familias sin ventaja y con el nulo baja al 4,7 %.
- **Opciones:** repetir y registrar la calibración, o aceptar la vigente; confirmar o cambiar los topes 0,40 / 0,25; las que dejan de pasar a LIMBO o NO PASA.
- **Hoy el código hace:** `abre: true`.
- **De esto cuelga:** la apertura de `oos2` para el 17 y el paso 20.
- **Fuente:** `wfc/calibrate/README.md:35-43`; `wfc/POSSIBLE_IMPROVEMENTS.md:#1,#1d,#3,#4`; `ledger/gate.py:85-120`; `AlgoData/ledger/wfc_calibration.json`; `thresholds.yaml:1273,1280,1347-1360,1364`; enc. 48:14,45-50,109,240; OPEN #50.

**P17-4 · Persistencia del top: ¿ponemos umbral?**
Hay dos hechos ofrecidos sin umbral. Ninguna de las 4 madres que pasan en `oos1` repite en `oos2`; F y `13.3.390` son familias que pierden. Coste de poner umbral: `_oos1` ≥ 0 cuesta 4; `_oos1` sobre nulo 6; `_minimo` ≥ 0 7; `_minimo` sobre nulo 10. Los 0,27 y 20/50 no tienen fuente escrita. La propuesta la sustituye por R_sel.
- **Fuente:** P17:736-745,811,871,935; P17p:170-190.

**P17-5 · Lecturas del WFC sin preguntarte: ρ parcial, orden bruto/neto, borde plano y `r_sel_min_gap`.**
(1b) la nube y los cuadrantes se dibujan en neto y la línea en ρ bruto; (1c) con «borde plano» a distinta frecuencia, el orden «positivo» sale 3 % (mismo nivel bruto/año) o 75 % (mismo borde por operación), y hoy cuenta; (2) la ρ parcial controlando por nº de operaciones (`order.partial`) existe y no se anota: hay que decidir qué recuento de operaciones controla; (5) celda de referencia de la calibración puesta por el agente. El número del «denominador casi nulo» de R_sel es provisional (`level.r_sel_min_gap: 0.05`, el Council pidió la guarda sin dar número).
- **Opciones:** en cada punto las alternativas están descritas en `POSSIBLE_IMPROVEMENTS.md`.
- **De esto cuelga:** el número de LIMBO y la lectura de «orden».
- **Fuente:** `wfc/POSSIBLE_IMPROVEMENTS.md:#1b,#1c,#2,#5`; enc. 48:12; `thresholds.yaml:1364`.

### Lo resolverá la calibración

| Regla | Valor de hoy | Quién lo puso | Qué falta para fijarlo |
|---|---|---|---|
| `wfc.c1.estado` | Pasa = 1; Limbo ≥ 0; interno: mediana del top > 0 y `p_nivel` ≤ 0,05 | tú (10-08, confirmado) | calibración que mida el criterio tal como se escribió (P17-3) |
| `max_false_pass` / `max_false_fail` | 0,40 / 0,25 | Council (el yaml dice `set_by: dueño`) | confirmación tuya |
| `wfc.sqx_gap_tolerance` / `sqx_gap_relative` | 1,0 / 0,01 | agente | ningún lote real repreciado contra el `NetProfit` de SQX |
| `wfc.r_sel_min_gap` | 0,05 | agente (el Council pidió la guarda) | idem |
| `top_share` | 0,20 | propuesta | medirlo |
| `rho_floor` | 0,30 (fuera del ledger) | código | P17-2 |

### Trabajo pendiente que no necesita tu respuesta

- Ningún lote real con `variant_trades.parquet`: la lectura real de `inputs/batch.py`, el ensayo build→oos1 de `wfc.calibrate` (probado solo con lote sintético) y la exportación de `pipeline/autopilot/variants.py` están sin verificar. La primera lectura de `oos2` por el WFC debe ser el bloque ciego real, nunca un test. Fuente: OPEN #50 (nota 2026-10-07, 336); enc. 48:12-14; WORKFLOW.md:46-47.
- Intervalo del ρ que respete la dependencia: el actual supone independencia (error 1,8-7× menor que el medido; N efectivo 8-145, mediana 17, frente a 220-477); solo 2 de 10 (`10.11.484` y C) distinguen su ρ contra `oos1` de «sin ventaja» al 5 % (con Bonferroni, 1). La dependencia mueve el PASA perdido, no el falso (sd del nulo de ρ 0,08 → 0,23 → 0,48); el generador debe reproducir la dependencia real (ruido 0,4 da sd 0,23 frente a 0,26 real). Fuente: P17:799-801,874,933; P17p:96-126,192-200; K `research/wfc-dependence-moves-missed-pass.md:6-11`.
- Limitaciones: controles y duplicados cuentan como puntos de la nube (G 332 → 203; mueve ρ ≤ 0,02); dos Sharpe en un cociente (SQX frente a Python difieren 1-38 %, sin medir por qué); README y figura describen cuadrantes pero ρ mide inclinación; neto del nulo difiere hasta 1.470 USD; `13.3.390` hizo 45 operaciones en `oos2` y no entra; `Strategy_10.11.484` no casa con `Strategy 10.11.484`; receta `pipeline/recipe.yaml:141` no arranca; abiertos: nº de sorteos del nulo (2.000) y top 20 % (¿10 %?) y cómo combina el 20 el WFC con CSCV, 18.5 y WFM; el nulo semanal es exacto para Spearman (5,1 / 5,0 %) pero sesgado en la cola inferior para la mediana. Fuente: P17:803-870,937-939; P17p:208-224; K `research/weekly-flip-null-skewed-lower-tail.md:6-12`.
- El WFC no se perfila (cuesta `oos2`); se medirá la primera vez que lo corras de verdad. Fuente: OPEN #42.
- `engines/variants/config.yaml`: `min_trades` y `split_mode` ya no los lee ningún estudio pero se cargan en el fingerprint (ver «Tests y código»). Fuente: `engines/variants/config.yaml:1-8,21,47`.
- Si en `drift_span` queda fuera el año de una operación, las derivas `b` y `d` no existen (ver 16.5). Fuente: enc. 48:9.

## Paso 18 — CSCV

Contexto mínimo: el CSCV mide la probabilidad de sobreajuste por selección (PBO) y `p_perdida`, la probabilidad de que la variante elegida pierda fuera.

### Decisiones tuyas

**P18-1 · ¿Qué pregunta debe contestar el CSCV?**
(a) «¿elegir parámetros sirve aquí?» (PBO: G sí, p < 0,02 sin corregir; `3.9.284` indicio; de las otras ocho ni sí ni no); (b) «¿es una meseta?» (el PBO no la responde: una meseta exacta da 0,5); (c) «¿cuánto infla elegir el mejor?» (caída de Sharpe de la elegida, G 1,09 → 0,77, que el estudio dibuja y no guarda). De ello cuelgan las demás decisiones.
- **Fuente:** P18:1062,1084.

**P18-2 · ¿Dónde pones las fronteras de NO PASA (0,5) y de LIMBO del CSCV?**
Hoy NO PASA si `p_perdida` ≥ 0,5 o PBO ≥ p95 de su nulo; LIMBO si `p_perdida` supera el p95 de su nulo propio (cambio tuyo del 2026-10-08, sin banda 0,25-0,5) o hay < 30 variantes. El corte de 0,5 suspende al 29 % de los paneles correlados sin ventaja (Sharpe semanal 0,03; 51 % a Sharpe 0). El LIMBO casi nunca salta con correlación (≈ 0,5 % a 0,2; 0 % a ≥ 0,6; solo 5,2 % en columnas independientes) porque el nulo se centra en la mediana de la propia muestra, y no puede dispararse si el p95 del nulo es ≥ 0,5. Un lote de variantes iguales supera 0,5 el 51 % de las veces. Alternativas: > 0,60 (2 fallan, 32 % de nulos), ≥ 0,71 (0), > 0,80 (4,2 %, sin calibrar fuera de 600 sorteos); exigir ≤ 0,30 (7 fallan), ≤ 0,18 (8), ≤ 0,08 (9). Tercer estado propuesto: < 0,18 estable, 0,18-0,8 no se distingue, > 0,8 perjudica (no propuesto como regla). Hay una tercera copia del 0,5 en `pipeline/config.yaml:54-62` (PROPOSED). El comentario de `criteria.yaml` aún habla de «cortes 0,25 y 0,5»: el 0,25 ya no existe.
- **Opciones:** dejar el p95 (hoy); centrar el nulo en otro sitio; leer contra la mediana del nulo más un margen; las alternativas numéricas de arriba.
- **Hoy el código hace:** p95 del nulo.
- **De esto cuelga:** Falla/Limbo del 18 y, con `peor`, el 20.
- **Fuente:** `criteria.yaml:251-267`; `cscv/README.md:45-70`; `cscv/POSSIBLE_IMPROVEMENTS.md:#1,#4`; `thresholds.yaml:56-62`; P18:807-868,1064-1070; WORKFLOW.md:47; K `research/cscv-null-probability-of-loss-above-limbo-cut.md:7-9`; EXP:541.

**P18-3 · Controles y copias en el panel, suelos de reparto, plateau, DSR y madre: ¿cómo se tratan?**
Canarios (controles) y la copia `P00001` compiten como candidatas (en `19.2.363` la elegida es un canario en 19,9 %); sin canarios el PBO sube de 0,391 a 0,441; G sin duplicados 0,073 → 0,121 (dentro del ruido). El suelo de 50 en `oos2` quita 9-36 % del panel. «El PBO es el mismo en todas las composiciones» es falso. El plateau a radio 1 es Argmax para la mayoría (21-100 % solas); como regla fallarían 4. La dominancia es «ninguna» por construcción (10/10). La unidad de `drift` no es comparable. El DSR incluye `build` (contradice PSR solo OOS) y deflacta solo por los grupos de una madre (en 4 de 10 no existen; con cada variante como prueba C pasa de 0,93 a 0,20). La «pendiente» tiene signo contrario en 8 de 10. G queda > 96 % entre sus variantes: parámetros cerca del mejor punto, no en meseta.
- **Fuente:** P18:893-947,949-965,980-988,1072-1076.

**P18-4 · Otras decisiones abiertas del CSCV: media de columnas igualadas frente a cero o mediana cruda, dominancia con tolerancia, números aleatorios comunes.**
Documentadas en `POSSIBLE_IMPROVEMENTS.md` (#1 «Owner's question, open», #2, #3); afectan a la potencia y al PBO.
- **Fuente:** `cscv/POSSIBLE_IMPROVEMENTS.md:3-14`.

### Lo resolverá la calibración

| Regla | Valor de hoy | Quién lo puso | Qué falta para fijarlo |
|---|---|---|---|
| `cscv.p_perdida` | Pasa < 0,5; Falla ≥ 0,5 | provisional «hasta calibrar» | población sin ventaja; potencia sobre paneles reales; si un PBO bajo predice (con 10 madres ρ +0,58 y +0,71 en G y `3.9.284`; las demás −0,27…+0,22) |
| `cscv.p_perdida_sobre_p95` / `pbo_sobre_p95` | < 1 (Limbo si no) / < 1 | tú (2026-10-08) | idem; medido pero casi nunca salta |
| Mínimo de variantes | 30 (menos = Limbo) | Council | idem |

### Trabajo pendiente que no necesita tu respuesta

- El CSCV lee la curva de mínimos diarios: `dailyEquity.bin` guarda el mínimo diario; las celdas se mueven 14-50 %; efecto en el PBO en poblaciones 0,37 → 0,35, 0,36 → 0,39, 0,40 → 0,52 (cruza la frontera); sobre un lote de variantes no medido. Reconstruir exige operaciones por variante (ver «Transversal»). Fuente: P18:821-840,885-891,976-1012,1078-1080; OPEN #88.
- Ningún número del CSCV llega a hechos (`contract.py:81-82`); falta población sin ventaja y curva de potencia sobre paneles reales. Documentación desfasada: el README dice 5.000 variantes y el tope es 500; `recipe.yaml:154`; N impar cuenta la central como sobreajustada. Fuente: P18:976-1012.
- No se ha corrido con lote real. Fuente: WORKFLOW.md:47.
- El paso 18 no se ha perfilado (cuesta `oos2`). Fuente: OPEN #42.

## Paso 18.5 — Superficies por mercado

Contexto mínimo: el 18.5 compara la superficie de rentabilidad de la madre con la de las mismas variantes retesteadas en otros mercados (11 declarados, 3 estructurales). Está partido en dos: la lectura que decide (build+oos1) se juzga tras el 16.5 y antes del bloque ciego; la de `oos2` solo puede añadir LIMBO.

### Decisiones tuyas

**P185-1 · ¿Decide algo el 18.5 o solo anota?**
Hoy su «fail» marca DESCARTAR en el 20 y falló las 10 madres; en `10.11.484` es el único motivo. No lo pasa ni el NIKKEI contra sí mismo (1/10) ni tres índices de EE. UU. casi iguales (3/60). Potencia «cercana a cero»; la regla pasó 0/1.000 sorteos sin ventaja. «No viaja» = «no ha llegado a 6 de 11».
- **Opciones:** (a) como hoy (decide); (b) solo anota.
- **Fuente:** P185:1263,1271-1273,1344,1362-1363,1377-1381; WORKFLOW.md:49.

**P185-2 · ¿Qué valen el suelo 0,30, la banda de 97,5 % y «la mitad de mercados», y el `min_weight` 5,0?**
Los tres primeros están firmados «agente», fijados antes de ver ningún lote; «mitad de mercados» es «PROVISIONAL hasta que el dueño lo fije». Banda de urna optimista (contraste de voltear días: 0,066 y 0,233); nivel real de `j>j_hi` 0,8-1,9 %. Ningún umbral aislado cambia el resultado: suelo 0,20 / 0,10 / 0 → 0 madres cambian; mercados exigidos 3/11 → 0; 2/11 → 1 sale de «no viaja»; 1/11 → 6 salen, pero contando `oos2` ninguna «viaja» y C llega a 1 por azar el 61 %. `min_weight 5,0` es la SUMA de pesos (el trío USA500/USATEC/DJ30 vale 1), no el número de mercados, y es el único umbral de la tabla marcado «provisional … pendiente de que el dueño lo confirme». `premium_percentile 5` está «sin calibrar (§10.1)».
- **Opciones:** confirmar o cambiar cada valor.
- **Fuente:** P185:969-1021,1110-1124,1210-1215,1348-1350; `marketSurfaces/README.md:88-102,136`; `marketSurfaces/config.yaml:25-29`; `thresholds.yaml:158,174`; K `research/surfaces-jaccard-lift-flip-null.md:6-14`; EXP:574-580.

**P185-3 · ¿Rho bruto o neutral? ¿Tramos? ¿Contraste en build? ¿Qué es un mercado?**
El código decide con rho neutral (`call.py:25,27`), las barras pintan el bruto y el manual y `POSSIBLE_IMPROVEMENTS` dicen «bruto, como pediste»; G contra HK50 sale en rojo con la barra entera sobre el suelo. Bruto: 5/2 parejas; neutral: 6/3; 0 madres cambian. Tramos: la llamada exige build, `oos1` y `oos2`; el intervalo de Fisher es ~3,6× estrecho y el contraste bueno (`lift.py`) no está enchufado. El contraste de voltear días en build es un contraste de azar en el build (doctrina: azar solo OOS): «te toca decir si entra». USA500, USATEC y DJ30 cuentan como 3 votos de 11 (≈ 10 independientes sin ventaja); no hay mínimo de variantes por pareja (n = 1 o 3 salen «en duda», 4 parejas de `19.2.363`); un mercado sin celdas desaparece sin aviso.
- **Opciones:** bruto o neutral (hoy neutral); contraste en build sí o no.
- **Fuente:** P185:1130-1142,1184-1208,1238-1257,1345,1349-1352.

**P185-4 · Siete lecturas «abiertas» que eligió el agente: ¿las confirmas?**
La familia plantada de la curva de potencia (mezcla gaussiana de cópula); el top es un solo conjunto, escogido por el exceso neto del principal; los empates cuentan como igualdad exacta del bruto; los duplicados se miran solo con operaciones build+oos1; `oos2` sin dato da `sin_dato = 1` (Limbo, tú 2026-10-08); no se aplica el escalado por año de la propuesta. Cada una es «un mando o una función» que puedes cambiar.
- **Fuente:** `marketSurfaces/README.md:88-102,136`; `marketSurfaces/POSSIBLE_IMPROVEMENTS.md:3-4`.

**P185-5 · ¿Cuántas variantes por mercado aleatorio (se decide en el 18.5)?**
- **Fuente:** enc. 48:246.

**P185-6 · Mejoras propuestas del 18.5: ¿plantar la transmisión en las semanas, una llamada por categoría de `_markets.yaml` y qué hacer con `marketSurfaces_detalle.json`?**
Plantar la transmisión en las semanas (no en las puntuaciones); una llamada por categoría de `_markets.yaml` (multiplicaría los looks); el fichero `marketSurfaces_detalle.json` («If nobody opens it, delete it»; pesa 299 MB y el 20 lo carga entero).
- **Opciones:** las tres, a hacer o no.
- **De esto cuelga:** potencia del nulo y espacio en disco.
- **Fuente:** `marketSurfaces/POSSIBLE_IMPROVEMENTS.md:6-22`; P185:1259-1282.

**P185-7 · ¿Cuántas variantes mínimo para llamar «meseta» a una región (recuadro de la meseta, encargo 38)?**
El encargo 38 necesita de ti un mínimo de variantes.
- **Fuente:** README encargos:116-121.

### Lo resolverá la calibración

| Regla | Valor de hoy | Quién lo puso | Qué falta para fijarlo |
|---|---|---|---|
| `orden.estado` | Pasa ≥ 0 | agente | lote real |
| `prima.bajo_p5`, `oos2.perverso`, `oos2.sin_dato` | < 1 (Limbo) cada una | agente / tú (sin_dato 10-08) | lote real; `premium_percentile` 5 sin calibrar |
| `min_weight` | 5,0 | agente (provisional) | P185-2 |

### Trabajo pendiente que no necesita tu respuesta

- Solo probado con paneles sintéticos (18 s con 500 variantes × 11 mercados); potencia con ventaja real, qué rho esperar entre Nikkei y cada mercado, si predice algo y `oos2`, sin medir. Fuente: `marketSurfaces/README.md:136-138`; P185:1259-1282; WORKFLOW.md:49.
- Textos fijos desfasados: se pega siempre «los 9 mercados» (real: 11 declarados, 3 estructurales) y la frase de costes provisionales aunque `costs_provisional` es false; `WORKFLOW.md:48` avisa de «comisión CERO»; los costes con que se retestaron las variantes en los once mercados no están verificados; README dice 9-11 s y 5.000 × 10 mercados, real ≈ 500 × 12, 245 s en C; la decisión mira todo el orden y el 10 % mejor, no una región (la meseta tiene 1-4 variantes). Orden de ejecución del 20 respecto a `marketSurfaces.json` sin comprobar. Fuente: P185:1161-1182,1223-1236,1356-1359.
- Comprobación de unidades (parámetros absolutos o adimensionales) no hecha; Jaccard y lift se retiraron el 2026-10-07 y el 18.5 lee Spearman contra nulo semanal. Fuente: K `research/surfaces-jaccard-lift-flip-null.md:6-14`.

## Paso 19 — WFM (Walk Forward Matrix)

Contexto mínimo: la WFM de SQX corre una matriz de 30 celdas de walk-forward sobre toda la ventana; hoy solo marca (`DeleteFailedStrategies=false`) y el análisis (L1, L2…) juzga en `oos2`.

### Decisiones tuyas

**P19-1 · ¿La marca de SQX de la WFM (área 4×4 ≥ 12 celdas, 80 %) decide algo?**
Hoy solo marca: 7/10 marcadas (quedan C, E, G); C y E pasan con el mínimo exacto (12). Las celdas valen 2-4,6 efectivas, no 30. Opciones: mínimo 14 deja solo a G; 70 % mete una cuarta; matriz 60 %/8 → 8 pasan, 80 %/12 → 3, 100 %/12 → 0. El YAML dice que SQX «descarta» (marca).
- **Fuente:** P19:880-912,984-986,1055.

**P19-2 · ¿La lectura «perversa» sigue siendo fallo en el 20?**
Marca DESCARTAR a 5/10 (el informe la llama «la decisión con menos respaldo»). El azar puro da «perversa» 64-74 % (36 % sin solape); intervalo 4,2-5,2× estrecho; centro −0,15…−0,21 por sesgo de solape. «Predice» sale 8-12 % sin ventaja y el de F no sobrevive a 10 miradas. L1 decide hoy (NO PASA si p− ≤ 0,05); una corrida real con 10 madres del Nikkei dio 4 PASA, 5 LIMBO y 1 NO PASA.
- **Opciones:** pasar a «vigilar», o arreglar el intervalo (bootstrap por bloques del 2026-10-01 sin construir; celdas efectivas no se calculan en código).
- **Fuente:** P19:864-868,930-970,1026,1056; WORKFLOW.md:50.

**P19-3 · ¿Qué tipo de walk-forward debe escribir la WFM, exacto o simulado?**
Decidiste `exact_is_exact_oos` el 2026-09-24. Hecho comprobado: `assets/_build.yaml:483` hoy dice `wf_type: exact_is_exact_oos`; el informe P19 que citaba un cambio a `simulated_is_simulated_oos` está desfasado. Queda confirmar que es lo que quieres.
- **Fuente:** `assets/_build.yaml:483`; P19:918-928.

**P19-4 · ¿Con qué spread se recarga la ventana de `oos2` de la WFM?**
`wfm.py:128` usa `costs_segment: oos1` para toda la ventana (NIKKEI225 474,91 frente a 796,12 de `oos2`: `oos2` al 60 %, build a +56 %); la pestaña del azar hereda el coste. El export cobra costes de `oos1`.
- **Fuente:** P19:918-928,976-978; K `export/wfm-export-recharge-and-score.md:6-11`.

**P19-5 · ¿Qué se hace con los umbrales de la WFM calibrados solo con el oro?**
Los diez umbrales se calibraron con 150 celdas de XAUUSD (5 estrategias del master); en NIKKEI225 C5 79 % → 42 %, C8 11 % → 26 %. `_build.yaml` dice que los porcentajes son «del ORO: en otro activo no valen y no se han recalibrado». `ledger/thresholds.yaml` no tiene entradas de WFM. El `score` incluye un tramo optimizado (C6 71 % frente a 34 %; E pasa solo por eso); 9 condiciones sin score, no calculado. Tramo: 67-79 % de lo que llama OOS es build y `oos1`; C1, C2, C7 inflados; `oos2` son 2,75 años (Sharpe ±1,2); la skill dice fechas de `oos2` pero siempre salen 2013-2023.
- **Fuente:** P19:918-928,976-978,988-998,1057-1061,1069; `assets/_build.yaml` (WFM, hunk 340-370).

**P19-6 · Siete preguntas de diseño de la WFM y `modo_real`: ¿las confirmas?**
(1) la referencia de L2 en modo `fijo`; (2) la cola baja del nulo con semanas asimétricas; (3) qué deriva se resta; (4) la recarga de costes es aritmética, sin mover stops; (5) build/`oos1` no se recargan en la tabla por segmento; (6) celdas efectivas sesgadas a la baja (~25 de 30); (7) la deriva cuenta cambios, no distancia. `wfm.skew_warn 1,0` lo puso el agente. `modo_real` por omisión es `fijo`; `reoptimizado` añade dos reglas `wfm.reopt.*` que solo dan LIMBO y cuyos umbrales no tienen calibración documentada.
- **Opciones:** las que enumera `wfm/POSSIBLE_IMPROVEMENTS.md`.
- **De esto cuelga:** el estado 19 que lee el 20.
- **Fuente:** `thresholds.yaml:1406`; `wfm/POSSIBLE_IMPROVEMENTS.md:#1-#7`; `wfm/README.md:63,66-70`; `criteria.yaml:287-304`.

### Lo resolverá la calibración

| Regla | Valor de hoy | Quién lo puso | Qué falta para fijarlo |
|---|---|---|---|
| `wfm.l1.p_menos` | Pasa > 0,05 | tú | calibración con paneles reales |
| `wfm.l1.mediana_exceso` | Pasa > 0; Limbo si no | idem | idem |
| `wfm.reopt.*` | solo Limbo | agente | calibración y medición del coste del reoptimizado (WORKFLOW dice ✅ sin anotarlo) |
| `wfm.skew_warn` | 1,0 | agente | provisional |
| Diez condiciones de la WFM (porcentajes) | del oro | agente | recalibrar por activo |

### Trabajo pendiente que no necesita tu respuesta

- Pestaña «Contra el activo y el azar» de la WFM: el beneficio no cuadra con SQX. Con p ≤ 0,05 caen 9/10 (queda `10.11.484`, p = 0,031); batir al activo hace caer las 10; no perder contra el activo no hace caer ninguna. Para C el azar da 7.021,62 y SQX 4.337,65 (+62 %), sin explicar (candidato: valor del punto y coste por operación; solo mirado en C). «reconcile» 0,997 es una correlación y no detecta diferencias de nivel. Hasta cerrarlo, ninguna p de esa pestaña es utilizable. Fuente: P19:890-892,992-994,1062.
- El paso 19 no guarda hechos y no hay carpeta `paso-19`; `blindJoint.verdict.19_wfm` es solo ρ. La deriva divide por dos columnas de más (0,63-0,80 en vez de 0,80-0,92 y sale alta en las 10). Dos tramos sin estadísticas (2 de 3.300). No se comprobó en el log si hubo las 5.000 pruebas por optimización ni cómo reparte SQX los 18 escalones del ±35 %. Nada aguas abajo usa los parámetros recomendados. README con «79 % de solape» (media 70 %) y tablas de XAUUSD; «% OOS» del YAML (40 %) es 28,6 %. Fuente: P19:862,870-878,968-982,1000-1011,1063.
- El export tiene 103 operaciones `EndTest` fuera de rejilla; el `score` de SQX sale de `all_` (67-79 %). Fuente: K `export/wfm-export-recharge-and-score.md:6-11`.
- El nulo de volteo semanal es sesgado en la cola inferior para la mediana (WFM L1: 13,3 % en una madre con sesgo positivo); `wfm.null.skew_warn` (1,0, provisional) solo avisa. Fuente: K `research/weekly-flip-null-skewed-lower-tail.md:6-12`.
- Con cero condiciones activas `MinConditions` y `MinMarkets` quedan inertes; se dejan «como estén … comprobar en la primera corrida real que no cae nadie». Fuente: `assets/_build.yaml:134-137`.
- El paso 19 no se ha perfilado (cuesta `oos2`). Fuente: OPEN #42.

## Paso 20 — Análisis conjunto de 17, 18, 18.5 y 19

Contexto mínimo: el paso 20 (`blindJoint`) combina los estados de los pasos 17, 18, 18.5 y 19 y calcula el SPA/StepM (contraste de superioridad sobre `oos2`). `joint.pieces` es la regla de combinación; `peor` significa que manda el peor de los cuatro estados.

### Decisiones tuyas

**P20-1 · ¿Qué es «pasar» el paso 20?**
El paso 20 no tiene definición de «pasar»; `criteria.yaml` no tiene reglas para el 20 (ni para 21, 23 y 24, «annotate only, no rule on purpose»). Lecturas escritas: `unanimidad`, `sin_fallo` (la que fijaste el 2026-10-04), `ninguna` (solo decide el StepM, ya existe en `blindJoint/config.yaml`), y `peor` (fijada provisionalmente el 2026-10-07 hasta que rediseñes el paso: algún NO PASA → DESCARTAR, algún LIMBO → REVISAR, si no MANTENER). Con `sin_fallo`, un «fail» de WFC, CSCV, 18.5 o WFM marcó DESCARTAR a las 10 madres, y el paso 20 no tiene corte. Con `peor`, cualquier LIMBO de 17/18/18.5/19 manda a REVISAR a cada madre (y como el 18 casi nunca da LIMBO por el p95, ver P18-2). Cuatro del Council votaron «ninguna pieza en fallo», uno «unanimidad». El 48 decidió que el 20 traduce el estado del 17 (PASA es un veto levantado, no un voto), sin rediseñarlo. `joint.population = entrantes` está decidida (Council 2026-10-04) y el StepM no decide bajo `peor`.
- **Opciones:** `unanimidad`, `sin_fallo`, `ninguna` (solo StepM), `peor`, u otra lectura rediseñada; presentarlas con sus lecturas escritas, lo que costaría y lo que ganaría.
- **Hoy el código hace:** `peor` (provisional).
- **De esto cuelga:** qué estrategias llegan a 21-26; D3 del encargo 41 y D2 del 43.
- **Fuente:** `studies/closing/blindJoint/config.yaml:20-35`; `blindJoint/README.md:53-62`; `blindJoint/readings.py:20`; `criteria.yaml:59`; `tests/test_blindjoint.py:111`; WORKFLOW.md:50,247; DP:295-320; COU:162-174; enc. 41:143,207; enc. 43:29-30,93; P17:698,929; P18:1030,1068; P185:1297,1344,1362-1363; P19:864-868,1056; `autopilot/README.md:197-198`.

**P20-2 · ¿Puede un agente autónomo leer `oos2` para BlindJoint, o debe quedar fuera?**
Hecho comprobado hoy: `assets/_policy.yaml:48` lista `BlindJoint` en `reserved_for` (añadido por ti el 2026-10-04), así que un agente autónomo (`ALGO_AUTONOMOUS=1`) lo encuentra cerrado, y un humano no. Siguen abiertos: si ese agente debe ser retenido siquiera; que el SPA sobre `oos2` se lea para un humano pero solo un agente autónomo lo encuentre cerrado; qué cosecha de operaciones se hace (la decisión del 2026-10-04 fue cosechar solo la madre, `mothertrades.py`; las operaciones por variante, CSCV reconstruido, siguen sin decidir, y su coste es ~90 min por lote — el encargo 48 revirtió E3). El SPA de blindJoint se rechaza hasta que el 16.5 coseche `trades.parquet` por variante. La pregunta 9 del Council: ¿se añade blindJoint a la lista?
- **Opciones:** ya está añadido (hoy); retirarlo; decidir la cosecha por variante.
- **Fuente:** `assets/_policy.yaml:48`; COU:76-77,101-102,193; DP:270-291; WORKFLOW.md:50; K `perf/variant-trades-export-cost.md:6-11`; OPEN #50 (307-336), #88 (536).

**P20-3 · La mirada del 2026-09-26 a `oos2` de dos madres USDJPY fuera de la puerta: ¿añades una fila al ledger?**
Una sesión leyó el P&L diario de `oos2` de dos madres USDJPY fuera de la puerta y no hay fila de ledger de esa mirada.
- **Fuente:** OPEN #50 (307-336).

**P20-4 · ¿Qué `--family` usan WFC y CSCV?**
La exigen WFC y CSCV pero no la pasan `pipeline/recipe.yaml` ni `ui/daemon/runner/optimisation.py`; Q9 decide de dónde sale la familia.
- **Fuente:** OPEN #50.

### Lo resolverá la calibración

| Regla | Valor de hoy | Quién lo puso | Qué falta para fijarlo |
|---|---|---|---|
| `joint.pieces` | `peor` | tú, provisional (2026-10-07) | rediseño del paso 20 (P20-1) |
| `joint.population` | `entrantes` | Council 2026-10-04 | decidido |
| Pasos 21, 23, 24 | solo anotan | Council 2026-10-04 | nada: «a propósito» |

### Trabajo pendiente que no necesita tu respuesta

- El orden de ejecución del 20 respecto a `marketSurfaces.json` y el hecho de que el 18.5 y el 20 cargan un JSON de 299 MB están sin comprobar; la composición con el WFC, CSCV, 18.5 y WFM sigue abierta. Fuente: P185:1356-1359; P17:937-939.
- `studies/closing/atrCalculator` (paso 24): `shape.tolerance` 0,10 está marcado «provisional default: the owner will set his own criteria». Fuente: `atrCalculator/config.yaml:43-46`.
- El SPA/StepM del encargo 10 B y la sobre-lectura de `oos2` no tienen aún lote real. Fuente: WORKFLOW.md:50.
- La skill y los README de `blindJoint` describen el estado del 17 con nombres antiguos (`no_fiable/indeciso/fiable`) y el 18 como «PBO over 0.5» (hoy p95 del nulo) — ver «Documentos que se contradicen». Fuente: `blindJoint/README.md:47-50,71`.

## Transversal: calibración, oos2 y registro

### Decisiones tuyas

**T-1 · ¿Cuándo y cómo se corre la calibración con población nula y plantada, y quién autoriza el gasto de `oos2` en ella?**
Ningún umbral de los pasos 8 a 19 está congelado (`criteria.yaml:59`: «PROVISIONAL (Council 2026-10-04): do not freeze before a null population has run the chain»). No hay tasa de falsos positivos ni potencia medidas para estas reglas. La propuesta es ≥ 5.000 estrategias por nivel (nula y Sharpe por operación 0,05 / 0,10 / 0,15; EXP añade 0,04) con la cascada apagada, en `studies/screening/falsePositives/`. Para los pasos 14-19 la nula serían ≈ 1.100 «monos seleccionados» (mide una tasa del 1 % con ±0,3 %); coste de CPU: 26 min de SPP por cada diez estrategias y un 16.5 por estrategia para 17/18. Antes de lanzar proyectos `Trade_` hay que congelar la versión 2 (1.9) con las tablas 1.7 y 1.8 delante («cuántos monos dejo pasar»). La autorización de `oos2` para calibrar murió con el borrado de `Test_Calib`: cualquier calibración nueva que lo necesite se pregunta otra vez. Además, las diez madres `Trade_NIKKEI225_M30_volatilidadL` (largas, M30) no sirven para calibrar: fallan hoy los pasos 8 y 10 y su `oos2` ya se leyó (en 18.5), y no hay medición para H4, builds largos ni réplicas. El encargo 9 (monos) se reabrió con la premisa «monos antes de mirar supervivientes reales»; la respuesta formal no consta (D5 del encargo 41).
- **Opciones:** autorizar la corrida por pasos (primero el 9, luego el 30); reservar `oos2`; definir qué población sirve en lugar de las diez madres.
- **Recomendación del agente:** D5 del encargo 41: primero el encargo 9, luego el 30.
- **De esto cuelga:** congelar `ledger/thresholds.yaml`, apagar `dev.on` y poner PASA con contenido en los pasos 10, 12 y 14-19; lanzar `Trade_`.
- **Fuente:** IND:84-96; ESP:104-105,1132-1163; EXP:123,644-650,683-688; P14:1053-1055,1129-1130; P16:858-864; P17:875,943; P18:1078; P185:1375-1376; P19:1006,1071; C04:53-54,300-304; enc. 41:145,231-236; memoria `oos2-autorizado-para-calibrar-criterios`.

**T-2 · D4: ¿La reserva de `oos2` ata al autopilot (`ALGO_AUTONOMOUS=1`) y un estudio ya empezado conserva su `oos2` de partida?**
La recomendación es «Sí, no puede leerlo». K dice que desde el 2026-09-28 la puerta solo vincula bajo `ALGO_AUTONOMOUS=1` y para un humano está abierta. `bin/monthly-oos2-roll.sh` corrió el 2026-10-03 y alargó `oos2` hasta fin de septiembre y lo alarga cada mes. Ningún estudio guarda su ventana de `oos2` (`assets/_policy.yaml`): anclarla es un diseño sin hacer. En el texto no consta contestada formalmente, aunque el código ya pone `ALGO_AUTONOMOUS=1`.
- **Opciones:** sí/no a que ate al autopilot; anclar o no la ventana por estudio.
- **Recomendación del agente:** «Sí» (sesión del encargo 41).
- **Fuente:** enc. 41:144,147-149,184; DP:202-211; COU:44,73-75,193; K `pipeline/blind-steps-write-no-ledger-rows.md:6-13`.

**T-3 · ¿Ampliamos el sello de `oos2` (`JUDGED`) a los pasos 18, 18.5 y 19?**
`JUDGED = (17,)` en `ledger/gate.py:18-28`: solo el paso 17 exige un criterio escrito y calibrado para leer `oos2`. Los pasos 18, 18.5 y 19 también leen el bloque ciego con criterios provisionales. Impacta el gasto de `oos2`.
- **Fuente:** `ledger/gate.py:18-28`.

**T-4 · ¿Qué hace la ventana con las seis preguntas de Criterios?**
(1) ¿Se añaden las métricas de SQX (Net Profit, PF, Ret/DD, IS y OOS) como criterios? (2) ¿Qué databank recortan los pasos 17-25? (3) ¿«Congelar» debe negarse con el modo desarrollo activo y la pestaña debe poder apagarlo? (4) ¿Se sustituyen los limbos `>= -1000` por `else: limbo`? (5) ¿Se editan desde la pestaña las excepciones y el paso 6? (6) ¿Nombres en español para los criterios? Los clics reales y la confirmación de «Congelar» no están probados.
- **Fuente:** FUI:18,190-202,221.

**T-5 · ¿Reconstruir la curva diaria a cierre (low-to-low) o documentar el sesgo, estudio por estudio? ¿Cosechar las operaciones por variante en 16.5 para el CSCV?**
La curva diaria de SQX (`dailyEquity.bin`) es el mínimo del día. Hay que decidir, por estudio (WFC, CSCV, blindJoint, exposure), entre reconstruir la curva a cierre (con `portfolio/common/construct/equity/`) o documentar el sesgo. Medido el 2026-10-04: `snoopingScreen` sobredimensionaba el benchmark un 15-26 %; SPA p 0,72→0,58 / 0,95→0,95 / 0,79→0,73; CSCV PBO 0,37→0,35, 0,36→0,39, 0,40→0,52. Cosechar las operaciones por variante cuesta ~90 min por lote.
- **Opciones:** reconstruir o documentar el sesgo; cosechar por variante o solo la madre.
- **Fuente:** OPEN #88 (526-536); enc. 41:35,188-197; P18:821-840; DP:270-291.

**T-6 · Registro del ledger: ¿qué se rellena hacia atrás y qué cuenta como N de pruebas?**
El 1.3 pide un registro completo (repasar que ningún paso quede sin fila) y rellenar hacia atrás las 23 poblaciones `Test_Calib_*` (87.357 estrategias) que sí se miraron, aunque esa calibración se borró el 2026-10-04 y el punto puede ser obsoleto; sin ese registro el Sharpe desinflado sale optimista. Preguntas: a) ¿cuáles 23 de las 28 poblaciones?; b) ¿N cuenta generadas (millones) o aceptadas? (cambiarlo altera todos los ajustes por pruebas múltiples); c) ¿«Aceptadas» = 4.600 o 4.238?; d) ¿las poblaciones de calibración llevan fila del 6 y del 8? Borraste las filas del ledger de `Test_Calib` contra el consejo del Council. COU R1c: «aceptadas» = Accepted de SQX (4.600), confianza baja; el código ya lo hace. Qué invalidaría R1b: si sintéticas con ventaja conocida no sobreviven con N = generadas, el funnel no tiene potencia (voto de Kahneman).
- **Fuente:** enc. 41:33,160-173,258; DP:187-200; COU:103,197-201.

**T-7 · ¿Añadimos claves por familia en `criteria.yaml` (`by:` de familia)?**
Hoy `by:` solo admite timeframe, símbolo y clase de activo. Si los criterios han de variar por familia hay que añadirlo con su test.
- **Fuente:** enc. 42:143-146.

**T-8 · Pasos 6-8 y 10-20: ¿cómo se firma un criterio como «tuyo»?**
El 1.2 pasa a firmado el criterio provisional de los pasos 6 y 8: las cifras de `assets/_study.yaml` siguen siendo «propuesta de agente»; `criteria.yaml` debe recibir las reglas del paso 8 y `dev.on: false`, y las cifras necesitan `set_by`/`set_on` en `ledger/thresholds.yaml`. La firma es provisional (v1); la definitiva es el 1.9. Además hay que adoptar cada criterio de los pasos 10-20 y apagar `dev.on` (D5 del encargo 43). Los umbrales de crossmarket, crossTF, mcRetest y WFC siguen en cada `config.yaml` y deben pasar a `ledger/thresholds.yaml`; el encargo 46 siguió al 44 y no los movió.
- **Opciones:** hoja PDF `decisiones-pendientes-2026-10-04` con los dos lados (D1, D2).
- **Recomendación del agente:** la sesión del 41 recomendó para D2 `drift_excess_t`, Limbo ≥ 1,65 y Pasa ≥ 2,33 (superada por el encargo 44).
- **De esto cuelga:** que una corrida del autopilot corte en el paso 8 por regla y no por sorteo.
- **Fuente:** enc. 41:32,141,151-158,199-209; enc. 43:97; enc. 46:274-276.

**T-9 · El archivo de criterios ¿sigue sin sellar (`frozen`)?**
El Council 2026-10-04 dice no congelar antes de que una población nula corra la cadena; el archivo no tiene `frozen`. Existe `ledger/criteria-history.jsonl` con cambios hasta el 10-08.
- **Fuente:** `criteria.yaml:58-59`.

### Lo resolverá la calibración

| Regla | Valor de hoy | Quién lo puso | Qué falta para fijarlo |
|---|---|---|---|
| Todas las líneas de los pasos 8-19 | «convención» | Council 2026-10-04 / agentes | T-1: población nula y plantada |
| Cada Pasa/Limbo/Falla de 14-19 | provisionales | idem | idem (≈ 1.100 monos seleccionados) |
| Umbrales del Monte Carlo de cartera (`survival_dd_pct` 10 %, veto de bloque muerto 24 meses, subpuntuación de Family D) | placeholders (veta 21 y 30 de 36) | aplazados por ti el 2026-09-29 | futuro; no bloquea (OPEN #19) |

### Trabajo pendiente que no necesita tu respuesta

- 0.3 El push real con `commit_apply` no se ha probado (solo `--dry-run` y 7 grupos reales). Fuente: enc. 41:257.
- 0.5 `/tmp` bajó del 93 % al 54 %; falta comprobar «< 50 % tras una corrida completa». Fuente: enc. 41:28,254,257.
- 0.6 Higiene de cron y auditoría mecánica: la auditoría mecánica sigue saliendo con 1 por tres causas ajenas (`checks.py` rojo por la sesión de Investigar, el proyecto `Infinox_SP500ft_H4_HighPrecision` que no se pinta y un export sin manifiesto); 13 pruebas apartadas con motivo en `tools/audit_tests.py` (OPEN #95); sin apuntar en OPEN que `ledger/thresholds.py` rompe con el feed `UKOIL.cash_M1` (0.7 dice que ya es OPEN #94). Fuente: enc. 41:29,254,257.
- 1.4 Autopilot para población nula: el código está (`ALGO_AUTONOMOUS=1`, cero supervivientes como final limpio), pero no consta probado el criterio de tres corridas seguidas a cero supervivientes que acaban en `FIN`, ni matar la JVM a media corrida y obtener un fallo con mensaje (y R5: ¿un «Project stopped» manual es fallo o parada?). Fuente: enc. 41:34,175-186,258; DP:213-236.
- 1.6 Reglas de los pasos 10, 12, 14, 16 y 20: ningún paso que juzga debe tener `rules: []` sin razón escrita. Fuente: enc. 41:36,199-209.
- 1.7 Monos por la cadena (encargo 9): falta el mono del paso 10 y la corrida a 10.000 con `--ledger` (es tuya, README:44); 1.8 monos seleccionados en SQX (encargo 30) cuesta una corrida de autopilot de custodio por población, con `Test_` retirados al acabar. Fuente: enc. 41:37-38,211-229; README encargos:44,100.
- Los pasos 10, 12, 14, 16 y 20 no tienen comparación con la gemela aleatoria, ni medida de cuánta evidencia nueva añade cada paso (los que releen `oos1` añaden poco), ni equipo rojo, ni embudo del 8 al 20 por población y agrupado; falta dar al riesgo flotante un lugar en los pasos 10-20 y exponer los hechos que faltan antes de calibrar. Fuente: enc. 43:43-87.
- Autopilot fases 2 y 3 sin cablear: `pipeline/recipe.yaml` falla como está escrito (a `ran` le falta `--project`, a `wfc`/`cscv` les falta `--family`, `--chart` fijado a XAUUSD); el paso 25 no recoge la versión con stop; no hay pool para el 26; bloquea los hechos «comparado con el original» del paso 12 que la celda baseline tuvo 0 operaciones en las 30 madres; solapar dos poblaciones solo si la medición muestra tiempo muerto grande. Fuente: OPEN #90 (684-695).
- Costes cambiados a mitad del run del 9-30: las patas del WFC se configuraron con el spread antiguo de USDJPY (0,65), mientras el activo lleva ahora 0,49 / 0,59 / 1,16 por tramo; los pasos 16.5-24 corrieron con patas viejas. Otras limitaciones del mismo run: MC Retest con dos tablas de nivel inservibles (`bar/4.3.53`, `ohlc/8.13.72`); el control «madre reconstruida» del paso 23 imprime tabla vacía; el paso 25 lee la madre sin su stop; «Replicación» nunca corre en un proyecto de workflow; «Filtros candidatos» exige ≥ 200 estrategias y tras el corte quedan 60; Hantec sigue fallando filas 1/3a/5 (drawdown 0,292 % SQX vs 0,228 % MT5 en 10.9.72). Propuesta: ofrecer el salto de nombre cuando el resultado esté en otro databank (`ui/daemon/runner/offer.py`). Fuente: OPEN #89 (578-598).
- Los pasos 17-19 no se han perfilado (cuestan `oos2`); se medirán la primera vez que los corras de verdad. Fuente: OPEN #42.
- Mejoras de velocidad del workflow: medido 230 → 159 min, ≈ 140 min estimado tras dos arreglos recientes («aplicado, sin medir junto»); reabrir SQX antes de SPP/WFM recupera 8-10 min por paso (probado solo con el SPP); `bin/workflow.sh template` con una plantilla real sin probar; ideas sin probar: exportar varias bases en un arranque de Java (1,5-2 min), saltar cosechas que nadie lee (≈ 1 min), feed quality en paralelo (≈ 1 min), limitar hilos del 18.5 (1-2 min), pasos 21 y 22 en paralelo. No tocado por ser decisiones tuyas: precisión de los backtests, simulaciones del MC, variantes por madre, cuántas pasan cada corte. El paso 26 (MT5) quedó fuera de la medición. Fuente: AS:7,174-189; TB:57-59,79.
- Cadena SQX: `Project finished` aparece antes de que todo esté en disco; un worker matado durante el sync pierde la databank del retest y puede dejar un `.sqx` roto; cada acción de SQX gasta ~27 s en arrancar y 90-230 s en exportar; huella del `optimizationProfile.bin` con otra causa abierta 🤔; arrastrar el spread-en-% a un segmento antiguo infraestima 2-4× (elasticidad −0,64 NIKKEI225, aplicado el 2026-10-04). Fuente: K `sqx-drive/unselected-build-population.md:6-13`, `costs/funded-tick-spread-vs-price.md:6-14`, `sqx-format/optimization-profile-byte-order.md:6-12`, `perf/autopilot-dead-time.md:6-13`.
- Referencias muertas a `Test_Calib` y `scratch/calib*`: `perf/inputs/construct.py:21` (`CLOSE_HARVEST`), `tests/test_progress_genetic.py:16`, `tests/test_portfolio_golden_current.py:18,33`, `ledger/backfill.py:121`, `ledger/README.md:20`, `tests/README.md:266`, `studies/transfer/crossTF/README.md:82`. Fuente: búsqueda de rutas anteriores.
- Costes provisionales de XAGUSD, UKOIL y USOIL arrastran avisos en todos los estudios (18.5 emite `costs_provisional`). Fuente: `studies/research/board/config.yaml:45`; `marketSurfaces/inputs/markets.py:33-36`.

## Tests y código

### Decisiones tuyas

**X-1 · Fixtures de datos reales borrados por la limpieza del 10-06: ¿se regeneran o se convierten en pequeños fixtures?**
`test_ui_batch` y `test_autopilot_closing` dependen de `strategyPermutations/<REAL>/metrics.parquet` y del lote de variantes de 10.9.72: ¿se regeneran (requiere corrida) o se convierten en fixtures pequeños? `test_mt5_start_check` lee un journal `20260930.log` que ya no existe: ¿fixture en el repo o retirar el test? `test_portfolio_universe`: ¿regenerar fixtures reales o usar uno sintético?
- **Opciones:** regenerar con corrida; fixtures pequeños; retirar; sintético.
- **Fuente:** `AlgoData/audit/2026-10-07-fixes.md`; OPEN #107.

**X-2 · `test_portfolio_build`: ¿cómo se arregla que ningún miembro del pool concilie?**
Decidiste el 2026-10-05 que corra con las condiciones actuales sin shim ni skip. Hoy nada del archivo reconcilia: los 15 con cosecha fallan por la licencia MAE/MFE (0,73-0,97, suelo 0,99), por desajuste de reloj de feed. Decides si se arregla la reconstrucción de equity o el estampado archivado, o se archiva una estrategia fresca.
- **Opciones:** arreglar la reconstrucción de equity; arreglar el estampado archivado; archivar una estrategia fresca.
- **Fuente:** OPEN #95; OPEN #104 (nota 2026-10-05, 858); `2026-10-08-mechanical.md:199-209`.

**X-3 · El árbol de trabajo bloquea al fixer: ¿commiteas o descartas?**
601 rutas sin commitear (25 grupos propuestos, 4 PDFs parados por tamaño). El fixer pide: «Commitea o descarta ese trabajo para que pueda arreglar los tests». Los grupos 8 y 11-15 comparten ficheros de criterios que siguen vivos.
- **Fuente:** `2026-10-08-fixes.md`; `2026-10-08-commit.md`.

**X-4 · Auditoría: ejecutor de tests, `instruments`, logs y snapshots.**
(a) Cambiar el ejecutor de tests de `tools/daily_audit.py` de pytest a `python3 <script>` (9 falsos fallos), que ya se hizo en parte; (b) qué hacer con `sqx.inspect.instruments` con `commissions` vacío en el master (OPEN #103); (c) purgar logs diarios de los workers (881 MB / 1,2 GB; 1,8 GB el 10-06) y 62 snapshots (7,02 GB); (d) escribir el manifest del export SPP_IS o retirarlo (resuelto el 10-06). Sin análisis estadístico nuevo que auditar en los informes del 10-05 a 10-08.
- **Fuente:** `2026-10-05-fixes.md`, `2026-10-06-fixes.md`, `2026-10-04.md`.

**X-5 · Tests cuyo comportamiento esperado cambió con el rediseño: ¿confirmas que no se perdió cobertura?**
`test_wfm_one` / `test_wfm_cell_selector` / `test_variants_pilot` cambian columnas y órdenes esperadas; `test_optimisation_calc`, `test_surfaces_lift`, `test_wfc_persistence`, `test_wfm_benchmark` y `test_cloud_underdetermined` se borran junto con sus módulos de medida; `test_autopilot_tail`, `test_ui_criteria` y `test_autopilot_variants_order` se reescriben. Lo único que lo explica es el rediseño de 17/18/18.5/19 y 16.5.
- **Fuente:** `git diff HEAD --stat -- tests`.

**X-6 · Claves muertas de `engines/variants/config.yaml`: ¿se borran?**
`min_trades` y `split_mode` ya no los lee ningún estudio pero se cargan en el fingerprint; siguen «until the owner says to delete them».
- **Fuente:** `engines/variants/config.yaml:1-8,21,47`.

**X-7 · Tests apartados (siete en `ASIDE`) y sus causas.**
`test_commission_segments`: el donante dice SizeBased 5.0 y las fichas PercentageBased 0.005; `test_mt5verify`; `test_strategymeta`: re-congelar el golden; `test_ui_research`, `test_ui_results` y `test_ui_strategy`: otra sesión en curso; falta además `test_ui_sqxconfig_studies`, que no aparece en la lista vigente.
- **Fuente:** OPEN #95; `2026-10-08-mechanical.md:199-209`.

### Trabajo pendiente que no necesita tu respuesta

- Auditoría del 10-08: 265 tests, 249 ok, 9 fallan y 7 apartados. Los tres nuevos son `test_batches`, `test_ui_blocks` y `test_feed_from_db`. Siguen sin diagnosticar `test_sqx_live` (`KeyError: 'strategies'` en `sqx/projects/live.py:235`) y `test_variants` (volcado de shapes/hash); `test_worker_lifecycle` puede ser un bug real de `bin/sqx-worker.sh stop` desde otro cwd (aunque la línea 386 ya hace `cd "$ROOT"`). Cinco de los siete del 10-07 fallan por datos que ya no están en disco (limpieza del 10-06, causa solo 🤔). Fuente: OPEN #107; `2026-10-08-fixes.md`; `OPEN.md:861-873`.
- Tests rojos de la ventana: `test_ui_criteria::test_state_write_stamp_freeze` (paso 11.5 nuevo); `test_ui_batch` (3) sin lote real; `test_ui_research` (2) por perfil de mercado; `test_ui_gate::test_window_client_sends_token` (404 en vez de 403); errores de `test_ui_tearmarket` y `test_ui_tearsheet` (8) por fixtures `http`/`app` inexistentes; `tests/test_oracle_draws.py:228` hace `sys.exit` a nivel de módulo y rompe `pytest tests/`; falta repetir `test_ui_shell` con el árbol quieto; `test_ui_criteria` y `test_ui_shell` fallan por `criteria-history.jsonl` con `dev.on`; `test_ui_results` (`studies/research/*` ausente del catálogo, anterior); `test_ui_workflow::test_project_knobs` falló por `run.symbol` (la nube ya no tiene `run.symbol`; quitarlo en `ui/daemon/runner/optimisation.py:13` y en `forproject.SET` es una petición a U). Fuente: enc. 46:415-449; enc. 48:13-16.
- Referencias muertas a `Test_Calib` en tests: `tests/test_progress_genetic.py:16`, `tests/test_portfolio_golden_current.py:18,33` (se salta si falta la cosecha), `tests/README.md:266`. Fuente: ver «Transversal».
- `checks.py` falla en capas por `engines → studies` (`drift_term`) y por el estado rojo causado por la sesión de Investigar. Fuente: enc. 48:15; enc. 41:254.

## Documentos que se contradicen

Para cada contradicción se indica lo que es verdad hoy en el árbol de trabajo y qué documento está desfasado.

- **Línea de PASA de R3 (1,65 o 2,33).** Verdad hoy: `pipeline/autopilot/criteria.yaml:85` carga `drift_excess_t ≥ 1,65` con Falla si falta el dato y sin Limbo. Desfasados: OPEN #91 (líneas 548-552: «limbo ≥ 1,65, pasa ≥ 2,33»), `criterios-implementados-2026-10-12` (EXP) y `criterios-implementados-2026-10-12` (C04), que además dicen «H1 nunca pasa», «17 reglas» y «R4b techo 75»; el documento correcto es la especificación de la puerta (ESP) y el encargo 44 (16 reglas, R4b retirada).
- **Muestra del sorteo `dev`.** Verdad hoy: `criteria.yaml:54` dice `sample: 3` (con `at: ["8"]`). OPEN #93 (línea 704: «5 survivors are then drawn at random») habla de 5: desfasado.
- **¿`oos2` está reservado para BlindJoint?** Verdad hoy: sí; `assets/_policy.yaml:48` lista `BlindJoint` en `reserved_for` (cambio sin commit, tú 2026-10-04). Desfasados: `studies/closing/blindJoint/README.md:47-50` («Step 20 is not listed… the SPA half is not read»), `WORKFLOW.md:50` («BlindJoint fuera de reserved_for») El README de blindJoint describe además el 18 como «PBO over 0.5» (hoy p95 del nulo) y el 17 con estados `no_fiable/indeciso/fiable`.
- **Criterio del paso 17.** Verdad hoy: `criteria.yaml:239-250` hace que el nivel decida con `p_nivel ≤ wfc.level_alpha (0,05)` (dueño, confirmado el 10-08, `thresholds.yaml:1368-1373`). Desfasada: la fila 17 de `WORKFLOW.md:46` («sin pedir significancia, `p_nivel` se anota y ya no decide»). `steps.md` coincide con el código.
- **Tipo de walk-forward de la WFM.** Verdad hoy: `assets/_build.yaml:483` dice `wf_type: exact_is_exact_oos` (lo que decidiste el 2026-09-24). Desfasada: P19:918-928, que decía que el yaml escribía `simulated_is_simulated_oos`.
- **Precisión de MCR/WFC.** `_build.yaml` pone `precision: 1` (timeframe elegido, tu «nada de retest a M1» del 2026-10-02) pero el comentario de MCR 2 (línea 249) sigue diciendo «un minuto — lento y fino»: el comentario es el desfasado.
- **Suelo de operaciones.** Tres cifras vivas: Build 10 (`_study.yaml`), puerta 35/20 (`criteria.yaml:79-81`), memoria 35 desde el 2026-10-02 y OPEN #93 «40-50». Los encargos 41/42 recogen las tres: ver P6-1. Y los comentarios de suelos de 16.5-18.5 dicen 50 en total mientras corren 100 en total y 50 por lado (P165-6).
- **Fila 6 de `WORKFLOW.md`.** Dice «PF ≥ 1,20, beneficio > 0» y cita `calib_final/ab_build.md` (borrado el 2026-10-04); hoy `_study.yaml:44-45` tiene PF 1,0 y la propuesta del 10-04 recomendaba solo ≥ 100 operaciones y beneficio > 0 dentro.
- **Fila 8 de `WORKFLOW.md`.** Dice «umbrales laxos de la puerta»; el código aplica las 16 reglas de las lecturas del encargo 44 (P.5 bis), que el dossier de 2026-10-04 no recoge («Suelo de 35 no como descarte» y «Pass solo con t ≥ 2,33 §5.2»).
- **README de `falsePositives`.** Dice que de los pasos 17-20 «no rule exists anywhere (owner's D3)»: falso; `criteria.yaml` tiene reglas para 17, 18, 18.5 y 19. Los pasos 10, 12 y 14 «no se aplican» al mono (no hay modelo).
- **Comentario del CSCV.** El comentario de `criteria.yaml` habla de «cortes 0,25 y 0,5» pero el 0,25 ya no existe; hay una tercera copia del 0,5 en `pipeline/config.yaml:54-62` (PROPOSED).
- **Estudios del paso 10.** README y `config.yaml` de `crossmarket` dicen que no emite veredicto, pero emite `verdict.csv`; el README lista un `POSSIBLE_IMPROVEMENTS.md` borrado.
- **Nube (16.5).** `WORKFLOW.md:66-70` dice que la nube corta en `oos2`; el manual dice que mira todo, incluido `oos2` (tú, 2026-09-28); el código solo corta con `ALGO_AUTONOMOUS=1`. El manual cap. 39 enseña B2 y rutas viejas; `WORKFLOW.md:45` dice `Retester` de serie pero usa bancos `WFC_*`.
- **18.5.** `README.md:52-55` («oos2 is never opened») es viejo; se pegan siempre «los 9 mercados» (real: 11) y la frase de costes provisionales aunque `costs_provisional` es false; README dice 9-11 s y 5.000 × 10 mercados, real ≈ 500 × 12.
- **SPP.** El glosario describe `area_de_meseta` como «cerca del mejor nivel»; en el código es la fracción de combinaciones con Ret/DD > 0 (`plateau.py:24`). El README cita «6 combinaciones comunes de 11.600» de otra estrategia (aquí 0).
- **Estado de las recomendaciones del encargo 41.** La recomendación de D2 del encargo 41 (Limbo ≥ 1,65, Pasa ≥ 2,33) quedó superada por el 44 (R3 ≥ 1,65 sin Limbo).
- **Dossieres de criterios 6-8 sin aviso.** `criterios-implementados-2026-10-12.md` y `criterios-implementados-2026-10-12.md` no llevan el aviso de que sus cifras no valen (enc. 42:139-142).
- **Paso 14.** El README del estudio dice que corre «tras ser aceptada», no es así; `mcRetest/README`, `criteria.yaml` y el glosario aplican tres umbrales distintos para lo mismo (1,0, 1,10, «<1»).
- **ESP/EXP/C04 sobre qué hay en disco del paso 8.** Es la misma contradicción que R3 arriba: el dossier C2 señalaba que «no se verificó cuál está en `criteria.yaml`»; verificado: el de la especificación (16 reglas, R3 en 1,65).

## Fuera del workflow de pruebas (cartera, fondeo, feed, infraestructura)

- Cortafuegos: `ufw` activo con tres reglas; ¿cerrar el puerto 22 público y dejar SSH solo por Tailscale? El 3389 (escritorio remoto) sigue abierto a todo; vía sin decidir para que SQX escuche solo en local (D7). (enc. 41:253-256)
- Encargo 45 (módulo de fondeo, entero sin ejecutar): D1 dónde vive (`portfolio/funded/` o `studies/`) y en qué paso se lee; D2 una cartera inviable ¿sale o queda marcada?; D3 qué cartera se evalúa; D4 contra qué cuentas; D5 relación con el simulador existente `portfolio/funded/sim/`. (enc. 45:143-152)
- Fondeo: veredicto 0,75 % / 0,4 % (viable ≥ 0,75 %, dudosa 0,4-0,75 %), probabilidad del día extremo (0,05/252), umbral de la cola, nivel del intervalo, longitud de bloque, repeticiones ≥ 5.000; Parte 5 (prueba del retraso con el feed de la firma: ¿módulo o lectura del paso 26?); cola del peor día `q_día` con Pareto (≈ 100 excedencias, ruidoso); vista en la ventana al estilo Quant Analyzer: se te enseña antes de construirla. (enc. 45:67-134,154)
- Cartera: C1 (archivar los supervivientes de USDJPY y XAUUSD, puerta de M0 y de la primera ejecución de F2), alcance del pool (30 madres o 182.220 supervivientes del paso 8 de `Test_Calib_*`, ya borrados), C6 rebalanceo, C7 «sin explicar, en prueba», `funded.open_risk_cap: null` (sin él la búsqueda de fondeo se niega a arrancar), `verdict.pass_percentile`, `stageb.t1_gap`, `wf.confidence`, `incubation.figure/history/band`, nueve entradas del banco de fondeo, F5; C4 provisional (una independiente entra con p = 0,75 por miembro; 24 % con cinco). (DP:20,28-39,68,94-120,165-175; COU:162-193)
- Cuatro hallazgos del motor de cartera sin decidir: qué versión archivada dimensiona a un miembro (usa la última, no la congelada del pool); saturación del rank del GA por encima de 1.000.000 combinaciones; qué finalista casi empatado es «la» cartera (sin semilla registrada); y cartera construida sin resultado real. (OPEN #104:851-858; WORKFLOW.md:250)
- Fondeo, firmas: F1 FundedNext (cuota por EAs, una cuenta por cartera, G3 y G4), F2 FundingPips (¿EA propio de SQX?), F3 FTMO (¿reembolso del 2-Step?), F4 Hantec (reembolso, «Profit Target −2 %», artículo de estrategias prohibidas, comisión del oro sin confirmar → el paso 26 rechaza Hantec en XAUUSD), F6 (`owner.eurusd`, `payout_cushion`, `tax_rate`, `payout_fee`, `p_payout_denied`, `p_firm_closes_year`, `gaps.*`); sin respuesta, FTMO sin reembolso sube el coste de 20 a 30 $ por 1.000 $; tres mensajes a soporte pendientes (FTMO, Hantec, FundingPips). (DP:127-181; COU:132-158,204-211)
- Darwinex/DarwinIA como meta real: ningún código lo implementa; abiertas: una o varias DARWIN, SILVER o GOLD, operaciones < 60 min, moneda y símbolos, `f`, fórmula SILVER, suelo de drawdown; releer la fuente antes de codificar. (K `research/darwinex-darwinia-published-rules.md:6-9`)
- Limitaciones de cartera: RAR de una combinación es la media de sus miembros (tiende a K = 1 con casi-clones); `p` del selector de la etapa B lee alto; T1 optimista con casi-clones; percentil 5 de la banda de incubación marca ~10 % de tramos sanos; EV bancario con suelo estático ≤ 0 en todos los planes a 504 días y > 0 en tres a 1.008; ni pool real ni `oos2` real leído; incubación no corre. (K `research/rank-score-rar-is-a-mean.md`, `stageb-selector-p-reads-high.md`, `t1-optimistic-on-near-clones.md`, `incubation-band-is-not-its-nominal-level.md`, `funded-bank-ev-read-against-the-monkey.md`)
- Equity de USDJPY: 0 de 3.732 reconstrucciones cuadran dentro de 1 $ (USA500: 97 %); el hueco coincide con la comisión de 5 $ por lote con posición abierta (inferencia de un caso; apunta a `portfolio/common/construct/equity/paths.py`); `Test_USDJPY_donchianUpperCrossUp_H1` no cuadra (10 de 60). (DP:18; COU:104-107,197-201)
- Recuento de ensayos independientes (`independent`) sobreestima con un cluster dominante (30+5+5 devuelve 14, silueta 0,147, en vez de k = 3; DSR sube de 0,85σ a 1,74σ); decidiste mantener la regla; abierto: imprimir la silueta junto al recuento. (OPEN #96:783-801)
- Brent: la sesión (109 huecos propios al año) y la plata (33) pasan del listón de 30; debes declarar la sesión del Brent; tres detalles de diseño abiertos en `studies/data/feedQuality/POSSIBLE_IMPROVEMENTS.md`; K y sesiones de NIKKEI225 (20), DAX40 (20), DJ30 (20), USA500 (25) las dejó el agente (10-04 y 10-06). (WORKFLOW.md:29,249,251; `thresholds.yaml` `feedQuality.K.*`)
- Literatura: 20 entradas esperan tu respuesta (`report`, bloques PREGUNTA, `--answer ID N`); 10 sin medida (sin parámetros, rejilla de 354 pares o condiciones que `rules.py` no tiene: Keltner, Hull, MACD, ADX); ¿debe el lector preguntar menos?; una clave API gratuita de OpenAlex levantaría su límite. (OPEN #100)
- Encargos sin empezar: 25 (estacionalidad), 26 (señal por plantilla), 28 (hueco aleatorio a prueba; depende de `/ab-hueco` por construir), 29 (meseta en el tiempo), 31 (mapa ventaja sobre el mono), 33 (economía del fondeo), 34 (validación MT5 pool; depende de OPEN #78), 35 (flota MT5), 38 (recuadro de la meseta), 39 (Edge por coste; necesita umbral de color), 40 (cerebro con probabilidades; necesita objetivo y corte de `p`), 16 (replay de operaciones, bloqueado), 13 (alfa-beta, aparcado), `5-nulos.md` (cinco pendientes en su §6). (README encargos:44-45,79,96-121,141-143)
- Infraestructura: logs diarios de workers (881 MB / 1,2 GB) y 62 snapshots (7,02 GB); OPEN #28, #29, #38b, #78, #81, #84, #85, #86, #87, #102 (tarjetas de knowhow en dominio equivocado), #103; encargo 41 §0.3, 0.5, 0.6. (OPEN)
- Cadena MT5: Hantec sigue fallando filas 1/3a/5 en la verificación del paso 26. (OPEN #89)

# Qué te pido que decidas, y qué cuesta cada cosa

De todo lo anterior, lo que desbloquea más con menos es esto, en este orden:

| orden | decisión | si dices que sí | lo que cuesta |
|---|---|---|---|
| 1 | Sellar `oos2` para los pasos 17, 18, 18.5 y 19 y cerrar el sello del 17 | Nada puede gastar el bloque ciego con criterios provisionales | Cero CPU. Los pasos 17-19 no leen un lote real hasta calibrarse |
| 2 | Apagar el sorteo `dev.on` en toda corrida que no sea una prueba de código | La población que llega al paso 10 deja de ser de 3 estrategias | Corridas más largas |
| 3 | Aceptar la prueba de viabilidad, con su regla escrita antes | En horas se sabe si merece la pena calibrar la cadena entera o acortarla | Horas de CPU; después, días (cadena entera) o una sola puerta medida (cadena corta) |
| 4 | Paso 8: tasa objetivo de un 1 % de monos como máximo, R3 en 2,33 y suelo de 35 mientras tanto | Código y documentos dicen lo mismo y el umbral lo pone la población, no una cifra borrada | Menos candidatas, en cantidad que hoy nadie sabe; puede que ninguna |
| 5 | Paso 10 como anotación y P7 fuera | El paso 10 deja de parar a todo el mundo | Los especialistas de un solo mercado siguen y gastan CPU después |
| 6 | Paso 20: dejar «peor» y decidirlo al final | No hay que rediseñarlo ahora | Los LIMBO se revisan a mano |

Con esas seis contestadas, el resto del catálogo se puede repartir en encargos sin volver a preguntarte por cada umbral. Lo que **no** resuelven y sigue siendo solo tuyo: las cifras del Build (P6-1 y P6-2), las lecturas K-1 a K-3 del paso 12, qué hacer con los tests que perdieron sus datos en la limpieza del 6 de octubre, y el árbol de trabajo sin commit, que hoy impide al agente que arregla los tests hacer su trabajo.

«Esto apenas importa» también es una respuesta válida para cualquiera de las 105.
