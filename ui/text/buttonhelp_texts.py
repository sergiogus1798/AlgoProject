"""The registry of button sentences, keyed by the button text as the window shows it.

A key is the text as written in the code («▶ Lanzar en SQX»); `buttonhelp.normalise` drops the
signs and counts, so «▶ correr marcados (3)» finds «correr marcados». Two buttons that say the
same word and do different things are told apart by the class of the widget holding them:
«Clase › texto», nearest class first. A button's own tooltip is added below the sentence, so
a sentence here says what the button does and the tooltip keeps saying why it is off now.
"""

HELP = {
    # BIBLIOTECA · Nueva plantilla
    "Empezar de nuevo": "Borra la conversación y vuelve a la primera pregunta. No escribe nada "
                        "en disco ni en SQX.",
    "Enviar": "Manda la respuesta escrita y pasa a la siguiente pregunta. No escribe nada: el "
              "borrador sólo existe al terminar la entrevista.",
    "Elige tú": "Deja esta pregunta al default documentado del dueño; el brief dirá que se "
                "aplicó ese valor.",
    "Copiar el prompt": "Copia al portapapeles el comando para pegarlo en Claude Code, que es "
                        "quien escribe la plantilla. La ventana no instala nada en SQX.",
    "Copiar el brief en JSON": "Copia al portapapeles el brief de la plantilla en JSON, tal "
                               "como lo guardaría la librería.",
    # BIBLIOTECA · Plantillas y Paletas
    "Detail › Guardar": "Guarda el estado de la plantilla (borrador, validada…) y la nota en la "
                        "librería de plantillas. No toca SQX.",
    "PaletteBar › Guardar": "Escribe la paleta abierta, con los pesos cambiados y la política "
                            "de los bloques sin etiqueta, en sqx/blocks/palettes/. No toca SQX.",
    "Clonar": "Pide un nombre y crea una copia de la paleta abierta como paleta nueva, que ya "
              "se puede editar. No toca SQX.",
    "Borrar": "Tras confirmar, borra la paleta abierta de la librería. Una paleta por "
              "defecto no se puede borrar.",
    # PROYECTO · Proyectos
    "+ Nuevo proyecto": "Despliega el formulario de un proyecto nuevo: plantilla, activo, "
                        "timeframe, tamaño del build y para qué. Crear pide confirmación; no "
                        "arranca SQX.",
    # BIBLIOTECA · Activos
    "Nuevo activo": "Abre un formulario para dar de alta un instrumento, con todos sus costes "
                    "por pactar, y crea su fichero en assets/. No consulta SQX.",
    "Fichero entero": "Enseña u oculta la tabla con todos los valores del fichero del activo, "
                      "cada uno con su comentario.",
    "Retirar": "Tras confirmar, mueve el fichero del activo a assets/symbols/_retired/: deja de "
               "contar, pero no se pierde.",
    "AssetSpans › Aplicar": "Escribe en assets/_policy.yaml la fecha que has movido de este "
                            "tramo. Se enciende sólo cuando hay un cambio válido.",
    "Añadir": "Abre un cuadro para elegir categoría y mercado, y lo añade a los mercados del "
              "Cross Market de este activo.",
    "AssetSpans › Quitar": "Tras confirmar, quita este mercado de su categoría del Cross "
                           "Market del activo.",
    # BIBLIOTECA · Configuración SQX
    "SqxConfigZone › recargar": "Vuelve a leer los ficheros de configuración por si otra "
                                "sesión los cambió. No escribe nada.",
    "seguir leyendo": "Despliega el texto entero de esta explicación.",
    # Barra lateral
    "Recargar": "Vuelve a pedir al demonio los datos de las zonas que no se refrescan solas. "
                "No escribe nada; en SQX solo consulta el estado (status) de un worker en "
                "marcha, y no arranca ni para nada.",
    # PROYECTO · el carril del workflow
    "Lanzar en SQX": "Tras una pantalla de confirmación, arranca en un worker (nunca el "
                     "master) la tarea de SQX elegida en la lista de al lado.",
    "Continuar workflow": "Tras una pantalla de confirmación, borra en SQX lo que descartaste "
                          "en Databanks (con filtros y a mano), tras copiarlo a "
                          "AlgoData/projects/discards/, y lanza la tarea siguiente en un worker.",
    "correr marcados": "Corre en Python las pruebas marcadas del carril. Si alguna lee oos2 o "
                       "escribe en el ledger, lo pregunta antes. No toca SQX.",
    "todas las pruebas Python pendientes": "Corre a la vez toda prueba de Python sin "
                                           "resultado, salvo las que gastan oos2 o escriben "
                                           "en el ledger. No toca SQX.",
    "Correr workflow (hasta la próxima decisión)":
        "Tras confirmar el plan entero, encola un solo trabajo que corre en orden los pasos de "
        "SQX y de Python hasta el siguiente punto en que decides tú.",
    "Rehacer las filas de": "Rehace en el ledger las filas de los pasos 17 a 19 que corrieron "
                            "sin escribirlas (ledger.backfill). No toca SQX.",
    "PY": "Corre en Python las pruebas marcadas de este paso. Sin ninguna marcada, pregunta "
          "y corre las que no están en marcha y ni leen oos2 ni escriben en el ledger (esas, "
          "solo si no hay otras). En los pasos que leen el panel, pregunta antes sobre qué "
          "databank y filas del panel de Databanks. No toca SQX.",
    "SQX": "Tras confirmar, lanza en un worker todas las tareas de SQX de este paso juntas.",
    "SQX lanzar el paso": "Tras confirmar, lanza en un worker todas las tareas de SQX de este "
                          "paso juntas.",
    "SQX Activar el builder": "Tras confirmar, lanza en el custodio sólo la tarea de "
                              "construcción (CONSTRUCCION); el retest OOS es el paso 7, con "
                              "su propio ▶ SQX. El worker se para al acabar.",
    "Lanzar todos": "Corre a la vez todas las pruebas de este paso que se pueden correr aquí. "
                    "Antes pregunta por las que leen oos2 o escriben en el ledger. No toca SQX.",
    "correr los marcados de": "Corre las pruebas marcadas de los pasos que se ven en esa "
                              "pestaña del panel de databanks. No toca SQX.",
    "ver en Databanks": "Abre la zona Databanks en la pestaña donde se ven los resultados de "
                        "este paso.",
    "configuración": "Enseña los valores con los que corre esta prueba.",
    # PROYECTO · Databanks
    "⚙ Métricas": "Elige qué métricas enseña la tabla: quita las de siempre o añade "
                  "cualquier métrica de IS, OOS1, OOS2 o IS+OOS1 (sin datos se ve «–»). Se "
                  "guarda para este databank, en todas sus pestañas, y sigue al reabrir; los "
                  "otros databanks guardan la suya. «Restaurar vista por defecto» vuelve a las "
                  "de siempre.",
    # PROYECTO · Estrategia
    "IS+OOS1": "Estadísticas y distribución de IS y OOS1 juntas, como una sola muestra: la "
               "curva de OOS1 sigue donde acaba la de IS. Sin Sharpe de SQX, que no lo da junto.",
    "Ficha › %": "Enseña el drawdown de cada muestra en porcentaje del máximo anterior.",
    "Ficha › $": "Enseña el drawdown de cada muestra en dinero.",
    "Correr marcados de este panel": "Corre las pruebas marcadas en el raíl para esta pestaña "
                                     "sobre las filas elegidas (todas si no eliges ninguna); sin "
                                     "ninguna marcada, pregunta y corre todas las de la pestaña. "
                                     "No toca SQX.",
    "condición": "Añade una fila vacía de condición al filtro. No filtra hasta pulsar Aplicar.",
    "Guardar con nombre…": "Pide un nombre y guarda las condiciones de ahora en "
                           "AlgoData/filters/saved.yaml, sin aplicarlas.",
    "FilterRow › ×": "Quita esta condición del filtro. Lo aplicado no cambia hasta pulsar "
                     "Aplicar.",
    # PROYECTO · Estrategia
    "Archivar": "Pide el paso del workflow y una nota, y congela la estrategia en "
                "AlgoData/archive/ con todo lo calculado, como versión nueva que se abre desde "
                "Portfolios.",
    "plegar panel básico": "Oculta las curvas y las estadísticas básicas para dejar sitio a "
                           "los estudios.",
    "desplegar panel básico": "Vuelve a enseñar las curvas y las estadísticas básicas.",
    "Stats › IS": "Enseña las estadísticas de la muestra de construcción (IS).",
    "Stats › OOS": "Enseña las estadísticas fuera de muestra (oos1).",
    "Stats › OOS1": "Enseña las estadísticas fuera de muestra (oos1).",
    "Stats › OOS2": "Enseña las estadísticas de oos2, sólo cuando ya han corrido los pasos 17, "
                    "18 y 19.",
    "esta estrategia": "Corre este estudio en Python sobre la estrategia abierta, con los "
                       "valores del cajón de configuración. No toca SQX.",
    "toda la población": "Corre este estudio en Python sobre todo el databank, con los "
                         "valores del cajón. Tarda más. No toca SQX.",
    "solo": "Vuelve a correr sólo la subprueba elegida en la lista; se guarda aparte y no toca "
            "el run entero.",
    "cancelar": "Cancela el trabajo de este estudio que está en marcha.",
    "comparar los dos runs elegidos": "Pone lado a lado los dos runs elegidos en la lista "
                                      "(Ctrl+clic).",
    "comparar con esta estrategia": "Pone este estudio de la estrategia abierta al lado del de "
                                    "la estrategia elegida en la lista.",
    "restablecer valores de fábrica": "Devuelve cada valor del cajón al de config.yaml. El "
                                      "fichero no se toca nunca.",
    "Informe de lo que ves": "Escribe y abre una página HTML con exactamente lo que ves en "
                             "este estudio. No recalcula nada.",
    "Volver al guardado": "Vuelve a enseñar el resultado guardado, sin la re-ejecución "
                          "parcial.",
    "Ver al lado del guardado": "Pone el resultado guardado y la re-ejecución parcial lado a "
                                "lado. No cambia el fichero guardado.",
    "Ver fusionado": "Enseña el guardado con esta subprueba tomada de la re-ejecución. No "
                     "cambia el fichero guardado.",
    "ver los avisos restantes": "Despliega los avisos que están plegados.",
    "calcular": "Calcula en Python esta métrica para esta estrategia. No toca SQX.",
    "todo el databank": "Calcula en Python esta métrica para todas las estrategias del "
                        "databank, en paralelo. Tarda más.",
    "TradeGallery › IS": "Enseña operaciones de la muestra de construcción (IS).",
    "TradeGallery › OOS": "Enseña operaciones fuera de muestra (oos1). oos2 nunca se lee.",
    "cuantiles": "Enseña las operaciones en los cuantiles 0, 25, 50, 75 y 100 % del resultado: "
                 "la peor, la mediana y la mejor.",
    "otra muestra": "Saca cinco operaciones al azar, con una semilla nueva.",
    # OPERACIÓN y PORTFOLIOS
    "Leer ahora": "Lee ya el pulso del custodio (procesos, memoria, log) sin esperar al "
                  "minuto de la lectura automática. En SQX solo consulta el estado (status) "
                  "de un worker en marcha; no arranca ni para nada.",
    "Importar esta versión": "Abre en Estrategia la versión archivada elegida, tal como se "
                             "congeló. No calcula nada.",
}
