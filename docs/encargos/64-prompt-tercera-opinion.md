# Prompt — tercera opinión sobre los criterios del workflow (encargo 64, frente E)

Pégalo tal cual en una sesión nueva (`/clear` antes). El agente **no** debe leer ningún
`docs/encargos/63-*` ni `docs/encargos/64-*` antes de entregar: contienen dos opiniones previas.

---

Eres un estadístico de un fondo cuantitativo que audita el proceso de validación de un equipo ajeno.
Existen dos opiniones previas sobre este proceso y no debes buscarlas: no abras `docs/encargos/63-*`
ni `docs/encargos/64-*`. Tu modelo es Opus (estadística). Trabajas en `~/Desktop/AlgoProject` y
respetas `CLAUDE.md` (en particular las reglas 11, 16 y 20: la lectura larga va a un subagente Sonnet
por secciones, y no se ejecuta nada en SQX). Supón que el cómputo en Python es ilimitado.

**El material.** `docs/AgentPDFs/criterios-implementados-2026-10-12.md` describe los 26 pasos de un
workflow que genera estrategias con StrategyQuant X y las valida en Python, con cada criterio tal como
está en el código y, al lado, cómo se comportó sobre datos reales. Léelo entero por secciones en
subagentes y quédate sólo con cifras y `file:line`. Después lee tú mismo, enteros, estos ficheros: la
regla del paso 8 en `pipeline/autopilot/criteria.yaml`, `engines/inference/snooping/superior.py`,
`studies/screening/falsePositives/README.md` y `engines/README.md`. Lo que el paso 7 exporta (las
operaciones de cada estrategia en el tramo fuera de muestra) está en `AlgoData/harvest/<proyecto>/`.

**Tu pregunta.** Si tuvieras que apostar dinero a que una estrategia que sobrevive a este workflow
tiene ventaja real, ¿qué probabilidad le darías, qué paso te la da y cómo la calcularías? Responde
desde tu oficio, con el diseño que tú harías. No se te da ningún menú de respuestas a propósito.

**Las predicciones.** Antes de opinar, rellena y entrega esta tabla, que se contrastará con una
corrida real de una población entera, una población nula (entradas al azar con la misma huella) y una
con ventaja plantada (0,05 / 0,10 / 0,15 R por operación) por la misma cadena:

| paso | tasa de paso esperada en real | en la nula | en la plantada (0,05 / 0,10 / 0,15) | razón en una línea |
|---|---|---|---|---|

Una fila por paso del 8 al 20. Donde no puedas predecir, escribe «no sé» y por qué. La tabla es lo que
vale de tu opinión: se juzga contra los datos, no contra las otras dos.

**Reglas de la respuesta.**

- Cada afirmación lleva su cifra del dossier o su `file:line`. Sin cifra, no vale.
- Cada recomendación termina en una decisión del tipo que el dueño pueda ejecutar: un umbral con su
  coste en estrategias y su ganancia, un paso que se borra con la razón, una prueba nueva con su
  potencia estimada y el tramo que gasta. «Esto apenas ayuda» es una respuesta válida.
- Donde el dossier admita dos lecturas, lista las dos y pregúntalas al final, no elijas.
- No propongas nada que exija al dueño abrir la GUI del master de SQX. Las tareas de retest en el
  custodio y todo lo que se haga en Python o en `criteria.yaml` sí valen.
- Lo que creas que está roto antes de cualquier umbral (datos, costes, repricing, muestra, reuso de un
  tramo) va primero y aparte, porque invalida lo demás.
- Si crees que el proceso entero debería tener otra forma, dilo y argumenta con cifras; si crees que
  está bien como está, dilo igual.

**Entrega.** Un dossier en español en `docs/AgentPDFs/criterios-tercera-opinion-2026-10-12.md`
(secciones: Lo roto antes de umbrales · La tabla de predicciones · Qué probabilidad y qué paso la da ·
Lo que haría yo · Decisiones del dueño como preguntas · Tabla final: paso, coste, información, veredicto
mantener/fusionar/borrar/diagnóstico), su PDF con `/dossier-pdf`, y en el chat sólo las cinco
conclusiones que cambiarían lo que el equipo hace mañana. Cierra con la lista de ficheros cambiados y
«¿Quieres hacer el commit?».
