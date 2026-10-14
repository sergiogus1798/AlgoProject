# Prompt — segunda opinión sobre los criterios del workflow (encargo 63, frente 0)

Pégalo tal cual en una sesión nueva (`/clear` antes). El agente **no** debe leer
`docs/encargos/63-criterios-del-workflow-opinion-y-rediseno-de-la-cola.md` antes de entregar.

---

Eres un estadístico de un fondo cuantitativo que audita el proceso de validación de un equipo ajeno.
No has visto ninguna opinión previa sobre este proceso y no debes buscarla: no abras
`docs/encargos/63-*`. Tu modelo es Opus (estadística). Trabajas en `~/Desktop/AlgoProject` y respetas
`CLAUDE.md` (en particular las reglas 11, 16 y 20: la lectura larga va a un subagente Sonnet por
secciones, y no se ejecuta nada en SQX).

**El material.** `docs/AgentPDFs/criterios-implementados-2026-10-12.md` describe los 26 pasos de un
workflow que genera estrategias con StrategyQuant X y las valida en Python, con cada criterio tal como
está en el código y, al lado, cómo se comportó sobre datos reales (recuentos de pasa / no pasa,
tiempos, ⚠ discrepancias). Los umbrales viven en `pipeline/autopilot/criteria.yaml` y
`ledger/thresholds.yaml`. Léelo entero por secciones en subagentes y quédate sólo con cifras y
`file:line`.

**Tu pregunta no es «¿estricto o laxo?».** Es ésta: **si yo tuviera que apostar dinero a que una
estrategia que sobrevive a este workflow tiene ventaja real, ¿qué probabilidad le daría, y qué paso me
la da?** Responde desde tres ángulos, cada uno con su sección:

1. **Potencia y multiplicidad.** Por paso: cuántas hipótesis mira, cuántas miradas sobre el mismo
   tramo acumula, qué tamaño de muestra tiene (operaciones, no barras) y qué potencia le queda para
   detectar una ventaja de 0,05-0,15 R por operación. Señala cada paso cuya tasa de paso en real no
   se distingue de la que tendría bajo la nula, y cada paso que no puede fallar por construcción.
   Di dónde se reutiliza un tramo (build, oos1, oos2) para más de una decisión.
2. **Economía del proceso.** Minutos de CPU y de SQX por madre y por paso frente a la información que
   aporta cada uno (bits de discriminación: cuánto cambia la probabilidad de ventaja real entre antes
   y después del paso). Ordena los pasos por coste/información y di cuáles borrarías, cuáles
   fusionarías y cuáles correrían sólo como diagnóstico sin veredicto.
3. **Lo que haría un fondo.** Qué prueba única y prerregistrada diseñarías para el tramo final, con
   qué nula (trader al azar de la misma huella, volteo de signo, bloques), cuántas miradas, cómo
   corriges por las K candidatas, y qué harías con el límite de ~35 operaciones/año: validar
   estrategias sueltas, familias o cestas. Si crees que el proceso entero debería invertirse
   (validar primero la familia de la idea, generar después), dilo y argumenta.

**Reglas de la respuesta.**

- Cada afirmación lleva su cifra del dossier o su `file:line`. Sin cifra, no vale.
- Cada recomendación termina en una decisión del tipo que el dueño pueda ejecutar: un umbral con su
  coste en estrategias y su ganancia, un paso que se borra con la razón, una prueba nueva con su
  potencia estimada y el tramo que gasta. «Esto apenas ayuda» es una respuesta válida.
- Donde el dossier admita dos lecturas, lista las dos y pregúntalas al final, no elijas.
- No propongas cambiar nada que exija al dueño abrir SQX: todo lo que recomiendes se hace en Python
  o en `criteria.yaml`.
- Lo que creas que está roto antes de cualquier umbral (datos, costes, repricing, muestra) va
  primero y aparte, porque invalida lo demás.

**Entrega.** Un dossier en español en `docs/AgentPDFs/criterios-segunda-opinion-2026-10-12.md`
(secciones: Lo roto antes de umbrales · Potencia y multiplicidad · Economía · Lo que haría un fondo ·
Decisiones del dueño como preguntas · Tabla final: paso, coste, información, veredicto
mantener/fusionar/borrar/diagnóstico), su PDF con `/dossier-pdf`, y en el chat sólo las cinco
conclusiones que cambiarían lo que el equipo hace mañana. Cierra con la lista de ficheros cambiados y
«¿Quieres hacer el commit?».
