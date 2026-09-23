# 23. Skills — qué hay instalado y qué sobra

### Qué pregunta responde

Cuántas skills hay, qué hace cada una, cuánto cuesta invocarla y cuándo se tocó por última vez.
Sirve para dos cosas distintas: que tú veas de un vistazo cuáles se han vuelto innecesarias, y que
una instancia nueva de Claude sepa qué tiene disponible sin ir abriendo carpetas.

### Cuándo lo usas, y cuándo no

Cuando añadas o quites una skill, y cuando quieras auditar qué está pesando. No sirve para saber si
una skill **funciona**: solo lee lo que declara.

### Antes de empezar

Nada. Lee carpetas del disco.

### Cómo se ejecuta

```bash
python3 tools/skillmap.py
```

Sin flags. Reescribe `docs/SKILLS.md` de la marca `<!-- generado -->` hacia abajo y **respeta todo
lo que haya encima**, que es donde vive el juicio: las familias, las candidatas a retirar, y cómo se
paga una skill. Instantáneo.

### Qué produce

```
docs/SKILLS.md
```

Dos tablas, una por sitio: las del proyecto (`.claude/skills/`) y las globales
(`~/.claude/skills/`). Ordenadas de más pesada a menos, porque las que hay que cuestionar son las
caras.

### Cómo se lee el resultado

```
| skill              | ~tokens al invocar | ficheros | último cambio | para qué |
| analysis-crossmarket |            2,734 |        1 |    2026-09-21 | ...     |
| template-run         |            1,189 |        1 |    2026-09-22 | ...     |

12 skills, 13,383 tokens de cuerpo en total, 52 KB en disco.
```

Tres columnas que deciden algo:

- **`~tokens al invocar`** es el cuerpo del `SKILL.md`, que solo se carga cuando la usas. La
  descripción (~90 tokens) está **siempre** en contexto, la invoques o no. Por eso el número de
  skills casi da igual y el peso de cada una no.
- **`ficheros`**: más de uno significa que tiene material de referencia que carga solo si hace
  falta. Eso es bueno — es cuerpo que no se paga por defecto.
- **`último cambio`**: una skill que lleva meses quieta y describe un flujo que ya cambió es una
  trampa, no documentación.

**La señal de que una skill hay que partirla** es cargar 6.000 tokens para hacer un 20 % de lo que
explica. La de que hay que retirarla es que su descripción compita con otra mejor: el riesgo no es
el gasto, es que una petición tuya enrute a la equivocada.

### Un ejemplo completo

```
$ python3 tools/skillmap.py
docs/SKILLS.md: 12 de proyecto, 4 de global
```

Y lo que sale a la luz al leerlo: las cuatro globales de sqx-lab suman **18.255 tokens**, más que
las doce del proyecto juntas (13.383), y ninguna conoce los defaults de esta casa. Están marcadas
como candidatas a retirar en la cabecera de `docs/SKILLS.md`.

### Qué NO te dice

- **No dice si una skill funciona**, ni si lo que declara sigue siendo cierto. Lee frontmatter.
- **No dice cuántas veces se ha usado.** No hay telemetría; "último cambio" es lo más parecido y no
  es lo mismo.
- **No mide lo que una skill carga a demanda.** La columna de tokens es el `SKILL.md`; sus ficheros
  de referencia pueden multiplicar eso si se leen todos.

### Si algo falla

`IndexError` al leer un `SKILL.md` — ese fichero no tiene frontmatter entre `---`. Es un error de
la skill, no del mapa.

Los cambios a mano desaparecen — los escribiste **debajo** de la marca `<!-- generado -->`. Todo lo
que quieras conservar va encima.
