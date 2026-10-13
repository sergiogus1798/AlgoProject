# docs/encargos — un fichero por instancia de agente

Cada fichero de esta carpeta es **un encargo autocontenido**: lo que una sola instancia necesita
para hacer su parte, y nada más. Se despacha diciéndole al agente que lea **su** fichero, no el
plan entero.

La secuencia manda desde `docs/AgentPDFs/WORKFLOW.md`. **Los encargos son la versión ejecutable de una parte de ellos.**
Donde discrepen, manda el WORKFLOW — y se arregla el encargo.

**Un encargo cumplido se borra.** No se marca como hecho ni se deja «por si acaso»: lo que se
aprendió haciéndolo ya está en `knowhow/`, en el manual y en el código. Limpieza del 2026-09-24:
salieron los encargos 1, 2, 3, 4 y 7, verificados uno a uno contra el repositorio. El 25-09 salió
el 19 (el contrato de datos de la ventana): vive en `core/study/CONTRACT.md` y `studies/CLAUDE.md`.
Y el 18 (perfilado de Python): hecho en los commits `c9011a2` y `3923010`; lo que no pudo medirse
porque gasta `oos2` está en `OPEN.md` §42. El 26-09, en una tanda de cinco frentes en paralelo con
un revisor detrás de cada uno, salieron el **8** (los 19 umbrales se leen de `ledger/thresholds.yaml`),
el **11** (`studies/readings/edgeCost/`, pasos 8 y 25), el **12** (`sqx/structural/` +
`studies/readings/structure/`, paso 23; el mono dentro de SQX es imposible,
`knowhow/conditions/no-seeded-hash-in-sqx.md`), el **14** (`studies/readings/conditionalMap/`, paso 22)
y el **15** (`studies/optimisation/marketSurfaces/`, paso 18.5). Lo que dejaron abierto está en
`OPEN.md` §43–§48. Y en la limpieza de `docs/` del mismo día salió el **21** (la prueba
del workflow entero): su informe es `docs/AgentPDFs/profiling-workflow-2026-09-26.md`. Con él
salieron el ejemplo USDJPY del 24-09, al que ese informe supera, y los dos `CONTEXTO-*`: las
skills de SQX y `/curate` ya existen. Ese mismo día salieron también el **20** (el ATR calculator,
paso 24: lo que decía vive en `docs/manual/10-cierre.pdf`, cap. 54-atr-calculator) y la ficha del
proyecto de ejemplo IS/OOS, que ahora es `knowhow/locations/xau-isoos-example-project.md`.
El 2026-10-02 salieron el **6** (los 768 bloques de `sqx/blocks/taxonomy.yaml` llevan sus siete
pesos de arquetipo, commit `a694e67`), el **10** (pasos 20 y 23 construidos; sus tres decisiones del
dueño viven en `OPEN.md` §50), el **37** (la matriz del WFM con sus 10 condiciones, verificada contra
SQX, commit `5d2d0dc`) y el **42** (noticias en el tester, la memoria con causas y el revisor, y los
tres contrastes, commit `69c4ada`; la lectura real con y sin filtro espera la estrategia y la firma
del dueño, `OPEN.md` §85, y lo que encontró está en §96-§99 y §101).
El 2026-10-06 salieron, por orden del dueño, el **27** (la criba de MAE profundo está construida en
`studies/screening/maeDepth/`; su umbral sigue siendo decisión suya) y el **32** (`ledger/tried.py`
registra lo que prueba cada barrido).

El 2026-10-09, por orden del dueño, los 24 encargos que quedaban se reagruparon por temática en los
ocho de abajo y se borraron: cada nuevo lleva sólo lo que falta por hacer, las preguntas abiertas y lo
que sólo estaba escrito en sus originales. El **38** (recuadro de la meseta) y el **39** (edge según
los costes) salieron sin heredero: se construyeron y un rediseño posterior quitó lo construido
(`ca7dd56` y `90d516d`). Los originales siguen legibles con `git show c923d10:docs/encargos/<fichero>`.

## Los encargos vivos — reagrupados por temática el 2026-10-09 (el 57 es posterior, 2026-10-10)

Los nueve son **planes vivos**: llevan tabla de estado y bitácora, y cada sesión actualiza su fila.

| fichero | qué queda por hacer | depende de |
|---|---|---|
| `49-plan-fases-0-y-1-y-criterios-10-a-20.md` | **el plan que ordena a los demás** (puntos 0.1-1.9, misma numeración que el 41): cerrar la fase 0, el registro completo, el autopilot para poblaciones nulas, las firmas del dueño; y el punto 1.6 — una regla medida o una razón escrita para los pasos 10, 12, 14, 16 y 20, los hechos del paso 16 y los umbrales de cuatro estudios al ledger | las firmas del dueño; los encargos 50 y 53 |
| `50-pasos-6-a-8-puerta-y-receta.md` | la puerta del paso 8: el embudo de las dos poblaciones de prueba, las líneas que fija el dueño, cargarlas, la documentación, la corrida de verificación y apagar `dev.on`; y la receta de filtros del IS del paso 6 por activo × marco × familia | máquina libre; dos paradas del dueño; el carril (regla 19) |
| `51-pasos-10-a-12-transferencia.md` | paso 10: calibrar P1-P9 y adaptar la pestaña Cross Market de la ventana; pasos 10.5-12: la primera corrida real, el «corta» del dueño con su paquete de reglas y borrar la lectura vieja `z_new` | el custodio libre; el «corta» del dueño |
| `52-pasos-16.5-a-18.5-variantes-y-meseta.md` | validar el WFC y la nube con un lote real (ya hay uno en disco); la meseta en el tiempo (tramo contra tramo) y el mapa de ventaja sobre el mono en Market Surfaces, ambos a reescribir contra el estudio actual | el «adelante» del dueño; `oos2` para la meseta |
| `53-monos-y-nulos.md` | el control negativo: el mono por los pasos 10 a 20 y la corrida a 10.000, los monos seleccionados dentro de SQX con el bloque con semilla, lo que queda vivo de los nulos, y el hueco aleatorio a prueba | reglas firmadas de los pasos 10-20 (encargo 49); el custodio libre |
| `54-fondeo.md` | que la ventana edite los datos del dueño que el simulador de fondeo necesita, la tabla de planes sobre una cartera real, y el módulo de riesgo máximo por operación (cola del peor día, drawdown esperado de la cartera) | los datos y decisiones del dueño; un pool validado (encargo 55) |
| `55-mt5-paso-26-y-flota.md` | paso 26: el test en verde, el drawdown flotante con M1, una superviviente real verificada y el pool que lee la cartera; flota: paquete de despliegue con perfil `.chr`, registro de magics, acciones sobre la VPS, exportador de carteras y conciliación con las diez cuentas | una superviviente real; la VPS; OPEN.md #78 |
| `56-lecturas-nuevas.md` | cinco lecturas sueltas, cada una despachable por separado: estacionalidad, señal por plantilla, replay de operaciones, cerebro con probabilidades y —aparcado por el dueño— alfa y beta | lo ya exportado; preguntas del dueño por frente |
| `57-gorilla-en-la-ventana.md` | fase 1: bloque «custodio_gorilla» en «En marcha» leyendo `/proc` por SSH (sólo mirar); fase 2: selector de servidor en los tres lanzadores, bloqueada por las respuestas del dueño | regla 3, regla 12 |
| `58-mcpt-fabrica.md` | MCPT de la fábrica: el generador de series sintéticas (volteo de signo alrededor de la deriva anual) en el repo y validado, el símbolo SYN reimportado en el worker, la fábrica entera K = 5 veces sobre el real y K = 5 sobre ruido, y el veredicto por configuración (FDR por etapa, lift por paso, TFP del paso 8 frente al 5 %, repetibilidad); primera configuración XAUUSD H1 ruptura | la propuesta del dueño (`docs/AgentPDFs/criterios-mcpt-fabrica-propuesta-2026-10-12.md`); dos servidores libres ~14 h; preguntas §8 |

## Tanda del 2026-10-11 — de la revisión del dueño de los pasos 1 a 7

Salen de `~/Desktop/revision-pasos-01-07-2026-10-11.md` (cifras de los dossiers
`docs/AgentPDFs/criterios-implementados-2026-10-12{1..7}-*-2026-10-08.md`), corregida con lo que el código dice ese día: el
suelo de 35 operaciones al año y la retirada de `MonteCarloManipulation` ya estaban hechos y no llevan encargo.

| fichero | qué construye | depende de |
|---|---|---|
| `59-politica-de-costes.md` | el recuento de estrategias que cambian de signo entre 304, 747 y 1.000 puntos (NIKKEI225, `build`) sobre una cosecha ya hecha, y después cinco decisiones del dueño ejecutadas: spread histórico de los índices, la hora del rollover, swap abonado a 0, el comando que calcula el método vigente y el coste de las salidas por stop | nada para el recuento; una respuesta del dueño por parte |
| `60-estudio-del-build.md` | métrica de fitness × genético/aleatorio, ≥ 3 réplicas por brazo en una celda nueva con `criteria.yaml` congelado; la medida es supervivientes del paso 8 menos el control de monos, registrada por celda y plantilla; el resultado queda escrito en `_build.yaml` | la celda, las métricas y el brazo aleatorio (dueño); el custodio libre 14-30 h; el mono por el paso 8 (encargo 53 si falta la pieza) |
| `61-money-management-por-stop.md` | las cinco comprobaciones antes de pasar al money management por stop loss (mismo ATR, tope de lotes, huecos, el EA de MT5, dónde se pone) y una recomendación; no cambia nada | nada; sólo lectura |
| `62-registro-unico-de-ya-probado.md` | un comando de sólo lectura que responde «¿se probó esta celda?» contando los `Test_` y los tramos gastados, y las tablas de antes y después de dos cambios de estadística que decide el dueño: N por serie de precios y BH por familia fijada en la propuesta | nada para el comando y las tablas; el sí del dueño para aplicar |

## Tanda del 2026-10-12 — de la opinión sobre los criterios de los 26 pasos

Sale de la lectura del dossier `docs/AgentPDFs/criterios-implementados-2026-10-12.md` y del «anota eso en un encargo» del dueño.

| fichero | qué construye | depende de |
|---|---|---|
| `63-criterios-del-workflow-opinion-y-rediseno-de-la-cola.md` | plan vivo: la opinión del 2026-10-12 (§0) y siete frentes — repricing que cuadre con SQX, `dev.on` apagado y una población entera con nula y plantada por la cola, `falsePositives` cacheado, el paso 14 por percentil entre vecinas, la cola 17-20 en una prueba prerregistrada en oos2, las reglas inertes del paso 8 a columnas, el perfil del paso 1 | las siete decisiones D-1..D-7 del dueño; los encargos 58, 59, 51, 60, 62 donde se solapan |
| `63-prompt-segunda-opinion.md` | el prompt para que otro agente, sin ver la primera opinión, audite el mismo dossier desde potencia, economía y «qué haría un fondo» | nada |
| `64-modelo-global-de-la-poblacion-y-stepm-en-el-paso-8.md` | plan vivo, segunda lectura con cómputo ilimitado en Python: N efectivo por solape de operaciones, StepM/SPA sobre las 10.000 del paso 8, modelo de mezcla empírico-bayesiano (P(μ>0) por estrategia, FDR local), los cambios al 63 (frente 2 primero y en Python, repricing al final, 13-14 a diagnóstico, paso 1 apagado) y la adjudicación de las tres opiniones por predicciones | D-1..D-5 del dueño; el 63 (frente 2), el 58 (poblaciones nula y plantada) |
| `64-prompt-tercera-opinion.md` | el prompt para un tercer agente, sin ver las dos opiniones, con pregunta abierta y tabla de predicciones prerregistradas por paso | nada |
| `65-consenso-cuatro-opiniones.md` | plan vivo: los diez cambios del consenso de las cuatro opiniones (§9 de `criterios-cuarta-opinion-2026-10-12.md`) en tres bloques — A borrados y apagados (`dev`, paso 1, cola 14/18/18.5/20, paso 10), B la estadística (mono con horas, contador por celda, una z y fdr local en el 8, lectura única de oos2, NIKKEI a 747, repreciador < 1 %), C build sintético y protocolo en vivo. Donde coincide con 63 o 64, manda este | nada; el bloque C espera al B |
| `66-performance.md` | plan vivo: la auditoría de rendimiento y errores del Python del workflow (2026-10-12) — pérdida de filas en `draws.merge`, el control de falsos positivos (37 % de la corrida), núcleos del mono para 1 M de sorteos, 48 núcleos donde hoy hay 8, el binario `AlgoBank` por databank y el almacén sin copia; cada cambio con su prueba de igualdad | evidencia en `AlgoData/audit/performance-2026-10-12/`; comparte `gate/level3c.py` y `falsePositives/` con el 65 |

| `67-filtro-minimo-calibrado-con-sinteticos.md` | el umbral mínimo del Build por celda (activo × TF), medido en lo que halla una hora de build sin filtros sobre series sintéticas; con su coste en estrategias rechazadas y minutos hasta 10.000 | `66` (D24 estable), `58` (generador) |
| `68-adaptar-el-codigo-al-codestyle.md` | plan vivo: que las reglas nuevas de `CODESTYLE.md` (2026-10-13) las compruebe una máquina — 18 fases: tests al entregar, hooks, trinquete, ruff ampliado, semillas, `assert` en los lectores, comprobador de tipos, los 1.375 `-> dict` sin tipar, código muerto, README generado, lockfile, canario, gorilla, agente `reviewer` y `ruff format` | nada |
| `69-renumerar-los-pasos-del-workflow.md` | aplazado: renumerar los pasos ahora que 22-25 no existen y el MT5 sigue siendo el 26; lo medido (77 + 82 ficheros), por qué se dejó y las tres preguntas previas | sin empezar; sólo cuando el dueño lo pida |

## Adónde fue cada encargo viejo

Para resolver una cita antigua («encargo 44», «el plan 41 §1.5») en el código, en `OPEN.md` o en un dossier.

| viejo | ahora | viejo | ahora |
|---|---|---|---|
| 5 nulos (§6) | 53, parte 5 | 35 flota MT5 | 55 |
| 9 monos de punta a punta | 53, partes 1-3 | 38 recuadro de la meseta | sin heredero |
| 13 alfa y beta | 56, frente 5 | 39 edge según los costes | sin heredero |
| 16 replay de operaciones | 56, frente 3 | 40 cerebro con probabilidades | 56, frente 4 |
| 25 estacionalidad | 56, frente 1 | 41 fases 0 y 1 | 49 (misma numeración de puntos) |
| 26 señal por plantilla | 56, frente 2 | 42 recalibración 6-7-8 | 50, parte 7 |
| 28 hueco aleatorio | 53, parte 6 | 43 criterios 10 a 20 | 49, §3 |
| 29 meseta en el tiempo | 52, parte M | 44 puerta del paso 8 | 50, partes 1-6 |
| 30 monos en SQX | 53, parte 4 | 45 módulo de fondeo | 54, frentes D-G |
| 31 mapa de ventaja sobre el mono | 52, parte R | 46 paso 10 | 51 |
| 33 economía del fondeo | 54, frentes A-C | 47 paso 12 | 51 |
| 34 validación MT5 y pool | 55 (su §0.5 es ahora el §1) | 48 pasos 16.5 y 17 | 52, partes V y Q |

## Cómo se despacha

> Lee `docs/encargos/51-pasos-10-a-12-transferencia.md` y ejecútalo entero. Es tu encargo completo: no necesitas
> leer el plan grande ni los otros encargos. Si algo te bloquea, párate y dímelo.

## Protocolo anticolisión

Tres ficheros son compartidos y los tocan varios agentes:

- **`docs/DEPENDENCIES.md` se regenera, nunca se fusiona.** Si hay conflicto, `python3
  tools/depmap.py` y se queda lo que salga.
- **`requirements.txt`: se añade línea, nunca se reordena.**
- **`ledger/thresholds.yaml`: un módulo nuevo añade sus filas al final de su sección y lee el valor
  con `ledger:<clave>`** (`knowhow/pipeline/thresholds-live-in-the-ledger.md`). Mover un umbral es del dueño.

## Qué devuelve cada agente

Todos cierran igual: **qué hizo · qué verificó, con la salida pegada · qué dejó sin hacer y por
qué · qué descubrió que merezca ir a `knowhow/`.**

## Idioma

Español, como el resto de `docs/` cuyo lector es el dueño. El código, los `README.md` de carpetas de
código y `knowhow/` siguen en inglés (`CLAUDE.md`).
