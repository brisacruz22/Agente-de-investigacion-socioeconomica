"""Cruza la estructura exportadora de cada departamento (BCRP, 2022) con sus condiciones de vida (ENAHO 2024).

    uv run analisis/cruzar.py

Lee los CSV que guarda la herramienta comparar_departamentos(..., guardar=True) del MCP y salidas/indicadores.csv
de la skill limpiando-enaho. Guarda en salidas/ el cruce, las correlaciones y el resumen por actividad principal,
y en figuras/ un gráfico de dispersión. Es asociación descriptiva entre 25 departamentos, no causalidad.
"""

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


RAIZ = Path(__file__).resolve().parents[1]
SALIDAS, FIGURAS = RAIZ / "salidas", RAIZ / "figuras"
PERIODO = "2022"
AZUL, FONDO, TEXTO, TEXTO_SUAVE = "#2E5E7E", "#fcfcfb", "#0b0b0b", "#52514e"     # los de graficando-enaho

# Actividad → grupos de exportación del BCRP que suma (lo que va después de «|» en el indicador) y el texto con
# que se pide cada grupo a comparar_departamentos
TOTAL = ("total exportaciones", "exportaciones grupo productos total exportaciones")
ACTIVIDADES = {
    "Minería": [("productos tradicionales - mineros", "exportaciones grupo productos tradicionales mineros")],
    "Agro": [("productos tradicionales - agricolas", "exportaciones grupo productos tradicionales agricolas"),
             ("productos no tradicionales - agropecuarios",
              "exportaciones grupo productos no tradicionales agropecuarios")],
    "Pesca": [("productos tradicionales - pesqueros", "exportaciones grupo productos tradicionales pesqueros"),
              ("productos no tradicionales - pesqueros", "exportaciones grupo productos no tradicionales pesqueros")],
}
def spearman(x, y):
    """Correlación de Spearman: la de Pearson sobre los rangos (así no hace falta scipy)."""
    return x.rank().corr(y.rank())


CONDICIONES = {"pobreza_pct": "Pobreza (%)", "gasto_real_pc": "Gasto real por persona",
               "ingreso_real_pc": "Ingreso real por persona", "ing_trabajo_pct": "Ingreso del trabajo (%)",
               "ing_transferencias_pct": "Transferencias (%)"}

# 1. Leer lo que guardó el MCP; si falta un grupo, decir con qué texto pedirlo
archivos = list(SALIDAS.glob(f"bcrp_*_{PERIODO}.csv"))
bcrp = pd.concat([pd.read_csv(a, dtype={"ccdd": str}) for a in archivos]) if archivos else pd.DataFrame()
bcrp["grupo"] = bcrp.indicador.str.split("|").str[-1].str.strip() if archivos else []
necesarios = [TOTAL] + [g for grupos in ACTIVIDADES.values() for g in grupos]
faltan = [texto for grupo, texto in necesarios if grupo not in set(bcrp.get("grupo", []))]
if faltan:
    sys.exit("ERROR: faltan exportaciones del BCRP. Pidan con comparar_departamentos(texto, periodo="
             f"'{PERIODO}', guardar=True) estos textos: " + "; ".join(faltan))
if not (SALIDAS / "indicadores.csv").exists():
    sys.exit("ERROR: no existe salidas/indicadores.csv. Corran primero la skill limpiando-enaho.")

# 2. Participación de cada actividad en las exportaciones del departamento
valores = bcrp.drop_duplicates(["ccdd", "grupo"]).pivot(index="ccdd", columns="grupo", values="valor")
if len(valores) != 25 or valores.isna().any().any():
    sys.exit(f"ERROR: se esperaban 25 departamentos con dato en todos los grupos; hay {len(valores)}.")
cruce = pd.DataFrame({"exportaciones_musd": valores[TOTAL[0]]})
for actividad, grupos in ACTIVIDADES.items():
    cruce[f"exp_{actividad.lower().replace('í', 'i')}_pct"] = 100 * valores[[g for g, _ in grupos]].sum(axis=1) \
                                                             / valores[TOTAL[0]]
cruce["exp_otros_pct"] = 100 - cruce.filter(like="exp_").drop(columns="exportaciones_musd", errors="ignore").sum(axis=1)
participaciones = ["exp_mineria_pct", "exp_agro_pct", "exp_pesca_pct", "exp_otros_pct"]
nombres = dict(zip(participaciones, ["Minería", "Agro", "Pesca", "Otros"]))
cruce["actividad_principal"] = cruce[participaciones].idxmax(axis=1).map(nombres)

# 3. Unir con la ENAHO por código
enaho = pd.read_csv(SALIDAS / "indicadores.csv", dtype={"ccdd": str})
cruce = enaho.merge(cruce.reset_index(), on="ccdd", how="inner", validate="1:1")
if len(cruce) != 25:
    sys.exit(f"ERROR: la unión BCRP-ENAHO dejó {len(cruce)} departamentos, no 25.")

# 4. Correlaciones de Spearman (por rangos: con 25 casos, menos sensible a extremos como Lima o Moquegua)
filas = [{"exportacion": nombres[p], "condicion": CONDICIONES[c], "spearman": spearman(cruce[p], cruce[c])}
         for p in participaciones[:3] for c in CONDICIONES]
filas.append({"exportacion": "Minería", "condicion": "Empleo en minería (%)",
              "spearman": spearman(cruce.exp_mineria_pct, cruce.empleo_mineria_pct)})
correlaciones = pd.DataFrame(filas)

# 5. Resumen por actividad principal, ponderado por población
resumen = cruce.groupby("actividad_principal").apply(lambda d: pd.Series({
    "departamentos": len(d),
    "lista": ", ".join(d.sort_values("pobreza_pct").departamento),
    "poblacion": d.poblacion.sum(),
    "pobreza_pct": (d.pobreza_pct * d.poblacion).sum() / d.poblacion.sum(),
    "gasto_real_pc": (d.gasto_real_pc * d.poblacion).sum() / d.poblacion.sum(),
    "ingreso_real_pc": (d.ingreso_real_pc * d.poblacion).sum() / d.poblacion.sum(),
}), include_groups=False).reset_index()

# 6. Dispersión: minería en exportaciones frente a pobreza.
# Base: python-graph-gallery.com/46-add-text-annotation-on-scatterplot (licencia 0BSD)
fig, ax = plt.subplots(figsize=(9, 6.5), facecolor=FONDO)
ax.set_facecolor(FONDO)
ax.scatter(cruce.exp_mineria_pct, cruce.pobreza_pct, color=AZUL, s=40, zorder=2)
puestas = []                                         # etiquetas ya escritas, para no encimar dos puntos vecinos
for _, d in cruce.sort_values("pobreza_pct", ascending=False).iterrows():
    y = d.pobreza_pct
    while any(abs(d.exp_mineria_pct - x0) < 8 and abs(y - y0) < 1.2 for x0, y0 in puestas):
        y -= 1.2
    puestas.append((d.exp_mineria_pct, y))
    movida = y != d.pobreza_pct                      # si se movió, una línea fina la une con su punto
    ax.annotate(d.departamento, xy=(d.exp_mineria_pct, d.pobreza_pct),
                xytext=(d.exp_mineria_pct + (4 if movida else 1), y), fontsize=8, color=TEXTO_SUAVE, va="center",
                arrowprops={"arrowstyle": "-", "color": "#c3c2b7", "linewidth": 0.6} if movida else None)
rho = spearman(cruce.exp_mineria_pct, cruce.pobreza_pct)
ax.set_xlabel("Minería en las exportaciones del departamento, 2022 (% del valor FOB)", color=TEXTO_SUAVE)
ax.set_ylabel("Pobreza monetaria, 2024 (% de personas)", color=TEXTO_SUAVE)
ax.set_xlim(0, 105)
ax.set_ylim(0, cruce.pobreza_pct.max() * 1.1)
ax.grid(color="#e6e5e1", linewidth=0.8)
ax.set_axisbelow(True)
ax.tick_params(colors=TEXTO_SUAVE, length=0)
for lado in ("top", "right"):
    ax.spines[lado].set_visible(False)
fig.suptitle(f"Minería exportadora y pobreza en los 25 departamentos (Spearman = {rho:.2f})",
             x=0.01, ha="left", fontsize=12, fontweight="bold", color=TEXTO)
fig.text(0.01, 0.005, "Fuente: BCRP, exportaciones por grupo de productos 2022 (vía MCP); INEI, ENAHO 2024, "
         "ponderado con factor07 × mieperho.\nAsociación descriptiva, no causalidad.", fontsize=8, color=TEXTO_SUAVE)
fig.tight_layout(rect=(0, 0.05, 1, 0.97))

# 7. Guardar
FIGURAS.mkdir(exist_ok=True)
cruce.round(2).to_csv(SALIDAS / "cruce_departamentos.csv", index=False)
correlaciones.round(3).to_csv(SALIDAS / "cruce_correlaciones.csv", index=False)
resumen.round(2).to_csv(SALIDAS / "cruce_resumen.csv", index=False)
fig.savefig(FIGURAS / "cruce_mineria_pobreza.png", dpi=200, facecolor=FONDO, bbox_inches="tight", pad_inches=0.2)
print(resumen.round(2).to_string(index=False))
print()
print(correlaciones.round(2).to_string(index=False))
print("\nGuardados: salidas/cruce_departamentos.csv, salidas/cruce_correlaciones.csv, salidas/cruce_resumen.csv, "
      "figuras/cruce_mineria_pobreza.png")
