# 53 · Monos y nulos: el control negativo de la cadena — plan que atraviesa sesiones

**Tu oficio:** control negativo del proyecto. Python para los monos (partes 1, 5 y 6) y SQX en el
custodio para los monos seleccionados y el A/B del hueco (partes 3 y 4). **Opus** para diseño y
estadística (partes 3, 4, 5 y la lectura de todo resultado); **Sonnet** para lo mecánico (la corrida a
10.000, exportar, instalar un fichero ya escrito, regenerar docs) — regla 17.
**Tu encargo:** devolver al dueño **cuántos falsos positivos deja pasar la cadena** (monos sin edge que
llegan vivos a cada paso), con la tasa de cada umbral escrita en `ledger/thresholds.yaml`, y saber si
el hueco aleatorio de las plantillas aporta ventaja o sólo sobreajuste. «Este control casi no discrimina»
es una respuesta válida: dila, con lo que cuesta en estrategias al lado.

Lee `CLAUDE.md` (reglas 1-6, 10, 11, 13-19) · `docs/AgentPDFs/WORKFLOW.md` ·
`studies/screening/falsePositives/README.md` · `studies/readings/monkey/README.md` ·
`engines/nulls/README.md` · `studies/screening/gate/README.md` · `ledger/README.md` ·
`knowhow/research/random-entry-nulls.md` · `knowhow/conditions/no-seeded-hash-in-sqx.md`.

## Estado y bitácora

| # | frente | modelo | depende de | estado |
|---|---|---|---|---|
| 1 | Monos de Python por la cadena (ex-9): pasos 10, 12, 14, 16, 17/18, embudo del 20 | Opus (diseño) | encargos 49, 51, 52 (reglas firmadas de esos pasos); `oos2`: autorización expresa | pasos 6-8 hechos; resto bloqueado |
| 2 | Corrida a 10.000 con `--ledger` y tasa de falsos positivos por umbral en `ledger/thresholds.yaml` (ex-9) | Sonnet | 1 (mejor tras él); ~35 min de CPU | sin hacer |
| 3 | Export de operaciones de la población real vía `orderstocsv` (ex-9 + ex-5 §6.1, fundidos) | Sonnet | `perf/` para medirlo; SQX | sin medir |
| 4 | Monos seleccionados dentro de SQX (ex-30) | Opus + Sonnet | punto 1.4 de `49` y frente 1; cinco preguntas del dueño | sin empezar |
| 5 | Nulos: lo vivo de ex-5 §6 (databank sin condiciones de aceptación, ATR del `.sqx`, `barrier.intrabar`) | Opus | SQX para el 5a; corpus con SL/TP para el 5c | módulo entregado; 3 flecos |
| 6 | El hueco aleatorio a prueba: A/B, atribución, bloque de ruido (ex-28) | Opus + Sonnet | A y C: custodio libre; C: frente 4; varias preguntas del dueño | sin empezar |

**Bitácora** (una línea por sesión: fecha · frente · qué quedó · qué sigue)

- 2026-10-09 · consolidado desde los encargos 9, 30, 5 y 28; nada ejecutado todavía.
- 2026-10-13 · 5c · **medido**: con una vela H1 que toca stop y objetivo (70.066 operaciones largas de 300
  estrategias, `Test_E53_5c_XAUUSD_H1`, precisión «timeframe elegido»), SQX no va «al stop primero»: recorre
  la vela Apertura→Mínimo→Máximo→Cierre si cierra al alza (sale por el **stop**: 41.894 de 41.894) y
  Apertura→Máximo→Mínimo→Cierre si cierra a la baja (sale por el **objetivo**: 25.758 de 25.758); 61,8 % stop
  en total. `pessimistic` falla en el 38 %. No se ha tocado código: la clave `barrier.intrabar` no la lee
  nadie y ningún número publicado depende de ella · sigue: decide el dueño si se borra la clave y se
  escribe la regla de la vela en el motor; sin medir cortos ni velas doji (0,2 %).
  Ficha `knowhow/export/sl-pt-same-bar-convention.md`.
- 2026-10-13 · 5c · B1 = A: clave `barrier.intrabar` borrada con sus citas — nadie la leía y la medida la desmiente; `kernel.touched` se queda, la usa `studies.readings.monkey.verify`; la regla medida está en `knowhow/export/sl-pt-same-bar-convention.md`.

## §0 · De dónde sale

- **Las palabras del dueño (2026-09-23, `WORKFLOW.md`):** «Si de diez mil monos llegan 4 y de diez mil
  tuyas llegan 5, ya sabes lo que vale ese 5.» Y se hace **antes** del primer pase completo de verdad;
  después el número de monos se compara con un resultado ya conocido. **El dueño reabrió el encargo 9 el
  2026-10-04.**
- **Python y no permutaciones (2026-09-24):** el test de Masters (permutar la serie) no es practicable:
  la API de SQX no tiene verbo de import (`knowhow/sqx-drive/project-verb.md`), fabricar símbolos exige
  la GUI del maestro y `user/data/History` está enlazado al del maestro. Los monos de Python responden
  la misma pregunta sin generar una serie. Un build con paleta neutra en SQX «cuesta horas de licencia,
  mide el generador además del filtro y mete en el maestro estrategias que nadie quiere» — y por eso el
  mono sin selección vive en Python.
- **El 2026-09-28 el dueño reabre SQX para monos** (ex-30), tras ver el plugin WinRateEdge: *«Sí, abre
  las dos cosas. Ya tienes además instalado en el SQX master el bloque random.»* Los dos frentes se
  complementan: el 1 pasa monos de Python por los **criterios** de la cadena sin selección; el 4 pasa
  monos de SQX por la **cadena real** con la selección del Builder. **La diferencia entre los dos
  números es lo que cuesta la selección.**
- **Aronson (*Evidence-Based Technical Analysis*, pp. 274-280 y 441-443):** las estrategias de SQX son
  las ganadoras de una búsqueda sobre `build`; un mono sin seleccionar no pasa por esa búsqueda, así que
  su tasa de supervivientes sólo es una **cota inferior** de los falsos positivos. En su libro, la mejor
  de 6.402 reglas sin valor gana un 11 % al año: un test ingenuo da **p = 0,0005**, el Reality Check de
  White **p = 0,82**. (Dossier `docs/AgentPDFs/ideas-de-internet-y-libros-2026-09-27.md`, §1.2.)
- **El hueco aleatorio (ex-28), dossier mismo §1.4 y palabras del dueño de 2026-09-28:** *«Me parecen
  muy buenas ideas las 3, apúntalas en un encargo. La 1 tiene que ir con automatización por parte de
  Claude.»* Chan: los algoritmos genéticos «rindieron miserablemente hacia delante» (*Quantitative
  Trading*, pp. 26-27); Shaw empieza por una hipótesis (*Stock Market Wizards*, pp. 143, 145); Eckhardt:
  sobreajuste = grados de libertad sin información (*New Market Wizards*, p. 48).

### Lo que ya está hecho (no se rehace)

| qué | dónde vive |
|---|---|
| Módulo de nulos de entrada aleatoria: escalera `timing` → `timing_holds` → `timing_sizing` → `free`, reconciliación de fills (`open-open`, 0,999985) | `studies/readings/monkey/`, `engines/nulls/`, manual `26-nulos.md`, `knowhow/research/random-entry-nulls.md` |
| Punto de entrada P1 (observado contra esperado, Storey, Benjamini-Hochberg, detección de muestra preseleccionada) | `engines/inference/excess.py`, `studies/screening/monkeyExcess/report.py` |
| Los monos por la cadena hasta el paso 8, con borde plantado (0,05/0,10/0,15 neto de costes) y cascada apagada | `studies/screening/falsePositives/` (README, sección «Not done»), `tests/test_false_positives.py`, manual `99-monos-por-la-cadena.md` (PDF `05-cribado-oos`), commit `9ea6292`, tarjeta `knowhow/research/monkey-size-carries-donor-volatility.md` |
| Informes ya corridos (escala de 1.000 monos, ~11 proyectos) | `AlgoData/reports/<P>/<D>/<día>/falsePositives/` |
| Bloque aleatorio sin semilla en el maestro | `~/Desktop/SQX/user/extend/Snippets/SQ/Blocks/RandomEntry/` (no en `SQX_w1` ni `SQX_w2`) |

## Parte 1 · El mono de Python en los pasos que faltan (ex-9)

**Lo que ya mide** (lee el README del módulo antes): del paso 8, todas las reglas con la cascada apagada;
**del paso 10 en adelante los monos vivos son un techo, no una medición**, porque un paso no aplicado
deja pasar a todos. Tabla del README, «step | applied to a monkey»:

| paso | hoy | qué falta |
|---|---|---|
| 10 | nada | el mono en los otros mercados: su huella de reentest colocada en las barras de cada mercado (`engines/nulls/placement`, `README.md` ahí). Espera la regla firmada de `51` |
| 12 | nada | los hermanos escalados los fabrica SQX desde parámetros; un mono no los tiene. La regla «nunca falla» de todos modos |
| 14 | nada | el estrés combinado del MC Retest es una tarea de SQX sin modelo en Python: **criterio equivalente sobre sus operaciones**, declarado uno a uno (`49`) |
| 16 | — | no hay regla en `criteria.yaml` |
| 17-18 | — | leen `oos2`. Cita del dueño: *«es su bala»* — **autorización expresa por tarea, nunca supuesta** (regla de `oos2`). Hasta entonces no se corre |
| 19 | — | el WFM es tarea de SQX: se le aplica su criterio, no la tarea |
| 20 | — | el embudo y **cuántos monos llegan al 20** es el número que justifica el frente |

Cada paso que se añada: (a) la regla de `pipeline/autopilot/criteria.yaml` leída tal cual (nunca copiada);
(b) qué condición de la tarea de SQX reproduce y qué parte no puede; (c) su fila en `reglas.csv` con
`nota`. **Sin una sola excepción**: un criterio ahorrado al mono infla su supervivencia, uno aplicado de
más la hunde; las dos direcciones invalidan el control.

Esto acota lo que el estudio mide, y el informe lo dice sin adornos: **mide la mortalidad de nuestros
filtros, no la del generador de SQX**.

Ficheros que posees: `studies/screening/falsePositives/{chain,model,many,inputs,report,tooltips}.py`,
`config.yaml`, `README.md`, `tests/test_false_positives.py`, el capítulo `99-monos-por-la-cadena.md`.
`chain.walk` ya recorre `criteria.yaml` por regla sola y en orden; lo nuevo es cada regla que hoy
no tiene columna de hechos (`applied` en `chain.py` ~l.158 lo señala).

**Dos modos de fallo, siempre presentes**
1. *Una población nula que no es nula:* los diez mil entran enteros, no se criba antes. El símbolo y los
   costes sí; la selección de qué monos entran, no.
2. *Medir el filtro en vez del generador:* `MC_Trades` tenía el 99,9 % de sus 757 con beneficio OOS
   positivo porque desciende de una tarea con tres condiciones sobre `main/OOS`, frente al 26,9 % de la
   databank `OOS` entera (§6bis de ex-5, recogido en la parte 5). Declara de qué databank sale cada
   población y qué condiciones llevaba encima.

**Verificación:** (1) el mono pierde dinero tras costes (con ocupación del 7,4 %: ~2.867 $ capturados de
la subida contra ~7.756 $ de coste; media negativa en el 100 % de las 757) — si la nula gana de media,
le has regalado algo; (2) `studies/readings/monkey/verify.py`, suelo 0,99, pasa antes de leer ninguna p;
(3) el embudo cuadra con el ledger fila a fila.

## Parte 2 · La corrida a 10.000 y la tasa por umbral (ex-9)

1. `python3 -m studies.screening.falsePositives.report --project <P> --databank Results --feed <ACTIVO_M1>
   --ledger --set population.per_level=10000` (~35 min de CPU: 757 estrategias × 4 peldaños × 2.500
   tiradas costaron 2 min 37 s, paralelo porque el sizing no compone sobre el equity). **Nada CPU-pesado
   a su lado** (regla 19) y proyecto que ya exista (regla 10).
2. **Escribir en `ledger/thresholds.yaml`, al final de su sección y leído como `ledger:<clave>`, la tasa
   de falsos positivos de cada umbral** (hoy no hay filas de esto: `grep -n falsePos
   ledger/thresholds.yaml` sale vacío). Cada fila lleva al lado lo que cuesta en estrategias reales.
3. `--ledger` escribe una fila por paso juzgado en el estudio de la población real
   (`studies/screening/falsePositives/report.py:19`, `to_ledger`); los monos son una mirada al segmento
   que `ledger.spend` cuenta, no candidatos.
4. **Cosechas viejas:** las de USDJPY anteriores a 2026-10-01 no reconcilian (0,966-0,988 contra 0,99;
   se exportaron antes de re-reloj de los feeds). Necesitan cosecha nueva en SQX, no se rescatan.

Cierre del frente: el embudo comparado, el número del paso 20 (cuando existan las reglas) y las tasas
escritas. Una decisión, no una descripción.

## Parte 3 · El export de las operaciones de la población real (ex-9 + ex-5 §6.1)

Hoy el módulo corre sobre las 757 de `MC_Trades` (y las cosechas por proyecto). Para 10.000 hay que
exportar las operaciones reales con las que se empareja la huella: ~265 MB de Parquet (nada); lo que no
está medido es **el tiempo de `orderstocsv` en SQX sobre 10.000 estrategias**, lo único sin cuantificar
del plan. Mídelo con `/perf` antes de pedirlo en serio; lo exporta el conductor (`/export`), nunca el
maestro, nunca el custodio entre arranque y recogida (regla 3). El resultado entra en el frente 2.

## Parte 4 · Monos seleccionados dentro de SQX (ex-30)

**Qué es:** poblaciones de estrategias de entrada aleatoria **construidas y seleccionadas por el Builder
de SQX** con la misma selección que las reales, pasadas por la cadena real. Cuántas sobreviven es la tasa
de falsos positivos **con la selección incluida**. Depende de que el frente 1 exista para comparar con
el mono de Python (y del punto 1.4 de `49`).

**El bloque tal como es** (🔬 leído del código el 2026-09-28; ficha en
`knowhow/conditions/no-seeded-hash-in-sqx.md`):

```java
@BuildingBlock(name="(RAND) Random Entry", display="Random Entry (#Probability#%)", returnType = ReturnTypes.Boolean)
public class RandomEntry extends ConditionBlock {
    @Parameter(name="Probability", defaultValue="5", minValue=0.01, maxValue=100, step=0.01)
    public double Probability;
    public boolean OnBlockEvaluate() throws TradingException { return Math.random() * 100 < Probability; }
}
```

Dispara en cada barra con probabilidad `Probability` %. **`Math.random()` no tiene semilla:** dos
backtests de la misma estrategia dan operaciones distintas. El plugin trae también un panel para el
Retester que no hace falta (su prueba es una z sobre la tasa de acierto, más débil que la escalera del
mono del proyecto). Copia fuente: `~/Downloads/codebase-strategy-vs-random-edge-testing-winrateedge-results-panel/RandomEntries-1.sxp`.

**Lo que la falta de semilla rompe y lo que no** (sólo vive aquí)
- *No rompe el control:* un mono seleccionado se eligió por un `build` con suerte; su retest en `oos1`
  es una tirada nueva e independiente, que es justo la hipótesis nula. La cadena lo debe matar al ritmo
  del azar.
- *Sí rompe todo paso que vuelva a correr el `build`:* MC Retest, SPP, variantes y la ablación del 23 no
  reproducen el `build` seleccionado; para un mono cada uno es otra tirada. El informe lo dice paso a
  paso. *Sí rompe la reproducibilidad* de los informes desde su manifest.

**Lo que se construye** (todo por hacer; verificado hoy: no existe `sqx/blocks/snippets/` — `sqx/blocks/`
tiene `install.py`, `palette.py`, `taxonomy*.py`, sin snippets —, ni test, ni capítulo, ni familia
`mono_sqx` en el ledger; `SQX_w1/w2` sólo tienen `Comparisons` e `Indicators` en `Snippets/SQ/Blocks`)

1. **`RandomEntrySeeded`** en `sqx/blocks/snippets/RandomEntrySeeded/` (con README; sitio a confirmar
   según `sqx/CLAUDE.md`): `Math.random()` se cambia por un número que sale de mezclar un parámetro `Seed`
   con la hora de la barra, con SplitMix64 (aritmética entera de 64 bits de Java, ~10 líneas). Mismo
   backtest = mismas operaciones; `Seed` es un grado de libertad puro sin información (es el bloque de
   ruido del frente 6c). Las plantillas `.tpl` de MT4/MT5 no importan: un mono nunca va a MetaTrader.
   Si el Builder deja a la búsqueda mover `Seed`, seleccionar semillas con suerte **es** la selección que
   se quiere medir. **Test de Python** que reproduce el mezclador y comprueba la frecuencia de disparo
   sobre barras reales (con probabilidad p, la fracción de barras con entrada dentro del intervalo
   binomial de p).
2. **Instalación en el worker**, con el worker parado y el protocolo de las reglas 1-3
   (`.claude/skills/sqx-wait/preflight.sh`: `ListAgents`, proyectos recientes, cola del log del día).
   Copia a `user/extend/Snippets/SQ/Blocks/<Bloque>/`, arranca con `bin/sqx-worker.sh` y comprueba con
   `python3 -m sqx.inspect.vocabulary --diff custodian`. 🤔 **Sin probar** cómo compila SQX un snippet
   sin GUI: si el bloque no aparece, **para y pregunta** (puede exigir compilar en la GUI, que es del
   dueño). Lo que descubras va a `knowhow/conditions/no-seeded-hash-in-sqx.md` (edítala, no añadas).
   Con el conductor si hace falta para retests cortos; el maestro no se toca.
3. **Reproducibilidad antes de nada más:** el mismo retest dos veces, operación a operación (el sin
   semilla dos veces: distintas). Si el de semilla no se reproduce, no sigas.
4. **Builds de monos**, uno a uno en el custodio, proyecto propio `Test_monos_<activo>_<TF>_<n>`
   (regla 6) con `sqx.projects.builder` (regla 10) y **lo mismo que la población real que controla**:
   activo, timeframe, ventanas, costes de `assets/`, salidas de `assets/_build.yaml`, función de
   aptitud, filtros de aceptación, tamaño de la databank. La única diferencia: la condición de entrada
   es el bloque aleatorio y nada más (sin hueco ni otra condición: «un mono con un indicador al lado ya
   no es un mono»). Entre arranque y recogida sólo `-project action=status`; la espera es **un** comando
   en segundo plano (`/sqx-wait`, regla 18).
5. **Retest `oos1`, cosecha y puerta** con `/oos-gate` y el mismo `config.yaml` de la real.
6. **Ledger:** filas con la familia `mono_sqx` y marca de población nula, para que nunca se mezclen con
   las reales en un recuento de supervivientes. Hoy `ledger/study.py` identifica el estudio por
   (símbolo, marco, familia) y `COLUMNS` no tiene marca de nula: añade la columna con su contrato o
   usa la familia, y dilo.
7. **Informe** en `AlgoData/reports/…/monosSQX/` con la forma de `core/study/CONTRACT.md`: el embudo de
   los monos de SQX al lado del de la población real y del de los monos de Python (frente 1).
8. **Limpieza:** `python3 -m sqx.projects.retire <P> --role <rol> --yes` con el worker parado.
9. **Manual:** capítulo en `AlgoData/manual-fuentes/` con capturas reales y su familia en `tools/manual.py`
   (regla 8); tarjeta `knowhow/` con la instalación y la tasa que salga.

**Qué puede mover la búsqueda.** Sin semilla, sólo la probabilidad y los parámetros de salida; con
semilla, también la semilla. Nada de eso tiene información del precio futuro salvo **cuánto tiempo pasa
dentro del mercado**: en el oro alcista, un mono que opera y aguanta mucho gana por deriva. No es un fallo
del control: es la exposición que también pueden capturar las reales, y la puerta debe verla igual.

**Verificación:** (1) el `oos1` medio de los monos seleccionados se parece al de monos sin seleccionar;
si rinden más fuera, algo se transfiere y lo más probable es la deriva — dilo con números; (2) el mono
pierde dinero tras costes; (3) el bloque dispara a la frecuencia que dice; (4) el embudo cuadra con el
ledger fila a fila.

## Parte 5 · Nulos: lo que sigue vivo de `5-nulos` §6

Entregado (ver tabla de arriba). Se llevan sólo los flecos; el ítem 5 de §6 está muerto (issues 71 y 72
cerrados, `docs/OPEN-closed.md`) y no se arrastra.

- **5a · Una databank SIN las tres condiciones de aceptación sobre `main/OOS`.** `monkeyExcess/report.py`
  corrido sobre `MC_Trades` salta el aviso de preselección: el exceso ahí mide el filtro, no el generador.
  Hace falta una databank sin esas condiciones (`AnnualPctReturn(OOS) > 0`, `AnnualPctReturn(OOS) >
  AnnualPctReturn(IS)`, `DrawdownPct(OOS) < DrawdownPct(IS)`) —es decir, una corrida en SQX— y correr
  `python3 -m studies.screening.monkeyExcess.report` sobre ella. El detector se apoya en los datos, no en
  la configuración: la databank se llenó cuando se llenó.
- **5b · El período del ATR desde el `.sqx`.** Estado verificado hoy: `engines/nulls/windowed.py` ya
  recalcula `c / atr[enter]` en el peldaño con sizing emparejado (`atr_sized`, l.24-42), pero con el ATR
  **del motor**: `engines/nulls/config.yaml:25` `barrier.atr_bars: 14`, y el propio docstring dice «the
  ATR period is the engine's, not the strategy's». Lo que falta es leer el período del `.sqx` de cada
  estrategia (la tarjeta `random-entry-nulls.md:26` dice que vive ahí). Medida de partida: `CV(Size ×
  ATR)` 0,384 en bruto → 0,200 con ATR(14) → 0,119 con ATR(50); nunca llega a 0 (la familia está
  identificada, los parámetros no). Tarea: leer el período del `.sqx`, pasarlo a `calibrate.atr`, y
  re-medir ese CV; si no baja, dilo. Reescribir contra el código actual: ex-5 hablaba del peldaño
  «con sizing emparejado» antes de que `windowed.py` existiera.
- **5c · Calibrar `barrier.intrabar` cuando haya un corpus con SL/TP.** El escaneo está probado contra un
  bucle explícito (0 discrepancias en barreras sintéticas), pero qué barrera gana cuando una vela toca las
  dos no se lee de un corpus sin barreras. Aviso ya cableado en `engines/nulls/verdict.py:88`. No hay nada
  que hacer hasta que exista ese corpus.

## Parte 6 · El hueco aleatorio a prueba (ex-28)

Cada plantilla es la condición fija del dueño (la hipótesis) más un hueco que SQX rellena (minería).
Pregunta: ¿el hueco trae supervivientes reales o ruido que la cadena debe matar? Estado verificado hoy:
no existe `.claude/skills/ab-hueco`, ni `sqx/experiments/`; `ledger/study.py` tiene `family` en la
identidad del estudio pero ninguna columna `arm`. **Orden recomendado (ex-28): B primero** (sólo Python,
sobre datos que ya existen), luego A, y C usando A como motor. A y C necesitan el custodio libre.

**6b · Atribución fija contra hueco (paso 23, diagnóstico, nunca selección).** `studies/readings/structure/`
ya hace una ablación por condición de entrada y mide su ΔM por operación contra un recorte al azar
(`measure.py`, `README.md:4`). Falta saber **cuál es la fija**: etiquetar cada condición como `fija` o
`hueco` comparando con la plantilla de origen (`sqx/templates/holes.py` separa `holes` de `fixed`, l.17 y
~l.66); una fila de cabecera por superviviente («de la ventaja medida, tanto viene de la fija y tanto del
hueco», con los ΔM que ya calcula); y en el ledger la misma cifra por familia.

**6a · El A/B, automatizado por una skill `/ab-hueco`.** Dos brazos idénticos salvo el hueco —**A · fija**
(la plantilla sin `RandomCondition`) y **B · fija + hueco** (la plantilla tal cual)—, mismo activo,
ventanas, costes, filtros, aptitud y presupuesto; cada brazo y repetición en su proyecto
(`Test_ab_<plantilla>_A_<n>`, `…_B_<n>`), alternando A y B, nunca los tres de un brazo seguidos. Por
brazo y repetición, tras retest `oos1`, cosecha y puerta: generadas y aceptadas · supervivientes de la
puerta · **exceso sobre el mono** (`engines/inference/excess.py`) · **exceso por hora de CPU** (la cifra
que decide) · distintas (agrupadas por solape de operaciones; 45 de 231 ya salieron idénticas una vez).
El informe no decide: pone los dos brazos lado a lado, con intervalos, y dice si la diferencia supera la
variación entre repeticiones. La skill, en `.claude/skills/ab-hueco/` con orquestador en
`sqx/experiments/ab_hole.py` (o donde encaje según `sqx/CLAUDE.md`), hace sin intervención y es
**reanudable** (como `pipeline/`): preflight `python3 -m core.assets <SÍMBOLO>` (regla 5; si no sale 0,
para y pregunta) y lectura de `runs.csv` · gemela sin hueco, registrada como variante de prueba con su
procedencia · proyectos con `sqx.projects.builder` · builds uno a uno en el custodio con el protocolo de
las reglas 1-3 (espera y avisa si otra sesión lo usa; arranque/parada sólo con `bin/sqx-worker.sh`;
espera con `/sqx-wait`) · retest y cosecha · puerta con el mismo `config.yaml` · ledger (`family` +
`arm` A/B + repetición; añadir la columna con su contrato) · informe en `AlgoData/reports/…/abHueco/` ·
retirar los `Test_` con el worker parado. **Reescribir contra las reglas posteriores:** ex-28 habla de
«pulso cada ~3 minutos»; hoy manda la regla 18 (un comando, un aviso). Ver preguntas 8-11 abajo.

**6c · El bloque de ruido.** Un bloque que no puede tener información sobre el precio futuro, en el hueco
o como única condición fija de una plantilla de control. El vocabulario sólo compone coma flotante (sin
hash entero con semilla): el candidato 0 es **`RandomEntrySeeded`** del frente 4, cuyo `Seed` es un grado
de libertad puro (el RAND sin semilla es otra cosa: un filtro al azar que se sortea de nuevo en cada
retest, útil como variante secundaria: ¿deja pasar la cadena una estrategia con un filtro al azar?). Si
el snippet no se compila en el worker, el ruido tiene que ser un reloj irrelevante y determinista, en
este orden: (1) reloj de periodo optimizable «barra mod P = r»; (2) fase lunar con `FLOOR` y división;
(3) último dígito del precio (casi ruido, no del todo: sólo si los dos primeros son imposibles, y dilo).
⚠️ Las opciones (1) y (2) **leen la hora o el calendario** y chocan con la regla 15: ver pregunta 10.
**Prueba de que es ruido, antes de usarlo:** la tarjeta de información sobre las barras de `build` —su
disparo no puede predecir el rendimiento siguiente; con su p en el informe. Variantes: la plantilla con
el ruido en el hueco; una plantilla cuya única condición fija es el ruido; un barrido de complejidad
(ver pregunta 9). Lo que se mide: cuántas llegan vivas a la puerta, a `oos1` y, si llegan, al paso 20.
Cada superviviente con ruido es un falso positivo de la cadena con nombre y apellidos; la curva
supervivientes contra número de condiciones dice cuánto compra un grado de libertad falso.

**Verificación (parte 6):** (1) el brazo A no lleva hueco: `sqx/inspect/template_check.py` sobre la
gemela da cero `RandomCondition`, y tras el build las estrategias llevan el bloque fijo (lo que ya
comprueba `/template-run`); (2) el ruido es ruido (p de la tarjeta de información en el informe); (3) las
repeticiones difieren (si las tres de un brazo dan lo mismo, la semilla no cambia y no valen); (4) el
ledger cuadra fila a fila. Cierre: capítulo de manual para `/ab-hueco` y el bloque de ruido,
`python3 tools/skillmap.py`, tarjeta `knowhow/` con el primer A/B y el barrido.

## Decisiones del dueño — pregúntalas (regla 11)

Ninguna se responde por defecto; las «propuestas» son lo que los encargos de origen sugerían, no una
decisión.

1. **(ex 30, §4.1) ¿Con o sin semilla?** Propuesta de origen: con semilla para todo (reproducible), y
   el bloque sin semilla sólo como comprobación de que los dos dan la misma tasa.
2. **(ex 30, §4.2) ¿Probabilidad fija o libre?** Libre deja a la búsqueda elegir frecuencia y
   exposición, como con las reales; fija en la frecuencia media de la población real mide sólo la
   suerte. Propuesta: libre, dentro del rango de frecuencias de la real.
3. **(ex 30, §4.3) ¿Cuántos builds de monos por población real?** Propuesta: tantos como builds tuvo la
   real, con el mismo tiempo cada uno.
4. **(ex 30, §4.4) ¿Hasta dónde llegan en la cadena?** Propuesta: primero `oos1` y la puerta; si
   sobrevive alguno, por los pasos de SQX hasta donde la política deje.
5. **(ex 30, §4.5) ¿Qué activo y qué población real se controlan primero?** Además: **¿largo o corto?**
   Un mono es una plantilla y la regla 13 exige una dirección por plantilla. Y **¿qué familia de idea?**
   (regla 15: nunca la paleta entera; un mono no tiene familia — ¿se corre una vez por dirección?).
6. **(ex 9, 2026-10-04) ¿Autorizas a los monos a mirar `oos2` (pasos 17-18)?** Es «su bala»: por tarea,
   expresamente. Mientras no, los pasos 17-18 quedan fuera del embudo, declarado como techo.
7. **(ex 9) ¿Qué criterio equivalente para los pasos que son tarea de SQX** (14 MC Retest, 19 WFM): qué
   condición se reproduce y cuál se da por no reproducible? Depende de las reglas firmadas en `49`/`52`.
8. **(ex 28, §2.3) ¿Presupuesto igual del A/B?** Mismo tiempo de reloj (`--minutes`) o mismo número de
   estrategias generadas. Con el mismo tiempo A genera muchas más (espacio pequeño). Propuesta de
   origen: mismo tiempo, porque la pregunta es qué da más por hora de máquina.
9. **(ex 28, §2.3 y §4) ¿Qué hacer si el brazo A agota su espacio** (sin hueco puede repetir la misma
   estrategia)? ¿Cuántas repeticiones por brazo (propuesta 3)? ¿Qué plantilla primero (propuesta: una
   `buildConfirmed` de `AlgoData/templates/registry.csv`)? **Y el barrido de complejidad 2, 4, 6, 8
   condiciones choca con la regla 14** (como mucho 2 de entrada y 2 de salida, contando por hueco):
   ¿se acota a 1-2 condiciones por lado, o el dueño exceptúa expresamente este control?
10. **(ex 28, §4) ¿Qué ruido, dada la regla 15?** El reloj «barra mod P» y la fase lunar leen
    reloj/calendario, prohibidos en cualquier generación. Opciones: (a) sólo `RandomEntrySeeded`; (b) el
    dueño exceptúa el control; (c) el dígito del precio. Además: ¿las plantillas con ruido pasan por los
    pasos caros (9-20) o se cortan en `oos1`? Propuesta de origen: hasta `oos1`, y más allá sólo si
    sobrevive alguna.
11. **(ex 28, regla 14 sobre A/B) ¿El brazo A, con una sola condición fija y sin hueco, es una plantilla
    legítima** o es un caso que la regla 14 trata distinto (sin hueco no hay minería de entrada: sólo
    se mueven las salidas)? Y en B, 1 fija + 1 hueco = «What to build» 0..1 en ese lado: ¿confirmas?

## Lo que no tocas

- El **maestro** (5050): ni se construye ni se instala nada ahí; su `RandomEntry.java` es una copia de
  lectura. Su configuración de tareas es del dueño.
- **`oos2`** salvo autorización expresa del dueño para esa tarea (los pasos 17-18 del mono, pregunta 6).
- Los **ficheros de otros frentes**: `pipeline/autopilot/criteria.yaml` se lee, nunca se edita para pasar
  un paso (regla 19); `studies/screening/gate/`, `studies/readings/structure/` sólo con el cambio mínimo
  que pida la parte 6b. `docs/DEPENDENCIES.md` se regenera, no se fusiona; `ledger/thresholds.yaml`
  sólo gana filas al final de su sección.
- **Regla fija del dueño:** los nulos de trader al azar y el PSR/benchmark se leen **sólo en el OOS del
  principal o en los mercados adicionales, nunca en el IS**; la escalera de atribución puede mirar el IS
  (potencia), la puerta no. (`knowhow/research/random-entry-nulls.md`.)
- Ningún paso a mano: el workflow corre por `bin/workflow.sh` (regla 19); un build o retest de mono es
  un proyecto `Test_` propio (reglas 6 y 10) y se retira al acabar. Nada de `git commit`.

## Objetivo — un comando

Los frentes 1 y 2 acaban en un comando; el resto no puede (depende del dueño o de una corrida de SQX).

```
python3 tools/depmap.py && python3 tools/checks.py && python3 -m pytest tests/test_false_positives.py tests/test_nulls_seed.py -q
```

(sale 0 sólo si el código de los monos sigue verde y el capítulo del manual los nombra; **no** prueba que
las tasas estén escritas). `Verificación` del encargo entero, a mano:

- [ ] `grep -n falsePos ledger/thresholds.yaml` devuelve las tasas por umbral (frente 2).
- [ ] El informe de 10.000 existe bajo `AlgoData/reports/<P>/<D>/<día>/falsePositives/` con su manifest.
- [ ] Embudo comparado y número del paso 20 entregados al dueño (frente 1).
- [ ] Snippet con semilla: test de mezclador y frecuencia en verde; `vocabulary --diff custodian` lo
      muestra; el mismo retest dos veces da las mismas operaciones (frente 4).
- [ ] `ls .claude/skills/ab-hueco` y su capítulo de manual; el primer A/B con tabla A contra B (frente 6).
- [ ] 5a/5b/5c cerrados o dejados por escrito con el motivo.

No hay línea `/loop`: el objetivo no es un comando real que cubra el encargo entero.

## Cómo cierras

1. **Qué hiciste**, por frente, con la tabla de estado actualizada y una línea nueva en la Bitácora.
2. **Qué verificaste**, con la salida pegada (tests, `checks.py`, la reconciliación del mono).
3. **Qué dejaste sin hacer y por qué** (un paso bloqueado por reglas sin firmar, `oos2` sin permiso, la
   corrida pendiente de CPU libre).
4. **Qué descubriste para `knowhow/`**: edita la tarjeta que exista (`random-entry-nulls.md`,
   `no-seeded-hash-in-sqx.md`, `monkey-size-carries-donor-volatility.md`); nada de apéndices.
5. Capítulo de manual de cada comando nuevo (regla 8); `python3 tools/depmap.py && python3 tools/checks.py`.
6. Lista de ficheros cambiados y, como última línea: **¿Quieres hacer el commit?**

## Lo que sólo vivía en los encargos de origen

- **Por qué el test de Tinsley no se implementó tal cual (ex-5 §1):** su generador es sintético (±1R,
  p = 0,5, media cero); comparado con su propio generador al 55/45 es impecable y «~600 operaciones para
  ver un edge del 10 % con potencia del 80 %» es correcto: **es un estudio de potencia**. Con una
  estrategia real deja de valer: las operaciones no son apuestas justas y el oro no es driftless. De ahí
  que **el null sea un mono con tu mismo conjunto de oportunidades**, no una moneda. El principio:
  *lo que le dejas fijo al null, se lo regalas*; la diferencia entre peldaños es lo que valía ese canal.
- **Las dos veces que se equivocó ex-5 (§3):** (1) se supuso que el mono heredaría la deriva del oro y
  sería el listón duro: falso, pierde en el 100 % de las 757; batir al mono es un listón **más bajo**
  que batir a cero. (2) Se concluyó que MinTRL hacía redundante al mono: artefacto de elegir el Sharpe,
  invariante de escala. Por operación, estrategia/mono: desviación 491/661 $ (36 % más volátil), skew
  +0,53/−0,78, curtosis 6,4/27,0. Con otro estadístico el veredicto se mueve entre 40 y 85 puntos de la
  misma simulación (tarjeta, línea 30): `dd` 84,5 % · `sharpe` 77,4 % · `retdd` 76,9 % · `pf` 55,2 % ·
  `net` 39,5 %. **La elección del estadístico decide el veredicto más que la del null**; el módulo
  imprime cinco y no elige. Contra MinTRL (202/757 = 26,7 %): con `sharpe` contención total, con `net`
  se cruzan (48 pasan MinTRL y fallan el mono, 145 al revés).
- **El hallazgo que salvó el estudio (ex-5 §4):** la puerta de reconciliación saltó con 0,87-0,91 contra
  un suelo de 0,99: SQX rellena a la apertura de la vela, entrada y salida; `open-open` reconcilia a
  1,0000 y la segunda mejor convención a 0,9629. Con el fill equivocado `net` daba 21,5 % en vez de
  39,5 %. Por eso `calibrate.convention()` mide el relleno por estrategia.
- **Dónde encaja el nulo en el flujo (ex-5 §5), no recogido en la tarjeta (`grep P0` no da nada ahí):**
  se evaluaron cinco sitios; el dueño eligió **P1**, tras el OOS sobre la población (corre antes de que
  el pipeline arranque, así lo que muere no gasta `sppultra` ni las 5.000 variantes; es el único sitio
  con cantidades de población). **P2** (`pipeline`, antes de `sppultra`: tres líneas `must:` en
  `recipe.yaml` reusando el módulo) cuando P1 haya fijado el umbral. Descartados: **P0** (generación IS:
  null contaminado, `M` desconocido), **P3** (sobre las 5.000 variantes: una vecindad de parámetros de
  una estrategia con edge no es un mono; ya lo contestan `sppUltra` y `walkForwardCorrelation`), **P4**
  (portfolio: aleatorizar una cartera es otro objeto, se diseña cuando exista).
- **Muestras (ex-5 §5):** la puerta corre sobre `oos1` y sólo `oos1`; la escalera de atribución puede
  correr también sobre IS (potencia y porque la selección infló el nivel pero no de qué canal venía el
  edge). `oos2` no se toca: `assets/_policy.yaml` lo reserva a WFC/WFM y cada mirada lo gasta.
- **Hallazgo 6bis de ex-5:** cadena del proyecto XAUUSD: `#1 Build→Results` 25 condiciones (0 sobre
  main/OOS) · `#2 Retest→OOS` 24 (3 sobre main/OOS) · `#4 Retest→MC Trades` 21 (0). `MC_Trades` tiene el
  99,9 % de sus 757 con beneficio OOS positivo; el export de la databank `OOS` (10.000 filas,
  2026-09-03), el 26,9 %.
- **Decisión del dueño (2026-10-07), no en este encargo pero vigente:** el borde plantado es neto de
  costes y el sizing del mono es `atr` (el de la doctrina, nunca los lotes del donante); ambas cosas y
  sus cifras (R3 pasa 0,9 % de la nula, 13,2/33,8/62,0 % de las plantadas) viven en
  `studies/screening/falsePositives/README.md`.
- **Costes ya medidos (ex-9 §4):** 757 × 4 peldaños × 2.500 tiradas = 2 min 37 s; a 10.000, ~35 min.
