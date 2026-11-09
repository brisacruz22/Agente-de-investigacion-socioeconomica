"""Respuestas esperadas de evaluacion/preguntas.csv, calculadas sin el MCP ni las skills.

    uv run evaluacion/verdades.py

BCRP: se lee directo la API oficial (estadisticas.bcrp.gob.pe), no el servidor MCP. De salidas/ solo se toman los
códigos de serie de cada departamento, no sus valores.
ENAHO: se leen directo las .dta de datos/ (módulos 34, 02 y 05), no las salidas de limpiar.py.
Las verdades se fijaron con este script antes de correr evaluar.py y no se cambian después.
"""
import json
import urllib.request
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
DATOS, SALIDAS = RAIZ / "datos", RAIZ / "salidas"


def api(codigo, periodo):
    """Valor de una serie del BCRP en un periodo, leído directo de su API."""
    url = f"https://estadisticas.bcrp.gob.pe/estadisticas/series/api/{codigo}/json/{periodo}/{periodo}"
    req = urllib.request.Request(url, headers={"User-Agent": "evaluacion-tarea4"})
    texto = urllib.request.urlopen(req, timeout=60).read().decode("utf-8-sig")
    datos = json.JSONDecoder().raw_decode(texto)[0]   # la API agrega un aviso de PHP después del JSON
    return float(datos["periods"][0]["values"][0])


# 1. BCRP (preguntas 1 a 4)
print("bcrp_exp_lima       ", api("RD41212BA", 2022))
print("bcrp_min_arequipa   ", api("RD41012BA", 2022))
print("bcrp_pesca_ancash   ", api("RD40976BA", 2022))
print("bcrp_cobre_arequipa ", api("RD15519DA", 2024))

# Participación minera de cada departamento: códigos (total y mineros) por ccdd, valores de la API
codigos = pd.concat([pd.read_csv(SALIDAS / f"bcrp_exportaciones_grupo_productos_{g}_2022.csv", dtype={"ccdd": str})
                     .assign(g=g) for g in ["total_exportaciones", "tradicionales_mineros"]])
cod = codigos.pivot(index="ccdd", columns="g", values="codigo")
mineria = {c: 100 * api(r.tradicionales_mineros, 2022) / api(r.total_exportaciones, 2022) for c, r in cod.iterrows()}

# 2. ENAHO desde la sumaria original (preguntas 5 a 7)
s = pd.read_stata(DATOS / "966-Modulo34/sumaria-2024.dta", convert_categoricals=False)
s["ccdd"] = s.ubigeo.astype(str).str.zfill(6).str[:2]
s["peso"] = s.factor07 * s.mieperho
pobreza = {c: 100 * (d.peso * (d.pobreza <= 2)).sum() / d.peso.sum() for c, d in s.groupby("ccdd")}
print("enaho_pobreza_puno  ", round(pobreza["21"], 2))
m = s[s.ccdd == "18"]
gasto = m.gashog2d / m.mieperho / 12 / m.ld
print("enaho_gasto_moquegua", round((gasto * m.peso).sum() / m.peso.sum(), 2))
trabajo = ["ingnethd", "pagesphd", "ingindhd", "ingauthd", "insedlhd", "paesechd", "ingseihd", "isecauhd", "ingexthd"]
print("enaho_ing_trabajo   ",
      round(100 * (s[trabajo].fillna(0).sum(axis=1) * s.factor07).sum() / (s.inghog2d * s.factor07).sum(), 2))

# 3. Empleo (pregunta 8): ocupados que son residentes habituales; agropecuaria = divisiones CIIU 01 y 02
llaves = ["conglome", "vivienda", "hogar", "codperso"]
miembros = pd.read_stata(DATOS / "966-Modulo02/enaho01-2024-200.dta", convert_categoricals=False,
                         columns=llaves + ["p204", "p205", "p206"])
residentes = miembros[((miembros.p204 == 1) & (miembros.p205 == 2)) |
                      ((miembros.p204 == 2) & (miembros.p206 == 1))][llaves]
empleo = pd.read_stata(DATOS / "966-Modulo05/enaho01a-2024-500.dta", convert_categoricals=False,
                       columns=llaves + ["ocu500", "p506r4", "fac500a"])
for df in (residentes, empleo):
    for k in llaves:
        df[k] = df[k].astype(str).str.strip()
ocupados = empleo[empleo.ocu500 == 1].merge(residentes, on=llaves, validate="1:1")
division = ocupados.p506r4.astype(int) // 100
print("enaho_empleo_agro   ", round(100 * ocupados.fac500a[division.isin([1, 2])].sum() / ocupados.fac500a.sum(), 2),
      f"({len(ocupados):,} ocupados)")

# 4. Combinadas (preguntas 9 y 10)
mayor = max(mineria, key=mineria.get)
print("ambas_mineria_pobreza", f"ccdd {mayor}: minería {mineria[mayor]:.2f} %, pobreza {pobreza[mayor]:.2f} %")
x = pd.Series(mineria)
y = pd.Series(pobreza).loc[x.index]
rx, ry = x.rank(), y.rank()   # Spearman = Pearson sobre los rangos, escrito a mano
cov = ((rx - rx.mean()) * (ry - ry.mean())).sum()
print("ambas_spearman      ", round(cov / (((rx - rx.mean()) ** 2).sum() * ((ry - ry.mean()) ** 2).sum()) ** 0.5, 3))
