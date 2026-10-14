# 58 · MCPT de la fábrica — la fábrica entera contra series sin nada que encontrar

**Tu oficio:** estadística y Python numérico sobre precios M1 y sobre lo que el autopiloto ya escribe;
SQX sólo a través de `bin/workflow.sh` y del custodio. **Opus** para F0.a (el generador), F1 y F5 (el
veredicto); **Sonnet** para lanzar runs, importar series, tabular y el capítulo del manual (regla 17).
**Tu encargo:** un veredicto **por configuración de la fábrica** (mercado × marco × paleta × ajustes):
PASA / LIMBO / NO PASA / sin datos, con la FDR por etapa y su intervalo, el lift de cada paso, la tasa de
falsos positivos empírica del paso 8 frente a su 5 % nominal, y la repetibilidad. La primera configuración
juzgada es **XAUUSD H1 ruptura, K = 5 por rama** (dueño, 2026-10-11). Es una decisión sobre la fábrica,
no una descripción: «este paso no discrimina» y «sin supervivientes reales» son respuestas válidas.

Lee `CLAUDE.md` (reglas 1-7, 9, 11, 16-20) · `CODESTYLE.md` · `studies/CLAUDE.md` · `engines/README.md` ·
`.claude/skills/workflow-simple/steps.md` (qué lee y escribe cada paso) · `knowhow/sqx-drive/import-csv-as-symbol.md`
(cómo entra un CSV como símbolo; **su cabecera dice UTC: está superada, `timezone=EETUS` en la importación
deja el feed en EST+07 como el real — corrige la ficha en F0**). El documento del dueño con la propuesta
completa y las fórmulas: `docs/AgentPDFs/criterios-mcpt-fabrica-propuesta-2026-10-12.md`; lo esencial
está aquí, léelo sólo para una duda de notación.

## Estado del plan (lo actualiza cada sesión al cerrar)

| fase | qué | modelo | depende de | estado |
|---|---|---|---|---|
| F0 | generador en el repo, símbolo SYN automatizado, exclusión `_mcpt_` del estado global, sorteo dev apagado, familias | Opus (a, e) · Sonnet (b, c, d) | nada | sin empezar; sólo existen las salidas de los pilotos en `AlgoData/scratch/synthetic/` y las fichas `XAUUSD_SYN01` |
| F1 | validar el generador (6 comprobaciones + sensibilidad) | Opus | F0.a | sin empezar |
| F2 | humo en SQX: 20 supervivientes reales retesteadas en una serie sintética | Sonnet | F0.b, F1 | sin empezar |
| F3 | control positivo: ventaja plantada δ = 0,02 / 0,05 / 0,10 | Opus | F1, F4 | sin empezar |
| F4 | piloto K = 1 por rama, embudo completo hasta el 21 | Sonnet | F0, F2 | parcial: un run sobre serie sintética llegó al 8 y cortó 1000 → 0 (`AlgoData/autopilot/Test_XAUUSD_H1_ruptura_mcptR/20261011-210613/resumen.md`) |
| F5 | K = 5 por rama, veredicto | Sonnet (runs) · Opus (veredicto) | F4 | sin empezar |
| F6 | qué se hace con los pasos de lift ≈ 1 y con las líneas mal calibradas | dueño | F5 | sin empezar |

### Bitácora

- 2026-10-11 — Encargo escrito desde la propuesta del dueño (2026-10-12) y el análisis de viabilidad.
  Decisiones ya tomadas por el dueño ese día: el símbolo sintético vive en el **worker y se reimporta en
  cada run** (no en el master); la parada del Builder es la de producción (**N estrategias pasadas**, 1.000);
  primera configuración **XAUUSD H1 ruptura, K = 5**; sin Council.

---

## 0 · De dónde sale

Idea de Jaffray Woodriff (*Hedge Fund Market Wizards*), MCPT de Timothy Masters, y la sección 6 de «A robust
data mining workflow» (Denelio). El dueño la formalizó en `docs/AgentPDFs/criterios-mcpt-fabrica-propuesta-2026-10-12.md`:
el Builder de SQX recorre millones de combinaciones y se queda con las mejores — **el sesgo de selección más
grande de la cadena, y el único que ningún paso del pipeline mide** (CSCV corrige la selección entre las
variantes de una madre; el mono del paso 8 es un nulo para una estrategia fija). El remedio: repetir la
fábrica entera, idéntica, sobre precios que conservan todo (volatilidad, rachas, calendario, perfil horario,
deriva anual, camino M1) **menos la dirección de un bloque al siguiente**, y comparar supervivientes.

Lo que ya se probó (pilotos del 2026-10-10 y 11): generar una serie cuesta 86 s (82 escribiendo el CSV),
importarla en el custodio 28 s, clonar el proyecto 0,05 s; un run hasta el paso 8 sobre la serie sintética,
58 min, con el paso 6+7 en 1.313 s para 1.000 estrategias. **La viabilidad está resuelta: K = 5 por rama son
~4 h de Builder por servidor.**

## 1 · F0 — Prerrequisitos

**1.a — El generador, en el repo (Opus).** Hoy no existe: sólo quedan `AlgoData/scratch/synthetic/*.csv|parquet`.
Escribe `engines/market/synthetic.py` (un README de dos líneas en `engines/market/README.md`) con:

- `flip(bars_m1, block: str, seed) -> DataFrame`: el **volteo de signo alrededor de la deriva anual**. Bloques
  de una barra del marco `block` (H1 para esta configuración), el gap de apertura dentro del bloque,
  $r_b = \ln(C_b/C_{b-1})$, $\mu_y$ la media de $r_b$ del año natural, $s_b = \pm 1$ con prob. ½ de
  `numpy.random.SeedSequence(seed).spawn(K)`, y cada precio M1 del bloque (O, H, L, C) por
  $d' = s_b\,d + (1-s_b)\,\mu_y\,\varphi$ con $d = \ln(p/C_{b-1})$ y $\varphi$ la fracción del bloque
  transcurrida; con $s_b = -1$ máximo y mínimo de cada barra se intercambian. Los bloques se encadenan desde
  el cierre sintético anterior. Timestamps **idénticos** al real: nunca se reasignan por posición (el
  piloto 1 cayó ahí).
- `plant(bars_m1, block, seed, hours: list[int], delta)`: igual, pero en los bloques que empiezan en esas
  horas $P(s_b=+1) = ½ + \delta$ — el control positivo de F3.
- `write_sqx_csv(df, path)`: `yyyy.MM.dd,HH:mm,O,H,L,C,V` sin cabecera (formato MT4 de la ficha). Escribe
  con `pyarrow.csv` si baja de 82 s a ~10 s; si no, no lo optimices.
- Un `__main__`: `python3 -m engines.market.synthetic XAUUSD --block H1 --seed 1 --k 5 [--plant 8,9 --delta 0.05]`
  que deja `AlgoData/synthetic/<SIM>_SYN<kk>_M1.parquet` y su CSV, y anota `seeds.csv` (kk, semilla, bloque,
  fecha, δ). Las barras M1 reales salen de `AlgoData/bars/` por `core.paths`, nunca una ruta absoluta.
- `tests/test_synthetic.py`: sobre 3 días sintéticos de datos, precios > 0, mismos timestamps, $|r'_b-\mu| = |r_b-\mu|$
  exacto, H/L intercambiados cuando $s_b=-1$, y `plant` con δ = 0,5 da signo + siempre en esas horas.

**1.b — El símbolo en el worker, automático (Sonnet).** `sqx/symbols/synthetic.py` (o donde `sqx/CLAUDE.md`
diga que vive un verbo de símbolo): `ensure(role, "<SIM>_SYN<kk>")` que, con el worker arrancado y sin
ningún job, hace el `-symbol action=add` + `-data action=import … timezone=EETUS` de la ficha, idempotente
(si el feed ya está con el mismo nº de barras, no hace nada), y crea `assets/symbols/<SIM>_SYN<kk>.yaml`
copiando el del real con `sqx_symbol` cambiado y el bloque de ventanas en `assets/_policy.yaml` como el de
`XAUUSD_SYN01` (`assets/_policy.yaml:147-151`). `python3 -m core.assets XAUUSD_SYN01` debe salir 0 (regla
5). Corrige la cabecera de `knowhow/sqx-drive/import-csv-as-symbol.md` (zona horaria, worker, pérdida al
copiar `data.db` → por eso se reimporta en cada run). Comprueba en `bin/mirror-data.sh` que las series
llegan a gorilla con el resto de `AlgoData/bars`; si no, añádelas.

**1.c — Nada del ruido entra en el estado global (Sonnet).** Convención: los proyectos de este encargo se
llaman `Test_<SIM>_<TF>_<idea>_mcpt_real_k<k>` y `Test_<SIM>_<TF>_<idea>_mcpt_syn<kk>`. Quien lee
`resumen.md` o los registros para alimentar algo (`studies/research/memory/sources.py`, `ledger/steprows.py:39`
`log_build`, `ledger/blind.py`, el tablero) **salta todo nombre con `_mcpt_`**; nunca `/store-save` de un
proyecto de ruido. Un test por lector que lo demuestre.

**1.d — El sorteo de desarrollo apagado (Sonnet).** `pipeline/autopilot/criteria.yaml:52-55` (`dev.sample: 3
at: ["8"]`) inventaría 3 «supervivientes» en la rama de ruido. Los runs de este encargo corren con `dev.on:
false` en **las dos ramas**; averigua cómo se pasa por run sin editar el YAML a mano (regla 19: si no hay
forma, es una opción nueva de `bin/workflow.sh`, con su línea en el manual).

**1.e — Únicos y familias (Opus).** `studies/research/mcpt/families.py`: únicos por la huella de la lista
de operaciones (`engines/variants/fingerprint.py`, `prints`/`keep`, hoy sólo usada entre variantes de una
madre); familias por correlación del P/L semanal en el tramo build ≥ `ledger:mcpt.family_rho` (propuesto
0,9), con el panel semanal de `engines/weekly/panel.py`. Devuelve las dos cuentas por etapa; **decide la de
familias**. Agrupación simple (unión por pares sobre el umbral); `ponytail:` si hace falta algo mejor.

## 2 · F1 — Validar el generador (Opus)

Tres series de XAUUSD en bloques H1 y, para la sensibilidad, una en bloques D1. `python3 -m
studies.research.mcpt.validate XAUUSD_SYN01..03` imprime y **falla (exit ≠ 0) si no se cumple**: (1) precios
> 0, mismos timestamps que el real; (2) misma zona horaria; (3) volatilidad media por hora del día, error
< 0,1 %; (4) autocorrelación de $|r|$ en retardos 1-50 bloques idéntica a la real (tolerancia que
justifiques); (5) autocorrelación de $r$ en retardos 1-10 dentro de $\pm 2/\sqrt{n}$; (6) retorno de cada
año compatible con el real dentro de su dispersión; (7, sólo informa) la serie D1 frente a la H1. Si (4) o
(5) fallan, el generador conserva o destruye de más: arregla el generador, no la tolerancia.

## 3 · F2 — Humo en SQX (Sonnet)

En el custodio, `ensure` de `XAUUSD_SYN01`, un proyecto `Test_XAUUSD_H1_ruptura_mcpt_humo` clonado del donante
congelado (`sqx/projects/builder.py`) con sólo el feed cambiado, y un retest de ~20 estrategias que hayan
pasado el paso 8 real (del almacén, `/store-open`; si no hay 20, las que haya y dilo). Medida: el exceso
sobre la deriva de cada una en la serie sintética con su t. **Éxito:** media de t ≈ 0 (o algo negativa por
costes) y no más de ~1 de 20 con t ≥ 1,65. Si muchas siguen ganando, la serie conserva estructura: vuelve a
F1 con bloque más corto. `/sqx-wait` para esperar (regla 18); retira el proyecto al acabar (regla 6).

## 4 · F4 — Piloto K = 1 por rama (Sonnet)

Primero averigua con `sqx/inspect/dump_project.py Test_XAUUSD_H1_ruptura_mcptR` qué feed usó el run del
2026-10-11 y renómbralo según 1.c o retíralo. Después, **el mismo comando en las dos ramas**, cambiando
sólo símbolo y nombre:

```
bin/workflow.sh simple Test_XAUUSD_H1_ruptura_mcpt_real_k1 XAUUSD       H1 long <PALETA> "MCPT real k1"  1000 180
bin/workflow.sh simple Test_XAUUSD_H1_ruptura_mcpt_syn01   XAUUSD_SYN01 H1 long <PALETA> "MCPT ruido 01" 1000 180
```

`<PALETA>` es la del run `ruptura` de producción (pregúntala si no está anotada). Parada por 1.000
estrategias pasadas, como producción; **anota el tiempo del paso 6 en cada rama**: es la única medida del
filtro del Builder (con la parada por N pasadas, $N_1$ es 1.000 en las dos ramas por construcción). Un run
por servidor (`bin/remote.sh gorilla --detach …` para el segundo; nada CPU-pesado al lado, regla 19).
**Éxito:** el embudo se completa en las dos ramas sin intervención; sin conclusiones estadísticas con K = 1.
Si la rama real corta 1000 → 0 en el paso 8 como lo hizo la sintética, **no es un fallo de este encargo**:
es el hallazgo «la configuración no produce supervivientes reales», se informa con la TFP del ruido en el
paso 8 (sección 5) y se para en F4 hasta que el dueño decida la configuración.

## 5 · F5 — K = 5 por rama y el veredicto (Sonnet corre, Opus juzga)

Cinco runs reales y cinco sobre `XAUUSD_SYN01..05` (series distintas, 1.a con `--k 5`). Cuando los diez
estén, `python3 -m studies.research.mcpt.report Test_XAUUSD_H1_ruptura --k 5` lee los
`AlgoData/autopilot/<P>/<stamp>/resumen.md` y `paso-<n>/hechos.parquet` de los diez, cuenta por etapa
(0 generadas si SQX lo escribe en su log, 1 pasadas, 2 únicas, 3 familias, 8, 14, 16, 16.5, 17, 18, 18.5,
19, 10, final = 20) y escribe `AlgoData/mcpt/<config>/veredicto.md` + `embudo.csv` con:

- $\widehat{\text{FDR}}_j = \min(1, \overline{N}^{\text{ruido}}_j / \overline{N}^{\text{real}}_j)$, bootstrap sobre
  runs (10.000 remuestras, IC percentil 90 %); «sin supervivientes reales» si el denominador es 0.
- $\text{lift}_j$ = cociente de tasas de paso real/ruido, con el mismo bootstrap. Informa, no decide.
- $\text{TFP}_j = N^{\text{ruido}}_j / N^{\text{ruido}}_{j-1}$ con Clopper-Pearson sumando los 5 runs; frente al
  nominal **sólo en los pasos que juzgan fuera de muestra** (8, 14, 10, 19…).
- Repetibilidad $R$ por rama: fracción de familias finales de un run con alguna familia en otro de la
  misma rama con ρ semanal ≥ `ledger:mcpt.repeat_rho` (propuesto 0,7), media sobre pares.
- El mejor de cada run ($S_{\max,k}$): sólo anotado.
- Estado: PASA si FDR final ≤ `ledger:mcpt.fdr_pass` **y** límite superior del IC ≤ `ledger:mcpt.fdr_fail`
  **y** $R_{\text{real}} > R_{\text{ruido}}$; NO PASA si FDR ≥ `ledger:mcpt.fdr_fail`; sin datos si no hay
  supervivientes reales; LIMBO el resto. Umbrales en `ledger/thresholds.yaml` (filas nuevas al final de su
  sección), valores propuestos 0,2 y 0,5 — **pregúntaselos al dueño antes de escribirlos** (sección 8).

Mercados adicionales (paso 10) **reales** en la rama de ruido, como propone el dueño. Los proyectos
`Test_…_mcpt_*` se retiran tras cosechar (`python3 -m sqx.projects.retire … --yes`), sin `/store-save`; lo
que queda es `AlgoData/mcpt/`. `/manual-chapter` para `engines.market.synthetic` y `studies.research.mcpt.report`
(regla 8). El estudio: `studies/research/mcpt/` — mira `studies/CLAUDE.md` y decide si el contrato de
`core/study/` le aplica (es un estudio sobre una configuración, no sobre una población); si no, la forma de
`studies/research/literature/`, y dilo en el README.

## 6 · F3 — Control positivo (Opus; después de F4)

Tres series con `--plant <horas> --delta 0.02|0.05|0.10` (la franja: las horas de la sesión europea, o las
que el dueño diga) y un run por serie con el mismo comando de F4. Medida: ¿encuentra el Builder la ventaja
(un filtro horario en las supervivientes)? ¿cae la FDR frente a las series sin ventaja? Entrega la **curva
de potencia** (δ → supervivientes finales) en `AlgoData/mcpt/<config>/potencia.md`. Sin ella una FDR alta
no significa nada.

## 7 · Lo que no tocas

El master y su `data.db`; el almacén de estrategias con nada de ruido; `oos2` como tramo de juicio (en la
serie sintética el histórico entero es sintético, incluido oos2, pero el pipeline no se cambia para juzgar
en él); `criteria.yaml` a mano para pasar un paso (regla 19); los ficheros de los encargos 54-57; ningún
heap (regla 3).

## 8 · Decisiones del dueño — pregúntalas (regla 11)

1. **Umbrales del veredicto:** PASA ≤ 0,2 y NO PASA ≥ 0,5 (propuesta), o la versión estricta PASA ≤ 0,1.
2. **Correlaciones de familia:** 0,9 para agrupar y 0,7 para la repetibilidad, o revisarlas con la tabla
   de F4 en la mano (el documento dice «revisar con F4»): ¿se fijan ahora o tras F4?
3. **Paleta y hora de F3:** qué paleta es la de «ruptura» y en qué franja horaria se planta la ventaja.
4. **Etapa 0 (generadas por el Builder):** si SQX no escribe el nº de estrategias generadas en su log, ¿se
   omite la etapa o se mide por el tiempo del paso 6?
5. **Pasos de lift ≈ 1 (F6):** quitar, recalibrar o sólo anotar. Después de F5.
6. **Dónde queda la FDR de la configuración:** ¿junto a cada estrategia del almacén que salga de ella (para
   que el fondeo reparta riesgo con ella) o sólo en `AlgoData/mcpt/`?

## Objetivo — un comando

```
python3 tools/depmap.py && python3 tools/checks.py \
  && python3 -m pytest tests/test_synthetic.py tests/test_mcpt.py -q \
  && python3 -m studies.research.mcpt.validate XAUUSD_SYN01 XAUUSD_SYN02 XAUUSD_SYN03 \
  && python3 -m studies.research.mcpt.report Test_XAUUSD_H1_ruptura --k 5
```

Sale 0 sólo con el generador validado y los diez runs cosechados en un veredicto (`report` sale ≠ 0 mientras
falte un run de cualquiera de las dos ramas; «sin datos» es un veredicto y sale 0). F3 y F6 se verifican a
ojo, con `potencia.md` y la nota del dueño.

## Cómo cierras

Qué hizo · qué verificó, con la salida del Objetivo pegada y la tabla del embudo · qué dejó sin hacer y por
qué (una fase bloqueada por una pregunta de §8 se queda en la tabla de estado con «bloqueado por …») · qué
descubrió para `knowhow/` (al menos: la TFP real del paso 8 frente al 5 %, en `knowhow/pipeline/`; el
tiempo del paso 6 real frente a ruido, en `knowhow/perf/`) · la lista de ficheros cambiados y, como última
línea, **¿Quieres hacer el commit?**

```
/loop Lee docs/encargos/58-mcpt-fabrica.md y ejecútalo entero. Tras cada iteración corre el Objetivo; si sale 0, para el bucle; si no, arregla lo que falló y vuelve a correrlo.
```
