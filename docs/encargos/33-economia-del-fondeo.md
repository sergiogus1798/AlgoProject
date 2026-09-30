# 33 · La economía del fondeo — lo que sale del banco contra lo que vuelve — encargo autocontenido

**Tu oficio:** Python y estadística, en `portfolio/funded/`, con una vista en `ui/` al final.
**Tu encargo es contestar, con números y su incertidumbre, una sola pregunta del dueño: ¿qué
challenge compro, con qué add-ons, con qué cartera de EAs y a qué riesgo, para que el dinero que
entra en mi cuenta bancaria por cobros supere al que sale por compras?** No la rentabilidad de la
cuenta fondeada: la del flujo de caja real entre el banco del dueño y la empresa de fondeo.

Lee `CLAUDE.md` · `CODESTYLE.md` · `portfolio/CLAUDE.md` · `portfolio/BUILD_COMPENDIUM.md` (§2, §5-§7,
§10) · `portfolio/DECISIONS.md` (#1, #6, #7) · `portfolio/common/monteCarlo/` · `mt5/README.md` ·
`knowhow/costs/prop-firm-catalogue-hantec.md` · `studies/readings/monkey/README.md` ·
`docs/encargos/34-validacion-mt5-pool.md` (el pool del que lee y la traducción a cada empresa).

---

## 0 · De dónde sale

El dueño, 2026-09-29: «Un error que cometía yo antes era ver las cuentas de fondeo de la misma forma
que una cuenta real, fijándome únicamente en la performance interna de la cuenta, sin contar el
coste de la fondeada. Quiero empezar a aplicar matemáticas seriamente». Una empresa (Hantec Trader,
la que está mirando) vende challenges de 1, 2 y 3 pasos y cuentas instantáneas, en varios tamaños,
con add-ons que cambian las reglas (más pérdida máxima, más reparto, menos objetivo…) y **cada uno
cambia el precio**. La elección es un problema de decisión con un precio en cada casilla.

Contesta `DECISIONS.md` #6 (qué reglas codificar y de qué empresa) con datos. El #1 ya está
decidido: la cartera fondeada y la real leen el mismo pool (dueño, 2026-09-29).

**Va después del motor de construcción de carteras y es suyo el dimensionado** (dueño, 2026-09-29):
el motor elige combinaciones y pesos; este encargo pone el riesgo por operación, las reglas de la
empresa y la probabilidad de aprobar. Riesgo fijo fraccional, nunca Kelly, y Monte Carlo de todos
los tipos de `BUILD_COMPENDIUM.md` §7: bootstrap de operaciones, bootstrap por bloques del P&L diario
conjunto, distribución por fecha de inicio, ventanas móviles e inyección de los peores días.
Y una pieza que va **antes** del motor: lo que una empresa prohíbe sin remedio (mantener el fin de
semana, operar en ventanas de noticias…) saca estrategias del pool de esa empresa antes de buscar
carteras; el motor busca sobre lo que queda (dueño, 2026-09-29).

## 1 · El cambio de unidad: el banco, no la cuenta

Una cuenta fondeada **no es capital del dueño**. El dueño compra una opción: paga una prima (el
precio del challenge) y, si el camino de la equity respeta las reglas hasta el objetivo, recibe una
serie de cobros hasta que una regla la rompe. Lo que se optimiza es:

```
VE_banco = E[ Σ cobros recibidos ]  −  E[ Σ precios pagados ]  (− comisiones de pago, − impuestos)
```

donde las compras incluyen **las recompras tras cada suspenso** y los cobros incluyen **el reembolso
de la cuota** si la empresa lo da. Una estrategia excelente en cuenta real puede tener VE_banco
negativo (pierde el 5 % diario una vez al año y eso basta para suspender), y una mediocre de baja
varianza puede tenerlo positivo.

Consecuencias que el modelo tiene que respetar:

1. **La pérdida está acotada al precio**; la ganancia es la cola. Es una opción: la varianza de la
   cuenta no se paga igual que en capital propio. El riesgo óptimo por operación es una U invertida
   (`BUILD_COMPENDIUM.md` §10.1) y **distinto en cada fase**: en el challenge conviene llegar al
   objetivo antes de tocar el límite; en la fondeada conviene sobrevivir muchos ciclos de cobro.
   El riesgo es una variable de decisión por fase, no un dato.
2. **Todo se mide en % del tamaño**: con reglas porcentuales una cuenta de 200k es dos de 100k en
   P&L, pero el precio **no** es lineal (Hantec Express: 2k = 39 $ = 19,5 $/k; 200k = 999 $ = 5,0 $/k).
   Hay que comparar planes por precio por unidad de riesgo y por lo que pesa un suspenso en la caja.
3. **Varias cuentas con la misma cartera no diversifican**: suspenden juntas. Sólo diversifica otra
   cartera, otro reparto temporal (comprar escalonado) u otra empresa.
4. **La caja tiene su propio drawdown**: la racha de suspensos antes del primer cobro. El dueño
   necesita ver el desembolso máximo acumulado esperable (percentiles), no sólo la media.

## 2 · El catálogo: extraerlo, no copiarlo a mano

**Ya está construido** (2026-09-29): la base de datos `AlgoData/funding/funding.sqlite`
(`portfolio/funded/catalog/`, léete su `README.md`) tiene Hantec y FTMO — planes, reglas por fase,
add-ons, **todas las combinaciones de add-ons con su precio y sus reglas resultantes** (tabla
`combos`) y un compendio de reglas con fuente y estado (`rules`). El agente `fundingWatcher` la
refresca cada domingo e investiga las reglas pendientes. **Lee de ahí; no vuelvas a extraer nada.**
Fórmula del precio de Hantec en `knowhow/costs/prop-firm-catalogue-hantec.md`.

Lo que viene en el JSON, por plan: tipo (`challengeType` 1/2/3/99), familia, tamaño, precio,
objetivo %, pérdida diaria %, pérdida máxima %, estática o trailing, días mínimos rentables,
frecuencia de cobro (días), consistencia sí/no, noticias prohibidas, cierre obligatorio el viernes,
límite de tiempo, reparto (sólo en las instantáneas: 80 %), y por add-on su recargo `pricePct` y su
efecto (`secondary`: «+2%», «95%»…).

A 2026-09-29, resumido:

| familia | pasos | tamaños | precio | objetivo | diaria | máxima | tipo DD | otras |
|---|---|---|---|---|---|---|---|---|
| Express | 1 | 2k-200k | 39-999 $ | 10 % | 5 % | 6 % | trailing | cobro 14 d |
| Enhanced | 2 | 5k-200k | 59-1169 $ | 10 % (fase 1) | 5 % | 10 % | estático | 3 días mín. |
| EnhancedX | 2 | 5k-200k | 59-1169 $ | 8 % (fase 1) | 4 % | 8 % | estático | consistencia |
| Endurance | 3 | 5k-200k | 29-499 $ | 6 % (fase 1) | 4 % | 8 % | estático | — |
| Instant Funding | 0 | 1k-50k | 43-2139 $ | — | 6 % | 6 % | trailing | 80 %, sin noticias, cierra viernes |
| Instant Lite | 0 | 1k-100k | 19-699 $ | — | 3 % | 5 % | trailing | 80 %, 5 días mín., consistencia |
| Instant24 | 0 | 2k-100k | 13-299 $ | — | 2 % | 3 % | trailing | 80 %, consistencia, cierra viernes |

Add-ons (recargo sobre el precio base, sumados, no compuestos): reparto 95 % +30 %, pérdida máxima
+1 % +20 % / +2 % +30 %, objetivo −2 % +25 %, cobro semanal +20 %, primer cobro a demanda +30 %,
noticias +25 %, fin de semana y noticias +25 %, sin días mínimos +10 %, sin días rentables mínimos
+25 %, consistencia +5 % +30 %, quitar consistencia en fases 1 y 2 +40 %, 12 h extra +30 %.

**Lo que el JSON no trae y hay que sacar de los Términos y confirmar con el dueño antes de simular:**

- el objetivo de las fases 2 y 3 (el JSON da uno solo por plan);
- el reparto base de los challenges (`profitSharePct` viene a 0);
- la pérdida diaria: su centro de ayuda dice que es un % del mayor entre balance y equity a las
  00:00 del servidor del día anterior — confirmarlo en los Términos vigentes;
- si la cuota se reembolsa con el primer cobro;
- la fórmula exacta de la consistencia (la página la muestra rota: «(Best Day's Profit + Total
  Profit) × 100», probablemente mejor día ÷ total);
- cobro mínimo, límite de riesgo abierto, apalancamiento, qué pasa con un add-on de pérdida máxima
  sobre la diaria, plan de escalado, y qué significa `rewardFrequency` 0 y `timeLimit` 0;
- **el precio que de verdad se paga**: la web anuncia un −50 % casi permanente (DROP50, no para
  Instant24) que no está en el catálogo. El precio pagado es una entrada del modelo, no el de lista.

**Otras empresas**: «Adding a firm» en el README del catálogo. Los precios cambian: un VE calculado
guarda la fecha del catálogo contra el que se calculó (las tablas llevan `valid_from`/`valid_to`).

## 3 · El modelo

### 3.1 Las reglas como máquina de estados

Cada plan es una secuencia de fases (1, 2, 3 o 0 pasos) más la fase fondeada, y cada fase un conjunto
de reglas evaluadas **sobre la equity flotante día a día del servidor**, no sobre el cierre
(`BUILD_COMPENDIUM.md` §2.6, §10.2): objetivo sin posiciones abiertas, pérdida diaria, pérdida máxima
estática o trailing, días mínimos, consistencia, límite de tiempo, noticias, cierre del viernes.
Estados: `fase_k → aprobado | suspendido`, `fondeada → cobro | suspendida`. Una función pura por
regla, con tests de caso conocido (`tests/`): un camino a mano que rompe cada regla justo por un
tick y otro que la roza sin romperla.

**Las reglas filtran estrategias antes de simular nada**: cerrar el viernes elimina las carteras que
aguantan el fin de semana (o las obliga a cortar la operación, lo que cambia la estrategia — el
dueño decide cuál), y la prohibición de noticias elimina o recorta las que operan en ventanas de
noticias. Eso se cuenta y se enseña: «Instant24 deja fuera 7 de tus 12 estrategias».

### 3.2 Los caminos — qué histórico, y para qué

Decidido por el dueño el 2026-09-29. **Ni el histórico corto de la feed de fondeo ni el largo de
SQX solos:**

- **Qué estrategias entran**: sólo las del **pool validado** de esa empresa (encargo 34, paso 26),
  es decir, las que superaron los pasos 1-25 y cuyo backtest en MT5 con la feed de la empresa
  coincide con el de SQX. El pool trae también la **traducción** de SQX a esa empresa (reloj de su
  servidor, sus costes, flotante con M1).
- **La forma del riesgo** — cómo se mueve la equity día a día, las colas, las rachas — sale del
  **histórico largo de SQX traducido**. El tramo de fondeo es uno o dos regímenes: un Monte Carlo
  sobre él remuestrea los mismos meses y da una P(suspender) optimista y estrecha, justo en lo que
  más pesa en el VE. El camino se genera con **bootstrap por bloques del P&L diario conjunto** (~20
  días, `DECISIONS.md` #7 y `BUILD_COMPENDIUM.md` §7.1), en el día del servidor de la empresa: barajar
  operaciones sueltas subestima el drawdown de una cartera. El intradía se reconstruye con M1; donde
  no, el MAE de cada operación como cota, y se dice.
- **El nivel del edge** sale de los tramos **OOS**, nunca del IS: la búsqueda genética eligió la
  estrategia por su poco drawdown en IS, así que el IS aporta variedad de regímenes pero no su
  optimismo. Los caminos se recentran a ese nivel y se les aplica el recorte `h` (0 %, 25 %, 50 %,
  75 %, 100 %). El resultado se enseña como curva VE_banco(h) y su **recorte de equilibrio**: «este
  plan sigue siendo positivo si el edge en vivo es al menos el 40 % del OOS». Una decisión que sólo
  vale con h = 0 no es una decisión.

El ciclo entero — compras, suspensos, recompras, fases, cobros cada N días, suspensión en fondeada —
se simula completo, no fase a fase por separado. `oos2` ya está gastado cuando se llega aquí (lo usan
los pasos 17-25): no hay restricción de tramo, pero la elección de plan y cartera sigue siendo una
búsqueda que cuenta en el ledger (§3.4).

### 3.3 El nulo: lo que vale el plan sin edge

Antes de puntuar una cartera, simula **un mono** (entrada aleatoria con la misma frecuencia, duración
y riesgo, `studies/readings/monkey/`) en cada plan, con su mejor riesgo. Eso es el VE de la lotería
pura: lo que la empresa cobra por la opción. Algunos planes pueden tener VE_banco del mono cercano a
cero o positivo (reembolso de cuota, objetivo bajo, reglas laxas) y otros muy negativo. **El valor
de nuestras EAs en un plan es su VE menos el del mono en ese mismo plan**, y un plan donde el mono
casi empata es donde el edge rinde más por dólar.

### 3.4 Qué se busca y cómo se cuenta

Variables de decisión: plan (familia × tamaño) × subconjunto de add-ons × cartera × riesgo por
operación en cada fase × cuántas cuentas y cuándo se compran. Cada add-on se evalúa como
**ΔVE(add-on) − su precio**, no por intuición («+2 % de pérdida máxima por un 30 % más» se paga o no se
paga según la cartera).

Es una búsqueda sobre muchas casillas: **cada combinación evaluada va al ledger**
(`BUILD_COMPENDIUM.md` §2.1, encargo 32) y la ganadora se valida sobre un tramo que no la eligió.
Qué tramo lee: todo, porque llega con `oos2` ya gastado (§3.2); lo que sigue abierto es con qué datos no vistos se valida la combinación elegida (`DECISIONS.md` #11).

### 3.5 Cómo se elige — el plan que el dueño aceptó el 2026-09-29

**Primera iteración: cuentas de 10k como máximo** (dueño, 2026-09-29: la caja no está para más).
El universo es el de `plans` con `size` ≤ 10.000 y `account_ccy` = USD, nada más (dueño,
2026-09-29) — hoy Hantec Express 2k/5k/10k, Enhanced, EnhancedX y Endurance 5k/10k, y FTMO 1-step y
2-step de 10k USD (79 € y 89 €); las Instant de Hantec quedan fuera porque prohíben EAs. Dos consecuencias de ir pequeño que el modelo tiene
que ver:

- **El lote mínimo cuantiza el riesgo.** En 10k, un 0,5 % son 50 $; con 0,01 lotes y un stop ancho
  (oro, stops por ATR del paso 24) el riesgo mínimo posible puede pasar del objetivo. El riesgo por
  operación es discreto: se simula con lotes redondeados a lo que la cuenta admite, y una estrategia
  cuyo lote mínimo ya excede el riesgo buscado queda fuera de ese plan.
- **El precio por cada 1.000 $ es el más caro** en las cuentas pequeñas (Express 2k: 19,5 $/k; 10k:
  9,9 $/k). Con el tope de 10k, casi siempre gana la de 10k frente a varias pequeñas, salvo que
  varias pequeñas escalonadas en el tiempo diversifiquen algo.

El **presupuesto de caja** (desembolso acumulado máximo) es una entrada del dueño y una restricción
dura, no un informe: un plan cuyo p90 de desembolso antes del primer cobro la supera no se elige.
**El dueño lo fijó el 2026-09-29: 1.000 € en total** («pon 1000 euros en total en la cuenta
bancaria»). Los planes están en USD: se convierte al cambio del día del cálculo, y ese cambio queda
escrito junto al resultado.

Pasos:

1. **La geometría de cada plan es el suelo.** Sin edge ni costes, P(tocar +a antes que −b) = b/(a+b):
   Express +10/−6 ≤ 37,5 %; Express con +2 %/−2 % 50 %; dos pasos +10/−10 y +5/−10 → 33 %; Endurance
   (+6/−8)³ → 19 %. Precio por cuenta aprobada sin edge = precio / esa P. Es un orden de magnitud; el
   mono de §3.3, con límite diario, trailing y costes, da el suelo real.
2. **Ficha de compatibilidad** estrategia (o cartera) × plan, antes de simular: posiciones de noche o
   en fin de semana (FTMO Standard fondeada: ni overnight ni fin de semana → sólo Swing, 2-step);
   operaciones o stops en ventanas de noticias; concentración del beneficio en pocos días
   (`studies/readings/profitShape/`) contra las reglas de consistencia (FTMO 1-step 50 %, EnhancedX
   35 %); colas diarias y gaps contra la pérdida diaria (3 % en FTMO 1-step); frecuencia contra días
   mínimos, inactividad y ciclos de cobro; lote mínimo (arriba).
3. **Sin límite de tiempo, el riesgo del challenge se baja**: con edge, menos riesgo sube P(aprobar)
   a costa de tiempo; lo que lo frena es la degradación del edge y el VE por mes, no las reglas. Riesgo
   por fase como variable, bajo en challenge y más alto en fondeada es la intuición a contrastar.
4. **La fondeada es una opción de compra sobre el P&L**: cobras una parte de lo positivo y no pagas lo
   negativo, así que la volatilidad tiene valor hasta la barrera. **La política de retiro es una
   variable de decisión**: retirar todo o dejar colchón (en la Express la pérdida máxima queda fija en
   el balance inicial tras el primer retiro).
5. **Add-ons por ΔVE − precio, también por parejas** (el −2 % de objetivo y el +2 % de pérdida máxima
   cambian la geometría juntos). Referencia: el 95 % en la Express de 25k (80 → 95 %, +59,70 $) sólo
   compensa si el beneficio bruto esperado en fondeada supera 59,70 / 0,15 ≈ 398 $.
6. **Criterio robusto**: el mayor VE_banco con un recorte pesimista (p. ej. `h` = 50 %), dentro del
   presupuesto de caja, y cuyo puesto no cambie mucho al mover `h`. Nunca el máximo con edge completo.
7. **Varias cuentas con la misma cartera son una sola apuesta**: el número de cuentas y su calendario
   salen del presupuesto, contando las correlacionadas como una.

Intuición a confirmar o tumbar, no a asumir: con edge modesto y fiable ganarán los planes de DD
estático, cuota reembolsable y sin consistencia (FTMO 2-step, Hantec Enhanced); con edge dudoso, lo
que ya vale algo sin edge (reembolso, barreras simétricas, reparto alto).

## 4 · Lo que el dueño recibe

Una tabla por cartera, un plan por fila, ordenada por VE_banco con el recorte elegido, con:

- precio pagado (lista, add-ons, descuento) y riesgo por operación en cada fase;
- P(aprobar cada fase), P(llegar al primer cobro), número esperado de compras hasta el primer cobro;
- cobros esperados por cuenta fondeada y vida esperada de la fondeada (días, ciclos de cobro);
- **VE_banco por compra, por dólar invertido y por mes**, con su intervalo al 90 %;
- desembolso máximo acumulado (mediana, p90, p99) antes del primer cobro: el drawdown de la caja;
- recorte de equilibrio y ventaja sobre el mono;
- la regla que más suspende (pérdida diaria, máxima, consistencia, tiempo) — la que hay que atacar.

Y la decisión escrita (`CLAUDE.md`: un análisis termina en una decisión): **«compra X de tamaño Y
con los add-ons Z, riesgo r₁ en challenge y r₂ en fondeada, con esta cartera; VE +A $/mes si el edge
en vivo es ≥ h% del OOS; no compres W, que sólo es positivo con edge completo»** — o «ningún plan es
positivo con esta cartera», que también es una respuesta válida.

## 5 · Límites que el modelo declara, no esconde

- **Riesgo de contraparte y de reglas**: la empresa puede cambiar reglas, negar un cobro o cerrar.
  Un parámetro de «probabilidad de cobro denegado» y otro de «cierre de la empresa por año», con el
  VE enseñado también con ellos.
- **Ejecución en el servidor de la empresa**: su spread, comisión y deslizamiento no son los de
  Darwinex. El puente MT5 (`mt5/`, OPEN.md #78, la cuenta Hantec ya leída) mide la diferencia con
  backtests en su servidor; sin eso, los costes del activo con su sobrecoste (`assets/RULES.md`).
- **Impuestos y comisiones de pago/divisa**: parámetros del dueño, no se inventan.
- **El techo de asignación por trader** de la empresa limita cuántas cuentas escalan.

## 6 · Lo que es ambiguo — se pregunta, no se decide (regla 11)

Antes de simular, lista y pregunta al dueño, como mínimo:

1. Los huecos del catálogo de §2 que los Términos no resuelvan sin interpretación.
2. Cierre del viernes / sin noticias: ¿se descarta la estrategia o se modifica para cumplir?
3. ¿Se puede cambiar el riesgo entre fase y fondeada (y dentro de la fondeada tras un cobro)?
4. Tras un suspenso, ¿se recompra el mismo plan siempre, o la política de recompra es parte de la
   decisión? ~~Y la cifra del presupuesto de caja~~: 1.000 € en total (dueño, 2026-09-29, §3.5).
5. ~~¿Otras divisas de cuenta?~~ Sólo cuentas en USD (dueño, 2026-09-29).
6. ~~¿Precio de lista o con descuento?~~ De lista: los descuentos se ignoran (dueño, 2026-09-29).
7. Con qué datos no vistos se valida la combinación elegida (`DECISIONS.md` #11) y qué recortes `h` quiere ver.

## 7 · Entregables

1. ✅ `portfolio/funded/catalog/` y el agente `fundingWatcher` (2026-09-29). Falta un test del
   cálculo de precio contra la fórmula del JS de Hantec.
2. `portfolio/funded/rules/` — las reglas como funciones puras, con tests de caso conocido.
3. `portfolio/funded/sim/` — el ciclo completo de compra → fases → fondeada → cobros, sobre caminos
   por bloques, con el recorte `h` y el mono.
4. `portfolio/funded/decide/` — la búsqueda sobre planes × add-ons × riesgo, registrada en el ledger,
   que devuelve la tabla de §4 por el contrato de estudios (`core/study/CONTRACT.md`).
5. Una vista en `ui/` (zona PORTFOLIOS o una zona FONDEO, estilo terminal `theme.T`) que pinta la
   tabla, la curva VE(h) y el drawdown de la caja; el dueño edita ahí los huecos del catálogo y el
   precio pagado (memoria: la configuración se edita desde la ventana).
6. El capítulo del manual en `AlgoData/manual-fuentes/` (regla 8) y las cards de `knowhow/` que salgan.
7. **Enchufar el VE en `python3 -m portfolio.funded.deals.worth`** (`portfolio/funded/deals/`, dueño
   2026-09-29): hoy ese comando juzga una oferta sólo por el suelo sin edge; cuando exista el modelo,
   una oferta se juzga por cuánto sube el VE_banco de cada plan del universo con el precio rebajado.
8. `portfolio/CLAUDE.md`: las reglas de fondeo quedan escritas ahí primero, y `DECISIONS.md` #6 se
   cierra con lo que el dueño conteste.

**Hecho es:** para la cartera que el dueño elija del archivo, la tabla de §4 sobre los planes de
10k como máximo de Hantec y FTMO (§3.5) con los add-ons que tengan sentido, contra el mono, con recortes, y una frase de decisión.
