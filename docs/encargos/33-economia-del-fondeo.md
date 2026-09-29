# 33 · La economía del fondeo — lo que sale del banco contra lo que vuelve — encargo autocontenido

**Tu oficio:** Python y estadística, en `portfolio/funded/`, con una vista en `ui/` al final.
**Tu encargo es contestar, con números y su incertidumbre, una sola pregunta del dueño: ¿qué
challenge compro, con qué add-ons, con qué cartera de EAs y a qué riesgo, para que el dinero que
entra en mi cuenta bancaria por cobros supere al que sale por compras?** No la rentabilidad de la
cuenta fondeada: la del flujo de caja real entre el banco del dueño y la empresa de fondeo.

Lee `CLAUDE.md` · `CODESTYLE.md` · `portfolio/CLAUDE.md` · `portfolio/BUILD_COMPENDIUM.md` (§2, §5-§7,
§10) · `portfolio/DECISIONS.md` (#1, #6, #7) · `portfolio/common/monteCarlo/` · `mt5/README.md` ·
`knowhow/costs/prop-firm-catalogue-hantec.md` · `studies/readings/monkey/README.md`.

---

## 0 · De dónde sale

El dueño, 2026-09-29: «Un error que cometía yo antes era ver las cuentas de fondeo de la misma forma
que una cuenta real, fijándome únicamente en la performance interna de la cuenta, sin contar el
coste de la fondeada. Quiero empezar a aplicar matemáticas seriamente». Una empresa (Hantec Trader,
la que está mirando) vende challenges de 1, 2 y 3 pasos y cuentas instantáneas, en varios tamaños,
con add-ons que cambian las reglas (más pérdida máxima, más reparto, menos objetivo…) y **cada uno
cambia el precio**. La elección es un problema de decisión con un precio en cada casilla.

Contesta `DECISIONS.md` #6 (qué reglas codificar y de qué empresa) con datos, y toca el #1 (si la
cartera fondeada y la real admiten las mismas estrategias).

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

### 3.2 Los caminos

La equity diaria de la cartera sale del archivo (`AlgoData/archive/`), a riesgo unitario. El camino
simulado se genera con **bootstrap por bloques del P&L diario conjunto** (~20 días,
`DECISIONS.md` #7 y `BUILD_COMPENDIUM.md` §7.1): barajar operaciones sueltas subestima el drawdown de
una cartera. El intradía (lo que importa para la pérdida diaria sobre flotante) se reconstruye con las
barras M1 que ya existen; donde no, se usa el MAE de cada operación como cota y se dice. El ciclo
entero — compras, suspensos, recompras, fases, cobros cada N días, suspensión en fondeada — se
simula completo, no fase a fase por separado.

**El edge real es la mayor incertidumbre, no el azar de los caminos.** Los caminos se generan con
el rendimiento **descontado**: el tramo OOS, no el IS, y un recorte del edge (`h` = 0 %, 25 %, 50 %,
75 %, 100 %). El resultado se enseña como curva VE_banco(h) y su **recorte de equilibrio**: «este
plan sigue siendo positivo si el edge en vivo es al menos el 40 % del OOS». Una decisión que sólo
vale con h = 0 no es una decisión.

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
Qué tramo puede leer la selección es `DECISIONS.md` #11: pregunta al dueño, no lo supongas.

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
   decisión (con un presupuesto máximo de caja)?
5. ¿El precio pagado es el de lista o con el descuento habitual, y cuál?
6. Qué tramo lee la selección (`DECISIONS.md` #11) y qué recortes `h` quiere ver.

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
7. `portfolio/CLAUDE.md`: las reglas de fondeo quedan escritas ahí primero, y `DECISIONS.md` #6 se
   cierra con lo que el dueño conteste.

**Hecho es:** para la cartera que el dueño elija del archivo, la tabla de §4 sobre los 44 planes de
Hantec con los add-ons que tengan sentido, contra el mono, con recortes, y una frase de decisión.
