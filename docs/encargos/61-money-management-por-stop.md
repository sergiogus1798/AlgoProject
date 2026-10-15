# 61 · Money management por stop loss — las cinco comprobaciones antes de mover nada

**Tu oficio:** dimensionado de posiciones en SQX y en el EA de MT5, leído del código, de proyectos en disco
y de cosechas ya hechas. **Opus**: es diseño y aritmética fina, no ejecución mecánica (regla 17).
**Tu encargo:** un informe de una página con **cinco respuestas** — cada una «comprobado: sí / no / no se
puede saber sin X», con su cifra y su `fichero:línea` — y, al final, una recomendación: cambiar al money
management por stop, no cambiarlo, o cambiarlo con condiciones. **Nada cambia hasta que las cinco estén
contestadas y el dueño diga sí:** ni `_build.yaml`, ni un proyecto, ni un EA.

Lee `CLAUDE.md` (reglas 2-5, 10, 11, 16, 20) · `sqx/CLAUDE.md` · `portfolio/CLAUDE.md` · `mt5/verify/README.md`.

## 0 · De dónde sale

Revisión del dueño del 2026-10-11 (`~/Desktop/revision-pasos-01-07-2026-10-11.md`, §6.5): «Si el stop entra
en la estrategia, usar el money management de SQX que dimensiona por el stop loss de la estrategia: riesgo
fijo en dinero sobre la distancia del SL», y «Lo que no cambia, y conviene saberlo antes de mover nada».

**Hoy** (`assets/_build.yaml:61-62`): `ATRRiskBasedSizingFixedRisk` con `{Amount: 1000, ATRPeriod: 20,
ATRMult: 4, MaxLots: 500}` — 1.000 USD de riesgo a 4 ATR(20), 250 USD por ATR. Con el stop del paso 24 a
X ATR, la pérdida nominal es X × 250 USD: de 295 a 1.148 USD entre las diez madres del Nikkei (X de 1,18 a
4,59), unas arriesgan cuatro veces más que otras.

**La propuesta:** tamaño = 1.000 USD / (X × ATR × valor del punto), para que todas arriesguen los mismos
1.000 USD nominales.

**El argumento que hay que confirmar o tumbar:** si el stop usa el mismo ATR(20) que el dimensionado,
cambiar de método multiplica todos los tamaños de una estrategia por la constante 4 / X; neto y drawdown se
escalan igual y **Ret/DD, profit factor, Sharpe y todo cociente quedan idénticos** — ningún veredicto de los
pasos 8 a 20 cambiaría, sólo las cifras en dólares y en % de la cuenta. Es lo que la cartera ya hace:
`factor = atr_multiple / (risk_usd * x)` en `portfolio/common/construct/inputs/risk.py:50`.

Lo que se comprobó en el código el 2026-10-11:

- `FixedAmount` («Risk fixed money amount»), el candidato de la revisión, **sólo aparece en**
  `ui/daemon/sqxconfig/lists.py:26`: ningún módulo lo escribe ni lo ha probado. Su nombre y comportamiento
  exactos están por comprobar.
- Las cifras 295-1.148 USD, las operaciones de 325 lotes y el «3,6 veces la nominal» **no están en el
  dossier del paso 6** (`docs/AgentPDFs/criterios-implementados-2026-10-12.md:204` sólo da el método):
  vienen del documento de los pasos 21 a 26. Recalcúlalas tú de la cosecha (parte 3), no las cites.

## Las cinco comprobaciones

Para cada una: qué miraste, la cifra, el `fichero:línea`, y el veredicto. Sin arrancar ni consultar ningún
install: proyectos y EAs se leen **en disco** (`sqx/inspect/dump_project.py <P>` sobre un proyecto del
conductor parado; nunca el master).

**1 · ¿El ATR del dimensionado es el del stop?** Periodo 20, última vela cerrada, mismo marco. Mira cómo
escribe el paso 24 el stop en la estrategia (`grep -rn 'ATR' studies/ sqx/ --include=*.py -l | grep -i
'stop\|atr'`; el capítulo `54-atr-calculator` del manual dice dónde vive) y cómo calcula SQX el ATR del
money management (`knowhow/export/sqx-atr-is-wilder.md`: es el de Wilder). Si difieren en periodo, vela o
suavizado, el factor 4 / X deja de ser constante: **mide cuánto** — sobre una madre con su stop, la
dispersión del cociente entre los dos tamaños operación a operación (coeficiente de variación).

**2 · ¿Muerde el tope de lotes?** `MaxLots: 500`. Con X = 1,18 el factor es 3,4. Sobre la cosecha
`AlgoData/harvest/Trade_NIKKEI225_M30_volatilidadL/Stop_p90/` (y `Results/`), por madre: tamaño máximo hoy,
tamaño máximo × 4 / X, y el % de operaciones que pasarían de 500. Y fuera de SQX: lote máximo y distancia
mínima de stop del símbolo en FTMO y Hantec (la ficha del activo en `assets/symbols/`, `mt5/README.md`); no
uses las herramientas MCP de MT5 si el terminal está ocupado por otra sesión.

**3 · Los huecos.** El riesgo se fija sobre el stop nominal, no sobre la pérdida real. Por madre, en
`build`: la peor pérdida con stop dividida por la nominal (la revisión dice hasta 3,6), su percentil 99, y
cuánto sería en USD con el riesgo igualado a 1.000. Con el tamaño igualado ese hueco pesa lo mismo en todas:
di si alguna estrategia pasa a tener una cola peor de lo que el fondeo admite por operación
(`OPEN.md` §85 — sólo léelo, no lo edites).

**4 · ¿El EA exportado lleva el mismo money management?** El paso 26 hoy fija el lote del fichero. Lee
`mt5/verify/README.md` y `sqx/projects/mt5verify.py`: qué money management lleva el EA que exporta SQX, si
MT5 calcularía el mismo tamaño (valor del tick, redondeo de lote, `Decimals: 2`), y qué habría que cambiar
en la verificación para que compare tamaños y no sólo operaciones. **No exportes ni compiles nada**: es
lectura; si la respuesta exige una corrida, descríbela y su coste, y pregunta.

**5 · Dónde se pone.** El método depende de que la estrategia tenga stop. Opciones a describir con lo que
cada una obliga a rehacer (qué pasos se repiten, qué cosechas dejan de valer): (a) en el build, para todas
— pero las estrategias del build pueden no tener stop: ¿qué hace SQX entonces?; (b) al adelantar el stop
antes del 16.5 (madre con stop y con este método, y de ahí todo igual — documento de los pasos 21 a 26,
§2.4 opción A); (c) sólo en el paso 24 y en el EA; (d) no en SQX: la cartera ya iguala el riesgo con
`risk.py:50`. Y comprueba el argumento central de §0 con un caso: una madre con su stop, sus operaciones
reescaladas por 4 / X — ¿Ret/DD y profit factor salen idénticos al tercer decimal?

## Lo que no tocas

`assets/_build.yaml` · ningún `project.cfx` · ningún install de SQX (ni arrancar, ni parar, ni consultar)
· el terminal de MT5 · `oos2` (todo se mide en `build`) · `portfolio/common/construct/inputs/risk.py` ·
los costes (encargo 59) · el rediseño de la cola (pasos 21 a 26): este encargo sólo dice dónde encajaría.

## Decisiones del dueño — pregúntalas (regla 11)

**Contestadas por el dueño (2026-10-14)** — lo que sigue manda sobre la lista de abajo:
- 2 → **`FixedAmount` con 1.000 USD**. 3 → **bajar el riesgo por operación** si el tope muerde. 5 → **sí**, tope de pérdida real además del nominal.
- 1 y 4 se contestan con el informe delante.


Al entregar el informe, no antes:

1. **¿Se cambia?** A la vista de las cinco respuestas: (a) sí, al money management por stop; (b) no — los
   cocientes no cambian y la cartera ya iguala el riesgo; (c) sí, pero sólo en el EA y en la cartera.
2. **¿Qué método exacto de SQX?** `FixedAmount` u otro de la lista (`ui/daemon/sqxconfig/lists.py`), con
   qué `Amount` — ¿los mismos 1.000 USD?
3. **El tope de lotes.** Si muerde: (a) subirlo; (b) bajar el riesgo por operación; (c) dejar que muerda y
   aceptar que la proporción se rompe en esas operaciones.
4. **Dónde.** Una de las cuatro opciones de la comprobación 5.
5. **Los huecos.** ¿Hace falta un tope de pérdida real por operación además del nominal?

## Objetivo — un comando

No lo hay: es un informe y una decisión. **Verificación:** el informe está en
`AlgoData/audit/money-management/por-stop-<fecha>.md` (regla 7), cada una de las cinco comprobaciones tiene
veredicto, cifra y `fichero:línea`; las tablas de las comprobaciones 2 y 3 salen de un script en `scratch/`
que se puede volver a correr; `git status --short` no muestra ningún cambio fuera de `knowhow/`.

## Cómo cierras

Qué hizo · qué verificó, con las tablas pegadas · qué dejó sin poder comprobar y qué haría falta · qué
descubrió para `knowhow/` (el comportamiento exacto del método de SQX y si el factor es constante, en
`knowhow/sqx-drive/` o `knowhow/conditions/`, editando la ficha que exista) · la lista de ficheros cambiados
y, como última línea, **¿Quieres hacer el commit?**

## Contestadas por el dueño (2026-10-14, noche)

- **61-1 → A con condiciones:** pasar a `FixedAmount` por stop, con riesgo común ≈ 550 USD o `MaxLots` por activo, y tope de pérdida real por operación.
- **61-4 → C:** sólo en el paso 24 y el EA (aceptar `FixedAmount` en `own_sizing` de `sqx/projects/mt5verify.py` y una fila de tamaño por operación en `mt5/verify/judge.py`).
