# Agente de investigación socioeconómica del Perú

Tarea 4 del curso Python Intermedio (Q-Lab PUCP). Enunciado:
[d2cml-ai/Data-Science-Python#201](https://github.com/d2cml-ai/Data-Science-Python/issues/201).

## 1. Objetivo

Construir un agente con Claude Code que investigue la realidad socioeconómica del Perú con datos oficiales y
respuestas verificables. El agente combina dos componentes:

- Un **servidor MCP** que consulta las series del BCRP.
- Tres **skills** que limpian, grafican y mapean la ENAHO 2024 del INEI.

Toda cifra sale de una herramienta o de un script, nunca de la memoria del modelo.

La pregunta de investigación es:

> ¿Cómo se relacionan las condiciones de vida de los hogares (pobreza, ingresos y gasto) entre departamentos según
> su actividad económica principal?

## 2. Arquitectura

```
                  Pregunta en lenguaje natural
                               │
                        Claude Code (agente)
             CLAUDE.md: reglas (ponderar, citar, no inventar)
                ┌──────────────┴───────────────┐
      Servidor MCP «bcrp»               Skills (.claude/skills/)
       (mcp/server.py)                         │
               │                limpiando-enaho → graficando-enaho
      API del BCRP (series,                    └→ mapeando-enaho
       catálogo de metadatos)                  │
               │                      Microdatos ENAHO 2024 (datos/)
 salidas/bcrp_*.csv, figuras/       salidas/, figuras/, mapas/
               └──────────────┬───────────────┘
                  analisis/cruzar.py (une por ccdd)
                               │
                   informes/informe_final.md
```

- El MCP devuelve los datos del BCRP con su código de serie, periodo, unidad y fuente. Con `guardar=True` deja un CSV
  con el código de departamento del INEI (`ccdd`).
- Las skills de gráficos y mapas llaman primero a `limpiando-enaho` si todavía no existe la base procesada.
- `analisis/cruzar.py` une ambas fuentes por `ccdd`, el código del departamento. Nunca une por nombre.

## 3. Herramientas MCP (`mcp/server.py`)

El servidor viene de [brisacruz22/mcp-bcrp](https://github.com/brisacruz22/mcp-bcrp) (sesión 04) y se extendió para
esta tarea.

| Herramienta | Qué hace |
|---|---|
| `buscar_series` | Busca códigos de serie por palabras en el catálogo oficial (categoría, grupo y nombre). Se puede filtrar por frecuencia |
| `serie` | Datos de una serie entre dos fechas, con la URL de la fuente |
| `resumen` | Variaciones, promedios y extremos de una serie, calculados en Python |
| `correlacion` | Correlación de Pearson entre dos series de la misma frecuencia, en los periodos que comparten |
| `metadatos` | Ficha de una serie: unidad (sacada del nombre si el catálogo la deja vacía), fuente original, cobertura, ámbito, departamento y `ccdd` |
| `comparar_departamentos` | Un mismo indicador para todos los departamentos en un periodo, ordenado y con `ccdd`. Con `guardar=True` escribe `salidas/bcrp_<texto>_<periodo>.csv` |
| `grafico` | Gráfico de `linea`, `area_apilada` (con `porcentaje`) o `barras`. Guarda el PNG y el CSV en `figuras/` |

Además, el servidor ofrece:

- **Recursos:** `bcrp://serie/{codigo}` (ficha de cualquier serie) y `bcrp://series/principales` (las más
  consultadas).
- **Prompt:** `informe(tema)`, una receta de informe breve con cifras del BCRP.

## 4. Skills (`.claude/skills/`)

| Skill | Qué hace | Salidas |
|---|---|---|
| `limpiando-enaho` | Une los módulos 34 (sumaria), 02 (miembros) y 05 (empleo) por `conglome`, `vivienda`, `hogar` (como texto con ceros a la izquierda). Filtra a los residentes habituales y pondera. Corre 14 validaciones, entre ellas la pobreza nacional (27.6 % ± 0.1), los 108,664 residentes y los 25 departamentos, y se detiene si alguna falla | `salidas/personas_2024.parquet`, `salidas/hogares_2024.parquet`, `salidas/indicadores.csv`, `salidas/validacion.txt` |
| `graficando-enaho` | Barras de pobreza, gasto o ingreso por persona según área, sexo o departamento, con título, unidad y fuente | `figuras/<indicador>_por_<grupo>.png` y `.csv` |
| `mapeando-enaho` | Mapa coroplético por departamento. Une `ubigeo[:2]` con `FIRST_IDDP` con 25 unidades, Lima y Callao separados. Compara con la referencia de la sesión 16 (tolerancia de 0.1) | `mapas/<indicador>_departamento.png` y `.csv` |

`indicadores.csv` trae, por departamento, las siguientes columnas:

- `pobreza_pct`, `gasto_real_pc` e `ingreso_real_pc`, ponderadas con `factor07 × mieperho`. Los montos están en soles
  mensuales por persona, a precios de Lima.
- La composición del ingreso, `ing_*_pct`, ponderada con `factor07`.
- El empleo por rama, `empleo_*_pct` y `rama_principal`, ponderado con `fac500a`.

El detalle de cada variable está en el `SKILL.md` y el `reference.md` de `limpiando-enaho`.

## 5. Fuentes y descarga de datos

| Fuente | Datos | Descarga |
|---|---|---|
| INEI | ENAHO 2024 (código de encuesta 966): módulo 34 `sumaria-2024.dta`, módulo 02 `enaho01-2024-200.dta`, módulo 05 `enaho01a-2024-500.dta` | [Microdatos del INEI](https://proyectos.inei.gob.pe/microdatos/) → ENAHO metodología actualizada → 2024 → anual. Descomprimir en `datos/966-Modulo34/`, `datos/966-Modulo02/` y `datos/966-Modulo05/` |
| BCRP | Series estadísticas y catálogo de metadatos | Automática: el MCP usa la [API del BCRP](https://estadisticas.bcrp.gob.pe/estadisticas/series/ayuda/api) y baja el catálogo a `datos/catalogo_bcrp.csv` la primera vez |
| Curso | Límites departamentales `peru_departamental_simple.geojson` | Automática: la baja `mapeando-enaho` del repositorio del curso si falta en `datos/` |

Los microdatos (`*.dta`, `*.zip`, `datos/`) y los `.parquet` están en `.gitignore` y no se suben.

## 6. Instalación con `uv`

```bash
git clone https://github.com/brisacruz22/Agente-de-investigacion-socioeconomica.git
cd Agente-de-investigacion-socioeconomica
uv sync            # crea .venv con fastmcp, pandas, pyarrow, geopandas, matplotlib, httpx y pytest
```

Requiere Python 3.11 o superior y [Claude Code](https://docs.claude.com/en/docs/claude-code).

## 7. Conectar el MCP a Claude Code

El repositorio ya trae `.mcp.json` en la raíz:

```json
{ "mcpServers": { "bcrp": { "command": "uv", "args": ["run", "mcp/server.py"] } } }
```

Al abrir Claude Code en la raíz del repo, aprueben el servidor `bcrp` cuando lo pida y revisen con `/mcp` que aparezca
conectado. Para registrarlo a mano:

```bash
claude mcp add --scope project bcrp -- uv run mcp/server.py
```

Las skills se cargan solas desde `.claude/skills/`.

## 8. Reproducir el procesamiento y las pruebas

```bash
uv run pytest                                                        # 10 pruebas del MCP (8 de la sesión 04 + 2 propias)
uv run .claude/skills/limpiando-enaho/scripts/limpiar.py             # limpia, valida (14/14) y arma indicadores.csv
uv run .claude/skills/graficando-enaho/scripts/graficar.py --por departamento --indicador pobreza
uv run .claude/skills/mapeando-enaho/scripts/mapear.py --indicador pobreza
```

Para el cruce, primero se piden al MCP los 6 grupos de exportación de 2022, con
`comparar_departamentos(<texto>, "2022", guardar=True)`:

- `exportaciones grupo productos total exportaciones`
- `exportaciones grupo productos tradicionales mineros`
- `exportaciones grupo productos tradicionales agricolas`
- `exportaciones grupo productos no tradicionales agropecuarios`
- `exportaciones grupo productos tradicionales pesqueros`
- `exportaciones grupo productos no tradicionales pesqueros`

Después:

```bash
uv run analisis/cruzar.py              # salidas/cruce_*.csv y figuras/cruce_mineria_pobreza.png
uv run evaluacion/verdades.py          # respuestas esperadas, sin MCP ni skills
uv run evaluacion/evaluar.py           # 10 preguntas en modos A y B → evaluacion/resultados.csv
```

## 9. Resultados de la evaluación

Las mismas 10 preguntas (4 del BCRP, 4 de la ENAHO y 2 combinadas) se corrieron con `claude-opus-5-5`, en sesiones
independientes. El detalle está en [`evaluacion/comparacion.md`](evaluacion/comparacion.md).

| | Modo A, sin MCP ni skills | Modo B, con MCP y skills |
|---|---|---|
| Correctas | 0 / 10 | 10 / 10 |
| Incorrectas | 1 | 0 |
| No contestadas | 9 | 0 |
| Tiempo promedio | 12.0 s | 26.8 s |

Sin herramientas, el modelo casi siempre se abstuvo de dar el valor, pero en el texto dejó estimaciones de memoria que
a veces eran incorrectas. Con herramientas acertó todas y citó la serie, la variable y el factor de expansión de cada
cifra.

**Resultado de la investigación** ([`informes/informe_final.md`](informes/informe_final.md)): la actividad principal
del departamento, medida por sus exportaciones, casi no distingue la pobreza, el gasto ni el ingreso de los hogares.
La correlación de Spearman entre minería y pobreza es −0.14. Lo que sí se asocia es la composición del ingreso: la
correlación entre minería y la parte del ingreso que viene del trabajo es 0.65. La minería pesa en lo exportado y poco
en el empleo: nunca más del 6.1 % de los ocupados.

## 10. Limitaciones y problemas encontrados

**Limitaciones del análisis**

- Las exportaciones por departamento llegan hasta 2022 y la ENAHO es de 2024. La ENAHO es transversal: no hay
  evolución de los hogares.
- Se cruzan agregados departamentales con indicadores de hogares, con n = 25. Es una asociación descriptiva, no
  causalidad.
- No está confirmado que el BCRP asigne cada exportación al departamento donde se produjo. Eso explicaría la minería
  de Callao y de Lima.
- En la evaluación, las preguntas combinadas del modo B leyeron resultados ya calculados. Los criterios de
  interpretación los redactó el mismo modelo evaluado (ver `comparacion.md`).

**Problemas encontrados y cómo se resolvieron**

- **Lima Metropolitana y Lima Provincias:** el BCRP las separa en algunas series, pero en la ENAHO ambas son el
  departamento 15. Se usó una sola Lima en las exportaciones y Callao (07) aparte.
- **Llaves de la ENAHO:** pierden sus ceros a la izquierda si se leen como número. Se leen como texto con ancho fijo y
  se validan.
- **El gasto total:** la suma de los grupos de gasto `gru*` no da `gashog2d`. El total se toma de `gashog2d`.
- **Indicadores casi iguales en el catálogo:** «tradicionales pesqueros» calza también con «no tradicionales
  pesqueros». `comparar_departamentos` elige el único indicador sin palabras de más.
- **La API del BCRP:** agrega un aviso de PHP después del JSON. `verdades.py` lee solo la parte JSON.
- **El JSON de la respuesta:** en la salida `stream-json` de Claude Code aparece como una herramienta,
  `StructuredOutput`. `evaluar.py` la excluye del conteo de herramientas.
- **`scipy` no está instalado:** la correlación de Spearman se calcula como Pearson sobre los rangos.

## 11. Ejemplo de una ejecución completa

En una sesión nueva de Claude Code se escribió solo la pregunta de investigación
([`evidencias_ia/integracion/09_corrida-agente_2026-11-09.md`](evidencias_ia/integracion/09_corrida-agente_2026-11-09.md)).
El agente hizo lo siguiente:

1. Activó la skill `limpiando-enaho`, corrió `limpiar.py` y comprobó las 14 de 14 validaciones.
2. Pidió al MCP los 6 grupos de exportación de 2022 con `comparar_departamentos(..., guardar=True)`. Llegaron los 25
   departamentos sin faltantes.
3. Revisó la unidad y la cobertura de las series con `metadatos("RD41012BA")`.
4. Corrió `analisis/cruzar.py` (unión por `ccdd`, Spearman y promedios ponderados por población).
5. Activó la skill `mapeando-enaho` para el mapa de pobreza, con 5 de 5 validaciones (diferencia máxima con la sesión
   16: 0.05).
6. Respondió con cuatro hallazgos, todos con su serie, variable y factor de expansión, y con las limitaciones.

En total usó 2 herramientas MCP y 2 skills en una misma ejecución. Después se generó un gráfico del BCRP con `grafico`
y se verificaron cifras a mano contra la API del BCRP y el INEI (informe, sección 8).

## 12. Evidencias del uso de IA

Las conversaciones completas, exportadas con `/export` y numeradas en orden cronológico, están en
[`evidencias_ia/`](evidencias_ia/):

| Carpeta | Conversaciones |
|---|---|
| `mcp/` | 02 configuración del MCP · 03 pytest con el BCRP real |
| `skills/` | 04 `limpiando-enaho` · 05 `graficando-enaho` · 06 `mapeando-enaho` · 07 módulo 05 y composición del ingreso |
| `integracion/` | 08 actividad principal y cruce · 09 corrida del agente · 10 informe final · 11 verificación de cifras |
| `evaluacion/` | 12 preguntas de evaluación · 13 corrida de la evaluación y comparación |

La 01 es la conversación de planificación en claude.ai y va en la raíz de `evidencias_ia/`. Antes de publicar se
buscaron en todos los archivos claves de API, tokens, contraseñas y correos electrónicos; no se encontró ninguno.
