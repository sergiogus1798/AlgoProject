# 55 · MT5: el paso 26 (verificar contra la cuenta de cada empresa, y el pool) y la flota viva — plan que cruza sesiones

**Tu oficio:** Python sobre `mt5/`, `sqx/projects/mt5verify.py` y `ui/daemon/mt5bridge/`; MQL5 y un poco de
Windows para la flota. **Sonnet** en lo mecánico (reescribir un test, el paquete de despliegue, el
exportador una vez decidido); **Opus** donde haya que decidir un criterio o una estadística (la lectura de
«R», el drawdown flotante). Nunca pides ni escribes una orden: el MCP `mt5` no tiene herramientas de
órdenes a propósito (dueño, 2026-09-27) y este encargo no las pide.
**Tu encargo:** (1) cerrar el **paso 26** — que una superviviente real de los pasos 1-25 salga de MT5 con la
feed de cada empresa con un veredicto y una fila en el pool, y que de ese pool, y sólo de él, lea la
cartera —; (2) dejar la **flota** (decenas de cuentas de fondeo en una VPS Windows) al punto en que el
dueño monta los EAs de una cuenta sin clicar: perfil de gráficos, registro de magics, exportador de
carteras. Cada frente devuelve una decisión o un artefacto, no una descripción.

Lee `CLAUDE.md` (reglas 3, 5, 8, 10, 11, 12) · `CODESTYLE.md` · `mt5/README.md` · `mt5/verify/README.md` ·
`mt5/fleet/README.md` y `mt5/fleet/CONTRACT.md` · `mt5/reconcile/README.md` · `OPEN.md` #78 (`grep -n '^## 78'
OPEN.md`) · `knowhow/mt5/INDEX.md` · `knowhow/locations/vps-fleet-access.md` ·
`docs/AgentPDFs/WORKFLOW.md` (paso 26).

---

## Estado — lo actualiza cada sesión

| frente | qué | modelo | depende de | estado |
|---|---|---|---|---|
| B | Paso 26: queda la fila 5 con flotante (M1 del terminal de cada firma, K-2; sin decidir si cambia `dd_rel_gap_max`) y «R» = distancia al stop donde haya stop (K-1b); ninguna superviviente con stop para probarlo | Opus / Sonnet | una corrida real en MT5 | parcial: símbolos y `mt5/README.md` hechos |
| C | Paso 26: «Hecho es» — una superviviente real, su veredicto y su fila en el pool | Sonnet (la corrida es mecánica) | A, B, #78, una superviviente real | bloqueado |
| E | Flota — pieza B: hecho `mt5/fleet/package.py` + `deploy.py` + `vps/*.ps1`; falta validar el `.chr` en una cuenta DEMO del terminal de Wine (la cuenta que tiene hoy es Hantec 8063673, no se sabe si demo) y probar contra la VPS | Sonnet | demo en Wine, visto bueno del dueño | parcial |
| F | Flota — pieza C: hecho el reinicio con tarea programada (`deploy.py --install-watchdog`, sin probar en la VPS); falta pausar una cuenta (K-8c, fichero de control: exige que el EA o la baliza lo lean) | Sonnet | el dueño ve el diseño | parcial |
| H | Exportador de carteras (§3 de 35): magic, riesgo en USD, noticias, comentario, nombre | Opus (diseño) → Sonnet | G, E, encargo 54 (riesgo por tamaño) | pendiente |
| I | Flota — pieza D: la conciliación alimentada por las cuentas de la flota | Sonnet | decisión del dueño | pendiente |

## Bitácora

- 2026-10-14 — frentes A (ya estaba en verde: `tests/test_mt5verify.py` sale 0), D (pool en SQLite, `AlgoData/pool/pool.sqlite`; columna MT5 en PORTFOLIOS › Estrategias: lista todo y marca lo validado, K-3/K-4) y G (`mt5/fleet/magics.py`, desde 1001, K-5) hechos; K-6 hecho (`mt5/symbols.csv` borrado). E y F parciales, B parcial: ver la tabla. Manual: capítulo 113 y 86. Hoy el pool trae 22 filas y una `pass` (FTMO, Strategy 16.18.388, XAUUSD H1): no la he verificado como superviviente real.

- 2026-10-09 — consolidado de los encargos 34 (validación en MT5 y pool) y 35 (flota de MT5 en la VPS).
  Lo hecho de ambos se resume en «Ya construido»; los originales se leen con `git show
  c923d10:docs/encargos/34-validacion-mt5-pool.md` (y `…/35-flota-mt5-en-la-vps.md`).

---

## AVISO DE SEGURIDAD para el dueño — léelo antes de empezar

La VPS (Windows Server 2022) tiene **abiertos a internet el puerto 3389 (RDP) y el 5986 (WinRM HTTPS)**
(medido el 2026-10-02; `knowhow/locations/vps-fleet-access.md`). El dueño los dejó abiertos ese día (su PC
no está en Tailscale y la VPS sólo lleva cuentas de fondeo en reto): **no es un hallazgo que re-reportar en
cada sesión**, pero sí algo que **hay que volver a ofrecer en cuanto vaya dinero real a esa máquina** —
y los frentes E-I añaden en ella más superficie (paquetes copiados, tareas programadas). Pregunta en la
sesión en que se despliegue el primer EA: «¿Cerramos 3389 y 5986 ahora que hay [fondeada/real]?».
Tailscale ya admite sólo `100.64.0.0/10` en el puerto 22.

## §0 De dónde sale

- **Dueño, 2026-09-29 (paso 26):** las empresas de fondeo tienen en MT5 mucho menos histórico que SQX. La
  idea: backtestear con la feed de cada empresa, ver cuánto se parece a SQX en el tramo común y, si se
  parece, dar por bueno el histórico largo de SQX para esa empresa. Orden: todo lo que usa `oos2` para
  desarrollar la estrategia va antes, en los pasos 1-25; esta puerta **no elige estrategias por su
  rendimiento**, sólo comprueba que SQX reproduce la cuenta de la empresa (el tramo de la feed de fondeo
  cae casi entero en `oos2`, ya gastado). Por eso este encargo **no lee `oos2` por su cuenta**: el tramo lo
  pone el dueño en la ventana (Desde/Hasta).
- **Dueño, 2026-09-29 (flota):** una VPS con 4-5 instancias de MT5 operando; prevé que el estudio del
  fondeo (encargo 54) concluya llevar **muchas cuentas a la vez y quemar muchas** (p. ej. 10 instancias,
  5 de Hantec y 5 de FTMO); montar a mano cada EA le da «una pereza impresionante».
- **Hechos de partida de la flota:** un terminal MT5 = una cuenta conectada (varias cuentas en vivo exigen
  varias instancias; ni un EA ni el paquete Python `MetaTrader5` operan otra cuenta que la del terminal).
  La VPS **recoge y envía**; el Linux **calcula, guarda y enseña**.
- Depende de `OPEN.md` #78 (MT5 bajo Wine). Los frentes de la flota (E-I) dependen del encargo 54
  (`docs/encargos/54-fondeo.md`) sólo para el riesgo en USD por tamaño de cuenta.

## Ya construido — no se rehace (una línea por bloque)

- **Paso 26, la verificación entera:** `mt5/verify/{run,judge,conditions,firms,sqxside,mt5side,sidebyside,
  ticks,report,autopilot,pool}.py` (README: `mt5/verify/README.md`), el proyecto `Test_MT5Verify_…` en
  `sqx/projects/mt5verify.py` (exporta el EA a MQL5 sin interfaz: resuelve `OPEN.md` #78.3), la zona **MT5
  BRIDGE › Verificar** en `ui/daemon/mt5bridge/{api,runs,display}.py` y `ui/desktop/mt5bridge/`, los siete
  umbrales `mt5verify.*` en `ledger/thresholds.yaml:1041-1085`, capítulos del manual `76-mt5-verificar` y
  `86-mt5-pool-validado` (`AlgoData/manual-fuentes/`), card `knowhow/mt5/mt5-validated-pool-register.md`;
  commits `a52652c`, `784ce1e`. Como paso del autopilot: `mt5/verify/autopilot.py` (🤔 sin correr contra un
  conductor y un terminal reales).
- **Flota, pieza A (ver):** `mt5/fleet/vps/{FleetBeacon.mq5,probe.ps1}`, `mt5/fleet/{collect,rows,remote}.py`,
  `mt5/fleet/CONTRACT.md`, `bin/fleet-collect.sh` (cron cada minuto), MetaTracker en `mt5/fleet/app/` (pestañas
  Flota, Estrategias, Despliegue, Salud, Conciliación; `bin/metatracker`), tests `tests/test_fleet_{collect,
  equity,floors,progress,risk_rules}.py`, manual `93-metatracker`, `94-flota-colector`; la plantilla
  `AlgoData/fleet/Flota_de_cuentas.xlsx`; commits `71a3c40`, `6346a04`, `a6329c9`, `9ff6bc7`, `794665d`,
  `784ce1e`. **Decidido por el dueño: la flota vive en su propia app, no en `ui/`**
  (`mt5/fleet/app/README.md:3-6`, 2026-10-02), y el terminal de Wine lo controla Claude.
- **Conciliación semanal (pieza D, el código):** `mt5/reconcile/` (README; capítulo `89-reconciliador-semanal`),
  `bin/weekly-reconcile.sh`. Escrito, **no instalado en cron** (la línea es del dueño) y con `sqxside.py`
  sin correr. El agente `weeklyReconciler` sigue pendiente (nota del dueño).
- **Filtro de noticias por empresa:** `mt5/newsfilter/` (skill `/ea-news`, manual `75-filtro-noticias`).
- **Símbolo por empresa:** `mt5:` en `assets/symbols/<S>.yaml` (`mt5/verify/firms.py:29-36`,
  `knowhow/mt5/mt5-symbols-csv-only-had-one-row.md`).

## 1 · Lo que decidió el dueño el 2026-09-29 para el paso 26 (ex 34 §0.5) — sección autónoma

> Otros documentos citan «encargo 34 §0.5»: esta es esa sección, íntegra en sustancia. Léela aquí.

**Cambio de diseño (dueño):** en vez de traducir el histórico de SQX a cada empresa, **un backtest de SQX
por empresa, con las condiciones de esa empresa, comparado con el backtest del EA en MT5 en la cuenta de
esa empresa** — FTMO con FTMO, Hantec con Hantec. El terminal cambia de cuenta solo (las contraseñas están
guardadas en él). Lo que se construyó primero es **sólo la verificación**; el pool espera (hoy construido
pero con el formato por confirmar, frente D). La traducción vieja del histórico de SQX (reloj, costes,
flotante M1 — ex 34 §2) quedó **sustituida** para la verificación: el reloj ya no se convierte a mano, se
lee de las operaciones (`mt5.verify.judge.clock`); sigue siendo lo que necesitaría el encargo 54 sobre el
histórico entero.

Sus respuestas, que **no se vuelven a preguntar**:

| pregunta | respuesta |
|---|---|
| ¿con qué datos corre SQX? | los suyos (Dukascopy/Darwinex), con los costes de la empresa |
| ¿qué spread? | el que da la empresa en el momento de leerlo («spread actual del símbolo») |
| ¿de dónde salen las estrategias? | del archivo y de los databanks |
| ¿cómo se dimensiona? | con el de la propia estrategia (hoy FixedSize), en los dos lados: la tarea de SQX lo lleva y el EA se compila con ese lote fijo (la primera prueba real enseñó que, solos, ninguno de los dos lo usa) |
| ¿dónde se ve? | en la misma ventana, sección **MT5 BRIDGE › Verificar** |

**Qué se compara** (por estrategia × empresa, sobre el tramo en que las dos fuentes tienen datos; el
beneficio total no basta: las reglas de fondeo leen *días* y *caminos*):

| # | qué | cómo |
|---|---|---|
| 1 | coincidencia de operaciones | % de las de SQX emparejadas en MT5 (mismo lado, entrada dentro de una tolerancia en barras) — `mt5.compare.pair` |
| 2 | P&L por operación | diferencia media y su dispersión sobre las emparejadas |
| 3 | P&L diario en el día del servidor | correlación entre las dos series diarias y diferencia media absoluta, en % de la cuenta |
| 4 | peor día | el de cada lado, en % de la cuenta |
| 5 | drawdown intradía máximo sobre flotante | el de cada lado, con la equity reconstruida con M1 |

**Umbrales de partida que aceptó el dueño** (ya viven en `ledger/thresholds.yaml`, claves `mt5verify.*`;
una corrida los cambia con `--set`, y cambiarlos tras ver un resultado «está permitido pero no es gratis»:
cada corrida guarda con los que se juzgó y el ledger cuenta las repeticiones como ensayos):

| # | umbral | valor |
|---|---|---|
| 1 | emparejadas · tolerancia de entrada | ≥ 95 % · 1 barra del timeframe |
| 2 | diferencia media por operación | ≤ 0,05 R |
| 3 | P&L diario: correlación · diferencia media absoluta | ≥ 0,95 · ≤ 0,1 % de la cuenta |
| 4 | peor día | diferencia ≤ 0,5 puntos de % |
| 5 | drawdown intradía máximo | diferencia relativa ≤ 10 % |

**Veredicto y regla de repetición** (única que sólo vivía en el encargo; está también en la ayuda de
`mt5/verify/judge.py:158`): por estrategia × empresa, *validada* o *no validada, con la causa* (qué fila
falla). Si falla, se diagnostica (casi siempre el reloj o un coste), se corrige y se vuelve a comparar
**una sola vez**; si sigue fallando, esa estrategia no entra en el pool de esa empresa. Cada comparación
deja su fila en el ledger. Una versión nueva de la estrategia en el archivo no hereda la validación.

**Lo que queda de esa lista**, estado verificado el 2026-10-09:

| punto de ex 34 §0.5 | hoy |
|---|---|
| 1. el pool | construido (`mt5/verify/pool.py`); su formato sigue «propuesto» → frente D |
| 2. R = pérdida media de SQX en la fila 2 | sin confirmar → pregunta K-1 |
| 3. fila 5 = drawdown del balance al cierre; falta el flotante con M1 | pendiente → frente B |
| 4. Hantec en XAUUSD se rechaza hasta confirmar su comisión | **obsoleto**: `assets/symbols/XAUUSD.yaml:100-109` ya trae `hantec: SizeBased 5.0, confirmed: true` (2026-10-01, de operaciones reales de la cuenta); el test sigue esperando el rechazo → frente A |
| 5. `mt5/symbols.csv` sólo tiene XAUUSD | **obsoleto**: el fichero ya trae 18 activos y **nada lo lee**: `firms.names()` lee `mt5:` de `assets/symbols/<S>.yaml`. Sobra la frase de `mt5/README.md:50`; el fichero (git-ignorado) lo retira el dueño → pregunta K-6 |

## 2 · Frente A — `tests/test_mt5verify.py` en verde (primer paso, mecánico)

`OPEN.md:765` anotó 5 aserciones rotas mientras se reescribía `mt5/verify`. **Verificado hoy (2026-10-09):
sigue rojo, sale 1, con las mismas cinco** — el test no es de pytest (es un script con `main()` y 0 `def test`:
`python3 -m pytest tests/test_mt5verify.py` no recoge nada); se corre así:

```
python3 tests/test_mt5verify.py        # imprime los fallos; exit 1 si hay alguno
```

Los cinco fallos y su causa (líneas del test):
1. `test_mt5verify.py:87` «Hantec sin comisión confirmada en el oro no se rechaza» — la comisión ya está
   confirmada (§1, punto 4): cambia la aserción a otro activo/empresa con la comisión sin confirmar, o a
   «Hantec acepta el oro con su comisión de `XAUUSD.yaml`».
2. `:118` y `:120`, para `ftmo` y para `hantec` (4 aserciones) — el `Setup` de la tarea escrita ya no lleva
   `<Chart symbol="XAUUSD_M1" timeframe="M30" spread="…"` ni `dateFrom="2025.01.01" dateTo="2026.09.01"`
   con ese formato. **Reescribir contra el código actual:** abre `sqx/projects/mt5verify.py` (`write_task`) y
   el `Setup` que produce hoy, y ajusta las dos expresiones a lo que el código escribe a propósito. Si el
   código está mal y el test bien, es un fallo de código: arréglalo ahí, no en el test.

Hecho = el script sale 0, y se añade a `tests/` lo que haga falta para que `tools/checks.py` lo corra (mira
cómo lo lanza hoy `tools/checks.py`; no inventes un runner nuevo). `python3 tools/depmap.py && python3
tools/checks.py` al cerrar.

## 3 · Frente B — lo que falta de la verificación

1. **Fila 5, el flotante con M1.** Hoy es el drawdown del balance al cierre de cada operación
   (`mt5/verify/README.md:49-50`). `mt5/reconcile/floating.py` ya reconstruye MAE/MFE con las barras M1 de la
   feed de desarrollo (`portfolio…equity.excursions.rebuild`, sólo donde las barras cubren la operación):
   **reutilízalo**, no escribas otro. Dos lados: SQX y MT5 con la misma reconstrucción
   (`knowhow/mt5/reconcile-mae-both-sides-rebuilt.md`). Decisión: qué barras (¿las de desarrollo o las del
   terminal de la empresa?) → pregunta K-2.
2. **La lectura de «R» en la fila 2** (K-1): hoy R = pérdida media de SQX (porque estas estrategias no llevan
   stop; una antigua, `Strategy 3.48.75`, sí: 4×ATR, donde R sería el riesgo inicial). No cambies el umbral
   `mt5verify.trade_gap_max_r` hasta que conteste.
3. **Símbolos:** cada activo nuevo se nombra a mano por empresa en `mt5:` de su `assets/symbols/<S>.yaml`
   (ventana › Activos). Un activo que no nombre a la empresa **detiene esa empresa; nunca se adivina**
   (regla del dueño, ex 35 §1 #3). No hay nada que construir: sólo comprobar, antes de cada verificación, que
   `python3 -c "from mt5.verify import firms; print(firms.usable('<ASSET>'))"` no devuelve un rechazo por esto.
4. **Corrección de `mt5/README.md:50`** (la frase sobre `symbols.csv`) — dilo en la lista de ficheros
   cambiados; es una línea de documentación de código, en inglés.

## 4 · Frente C — «Hecho es» del paso 26

**Una superviviente real de los pasos 1-25, backtesteada con la feed de Hantec (y la de FTMO), con su
veredicto y su fila en el pool.** Necesita SQX (el conductor `SQX_w1`) y MT5 bajo Wine, una superviviente real
y un tramo Desde/Hasta del dueño. Por tanto: **no se corre sin que el dueño dé la estrategia, las fechas y el
modelo** (`ohlc_m1` o `every_tick`; ninguno tiene defecto, algunos datos de empresa son pobres) — regla 11.
Camino: la ventana (MT5 BRIDGE › Verificar, lanzador con confirmación — `ui/daemon/mt5bridge/`) o

```
python3 -m mt5.verify.run --strategy <sqx> --from YYYY-MM-DD --to YYYY-MM-DD --model ohlc_m1 [--firms ftmo,hantec] [--set k=v]
```

El conductor se pide con el protocolo de siempre (`/sqx-wait` antes y después; el trabajo ya arranca y para
el worker con `core.worker`); nada de `sqcli` a mano; el proyecto `Test_MT5Verify_…` se retira solo
(`sqx.projects.retire`). Esperar al resultado es **un solo comando en segundo plano** (regla 18).
Hoy `AlgoData/pool/{ftmo,hantec}.csv` tienen **5 filas cada uno, todas `fail`** (corridas del 2026-10-04 sobre
`Trade_NIKKEI225_M30_volatilidadL`; **sin verificar** si son de calibración o de una superviviente real):
léelas con `python3 -m mt5.verify.pool` antes de correr nada, y di en la bitácora qué eran. Un `fail` es un
resultado, no un error: diagnostica la fila que falla (reloj o coste) y repite **una vez** (regla de §1).

## 5 · Frente D — el pool: formato y quién lo lee

- **Formato:** hoy un CSV por empresa, sólo-añadir, `AlgoData/pool/<firm>.csv` (`mt5/verify/pool.py`,
  `record/read/history/rows_of/rebuild/pending`; card `knowhow/mt5/mt5-validated-pool-register.md`). Ex 34 §4
  dejó el formato «a decidir con el dueño» (el catálogo de fondeo usa SQLite: un precedente, no una
  obligación) → K-3.
- **Quién lo lee — grep hecho el 2026-10-09:** ni `portfolio/` ni la zona PORTFOLIOS de `ui/` importan
  `mt5.verify.pool` ni abren `AlgoData/pool/`. Sólo lo tocan `mt5/verify/` y sus llamadores
  (`pipeline/autopilot/finalists.py:59`, `ui/daemon/mt5bridge/`, `ui/daemon/workflow/sources.py`). La
  «pool» de `portfolio/` (`portfolio/PLAN.md:47`, `portfolio/common/construct/inputs/pool.py`) es **otro
  pool**: el declarado y congelado de la búsqueda, no el validado en MT5. **Es decir, el requisito de ex 34 §5
  punto 4 («el módulo de cartera y la zona PORTFOLIOS lista sólo lo validado») no está cumplido.**
  Reescribir contra el código actual: leer `portfolio/CLAUDE.md` y `portfolio/PLAN.md` §«POOL» y proponer al
  dueño (K-4) dónde engancharlo — p. ej. un filtro `--firm` que ya existe en `universe/real/funded`
  (PLAN: «`--firm` … drops every identity listed for that firm») — antes de tocar nada.
- Cuando el dueño decida: la lectura debe dar **por empresa** la lista de identidades con último veredicto
  `pass`; una versión nueva de la estrategia no hereda la validación.

## 6 · Frente G — el registro de magics (flota)

Decisión del dueño (2026-09-29, ex 35 §1 #6): **un magic por combinación estrategia × activo × temporalidad,
el mismo en todas las cuentas**, sacado de un registro y nunca reutilizado; **cortito**: secuencial de 4
cifras (1001, 1002…). Así nunca chocan dentro de una cuenta y cualquier operación del vivo dice qué
combinación la abrió, que es lo que lee la conciliación.

**No existe ningún asignador.** Y hay dos hechos que hay que reconciliar antes de escribir uno
(`knowhow/locations/live-ea-magic-numbers.md`): los EAs en vivo llevan hoy los magic **1…7**, y el registro que
lee la conciliación, `AlgoData/mt5/reconcile/register.csv` (`magic,strategy,identity,sqx,firm,since`), es **del
dueño** y no está escrito. → K-5 antes de construir. Cuando conteste, el asignador (un módulo pequeño en
`mt5/fleet/`) debe: leer/escribir un solo fichero en `AlgoData/fleet/`, asignar el siguiente libre desde 1001,
no reutilizar nunca uno retirado, y rellenar la columna «Magic» (gris) de `Flota_de_cuentas.xlsx`
(«lo rellena el despliegue»).

## 7 · Frente E — flota, pieza B: el paquete de despliegue

**Nada existe** (verificado: ningún `.chr` ni `profiles/charts` en `mt5/`, `bin/` ni `knowhow/`). Qué hace
(ex 35 §2 B), en el Linux y sin tocar la VPS:
1. El dueño deja la carpeta de `.mq5` y el Excel. Se compila cada `.mq5` a `.ex5` con `mt5/metaeditor.py`
   (`compile_path`, `expert`; **con el terminal cerrado**: `mt5/README.md`); se comprueba que compila, que el
   activo existe en la tabla de su empresa y que el EA es para la fondeada de esa cuenta (por el nombre del
   archivo: K-7); se asigna el magic (G).
2. Por instancia, un paquete: los `.ex5`, un `.set` por EA con su magic, y **un perfil de gráficos**
   (`profiles/charts/<perfil>/chartNN.chr`), un gráfico por EA con su símbolo, su temporalidad y el EA
   enganchado. **El formato del `.chr` depende de la versión de MT5: se valida primero con el terminal de
   Wine en una cuenta demo**, antes de acercarse a la VPS.
3. El paquete viaja por Tailscale (`ssh vps`, `mt5/fleet/remote.py` ya hace `scp` y `ssh`); un script de
   `mt5/fleet/vps/` lo copia a la instancia y la reinicia con ese perfil. Los terminales de la VPS **no son
   portables** (cada uno guarda sus datos en `%APPDATA%\MetaQuotes\Terminal\<hash>\`, comparten
   `Common\Files\`; `knowhow/locations/vps-fleet-access.md`) — el script de despliegue debe localizar la
   carpeta por `origin.txt`, no por una ruta fija.
4. **El «play» es del dueño:** se loguea y pulsa AutoTrading; las contraseñas no pasan por el sistema.
   Crear la instancia de una cuenta nueva (copiar una instalación limpia, nombrarla, registrarla) entra
   cuando el dueño lo pida, no antes.
Traducción de símbolos: el Excel lleva el nombre **de SQX**; `mt5:` de `assets/symbols/<S>.yaml` lo traduce
por empresa (ya no hay tabla aparte, véase §1 punto 5). Cada comando nuevo, con su capítulo del manual (regla 8).

## 8 · Frente F — pieza C: actuar desde la app

MetaTracker **no alcanza la VPS ni escribe nada** (`mt5/fleet/app/README.md`). Riesgo por acción (ex 35 §2 C):

| acción | riesgo | entra |
|---|---|---|
| desplegar o cambiar los EAs de una cuenta | bajo: el play sigue siendo del dueño | sí (frente E) |
| crear una instancia nueva, retirar una cuenta quemada | bajo | sí |
| reiniciar un terminal colgado | bajo | sí |
| pausar una cuenta (el EA no abre operaciones nuevas) | medio | **preguntar antes** (K-8) |
| cerrar todas las posiciones de una cuenta | alto, dinero real | **no**, salvo que el dueño lo pida; el MCP de MT5 tiene las órdenes prohibidas a propósito |

Lo mecánico que falta: reabrir un terminal caído (hoy el Linux sólo lo ve por el silencio de su baliza) con
una **tarea programada de Windows** en la VPS, propuesta del encargo original. Va aparte de la app: la app
sigue sin escribir. Que lo ejecute `mt5/fleet/vps/`, desplegado como el resto.

## 9 · Frente H — el exportador de carteras (agente o skill)

El dueño no exportará los `.mq5` a mano: dirá **«me gusta esta cartera, exporta las estrategias»** y un agente
o una skill, por cada estrategia × cuenta de destino:
1. asigna el **magic** del registro (G);
2. pone el **riesgo por operación en USD** que toca al tamaño de la fondeada de destino (cada EA ya trae el
   suyo programado para una fondeada concreta, y **el despliegue no lo toca**; el exportador sí lo fija);
3. pone un **filtro de noticias**, si procede (reutiliza `mt5/newsfilter/`, skill `/ea-news`: ya escribe dos
   EAs por estrategia, `<name>_<Firm>.mq5` y `<name>_NoNews.mq5`);
4. cambia el **comentario** de las operaciones para que salga el nombre de la estrategia (31 caracteres como
   máximo en MT5; hay brokers que lo recortan o sobrescriben: **el magic es la llave, el comentario es para
   leerlo**);
5. **nombra el `.mq5`** de modo que el despliegue sepa para qué fondeada es (K-7).

El bloqueo de `OPEN.md` #78.3 (exportar el `.mq5` sin interfaz) **ya no bloquea**: lo resuelve
`sqx/projects/mt5verify.py`. Lo que sí necesita es el magic (G) y el riesgo por tamaño, que sale del encargo
54 (`docs/encargos/54-fondeo.md`, frentes D-E); no empieces el exportador sin ese número. Primero diseño
(Opus: ¿skill o agente?, qué lee del archivo y de la cartera), después implementación mecánica.

## 10 · Frente I — pieza D: conciliar el vivo contra SQX con la flota

Con el magic de G, cada operación del vivo sabe de qué combinación viene. La conciliación semanal
(`mt5/reconcile/`) existe, pero **lee las cuentas con el terminal de Wine** (`live.accounts`, historial con el
verbo `history` de `mt5/winside/query.py`), no con lo que ya recoge el colector de la VPS en
`AlgoData/fleet/live/<login>.history.json`. **No está alimentada por las 10 cuentas todavía.** Reescribir
contra el código actual: leer `mt5/reconcile/live.py` y proponer (K-9) si la fuente pasa a ser el histórico del
colector (más barato, sin cambiar de cuenta) o se queda el terminal; en cualquier caso `register.csv` es
imprescindible (la conciliación se niega sin él) y lo escribe el dueño (G). Instalar la línea de cron de
`bin/weekly-reconcile.sh` es del dueño (propuesta: sábado 02:10). El agente `weeklyReconciler` sigue pendiente.

## Decisiones del dueño — pregúntalas (regla 11)

**Contestadas por el dueño (2026-10-14)** — lo que sigue manda sobre la lista de abajo:
- K-1b → **1 R = distancia al stop** en las estrategias con stop. K-2 → **M1 del terminal de cada firma**. K-3 → **SQLite**.
- K-4 → **la zona lista todo y marca lo validado**. K-5 → **los 7 EAs vivos se quedan; los nuevos empiezan en 1001 y el asignador genera `register.csv`**.
- K-6 → **lo quita el encargo**. K-7 → **firma + tamaño**. K-8a → **el filtro de `mt5/newsfilter/`**. K-8b → **sale del 54**. K-8c → **fichero de control**.
- K-9a → **el Excel se rellena solo**. K-9b → **la app lee el Excel como lo esperado**. K-9c → **histórico del colector**. K-10 → **cerrar 3389 y 5986** cuando haya dinero real.
- Sigue abierta: K-11 (qué superviviente, fechas y modelo).
- K-11 → **todo el histórico que haya, con ticks reales**. La superviviente, la primera real que salga.


Nada de esto se resuelve con un defecto; cada línea lleva su origen.

- **K-1 (ex 34 §0.5 punto 2).** El «≤ 0,05 R» de la fila 2: ¿R es **la pérdida media de SQX** (lectura de
  hoy, porque las estrategias de la doctrina no llevan stop) o **el riesgo inicial** (el stop, cuando lo
  hay: `Strategy 3.48.75` para a 4×ATR)? ¿Una lectura para todas o según lleve stop?
- **K-2 (ex 34 §1 fila 5).** El drawdown intradía sobre flotante, ¿con M1 de la feed de desarrollo (la que
  ya usa `mt5/reconcile/floating.py`) o con el M1 del terminal de cada empresa? ¿Se cambia el umbral
  `dd_rel_gap_max` (10 %) al pasar de «balance al cierre» a «flotante»?
- **K-3 (ex 34 §4).** Formato del pool: ¿se queda el CSV sólo-añadir por empresa (hoy «propuesto») o pasa
  a SQLite como el catálogo de fondeo, o a otro?
- **K-4 (ex 34 §5.4).** ¿Cómo y dónde se engancha el pool a la cartera? ¿`--firm` filtra por «validada en
  esa empresa»? ¿La zona PORTFOLIOS lista sólo lo validado, o lo validado se marca y se lista todo?
- **K-5 (ex 35 §1 #6 y `live-ea-magic-numbers.md`).** Los EAs en vivo llevan magic 1…7, y el registro
  secuencial desde 1001 no existe: ¿los siete actuales se **renumeran** (cambian en la cuenta y se reescribe
  `register.csv`) o se **conservan** y el registro nuevo arranca en 1001 sin tocarlos? ¿`register.csv` lo
  escribe el dueño o lo genera el asignador?
- **K-6 (ex 34 §0.5 punto 5).** `mt5/symbols.csv` (git-ignorado, 18 activos, ya sin lector): ¿lo retiras tú
  o lo quita el encargo?
- **K-7 (ex 35 §4 #3).** El patrón de nombre que liga un EA a su fondeada, p. ej. `Est17_FTMO100k.mq5`:
  ¿vale para **una empresa y un tamaño** (todas las cuentas de ese tamaño lo comparten) o para **una cuenta
  concreta** (lleva el número de cuenta)?
- **K-8 (ex 35 §4 #4-#6).** (a) **Filtro de noticias**: qué noticias (impacto alto, de qué divisas), qué
  ventana antes y después, qué hace el EA dentro (no abrir, o cerrar también), de dónde sale el calendario.
  `mt5/newsfilter/` ya implementa una lectura por empresa (cierra `close_before`…`rule_minutes` antes,
  no abre entre `block_before` y `block_after`): **confirma que es la que quiere** o dile la otra.
  (b) **Riesgo por tamaño**: qué USD por operación para cada tamaño de cuenta (lo más probable: del
  encargo 54). (c) **Pausar una cuenta**: si entra, cómo (un archivo de control que lea el servicio, o cerrar
  el terminal).
- **K-9 (ex 35 §4 #7 y §2 D).** (a) ¿De dónde se rellena sola la plantilla Excel (requisito del dueño,
  2026-09-29: «ha de rellenarse automáticamente, no a mano»)? Candidatos: las hojas de cuenta (qué EAs lleva
  cada una) desde el exportador de H; la hoja «Cuentas» (empresa, tamaño, fase, estado) desde lo que envía la
  baliza y el catálogo de `portfolio/funded/`. (b) ¿**Sustituye la app al Excel** o el Excel se sigue
  escribiendo para que él lo lea? (`mt5/fleet/app/tab_deploy.py` ya lee el Excel como lo «esperado».)
  (c) La fuente de la conciliación semanal (frente I): histórico del colector o terminal de Wine.
- **K-10 (seguridad).** Ver el AVISO de arriba: ¿cerramos 3389 y 5986 cuando vaya dinero real?
- **K-11 (§1 «Hecho es»).** Para el frente C: qué superviviente, qué Desde/Hasta y qué modelo del tester.

## Lo que sólo vivía en los encargos de origen

- **Decisiones del dueño de la flota (ex 35 §1)**, todas vigentes: #1 se ve en la ventana de su Linux,
  nada de web ni móvil (**matizado el 2026-10-02**: app propia, MetaTracker, no `ui/`); #2 el código vive en
  `mt5/fleet/`, y a la VPS va sólo `vps/`, copiada por un script — ni git ni el repo; #3 símbolo del Excel =
  nombre de SQX, traducido por empresa, un activo ausente **se dice y no se adivina**; #4 **el riesgo por
  operación en USD ya viene en cada EA y el despliegue no lo toca** (sólo le pone el activo y la
  temporalidad del Excel, encontrándolo por el nombre del archivo); #5 el Excel con una hoja «Cuentas»
  (cuenta, empresa, tamaño USD, fase, instancia MT5, estado, notas) y una hoja por cuenta
  (`Activo · Temp. · Estrategia · Magic`, activo y temporalidad con desplegable con los nombres de
  `assets/symbols/`: `USATEC`, `USA500`, `NIKKEI225`, no `NAS100`/`US500`/`NIKKEI`; Magic en gris; fuera la
  hoja de WalkForward y la columna Long/Short: no usará variaciones); #6 el magic, el de §6; #7 el «play»
  es del dueño.
- **Medidas del dueño sobre la RAM de la VPS:** un terminal Hantec con 15 gráficos ocupa ~450 MB, así que
  10 terminales son ~4,5 GB y 15 ~7 GB, más ~3 GB de Windows: caben 15-18 como techo, 12-14 con holgura.
  Medido en la VPS el 2026-10-02: tres terminales abiertos (FTMO, Hantec, MetaQuotes) ocupan 1,4 GB y quedan
  5,8 GB libres de 12; 6 núcleos. La RAM ya no obliga a nada: servicio MQL5 (`FleetBeacon`) más tarea
  programada de Windows. **No pasar la VPS a Linux** (MT5 no tiene versión nativa, bajo Wine no va más
  rápido y con dinero real Windows es la plataforma soportada). Sigue en pie: `knowhow/locations/
  vps-fleet-access.md`.
- **Red:** Tailscale entre las dos máquinas; si se corta, los datos esperan y se envían después. **Datos
  sensibles** (números de cuenta, IP de Tailscale, ruta de cada instancia) en `config/machine.yaml`, que no
  está en git. Semáforo de la zona: 🟢 operando · 🟡 AutoTrading apagado o desconectado · 🔴 cerca del límite
  diario o total de su empresa (los límites los da `portfolio/funded/catalog/`) — ya implementado en
  `mt5/fleet/app/state.py`.
- **Orden de trabajo propuesto en 35 §5**, de lo que queda: (1) tabla de símbolos — ya es `mt5:` — y registro
  de magics (G) → (2) perfil `.chr` validado en el terminal de Wine, en demo (E) → (3) lector del Excel
  (ya lo usa `tab_deploy.py`) → (4) colector y servicio MQL5 (**hechos**) → (5) zona de la ventana
  (**hecha**, MetaTracker) → (6) exportador (H), cuando haya magic y riesgo por tamaño.
- **Idea del dueño del exportador, en sus palabras (2026-09-29):** «me gusta esta cartera, exporta las
  estrategias».
- **Formato de la fila del pool (ex 34 §4)**: identidad y versión del archivo
  (`AlgoData/archive/<identity>/<version>/`), la empresa y su símbolo, el tramo comparado, las cinco cifras,
  los umbrales vigentes, el veredicto y la fecha; el pool es **por empresa** (una estrategia puede valer para
  Hantec y no para FTMO). Las columnas reales están en el CSV (`identity, strategy, project, mother, symbol,
  timeframe, firm, run, verified_on, window_from, window_to, model, verdict, thresholds_hash, config_hash,
  sqx_trades, mt5_trades, clock_h, row_1…row_5, …`).

## Lo que no tocas

- El **master** y su GUI (regla 3); nada de `sqcli` a mano; los workers sólo por `bin/sqx-worker.sh` o el
  propio trabajo (`core.worker`). Todo en un proyecto `Test_`/`Trade_`/`Research_` propio (regla 10): el
  verificador ya crea y retira el suyo.
- **`oos2`**: reservado. El tramo de la verificación lo da el dueño, no se lee por iniciativa del agente.
- **Órdenes de MT5**: ningún código ni petición que envíe, modifique o cierre una orden. Las herramientas de
  trading y de EA/script del MCP de MetaQuotes están denegadas en `.claude/settings.json`.
- Los ficheros de **otros frentes**: `docs/encargos/54-fondeo.md` (riesgo por tamaño), `portfolio/` (sólo
  propones el enganche del pool, K-4), `AlgoData/fleet/Flota_de_cuentas.xlsx` (la plantilla es del dueño; la
  copia de trabajo se pide). `register.csv` es del dueño.
- La VPS: nada se despliega ni se reinicia sin que el dueño lo vea; el play y las contraseñas son suyos.
- `git`: el dueño commitea (regla 12).

## Objetivo — un comando

Done-ness mixta. Los frentes **A** y la parte de código de **B**, **E**, **G** y **H** se verifican con tests
y checks; **C**, **D**, **F** e **I** dependen de una corrida real en SQX/MT5 o de una decisión del dueño, y
se cierran con una lista `Verificación`. El comando cubre lo automatizable:

```
python3 tests/test_mt5verify.py && python3 -m pytest tests/test_fleet_collect.py tests/test_fleet_equity.py tests/test_fleet_floors.py tests/test_fleet_progress.py tests/test_fleet_risk_rules.py -q && python3 tools/depmap.py && python3 tools/checks.py
```

(Hoy sale 1 por el primer eslabón. Si E/G/H crean tests nuevos, súmalos aquí.)

**Verificación (lo que ningún comando prueba):**
1. `python3 -m mt5.verify.pool` muestra al menos una fila `pass` o un `fail` diagnosticado de una
   superviviente real, con su corrida en `AlgoData/mt5/verify/<run>/` (frente C).
2. El dueño ha contestado K-1…K-11 y la bitácora lo dice.
3. Un `grep` muestra que `portfolio/` o la zona PORTFOLIOS lee el pool validado (frente D), o el dueño ha dicho
   que no hace falta.
4. Un perfil `.chr` generado abre en el terminal de Wine con los gráficos y EAs esperados, en demo
   (frente E), con captura en `AlgoData/`.

## Cómo cierras

Qué hiciste · qué verificaste, con la salida pegada de cada comando · qué dejaste sin hacer y por qué · qué
descubriste para `knowhow/` (edita la card existente: `knowhow/mt5/mt5-validated-pool-register.md`,
`knowhow/locations/live-ea-magic-numbers.md`, `knowhow/locations/vps-fleet-access.md`; no añadas al final).
Cada comando nuevo, con su capítulo del manual (regla 8: `AlgoData/manual-fuentes/` y `python3 tools/manual.py`).
Cuando un frente quede entero, bórralo de la tabla de estado y apúntalo en la bitácora con la fecha.
Termina con la lista de ficheros cambiados y, como última línea de tu respuesta: **¿Quieres hacer el commit?**

/loop Lee docs/encargos/55-mt5-paso-26-y-flota.md y ejecútalo entero. Tras cada iteración corre el Objetivo; si sale 0, para el bucle; si no, arregla lo que falló y vuelve a correrlo.
