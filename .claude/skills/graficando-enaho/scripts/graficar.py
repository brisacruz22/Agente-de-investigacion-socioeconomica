"""Gráfico de barras de la ENAHO 2024: pobreza, gasto o ingreso por área, sexo o departamento.

    uv run .claude/skills/graficando-enaho/scripts/graficar.py --por departamento --indicador gasto

Lee las bases de limpiando-enaho y guarda en figuras/ un PNG a 200 dpi y un CSV con las cifras del gráfico.
Área y departamento se ponderan por hogar (factor07 × mieperho), que reproduce las cifras del INEI;
sexo, por persona (facpob07), porque es una característica de cada persona.
"""

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


RAIZ = Path(__file__).resolve().parents[4]          # scripts/ → graficando-enaho/ → skills/ → .claude/ → raíz
SALIDAS = RAIZ / "salidas"
FIGURAS = RAIZ / "figuras"
AZUL, FONDO, TEXTO, TEXTO_SUAVE = "#2E5E7E", "#fcfcfb", "#0b0b0b", "#52514e"     # el azul de grafico en el MCP

# Códigos de FIRST_IDDP en el GeoJSON del curso; los nombres llevan tildes para el gráfico
DEPARTAMENTOS = {
    "01": "Amazonas", "02": "Áncash", "03": "Apurímac", "04": "Arequipa", "05": "Ayacucho", "06": "Cajamarca",
    "07": "Callao", "08": "Cusco", "09": "Huancavelica", "10": "Huánuco", "11": "Ica", "12": "Junín",
    "13": "La Libertad", "14": "Lambayeque", "15": "Lima", "16": "Loreto", "17": "Madre de Dios", "18": "Moquegua",
    "19": "Pasco", "20": "Piura", "21": "Puno", "22": "San Martín", "23": "Tacna", "24": "Tumbes", "25": "Ucayali",
}
# indicador: (columna, nombre, unidad)
INDICADORES = {
    "pobreza": ("pobre", "Pobreza monetaria", "% de personas"),
    "gasto": ("gasto_real_pc", "Gasto real por persona", "soles mensuales a precios de Lima"),
    "ingreso": ("ingreso_real_pc", "Ingreso real por persona", "soles mensuales a precios de Lima"),
}
# grupo: (base, columna, peso, texto del peso)
GRUPOS = {
    "area": ("hogares", "area", "peso", "factor07 × mieperho"),
    "sexo": ("personas", "sexo", "facpob07", "facpob07"),
    "departamento": ("hogares", "departamento", "peso", "factor07 × mieperho"),
}


def cargar(nombre):
    ruta = SALIDAS / f"{nombre}_2024.parquet"
    if not ruta.exists():
        sys.exit(f"ERROR: no existe {ruta.relative_to(RAIZ)}. Corran primero la skill limpiando-enaho.")
    df = pd.read_parquet(ruta)
    df["area"] = df.urbano.map({True: "Urbana", False: "Rural"})
    df["departamento"] = df.ccdd.map(DEPARTAMENTOS)
    if "p207" in df:
        df["sexo"] = df.p207.map({1: "Hombres", 2: "Mujeres"})
    return df


def ponderar(valor, peso, indicador):
    """Pobreza: % ponderado de pobres. Gasto e ingreso: promedio ponderado."""
    total = (valor * peso).sum() / peso.sum()
    return 100 * total if indicador == "pobreza" else total


def formato(v, indicador):
    return f"{v:.1f} %" if indicador == "pobreza" else f"S/ {v:,.0f}"


parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
parser.add_argument("--por", choices=GRUPOS, required=True)
parser.add_argument("--indicador", choices=INDICADORES, default="pobreza")
args = parser.parse_args()

columna, nombre, unidad = INDICADORES[args.indicador]
base, grupo, peso, texto_peso = GRUPOS[args.por]
df = cargar(base)

cifras = (df.groupby(grupo)
          .apply(lambda d: pd.Series({"valor": ponderar(d[columna], d[peso], args.indicador),
                                      "poblacion": d[peso].sum()}), include_groups=False)
          .sort_values("valor")
          .astype(float)                                   # los factores vienen en float32
          .reset_index())
nacional = ponderar(df[columna], df[peso], args.indicador)
mayor, menor = cifras.iloc[-1], cifras.iloc[0]

# Título analítico: dice el rango que muestra el gráfico; las cifras salen de los datos
titulo = (f"{nombre} por {args.por.replace('area', 'área')}, 2024: de {formato(menor.valor, args.indicador)} ({menor[grupo]}) "
          f"a {formato(mayor.valor, args.indicador)} ({mayor[grupo]})")

# Base: python-graph-gallery.com/2-horizontal-barplot (licencia 0BSD), la misma de grafico en el MCP.
# Encima, las reglas de la sesión 16: cifra en cada barra, línea nacional, fuente y factor.
alto = 0.32 * len(cifras) + 1.6
fig, ax = plt.subplots(figsize=(9, alto), facecolor=FONDO)
ax.set_facecolor(FONDO)
barras = ax.barh(cifras[grupo], cifras.valor, color=AZUL, height=0.7, zorder=2)
etiquetas = ax.bar_label(barras, labels=[formato(v, args.indicador) for v in cifras.valor], padding=4,
                         color=TEXTO, fontsize=9)
for etiqueta in etiquetas:                                 # la línea nacional pasa por detrás de las cifras
    etiqueta.set_bbox({"facecolor": FONDO, "edgecolor": "none", "pad": 1})
ax.axvline(nacional, color=TEXTO_SUAVE, linestyle="--", linewidth=1, zorder=1)
ax.text(nacional, len(cifras) - 0.4, f" Nacional: {formato(nacional, args.indicador)}", color=TEXTO_SUAVE,
        fontsize=9, va="bottom")
ax.set_xlim(0, cifras.valor.max() * 1.15)                 # las barras empiezan en cero
ax.set_xlabel(unidad[0].upper() + unidad[1:], color=TEXTO_SUAVE)     # capitalize() pondría «lima»
ax.tick_params(colors=TEXTO_SUAVE, length=0)
ax.grid(axis="x", color="#e6e5e1", linewidth=0.8)
ax.set_axisbelow(True)
for lado in ("top", "right", "left"):
    ax.spines[lado].set_visible(False)
ax.spines["bottom"].set_color("#c3c2b7")
fig.suptitle(titulo, x=0.01, ha="left", fontsize=12, fontweight="bold", color=TEXTO)
fig.text(0.01, 0.005, f"Fuente: INEI, ENAHO 2024 (módulos 34 y 02). Estimación ponderada con {texto_peso}.",
         fontsize=8, color=TEXTO_SUAVE)
fig.tight_layout(rect=(0, 0.03, 1, 0.97))

FIGURAS.mkdir(exist_ok=True)
archivo = FIGURAS / f"{args.indicador}_por_{args.por}"
fig.savefig(archivo.with_suffix(".png"), dpi=200, facecolor=FONDO, bbox_inches="tight", pad_inches=0.2)
cifras.round(2).to_csv(archivo.with_suffix(".csv"), index=False)
print(titulo)
print(cifras.round(2).to_string(index=False))
print(f"Nacional: {nacional:.2f}")
print(f"Guardados: {archivo.relative_to(RAIZ)}.png y .csv")
