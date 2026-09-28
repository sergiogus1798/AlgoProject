# 28 · El hueco aleatorio, a prueba — encargo autocontenido

**Tu oficio:** Python, SQX en el custodio para la parte A, y la skill que lo automatiza.
**Tu encargo es medir si la búsqueda genética aporta ventaja o sólo sobreajuste.** No se quita nada:
se mide con tres piezas, y el ledger dice quién tiene razón.

Lee `CLAUDE.md` (sobre todo las reglas duras 1-6, 10 y 11) · `CODESTYLE.md` · `docs/AgentPDFs/WORKFLOW.md` ·
`sqx/CLAUDE.md` · `sqx/templates/README.md` · `.claude/skills/template-run/SKILL.md` ·
`studies/screening/gate/README.md` · `studies/readings/structure/README.md` · `ledger/README.md` ·
`knowhow/conditions/no-seeded-hash-in-sqx.md`.

---

## 0 · De dónde sale

Del dossier `docs/AgentPDFs/ideas-de-internet-y-libros-2026-09-27.md`, §1.4. Chan dice que los
algoritmos genéticos «rindieron miserablemente hacia delante» (*Quantitative Trading*, pp. 26-27).
Shaw empieza siempre por una hipótesis y evita buscar a ciegas (*Stock Market Wizards*, pp. 143 y
145). Eckhardt define el sobreajuste como grados de libertad que no aportan información (*New Market
Wizards*, p. 48). El dueño, 2026-09-28:

> *«Me parecen muy buenas ideas las 3, apúntalas en un encargo. La 1 tiene que ir con automatización
> por parte de Claude.»*

Cada plantilla del proyecto es la condición fija del dueño, que es la hipótesis, más un hueco
aleatorio que SQX rellena, que es minería. La pregunta es si ese hueco trae supervivientes reales o
sólo ruido que la cadena después tiene que matar.

## 1 · Objetivos

1. **Parte A — el A/B:** saber, por familia, si el hueco aleatorio produce más supervivientes reales
   por hora de CPU que la condición fija sola. **Automatizado de punta a punta por Claude** con una
   skill: el dueño pide «prueba el hueco de `<plantilla>` en `<activo> <TF>`» y recibe la tabla.
2. **Parte B — la atribución:** que cada superviviente diga cuánto de su ventaja viene de la condición
   fija y cuánto del hueco.
3. **Parte C — el bloque de ruido:** medir cuánto «compra» un grado de libertad falso dentro de esta
   cadena.
4. Que las tres dejen sus filas en el ledger, con la familia y el brazo, para que la tabla de
   rendimiento por familia (idea 4 del dossier `ideas-de-edge-2026-09-26`) las pueda leer.

## 2 · Parte A — el A/B, automatizado

### 2.1 · El diseño

Para una plantilla, un activo y un timeframe, dos brazos idénticos en todo salvo en el hueco:

| brazo | plantilla |
|---|---|
| **A · fija** | sólo la condición fija del dueño, sin `RandomCondition` |
| **B · fija + hueco** | la plantilla tal cual, como se construye hoy |

Mismo activo, mismas ventanas, mismos costes de `assets/`, mismos filtros de aceptación, misma función
de aptitud, y **el mismo presupuesto** (§2.3). Cada brazo en su propio proyecto (`Test_ab_<plantilla>_A_<n>`,
`…_B_<n>`), creado con `sqx.projects.builder --workflow`, porque un build y su retest viven en un
proyecto (regla dura 10).

**Repeticiones.** El generador da resultados distintos con cada semilla, y eso ya está aceptado como
idea en el dossier de edge. Un solo par no dice nada: por defecto tres builds por brazo, alternando A
y B, nunca los tres de un brazo seguidos.

### 2.2 · Lo que se compara

Cada build pasa por lo que ya existe: retest `oos1` en SQX, cosecha y puerta (`/oos-gate`), con el mono
de la puerta. Por brazo y repetición:

| medida | qué es |
|---|---|
| generadas y aceptadas | lo que SQX produjo y lo que pasó sus filtros |
| supervivientes de la puerta | las que la puerta mantiene |
| **exceso sobre el mono** | supervivientes menos lo que el azar daría, de `engines/inference/excess.py` |
| **exceso por hora de CPU** | la cifra que decide |
| distintas | supervivientes agrupadas por solape de operaciones: 45 de 231 ya salieron idénticas una vez |

**La lectura.** Si B no saca más exceso por hora que A, con su intervalo, el hueco sólo añade
minería en esa familia. Si saca más, el hueco trae algo. El informe no decide: pone los dos brazos
lado a lado, con sus intervalos, y dice si la diferencia supera la variación entre repeticiones.

### 2.3 · Decisiones del dueño antes de lanzar — pregúntalas (regla dura 11)

1. **El presupuesto igual.** ¿Mismo tiempo de reloj (`--minutes`), o mismo número de estrategias
   generadas? Con el mismo tiempo, A genera muchas más, porque su espacio es pequeño. Propuesta:
   mismo tiempo, porque la pregunta es qué da más por hora de máquina.
2. **Qué hacer si el brazo A agota su espacio.** Sin hueco, la búsqueda puede repetir la misma
   estrategia. ¿Se para cuando deja de encontrar nuevas? Propuesta: sí, y se anota.
3. **Cuántas repeticiones** por brazo. Propuesta: 3.
4. **Qué plantillas** primero. Propuesta: una de las `buildConfirmed` de `AlgoData/templates/registry.csv`.

### 2.4 · La automatización: la skill `/ab-hueco`

Una skill en `.claude/skills/ab-hueco/`, con un orquestador Python en `sqx/experiments/ab_hole.py` (o
donde encaje según `sqx/CLAUDE.md`), que hace, en este orden y sin intervención:

1. **Preflight:** `python3 -m core.assets <SÍMBOLO>` (regla dura 5). Si sale distinto de 0, se para y
   pregunta. Lee `runs.csv` por si ya se probó.
2. **El brazo A:** fabrica la plantilla gemela sin el hueco a partir de la original
   (`sqx/templates/holes.py` sabe dónde está cada `RandomCondition`) y la registra en la librería como
   variante de prueba, con su procedencia.
3. **Los proyectos:** `sqx.projects.builder` para cada brazo y repetición, con el mismo `--minutes`.
4. **Los builds, uno a uno en el custodio:** antes de cada arranque, el protocolo de las reglas
   duras 1-3: `ListAgents`, los proyectos recientes del worker y la cola del log del día. Si otra
   sesión lo está usando, **espera y avisa**, no lo toca. Arranca y para sólo con `bin/sqx-worker.sh`.
   Entre arranque y recogida, sólo `-project action=status`. El final es `Project finished` en el log
   de SQX. Pulso cada ~3 minutos, como pide el dueño para los runs largos.
5. **El retest `oos1` y la cosecha** de cada brazo con las herramientas que ya existen.
6. **La puerta** sobre cada cosecha, con el mismo `config.yaml`.
7. **El ledger:** una fila por build y por criba, con `family` y un campo `arm` (`A`/`B`) y la
   repetición. Si `ledger/study.py` no tiene dónde ponerlo, se añade la columna con su contrato.
8. **El informe** A contra B (§2.2), escrito en `AlgoData/reports/…/abHueco/` con la forma de contrato
   de `core/study/CONTRACT.md`, para que la ventana lo pinte.
9. **La limpieza:** los proyectos `Test_` se retiran con `python3 -m sqx.projects.retire` al acabar
   (regla dura 6), con el worker parado.

La skill **es reanudable**: si se corta a mitad, sabe qué builds ya están y sigue desde ahí, igual
que `pipeline/`.

## 3 · Parte B — la atribución fija contra hueco

El paso 23 (`studies/readings/structure/`) ya hace una ablación por cada condición de entrada y mide
su ΔM por operación contra un recorte al azar. Le falta saber **cuál de las condiciones es la fija**.

- Etiquetar cada condición de la estrategia como `fija` o `hueco`, comparando con la plantilla de
  origen: la condición fija lleva el bloque del dueño, y la del hueco, lo que SQX eligió.
- Una fila de cabecera por superviviente: «de la ventaja medida, tanto viene de la condición fija y
  tanto del hueco», con los ΔM que ya calcula.
- En el ledger, la misma cifra por familia: ¿las supervivientes de esta plantilla viven de la idea
  del dueño o de lo que minó SQX?

Sigue siendo **diagnóstico, nunca selección**, como todo el paso 23. Sólo añade la etiqueta y el
agregado.

## 4 · Parte C — el bloque de ruido

Un bloque de condición que **no puede tener información** sobre el precio futuro, metido en el hueco
aleatorio, o como condición fija de una plantilla de control.

⚠️ **No se puede usar azar de verdad dentro de SQX.** El vocabulario sólo compone números de coma
flotante, sin las operaciones enteras de un hash con semilla
(`knowhow/conditions/no-seeded-hash-in-sqx.md`). Esa limitación es del vocabulario de bloques, no de SQX:
un **snippet Java** sí tiene aritmética entera. El dueño instaló el 2026-09-28 en el maestro el bloque
«(RAND) Random Entry» del plugin WinRateEdge, y autorizó usarlo. 🔬 Su código usa `Math.random()`
**sin semilla** (encargo 30, §1). Eso decide cómo sirve aquí:

- **El RAND sin semilla no es un grado de libertad falso.** Cambia en cada backtest, así que la
  búsqueda no puede ajustarlo: lo que mide es un **filtro aleatorio que se sortea de nuevo** en cada
  retest. Sirve como variante secundaria: ¿deja pasar la cadena una estrategia con un filtro al azar?
- **El ruido que pide Eckhardt es `RandomEntrySeeded`**, el bloque con semilla que construye el
  encargo 30 (§1.2). Su parámetro `Seed` es un grado de libertad puro: la búsqueda lo ajusta al pasado
  y no puede tener información sobre el futuro. **Es el candidato 0** de esta parte, y esta parte
  depende del encargo 30 para tenerlo.

Si el bloque con semilla no se puede compilar en el worker, el ruido tiene que ser un **reloj
irrelevante y determinista**. Candidatos, por orden de preferencia:

1. **Un reloj de periodo optimizable:** «el número de barra módulo P es igual a r», con P y r como
   parámetros que SQX puede mover. Es un grado de libertad puro, sin información. Necesita una forma
   de contar barras o de leer la hora en el vocabulario: compruébalo con `sqx/inspect/vocabulary.py`.
2. **La fase lunar,** calculada con la hora de la barra, `FLOOR` y la división. Es también la familia
   placebo del dossier (§3.1).
3. **Un dígito del precio,** por ejemplo el último dígito del cierre en puntos. Es casi ruido, pero no
   del todo independiente del precio: úsalo sólo si los dos primeros son imposibles, y dilo.

**La prueba de que es ruido.** Antes de usarlo, el bloque pasa la tarjeta de información sobre las
barras de `build`: su disparo no puede predecir el rendimiento siguiente. Si lo predice, no es ruido.

**Lo que se corre.** Tres variantes:

- La plantilla con el bloque de ruido **en el hueco**, en lugar del hueco libre.
- Una plantilla **cuya única condición fija es el ruido**.
- Un barrido de **complejidad**: builds limitados a 2, 4, 6 y 8 condiciones, con el ruido dentro,
  usando el `/ab-hueco` de la parte A como motor.

**Lo que se mide.** Cuántas llegan vivas a la puerta, a `oos1` y, si llegan, al paso 20. Cada una que
sobrevive con un bloque de ruido es un falso positivo de la cadena con nombre y apellidos. La curva de
supervivientes contra número de condiciones dice cuánto compra cada grado de libertad falso.

**Decisión del dueño:** ¿las plantillas con ruido pasan también por los pasos caros, del 9 al 20, o
se cortan en `oos1`? Propuesta: hasta `oos1`, y más allá sólo si sobrevive alguna.

## 5 · Verificación

1. **El brazo A no lleva hueco.** Antes de gastar CPU, `sqx/inspect/template_check` sobre la gemela:
   cero `RandomCondition`. Y después del build, que las estrategias llevan el bloque fijo de verdad
   (lo que ya comprueba `/template-run`).
2. **El ruido es ruido.** La tarjeta de información del §4, con su p, escrita en el informe.
3. **Las repeticiones difieren.** Si las tres de un brazo dan exactamente lo mismo, la semilla no
   cambia y las repeticiones no valen.
4. **El ledger cuadra** con lo que corrió, fila a fila.

## 6 · Cómo cierras

- Capítulo de manual en `AlgoData/manual-fuentes/` para `/ab-hueco` y para el bloque de ruido, con
  capturas reales, y su familia en `tools/manual.py` (regla dura 8).
- La skill aparece en `docs/SKILLS.md` al regenerar con `python3 tools/skillmap.py`.
- Tarjeta en `knowhow/` con el resultado del primer A/B y del barrido de complejidad: son hechos que
  cambian cómo se configura cada build.
- `python3 tools/depmap.py && python3 tools/checks.py`.
- Lista de ficheros cambiados y **¿Quieres hacer el commit?** (regla dura 12).

**Orden recomendado:** B primero (sólo Python, sobre datos que ya existen), después A, y C usando A
como motor.
