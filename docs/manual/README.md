# docs/manual — el manual de uso

Está escrito **en castellano** y para un humano, no para una sesión futura. Es la única excepción a
la regla "Files in English" del `CLAUDE.md`, y es deliberada: su lector es el dueño del proyecto.

## Leerlo

```bash
python3 tools/manual.py
xdg-open docs/manual/AlgoProject-Manual.pdf
```

Un solo PDF con todos los capítulos, portada e índice. También puedes leer los `.md` sueltos en
GitHub o en el editor: son el original, el PDF es solo el resultado.

## Qué hay aquí

| archivo | qué es |
|---|---|
| `00-empezar.md` | instalación, cómo se ejecuta cualquier cosa, dónde acaban los datos, las reglas de SQX que no se rompen |
| `01-analisis-is-oos.md` | el análisis IS/OOS: qué responde, cómo se corre, cómo se lee el informe y el explorador |
| `02-filtros.md` | el barrido de filtros: cuánto mejora cada filtro candidato el resultado OOS y a costa de cuántas estrategias |
| `03-comparar-muestras.md` | la comprobación entre generaciones: si las conclusiones de una muestra se cumplen en otras |
| `04-decaimiento.md` | el decaimiento estrategia por estrategia: cuánto edge sobrevive fuera de muestra y si te la quedas |
| `40-sqx-lab.md` | instalar y refrescar el kit de autoría de SQX sin `/plugin`, que en este entorno no existe — y por qué un catálogo rancio inventa bloques |
| `39-crossmarket-lote.md` | el paso 10 automático: juzga la población entera por amplitud y escribe el veredicto que `/curate` aplica |
| `05-retest-mercados.md` | el retest en mercados adicionales: si el sistema gana por acertar cuándo entra o por estar comprado |
| `06-mover-estrategias.md` | aplicar un veredicto dentro de SQX: borrar de la databank las estrategias descartadas, con comprobación de identidad y registro de lo que había |
| `29-puerta.md` | la puerta OOS: pasar un databank entero por una cascada de cribas —sanidad, métricas, degradación, forma, el mono, la familia y la redundancia— y salir con una lista de supervivientes y el motivo de cada descarte |
| `27-curar.md` | escribir el veredicto tú mismo: un filtro sobre las métricas o una estrategia elegida por su nombre |
| `07-montecarlo.md` | el Monte Carlo de robustez: de qué depende el resultado de una estrategia — del orden, de qué operaciones salieron, de la ejecución o del régimen |
| `08-spp.md` | el perfil Sys. Param Permutation a CSV: cuántas permutaciones sobreviven y cuánto se aleja tu estrategia de la permutación mediana |
| `33-spp.md` | configurar los SPP en SQX: las dos tareas de permutación de un custom project, con la rejilla del dueño, el tope de permutaciones escrito y no heredado, y la aceptación del propio crosscheck apagada para que sea un mapa y no un filtro |
| `09-diccionario-spp.md` | el inventario completo: cada campo que sale de una estrategia con SPP, con su nombre exacto y qué es. La página de consulta mientras escribes el análisis |
| `09-wfm.md` | la matriz Walk-Forward a CSV: cada celda, cada tramo con sus fechas y sus parámetros, el rendimiento dentro y fuera de muestra, y los trades repartidos por tramo |
| `10-github.md` | tener el proyecto subido a GitHub y poder clonarlo en otro ordenador: qué viaja en el repositorio, qué no, y qué hay que hacer en el clon |
| `11-retest-mc.md` | el Monte Carlo Retest: ocho tareas aisladas que vuelven a ejecutar el backtest entero contra una entrada perturbada, para saber **cuál** de ellas rompe la estrategia |
| `32-mcretest.md` | configurar el MC Retest en SQX: las ocho tareas de un custom project escritas de una vez, cada una perturbando una sola cosa, con la de distancia mínima sólo si la población lleva órdenes stop o limit |
| `13-barras.md` | la librería de barras: un solo dato guardado (el minuto) y todos los timeframes calculados desde él, cómo se sincroniza con SQX y cómo se entera de que actualizaste data |
| `34-wfm.md` | configurar la Walk Forward Matrix en SQX: las 30 celdas, la ventana `oos2` que sólo esta tarea puede escribir, y las dos reglas del dueño — cada mirada la gasta, y no se lee hasta que 17, 18 y 19 estén los tres hechos |
| `14-walkforwardmatrix.md` | el análisis de la matriz Walk-Forward: si lo que optimiza bien predice lo que va bien después, cuánto deriva el óptimo entre tramos, y por qué la unidad es la celda y no el tramo |
| `15-sppultra.md` | el reconocimiento SPP: qué parámetros mueven el resultado, cuáles están demostradamente muertos, si la familia entera es ruido, y el diseño de las 5.000 variantes que sale de ahí |
| `17-pipeline.md` | el encadenador: mete las ~100 estrategias madre de un databank, vuelve al cabo de unos días y lee los veredictos. Reanudable, con el registro de lo que va pasando mientras pasa, y el borrado de variantes con su prueba de que no se pierde nada |
| `18-variantes.md` | la fábrica de variantes: coge el diseño que salió del reconocimiento SPP y escribe las 5.000 estrategias en disco, con la tabla que dice qué combinación lleva cada archivo y los controles que delatan una cadena rota |
| `19-wfc.md` | ¿sirve de algo optimizar los parámetros? Fabrica muchas versiones de una estrategia, las retestea todas con la misma partición IS/OOS y dibuja un punto por combinación: lo que ganó dentro contra lo que ganó fuera. Cubre `sqx.variants.execute`, `sqx.variants.collect` y `studies.optimisation.wfc.report` |
| `39-nube-de-parametros.md` | la nube de clones: si el punto elegido es un pico de suerte o una meseta, qué parámetros mandan de verdad, si la superficie se rebaraja cada año, y qué rinde la meseta entera repartida contra el punto único |
| `40-forma-del-beneficio.md` | de qué pocas cosas depende el resultado: cuántas operaciones y cuántos meses lo sostienen, si las operaciones se agrupan —y entonces barajarlas subestima la caída— y si la media cambió dentro de la muestra |
| `42-calidad-de-la-entrada.md` | si la señal de entrada vale algo por sí sola: cuánto corre el precio a favor y en contra desde cada entrada, contra entradas al azar a las mismas horas, y cuánto edge se pierde llegando tarde |
| `43-ledger.md` | el libro mayor de la búsqueda: una línea por búsqueda durante toda la vida de un estudio, el embudo entero, cuánta historia se ha gastado, y las dos reglas que ahora se hacen cumplir solas —nadie mira el `oos2` fuera de los pasos 17 y 19, y el paso 20 no se lee hasta tener los tres |
| `20-donde-esta-todo.md` | el mapa de los datos: dónde quedan las estrategias generadas, las métricas, los backtests, los informes y los veredictos, qué se borra a propósito y qué no se borra nunca |
| `24-costes.md` | qué le cobras a cada mercado y en qué unidad: los cuatro ficheros de `assets/`, las dos clases (forex contra todo lo demás), las dos trampas de unidad que cuestan dinero, y los mercados adicionales donde se comprueba el edge |
| `25-actualizar-datos.md` | el botón «Update all» automatizado: descarga en el maestro con la GUI cerrada, cuenta las 7.546 estrategias antes y después porque cada sync se las puede llevar, y refresca las fechas de `_policy.yaml` al terminar |
| `26-nulos.md` | el test del mono: miles de versiones imaginarias de una estrategia sobre las mismas velas, cambiando solo cuándo entra; por qué el estadístico elegido decide el veredicto más que el mono, y por qué un mono que entra al azar en el oro pierde dinero |
| `35-app-plantillas.md` | la aplicación de escritorio: la matriz de cobertura de la librería de plantillas, la ficha de cada una con sus corridas y su veredicto, y el chat que entrevista una idea hasta dejar el brief escrito y el comando listo |
| `36-taxonomia.md` | la taxonomía de bloques —los 767 que el builder puede sortear de verdad, listos para etiquetar por familia— y la librería de paletas que se construye encima |
| `45-app-puerta.md` | la zona de la puerta IS/OOS: las cosechas, el embudo criba a criba, el scorecard por estrategia con su curva y sus métricas dentro y fuera, y el botón que corre la puerta con los umbrales a la vista |
| `46-knowhow.md` | el knowhow en fichas: cómo encontrar un hecho leyendo lo mínimo (grep de `q:` y la cabecera), cómo escribir uno nuevo sin volver al diario, y lo que se ahorra: 43× menos tokens por consulta, medido
| `44-app-estrategias.md` | la zona de estrategias de la ventana: los databanks exportados como los agrupa SQX, las estrategias de cada uno, y al pulsar una, qué dijo ya cada módulo de análisis sobre ella y el comando de lo que falta |
| `38-app-activos.md` | la zona de activos de la ventana: los diecinueve instrumentos y los cuatro ficheros compartidos, con sus costes, tramos y rangos editables sin abrir un YAML |
| `37-wfc-retest.md` | el retest de las variantes para el WFC y el CSCV: tres tareas de SQX, una por tramo (`build`, `oos1`, `oos2`), cada una a sus costes y con los mercados adicionales dentro |
| `38-exposicion.md` | la exposición: cuánto tiempo de mercado le costó a la estrategia lo que ganó, contra el buy and hold al mismo riesgo — el paso 21, el último de la secuencia |
| `_PLANTILLA.md` | **la plantilla obligatoria.** Se copia para documentar cada módulo nuevo |
| `PENDIENTE.md` | los comandos que aún no tienen página. Solo atraso heredado; no crece |
| `assets/` | las capturas. Salidas reales, nunca inventadas |
| `AlgoProject-Manual.pdf` | generado, no está en git. Se reconstruye en segundos |

## La regla

**Un comando nuevo sale con su página de manual en el mismo trabajo que lo crea.** Es la regla 9 del
`CLAUDE.md` y `tools/checks.py` la comprueba: si un script tiene un `__main__` y no aparece —ni por
su ruta ni por su comando `-m`— ni en una página del manual ni en `PENDIENTE.md`, la comprobación
falla.

El motivo es que un análisis que nadie sabe ejecutar no existe. La documentación escrita semanas
después la escribe alguien que ya olvidó qué confundía al principio, que es justo lo que hay que
explicar.

## Por qué markdown y no un PDF a mano

El PDF no se puede editar ni comparar entre versiones. El markdown sí: se ve qué cambió en cada
commit, se corrige una frase sin rehacer el documento, y el PDF se regenera con un comando. El
original es el `.md`; el PDF es un producto.

`tools/manual.py` usa Chrome en modo headless para imprimirlo, y la ruta del navegador vive en
`config/machine.yaml` como todo lo que depende de la máquina.
