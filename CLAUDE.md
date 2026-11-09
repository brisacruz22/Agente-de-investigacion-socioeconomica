# Agente de investigación socioeconómica (Tarea 4, Python Intermedio)

Repo de Brisa (GitHub `brisacruz22`) para la tarea 4 del curso Python Intermedio (Q-Lab PUCP, profesor Alex Quispe).
Enunciado completo: https://github.com/d2cml-ai/Data-Science-Python/issues/201. **El issue es el mapa**: la estructura
de carpetas y los entregables siguen su árbol. Ante cualquier duda, volver a su lista de verificación.

## Pregunta de investigación (cerrada)

> ¿Cómo se relacionan las condiciones de vida de los hogares (pobreza, ingresos y gasto) entre departamentos según su
> actividad económica principal?

- Condiciones de vida: ENAHO 2024 (pobreza, ingreso y gasto por persona, composición del ingreso).
- Actividad económica principal: estructura productiva del BCRP (exportaciones por grupo, minería, pesca) y el empleo
  por rama del módulo 05 de la ENAHO.
- Limitaciones ya aceptadas: la ENAHO 2024 es transversal (no hay evolución de los hogares); las exportaciones por
  departamento llegan hasta 2022; se cruzan agregados departamentales con datos de hogares; es asociación descriptiva
  (n = 25), no causalidad. «Good enough is enough».

## Datos

Los microdatos viven **fuera del repo** y no se suben nunca:
`C:\Users\brisa\OneDrive\Documentos\PUCP\DIPLOMATURA-CCSS ML\Bloque 3_Python intermedio\Tarea 4_ agente de consultas socioeconomicas enaho-bcr\datos-base`

| Módulo | Archivo | Una fila por | Uso |
|---|---|---|---|
| 34 sumaria | `966-Modulo34/sumaria-2024.dta` (no la `-12g`) | hogar | Pobreza, ingreso, gasto |
| 02 miembros | `966-Modulo02/enaho01-2024-200.dta` | persona | Sexo, edad, residentes habituales |
| 05 empleo | `966-Modulo05/enaho01a-2024-500.dta` | persona | Rama de actividad (variable por confirmar en su diccionario) |

- El diccionario de la sumaria es `Sumaria-2024.pdf`, no `Diccionario2024.pdf` (ese es el general).
- Guía de las 163 variables de la sumaria por categoría: `.claude/skills/limpiando-enaho/reference.md`.
- Verificado con los datos: los montos de la sumaria son **anuales por hogar**; las líneas de pobreza, **mensuales por
  persona**. Un hogar es pobre exactamente cuando `gashog2d / mieperho / 12 < linea`, y con `factor07 × mieperho` la
  pobreza nacional da 27.58 %. La suma de las `gru*` no da `gashog2d`: el total se toma de `gashog2d`. El detalle de
  alimentos (`sg23`, `g05hd`…) no suma lo mismo que `gru1*`: revisar `ConstVarGasto-Metodologia actualizada.zip` antes
  de calcular el peso de los alimentos. Para comparar montos entre departamentos: monto / mieperho / 12 / `ld`.
- Validaciones obligatorias del issue: pobreza nacional ≈ 27.6 % (tolerancia 0.1 pp), 108,664 residentes habituales,
  25 departamentos, urbana ≈ 24.8 %, rural ≈ 39.3 %. Unir por `conglome`, `vivienda`, `hogar` como texto con ceros y
  `validate="m:1"`. Mapa por `ubigeo[:2]` con `FIRST_IDDP`, nunca por nombre; Lima (15) y Callao (07) separados.

## Parte 1 · MCP del BCRP (`mcp/server.py`)

Viene de `brisacruz22/mcp-bcrp` (sesión 04), copiado literal y luego extendido.

| Herramienta | Origen | Qué hace |
|---|---|---|
| `buscar_series`, `serie`, `resumen` | Sesión 04 | Buscar códigos, bajar datos, resumir sin cuentas a mano |
| `correlacion` | Ejemplo del issue, implementado en la sesión 04 | Herramienta de análisis que cumple ese requisito |
| `metadatos` | Idea de Brisa | Unidad (sacada del nombre si el catálogo la deja vacía), fuente original, cobertura, departamento y ccdd |
| `comparar_departamentos` | Tarea 4 | Una serie para todos los departamentos en un periodo, ordenada y con ccdd para cruzar con la ENAHO |
| `grafico` | Tarea 4 | `linea`, `area_apilada` (con `porcentaje`) o `barras`; PNG + CSV en `figuras/`; bases de python-graph-gallery.com |

- Tests: `mcp/test_server.py` (8 originales, **no se tocan**) + `mcp/test_propias.py` (2). Meta: `uv run pytest` → 10 passed.
- Series departamentales útiles del catálogo (4,764 en 28 temas): exportaciones por grupo de productos (25 dptos,
  hasta 2022), producción minera (hasta 2025), desembarque de anchoveta, electricidad, turismo (hasta 2019), PBI total
  (hasta 2023), crédito y depósitos, recaudación y gasto público. El BCRP separa Lima Metropolitana y Lima Provincias:
  en la ENAHO ambas son 15. El foco es la estructura productiva; lo demás es contexto.

## Reglas para el agente

- Ninguna cifra de memoria: toda cifra sale del MCP o de un script, citando serie y periodo (BCRP) o variable y factor
  de expansión (ENAHO). Siempre ponderar.
- Si una herramienta falla o falta un dato, decirlo; nunca rellenar.
- Asociación no es causalidad.
- Brisa debe poder explicar cada línea de código: explicar antes de escribir y no agregar piezas que no pidió.
- Brisa hace los commits desde GitHub Desktop.

## Evidencias de IA

- Cada vez que cerremos un paso de la tarea (un test que pasa, una skill terminada, un commit) o cuando Brisa se
  despida, recordarle en una línea correr `/export` y darle el nombre exacto del archivo y la subcarpeta de
  `evidencias_ia/` donde va (`mcp`, `skills`, `integracion` o `evaluacion`), con numeración correlativa y fecha:
  `NN_tema_AAAA-MM-DD.md`. Llevar la cuenta del último número usado leyendo `evidencias_ia/`.

## Estado (9 nov 2026) y siguiente paso

- [x] Pregunta cerrada; módulos 34, 02 y 05 descargados; guía de variables de la sumaria
- [x] Parte 1 escrita; probada sin conexión (5 tests con el catálogo real, herramientas nuevas con datos simulados)
- [x] Correr `uv run pytest` en la laptop: 10 passed con el BCRP real
- [ ] Parte 2: skills `limpiando-enaho`, `graficando-enaho`, `mapeando-enaho`
  - [x] `limpiar.py` con los módulos 34 y 02 (copiados a `datos/`), validado; sale `personas_2024.parquet`,
    `indicadores.csv` y `validacion.txt`
  - [x] `graficando-enaho`: pobreza, gasto o ingreso por área, sexo o departamento (factores mixtos, documentados en
    su SKILL.md); se activa sola y encadena `limpiando-enaho` si faltan las bases
  - [x] `mapeando-enaho`: mapa de pobreza, gasto o ingreso por departamento, unido por código, validado contra la
    sesión 16 (dif. máx. 0.05); se activa sola y encadena `limpiando-enaho`
  - [ ] **Después de validar:** agregar el módulo 05 (empleo por rama). Antes, confirmar en su diccionario la
    variable de rama y el factor (¿`fac500a`?), decidir cómo agrupar las ramas y a quiénes contar (ocupados, 14+)
  - [ ] Composición del ingreso (parte de «condiciones de vida»): sale de la sumaria (módulo 34), no del 05. Elegir
    en `reference.md` las variables (ingreso por trabajo, transferencias…) y agregarlas a `indicadores.csv`
- [ ] Parte 3: corrida del agente, `informes/informe_final.md`, 3 cifras verificadas a mano
- [ ] Parte 4: 10 preguntas (4 BCRP, 4 ENAHO, 2 combinadas), modos A y B, `comparacion.md`, README de 12 secciones
- [ ] Pendiente: copia de la guía de variables con una columna de palabras clave para búsqueda en lenguaje natural
- [ ] Evidencias de IA: exportar cada conversación, numerada (la 01 es la de planificación en claude.ai)
