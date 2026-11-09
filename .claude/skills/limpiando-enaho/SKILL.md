---
name: limpiando-enaho
description: Limpia los módulos 34 (sumaria) y 02 (miembros) de la ENAHO 2024 del INEI, valida la pobreza oficial y arma una base de personas y una tabla por departamento con pobreza, ingreso y gasto por persona. Úsala cuando pidan limpiar, unir o analizar la ENAHO, o calcular pobreza, ingreso o gasto por departamento, área, sexo o edad. Úsala antes de responder cualquier cifra de la ENAHO, aunque ya existan las salidas, porque revisa la validación.
---

# Limpiar la ENAHO 2024

1. Si faltan `datos/966-Modulo34/sumaria-2024.dta` o `datos/966-Modulo02/enaho01-2024-200.dta`, pide al usuario
   bajarlos del INEI (código 966 = 2024) y detente.
2. Corre exactamente: `uv run ${CLAUDE_SKILL_DIR}/scripts/limpiar.py`
3. Lee `salidas/validacion.txt`. Si alguna línea dice `[FALLA]`, detente e informa cuál; nunca ajustes cifras para
   que coincidan con las del INEI.
4. Responde con las salidas:
   - `salidas/personas_2024.parquet`: una fila por residente habitual. Toda cifra de personas va ponderada con
     `facpob07`.
   - `salidas/indicadores.csv`: una fila por departamento (`ccdd`), con pobreza (%) y gasto e ingreso real por
     persona (soles mensuales a precios de Lima), ponderados con `factor07 × mieperho`.
5. Antes de usar una variable que no está en la base, lee `reference.md`.
6. Cita la variable y el factor de expansión de cada cifra. Asociación no es causalidad.
