# PLANTILLA — copiar esto al documentar algo nuevo

No se borra ni se renombra. Se copia a `NN-nombre-del-modulo.md` y se rellena.
Las secciones marcadas **obligatoria** no se pueden omitir; `tools/checks.py` no las revisa
una por una, pero el auditor sí, y una página sin ellas no sirve para lo que existe.

Regla de oro: **lo escribe alguien que sabe, para alguien que no.** Si una frase solo se entiende
sabiendo cómo está programado por dentro, está mal escrita.

---

## N. Título — qué hace, en una línea

### Qué pregunta responde  *(obligatoria)*

Dos o tres frases en cristiano. No "calcula correlaciones de Spearman", sino "te dice si una
métrica que se ve bien en el histórico sigue viéndose bien después".

### Cuándo lo usas, y cuándo no  *(obligatoria)*

Cuándo tiene sentido correrlo. Y sobre todo cuándo **no** sirve, que es la mitad que siempre falta.

### Antes de empezar  *(obligatoria)*

Qué tiene que existir ya: datos exportados, SQX abierto o cerrado, el worker parado, lo que sea.
Si hay que hacer algo en la GUI de SQX antes, se dice aquí paso a paso.

### Cómo se ejecuta  *(obligatoria)*

El comando entero, copiable, con rutas reales y no con `<placeholders>` a medias:

```bash
python3 ruta/al/script.py --project XAUUSD --databank OOS
```

Una tabla con cada flag: qué es, si es obligatorio, qué pasa si no lo pones.

| flag | obligatorio | qué hace |
|---|---|---|
| `--project` | sí | nombre del proyecto tal y como aparece en SQX |

Cuánto tarda, y si toca SQX o no. Eso decide si lo puedes lanzar con la GUI abierta.

### Qué produce  *(obligatoria)*

Rutas exactas de todo lo que escribe, y qué es cada archivo. Si sobrescribe algo, se dice aquí
con todas las letras.

### Cómo se lee el resultado  *(obligatoria)*

**Con capturas reales del output real.** Van en `assets/`. Una imagen con números inventados es
peor que ninguna imagen. Si el resultado es un número, se explica qué valor es bueno y cuál malo.

### Un ejemplo completo  *(obligatoria)*

De principio a fin, con la salida de verdad pegada. Alguien que no ha visto el módulo nunca tiene
que poder seguirlo sin preguntar nada.

### Qué NO te dice  *(obligatoria)*

Los límites. Qué conclusión parece que puedes sacar pero no puedes. Esta sección es la que evita
que el análisis se use para decidir algo que no soporta.

### Si algo falla

Los errores que van a salir de verdad y qué significan. No un catálogo de excepciones: los dos o
tres que pasan en la práctica.
