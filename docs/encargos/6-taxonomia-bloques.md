# 6 · Etiquetar la taxonomía de bloques — encargo cerrado y autocontenido

Tu trabajo entero cabe en una frase: **rellenar el campo `archetypes` de cada bloque de
`sqx/blocks/taxonomy.yaml`.** Nada más. Ni una línea de código, ni un fichero nuevo, ni SQX.

Lee este fichero y ejecútalo. No necesitas el plan grande ni los otros encargos.

---

## 1 · Qué existe ya, y por qué

El builder de StrategyQuant X puede sortear **767 bloques**. Con tantos, genera estrategias que
mezclan un filtro de reversión a la media con un disparador de ruptura: combinaciones que dan buen
backtest y no describen ninguna hipótesis. El dueño quiere que, al construir sobre una plantilla de
ruptura, el builder solo pueda sortear bloques que peguen con una ruptura.

La tabla vacía ya está hecha y generada de la instalación real:

```
sqx/blocks/taxonomy.yaml     767 bloques en 83 categorías
```

Una fila:

```yaml
BookTriggers_user:                    # la categoría de SQX, es la clave padre
  CBlock_BBBreakoutUp:
    roles: [signal]                   # derivado, NO lo toques
    origin: own                       # derivado, NO lo toques
    form: BBBreakoutUp                # derivado, NO lo toques
    groups: [BookTriggers]            # derivado, NO lo toques
    archetypes: {}                    # <-- ESTO es tuyo, y solo esto
```

**Todo lo que no sea `archetypes` se regenera de la instalación y se pisa.** Si lo editas, tu
cambio se pierde en el siguiente refresco y habrás ensuciado el diff para nada.

## 2 · Lo único que escribes

`archetypes` es **un peso por familia**. Tres familias, fijadas por el dueño el 2026-09-24, y no se
inventan más:

| familia | qué es |
|---|---|
| `breakout` | el precio sale de un rango, un nivel o una banda, y se espera continuación |
| `mean_reversion` | el precio se ha estirado respecto de un centro, y se espera vuelta |
| `trend` | la dirección persiste: orden de medias, pendiente, fuerza direccional |

La escala, tal cual:

| valor | significa |
|---|---|
| `0` | **excluir**: este bloque contradice la tesis de esa familia |
| `1` | neutro: puede aparecer, sin preferencia |
| `2` | encaja |
| `3` | es característico de esa familia |

Las tres claves van siempre, aunque valgan 1:

```yaml
    archetypes: {breakout: 3, mean_reversion: 0, trend: 1}
```

Un bloque que dejes en `{}` queda **sin etiquetar** y no entra en ninguna paleta. Es una respuesta
válida solo si de verdad no sabes; no es el sitio donde aparcar lo difícil.

## 3 · La regla que decide el 90 % de los casos

**Etiqueta por lo que dice `form`, nunca por el nombre del indicador.** Un mismo indicador produce
bloques opuestos, y ahí es donde se equivoca todo el mundo:

| bloque | `form` | por qué |
|---|---|---|
| `BBBarClosesAboveUpper` | el cierre cruza **por encima** de la banda superior | ruptura: el precio escapa de la banda |
| `BBBarIsAboveUpper` | el cierre **está** por encima de la banda superior | estirado: lectura de reversión |

El primero es una **transición**; el segundo es un **estado**. Casi todas las familias de bloques
de SQX vienen en ambas formas y significan cosas distintas. Si `form` no te basta para distinguirlo,
ese bloque va a la lista de dudas (§7), no a una apuesta.

## 4 · Las tres reglas de criterio

1. **Un `0` es la decisión cara, y hay que justificarla.** Excluir estrecha la búsqueda; si te pasas,
   el builder deja de encontrar cosas y nadie sabrá por qué. Un `0` se pone solo cuando el bloque
   **contradice** la tesis, no cuando "no es muy de esa familia" — para eso está el `1`.
2. **Un bloque puede ser característico de dos familias.** `ATR` mide volatilidad y lo usan tanto la
   ruptura como la reversión. No fuerces una familia única.
3. **Lo neutro se etiqueta neutro.** Las horas, los días de la semana, los precios crudos (`Close`,
   `High`, `Ask`), los comparadores (`IsGreater`, `CrossesAbove`): `{breakout: 1, mean_reversion: 1,
   trend: 1}`. No son de ninguna familia y no deben excluirse de ninguna.

## 5 · El orden de trabajo

Por lotes, en este orden, y **reportando al terminar cada lote**:

| lote | qué | cuántos |
|---|---|---|
| 1 | los 171 bloques **propios** del dueño (`origin: own`) | 171 |
| 2 | `Comparisons`, `Price`, `Bar And Time` — el lote neutro, es rápido | ~74 |
| 3 | `Indicators` (papel `indicator` y `level`) | 116 |
| 4 | las categorías nativas de condición, de la más grande a la más pequeña | ~406 |

El lote 1 va primero a propósito: son los bloques que el dueño autoró con una intención concreta, y
sus nombres (`BreakoutLong`, `MeanReversion_user`, `TrendRegime_user`, `VolatilityRegime_user`) ya
llevan media respuesta. **Media, no toda: comprueba `form` igual.**

## 6 · Lo que NO tocas

Esto es lo que evita que pises a otro agente. La lista es cerrada:

- **Solo escribes en `sqx/blocks/taxonomy.yaml`, y solo en los campos `archetypes`.** Ningún otro
  fichero del repositorio.
- **No tocas `sqx/blocks/taxonomy.py`** ni ningún otro `.py`. Si crees que el generador tiene un
  fallo, lo reportas; no lo arreglas.
- **No creas paletas** (`sqx/blocks/palettes/`), no tocas `ui/`, no tocas `sqx/projects/`.
- **No tocas ninguna instalación de SQX**, no arrancas ningún worker, no construyes nada, no autoras
  bloques ni grupos. Este encargo no gasta CPU ni toca estado compartido.
- **No regeneras el fichero a mitad** con `python3 -m sqx.blocks.taxonomy`. Solo al final, una vez,
  como verificación (§8).
- **No añades familias**, no añades campos, no reordenas el fichero.
- **No ejecutas `tools/depmap.py`** — no cambias código, así que no hay mapa que regenerar.

## 7 · Las dudas se preguntan, no se resuelven

Regla del dueño: ante una ambigüedad de verdad, se pregunta. Aquí significa:

- Si `form` no te deja decidir si un bloque es transición o estado → lista de dudas.
- Si un bloque parece pedir una cuarta familia (volatilidad pura, microestructura, sesión) → **no la
  crees**. Anótalo y sigue con las tres.
- Si un bloque de `origin: own` tiene un `form` que no explica qué hace → lista de dudas, con el
  nombre del bloque y qué te falta saber.

La lista de dudas va en tu informe final, no en el YAML.

## 8 · Cómo cierras

Al terminar los cuatro lotes, **una sola vez**:

```bash
python3 -m sqx.blocks.taxonomy
```

Ese comando relee la instalación y **conserva** lo que has etiquetado. Su salida tiene que decir
`etiquetas 767 puestas, 0 por poner` (o el número que sea, si dejaste dudas sin etiquetar). Si dice
menos de las que pusiste, algo se perdió: párate y repórtalo, no lo vuelvas a correr.

Después:

```bash
python3 tools/checks.py
```

Tiene que salir igual de verde que antes de empezar. No has tocado código, así que si aparece un
problema nuevo no es tuyo — dilo, no lo arregles.

## 9 · Qué devuelves

Lo de siempre en esta carpeta: **qué hiciste · qué verificaste, con la salida pegada · qué dejaste
sin hacer y por qué · qué descubriste que merezca ir a `knowhow/`.** Y además, propio de este
encargo:

- **El recuento por familia**: cuántos bloques llevan `3`, `2`, `1` y `0` en cada una.
- **Los `0` justificados**, agrupados: no uno por uno, sino "los N bloques de estado de banda llevan
  `breakout: 0` porque …".
- **La lista de dudas** de §7, con el bloque y la pregunta concreta.
- **Las categorías que te han hecho dudar en bloque**, si las hay — son las que probablemente
  necesitan que el dueño decida algo antes.

## 10 · Lo que tienes que saber para no sacar conclusiones de más

Tres hechos medidos el 2026-09-24 que acotan lo que tus etiquetas pueden llegar a hacer. Están en
`knowhow/06-locations.md`, y no se te pide comprobarlos:

- Una paleta construida con tus etiquetas gobierna **solo los huecos libres** de una plantilla.
- Un hueco **atado a un grupo aleatorio** sortea ese grupo e ignora la paleta por completo.
- Un bloque **fijo** en la plantilla se salta la paleta también: es parte del esqueleto, no del pool.

Por eso `groups` está en la tabla que lees: un bloque con grupos es alcanzable por una vía que tu
etiqueta no controla. **No cambia cómo lo etiquetas** — la etiqueta describe el bloque, no la vía —
pero sí explica por qué el campo está ahí y por qué no debes borrarlo.
