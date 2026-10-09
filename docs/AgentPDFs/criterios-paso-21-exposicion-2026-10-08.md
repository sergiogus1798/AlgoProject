# Paso 21 — Exposición contra el buy and hold: qué se calcula, con qué aritmética y qué criterio hay cargado

**Fecha:** 2026-10-08 · **Para:** el dueño, que va a fijar los criterios él mismo · **Alcance:** sólo el paso 21: `studies/closing/exposure/` entero, su capítulo del manual (`AlgoData/manual-fuentes/38-exposicion.md`) y lo que el autopiloto hace con él (`pipeline/autopilot/tail.py`, `closing.py`, `criteria.yaml`, `facts.py`).

Revisado por dos miembros del Council (Feynman, Taleb) el 2026-10-08; correcciones aplicadas. Lo que lleva «(calculado por el revisor)» lo calcularon ellos, no yo; el método y las salvedades van en cada sitio.

**Qué es:** el documento de consulta del paso 21, con la misma forma que el de los pasos 15-16 (`criterios-paso-16-spp-2026-10-07`). Explica desde cero qué es la exposición y cómo se cuenta, qué significa «comprar y mantener» cuando se compara con una estrategia, repasa **todos** los números que escribe el estudio con su `fichero:línea`, y dice qué no cuadra entre el código, su documentación y la doctrina.

**Commit descrito:** `b2b4c8c`. `studies/closing/exposure/` y `pipeline/autopilot/tail.py` **no tienen cambios sin confirmar**. Sí los tiene `pipeline/autopilot/facts.py` (y `README.md`, `blind.py`, `judge.py`, `plan.py`, `run.py`, `tailrun.py`, `variants.py` de esa carpeta, más tres ficheros nuevos sin seguir); lo que este documento cita de `facts.py` es el fichero tal como está en disco hoy. El capítulo del manual vive en AlgoData, fuera de git.

**De dónde salen los números.** Los ejemplos son de la corrida `Test_USA500_H1_indicesIBS` del 2026-10-06 (USA500, H1, largas, tres madres) y, como contraste, de `Test_USDJPY_M30_doubleROCLong` del mismo día (USDJPY, M30, largas). El código del estudio no ha cambiado desde el 2026-10-04, así que las dos están hechas con el código actual. Están **recalculados por mí** desde `AlgoData/raw/<proyecto>/CrossTF_Mothers/2026-10-06/trades.parquet` y las barras de la librería, con una aritmética escrita aparte (no llamando al estudio), y coinciden con las fichas guardadas al cuarto decimal. Para los recuentos uso además las 29 fichas guardadas de cuatro corridas (las dos anteriores, `Test_NIKKEI225_M30_simpleL_fin` del 10-05 y `Trade_NIKKEI225_M30_volatilidadL` del 10-04). Un aviso: el export de USDJPY del 10-06 hoy trae tres estrategias y las fichas de ese día son seis — el export se reescribió ese mismo día —, así que de USDJPY sólo he podido recalcular tres. Todo lo marcado «calculado por mí» está en `scratchpad/paso21/` (`tabla.py`, `recalc.py`, `residuo.py`).

**Ninguna línea de este documento está congelada.** El paso no tiene regla en `criteria.yaml`, a propósito, y el único umbral que existe (eficiencia ≥ 2) es, según su propio fichero, «una preferencia del dueño, pensada para moverse».

---

## 0. En una página

**La pregunta del paso.** Lo que la estrategia ganó, ¿cuánto tiempo de mercado costó, y es más o menos de lo que habría dado tener el activo comprado sin hacer nada?

**Lo que hay cargado hoy.** En el autopiloto, **ninguna regla**: `criteria.yaml` no tiene entrada «21» y su cabecera dice que 21, 23 y 24 «sólo anotan». El estudio sí tiene un veredicto propio, `worth_it` / `not_worth_it` («Aprobado» / «Suspenso» en la ventana): aprueba si la **eficiencia** es ≥ 2,0 y la estrategia es legible (≥ 30 operaciones, ≥ 250 días, gana dinero, y el buy and hold también gana). Ese veredicto no corta nada.

**Lo que sale en las corridas reales.** De las 29 fichas guardadas, 14 «Aprobado» y 15 «Suspenso». De los 15 suspensos, 12 son simplemente estrategias que pierden dinero en `oos1`; sólo 3 suspenden por eficiencia. De las 17 que ganan algo, aprueban 14. En USA500: dos aprueban (eficiencia 5,48 y 3,36) y una suspende (1,03).

**Las trece cosas que conviene saber antes de leer el resto:**

1. **La «eficiencia» es el cociente de Sharpes dividido por la ocupación, exactamente.** Con el buy and hold «a igual riesgo», *retorno de la estrategia ÷ retorno del buy and hold* es, por álgebra, *Sharpe de la estrategia ÷ Sharpe del activo* (apartado 2.5; comprobado en las seis recalculadas: 1,239 = 0,601 ÷ 0,485). Así que la regla «eficiencia ≥ 2» equivale a **Sharpe de la estrategia ≥ 2 × ocupación × Sharpe del activo**. Con un 20 % de ocupación basta el 40 % del Sharpe del activo; con un 5 %, el 10 %. En USA500 el listón real fue un Sharpe de entre 0,16 y 0,22; en NIKKEI225, entre 0,01 y 0,14.
2. **Por eso el veredicto aprueba casi todo lo que gana algo.** Una estrategia de NIKKEI225 con un retorno del 1,0 % en cuatro años y Sharpe 0,054 sacó eficiencia 1,99: se quedó a una centésima de aprobar. El propio README lo avisa (755 de 757 en la primera población) y lo atribuye a que la población ya venía filtrada por beneficio; la razón de fondo es la del punto 1.
3. **No hay ningún contraste: ni nulo, ni p-valor, ni intervalo.** El estudio lo dice («una estrategia con suerte y poca exposición sale igual de bien»). El contraste contra el buy and hold a igual riesgo existe, pero en el paso 20 (SPA y StepM sobre `oos2`), no aquí.
4. **Se lee sobre `oos1`, el tramo que ya eligió a las supervivientes.** La puerta del paso 8 selecciona mirando `oos1`; medir después sobre ese mismo tramo cuánto ganan frente al activo está sesgado a favor. En el dossier de las curvas del WFM el dueño contestó justo lo contrario para la misma pregunta: «sólo el `oos2`: un tramo que eligió no puede juzgar».
5. **La deriva del activo no se separa.** Las dos medidas que el estudio llama «antesala de la beta» (`captured`, `aligned`) no la aíslan, y el motivo «se parece a estar presente en los tramos buenos» no se ha disparado en ninguna de las 29 fichas (apartado 3.6). Calculado por mí sobre USA500, con la rejilla del estudio (H1; mi primera versión usó M30 y la conclusión no cambia): de los 21.485 USD brutos que la mejor madre ganó a cierres de barra, 7.027 son lo que habría dado tener sus mismos lotes medios todo el tiempo (deriva) y 14.458 son lo que queda por encima; frente a todas las rotaciones posibles de su calendario de posiciones queda en el percentil 85,2 — no en el 95 (cifras H1 calculadas por el revisor). Ese «por encima» mezcla elección del momento y tamaño de las posiciones (apartado 2.7).
6. **Con operaciones que se solapan, la ocupación puede salir disparatada.** La suma de lotes por barra deja residuos de coma flotante (10⁻¹⁷ lotes) y el código cuenta «lotes > 0» como estar dentro: dos operaciones solapadas de 0,1 y 0,2 lotes dan ocupación 100 % en vez de 50 % (apartado 5.1, reproducido con el código real). En las 29 fichas guardadas **no ha ocurrido** (ninguna estrategia solapa posiciones en su rejilla); ocurre en cuanto la rejilla es más gruesa que la estrategia, hay piramidación, o una operación abre en la barra donde otra cierra (según los tamaños: 1,1 y 0,3 lotes lo provocan, 0,3 y 0,1 no). Sólo puede suspender de más, nunca aprobar de más.
7. **La rejilla no es la del `config.yaml`.** El fichero dice M30; la ventana y el autopiloto la sustituyen por el timeframe del export (`ui/daemon/runner/readings.py:79-83`). La corrida de USA500 se contó en H1. A mano, sin `--set`, se cuenta en M30.
8. **El autopiloto corre una ficha por madre y no escribe `verdict.csv` ni la página de la población.** En `reports/Test_USA500_H1_indicesIBS/CrossTF_Mothers/2026-10-06/exposure/` sólo hay `estrategias/`. Los hechos sí existen (44 claves `exposure.*` por madre), listos para una regla que hoy no hay.
9. **El umbral 2,0 no está por encima del azar.** Una exposición colocada sin criterio no saca eficiencia 1,0 sino 1 ÷ √ocupación (2,1 al 22,6 %), y entre el 50 % y el 55 % de las rotaciones del calendario de cada madre dan eficiencia bruta ≥ 2 (calculado por el revisor, sin costes; apartado 5.12).
10. **El Sharpe del activo, que divide, tiene un error de ±0,5.** El veredicto de una misma estrategia sale «Aprobado» sólo el 70 %, el 54 % o el 37 % de las veces al remuestrear los días (calculado por el revisor; apartado 5.13).
11. **El buy and hold no paga swap, y en USA500 es más de la mitad de su retorno.** Una estimación gruesa lo mide, y con él 5.13.334 pasaría de Suspenso a Aprobado (apartado 5.7).
12. **Una corta ganadora sale siempre Suspenso**, porque el buy and hold es largo; el dossier lo tenía al revés (apartado 5.3, leído en el código, no ejecutado).
13. **Poca ocupación no es poco riesgo en fondeo.** Una aprobada de USDJPY (4.25.395, ocupación 15 %) llegó a perder en flotante el 11,25 % del saldo en una sola operación y un día (apartado 5.15).

---

## 1. Qué es el paso 21 y cómo decide

### 1.1 Dónde está

Fila 21 de `docs/AgentPDFs/WORKFLOW.md`, familia «Cierre», detrás del análisis conjunto (20) y delante del mapa condicional (22). Módulo `studies/closing/exposure/` (872 líneas en 12 ficheros). Manual: `docs/manual/10-cierre.pdf`, capítulo 38. No toca SQX: lee un export de operaciones y las barras de la librería.

El encargo es del dueño, 2026-09-24: *«Una estrategia que saque 5 %, pero solo se exponga al mercado 1 hora a la semana, me parecería mejor que sacar un 10 % con el buy and hold.»* Los pasos anteriores preguntan si la ventaja es real; éste pregunta qué forma tiene.

### 1.2 Qué lee

| entrada | de dónde | `fichero:línea` |
|---|---|---|
| las operaciones | el `trades.parquet` **más reciente** de `AlgoData/raw/<proyecto>/<databank>/<fecha>/`, cortado a `Sample type == OOS1` | `inputs.py:28-40`, `inputs.py:60-65` |
| la ventana | las fechas del tramo `oos1` en `assets/_policy.yaml` — **nunca** la primera y la última operación | `inputs.py:84-98` |
| las barras | el feed del activo, remuestreado al timeframe de la rejilla y cortado a la ventana; sólo existen barras con el mercado abierto | `inputs.py:68-81` |
| el valor del punto | la ficha del activo (`instrument.point_value`) | `inputs.py:101-110` |
| el saldo inicial | el `Balance` tras la primera operación menos su resultado | `compare.py:36-48` |

Tres detalles:

- **La ventana es la de la política.** Una estrategia que no operó en 2020 se mide sobre los cuatro años igualmente. Tomar la ventana de sus propias operaciones la haría parecer más ocupada de lo que es.
- **El databank lo da quien lanza.** `bin/workflow.sh:81` pasa siempre `--panel 21=CrossTF_Mothers`: las madres tal como salieron del paso 12, con sus operaciones de `oos1`. Sin ese argumento el autopiloto se para limpio en el 21 (`tail.py:147-149`), no elige por ti.
- **El saldo inicial fue 100.000 USD (a un céntimo) en las 29 fichas**, porque ese export arranca la cuenta en `oos1`. El comentario del código avisa de que en otros exports el `oos1` continúa la cuenta del IS y el saldo inicial no es el depósito.

### 1.3 Cómo lo lanza el autopiloto

`tail.walk` planifica el 21 como una acción `reading` (`tail.py:144-150`); `closing.reading` (`closing.py:19-25`) pide a la ventana el mismo comando que arrancaría su botón, **uno por madre** con `--strategy`, sobre las madres que quedan en el databank del último corte («SPP OOS», paso 16). Cada comando escribe la ficha de esa madre (`estrategias/<nombre>.json` y `.html`) y nada más: sin `--strategy` el comando escribiría además `verdict.csv` y la página de la población (`report.py:30-43`), pero el autopiloto nunca lo llama así.

El raíl da el paso por hecho en cuanto **una** madre tiene su ficha (`ui/daemon/workflow/derive.py:124-148`: `study` marca «hecho» en cuanto `sources.results` devuelve algo; `tail.py:67-68` lo repite en su docstring).

### 1.4 Cómo decide

No decide. `criteria.yaml:59`: «Steps 21, 23, 24 annotate only: no rule on purpose». `tail.walk` sólo añade un juicio a los pasos con reglas (`tail.py:81-84`, `tail.py:104`), y el 21 no las tiene. `survivors.CUTS` (`survivors.py:14`) ya incluye «21» para el día en que el dueño le dé reglas y un `cut`.

El veredicto propio del estudio (apartado 3.7) se guarda como hecho (`exposure.verdict.pass`, 1 ó 0) y se pinta en la ventana en verde o rojo; no mueve ninguna estrategia.

### 1.5 Las estrategias que nos acompañan

Las tres madres de USA500 (H1, largas, `oos1` = 2020-01-01 a 2024-01-01, saldo 100.000 USD):

| madre | operaciones | ocupación | horas/semana | retorno | Sharpe | eficiencia | veredicto |
|---|---|---|---|---|---|---|---|
| 1.13.354 | 129 | 22,6 % | 25,6 | 16,66 % | 0,601 | 5,48 | Aprobado |
| 18.15.392 | 123 | 20,9 % | 23,7 | 9,53 % | 0,340 | 3,36 | Aprobado |
| 5.13.334 | 95 | 16,4 % | 18,6 | 1,92 % | 0,082 | 1,03 | Suspenso |

Cómo operan (calculado por mí): duración mediana de 24 a 31 horas, mínima 3, máxima 115 (de lunes a viernes); ninguna dura menos de 30 minutos; nunca tienen dos posiciones a la vez; el tamaño va de 3,5 a 56,6 lotes (gestión monetaria por riesgo); el 44 % de las salidas son «End Of Friday», así que **ninguna** cruza un fin de semana, y el 85 % cruza al menos un cierre diario del índice. Con 129 operaciones en cuatro años son 32 al año: por debajo del suelo de 35 que el dueño fijó el 2026-10-02. El paso 21 no lo comprueba (su suelo es de 30 operaciones en toda la ventana).

---

## 2. Fundamentos de este paso

### 2.1 Qué es la exposición

**Exposición** (u ocupación) es la parte del tiempo en que la estrategia tiene alguna posición abierta. Una estrategia sin posición no puede perder: no le afecta un gap, una noticia ni una caída. Estar poco tiempo, sin embargo, no es estar poco expuesto cuando se está: la aprobada con mayor eficiencia de USDJPY (4.25.395, 6,17, ocupación 15 %) llegó a perder en flotante el 11,25 % del saldo en una sola operación y un solo día (2022-10-21; calculado por el revisor desde la columna `MAE ($)` del export). Ni la ocupación, ni la eficiencia, ni el drawdown de saldo del estudio ven esa cifra (apartado 5.15). Por dos estrategias que ganan lo mismo no son el mismo negocio si una está dentro el 5 % del tiempo y la otra el 100 %.

Hay que decidir tres cosas para medirla, y las tres cambian el número:

- **El denominador.** ¿Porcentaje de qué? El estudio usa **las barras que existen en la ventana**, es decir, las horas de mercado abierto. No cuenta las horas de reloj: un fin de semana no tiene barras.
- **La resolución.** El tiempo se cuenta en barras enteras. Una operación de cinco minutos ocupa la barra entera en que cae.
- **Qué pasa cuando hay dos posiciones a la vez.** Para «¿estaba dentro?» da igual una que dos; para «¿cuánto tenía comprometido?» se suman.

### 2.2 Un ejemplo de ocupación hecho a mano

Diez barras de una hora, de 08:00 a 17:00. Tres operaciones:

| operación | abre | cierra | lotes | barras que ocupa según el código | tiempo real |
|---|---|---|---|---|---|
| A | 09:20 | 11:00 | 1,0 | 09:00 y 10:00 | 1 h 40 min |
| B | 10:00 | 10:05 | 0,5 | 10:00 | 5 min |
| C | 14:10 | 14:20 | 1,0 | 14:00 | 10 min |

La regla (`occupancy.py:25-27`): la operación entra en la barra **que contiene** su hora de apertura (09:20 pertenece a la barra de las 09:00), y sale en la primera barra que **empieza** a la hora de cierre o después (11:00 → la barra de las 11:00 ya no cuenta). Si las dos caen en la misma barra, el código fuerza que ocupe al menos una: una operación nunca ocupa cero.

Lotes por barra: 0 · 1 · **1,5** · 0 · 0 · 0 · 1 · 0 · 0 · 0. En la barra de las 10:00 se suman A y B.

- **Ocupación** = barras con lotes > 0 ÷ barras = 3 ÷ 10 = **30 %**. El tiempo real con posición fue 1 h 50 min de 10 horas: el 18 %. La diferencia es el redondeo a barra entera, siempre hacia arriba.
- La barra de las 10:00 cuenta **una vez** para la ocupación aunque haya dos posiciones; cuenta 1,5 lotes para el capital comprometido.

Consecuencia práctica: cuanto más corta es la operación respecto de la barra, más se infla la ocupación. Con la rejilla en el timeframe de la estrategia y operaciones que abren y cierran en aperturas de barra (el caso de USA500), el recuento es exacto. Con operaciones de minutos sobre barras de media hora, cada una cuenta como media hora.

Lo midí sobre USA500 cambiando sólo la rejilla (calculado por mí, madre 1.13.354): M30 22,7 % · H1 22,6 % · H4 24,7 % · D1 31,2 %. La eficiencia es inversamente proporcional: con rejilla diaria bajaría de 5,48 a 3,98 sin que la estrategia cambie.

### 2.3 Horas por semana

`horas por semana = barras con posición × duración de la barra ÷ semanas de la ventana` (`occupancy.py:72-75`). La duración de la barra es la mediana de los saltos entre barras (la mediana, para que un fin de semana no la estire). Para 1.13.354: 5.332 barras de una hora ÷ 208,3 semanas = **25,6 horas por semana**.

Y «horas fuera» = 168 − horas dentro (`compare.py:76`) = 142,4. Atención a lo que mezcla: 168 son horas de reloj y las 25,6 son horas de mercado abierto. El índice abre unas 113 horas a la semana; de las 142 «fuera», unas 55 son mercado cerrado, y la estrategia puede tener la posición abierta durante ese cierre (apartado 5.4).

### 2.4 «Buy and hold» son tres frases distintas

Comprar el activo el primer día y no tocarlo: ¿cuántos lotes? De eso depende todo. El estudio calcula tres (`benchmark.py:19-70`):

| convención | lotes que mantiene | qué frase permite decir | USA500, madre 1.13.354 |
|---|---|---|---|
| `one_lot` | 1 | una vara absoluta | 1 lote → 1.509 USD (1,5 %) |
| `avg_size` | el tamaño medio de las operaciones de la estrategia | «el mismo dinero, dejado en vez de operado» | 20,47 lotes → 30.885 USD (30,9 %) |
| `equal_risk` | los que hacen que su resultado diario oscile lo mismo que el de la estrategia | «más o menos retorno por el mismo riesgo» | 8,91 lotes → 13.445 USD (13,4 %) |

La estrategia ganó 16.663 USD. «Gana once veces más que el buy and hold», «gana la mitad» y «gana un 24 % más» son las tres verdad. El veredicto lee la tercera.

El beneficio del buy and hold es simplemente `variación diaria del cierre × lotes × valor del punto` (`benchmark.py:109-122`): lotes fijos, sin reinvertir, **sin spread, sin comisión y sin swap**.

### 2.5 «A igual riesgo», desde cero, y por qué acaba siendo un cociente de Sharpes

**Desviación típica** de una serie de resultados diarios: cuánto se separa un día normal de la media. Se calcula restando la media a cada día, elevando al cuadrado, promediando (dividiendo por n − 1) y sacando la raíz.

Cinco días de juguete, valor del punto 1:

| día | el activo se mueve | la estrategia gana |
|---|---|---|
| 1 | +10 | 0 |
| 2 | −20 | 0 |
| 3 | +30 | +300 |
| 4 | −10 | 0 |
| 5 | +20 | −100 |
| suma | +30 | +200 |

- Activo: media 6; desvíos 4, −26, 24, −16, 14; cuadrados 16, 676, 576, 256, 196 = 1.720; ÷ 4 = 430; raíz = **20,74**.
- Estrategia: media 40; desvíos −40, −40, 260, −40, −140; cuadrados 1.600, 1.600, 67.600, 1.600, 19.600 = 92.000; ÷ 4 = 23.000; raíz = **151,66**. Los días sin operar entran como ceros, a propósito: así se le imputa el riesgo que corrió de verdad en la ventana, no el que corre sólo cuando opera.

Una salvedad con datos reales: en las madres de USA500 esa serie tiene resultado en el 9-12 % de los días y el resto son ceros; cinco días concentran el 38-44 % de su varianza y la curtosis es 47-73 (calculado por el revisor sobre la serie diaria). La desviación típica de una serie así describe mal lo que arriesga un día con posición: la de los días con resultado es 2,8 a 3,3 veces mayor (1.204 frente a 426 USD en 1.13.354). La anualización es correcta: hay 258,9 días con dato por año y se usa √252, el Sharpe sale 0,485 en vez de 0,492 y el factor se cancela en el cociente.

**Lotes a igual riesgo** = 151,66 ÷ (20,74 × 1) = **7,31** (`benchmark.py:67`). Con 7,31 lotes el activo oscila cada día lo mismo que la estrategia. Ese buy and hold gana 30 × 7,31 = **219,4**. La estrategia ganó 200: `return_ratio` = 200 ÷ 219,4 = **0,91**.

Ahora el **Sharpe** de cada uno (media ÷ desviación típica; la anualización √252 es la misma en los dos y se cancela): estrategia 40 ÷ 151,66 = 0,2637; activo 6 ÷ 20,74 = 0,2893. Cociente: **0,91**. El mismo número.

No es casualidad. Al escoger los lotes para igualar las desviaciones típicas, lo único que queda distinto entre las dos series es la media, y media ÷ desviación es el Sharpe. Siempre:

> **`return_ratio` = Sharpe de la estrategia ÷ Sharpe del activo en la ventana.**

Dos consecuencias. Una: el Sharpe del buy and hold a igual riesgo es el del activo, idéntico para todas las estrategias de la corrida (0,485 en las tres de USA500; 0,374 en USDJPY; 0,439 en NIKKEI225). Dos: todo lo que el estudio dice «frente al buy and hold» en retorno total se podía leer directamente comparando dos Sharpes.

El Sharpe del activo es una estimación sobre cuatro o cinco años, con un error típico de ±0,45-0,50: en USA500 0,485 con intervalo del 95 % de −0,44 a +1,48 y probabilidad del 15 % de ser ≤ 0; en USDJPY 0,374, de −0,49 a +1,29 y 20 % (calculado por el revisor, bootstrap estacionario de días con bloque medio de 10 y 4.000 tiradas, los mismos días para la estrategia y el activo). La eficiencia divide por él (apartado 5.13).

### 2.6 El beneficio por unidad de tiempo expuesto y la eficiencia

`rendimiento por hora expuesta = retorno ÷ ocupación` (`compare.py:71`). En el juguete, si la estrategia estuvo dentro el 20 % de las barras y ganó un 2 %, sale un 10 %: «lo que rendiría si estuviera dentro siempre al ritmo al que rinde cuando está». **Es una extrapolación**: nadie puede cobrarla, porque una estrategia que espera una señal no encuentra cinco veces más señales. Mide la calidad del tiempo gastado.

`eficiencia = rendimiento por hora expuesta ÷ retorno del buy and hold a igual riesgo` (`compare.py:73`). El buy and hold está dentro el 100 % del tiempo, así que su «por hora expuesta» es su retorno. En el juguete: (0,91 del retorno del activo) ÷ 0,20 = **4,56**. Aprobaría con holgura **ganando menos que el activo a igual riesgo**. Ésa es exactamente la preferencia del encargo: menos retorno, mucho menos tiempo.

Juntando 2.5 y 2.6:

> **eficiencia = (Sharpe de la estrategia ÷ Sharpe del activo) ÷ ocupación**

y el umbral 2,0 se puede escribir como un Sharpe mínimo que depende de la ocupación:

| ocupación | Sharpe mínimo para aprobar, como parte del Sharpe del activo | con el Sharpe de USA500 en `oos1` (0,485) |
|---|---|---|
| 50 % | el 100 % | 0,485 |
| 22,6 % (1.13.354) | el 45 % | 0,219 |
| 10 % | el 20 % | 0,097 |
| 5 % | el 10 % | 0,049 |
| 1,3 % (la menos ocupada de las 29) | el 2,6 % | 0,013 |

Es aritmética, no una medición. Dice que la regla premia estar poco tiempo de forma lineal y sin suelo: una estrategia que casi no opera aprueba con casi cualquier ganancia positiva.

Y el 2,0 no está por encima de lo que saca una exposición colocada al azar: un calendario con la misma ocupación, puesto en cualquier otro sitio del tramo, tiene eficiencia bruta mediana 2,0-2,7 en las seis estrategias recalculadas, y entre el 50 % y el 55 % de esas colocaciones da 2 o más (calculado por el revisor, sin costes). El valor de referencia de quien no elige el momento no es 1,0 sino 1 ÷ √ocupación: 2,1 al 22,6 % de ocupación, 4,5 al 5 %, 8,8 al 1,3 %. El comentario de `config.yaml` («1,0 significa tan productivo por hora como tener el activo») no describe eso (apartado 5.12).

### 2.7 Qué parte de lo ganado es deriva del activo

Una estrategia que sólo compra, en un activo que sube, gana aunque entre al azar. Esa parte se llama **deriva**. Separarla es contestar: ¿cuánto habría ganado alguien con la misma cantidad de exposición, colocada sin criterio?

La forma más simple, sin estadística: **lotes medios × lo que subió el activo**. Si la estrategia tuvo de media 4,59 lotes (contando como cero las barras fuera) y el índice subió 1.531 puntos, tener 4,59 lotes todo el tiempo habría dado 4,59 × 1.531 = 7.027 USD (rejilla H1). Eso es lo que su exposición «valía» sin elegir el momento. Lo que gane por encima es, en una primera lectura, **elección del momento**; lo que gane por debajo, mala elección. Es una simplificación: ese «por encima» mezcla cuándo se está dentro y cuántos lotes se llevan en cada momento (véase la salvedad bajo la tabla).

El estudio **no hace este cálculo**. Lo que tiene en su lugar son dos proporciones (apartado 3.6) que no llegan a separar nada. La regresión de alfa y beta — el método habitual — está aparcada por decisión del dueño del 2026-09-24.

Calculado por mí sobre las seis estrategias que pude recalcular (bruto a cierres de barra, sin costes; `recalc.py`). Corrección de la revisión: mi script contó las barras de la rejilla M30, y el estudio corrió con la rejilla H1 del export; las tres filas de USA500 van ahora en H1 (cifras del revisor, que rehízo el cálculo con el código real), las de USDJPY en M30, que sí es su rejilla. La conclusión no cambia:

| madre | neto real | bruto a cierres | deriva (lotes medios × subida) | momento (bruto − deriva) | veredicto del estudio |
|---|---|---|---|---|---|
| USA500 1.13.354 | 16.663 | 21.485 | 7.027 | +14.458 | Aprobado |
| USA500 18.15.392 | 9.530 | 14.348 | 6.766 | +7.582 | Aprobado |
| USA500 5.13.334 | 1.923 | 5.440 | 4.852 | +588 | Suspenso |
| USDJPY 10.23.380 | −24.603 | 202 | 7.889 | −7.687 | Suspenso |
| USDJPY 3.13.366 | 294 | 19.637 | 8.104 | +11.533 | Suspenso |
| USDJPY 4.25.395 | 16.261 | 26.831 | 8.327 | +18.504 | Aprobado |

Cómo leerla: la 5.13.334 ganó en bruto casi lo que valía su exposición (5.440 frente a 4.852), y los costes se comen el resto. No es, sin embargo, «deriva pura»: su bruto coincide con el valor de su exposición, pero no porque no haga nada. A tamaño constante, la elección del momento suma unos +5.800 USD y el tamaño de las posiciones resta unos −5.200 (calculado por el revisor, rejilla H1, USD). El reparto deriva/momento cambia con la rejilla (bruto de 1.13.354: 20.932 en M30, 21.485 en H1, con las mismas operaciones) y con el periodo sobre el que se promedia la deriva; para la 5.13.334 el «momento» pasa de positivo a −1.219 si la deriva se calcula año a año. La diferencia entre «bruto a cierres» y «neto real» son los costes y la diferencia entre el precio de ejecución y el cierre de la barra; en USDJPY son enormes (unos 24.800 USD en 402 operaciones) porque los costes están cargados al peor caso.

Para las otras dos de USA500 (revisor, H1): 1.13.354 separa +20.931 de momento a tamaño constante y −6.473 de tamaño; 18.15.392, +5.379 y +2.203; con la deriva calculada año a año, su «momento» queda en +12.619 y +6.788.

Supuestos: el bruto empareja los lotes de cada barra con el cambio de cierre a cierre de esa barra, así que el hueco entre el cierre anterior y la apertura se le imputa a quien entra en la apertura.

### 2.8 Con qué nulo, si lo hubiera

Un **nulo** es una población de estrategias falsas, sin ventaja por construcción, con la que comparar la real. Si la real no destaca de ellas, lo que ganó es lo que gana cualquiera con sus mismas características.

**En el paso 21 no hay ninguno.** Para la pregunta «¿es deriva o es elección del momento?», el nulo natural es conservar *todo* lo que la estrategia hace con su exposición — cuántos lotes, cuánto dura cada posición, cuánto espera entre una y otra — y cambiar sólo *cuándo*. La forma más barata es la **rotación**: coger el calendario de posiciones y desplazarlo entero k barras (lo que se sale por el final entra por el principio), para todos los k posibles. Cada rotación es un «trader» con exactamente la misma ocupación, los mismos tamaños y las mismas duraciones, colocado en otro sitio del tramo. La media de todas las rotaciones es, exactamente, la deriva del apartado 2.7.

Ejemplo de juguete: cinco barras con movimientos +1, +3, −2, +4, −1 y una posición de 1 lote en las barras 2 y 4. La real gana 3 + 4 = 7. Las cinco rotaciones ganan 7 (0 barras), −3 (una: barras 3 y 5), 5, −1 y 2. Media 2 = lotes medios (2/5) × subida total (5). La real es la mejor de cinco: percentil 80.

Calculado por mí, con **todas** las rotaciones de la rejilla (23.596 en USA500 H1, la rejilla del estudio — mi primera versión contó 46.168 en M30 — y 62.361 en USDJPY M30; no hay sorteo, son todas), sobre `oos1`, en bruto y sin costes en los dos lados:

| madre | bruto real | media de las rotaciones | percentil 95 de las rotaciones | rotaciones que ganan menos que la real | veredicto del estudio |
|---|---|---|---|---|---|
| USA500 1.13.354 | 21.485 | 7.027 | 29.298 | 85,2 % | Aprobado (5,48) |
| USA500 18.15.392 | 14.348 | 6.766 | 29.571 | 70,5 % | Aprobado (3,36) |
| USA500 5.13.334 | 5.440 | 4.852 | 23.030 | 49,0 % | Suspenso (1,03) |
| USDJPY 10.23.380 | 202 | 7.889 | 53.500 | 38,7 % | Suspenso |
| USDJPY 3.13.366 | 19.637 | 8.104 | 52.632 | 66,4 % | Suspenso (0,15) |
| USDJPY 4.25.395 | 26.831 | 8.327 | 48.351 | 77,2 % | Aprobado (6,17) |

Lo que enseña, y lo que no:

- Ninguna de las tres «Aprobado» supera al 95 % de sus propias rotaciones. La mejor queda en el 85,2 %.
- El orden sí coincide con el del estudio: las aprobadas son las tres más altas.
- Y eso con el sesgo a favor: las tres fueron elegidas por ganar en este mismo tramo. La mejor queda a una desviación típica de la media de sus rotaciones (1,00; las otras dos, 0,51 y 0,05; la desviación de las rotaciones es de 14.465 USD). Con cuatro años, este contraste sólo distingue del azar un Sharpe bruto cercano a 1: hacía falta un bruto de unos 29.300 USD, 4,2 veces la deriva, y las tres tienen 0,60 · 0,34 · 0,08 neto. Lo que se puede afirmar es que en `oos1` ninguna aprobada se separa de su propia exposición colocada en otro momento, no que no tengan ventaja (todo calculado por el revisor, sin costes).
- Las rotaciones vecinas dejan de parecerse a unas 60-120 barras, así que hay unas 260-460 independientes en USA500, no decenas de miles; bastan para situar un percentil 84 (revisor).
- **No es un resultado del estudio ni un criterio.** Es una ilustración de qué nulo cabría aquí. Tiene límites serios: las rotaciones vecinas son casi la misma estrategia, así que 23.596 rotaciones no son 23.596 pruebas; al rotar, una posición puede quedar partida entre el final y el principio de la ventana; y la doctrina del dueño ya tiene un trader al azar con la misma huella (`core/significance.footprint`, paso 8), que es el que habría que usar si se quisiera un nulo aquí, no uno nuevo.
- Se hace sobre `oos1`, que cumple «el azar sólo fuera de muestra», pero arrastra el problema del apartado 2.9.

### 2.9 Sobre qué tramo se lee

`config.yaml:8-9`: muestra `OOS1`, tramo `oos1`. En USA500, 2020-2023.

`oos1` es fuera de muestra respecto de la construcción (`build`), pero **no respecto de la selección**: la puerta del paso 8 decide quién sigue mirando precisamente `oos1`. Una estrategia que llega al 21 ha sido elegida, entre otras cosas, por ganar ahí. Medir luego sobre ese tramo cuánto gana frente al activo devuelve un número inflado: es como preguntar a los que aprobaron el examen qué nota sacaron.

Esto no invalida la **ocupación** ni las **horas por semana**: son una descripción de cómo opera la estrategia, no una ganancia, y la selección no las infla de forma evidente. Sí afecta a todo lo que lleva el retorno en el numerador: `return_ratio`, `eficiencia`, `dd_ratio`.

El tramo limpio es `oos2`, y es donde el paso 20 hace su comparación contra el buy and hold. El estudio admite el cambio con `--set study.sample=… study.segment=oos2`, pero el export `CrossTF_Mothers` de estas corridas sólo trae `OOS1`, y `oos2` está reservado: este documento no ha calculado nada sobre él.

### 2.10 En qué se solapa con el dossier de las curvas del WFM y con el paso 20

`docs/AgentPDFs/curvas-wfm-2026-10-01.md` hizo la misma pregunta («¿ganan algo que no gane ya el activo?») sobre cinco madres de XAUUSD y llegó a una pestaña del WFM, «Contra el activo y el azar». Las tres piezas, lado a lado:

| | paso 21 (este) | dossier de las curvas (2026-10-01) | paso 20 (`blindJoint`) |
|---|---|---|---|
| tramo | `oos1` | `oos2` | `oos2` |
| serie diaria de la estrategia | resultado en el día de **cierre** de la operación | marcada al **cierre diario** | diaria, del lote de variantes |
| tamaño del buy and hold | a igual riesgo (`benchmark.py:67`) | a igual riesgo | a igual riesgo, la misma fórmula (`blindJoint/benchmark.py:25`) |
| qué compara | retorno total y retorno por tiempo expuesto | Sharpe contra Sharpe, con intervalo de la diferencia; alfa tras quitar la beta diaria | exceso diario medio, con SPA y StepM |
| nulo / contraste | ninguno | 10.000 traders al azar con la misma huella | bootstrap del SPA |
| lo que sólo tiene él | **la ocupación** y todo lo que cuelga de ella | la beta quitada | la corrección por haber buscado entre muchas |

Lo que se repite: la comparación «a igual riesgo» (que, por 2.5, es Sharpe contra Sharpe) está en los tres sitios. Lo que el 21 aporta y nadie más tiene es dividir por la ocupación. Lo que el dossier tenía y el 21 no: tramo limpio, marcado a mercado, intervalo y un nulo.

Dos notas. El dossier ya avisaba de que con el resultado puesto en el día de cierre «la beta real es mayor que la medida»; lo he medido en el apartado 5.6. Y no he encontrado la pestaña «Contra el activo y el azar» en el código actual de `studies/optimisation/wfm/`: el commit que la añadió es `7b6f746`, pero la frase ya no aparece en `studies/` ni en `ui/`. No he seguido su historia.

---

## 3. Lo que calcula el estudio, pieza a pieza

Cada ficha guarda un `summary` de 44 entradas (42 números, el veredicto y sus motivos); el autopiloto recoge los 42 números como hechos `exposure.summary.<nombre>` y añade `exposure.verdict.pass` y `exposure.verdict.score` (`facts.gather`, `facts.py:195-223`). El ejemplo real es siempre la madre **1.13.354 de USA500**.

### 3.1 Datos de partida

| hecho | regla | `fichero:línea` | 1.13.354 |
|---|---|---|---|
| `n` | operaciones de la muestra | `one.py:75` | 129 |
| `days` | días entre el primer y el último cambio diario de cierre | `one.py:71` | 1.456 |
| `equity_start` | saldo tras la primera operación − su resultado | `compare.py:47-48` | 100.000 |

### 3.2 Ocupación: `exp_*`

| hecho | fórmula | `fichero:línea` | 1.13.354 |
|---|---|---|---|
| `exp_share` | barras con lotes brutos > 0 ÷ barras de la ventana | `occupancy.py:70,73` | 0,2260 (5.332 de 23.596 barras H1) |
| `exp_hours_per_week` | barras dentro × minutos de barra ÷ 60 ÷ semanas | `occupancy.py:72-75` | 25,60 |
| `exp_avg_notional_pct` | media sobre **todas** las barras de lotes × cierre × valor del punto, ÷ saldo | `occupancy.py:71,76` | 18,6 % |
| `exp_notional_when_in_pct` | lo mismo, sólo en las barras con posición | `occupancy.py:77` | 82,3 % |
| `exp_tilt` | lotes con signo ÷ lotes brutos: +1 siempre larga, −1 siempre corta | `occupancy.py:78` | 1,0 |
| `hours_off` | 168 − `exp_hours_per_week` | `compare.py:76` | 142,4 |

Los lotes por barra salen de `occupancy.held` (`occupancy.py:9-36`): cada operación suma su tamaño en la barra de entrada y lo resta en la de salida, y se acumula. Las posiciones que se solapan **se suman**. `gross` ignora la dirección; `signed` pone las cortas en negativo. El 82 % de «cuenta comprometida mientras opera» dice que con 20 lotes de un índice a unos 4.000 puntos la posición vale el 82 % del saldo; en USDJPY sale un 400 % (apalancamiento 4), y es lo que explica sus drawdowns del 25-30 %.

`exp_tilt` vale 1,0 en las 29 fichas: una dirección por plantilla.

### 3.3 La serie diaria de la estrategia y sus estadísticos: `strat_*`

La serie (`benchmark.daily`, `benchmark.py:86-106`): el resultado de cada operación va al **día en que cerró**; los días sin cierres valen cero; lo cerrado en un día sin dato del activo pasa al siguiente, para que la suma sea siempre el beneficio total.

| hecho | fórmula (`compare.stats`, `compare.py:26-33`) | 1.13.354 |
|---|---|---|
| `strat_net` | suma de la serie | 16.662,90 USD |
| `strat_return_pct` | neto ÷ saldo inicial | 16,66 % |
| `strat_cagr_pct` | (saldo final ÷ inicial)^(1/años) − 1, años = días ÷ 365,25 | 3,94 % |
| `strat_maxdd_pct` | mayor caída desde el máximo previo del saldo, sobre la serie diaria **de cierres de operación** | 5,45 % |
| `strat_vol` | desviación típica diaria (n − 1), en USD | 426,47 |
| `strat_sharpe` | media ÷ desviación × √252, contra cero | 0,601 |

Dos cosas que el nombre no dice. El retorno en % depende del tamaño de las posiciones que eligió la gestión monetaria: el doble de lotes, el doble de retorno. Y el drawdown es de **saldo**, no de flotante: no ve lo que la posición perdió mientras estaba abierta (el export trae la columna `MAE ($)`; el estudio no la usa). La peor operación, que es la misma en las tres madres de USA500 (2020-02-25 a 02-28, 16,22 lotes), llegó a ir perdiendo 6.285 USD, el 6,3 % del saldo, más que todo el drawdown «oficial» de 1.13.354 (calculado por el revisor desde `MAE ($)`).

### 3.4 Los tres buy and hold: `lots_*` y `bench_<convención>_*`

Para cada convención (apartado 2.4), los lotes y los mismos seis estadísticos del 3.3 aplicados a `variación diaria del cierre × lotes × valor del punto`:

| | lotes | neto | retorno | CAGR | drawdown | Sharpe |
|---|---|---|---|---|---|---|
| la estrategia | – | 16.663 | 16,66 % | 3,94 % | 5,45 % | 0,601 |
| `one_lot` | 1,00 | 1.509 | 1,51 % | 0,38 % | 1,20 % | 0,485 |
| `avg_size` | 20,47 | 30.885 | 30,89 % | 6,99 % | 22,98 % | 0,485 |
| `equal_risk` | 8,91 | 13.445 | 13,45 % | 3,22 % | 10,15 % | 0,485 |

Comprobación a mano del tercero: desviación diaria de un lote 47,857 USD → 426,47 ÷ 47,857 = 8,911 lotes; 1.508,73 × 8,911 = 13.445 USD. El Sharpe es el mismo en las tres filas del activo, como tiene que ser: multiplicar los lotes no cambia el Sharpe.

El drawdown del buy and hold **sí** es marcado a mercado día a día (es una posición que nunca se cierra); el de la estrategia no (3.3). `dd_ratio` compara uno con otro.

### 3.5 La dicotomía: `return_per_exposure_pct`, `efficiency`, `return_ratio`, `dd_ratio`

`compare.dichotomy`, `compare.py:71-76`, siempre contra la convención de cabecera (`equal_risk`, `config.yaml:17`):

| hecho | fórmula | 1.13.354 | 18.15.392 | 5.13.334 |
|---|---|---|---|---|
| `return_per_exposure_pct` | retorno ÷ ocupación | 16,66 ÷ 0,2260 = 73,7 % | 45,6 % | 11,7 % |
| `efficiency` | lo anterior ÷ retorno del buy and hold | 73,7 ÷ 13,45 = **5,48** | **3,36** | **1,03** |
| `return_ratio` | retorno ÷ retorno del buy and hold | 1,239 | 0,702 | 0,169 |
| `dd_ratio` | drawdown ÷ drawdown del buy and hold | 0,536 | 0,917 | 1,180 |

Por el apartado 2.5: 1,239 = 0,601 ÷ 0,485; 0,702 = 0,340 ÷ 0,485; 0,169 = 0,082 ÷ 0,485. La 18.15.392 gana a igual riesgo el 70 % de lo que gana el índice y aprueba con 3,36, porque está dentro la quinta parte del tiempo: es el caso que el encargo quería premiar. Si esa preferencia vale también con un Sharpe de 0,34 es justo la decisión que no está tomada.

Si el buy and hold pierde en la ventana, `efficiency` y `return_ratio` cambian de signo y dejan de significar nada; el veredicto lo trata aparte (3.7). Eso cubre el denominador negativo o nulo (`verdict.py:46`); no cubre el positivo y pequeño, donde `compare.py:73` divide y la eficiencia crece sin límite (apartado 5.13).

### 3.6 Dónde estaba cuando el mercado se movió: `captured`, `aligned`

`occupancy.presence`, `occupancy.py:81-97`, con el cambio de cierre de cada barra respecto de la anterior (`one.py:60-62`):

- `captured` = suma de |movimiento| en las barras con posición ÷ suma de |movimiento| en todas. Qué parte del «ruido total» del mercado ocurrió con la estrategia dentro.
- `aligned` = suma del movimiento **con el signo de la posición** en las barras dentro ÷ suma de |movimiento| en todas. Para una larga: lo que el precio subió neto mientras estaba dentro, como parte de todo lo que el precio se movió arriba y abajo.

Juguete: movimientos +1, +3, −2, +4, −1; larga en las barras 2 y 4. Total absoluto 11. `captured` = (3 + 4) ÷ 11 = 0,64, con una ocupación de 2 ÷ 5 = 0,40: estuvo en barras más movidas que la media. `aligned` = (3 + 4) ÷ 11 = 0,64.

En los datos reales: `captured` 0,279 con ocupación 0,226 en 1.13.354; `aligned` 0,0095. En las 29 fichas `aligned` va de −0,0003 a 0,0095.

Por qué `aligned` es siempre minúsculo: el denominador es la suma de **todos** los vaivenes de 23.596 barras, que es enorme comparada con cualquier ganancia neta. No tiene escala propia; su único uso real en el código es el signo.

El motivo «timing» del veredicto (`verdict.py:54-57`) se escribe cuando `captured` > 2 × ocupación **y** `aligned` ≤ 0: mucho movimiento capturado y nada a favor. **No se ha escrito en ninguna de las 29 fichas**: `captured` nunca pasa de 1,6 veces la ocupación (la más alta: 0,020 con ocupación 0,013). Y además es sólo un texto: no cambia el veredicto.

Lo que el manual dice de estas dos cifras — «un número alto aquí significaría que lo que hace es acertar cuándo estar dentro, que es beta con horario» — no se sostiene con la definición: `aligned` alto es simplemente haber ganado en bruto, venga de la deriva o no. Ninguna de las dos resta lo que el activo subió.

### 3.7 El veredicto: `verdict`, `reasons`

`verdict.judge`, `verdict.py:38-59`. Primero cuatro comprobaciones de «ilegible»:

| motivo | condición | línea |
|---|---|---|
| pocas operaciones | `n` < `gate.min_trades` (30) | `verdict.py:40` |
| ventana corta | `days` < `gate.min_days` (250) | `verdict.py:42` |
| pierde | neto de la estrategia ≤ 0 | `verdict.py:44` |
| el buy and hold pierde | retorno del buy and hold ≤ 0 | `verdict.py:46` |

Después, `efficiency` ≥ `gate.min_efficiency` (2,0) (`verdict.py:50`). **`worth_it` sólo si aprueba la eficiencia y no hay ningún motivo de ilegible** (`verdict.py:58`). Cualquier otra cosa es `not_worth_it`. No hay tercer estado.

En la ventana: `worth_it` → «Aprobado», verde; `not_worth_it` → «Suspenso», rojo (`one.py:16`, `one.py:104-105`). `exposure.verdict.score` es la eficiencia; `exposure.verdict.pass`, 1 ó 0.

Sobre las 29 fichas:

| resultado | cuántas | quiénes |
|---|---|---|
| Aprobado | 14 | 2 de USA500, 2 de USDJPY, las 10 de `Trade_NIKKEI225` |
| Suspenso por «pierde» (y eficiencia negativa) | 12 | 3 de USDJPY, 9 de `Test_NIKKEI225…_fin` |
| Suspenso sólo por eficiencia | 3 | 5.13.334 (1,03), USDJPY 3.13.366 (0,15), NIKKEI225 19.16.284 (1,99) |
| pocas operaciones, ventana corta, el activo pierde, «timing» | 0 | – |

Nota (calculado por el revisor): USDJPY 4.25.395 gana 31.673 USD en 2022 y pierde 15.411 en los otros cuatro años juntos (neto por año natural 2018-2022: +1.020 · −13.937 · −723 · −1.771 · +31.673); su eficiencia 6,17 es la de ese año.

### 3.8 Lo que se escribe en disco

En `AlgoData/reports/<proyecto>/<databank>/<día>/exposure/` (`report.py:27`):

| fichero | cuándo | qué |
|---|---|---|
| `estrategias/<nombre>.json` y `.html` | siempre | la ficha: veredicto, tres tablas («La dicotomía», «La estrategia y el buy & hold», «Dónde estaba…»), glosario y el `summary` |
| `verdict.csv` | sólo sin `--strategy` | 14 columnas (`many.py:18-20`): estrategia, identidad, veredicto, n, ocupación, horas, retorno, por hora expuesta, eficiencia, `return_ratio`, `dd_ratio`, `captured`, `aligned`, motivos |
| `exposure.html` / `.md` / `.json`, `manifest.json` | sólo sin `--strategy` | la población |

El autopiloto sólo produce la primera fila.

---

## 4. El criterio cargado y por qué

### 4.1 Tal como está hoy

- **`pipeline/autopilot/criteria.yaml`:** no hay clave «21». Las claves de paso que existen son 8, 10, 11.5, 12, 14, 16, 16.5, 17, 18, 18.5 y 19. Línea 59: «PROVISIONAL (Council 2026-10-04): do not freeze before a null population has run the chain. Steps 21, 23, 24 annotate only: no rule on purpose».
- **`ledger/thresholds.yaml`:** ninguna fila de `exposure`.
- **`studies/closing/exposure/config.yaml`:** los tres umbrales del veredicto propio — `min_efficiency: 2.0`, `min_trades: 30`, `min_days: 250` — y la convención de cabecera `equal_risk`.

De dónde sale el 2,0, según el comentario del fichero: «1,0 significa tan productivo por hora como tener el activo; el dueño quiere que sea claramente mejor por hora expuesta». No hay calibración detrás, ni se presenta como tal. Tampoco describe lo que dice: «1,0» no es el valor de quien no elige el momento, que es 1 ÷ √ocupación (apartado 5.12).

### 4.2 Los hechos disponibles para una regla

`python3 -m pipeline.autopilot.facts --project Test_USA500_H1_indicesIBS --step 21` devuelve 44 claves por madre. Las que podrían sostener una regla, con lo que valen en USA500 (mínimo · mediana · máximo de las tres):

| hecho | valores | qué es |
|---|---|---|
| `exposure.summary.exp_share` | 0,164 · 0,209 · 0,226 | ocupación |
| `exposure.summary.exp_hours_per_week` | 18,6 · 23,7 · 25,6 | horas de mercado dentro, por semana |
| `exposure.summary.return_ratio` | 0,169 · 0,702 · 1,239 | Sharpe de la estrategia ÷ Sharpe del activo |
| `exposure.summary.efficiency` | 1,03 · 3,36 · 5,48 | lo anterior ÷ ocupación |
| `exposure.summary.dd_ratio` | 0,536 · 0,917 · 1,180 | drawdown de saldo ÷ drawdown del activo a igual riesgo |
| `exposure.summary.strat_sharpe` | 0,082 · 0,340 · 0,601 | Sharpe en `oos1` |
| `exposure.verdict.pass` | 0 · 1 · 1 | el veredicto propio |

### 4.3 Qué cortaría cada lectura, sobre las 29 fichas

Sólo lo que ya se puede contar con los umbrales que existen o con cortes que no elijo yo (1 = «igual que el activo»):

| lectura | pasan | caen |
|---|---|---|
| ninguna regla (hoy) | 29 | 0 |
| el veredicto propio (`efficiency` ≥ 2 y legible) | 14 | 15 |
| sólo «gana en `oos1`» | 17 | 12 |
| `return_ratio` ≥ 1 (Sharpe ≥ el del activo, sin premiar la ocupación) | 6 | 23 |

Es decir: el veredicto propio añade **3 bajas** a las 12 que ya da «pierde dinero», y exigir batir al activo a igual riesgo sin dividir por la ocupación dejaría 6 (una de USA500, una de USDJPY y cuatro de `Trade_NIKKEI225`). Entre una y otra está toda la decisión del dueño: cuánto vale estar poco tiempo.

Estas 29 no son una población: son cuatro corridas de prueba, tres activos, y diez de ellas (`…simpleL_fin`) pierden casi todas en `oos1`.

### 4.4 Si mueves el umbral

Por el apartado 2.6, subir `min_efficiency` de 2 a X es pedir un Sharpe de X × ocupación × Sharpe del activo. A la ocupación de USA500 (≈ 21 %), X = 4,8 equivaldría a «el mismo Sharpe que el índice». A la ocupación del 5 % haría falta X = 20 para lo mismo. Un único X no puede significar lo mismo para estrategias con ocupaciones distintas: ésa es la naturaleza de la medida, no un defecto de calibración.

---

## 5. Lo que no cuadra o no está medido

### 5.1 Con posiciones solapadas, la ocupación cuenta residuos de coma flotante como «dentro»

`occupancy.held` acumula sumas y restas de tamaños (`occupancy.py:32-35`) y `measure` cuenta `gross > 0` (`occupancy.py:70`); `presence` cuenta `lots != 0` (`occupancy.py:95`). En coma flotante, 0,1 + 0,2 − 0,1 − 0,2 no da cero sino 2,8 × 10⁻¹⁷. Tras dos operaciones que se solapan, ese resto queda en todas las barras siguientes.

Reproducido con el código real (`residuo.py`): operación A de 0,1 lotes en las barras 0-2 y B de 0,2 lotes en las barras 2-4, de diez barras. Los lotes salen `0,1 · 0,1 · 0,3 · 0,2 · 0,2 · 2,8e-17 · 2,8e-17 …` y la ocupación sale **1,0** en vez de 0,5. Con 0,3 y 0,6 el resto es negativo: la ocupación sale bien (0,5) pero `presence` cuenta el 100 % de las barras como dentro. Con 0,1 y 0,2 solapadas el resto es 2,8 × 10⁻¹⁷ desde la barra 5 y la ocupación sale 1,0 (revisor, con `occupancy.held`). El mecanismo es que `edges[k] = -a + b` se redondea antes del `cumsum` (`occupancy.py:33-35`).

Alcance real: en las 29 fichas, **cero barras con residuo** en la rejilla que se usó, porque ninguna estrategia tiene dos posiciones en la misma barra. Aparece al contar las mismas operaciones en una rejilla más gruesa (USDJPY M30 contada en H1: ocupación 33,7 % en vez de 12,5 %, y hasta 92,6 % en `presence`), o con cualquier estrategia que piramide. También lo provoca una operación que abre en la barra donde otra cierra, según los tamaños: A de 1,1 lotes en las barras 0-2 y B de 0,3 que abre en la barra 3 dejan un resto de 5,55 × 10⁻¹⁷ y ocupación 1,0 en vez de 0,6; 0,3 y 0,1, o 0,1 y 0,7, salen exactos (calculado por el revisor con el código real). Hay datos reales: USDJPY y NIKKEI225 contados en rejillas gruesas con operaciones que abren en la barra donde otra cierra dan residuo (p. ej. USDJPY H1, 10.23.380: ocupación 0,3371 frente a 0,1245).

Como la ocupación está en el denominador de la eficiencia, un fallo así hunde la eficiencia sin avisar. El error sólo puede suspender de más, nunca aprobar de más: la ocupación y las horas por semana se inflan y la eficiencia baja. Un arreglo posible, leído en el código y no probado: umbral `gross > 1e-9` en `occupancy.py:70` y `np.abs(lots) > 1e-9` en `:95`, o redondear el `cumsum` a 9 decimales en `:35`.

### 5.2 La rejilla del `config.yaml` no es la que se usa

`config.yaml:13` dice `timeframe: M30 # the bar grid occupancy is counted on`. `ui/daemon/runner/readings.py:79-83` la sustituye por el timeframe del export («The occupancy grid is the export's own timeframe, not config.yaml's M30»). Comprobado: la ocupación guardada de USA500 (0,2260) es la de H1; en M30 daría 0,2268. La diferencia es pequeña aquí, pero ni el README ni el manual ni el tooltip lo cuentan, y el comando del manual, lanzado a mano, usa M30. Para una estrategia de M5 o M15 lanzada a mano, eso activa además el problema del 5.1.

### 5.3 «Ilegible» se pinta como suspenso; no hay Limbo

El manual: una estrategia con pocas operaciones o ventana corta «no es que suspenda, es que no se puede leer». El código la marca `not_worth_it` y la ventana la pinta «Suspenso» en rojo (`verdict.py:58`, `one.py:104-105`), y `exposure.verdict.pass` vale 0. Lo mismo cuando el buy and hold pierde: una estrategia que gana en un activo que cae — por ejemplo una **corta** que gana, porque el buy and hold es siempre largo (`benchmark.py:109-122` y `:67` dan siempre lotes > 0) — sale suspendida con el motivo «el buy & hold pierde» (`verdict.py:46`). El dossier lo tenía al revés (una corta en un activo que sube): ahí el buy and hold gana, no hay ese motivo y la corta, que pierde, sale con «pierde dinero» (`verdict.py:44`). Consecuencia: una corta ganadora sale siempre Suspenso (eficiencia negativa más «el buy & hold pierde»), y una corta ganadora en un activo que sube se compararía con un largo, Sharpe contra Sharpe de signo opuesto, sin sentido. Choca con la regla 13 del proyecto (hay plantillas cortas). Verificado sólo leyendo el código (ninguna ficha es corta); `occupancy.held` (`:29`) y `presence` (`:97`, `np.sign`) sí manejan cortas bien y el `tilt` vale −1. La doctrina del dueño es que un hecho que falta es Limbo; aquí no existe ese estado. De los cuatro motivos que el código llama ilegibles, tres no han ocurrido en las 29 fichas (todas largas en activos que subieron en `oos1`). El cuarto, «pierde», está en 12 de las 29 (calculado por el revisor sobre `tabla.csv`): el código dice de ellas que su eficiencia «no se interpreta» (`verdict.py:44-45`) y las pinta «Suspenso». Con un estado Limbo, esas 12 dependerían de si perder en `oos1` se toma como hecho medido o como hecho que falta, que es lectura del dueño.

### 5.4 Las «horas fuera» incluyen horas con la posición abierta

`hours_off` = 168 − horas de barra con posición. La frase del README — las horas no expuestas «no llevan gap, ni noticia, ni drawdown» — sólo es cierta para las horas de mercado abierto sin posición. Una posición que cruza un cierre no suma horas (no hay barras) y sí sufre el hueco de la reapertura.

Medido por mí: en USA500 el 85 % de las operaciones cruza al menos un cierre diario; ninguna cruza un fin de semana, pero porque el 44 % de las salidas son «End Of Friday» — es una propiedad de estas estrategias, no del estudio. Una estrategia que mantenga el fin de semana tendría las mismas horas por semana y 48 horas más de riesgo que este número no ve. En USDJPY no cruza cierres ninguna.

### 5.5 «El día de cierre infla la desviación típica, así que es conservador»: no en lo medido

`benchmark.py:98-102` afirma que imputar todo el resultado al día de cierre hace la serie «más a saltos», infla su desviación típica y deja la comparación «conservadora hacia la estrategia, no favorecedora». El README y el manual repiten la conclusión, pero con el mecanismo al revés: dicen que así `equal_risk` mantiene **menos** activo. Con una desviación mayor mantendría **más** (lotes = desviación de la estrategia ÷ desviación del activo), y eso es lo que perjudicaría a la estrategia. Ninguno de los tres trae una medida.

Reconstruí la serie marcada a mercado barra a barra (calculado por mí; el neto total coincide al céntimo) en las seis recalculadas: la desviación típica marcada a mercado es **mayor**, no menor, en las seis, entre un 1,0 % y un 2,4 % (1.13.354: 436,9 frente a 426,5). Es decir: en estos datos el día de cierre **rebaja** un poco la desviación, el buy and hold a igual riesgo sale con algo menos de lotes y la eficiencia queda en torno a un 2 % **a favor** de la estrategia. El sentido es el contrario al escrito y el tamaño es pequeño. Con operaciones de varias semanas podría ser distinto; aquí la más larga dura cinco días.

El drawdown de saldo frente al marcado a mercado diario apenas difiere (5,45 % frente a 5,53 %), pero ninguno de los dos es el flotante intradía (apartado 3.3), que es lo que manda en fondeo.

### 5.6 La correlación con el activo, medida al día de cierre, sale mucho más baja de lo que es

Calculado por mí: la correlación entre el resultado diario de la estrategia y el movimiento diario del activo es 0,07 con la serie del estudio y **0,49** marcada a mercado (1.13.354); 0,08 y 0,44; 0,04 y 0,43. En USDJPY, 0,22-0,26 frente a 0,25-0,38. El estudio no calcula ninguna correlación, así que hoy no le afecta; pero el README dice que este módulo es «la antesala» de la regresión de alfa y beta. Hecha sobre esta serie, la beta saldría casi nula y todo parecería alfa.

### 5.7 El buy and hold no paga swap, y en índices no es un redondeo

El README y el manual lo dicen: no se le descuenta ni spread ni swap. Para el spread de una sola entrada es razonable. Para el swap, mantener 8,9 lotes de un CFD de índice durante cuatro años cuesta financiación todas las noches, mientras que la estrategia sí la paga en su resultado. El sesgo va **contra** la estrategia (el buy and hold sale más alto de lo que sería), y no es un redondeo. `assets/symbols/USA500.yaml:146-149` carga `swap_long: use -5.72` (% anual, el peor caso de FTMO y Hantec, decisión del dueño de 2026-10-01) y `benchmark.py:117-120` lo ignora a propósito. Estimación de orden de magnitud (calculada por el revisor: lotes a igual riesgo × cierre medio 3.968 × 5,72 % × 1.461/360; es una cota, usa el swap de hoy del peor caso y no el de Infinox ni el histórico, sin dividendos): swap del buy and hold de 8.209 · 8.290 · 6.966 USD (1.13.354 · 18.15.392 · 5.13.334), contra un neto del buy and hold de 13.445 · 13.578 · 11.410. Con el swap puesto quedaría en 5.236 · 5.288 · 4.444 y la eficiencia en 14,1 · 8,6 · 2,6 (hoy 5,48 · 3,36 · 1,03): **5.13.334 pasaría de Suspenso a Aprobado**. Es más de la mitad del retorno del buy and hold en esta ventana.

### 5.8 Se juzga en el tramo que eligió

Apartado 2.9. Además, el README avisa con razón de que el veredicto «no tiene nada que cortar» en una población filtrada por beneficio en OOS; pero el autopiloto lo corre **siempre** sobre una población así (las supervivientes de la puerta), nunca sobre otra.

### 5.9 El suelo de operaciones no es el del dueño

`min_trades: 30` en toda la ventana. El suelo de trabajo del dueño es de 35 operaciones **al año**. En USA500 las tres madres tienen 32, 31 y 24 al año y el paso 21 no dice nada. Sobre las 29 fichas, 21 quedan por debajo de 35 operaciones al año, entre ellas 10 de las 14 aprobadas; las que lo superan son USDJPY 4.25.395 y tres de `Trade_NIKKEI225` (calculado por el revisor sobre `tabla.csv`: operaciones ÷ `days` ÷ 365,25). Además, 9 de las 14 aprobadas tienen un Sharpe menor que un error típico (0,5) y 13 de 14, menor que dos.

### 5.10 La documentación va por detrás

| dónde | qué dice | qué hay |
|---|---|---|
| README línea 3, manual líneas 12-13 | «el último paso de la secuencia» | el workflow sigue hasta el 26 |
| `studies/closing/README.md` | `atrCalculator` es el paso 22 | el 22 es el mapa condicional; el stop es el 24 |
| manual, «Qué produce» | `verdict.csv` con «las 30 columnas» | 14 columnas (`many.py:18-20`); y el autopiloto no lo escribe |
| manual, «Cómo se ejecuta» | feed `XAUUSD_DukasM1_Infinox` | los feeds se llaman `XAUUSD_M1` desde el 2026-10-01 |
| manual, «Cómo se lee» | un bloque de texto «EN EL MERCADO… VEREDICTO worth_it» | el comando imprime hoy las tablas del contrato; ese formato ya no sale, y los datos del ejemplo se borraron el 2026-09-25 |
| manual, «ESTUVO PRESENTE» | un número alto sería «beta con horario» | apartado 3.6 |
| `occupancy.py:86` | `moves`: «cambio de cada barra a la siguiente» | se le pasa el cambio desde la barra anterior (`one.py:62`), que es lo correcto según el test |
| `inputs.py:36-37` | «los exports son fechados e inmutables» | el de USDJPY del 10-06 se reescribió ese día con otras estrategias |

### 5.11 Lo que no está medido

- **Ningún nulo ni intervalo** para ninguna de las cifras del paso (2.8 es una ilustración mía, no parte del estudio).
- **Cuánto infla la selección sobre `oos1`** la eficiencia: haría falta la misma cuenta sobre `oos2`, que está reservado.
- **El swap del buy and hold** (5.7): sólo estimado por el revisor, como cota; el estudio no lo cobra.
- **El sesgo de redondeo a barra** en estrategias de operaciones cortas: en estas corridas es cero (todas abren y cierran en aperturas de barra), así que no hay caso real con el que medirlo.
- **Cortas.** Las 29 fichas son largas. Todo lo que el estudio haría con una corta (5.3) está leído en el código, no visto en datos.
- **La pestaña «Contra el activo y el azar»** del WFM: no he comprobado qué fue de ella.

### 5.12 El umbral 2,0 frente al azar

Quien tiene el activo una fracción p del tiempo, puesta al azar, gana p veces la deriva con una desviación diaria √p veces la del activo: su Sharpe es √p × el del activo y su eficiencia √p ÷ p = **1 ÷ √p**. Con p = 22,6 % sale 2,10; con 5 %, 4,5; con 1,3 %, 8,8 (álgebra; el revisor). El comentario de `config.yaml` («1,0 significa tan productivo por hora como tener el activo») no describe eso.

Con datos (calculado por el revisor; eficiencia bruta de las rotaciones del calendario de cada madre, sin costes: con costes el nulo baja y no lo midió):

| madre | mediana de las rotaciones | rotaciones con eficiencia ≥ 2 | 1 ÷ √ocupación |
|---|---|---|---|
| USA500 1.13.354 | 2,02 | 50,3 % | 2,10 |
| USA500 18.15.392 | 2,42 | 53,9 % | 2,19 |
| USA500 5.13.334 | 2,71 | 55,1 % | 2,47 |
| USDJPY (las tres) | 2,57 a 2,71 | 52,5 a 53,9 % | 2,55 a 2,90 |

Es decir: el umbral 2,0 es, hoy, lo que saca la mitad de las colocaciones al azar de la misma exposición.

### 5.13 El error del Sharpe del activo y cuánto se repite el «Aprobado»

Calculado por el revisor (bootstrap estacionario de días, bloque medio 10, 4.000 tiradas, mismos días para la estrategia y el activo, ocupación fija; otros bloques moverían los porcentajes, no el orden de magnitud). Activo: USA500, 1.032 días (3,99 años), Sharpe 0,485, error típico ±0,49, intervalo del 95 % de −0,44 a +1,48, probabilidad de ≤ 0 del 15 %; USDJPY, 1.300 días (4,99 años), 0,374, ±0,44, de −0,49 a +1,29, 20 %. Veredicto bajo el remuestreo:

| madre | eficiencia guardada | intervalo del 95 % | veces que sale «Aprobado» |
|---|---|---|---|
| 1.13.354 | 5,48 | −32 a +45 | 70 % |
| 18.15.392 | 3,36 | −25 a +37 | 54 % |
| 5.13.334 (suspensa) | 1,03 | −34 a +43 | 37 % |

Por año natural en USA500 (revisor): Sharpe del activo +0,53 · +1,78 · −0,96 · +1,71 (2020 a 2023); eficiencia de 1.13.354: 7,36 · 2,67 · −0,83 · 1,27. En 2022 ninguna estrategia podría aprobar (el buy and hold pierde); en 2023 la mejor madre suspende con 1,27. En USDJPY el activo pierde en tres de los cinco años. El código sólo aparta el denominador negativo o nulo (`verdict.py:46`); con uno positivo y pequeño la eficiencia se dispara y aprueba.

### 5.14 El swap del buy and hold que el estudio no cobra

Descrito en 5.7. Resumen: el estudio no lo descuenta; una cota gruesa lo pone en 6.966-8.290 USD por madre en USA500, y con él la eficiencia de 5.13.334 pasaría de 1,03 a 2,6 y de Suspenso a Aprobado.

### 5.15 Poca ocupación no es poco riesgo en fondeo

«Una estrategia sin posición no puede perder» es verdad y no es el riesgo que quiebra una cuenta de fondeo. Caso (calculado por el revisor desde la columna `MAE ($)` del export): USDJPY 4.25.395, «Aprobado» con eficiencia 6,17 y ocupación 15 %, tuvo una operación de 4,23 lotes abierta el 2022-10-21 de 08:00 a 21:00 que llegó a ir perdiendo 11.246 USD, el 11,25 % del saldo, dentro de un solo día; cerró en −5.370. En USA500 las tres madres comparten la misma peor operación (flotante −6.285 USD, cierre −5.555). «Igual riesgo» iguala la media de la ventana, no lo que se arriesga un día dentro (los días con resultado oscilan 2,8 a 3,3 veces más que la serie con ceros). No se ha consultado el límite diario de cada firma en el catálogo.

### 5.16 Cortas

Descrito en 5.3: una corta ganadora sale Suspenso porque el buy and hold es largo. Las 29 fichas son largas y esto está leído en el código, no visto en datos.

---

## 6. Cierre

El paso 21 hace bien una cosa que nadie más hace en el workflow: contar cuánto tiempo de mercado usa una estrategia, con la ventana fijada por la política y no por las operaciones. Eso es una descripción fiable (con la salvedad del 5.1) y útil para comparar supervivientes y, más adelante, para la cartera.

Lo que añade encima — la eficiencia y su veredicto — es un cociente de Sharpes dividido por la ocupación, leído sin contraste sobre el tramo que ya seleccionó a las estrategias. Tal como está aprueba casi todo lo que gana algo, y por eso no tiene regla en el autopiloto. Las decisiones que quedan:

| # | decisión | lo que gana | lo que cuesta |
|---|---|---|---|
| 1 | **Dejar el 21 como anotación** (hoy) o darle una regla | sin regla no se pierde ninguna estrategia y la ocupación queda para la cartera | con el veredicto propio caerían 15 de 29, pero 12 ya pierden dinero en `oos1`: la regla sólo añade 3 bajas |
| 2 | **Qué mide «merece la pena»:** eficiencia (premia estar poco tiempo, linealmente y sin suelo), `return_ratio` (Sharpe contra Sharpe, sin premio), o las dos por separado | con `return_ratio` ≥ 1 el listón no depende de la ocupación y se entiende solo | pasarían 6 de 29; y renuncia a la preferencia del encargo («5 % en una hora a la semana»). Ojo: con el swap del buy and hold puesto (5.7), el veredicto de una de las tres madres de USA500 cambia |
| 3 | **Sobre qué tramo** | en `oos2` el número no está inflado por la selección y coincide con el tramo del paso 20 | gasta una mirada a `oos2`; el export `CrossTF_Mothers` no lo trae; y entonces el 21 repite casi exactamente la comparación del 20, salvo la ocupación |
| 4 | **Si separar la deriva** (lotes medios × subida del activo, o el trader al azar del paso 8, o la regresión aparcada) | contesta la pregunta que el dueño hace de una larga en un activo que sube; en la ilustración, ninguna aprobada llega al percentil 95 | es estadística nueva: un nulo más que mantener y, con rigor, otra prueba que corregir |
| 5 | **Qué hacer con lo ilegible** (pocas operaciones, el activo pierde, cortas) | un estado Limbo, como en el resto de la cadena | hoy no ocurre en ningún caso real; es trabajo para un caso que aún no ha aparecido |
| 6 | **Arreglar la ocupación con solapes y documentar la rejilla** (5.1, 5.2) | la ocupación deja de poder salir al 100 % por un residuo | nada en estrategias; es una corrección de código y una línea del manual |
| 7 | **El suelo de operaciones**: 30 en la ventana o 35 al año | coherencia con el resto de la cadena | en USA500 las tres madres quedarían por debajo |
| 8 | **Qué significa el umbral** | hoy 2,0 es lo que saca la mitad de las colocaciones al azar de la misma exposición (en bruto), y el veredicto de una misma estrategia cambia entre el 37 % y el 70 % de las veces al remuestrear los días | cualquier umbral fijo hereda el error del Sharpe del activo en cuatro años (±0,5); no hay cifra que lo evite con este tramo (calculado por el revisor) |

Ninguna de estas ocho depende de las otras salvo la 2 y la 3 con la 1: si el paso sigue siendo una anotación, lo único urgente es la 6.
