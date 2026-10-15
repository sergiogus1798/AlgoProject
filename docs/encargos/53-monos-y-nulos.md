# 53 · Monos y nulos: el control negativo de la cadena — plan que atraviesa sesiones

> **PARADO POR EL DUEÑO (2026-10-14).** No se empieza ningún frente, ni se corre nada, hasta que él lo
> diga. Texto reescrito el 2026-10-15 contra el encargo 65 para que siga valiendo cuando se reanude.

**Tu oficio:** control negativo del proyecto. Python para los monos (frentes 1 y 5) y SQX en el
custodio para los monos seleccionados y el A/B del hueco (frentes 4 y 6). **Opus** para diseño y
estadística (frentes 4, 5, 6 y la lectura de todo resultado); **Sonnet** para lo mecánico (la corrida,
instalar un fichero ya escrito, regenerar docs) — regla 17.
**Tu encargo:** devolver al dueño **cuántos falsos positivos deja pasar la cadena** (monos sin edge que
llegan vivos a cada paso que juzga sin `oos2`), con la tasa de cada paso escrita en
`ledger/thresholds.yaml`, y saber si el hueco aleatorio de las plantillas aporta ventaja o sólo
sobreajuste. «Este control casi no discrimina» es una respuesta válida: dila, con lo que cuesta en
estrategias al lado.

Lee `CLAUDE.md` (reglas 1-6, 10, 11, 13-19) · `docs/AgentPDFs/WORKFLOW.md` ·
`docs/encargos/65-consenso-cuatro-opiniones.md` (bloque B, §5.0-5.4) ·
`studies/screening/falsePositives/README.md` · `studies/readings/monkey/README.md` ·
`engines/nulls/README.md` · `ledger/README.md` · `knowhow/research/random-entry-nulls.md` ·
`knowhow/conditions/no-seeded-hash-in-sqx.md` · `docs/AgentPDFs/criterios-paso-08-corrida-nula-2026-10-12.md` §4.

## Lo que cambió con el encargo 65 (manda sobre todo lo de abajo)

- **El paso 8 es una sola z:** la de la estrategia sobre su **mono con horas** (sorteado sólo en las
  horas en que entra la estrategia; `engines/nulls/windowed.py`, `studies/screening/gate/level3c.py`)
  ≥ Φ⁻¹(1 − α/B), **α 0,01** (dueño, 2026-10-15, P8-Z → C), B = lotes cribados en `oos1` en la celda
  (activo × TF × dirección × familia). Regla «z del mono con horas, por celda» en
  `pipeline/autopilot/criteria.yaml`; las demás reglas del 8 juzgan o son columnas según ese fichero,
  que se lee tal cual. El limbo sigue (P8-L → A); `edge_mean_oos` no se endurece (P8-E → A).
- **El ledger cuenta por celda y sella el 8** (65 §5.1): un `Test_` cuenta igual que un `Trade_`.
- **La corrida nula del paso 8 ya está hecha** (65 fila 5.4, 2026-10-15): 5.000 monos de 100 donantes
  de `Test_USATEC_H1_ruptura_leaseWeb` (cosecha del build entero,
  `AlgoData/harvest/Test_USATEC_H1_ruptura_leaseWeb/Results/_aparte/2026-10-11.090924`). Con α 0,05
  sobrevive el **4,8 %** de la nula; con α 0,01, medido en mitades partidas, **0,78 %** (techo 1,06 %),
  plantas 0,05/0,10/0,15 → 23/57/80 %.
- **Pasos 14 y 18 son columnas** (no juzgan); el **10** juzga con P1-P6 de `criteria.yaml` (P3 = z
  conjunta sobre V0 + V2, signo por familia); `oos2` se lee en 17, 19, 19.5 y 20; el 18.5 se juzga
  sobre `build+oos1` pero lee el `descuadre_sqx` de las variantes. Comprueba todo esto en
  `criteria.yaml` al reanudar: lo que diga el fichero ese día es lo que se aplica al mono.

## Estado y bitácora

| # | frente | modelo | depende de | estado |
|---|---|---|---|---|
| 1 | Monos de Python por la cadena: paso 10 y la corrida 8 → 10 a α 0,01, con su tasa por paso en `ledger/thresholds.yaml` | Opus (diseño) + Sonnet (corrida) | regla del 10 estable (encargo 51); ~10 h de CPU sin nada pesado al lado | paso 8 hecho (65 fila 5.4); resto parado |
| 2 | ~~Corrida a 10.000 y tasa por umbral~~ | — | — | **quitado**: la corrida a escala la hizo 65 fila 5.4 (5.000 por población); la tasa por paso pasa al frente 1 |
| 3 | ~~Export de operaciones de la población real~~ | — | — | **quitado**: la cosecha del paso 8 ya exporta las operaciones de toda la población (`knowhow/export/orderstocsv-slow-is-datamanager.md`) |
| 4 | Monos seleccionados dentro de SQX (ex-30) | Opus + Sonnet | punto 1.4 de `49` | parado |
| 5 | Nulos: 5a (exceso sobre una cosecha sin preselección) y 5b (ATR del `.sqx`) | Opus | — (sólo Python) | 5c cerrado; 5a y 5b parados |
| 6 | El hueco aleatorio a prueba: A/B y bloque de ruido (ex-28) | Opus + Sonnet | custodio libre; frente 4 para el ruido | parado |

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
- 2026-10-13 — **5c a precisión de 1 minuto** (las mismas 300 estrategias, `Test_E53_5c_M1_XAUUSD_H1`, retirado): 🔬 a 1 minuto SQX sigue el camino de M1 (99,45 % de 70.201 operaciones con las dos barreras en la vela H1 de salida) y, si una sola vela de M1 contiene las dos, decide por el sentido de esa vela (268 de 268). La regla del sentido de la vela H1 cae al 78,8 %. De precisión 1 a 2 cambia la salida del 5,4 % de las operaciones y el beneficio neto baja en el 73,7 % de las estrategias (mediana −890 $). Un corpus de referencia para comportamiento intrabar se retestea a `testPrecision=2`; la precisión del workflow no se toca.
- 2026-10-14 · todo · **parado por el dueño**: no se empieza hasta que él lo diga.
- 2026-10-15 · el dueño contestó la pregunta 12 → B (recomendación): los controles (monos de SQX y brazos A/B) van a una celda propia y se juzgan con el B congelado de la celda real que controlan; no suman a la real. Sigue parado.
- 2026-10-15: reescrito contra el 65 (fila 5 del orden). Quitados los frentes 2 y 3 (los hizo el 65 y
  la cosecha del 8), el 5c (cerrado el 13) y la atribución 6b (su estudio de ablación se borró con los
  pasos 22-25, commit `443315f`); el frente 1 se reduce al paso 10; pregunta 12 nueva (contador por celda).

## §0 · De dónde sale

- **Las palabras del dueño (2026-09-23, `WORKFLOW.md`):** «Si de diez mil monos llegan 4 y de diez mil
  tuyas llegan 5, ya sabes lo que vale ese 5.» Y se hace **antes** del primer pase completo de verdad;
  después el número de monos se compara con un resultado ya conocido. **El dueño reabrió el encargo 9 el
  2026-10-04.**
- **Python y no permutaciones (2026-09-24):** el test de Masters (permutar la serie) no es practicable:
  la API de SQX no tiene verbo de import (`knowhow/sqx-drive/project-verb.md`), fabricar símbolos exige
  la GUI del maestro y `user/data/History` está enlazado al del maestro. Los monos de Python responden
  la misma pregunta sin generar una serie.
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
| Mono con horas: el juez del paso 8 | `engines/nulls/windowed.py`, `studies/screening/gate/level3c.py` (65 §5.0, §5.2) |
| p por estrategia (fdr local) del paso 8 | `engines/inference/localfdr.py` (65 §5.3) |
| Los monos por la cadena hasta el paso 8, con borde plantado (0,05/0,10/0,15 neto de costes), y la corrida nula a escala | `studies/screening/falsePositives/`, `tests/test_false_positives.py`, manual `99-monos-por-la-cadena.md` (PDF `05-cribado-oos`), dossier `criterios-paso-08-corrida-nula-2026-10-12.md` §4 |
| Regla de la vela que toca stop y objetivo (5c) | `knowhow/export/sl-pt-same-bar-convention.md` |
| Bloque aleatorio sin semilla en el maestro | `~/Desktop/SQX/user/extend/Snippets/SQ/Blocks/RandomEntry/` (no en `SQX_w1` ni `SQX_w2`) |

## Frente 1 · El mono de Python más allá del paso 8 (ex-9)

**Qué queda.** El paso 8 ya se mide (arriba). De los pasos siguientes, sólo el **10** puede aplicarse a
un mono de Python; los demás se declaran techo en el informe, y el informe lo dice paso a paso:

| paso | aplicado al mono | por qué |
|---|---|---|
| 10 | **por hacer** | su huella de retest colocada en las barras de cada mercado (`engines/nulls/placement/`, su `README.md`) y las reglas P1-P6 de `criteria.yaml` sobre esos hechos |
| 11.5, 16, 16.5 | — | sin reglas en `criteria.yaml` |
| 12 | techo | los hermanos escalados los fabrica SQX desde parámetros; un mono no los tiene. La regla no falla nunca de todos modos |
| 14, 18 | — | columnas, no juzgan (65 §3) |
| 18.5 | techo | lee las variantes del 16.5 (`descuadre_sqx`); un mono no tiene parámetros que variar |
| 17, 19, 19.5, 20 | fuera | leen `oos2`: **los monos no miran `oos2`** (dueño, 2026-10-14, pregunta 6) y del 19 no se reproduce nada (pregunta 7) |

Cada regla que se añada: (a) leída de `criteria.yaml` tal cual, nunca copiada; (b) qué condición
reproduce y qué parte no puede; (c) su fila en `reglas.csv` con `nota`. **Sin excepción**: un criterio
ahorrado al mono infla su supervivencia, uno aplicado de más la hunde. El informe dice sin adornos que
**mide la mortalidad de nuestros filtros, no la del generador de SQX**.

**La corrida.** `python3 -m studies.screening.falsePositives.report` sobre la misma cosecha del 65 fila
5.4 (`--harvest …/Test_USATEC_H1_ruptura_leaseWeb/Results/_aparte/2026-10-11.090924`, 100 donantes,
5.000 monos por población), ya con α 0,01, hasta el paso 10. Lánzala con `TMPDIR` en `AlgoData` (la
del 65 murió una vez por `/tmp` lleno). Sale: la tasa de supervivencia nula y de las plantas en el 8 (sobre
la población entera, no en mitades) y en el 10. **Escríbelas en `ledger/thresholds.yaml`**, al final de
su sección, leídas como `ledger:<clave>`, cada una con lo que cuesta en estrategias reales al lado
(`--ledger`: los monos son una mirada al segmento que `ledger.spend` cuenta, no candidatos).

Ficheros que posees: `studies/screening/falsePositives/{chain,model,many,inputs,report,tooltips}.py`,
`config.yaml`, `README.md` (su «Not done»), `tests/test_false_positives.py`, el capítulo
`99-monos-por-la-cadena.md`.

**Dos modos de fallo, siempre presentes**
1. *Una población nula que no es nula:* los monos entran enteros, no se criba antes.
2. *Medir el filtro en vez del generador:* declara de qué databank sale cada población y qué condiciones
   llevaba encima (el `_aparte` es el build entero: el build de USATEC no lee `oos1`, 65 §5.2).

**Verificación:** (1) el mono pierde dinero tras costes — si la nula gana de media, le has regalado
algo; (2) `studies/readings/monkey/verify.py`, suelo 0,99, pasa antes de leer ninguna p; (3) la tasa del
8 a α 0,01 sobre la población entera queda ≤ 1,2 % (el objetivo del 65); si no, para y dilo; (4) el
embudo cuadra con el ledger fila a fila.

## Frente 4 · Monos seleccionados dentro de SQX (ex-30)

**Qué es:** poblaciones de estrategias de entrada aleatoria **construidas y seleccionadas por el Builder
de SQX** con la misma selección que las reales, pasadas por la cadena real. Cuántas pasan el paso 8 es
la tasa de falsos positivos **con la selección incluida**.

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
backtests de la misma estrategia dan operaciones distintas. Copia fuente:
`~/Downloads/codebase-strategy-vs-random-edge-testing-winrateedge-results-panel/RandomEntries-1.sxp`.

**Lo que la falta de semilla rompe y lo que no**
- *No rompe el control:* un mono seleccionado se eligió por un `build` con suerte; su retest en `oos1`
  es una tirada nueva e independiente, que es justo la hipótesis nula.
- *Sí rompe todo paso que vuelva a correr el `build`* (MC Retest, SPP, variantes) y la reproducibilidad
  de los informes desde su manifest. Por eso se construye con semilla (pregunta 1, contestada).

**Lo que se construye** (verificado 2026-10-15: no existe `sqx/blocks/snippets/`; `SQX_w1/w2` no tienen
`RandomEntry`)

1. **`RandomEntrySeeded`** en `sqx/blocks/snippets/RandomEntrySeeded/` (con README; sitio a confirmar
   según `sqx/CLAUDE.md`): `Math.random()` se cambia por un número que sale de mezclar un parámetro `Seed`
   con la hora de la barra, con SplitMix64 (~10 líneas de Java). Mismo backtest = mismas operaciones;
   `Seed` es un grado de libertad puro sin información. **Test de Python** que reproduce el mezclador y
   comprueba la frecuencia de disparo sobre barras reales (fracción de barras con entrada dentro del
   intervalo binomial de p). La hora de la barra es la semilla del mezclador, no una condición: no es un
   bloque de tiempo de la regla 15, pero dilo en el README del bloque.
2. **Instalación en el worker**, parado y con el protocolo de las reglas 1-3
   (`.claude/skills/sqx-wait/preflight.sh`). Copia a `user/extend/Snippets/SQ/Blocks/<Bloque>/`, arranca
   con `bin/sqx-worker.sh` y comprueba con `python3 -m sqx.inspect.vocabulary --diff custodian`. 🤔 **Sin
   probar** cómo compila SQX un snippet sin GUI: si el bloque no aparece, **para y pregunta**. Lo que
   descubras va a `knowhow/conditions/no-seeded-hash-in-sqx.md` (edítala). El maestro no se toca.
3. **Reproducibilidad antes de nada más:** el mismo retest dos veces, operación a operación. Si no se
   reproduce, no sigas.
4. **Builds de monos**, uno a uno en el custodio, proyecto `Test_monos_<activo>_<TF>_<n>` (regla 6) con
   `sqx.projects.builder` (regla 10), **igual que la población real que controla** (contestada 5: USATEC
   H1 ruptura, su dirección y su paleta; tantos builds como la real, contestada 3): activo, timeframe,
   ventanas, costes, salidas, aptitud, filtros, tamaño. La única diferencia: la entrada es el bloque
   aleatorio y nada más, probabilidad libre dentro del rango de frecuencias de la real (contestada 2).
   Espera con `/sqx-wait` (regla 18).
5. **Retest `oos1`, cosecha y paso 8** tal como esté en `criteria.yaml`, con el umbral que fije la
   la pregunta 12 (B congelado de la celda real). Más allá del 8 sólo si sobrevive alguno (contestada 4).
6. **Ledger:** familia `mono_sqx` y marca de población nula; nunca se mezclan con las reales en un
   recuento de supervivientes. Entran en una celda propia (pregunta 12 = B), nunca en la real.
7. **Informe** en `AlgoData/reports/…/monosSQX/` con la forma de `core/study/CONTRACT.md`: el embudo de
   los monos de SQX al lado del de la real y del de los monos de Python (frente 1).
8. **Limpieza:** `python3 -m sqx.projects.retire <P> --role <rol> --yes` con el worker parado.
9. **Manual** (regla 8) y tarjeta `knowhow/` con la instalación y la tasa que salga.

**Qué puede mover la búsqueda.** La probabilidad, la semilla y las salidas. Nada tiene información del
precio futuro salvo **cuánto tiempo pasa dentro del mercado** (deriva). El mono con horas del paso 8 lo
ve igual que en las reales.

**Verificación:** (1) el `oos1` medio de los seleccionados se parece al de monos sin seleccionar; si
rinden más, dilo con números; (2) el mono pierde dinero tras costes; (3) el bloque dispara a la
frecuencia que dice; (4) el embudo cuadra con el ledger.

## Frente 5 · Nulos: lo que sigue vivo de `5-nulos` §6

5c está cerrado (bitácora del 2026-10-13); el ítem 5 de §6 está muerto (issues 71 y 72).

- **5a · El exceso sobre una población sin preselección.** `monkeyExcess/report.py` sobre `MC_Trades`
  (XAUUSD) salta el aviso de preselección: esa databank llevaba tres condiciones sobre `main/OOS`. Ya no
  hace falta una corrida de SQX: la cosecha del build entero de USATEC (`_aparte/2026-10-11.090924`) no
  lleva ninguna. Corre `python3 -m studies.screening.monkeyExcess.report` sobre ella y di si el aviso
  calla y qué exceso sale.
- **5b · El período del ATR desde el `.sqx`.** `engines/nulls/windowed.py` (`atr_sized`) dimensiona con
  el ATR **del motor** (`engines/nulls/config.yaml` `barrier.atr_bars: 14`). Falta leer el período del
  `.sqx` de cada estrategia (la tarjeta `random-entry-nulls.md` dice que vive ahí), pasarlo a
  `calibrate.atr` y re-medir `CV(Size × ATR)` (0,384 en bruto → 0,200 con ATR(14) → 0,119 con ATR(50)).
  Si no baja, dilo. Ojo: el sizing entra en la z del paso 8; si cambia la z, cambia `criteria.yaml`
  efectivo y el sello del 8 — avisa antes de dejarlo activo.

## Frente 6 · El hueco aleatorio a prueba (ex-28)

Cada plantilla es la condición fija del dueño (la hipótesis) más un hueco que SQX rellena (minería).
¿El hueco trae supervivientes reales o ruido que la cadena debe matar? (La atribución fija contra hueco,
ex-6b, se quitó: el estudio de ablación en que se apoyaba se borró con los pasos 22-25.)

**6a · El A/B, automatizado por una skill `/ab-hueco`.** Dos brazos idénticos salvo el hueco —**A · fija**
(la plantilla sin `RandomCondition`, legítima: contestada 11) y **B · fija + hueco** («What to build»
0..1)—, mismo activo, ventanas, costes, filtros, aptitud y **mismo tiempo de reloj** (contestada 8);
plantilla `buildConfirmed` de `AlgoData/templates/registry.csv`, **3 repeticiones** por brazo, cada una
en su proyecto (`Test_ab_<plantilla>_A_<n>`, `…_B_<n>`), alternando A y B. Si A agota su espacio,
parar y anotar (contestada 9). Por brazo y repetición, tras retest `oos1`, cosecha y paso 8: generadas
y aceptadas · **supervivientes del paso 8** (la z del mono con horas, con el umbral de la pregunta 12)
· **supervivientes por hora de CPU** (la cifra que decide) · distintas (agrupadas por solape de
operaciones). El informe pone los dos brazos lado a lado, con intervalos, y dice si la diferencia supera
la variación entre repeticiones. Skill en `.claude/skills/ab-hueco/`, orquestador en
`sqx/experiments/ab_hole.py` (o donde encaje según `sqx/CLAUDE.md`), **reanudable**: preflight
`python3 -m core.assets <SÍMBOLO>` (regla 5) · gemela sin hueco registrada como variante de prueba ·
proyectos con `sqx.projects.builder` · builds uno a uno en el custodio (reglas 1-3, `/sqx-wait`) ·
retest y cosecha · paso 8 · ledger (`family` + `arm` + repetición; la columna con su contrato) · informe
en `AlgoData/reports/…/abHueco/` · retirar los `Test_` con el worker parado.

**6c · El bloque de ruido: sólo `RandomEntrySeeded`** del frente 4 (contestada 10), en el hueco o como
única condición fija de una plantilla de control. **Prueba de que es ruido, antes de usarlo:** su disparo
no predice el rendimiento siguiente en `build`, con su p en el informe. Variantes: la plantilla con el
ruido en el hueco; una plantilla cuya única condición fija es el ruido; barrido de complejidad acotado a
1-2 condiciones por lado (regla 14, contestada 9). Se cortan en `oos1` salvo que sobreviva alguna
(contestada 10). Cada superviviente con ruido es un falso positivo de la cadena con nombre y apellidos.

**Verificación (frente 6):** (1) el brazo A no lleva hueco (`sqx/inspect/template_check.py` da cero
`RandomCondition`) y tras el build las estrategias llevan el bloque fijo; (2) el ruido es ruido; (3) las
repeticiones difieren; (4) el ledger cuadra. Cierre: capítulo de manual para `/ab-hueco`,
`python3 tools/skillmap.py`, tarjeta `knowhow/` con el primer A/B.

## Decisiones del dueño — pregúntalas (regla 11)

**Contestadas por el dueño (2026-10-14)**, ya incorporadas arriba:
- 1-5 → **recomendaciones aceptadas**: con semilla; probabilidad libre dentro del rango de la real;
  tantos builds como la real; hasta `oos1` y el paso 8, más allá sólo si sobrevive alguno; primero
  USATEC H1 ruptura, con su dirección y su paleta.
- 6 → **los monos no miran `oos2`**. 7 → **no se reproduce** nada del 19. 8 → **mismo tiempo de reloj**.
- 9 → **parar y anotar** si A agota su espacio; 3 repeticiones; una `buildConfirmed`; barrido a 1-2
  condiciones por lado. 10 → **sólo `RandomEntrySeeded`**; con ruido se corta en `oos1` salvo que
  sobreviva alguna. 11 → **el brazo A es legítimo**; el B lleva «What to build» 0..1.
- **Encargo PARADO (2026-10-14)**: no se empieza hasta que él lo diga.

**Contestada el 2026-10-15 («todas las recomendaciones»):**
- 12 → **B**: los monos de SQX (familia `mono_sqx`) y los brazos del A/B van a una celda propia y se juzgan en el paso 8 con el B congelado, al empezar, de la celda real que controlan; no suman al contador de la real. Un control se ve con la misma vara que lo controlado.

## Lo que no tocas

- El **maestro** (5050): ni se construye ni se instala nada ahí.
- **`oos2`**: los monos no lo miran (pregunta 6).
- `pipeline/autopilot/criteria.yaml` se lee, nunca se edita para pasar un paso (regla 19);
  `studies/screening/gate/` sólo con el cambio mínimo que pida el frente 1. `docs/DEPENDENCIES.md` se
  regenera; `ledger/thresholds.yaml` sólo gana filas al final de su sección.
- **Regla fija del dueño:** los nulos de trader al azar se leen **sólo en el OOS del principal o en los
  mercados adicionales, nunca en el IS** (`knowhow/research/random-entry-nulls.md`).
- Ningún paso a mano: el workflow corre por `bin/workflow.sh` (regla 19); un build de mono es un proyecto
  `Test_` propio (reglas 6 y 10) y se retira al acabar. Nada de `git commit`.

## Objetivo — un comando

```
python3 tools/depmap.py && python3 tools/checks.py && python3 -m pytest tests/test_false_positives.py tests/test_nulls_seed.py -q
```

(sale 0 sólo si el código de los monos sigue verde; **no** prueba que las tasas estén escritas).
Verificación del encargo entero, a mano:

- [ ] `grep -n falsePos ledger/thresholds.yaml` devuelve la tasa del 8 (α 0,01, población entera) y la del 10 (frente 1).
- [ ] Snippet con semilla: test de mezclador y frecuencia en verde; `vocabulary --diff custodian` lo
      muestra; el mismo retest dos veces da las mismas operaciones (frente 4).
- [ ] `ls .claude/skills/ab-hueco` y su capítulo; el primer A/B con tabla A contra B (frente 6).
- [ ] 5a y 5b cerrados o dejados por escrito con el motivo.

No hay línea `/loop`: el objetivo no es un comando real que cubra el encargo entero.

## Cómo cierras

1. **Qué hiciste**, por frente, con la tabla de estado actualizada y una línea nueva en la Bitácora.
2. **Qué verificaste**, con la salida pegada.
3. **Qué dejaste sin hacer y por qué.**
4. **Qué descubriste para `knowhow/`**: edita la tarjeta que exista; nada de apéndices.
5. Capítulo de manual de cada comando nuevo (regla 8); `python3 tools/depmap.py && python3 tools/checks.py`.
6. Lista de ficheros cambiados y, como última línea: **¿Quieres hacer el commit?**

## Lo que sólo vivía en los encargos de origen

- **Por qué el test de Tinsley no se implementó tal cual (ex-5 §1):** su generador es sintético (±1R,
  p = 0,5, media cero): **es un estudio de potencia**. Con una estrategia real deja de valer: las
  operaciones no son apuestas justas y el oro no es driftless. De ahí que **el null sea un mono con tu
  mismo conjunto de oportunidades** — y desde el 65, también con tus mismas horas. El principio: *lo que
  le dejas fijo al null, se lo regalas*; la diferencia entre peldaños es lo que valía ese canal.
- **Las dos veces que se equivocó ex-5 (§3):** (1) se supuso que el mono heredaría la deriva del oro: falso,
  pierde en el 100 % de las 757; batir al mono es un listón **más bajo** que batir a cero. (2) Se concluyó
  que MinTRL hacía redundante al mono: artefacto de elegir el Sharpe. Con otro estadístico el veredicto se
  mueve entre 40 y 85 puntos de la misma simulación: `dd` 84,5 % · `sharpe` 77,4 % · `retdd` 76,9 % · `pf`
  55,2 % · `net` 39,5 %. **La elección del estadístico decide el veredicto más que la del null.**
- **El hallazgo que salvó el estudio (ex-5 §4):** SQX rellena a la apertura de la vela, entrada y salida;
  `open-open` reconcilia a 1,0000. Con el fill equivocado `net` daba 21,5 % en vez de 39,5 %. Por eso
  `calibrate.convention()` mide el relleno por estrategia.
- **Dónde encaja el nulo en el flujo (ex-5 §5):** el dueño eligió **P1**, tras el OOS sobre la población;
  hoy vive dentro del paso 8 como la z del mono con horas (65 §5.2). Descartados: P0 (generación IS: null
  contaminado), P3 de ex-5 (sobre las variantes: una vecindad de parámetros no es un mono), P4 (cartera).
- **Hallazgo 6bis de ex-5:** `MC_Trades` (XAUUSD) tiene el 99,9 % de sus 757 con beneficio OOS positivo
  porque desciende de una tarea con tres condiciones sobre `main/OOS`; la databank `OOS` entera, el 26,9 %.
- **Decisión del dueño (2026-10-07), vigente:** el borde plantado es neto de costes y el sizing del mono es
  `atr` (nunca los lotes del donante); cifras en `studies/screening/falsePositives/README.md`.
