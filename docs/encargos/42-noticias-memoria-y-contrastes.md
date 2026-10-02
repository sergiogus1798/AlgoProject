# 42 · Noticias en el tester, una memoria que sabe por qué, y tres contrastes — encargo con tres frentes

**Tu oficio:** jefe de un equipo de tres agentes. Planificas, repartes, revisas cada diff tú mismo
y devuelves un solo informe.
**Tu encargo:** cinco piezas que el dueño aprobó el 2026-10-02, repartidas en tres frentes que no
comparten ningún fichero.

Lee `CLAUDE.md` · `CODESTYLE.md` · `docs/encargos/README.md` (protocolo anticolisión y qué
devuelve cada agente) · `docs/AgentPDFs/repos-externos-2026-10-02.md` (de dónde sale cada repo que
se nombra aquí, con sus avisos de licencia). Cada frente dice abajo qué más leer.

---

## 0 · De dónde sale

Conversación del 2026-10-02. El dueño pidió una búsqueda exhaustiva de repos externos y, sobre su
resultado, eligió qué implementar. Prioridad suya: **fondeo primero**. Lo que quiere al final es
una fábrica de agentes coordinados que investigue, genere plantillas y lo pruebe todo sola; estas
cinco piezas son las que no dependen de nada más.

**Ya despachado en esa conversación, con su propio prompt — no lo hagas tú:** el final de la cadena
(autopilot del 16.5 al 26, F3-F5 del fondeo, `weeklyReconciler`); las ideas gastadas dentro de la
cuenta de ensayos del ledger; la potencia del perfil de mercado y su medición agrupada; el
`literatureScout` que busca papers. Si encuentras a otra sesión tocando algo de eso, es lo
esperado.

**No toques:** umbrales ni criterios de ningún paso (`criteria.yaml`, `ledger/thresholds.yaml`):
otros agentes los están calibrando. Ni SQX: los dos workers están ocupados con esa calibración, y
nada de este encargo los necesita.

## 1 · Reglas para los tres frentes

- Una carpeta, una rama, sin worktrees y sin commits (regla 12). Hay otras sesiones editando este
  árbol: antes de tocar un fichero mira `git status` y su fecha de modificación.
- Cada agente recibe en su brief **la lista de carpetas que posee** y la prohibición de salir de
  ella. Los tres ficheros compartidos se tratan como dice el protocolo anticolisión.
- Regla 11: lo ambiguo se pregunta. Cada frente trae abajo sus preguntas para el dueño: van
  **todas juntas en tu primer mensaje**, cada una con sus lecturas y tu recomendación. Lo que no
  dependa de la respuesta arranca sin esperar.
- Código de terceros: se lee o se porta lo mínimo, con su atribución, y solo si la licencia lo
  permite (MIT, BSD, Apache). GPL, AGPL y repos sin licencia son solo para leer y comparar salidas.
  Lo que se clone va a `scratch/`, nunca al árbol del repo, y **nunca se ejecuta contra nuestras
  instalaciones** de SQX ni contra el terminal de MT5.
- Todo comando nuevo lleva su capítulo en `AlgoData/manual-fuentes/` (regla 8), toda carpeta su
  fila en el `README.md`, todo hallazgo su tarjeta en `knowhow/`, y al final
  `python3 tools/depmap.py && python3 tools/checks.py` en verde.
- El informe de un agente no es evidencia: lee su diff y corre sus tests antes de darlo por bueno.

---

## 2 · Frente A — el filtro de noticias dentro del tester de MT5

**Posee:** `mt5/newsfilter/` y su capítulo `75-filtro-noticias`.
**Lee:** `mt5/README.md` · `mt5/newsfilter/README.md` · `knowhow/eng/ea-news-filter.md` ·
`knowhow/eng/ftmo-news-vs-mt5-importance.md` · `.claude/skills/ea-news/SKILL.md` · OPEN.md #85.

**El hueco.** `mt5.newsfilter` escribe el filtro en el EA que exporta SQX, pero ningún calendario
existe dentro del Strategy Tester: allí el filtro no hace nada. Hoy no se puede saber cuánto le
cuesta a una estrategia la regla de noticias de la firma en la que va a operar.

**Qué se construye.**
1. **El histórico del calendario**, en `AlgoData`. Fuente principal: el propio calendario de MT5
   exportado desde el terminal (es el mismo que el filtro usa en vivo, con sus códigos de evento y
   su importancia). Segunda fuente para la carpeta roja de Forex Factory que usa Hantec:
   `janickfarrell/newfac` (MIT) o `ehsanrs2/forexfactory-scraper` (GPL: solo sus datos, no su
   código). Las dos se cruzan y las discrepancias se cuentan.
2. **El modo tester del filtro**: dentro del tester lee ese histórico de un CSV; en vivo sigue
   igual que hoy. Referencia de diseño: `sushiix-trader/mql5-news-filter` (Apache-2.0, 3
   estrellas: leerlo entero antes de fiarse de nada).
3. **La lectura que decide**: la misma estrategia en el tester con filtro y sin él — operaciones
   que no se abrieron, las que se cerraron antes de tiempo, y la diferencia de resultado y de
   peor día.

**Trampas que ya se conocen.** El reloj: el servidor va en EET con su cambio de hora, Forex Factory
da la hora de Nueva York con su desfase, y el tester corre en la hora del servidor; una hora de
error mueve todas las ventanas. FTMO no usa la importancia de MT5 sino su lista propia de 37
códigos. El tester solo lee ficheros de su carpeta común.

**Preguntas para el dueño.**
- Desde qué año hace falta el histórico.
- Si la segunda fuente es obligatoria para dar el histórico por bueno, o basta la de MT5.
- Sobre qué estrategia y qué firma se hace la primera lectura con y sin filtro.

**Hecho cuando:** un EA parcheado, corrido en el tester sobre un tramo con publicaciones conocidas,
deja de abrir y cierra donde el filtro dice, comprobado contra tres publicaciones elegidas a mano;
y hay un test con una publicación sintética cuya respuesta se conoce. El terminal de MT5 es uno:
antes de usarlo mira que no lo tenga otra sesión (`mt5/README.md`).

---

## 3 · Frente B — una memoria que sabe por qué murió cada idea

**Posee:** `studies/research/memory/`, `studies/research/board/proposal.py` y
`proposalmd.py`, `.claude/agents/ideaExpert.md`, `.claude/agents/researchDirector.md`, y el agente
nuevo.
**Lee:** `studies/research/README.md` y los de `memory/` y `board/` ·
`docs/AgentPDFs/director-de-investigacion-2026-10-01.md` §4, §6 y §7 ·
`pipeline/autopilot/README.md` (qué escribe `judge.py` en `verdict.csv`) · los dos agentes.

**El hueco.** La memoria guarda dónde murió una corrida (`died@<etapa>`), no por qué. El
`ideaExpert` propone sin tener que mirar lo que ya fracasó en esa celda, nadie distinto de él
revisa sus ideas, y lo que una idea predice (cuánto opera, cuánto dura) no se compara nunca con lo
que el build produjo. Sin eso, una corrida cerrada no enseña casi nada al director.

**Qué se construye — tres piezas que se apoyan una en otra.**
1. **El fracaso tipado.** Cada corrida cerrada gana una causa con vocabulario cerrado, sacada de
   las razones que el autopilot ya escribe por estrategia y por paso, más qué descarta y qué
   sugiere probar. Las corridas en modo desarrollo siguen sin contar. Patrón:
   `hch-wang/Negative_Knowledge` (se copia el esquema, no el código).
2. **La hoja de hipótesis.** Antes del build cada idea fija: operaciones por año esperadas,
   duración esperada, dónde **no** debería funcionar y qué resultado la mata. La propuesta la
   sella. Al cerrar la corrida se compara con lo que salió, y un desajuste es una causa más.
3. **El revisor.** Un agente distinto del que propone recibe las tres ideas y la memoria de la
   celda, e intenta tumbarlas: mecanismo, coste, parecido con lo ya probado, lecturas ambiguas.
   No mide nada sobre datos — no añade miradas a la cuenta de ensayos. El `ideaExpert`, antes de
   proponer, adopta o rechaza por escrito cada fracaso previo de la celda. Prompts de referencia:
   `Kaimen-Inc/Co-Scientist` (Apache-2.0), revisor y proximidad.

**Preguntas para el dueño.**
- El vocabulario de causas: propón una lista corta y que la apruebe él.
- Si el veredicto del revisor puede retirar una idea de la propuesta o solo anotarla; el veto
  sigue siendo del dueño en cualquier caso.
- Qué desajuste entre lo predicho y lo construido cuenta como fallo (el umbral es suyo).

**Hecho cuando:** `tests/test_research_memory.py` y `test_research_board.py` cubren la causa, la
hoja y el rechazo de una propuesta sin hoja o sin revisión; una propuesta real generada de punta
a punta lleva las tres cosas; y está medido, en dólares, cuánto encarece el revisor cada propuesta
(hoy 10-30 $). Ningún paso lanza nada en SQX.

---

## 4 · Frente C — tres contrastes contra código ajeno

**Posee:** `tests/` (ficheros nuevos y su fila), `studies/data/spread/`, y solo lectura de todo lo
demás.

### C1 · El Sharpe deflactado contra `jsharpe`

**Lee:** `engines/inference/README.md` · `core/significance.py` · `core/surface/plateau.py` y
`trials.py` · `ledger/trials.py`.
Contrastar nuestro PSR, el mínimo de historial, el número de ensayos independientes y el Sharpe
deflactado contra `tschm/jsharpe` (MIT) sobre series sintéticas. Las dos convenciones que rompen
estas fórmulas sin avisar: el Sharpe va por observación, no anualizado, y la curtosis es la no
excedente (3 para una normal). **Una discrepancia es un hallazgo que se reporta con los dos
números, no algo que se corrige en silencio.** El test guarda los valores de referencia como
cifras fijas: `jsharpe` no entra en `requirements.txt`.

### C2 · El spread desde OHLC como quinto modelo

**Lee:** `studies/data/spread/README.md` y `model.py` · `docs/AgentPDFs/spread-real-2026-09-27.md`
· `assets/RULES.md`.
El estimador EDGE de `eguidotti/bidask` (MIT, JFE 2024) saca el spread efectivo de las barras, sin
ticks. Entra como un candidato más en `model.MODELS` y compite en la misma validación que ya
elige modelo por su error en los años que no vio. Su contrato es distinto del de los cuatro que
hay (no se ajusta sobre días con ticks): si no cabe en el registro sin forzarlo, dilo antes de
tocarlo. **El resultado es una decisión por activo:** dónde gana, dónde no, y por cuánto. Si no
gana en ninguno, se dice y no se añade. No reescribe ninguna ficha de `assets/`.

### C3 · Nuestros parsers contra los de fuera

**Lee:** `core/README.md` (los lectores de `.sqx` y `.cfx`) · `mt5/README.md` (`report.py`,
`tester.py`) · `tests/README.md` (los tests dorados).
Solo lectura. Comparar con `DAVIDAROCA27/sqx-mcp` (parsers de `.sqx`, `.cfx` y `.mq5`, y cómo
trata la sincronización de databanks), `masdevid/mt5-quant` y `PHUICMT/mcp-mt5` (informes del
tester, generación del `.ini`). Lo que se busca: casos que ellos tratan y nosotros no. Cada uno se
comprueba contra un fichero real nuestro antes de escribirlo; lo que se confirme va a `OPEN.md`
con su número y a una tarjeta. No se instala ninguno de esos servidores MCP.

**Hecho cuando:** C1 tiene su test en verde o su discrepancia reportada; C2 su tabla por activo y
su decisión; C3 su lista, con cada punto marcado «comprobado en nuestro fichero X» o «no aplica».

---

## 5 · Lo que devuelves

Primer mensaje, en la primera media hora: el plan en una tabla y todas las preguntas juntas.

Al final, en español: por frente, qué se hizo · qué se verificó, con la salida pegada · qué quedó
sin hacer y por qué · qué se descubrió para `knowhow/`. Después la lista de ficheros cambiados y,
como última línea, **¿Quieres hacer el commit?**
