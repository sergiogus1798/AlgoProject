# Decisiones pendientes del dueño — 2026-10-15

Encargo 72, parte A1. Son todas las decisiones tuyas que hoy dejan provisional un umbral o impiden
que un comando corra, sacadas de `WORKFLOW.md`, `OPEN.md`, los encargos 49, 50, 51, 54, 61 y 65, y
las configuraciones de cartera, fondeo y vivo.

Hay una tabla por decisión, ordenadas por lo que desbloquean. Primero va lo que desbloquea el 53,
los monos por la cadena 10-20. Cada tabla tiene un código, las opciones tal como están escritas en
la fuente, y mi recomendación con su coste en estrategias o en trabajo.

**Cómo contestar:** con los códigos, por ejemplo «C1 C, C2 A, F2 0,30…». Con una línea vale. La
parte A2 del encargo lleva cada respuesta a su sitio.

Se han dejado fuera tres cosas:
- lo que ya contestaste (la lista de notas desfasadas está al final);
- el redondeo al tick del repreciador, que es el encargo 70 y está en manos de otra sesión;
- los umbrales del Monte Carlo de cartera (OPEN #19), que aplazaste el 2026-09-29.

---

## 1. Desbloquean el 53 y la congelación de los umbrales

Esta es la cadena que importa: 49 fila 1.2 (firmar los pasos 6 y 8), luego 1.6 (reglas de los
pasos 10-20), luego 1.9 (congelar). Mientras no esté firmada, la corrida de monos mediría unos
umbrales que todavía pueden moverse, y habría que repetirla.

### C1 — α de la regla z del paso 8 (P8-Z)

Fuente: `criterios-paso-08-corrida-nula-2026-10-12.md:114-120`. Es lo único tuyo que queda en el 65
bloque B.

| opción | α | monos que sobreviven | ventajas plantadas detectadas (0,05 / 0,10 / 0,15) | reales que quedan |
|---|---|---|---|---|
| A (hoy) | 0,05 | 4,8 % | 45 / 76 / 89 % | 122 |
| B | 0,0125 | 1,04 % (techo 1,36) | 25 / 59 / 82 % | 2 |
| C | 0,01 | 0,78 % (techo 1,06) | 23 / 57 / 80 % | 0 |

**Recomiendo C.** El objetivo de supervivencia nula es el 1,2 %:
- C es la única opción cuyo techo queda por debajo de ese 1,2 %.
- A deja pasar a 1 de cada 21 monos.
- **Coste:** las 122 reales de hoy se quedan en 0. Eso no lo provoca C. Dice que esas poblaciones
  no tenían una ventaja que se distinga del azar.
- **Ganancia:** una superviviente del paso 8 vuelve a significar algo.
- Una ventaja plantada de 0,15 sigue pasando el 80 % de las veces.

### C2 — El limbo del paso 8 (P8-L)

| opción | qué pasa |
|---|---|
| A (hoy) | el limbo sigue por la cadena |
| B | el limbo sale y sólo continúa el «pasa» |

**Recomiendo A.** Quitar el limbo reduce en 24 puntos la detección de la ventaja plantada de 0,15,
porque los pasos siguientes son los que separan el limbo bueno del malo. **Coste:** más CPU en los
pasos 9-19 por cada limbo.

### C3 — Endurecer `edge_mean_oos` en lugar de la z (P8-E)

| opción | qué pasa |
|---|---|
| A (hoy) | no se endurece |
| B | ≥ 5,75: 0,88 % de monos sobreviven; plantadas 17 / 48 / 79 %; quedan 106 reales |

**Recomiendo A, junto con C1 = C.** B deja pasar más reales, pero detecta peor las ventajas
pequeñas: 17 % contra 23 % en la de 0,05. Si eliges C1 = C, C3 sobra.

### C4 — Firmar las cifras del paso 6 (`assets/_study.yaml`)

Fuente: `WORKFLOW.md:239` y OPEN #93.

**Qué se decide:** la regla de PF ≥ 1,20 y beneficio > 0, en IS. El suelo de operaciones al año ya
lo fijaste el 2026-10-09: 35 en M15, M30 y H1, y 20 en H4. La calibración de la que salían estas
cifras se borró el 2026-10-04 porque el spread estaba mal.

| opción | qué pasa |
|---|---|
| A | se firman como v0 provisional y se recalibran con la corrida de monos del 53 |
| B | no se firman hasta una calibración nueva con los spreads recalculados |

**Recomiendo A.** El paso 6 es un filtro holgado. El que corta por estadística es el paso 8 (C1).
- Un PF de 1,20 demasiado bajo cuesta CPU en los pasos 7-8, pero no deja pasar falsos positivos.
- Con B, el 53 no puede empezar: necesita un carril fijo para medirlo.

### C5 — `dev.on` (5 supervivientes al azar que pasan para probar)

| opción | qué pasa |
|---|---|
| A | se apaga en todo salvo en la prueba funcional (`workflow test`) |
| B | sigue encendido |

**Recomiendo A.** Con él encendido, el recuento del embudo de los monos sale contaminado por 5
estrategias que no pasaron nada. **Coste:** ninguno en las corridas reales. Si `dev.on` es hoy un
interruptor global y no separa la prueba funcional, A2 lo comprueba.

### C6 — La regla de salida en la estrategia simple

Fuente: OPEN #93, al final.

| opción | qué pasa |
|---|---|
| A (hoy) | `_ExitRule_` aparece en un 50 % de las estrategias |
| B | toda estrategia lleva una (`exits.condition_required`) |

**Recomiendo A.** La regla 14 permite de 0 a 2 condiciones de salida. Obligar a una recorta el
espacio de búsqueda sin una medida que lo justifique. **Coste:** ninguno; es lo de hoy.

### C7 — ¿Son bloques de reloj `SessionHigh/Low/Open/Close`, `HighestInRange` y `CBlock_TimeBreakout*`?

Fuente: `WORKFLOW.md:240` y OPEN #93.

| opción | qué pasa |
|---|---|
| A | sí, prohibidos por la regla 15 |
| B | no, se permiten |

**Recomiendo A.** Una sesión se define por horas, y el 2026-10-13 ya metiste «session close» en la
regla 15. **Coste:** desaparece la familia de rupturas de sesión de las paletas v3. Si quieres
conservarla, la idea tiene que entrar por plantilla, con la sesión como bloque fijo y declarado.

### C8 — Qué significa «pasa» en el paso 20

Fuente: OPEN #50, encargo 65 D4 y D12.

Hay una contradicción entre dos decisiones tuyas:
- El 2026-10-04 fijaste `joint.pieces = sin_fallo`.
- El consenso del 65 (D4 y D12) dice que el paso 20 no deja fuera a nadie y que sólo corta la
  lectura única de `oos2` del 19.5.

| opción | qué pasa |
|---|---|
| A | manda el 65: el paso 20 sólo diagnostica, y se borra `sin_fallo` |
| B | manda `sin_fallo`: el paso 20 corta |

**Recomiendo A.** El 65 es posterior y deja un único punto de corte en `oos2`. Cada corte de más
sobre el mismo segmento es otra mirada. **Coste:** el paso 20 deja de filtrar. **Ganancia:** el
recuento de pruebas es honesto.

### C9 — Anotar en el ledger la mirada del 2026-09-26 a `oos2`

Aquella mirada fue al P&L diario en `oos2` de las madres de USDJPY.

| opción | qué pasa |
|---|---|
| A | se añade la fila |
| B | no se añade |

**Recomiendo A.** **Coste:** una prueba más en el contador, que sube un poco el listón de las
estrategias de USDJPY. Sin la fila, ese listón está mal calculado.

### C10 — La autorización única de `oos2`

Fuente: el README de encargos, «Una sola autorización».

Quedan tres usos, porque el 52 Q-8 lo quitaste el 14-10:
- el 49 §3.4 (ya contestado: calibrar en `oos1`);
- el 53 P6: los monos de los pasos 17-18;
- el 54 punto 12.

| opción | qué pasa |
|---|---|
| A | `oos2` sólo para la población de monos de los pasos 17-18; para estrategias reales sigue sellado hasta el 19.5 |
| B | sigue sellado para todo: los pasos 17-18 quedan fuera del embudo del 53, como techo declarado |

**Recomiendo A.** Una población sin ventaja no elige nada. Leer `oos2` con ella revela cómo se
comporta el azar en ese tramo, no qué estrategia real funciona.
- **Coste:** una fuga pequeña. Sabrás si `oos2` es un tramo fácil o difícil. Hay que anotarla en el
  ledger.
- **Ganancia:** el embudo del 53 cubre de verdad los pasos 17-18.

Para el 54 punto 12 (qué valida la combinación de cartera cuando `oos2` ya está gastado), recomiendo
la incubación en vivo (F5).

### C11 — Calibrar los P1-P9 del paso 10

Fuente: 51 D-1. El 14-10 la marcaste «sin objeto por el 65», pero las líneas siguen sin calibrar
(`criteria.yaml:127-183`).

| opción | qué pasa |
|---|---|
| A | se calibran dentro de la corrida del 53: sus monos son la población nula del paso 10 |
| B | corrida aparte, con una población plantada |
| C | se dejan sin calibrar y el paso 10 no corta |

**Recomiendo A.** No cuesta CPU de más. La parte plantada sale de las ventajas plantadas que ya
lleva el 53.

---

## 2. Desbloquean la cartera y el fondeo: hoy el código se niega a correr

### F1 — `stageb.t1_gap` (modelo de huecos del Monte Carlo T1)

Fuente: `portfolio/common/construct/config.yaml:54`. Sin este valor, el veredicto de fondeo no corre.

Sólo hay una opción construida: `close_to_open_blocks`. **Recomiendo esa.** **Coste:** ninguno; es
la que usa el ejemplo del README.

### F2 — `owner.tax_rate`

Fuente: `portfolio/funded/sim/config.yaml:30`. Sin ella no corre la simulación del banco (54 C).

Es la fracción de cada payout que se va en impuestos. No se puede proponer sin ti.

**Recomiendo** que pongas tu tipo marginal real; si dudas, uno prudente. Mueve el valor esperado,
casi nunca qué firma o plan sale elegido. Que lo confirme tu gestor: no es una cifra que deba poner
yo.

### F3 — `owner.p_payout_denied`

Fuente: `funded/sim/config.yaml:32`. Dijiste «5 % al año», pero el modelo lo aplica a cada
solicitud de payout.

| opción | qué pasa |
|---|---|
| A | 5 % al año, convertido por solicitud: 1 − 0,95^(1/n), con n = solicitudes al año del plan |
| B | 5 % por solicitud |

**Recomiendo A.** Es lo que dijiste. B penaliza el doble a un plan con payouts quincenales.

### F4 — `wf.confidence` (cuándo unos pesos «ganan» al reparto igual)

Fuente: `config.yaml:67`. El M8 se niega a correr sin él.

Con 6 brazos comparados al 95 %, una de cada 7 corridas da un ganador por azar.

| opción | qué pasa |
|---|---|
| A | 0,95 por brazo |
| B | 0,95 conjunto, con Bonferroni sobre los brazos (≈ 0,99 por brazo) |

**Recomiendo B.** **Coste:** el reparto igual gana más a menudo. **Ganancia:** un ganador ya no es
casualidad.

### F5 — Incubación (`incubation.figure`, `.history`, `.band`)

Fuente: `config.yaml:70-77`. El M9 no corre sin ellas.

| clave | opciones | recomiendo |
|---|---|---|
| `figure` | `pnl` / `sharpe` | `pnl`: es lo que paga una firma |
| `history` | `[oos1, oos2]` / `[build, oos1, oos2]` | `[build, oos1, oos2]`: la banda más ancha y estable |
| `band` | `[5, 100]` sólo marca por abajo / `[5, 95]` | `[5, 100]`: ir mejor de lo esperado no es motivo para retirar |

Lo que el plan no fija se pregunta con la primera cartera real, no ahora: cuánto dura la
incubación, cuántas marcas retiran una cartera y la rampa de tamaño.

### F6 — Qué entra en el pool de desarrollo (M0)

Fuente: PLAN §12, punto 8.

| opción | qué pasa |
|---|---|
| A | fuera los `Test_Calib_*` (spread mal) y todo lo construido con costes anteriores al 2026-10-01; dentro sólo lo de costes actuales |
| B | dentro todo lo archivado |

**Recomiendo A.** **Coste:** el pool se queda casi vacío hasta la primera corrida limpia, que es lo
que ya está pasando. Con B la cartera se construiría sobre costes que ya no son los tuyos.

### F7 — Confirmar las lecturas del código

| código | lectura que tomó el código | recomiendo |
|---|---|---|
| F7a | tope de riesgo abierto 0,5: la base es la `daily_loss` del catálogo sobre el saldo inicial, sea cual sea la base diaria del plan | confirmar |
| F7b | la pérdida máxima *trailing* no entra en ese tope | **cambiar**: en los planes trailing es el suelo que se rompe primero |
| F7c | percentil del veredicto, «mismo tamaño» = el K de la cartera elegida | confirmar |
| F7d | la peor métrica sobre los arranques desplazados en `oos1` | confirmar |
| F7e | menos de 20 combinaciones admisibles da «no se puede juzgar» | confirmar |
| F7f | el GA por encima de 1.000.000 de combinaciones no se ordena contra cliques al azar | dejarlo hasta que un pool real pase de ese límite |

### F8 — Hallazgos del #104 que necesitan tu sí

| código | qué | recomiendo |
|---|---|---|
| F8a | el tamaño de cada miembro se lee de la última versión archivada, no de la `identity@version` congelada en el pool | arreglarlo: que lea la congelada (es un error) |
| F8b | tres corridas dan tres ganadores a 0,003 | guardar la semilla en el manifiesto y una carpeta por corrida |
| F8c | `tests/test_portfolio_build.py` falla: nada archivado concilia | archivar una estrategia nueva cuando la corrida limpia dé una superviviente; no hay arreglo antes |

---

## 3. Fondeo: preguntas a soporte (tuyas, no de código)

| código | firma | pregunta | por qué importa |
|---|---|---|---|
| S1 | FundedNext | importe de la tarifa por uso de EA; si se permite una cuenta por cartera; puertas G3 (España) y G4 (historial de payouts) | decide si se activa: hoy es candidata, sólo para cuentas < 25k |
| S2 | FundingPips | ¿puede operar un EA propio exportado de SQX? | si es no, se descarta; si es sí, confirmar 8 precios y reglas en `fundingpips.yaml` |
| S3 | FTMO | ¿la devolución de la cuota del 2-Step es por cuenta? | valor esperado del plan |
| S4 | Hantec | ¿«Profit Target −2 %» baja todas las fases o sólo la 1? | hoy se modela sólo la fase 1 |
| S5 | Hantec | comisión en oro | la verificación se niega con Hantec en XAUUSD hasta que la rellenes en la zona Activos |
| S6 | todas | objetivo de las fases 2-3, reparto base, fórmula exacta de consistencia, pago mínimo, apalancamiento, plan de escalado, si el riesgo puede cambiar tras un payout | 33 §2 y 54-10, sin respuesta |

El reloj del servidor de Hantec (hoy se supone Nueva York + 7 h) no necesita soporte: lo leo yo del
terminal de MT5. **¿Lo leo?**

---

## 4. Vivo: desbloquean la parte C (conciliador y SPRT en cron)

La configuración del SPRT ya está completa (`ledger/thresholds.yaml:1176-1210`, Council 2026-10-12).
Lo que falta es del conciliador.

### V1 — `live.accounts`: qué cuentas son reales

Fuente: `mt5/reconcile/config.yaml:11`. Hay tres cuentas con beacon (11308943, 541350656 y 8063673).

**Dime cuáles son reales.** No se deduce de un nombre. Las de demo o de prueba no se concilian.

### V2 — `pairing.entry_tolerance_bars`

Fuente: `config.yaml:25`.

| opción | qué pasa |
|---|---|
| A | 1 barra, la misma que el paso 26 (`mt5verify.entry_tolerance_bars`, tuya del 2026-09-29) |
| B | otro valor |

**Recomiendo A:** la misma vara en la verificación y en la conciliación.

### V3 — El registro magic → estrategia (`reconcile/register.csv`)

No existe. Sin él, ni el conciliador ni el SPRT saben qué operación es de qué estrategia.

| opción | qué pasa |
|---|---|
| A | se genera solo desde `AlgoData/fleet/magics.csv`, la fuente que ya mantiene el despliegue |
| B | lo llevas tú a mano |

**Recomiendo A.** Una sola fuente, y no se desincroniza. **Coste:** un comando pequeño, dentro de
la parte C.

### V4 — Qué significa que «coincide»

| opción | qué pasa |
|---|---|
| A | sin listón por ahora: el informe describe, y el listón se fija tras 8 semanas reales |
| B | se fija ya |

**Recomiendo A.** No hay ni una semana real con la que calibrarlo.

---

## 5. Sueltas: no bloquean nada

| código | qué | opciones | recomiendo |
|---|---|---|---|
| L1 | NIKKEI225_M1 casi vacío al inicio del `build` (#117) | mover `build.from` / comprobar la primera operación | moverlo a 2014-01-01: 2013 todavía tiene marzo y abril vacíos |
| L2 | sesión de Brent: 109 huecos propios al año contra un límite de 30 | aprobar la sesión deducida / declarar otra | no construir sobre Brent hasta declararla; ahora no hace falta |
| L3 | puertas diferidas del builder (#118) | (a) ventana de la tarea contra su segmento; (b) segundo gráfico en una plantilla | (a) ya, porque es barata; (b) cuando aparezca la primera plantilla de dos gráficos |
| L4 | contador de pruebas (#96): nadie muestra la silueta junto al recuento | mostrarla / no | mostrarla: es ingeniería y no cambia ninguna cifra |

---

## Notas desfasadas que A2 corrige al aplicar tus respuestas

Estas notas dicen como pendiente algo que ya contestaste:
- `OPEN.md:564` y `portfolio/PLAN.md:561`: tope de riesgo abierto y percentil del veredicto. Están
  fijados desde el 2026-10-14 (0,5 y 0,95).
- `docs/AgentPDFs/WORKFLOW.md`, fila 14: «T3 no discrimina». T2 y T3 están borrados desde el 65
  (`criteria.yaml:187-194`).
- `docs/encargos/54-*.md:36`: el frente E sigue como «bloqueado por D», pero D está contestado.
- `docs/encargos/README.md:82`: el 52 sigue dependiendo de «`oos2` para la meseta», que se quitó el
  14-10.
