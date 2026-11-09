---
name: limpiando-enaho
description: Limpia los módulos 34 (sumaria), 02 (miembros) y 05 (empleo) de la ENAHO 2024 del INEI, valida la pobreza oficial y arma una base de personas y una tabla por departamento con pobreza, ingreso y gasto por persona, composición del ingreso y empleo por rama de actividad. Úsala cuando pidan limpiar, unir o analizar la ENAHO, o calcular pobreza, ingreso, gasto, fuentes del ingreso o empleo por rama según departamento, área, sexo o edad. Úsala antes de responder cualquier cifra de la ENAHO, aunque ya existan las salidas, porque revisa la validación.
---

# Limpiar la ENAHO 2024

1. Si falta alguno de `datos/966-Modulo34/sumaria-2024.dta`, `datos/966-Modulo02/enaho01-2024-200.dta` o
   `datos/966-Modulo05/enaho01a-2024-500.dta`, pide al usuario bajarlo del INEI (código 966 = 2024) y detente.
2. Corre exactamente: `uv run ${CLAUDE_SKILL_DIR}/scripts/limpiar.py`
3. Lee `salidas/validacion.txt`. Si alguna línea dice `[FALLA]`, detente e informa cuál; nunca ajustes cifras para
   que coincidan con las del INEI.
4. Responde con las salidas:
   - `salidas/personas_2024.parquet`: una fila por residente habitual. Toda cifra de personas va ponderada con
     `facpob07`.
   - `salidas/hogares_2024.parquet`: la sumaria con las variables construidas y `peso` = `factor07 × mieperho`.
   - `salidas/indicadores.csv`: una fila por departamento (`ccdd`, `departamento`). Columnas en la tabla de abajo.
5. Antes de usar una variable que no está en la base, lee `reference.md`.
6. Cita la variable y el factor de expansión de cada cifra. Asociación no es causalidad.

## Columnas de `indicadores.csv`

| Columnas | Qué es | Factor |
|---|---|---|
| `pobreza_pct` | % de personas pobres (`pobreza` <= 2) | `factor07 × mieperho` |
| `gasto_real_pc`, `ingreso_real_pc` | Gasto total (`gashog2d`) e ingreso neto total (`inghog2d`) por persona, soles mensuales a precios de Lima (/ `mieperho` / 12 / `ld`) | `factor07 × mieperho` |
| `ing_*_pct` | De cada sol del ingreso neto total del departamento, cuánto viene de cada fuente; suman 100 | `factor07` |
| `empleo_*_pct` | % de ocupados en cada rama; suman 100 | `fac500a` |
| `rama_principal` | La rama con más ocupados | `fac500a` |

**Fuentes del ingreso** (variables de la sumaria):

| Columna | Fuente | Variables |
|---|---|---|
| `ing_trabajo_pct` | Trabajo, principal y secundario, dependiente e independiente | `ingnethd`, `pagesphd`, `ingindhd`, `ingauthd`, `insedlhd`, `paesechd`, `ingseihd`, `isecauhd`, `ingexthd` |
| `ing_alquiler_imputado_pct` | Alquiler imputado de la vivienda propia | `ia01hd` |
| `ing_transferencias_pct` | Transferencias del país (públicas y privadas) y del extranjero | `ingtrahd`, `ingtexhd` |
| `ing_extraordinarios_pct` | Otros ingresos extraordinarios | `ingoexhd` |
| `ing_rentas_pct` | Rentas de la propiedad | `ingrenhd` |
| `ing_otros_pct` | Otros ingresos: diferencia con el ingreso neto total del hogar (`inghog2d`) | — |

«Otros» nunca es negativo (lo valida el script) y a nivel nacional es cerca del 7 %: probablemente ingresos no
monetarios (donaciones, especie), pero sin la metodología del INEI no se afirma.

**Empleo por rama** (módulo 05): ocupados (`ocu500 == 1`) que son residentes habituales, 57,684 personas. La rama
sale de la división (dos primeros dígitos) del código CIIU rev. 4 `p506r4`, revisada con
`enaho_tabla_ciiu_rev4.dta`: Agropecuaria 01–02, Pesca 03, Minería 05–09, Manufactura 10–33, Construcción 41–43,
Comercio 45–47 y Servicios el resto. No se filtra a adultos: el módulo ya empieza en 14 años, y los ocupados de
14 a 17 (2.9 % del total) trabajan en agropecuaria el doble que los de 18 a más (43.2 % frente a 21.9 %); sacarlos
reduciría el peso del agro.
