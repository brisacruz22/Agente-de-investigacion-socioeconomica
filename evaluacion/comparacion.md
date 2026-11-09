# Comparación: Claude Code sin y con MCP y skills

Las mismas 10 preguntas (`evaluacion/preguntas.csv`: 4 del BCRP, 4 de la ENAHO, 2 combinadas) se corrieron en dos
modos con `uv run evaluacion/evaluar.py`. Resultados por pregunta en `evaluacion/resultados.csv`.

## Diseño

| | Modo A, sin MCP ni skills | Modo B, con MCP y skills |
|---|---|---|
| Modelo | `claude-opus-5-5` | `claude-opus-5-5` |
| Instrucción | La misma: un número en «valor» (o `null` si no puede obtenerlo), su fuente y una interpretación breve | La misma |
| Carpeta de trabajo | Carpeta temporal vacía: no ve `CLAUDE.md`, `.claude/skills/`, `salidas/` ni los datos | Raíz del repositorio |
| Herramientas habilitadas | Ninguna (`--tools ""`, `--strict-mcp-config`) | `Bash`, `Read`, `Glob`, `Grep`, `Skill`, `ToolSearch` y el servidor MCP `bcrp` (`.mcp.json`) |
| Sesiones | Una sesión independiente por pregunta (`claude -p --no-session-persistence`), 10 en paralelo | Una sesión independiente por pregunta, de a una (`limpiar.py` escribe en `salidas/`) |

- **Respuestas esperadas:** se calcularon con `evaluacion/verdades.py` antes de la corrida, sin el MCP ni las skills.
  El BCRP se leyó directo de su API oficial; la ENAHO, directo de las `.dta` de los módulos 34, 02 y 05. No se
  cambiaron después de ver los resultados.
- **Tolerancia:** se fijó por pregunta en `preguntas.csv`. Por ejemplo, ±0.5 millones de US$, ±0.1 pp en pobreza y
  ±0.02 en la correlación.
- **Herramientas usadas:** se leyeron de la salida `stream-json` de cada sesión, es decir, de las llamadas que el
  modelo hizo de verdad, no de lo que dijo haber usado.
- **Preguntas combinadas:** cuentan como correctas solo si aciertan el número **y** la interpretación cumple el
  criterio de `preguntas.csv`. La interpretación la calificó una evaluadora humana (columna `interpretacion_ok`).

## Resultados

| | Modo A | Modo B |
|---|---|---|
| Correctas | **0 / 10** | **10 / 10** |
| Incorrectas | 1 | 0 |
| No contestadas (`null`) | 9 | 0 |
| Errores de ejecución o tiempo agotado | 0 | 0 |
| Tiempo promedio por pregunta | 12.0 s (9.8 a 15.9) | 26.8 s (18.9 a 42.5) |
| Llamadas a herramientas por pregunta | 0 | 3.0 en promedio |

Tiempo promedio según el tipo de pregunta: en el modo A, 11.0 s (BCRP), 11.4 s (ENAHO) y 15.4 s (combinadas); en el
modo B, 22.0 s, 31.9 s y 26.3 s.

### Por pregunta

| Pregunta | Verdad | Modo A | Modo B | Herramientas del modo B |
|---|---|---|---|---|
| `bcrp_exp_lima` | 15,031.03 millones US$ | `null` | 15,031.03 ✔ | MCP `buscar_series`, `serie` |
| `bcrp_min_arequipa` | 5,377.89 millones US$ | `null` | 5,377.89 ✔ | MCP `comparar_departamentos` |
| `bcrp_pesca_ancash` | 829.35 millones US$ | `null` | 829.35 ✔ | MCP `buscar_series`, `serie` |
| `bcrp_cobre_arequipa` | 453,836.34 tm finas | `null` | 453,836.34 ✔ | MCP `buscar_series`, `serie`, `metadatos` |
| `enaho_pobreza_puno` | 39.94 % | `null` | 39.94 ✔ | Skill `limpiando-enaho`, `Bash` |
| `enaho_gasto_moquegua` | S/ 1,163.86 | `null` | 1,163.86 ✔ | Skill `limpiando-enaho`, `Bash` |
| `enaho_ing_trabajo` | 70.80 % | `null` | 70.80 ✔ | Skill `limpiando-enaho`, `Bash` |
| `enaho_empleo_agro` | 22.54 % | 24.6 ✘ | 22.54 ✔ | Skill `limpiando-enaho`, `Bash`, `Grep`, `Read` |
| `ambas_mineria_pobreza` | Apurímac, 23.96 % | `null` (interpretación: sí) | 23.96 ✔ (interpretación: sí) | `Glob`, `Bash` |
| `ambas_spearman` | −0.141, débil | `null` (interpretación: no) | −0.141 ✔ (interpretación: sí) | `Glob`, `Read`, `Bash` |

**Mejoraron:** las 10 preguntas pasaron de incorrectas o sin respuesta en el modo A a correctas en el modo B.
**Empeoraron:** ninguna.

## Principales errores y comportamientos

1. **El modo A casi siempre se abstuvo.** En 9 de 10 preguntas devolvió `null` y explicó que no podía verificar la
   cifra sin acceso a la fuente. En lugar de inventar, nombró dónde estaría el dato (síntesis regionales del BCRP,
   informe de pobreza del INEI). Su único número fue de memoria y estuvo fuera de la tolerancia: 24.6 % de ocupados
   en el agro frente a 22.54 % (2.1 pp de diferencia). Además, mezcló una categoría más amplia del INEI («agricultura,
   pesca y minería»).
2. **En el texto, el modo A sí arriesgó cifras sin verificar.** Aunque dejó «valor» en `null`, escribió rangos «de
   memoria» que en dos casos son incorrectos:
   - Pesca de Áncash «entre US$ 400 y 600 millones»: la verdad es 829.35.
   - Pobreza de Apurímac «entre 30 y 35 %»: la verdad es 23.96.

   Solo el rango del cobre de Arequipa (430 a 470 mil TMF) contiene la verdad. Un usuario que leyera solo el texto se
   llevaría cifras equivocadas.
3. **En las preguntas combinadas, el modo A reconoció el departamento pero no pudo dar el dato.** En
   `ambas_mineria_pobreza` nombró Apurímac (por Las Bambas) «según mi memoria, sin verificar». Cumple el criterio
   literal, aunque sin la pobreza la pregunta falla. En `ambas_spearman` no calculó la correlación ni dijo si la
   relación era fuerte o débil.
4. **El modo B citó siempre la fuente rastreable.** En las del BCRP, el código de serie y el periodo (con la URL de la
   API). En las de la ENAHO, la variable, el factor de expansión y que pasaron las 14 validaciones. En las combinadas,
   además, aclaró que es una asociación descriptiva y no causal.

## Limitaciones del experimento

- **Criterios de interpretación.** Fueron redactados con el asistente de IA y fijados antes de la corrida, pero
  ninguna persona los revisó antes de ejecutar. Además, el asistente que los redactó es el mismo modelo que se evaluó,
  lo que puede sesgarlos hacia lo que ese modelo suele responder.
- **El criterio de `ambas_spearman` depende en parte del valor numérico.** Si el número es correcto, decir «débil» es
  casi automático. Un criterio más exigente habría pedido también mencionar que n = 25 y que se cruzan años distintos
  (2022 y 2024). La respuesta del modo B igual menciona que «con n = 25 la cifra no se distingue de cero».
- **El criterio de `ambas_mineria_pobreza` quedó corto.** Acepta nombrar Apurímac de memoria. Debió exigir que el
  departamento saliera de un dato consultado. Se aplicó tal como estaba escrito, sin cambiarlo.
- **En las combinadas, el modo B leyó resultados ya calculados.** No llamó al MCP ni a las skills: leyó con `Glob` y
  `Bash` los archivos `salidas/cruce_*.csv` de la Parte 3. Sus respuestas son correctas y vienen de un cálculo
  verificado, pero esta corrida no muestra que el agente rehaga el cruce desde cero. Eso se muestra en la corrida del
  agente (`evidencias_ia/integracion/09_corrida-agente_2026-11-09.md`).
- **No se registró qué comando corrió cada `Bash`.** En las preguntas de la ENAHO no se puede confirmar si se volvió a
  correr `limpiar.py` o si se leyeron las salidas existentes.
- **Una sola corrida por pregunta y modo.** No se midió cuánto varían las respuestas si se repite la misma pregunta.
- **Comparación de tiempos.** El modo A corrió en paralelo y el B de a una. Los tiempos son por pregunta, pero no se
  midieron en las mismas condiciones de carga.

## Conclusión

Con el MCP y las skills, Claude Code pasó de 0 a 10 respuestas correctas, a cambio de unos 15 segundos más por
pregunta (26.8 s frente a 12.0 s). Sin herramientas, el modelo en general no inventó el valor pedido: se abstuvo. Pero
tampoco pudo responder, y en el texto dejó estimaciones de memoria que a veces eran incorrectas. El aporte de las
herramientas no fue solo dar la cifra exacta, sino hacerla **rastreable**: cada respuesta del modo B dice de qué serie,
variable y factor de expansión sale, y cuál es el periodo. Esto se mostró con 10 preguntas de cifras concretas. No
mide la calidad de análisis más abiertos, y en las combinadas el modo B se apoyó en resultados ya calculados del
repositorio.
