---
name: graficando-enaho
description: Hace gráficos de barras de la ENAHO 2024 del INEI con estimaciones ponderadas, título, unidad y fuente. Úsala cuando pidan graficar, comparar o visualizar la pobreza monetaria, el gasto o el ingreso por persona según área urbana y rural, sexo o departamento.
---

# Graficar la ENAHO 2024

1. Si no existe `salidas/personas_2024.parquet` o `salidas/hogares_2024.parquet`, usa primero la skill
   `limpiando-enaho`.
2. Elige `--por` y `--indicador` según el pedido y corre exactamente:
   `uv run ${CLAUDE_SKILL_DIR}/scripts/graficar.py --por <area|sexo|departamento> --indicador <pobreza|gasto|ingreso>`
   (`--indicador` es `pobreza` si el pedido no dice otra cosa).
3. El script guarda `figuras/<indicador>_por_<grupo>.png` (200 dpi) y un `.csv` con las cifras del gráfico.
   Responde con esas cifras, no con otras; muestra la ruta del PNG.
4. Si el pedido no cabe en estas opciones (otro grupo, otro indicador), dilo; no improvises un gráfico sin
   las reglas del script.
5. Al interpretar: diferencias pequeñas (como entre sexos) pueden no ser significativas, porque la ENAHO es una
   muestra y el script no calcula intervalos de confianza. Asociación no es causalidad.

## Qué factor usa cada gráfico

| Grupo | Base | Factor | Por qué |
|---|---|---|---|
| Área, departamento | `hogares_2024.parquet` | `factor07 × mieperho` | Reproduce las cifras del INEI |
| Sexo | `personas_2024.parquet` | `facpob07` | El sexo es de cada persona, no del hogar |

Comprobado con los datos (9 nov 2026), contra las referencias del issue 201 y de la sesión 16:

| Referencia | `factor07 × mieperho` | `facpob07` |
|---|---|---|
| Nacional 27.6 % | 27.58 | 27.53 |
| Urbana 24.8 % | 24.81 | 24.74 |
| Rural 39.3 % | 39.30 | 39.44 (fuera de la tolerancia de 0.1) |
| 25 departamentos (CSV de la sesión 16) | diferencia media 0.03, máxima 0.05 | media 0.17, máxima 0.52 (Puno) |

La diferencia viene de que en 1,846 de los 33,691 hogares el número de residentes habituales no es igual a
`mieperho`. Por eso la línea «Nacional» del gráfico por sexo dice 27.5 % y no 27.6 %. El CSV de departamentos
de la sesión 16 se calculó con `factor07 × mieperho`, así que esa comparación favorece a ese método; la evidencia
independiente son las tres cifras del issue.

## Reglas que ya cumple el script

Barras horizontales ordenadas que empiezan en cero, un solo color, la cifra escrita en cada barra, línea con el
valor nacional, título con el rango y el año, unidad en el eje, nota con la fuente y el factor. Los departamentos
se muestran con su nombre; los códigos coinciden con `FIRST_IDDP` del GeoJSON del curso.
