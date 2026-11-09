"""Mapa coroplético de la ENAHO 2024 por departamento: pobreza, gasto o ingreso por persona.

    uv run .claude/skills/mapeando-enaho/scripts/mapear.py --indicador pobreza

Lee salidas/indicadores.csv (de limpiando-enaho) y el GeoJSON departamental del curso, los une por código
(ccdd = FIRST_IDDP, nunca por nombre) y guarda en mapas/ un PNG a 200 dpi y un CSV con las cifras del mapa.
Para la pobreza, además compara con la referencia de la sesión 16. Si una validación falla, se detiene.
"""

import argparse
import sys
import unicodedata
from pathlib import Path

import geopandas as gpd
import httpx
import matplotlib.pyplot as plt
import pandas as pd


RAIZ = Path(__file__).resolve().parents[4]          # scripts/ → mapeando-enaho/ → skills/ → .claude/ → raíz
INDICADORES_CSV = RAIZ / "salidas" / "indicadores.csv"
GEOJSON = RAIZ / "datos" / "peru_departamental_simple.geojson"
URL_GEOJSON = ("https://raw.githubusercontent.com/d2cml-ai/Data-Science-Python/main/sessions/06-geoespacial/"
               "lab/Data/peru_departamental_simple.geojson")
REFERENCIA = Path(__file__).resolve().parents[1] / "referencia_sesion16.csv"
MAPAS = RAIZ / "mapas"
FONDO, TEXTO, TEXTO_SUAVE = "#fcfcfb", "#0b0b0b", "#52514e"
TOLERANCIA = 0.1                                    # puntos porcentuales frente a la sesión 16

# indicador: (columna de indicadores.csv, nombre, unidad)
INDICADORES = {
    "pobreza": ("pobreza_pct", "Pobreza monetaria", "% de personas"),
    "gasto": ("gasto_real_pc", "Gasto real por persona", "soles mensuales a precios de Lima"),
    "ingreso": ("ingreso_real_pc", "Ingreso real por persona", "soles mensuales a precios de Lima"),
}


def sin_tildes(texto):
    return unicodedata.normalize("NFD", texto).encode("ascii", "ignore").decode().upper()


def formato(v, indicador):
    return f"{v:.1f} %" if indicador == "pobreza" else f"S/ {v:,.0f}"


parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
parser.add_argument("--indicador", choices=INDICADORES, default="pobreza")
args = parser.parse_args()
columna, nombre, unidad = INDICADORES[args.indicador]

# 1. Leer: indicadores de la ENAHO y geometrías (el GeoJSON se baja una vez a datos/)
if not INDICADORES_CSV.exists():
    sys.exit("ERROR: no existe salidas/indicadores.csv. Corran primero la skill limpiando-enaho.")
indicadores = pd.read_csv(INDICADORES_CSV, dtype={"ccdd": str})
if not GEOJSON.exists():
    GEOJSON.parent.mkdir(exist_ok=True)
    GEOJSON.write_bytes(httpx.get(URL_GEOJSON, timeout=60).raise_for_status().content)
geometrias = gpd.read_file(GEOJSON)
geometrias["FIRST_IDDP"] = geometrias.FIRST_IDDP.astype(str)

# 2. Unir por código, nunca por nombre
mapa = geometrias.merge(indicadores, left_on="FIRST_IDDP", right_on="ccdd", how="left", validate="1:1")

# 3. Validar: (qué se revisa, valor obtenido, criterio, ¿pasa?)
codigos = sorted(mapa.FIRST_IDDP)
sin_dato = mapa.loc[mapa[columna].isna(), "NOMBDEP"].tolist()
nombres_distintos = mapa.loc[mapa.departamento.fillna("").map(sin_tildes) != mapa.NOMBDEP, "FIRST_IDDP"].tolist()
validaciones = [
    ("Unidades territoriales", f"{len(mapa)}", "25", len(mapa) == 25),
    ("Departamentos sin dato", ", ".join(sin_dato) or "ninguno", "ninguno", not sin_dato),
    ("Lima (15) y Callao (07) separados", "sí" if {"07", "15"} <= set(codigos) else "no", "sí",
     {"07", "15"} <= set(codigos)),
    ("Nombres de la ENAHO = NOMBDEP del GeoJSON (sin tildes)", ", ".join(nombres_distintos) or "coinciden",
     "coinciden", not nombres_distintos),
]
if args.indicador == "pobreza":
    referencia = pd.read_csv(REFERENCIA, dtype={"ccdd": str})
    comparacion = mapa[["ccdd", "departamento", columna]].merge(referencia[["ccdd", "pobreza_pct"]], on="ccdd",
                                                                suffixes=("", "_sesion16"), validate="1:1")
    comparacion["diferencia"] = (comparacion[columna] - comparacion.pobreza_pct_sesion16).round(2)
    peor = comparacion.loc[comparacion.diferencia.abs().idxmax()]
    validaciones.append(("Pobreza frente a la sesión 16",
                         f"diferencia máxima {abs(peor.diferencia):.2f} ({peor.departamento})",
                         f"<= {TOLERANCIA}", (comparacion.diferencia.abs() <= TOLERANCIA).all()))

for nombre_v, valor, criterio, ok in validaciones:
    print(f"[{'OK' if ok else 'FALLA'}] {nombre_v}: {valor} (esperado: {criterio})")
if not all(v[3] for v in validaciones):
    sys.exit("ERROR: el mapa no pasó las validaciones; no se guardó.")

# 4. Dibujar. Base: python-graph-gallery.com/web-map-europe-with-color-by-country (licencia 0BSD);
# encima, las reglas de la sesión 16: un color de claro a oscuro desde 0 y la unidad en la leyenda.
mayor, menor = mapa.loc[mapa[columna].idxmax()], mapa.loc[mapa[columna].idxmin()]
titulo = (f"{nombre} por departamento, 2024:\nde {formato(menor[columna], args.indicador)} ({menor.departamento}) "
          f"a {formato(mayor[columna], args.indicador)} ({mayor.departamento})")

fig, ax = plt.subplots(figsize=(7, 9), facecolor=FONDO)
mapa.plot(column=columna, cmap="Blues", vmin=0, vmax=mapa[columna].max(), edgecolor="white", linewidth=0.6,
          ax=ax, legend=True, legend_kwds={"label": f"{nombre} ({unidad})", "shrink": 0.5})
ax.axis("off")
ax.set_title(titulo, loc="left", fontsize=12, fontweight="bold", color=TEXTO)
fig.text(0.02, 0.02, "Fuente: INEI, ENAHO 2024 (sumaria). Estimación ponderada con factor07 × mieperho.\n"
         "Límites: GeoJSON departamental del curso, unido por código (ubigeo[:2] = FIRST_IDDP).",
         fontsize=7, color=TEXTO_SUAVE)

# 5. Guardar
MAPAS.mkdir(exist_ok=True)
archivo = MAPAS / f"{args.indicador}_departamento"
fig.savefig(archivo.with_suffix(".png"), dpi=200, facecolor=FONDO, bbox_inches="tight", pad_inches=0.2)
(comparacion if args.indicador == "pobreza" else mapa[["ccdd", "departamento", columna]]) \
    .sort_values("ccdd").to_csv(archivo.with_suffix(".csv"), index=False)
print(titulo.replace("\n", " "))
print(f"Guardados: {archivo.relative_to(RAIZ)}.png y .csv")
