---
name: mapeando-enaho
description: Hace un mapa coroplético del Perú por departamento con la ENAHO 2024 del INEI (pobreza monetaria, gasto o ingreso por persona), unido por código ubigeo y validado contra la referencia de la sesión 16. Úsala cuando pidan un mapa, mapear o ver en el territorio la pobreza, el gasto o el ingreso por departamento o región.
---

# Mapear la ENAHO 2024

1. Si no existe `salidas/indicadores.csv`, usa primero la skill `limpiando-enaho`.
2. Corre exactamente: `uv run ${CLAUDE_SKILL_DIR}/scripts/mapear.py --indicador <pobreza|gasto|ingreso>`
   (`pobreza` si el pedido no dice otra cosa).
3. Revisa las líneas `[OK]` / `[FALLA]` que imprime. Si alguna falla, el script no guarda el mapa: detente e
   informa cuál; nunca unas por nombre ni completes departamentos a mano.
4. Responde con la ruta `mapas/<indicador>_departamento.png` y las cifras de `mapas/<indicador>_departamento.csv`
   (para pobreza, ese CSV trae también la referencia de la sesión 16 y la diferencia).
5. Al interpretar: es asociación descriptiva entre 25 departamentos, no causalidad.

## Qué garantiza el script

- Une `ccdd` (= `ubigeo[:2]`) con `FIRST_IDDP` del GeoJSON del curso, como texto y con `validate="1:1"`.
- Exige 25 unidades con dato, Lima (15) y Callao (07) separados, y que los nombres coincidan con `NOMBDEP`.
- Para pobreza, compara con `referencia_sesion16.csv` (la de `sessions/16-skills-enaho/referencias/`) con una
  tolerancia de 0.1 puntos.
- Escala de un solo color (azules, como los gráficos del MCP y de `graficando-enaho`), de claro a oscuro desde 0,
  y la unidad en la leyenda.
- Si falta `datos/peru_departamental_simple.geojson`, lo baja del repositorio del curso.
