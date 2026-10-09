"""The Spanish sentence under each study section of the Configuración SQX zone."""

CSCV_HELP = ("Paso 18. Donde el WFC pregunta si esta superficie se mantuvo fuera de muestra, el "
             "CSCV pregunta lo que hay detrás: ¿la MANERA de elegir parámetros tiende a "
             "sobreajustar? Parte la historia en bloques, prueba cada mitad posible como dentro "
             "de muestra contra la otra, y cuenta cuántas veces la variante elegida dentro queda "
             "por debajo de la mediana fuera: eso es el PBO. Lee siempre build+oos1+oos2.")
SURF_HELP = ("Paso 18.5. ¿El orden de las variantes en el mercado principal se repite en los demás "
             "mercados (los de assets/_markets.yaml)? Un nulo de signos semanales, el mismo para "
             "todas las variantes, dice qué orden cuenta como casualidad. Decide la lectura "
             "build+oos1; la de oos2 sólo puede añadir LIMBO.")
WFM_HELP = ("Paso 19. La Walk Forward Matrix de SQX juzgada sólo con las operaciones que cierran en "
            "oos2, recobradas con los costes de oos2. L1 decide; el resto se anota. En modo fijo "
            "(el de partida) no existen las dos reglas de reoptimizado.")
GATE_HELP = ("Paso 8. Cada valor que lee la puerta, por nivel: cuánto se resta de deriva, cuántos "
             "sorteos, qué tope. Los umbrales con los que se juzga cada regla (>= 100, > 0…) viven "
             "en pipeline/autopilot/criteria.yaml, no aquí.")
FP_HELP = ("Falsos positivos. El control negativo de la cadena: monos que la cadena juzga como a "
           "una población real, y las poblaciones de prueba con ventaja plantada.")
