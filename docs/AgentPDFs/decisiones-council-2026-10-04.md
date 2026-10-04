# Lo que decidió el Council y lo que se hizo — 2026-10-04

Leíste la hoja de 27 decisiones y contestaste «Confío en el criterio de la comunidad, hacedlo todo».
Este documento dice qué se decidió, qué se ejecutó el mismo día, qué tienes que hacer tú y qué sigue
abierto. La hoja original es `decisiones-pendientes-2026-10-04`.

## 1. En una página

- **Decidido:** 26 de los 30 puntos. **Vuelven a ti:** 4 (C4, R1c, F6, P1).
- **Ejecutado:** el registro tiene las 28 poblaciones de calibración; el autopilot ya no puede leer la
  reserva `oos2`; el fondeo se modela con el peor caso mientras no contesten los soportes; el descuadre
  de USDJPY en la reconstrucción de la curva está explicado y arreglado; snoopingScreen lee la curva a
  cierre; la búsqueda de cartera (hito M3) está construida y probada.
- **No se hizo:** ninguna corrida real de cartera, ninguna lectura de `oos2`, nada en StrategyQuant X.
- **Tú:** enviar tres mensajes a soporte (§4) y contestar las preguntas de §5.

**Cuánto fiarse.** Los cinco miembros corren sobre el mismo proveedor de modelos y 22 de los 30 puntos
fueron unánimes desde la primera ronda: eso es riesgo de que todos piensen igual, no prueba de acierto.
Sólo 3 decisiones se comprobaron en el código y 1 en las cifras de la hoja; las otras 22 son
razonamiento.

## 2. Las decisiones

«Peso» es la suma de los votos a favor, cada uno ponderado por la confianza de quien vota (alta 1,
media 0,75, baja 0,5). El máximo es 5 y una decisión necesita 3,33.

| ID | decisión | peso | estado hoy |
|---|---|---|---|
| C1 | archivar el pool de desarrollo | 5,00 | 30 madres archivadas; el resto depende de la pregunta 1 |
| C2 | la búsqueda de cartera ordena por rangos de cuatro métricas a pesos iguales | 3,75 | construido |
| C3 | la cartera elegida debe batir al 95 % de 10.000 carteras al azar en oos1, y tener Sharpe deflactado mayor que cero en oos2, leído una sola vez | 3,75 | escrito en el plan, sin ejecutar |
| C5 | cuántas estrategias por cartera: lo que permita la cuenta de 10k al lote mínimo | 3,75 | anotado |
| C6 | sin rebalanceo: pesos fijos | 4,75 | anotado |
| C7 | no hay categoría «sin explicar, en prueba» | 5,00 | anotado |
| F1 | FundedNext se aplaza | 5,00 | sigue como candidata |
| F2 | FundingPips: preguntas tú al soporte | 4,75 | mensaje redactado |
| F3 | FTMO: preguntar; mientras, sin reembolso de la cuota por cuenta | 5,00 | hecho |
| F4 | Hantec: preguntar; mientras, sin reembolso, el −2 % sólo en fase 1, rechazada en oro | 4,75 | hecho |
| F5 | gastado oos2, lo que valida la cartera es la incubación en vivo | 3,75 | anotado en el hito M9 |
| R1a | el registro se rellena con las 28 poblaciones | 4,25 | hecho |
| R1b | N cuenta las estrategias generadas, no las aceptadas | 4,25 | hecho |
| R1d | cada población de calibración lleva fila del paso 6 y del paso 8 | 3,75 | hecho |
| R2 | la reserva de oos2 ata al autopilot | 5,00 | hecho |
| R2b | un estudio empezado conserva la ventana de oos2 con la que empezó | 4,75 | **no hecho** (§3.1) |
| R3 | si falta un dato: fallo en presencia y sanidad, limbo en las demás reglas | 3,75 | hecho |
| R4 | los pasos 10 a 16 leen oos1 | 4,00 | hecho |
| R5 | parar un proyecto a mano cuenta como fallo | 4,50 | ya era así |
| E1 | los umbrales de la t no se tocan; se juzga con `drift_excess_t` | 5,00 | hecho |
| E2a | no se vuelve a correr XAUUSD/OOS | 3,75 | nada que hacer |
| E2b | «tiene ventaja» se mide contra el azar sin costes | 3,75 | anotado, sin tocar código |
| E2c | la ficha de costes de XAGUSD no es definitiva | 4,50 | aviso para la sesión del spread |
| E3 | cosechar operaciones por variante en el paso 16.5, tras medir el coste en un lote | 3,50 | pendiente: necesita SQX |
| E3s | snoopingScreen y blindJoint leen la curva a cierre reconstruida | 5,00 | hecho en snoopingScreen; blindJoint, sólo el código |
| P2 | en el paso 20 la corrección cuenta todas las madres que entraron | 4,25 | hecho |

**Glosario mínimo.** *oos1* y *oos2*: los dos tramos de datos que la búsqueda no vio; oos2 es la
reserva y sólo se puede leer una vez. *N*: cuántas estrategias se han probado en total; cuanto mayor,
más exigente es cualquier prueba, porque entre muchas siempre alguna sale bien por suerte. *Sharpe
deflactado*: el Sharpe descontando esa suerte. *Limbo*: ni pasa ni falla; la estrategia queda apartada.

## 3. Lo que se hizo

### 3.1 Autopilot y registro

- **Registro.** Escritas 56 filas: 14 estudios, 118.235 estrategias sobre las 28 poblaciones. El
  registro pasa de 807 a 863 filas y una segunda ejecución se niega, así que no duplica. N global:
  **1.341.126 estrategias en 86 estudios**. Copia previa en
  `AlgoData/scratch/ledger-backup-2026-10-04/`.
- **Reserva.** El autopilot arranca con `ALGO_AUTONOMOUS=1`: el paso 8 sobre oos2 se niega; los pasos
  17, 18, 18.5, 19 y 24 siguen funcionando.
- **Dato ausente.** `presencia_passed` y `sanidad_passed` fallan si falta el dato; el resto, limbo.
- **Segmento.** Los pasos 10, 12, 14 y 16 declaran oos1.
- **No hecho — R2b.** La ventana de oos2 se lee de `assets/_policy.yaml` cada vez; ningún estudio de
  Python guarda la suya. Las tareas de SQX sí conservan sus fechas. Fijarla exige guardar las fechas
  por estudio y cambiar quien las lee: es un diseño, no un retoque, y no se improvisó.
- **Efecto lateral.** Con la reserva cerrada, el paso 20 pierde dentro del autopilot su mitad
  SPA/StepM, porque blindJoint no está en la lista de estudios con permiso sobre oos2 (pregunta 9).
- **Sigue debido.** La prueba real del autopilot: tres corridas a cero supervivientes y matar SQX a
  mitad. Necesita el custodian.

### 3.2 La curva a cierre

- **Causa del descuadre de USDJPY, medida.** SQX resta la comisión entera de ida y vuelta de la equity
  flotante desde la entrada; la reconstrucción la apuntaba al cierre. Sobre 400 estrategias y 182.389
  días con posición abierta, el descuadre dividido por los lotes da 5,00 $ (entre 4,96 y 5,04 en el
  90 % de los casos), que es la comisión. La convención de SQX es la correcta: el bróker cobra al
  ejecutar.
- **Resultado.** Estrategias de USDJPY que cuadran con SQX a menos de 1 $: de 0 a **3.729 de 3.732**.
  USA500 sigue en 97,3 %.
- **snoopingScreen** ya lee la curva a cierre. Antes y después:

| población | p del SPA antes | p del SPA después | correlación con el activo | estrategias que nombra |
|---|---|---|---|---|
| USDJPY calibración (3.732) | 0,76 | 0,71 | 0,13 → 0,32 | 0 → 0 |
| USA500 calibración (3.786) | 0,95 | 0,93 | 0,28 → 0,42 | 0 → 0 |

  La *p del SPA* es la probabilidad de ver un resultado así de bueno si ninguna estrategia de la
  población batiera a comprar y mantener; por debajo de 0,05 habría algo. Aquí sigue muy lejos.
  **Decisión: el arreglo es correcto pero no cambia ningún veredicto; coste, cero estrategias.** Lo
  que sí cambia es la correlación con el activo, que estaba subestimada a menos de la mitad.
- **blindJoint** tiene el mismo código, probado sólo con datos sintéticos. No puede calcular su SPA
  hasta que el paso 16.5 guarde las operaciones por variante (E3); mientras, se niega sin abrir oos2.
- **Paso 20.** `joint.population` queda en `entrantes`; `joint.pieces` sigue sin decidir (P1).
- **Queda suelto.** `search/stageb_data.py`, de otra sesión, aún reconstruye sin la comisión; las
  cachés de universo anteriores a hoy hay que rehacerlas; la comisión en porcentaje no está
  verificada. La población `Test_USDJPY_donchianUpperCrossUp_H1` no cuadra (10 de 60): se construyó
  con otro valor del punto y con el feed anterior al cambio de reloj.

### 3.3 Cartera

- Decisiones escritas en `portfolio/PLAN.md` §12 y `portfolio/DECISIONS.md`, con fecha y con lo que
  las revertiría. C4 va marcada como provisional.
- **Hito M3 construido y probado:** las cuatro métricas, la puntuación por rangos, la búsqueda
  (exhaustiva o genética), la admisión, las filas del registro y el comando, con su capítulo en el
  manual de cartera.
- **No existe todavía:** ninguna corrida real, ni el veredicto (M5), ni la mitad de oos1 con las
  carteras al azar.
- **Para la primera corrida real hacen falta:** un pool declarado y miembros que lleven el stop del
  paso 24. De las 30 madres archivadas, ninguna lo lleva.

### 3.4 Fondeo

- **FTMO 2-Step 10k** sin reembolso por cuenta: el coste esperado en cuotas sube de 20,0 a 30,0 $ por
  cada 1.000 $ de cuenta aprobada, y el plan baja del puesto 5 al 11 del ranking. Esa cifra es lo que
  se paga de media en cuotas hasta aprobar si la estrategia no tuviera ventaja; una ventaja real la
  baja.
- **Hantec:** el add-on «Profit Target −2 %» baja sólo la fase 1. No mueve ningún precio, porque sólo
  se vende en Express, que tiene una fase.
- Con el descuento de hoy encabeza el ranking Hantec Express 10k (13,2 $ por cada 1.000 $).
- Las dos reglas siguen marcadas «sin confirmar»: la respuesta del soporte las cambia.

## 4. Lo que tienes que enviar tú

**FTMO**

> Hello, I plan to buy several FTMO 2-Step Challenges. Your FAQ says the paid fee is refunded with the
> first Reward withdrawal. If I buy several 2-Step Challenges and each becomes an FTMO Account, is the
> fee refunded for each account (with that account's first Reward), or only once per trader? Thank you.

Si es por cuenta, el coste vuelve a 20 $ por cada 1.000 $.

**Hantec**

> Hello, I have four questions about Hantec Trader challenges: (1) Is the challenge fee refunded after
> passing or at the first payout? (2) Does the add-on «Profit Target -2%» lower the profit target of
> every phase or only of phase 1? (3) Where can I find the list of prohibited trading strategies?
> (4) What commission is charged on gold (XAUUSD) on these accounts? Thank you.

Con la comisión del oro, Hantec deja de rechazarse en XAUUSD.

**FundingPips**

> Hello, I trade with an Expert Advisor I built myself (exported from StrategyQuant X, running on
> MetaTrader 5, fixed rules, no copying between accounts, no latency or arbitrage tricks). May such a
> self-built EA open and close trades on your Challenge and Funded accounts, or are EAs allowed only
> as trade/risk managers? Please point me to the rule that says so. Thank you.

Este mensaje se redactó sin releer la hoja de admisión de FundingPips; revísalo antes de enviarlo.

## 5. Lo que sigue siendo tuyo

### Las cuatro sin consenso

- **C4 — cuándo entra una candidata en la cartera.** Los cinco eligieron «mejora el Sharpe de la
  cartera y además pasa los filtros de pares contra cada miembro», pero con confianza baja. En contra:
  con esos filtros una candidata independiente entra con probabilidad de 0,75 por cada miembro ya
  dentro, un 24 % con cinco. Se usa como provisional.
- **R1c — qué es «aceptadas».** Los cinco eligieron el Accepted de SQX (4.600), con confianza baja.
  Con N contando generadas apenas importa. El código ya hace esto.
- **F6 — riesgo por fase, recompra, qué horizonte mostrar.** Tres aplazan, dos proponen: riesgo igual
  en cada fase, sin recompra automática dentro de los 1.000 €, y varios horizontes con el más prudente
  de titular. No se cambió nada.
- **P1 — qué es pasar el paso 20.** Cuatro por «ninguna pieza en fallo», uno por «unanimidad». A favor
  de la unanimidad: endurecer después es honesto, aflojar no.

### Preguntas nuevas que salieron al ejecutar

1. ¿El pool de desarrollo son sólo las 30 madres, o también los 182.220 supervivientes del paso 8 de
   `Test_Calib_*`, XAUUSD y los demás `Test_*`?
2. Probabilidad de año perdedor: ¿años naturales o ventanas móviles de 252 días?
3. Con búsqueda genética, ¿los rangos se calculan contra las semillas voraces o contra otro conjunto?
4. ¿La búsqueda puntúa la ventana de construcción entera, o el mínimo de ventanas desplazadas de 0 a
   3 meses?
5. «Mejora el Sharpe»: ¿Sharpe con la candidata menos Sharpe sin ella, o la derivada marginal? ¿Las
   candidatas se prueban en secuencia o todas contra la misma base?
6. ¿Hay tope de riesgo abierto a la vez y tope por símbolo? Hoy el tamaño sólo lo limita el filtro de
   pares.
7. Veredicto en oos1: ¿qué cifra se compara con el percentil 95, y son 10.000 combinaciones al azar o
   10.000 búsquedas enteras?
8. Veredicto en oos2: ¿el N es el del estudio del pool, el de sus miembros o el de todo el proyecto?
9. ¿Se añade blindJoint a la lista de estudios con permiso sobre oos2, para que el paso 20 conserve su
   mitad SPA/StepM dentro del autopilot?
10. R2b: ¿se diseña el anclaje de la ventana de oos2 por estudio?

## 6. Lo que invalidaría una decisión

- **R1b.** Si estrategias sintéticas con ventaja conocida no sobreviven con N = generadas, el embudo no
  tiene potencia y toca un N efectivo. Kahneman lo dejó escrito como voto particular.
- **F3 y F4.** Si un soporte confirma el reembolso antes de comprar, se remodela.
- **E3.** Si exportar un lote de variantes resulta inasumible, la reconstrucción se queda en
  snoopingScreen.

**Difíciles de deshacer:** todo lo que toca la lectura de oos2 (R2, C3, P2, P1); el fondeo en cuanto se
compre una cuenta; y cambiar N después de haber visto resultados.

## 7. Lo siguiente

1. Tus respuestas a §5: las preguntas 1 y 5 a 8 bloquean la primera corrida real de cartera.
2. Con el custodian libre: la prueba real del autopilot y medir el coste de exportar un lote de
   variantes.
3. Que las madres lleguen al paso 24: sin el stop no hay miembros para una cartera.
