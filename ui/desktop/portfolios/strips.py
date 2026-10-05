"""What each rail module of PORTFOLIOS puts in its settings strip: one line of what it is, selectors, launchers."""

# selector: (key, label, tooltip, kind) — kind `combo` is filled from the daemon's answer
# (`options`), `edit` is typed. launcher: (text, action of ui.daemon.portfolios.commands, tooltip).
FIRM = ("firm", "Empresa", "Quita del pool las estrategias que esa empresa prohíbe. «—» = ninguna.", "combo")
PLAN = ("plan", "Plan", "El plan de la empresa de fondeo, del catálogo.", "combo")
MODULES = {
    "Analizar": {
        "intro": "La cartera (o la estrategia) elegida abajo: sus cifras, su curva y sus miembros. Solo los tramos "
                 "que ya se han leído: oos2 no se dibuja hasta que un veredicto lo abre.",
        "selectors": (), "launchers": ()},
    "Correlación": {
        "intro": "Cuánto se parecen las estrategias del pool entre sí, pareja a pareja, medido en build. Dos que se "
                 "parecen demasiado no pueden ir en la misma cartera.",
        "selectors": (FIRM,
                      ("freq", "Frecuencia", "Con qué P&L se miden Pearson y Spearman: el de cada mes o el de cada "
                       "día. Las dos tienen que pasar.", "combo"),
                      ("measure", "Medida", "Cuál de las medidas de pareja se pinta en la matriz.", "combo")),
        "launchers": (("Calcular parejas", "universe", "Reconstruye la curva diaria de cada estrategia del pool y "
                       "mide todas las parejas en build. Solo Python; no toca SQX ni oos."),)},
    "Constructor": {
        "intro": "La cartera para cuenta real: se buscan combinaciones admisibles del pool, se puntúan por rangos "
                 "en build y la mejor se juzga contra carteras al azar en oos1.",
        "selectors": (FIRM,),
        "launchers": (("Buscar cartera", "real", "Puntúa las combinaciones admisibles del pool en build y deja la "
                       "mejor. No lee oos."),
                      ("Juzgar: veredicto", "verdict", "Mide la cartera elegida contra el azar en oos1 y, si pasa, "
                       "abre oos2 UNA sola vez. Pide confirmación."))},
    "Fondeo": {
        "intro": "La cartera para pasar el challenge de un plan: la etapa A criba combinaciones y riesgos por "
                 "P(pasar); la etapa B mide las finalistas con tres Monte Carlo y las juzga.",
        "selectors": (PLAN,),
        "launchers": (("Calcular etapa A", "stage_a", "Busca en el pool la combinación y el riesgo con más "
                       "P(pasar) en build para ese plan."),
                      ("Etapa B y veredicto", "stage_b", "Corre los tres Monte Carlo sobre las finalistas de la run "
                       "elegida abajo y la juzga. Usa todos los núcleos. Pide confirmación."))},
    "Banco": {
        "intro": "Qué plan comprar con la caja: el valor esperado de cada plan con cada política de recompra, "
                 "según cuánto del edge fuera de muestra se dé por perdido (h), contra el mono.",
        "selectors": (("bank", "Tabla", "Cuál de las tablas calculadas se enseña.", "combo"),
                      ("plan", "Plan de la curva", "El plan cuya curva VE(h) se dibuja.", "combo"),
                      ("horizon", "Horizonte (días)", "Cuántos días se simula la caja. Decisión tuya: no hay valor "
                       "por defecto. No compares tablas de horizontes distintos.", "edit"),
                      ("edge_from", "Edge de", "Los tramos fuera de muestra de los que se toma el edge: oos1, u "
                       "oos1,oos2 si el veredicto abrió oos2. Decisión tuya.", "edit"),
                      ("n_paths", "Caminos", "Cuántos caminos de Monte Carlo. Más caminos, menos error.", "edit")),
        "launchers": (("Calcular la caja", "bank", "Tres pasos en un trabajo: los caminos de la cartera de fondeo "
                       "elegida abajo, la caja por plan sobre ellos, y la decisión."),)},
    "Pesos": {
        "intro": "¿Algún método de pesos mejora a los pesos iguales fuera de muestra? El walk-forward lo compara en "
                 "oos1. Informa: no cambia la cartera.",
        "selectors": (),
        "launchers": (("Calcular walk-forward", "weights", "Compara cada método de pesos con pesos iguales sobre "
                       "la cartera del camino real elegida abajo, en oos1."),)},
    "Incubación": {
        "intro": "El tramo nuevo después de oos2, en papel o en real, contra la banda de la propia historia de la "
                 "cartera.",
        "selectors": (), "launchers": ()},
}
ARCHIVE = "Archivo"
STATIC = {"freq": [("monthly", "Mensual"), ("daily", "Diaria")]}
PREFILLED = {"n_paths": "10000"}
