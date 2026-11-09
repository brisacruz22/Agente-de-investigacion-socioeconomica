"""Limpia los módulos 34 (sumaria) y 02 (miembros) de la ENAHO 2024 y valida contra las cifras oficiales del INEI.

    uv run .claude/skills/limpiando-enaho/scripts/limpiar.py      # desde la raíz del repo

Sale salidas/validacion.txt siempre. Si todas las validaciones pasan, también salidas/personas_2024.parquet
(una fila por residente habitual) y salidas/indicadores.csv (una fila por departamento). Si alguna falla,
se detiene con un error y no guarda la base.
"""

import sys
from pathlib import Path

import pandas as pd


RAIZ = Path(__file__).resolve().parents[4]          # scripts/ → limpiando-enaho/ → skills/ → .claude/ → raíz
SUMARIA = RAIZ / "datos" / "966-Modulo34" / "sumaria-2024.dta"
MIEMBROS = RAIZ / "datos" / "966-Modulo02" / "enaho01-2024-200.dta"
SALIDAS = RAIZ / "salidas"
LLAVES = ["conglome", "vivienda", "hogar"]
ANCHO = {"conglome": 6, "vivienda": 3, "hogar": 2, "codperso": 2, "ubigeo": 6}    # con sus ceros a la izquierda

# Referencias del issue 201 (ENAHO 2024)
POBREZA_NACIONAL, POBREZA_URBANA, POBREZA_RURAL = 27.6, 24.8, 39.3
TOLERANCIA = 0.1                                    # puntos porcentuales
RESIDENTES = 108_664
DEPARTAMENTOS = [f"{i:02d}" for i in range(1, 26)]


def leer(ruta, columnas):
    """Lee un .dta con los códigos (no las etiquetas) y los nombres en minúscula; «aÑo» pasa a anio."""
    df = pd.read_stata(ruta, convert_categoricals=False)
    df.columns = df.columns.str.lower().str.replace(r"^a.o$", "anio", regex=True)
    df = df[columnas]
    for col in set(ANCHO) & set(columnas):
        df[col] = df[col].astype(str)
    return df


def pct(condicion, peso):
    """Porcentaje ponderado: suma de pesos donde se cumple la condición / suma de pesos."""
    return 100 * peso[condicion].sum() / peso.sum()


def promedio(valor, peso):
    return (valor * peso).sum() / peso.sum()


# 1. Leer
sumaria = leer(SUMARIA, LLAVES + ["ubigeo", "dominio", "estrato", "mieperho", "pobreza", "factor07",
                                  "inghog2d", "gashog2d", "linea", "ld"])
miembros = leer(MIEMBROS, LLAVES + ["codperso", "p204", "p205", "p206", "p207", "p208a", "facpob07"])

# 2. Filtrar residentes habituales (condición del INEI usada en la sesión 16)
residente = (((miembros.p204 == 1) & (miembros.p205 == 2)) |
             ((miembros.p204 == 2) & (miembros.p206 == 1)))
personas = miembros[residente].drop(columns=["p204", "p205", "p206"])

# 3. Unir: cada persona con su hogar. ubigeo, dominio y estrato vienen solo de la sumaria
base = personas.merge(sumaria, on=LLAVES, how="left", validate="m:1", indicator=True)

# 4. Construir
for df in (sumaria, base):
    df["ccdd"] = df.ubigeo.str[:2]
    df["urbano"] = df.estrato <= 5
    df["pobre"] = df.pobreza <= 2
    df["gasto_real_pc"] = df.gashog2d / df.mieperho / 12 / df.ld       # soles mensuales por persona, a precios de Lima
    df["ingreso_real_pc"] = df.inghog2d / df.mieperho / 12 / df.ld
base["area"] = base.urbano.map({True: "Urbana", False: "Rural"})
peso_hogar = sumaria.factor07 * sumaria.mieperho    # personas que representa cada hogar

# 5. Validar: (qué se revisa, valor obtenido, criterio, ¿pasa?)
pobreza_sumaria = pct(sumaria.pobre, peso_hogar)
pobreza_personas = pct(base.pobre, base.facpob07)
urbano = sumaria.urbano
urbana = pct(sumaria.pobre[urbano], peso_hogar[urbano])
rural = pct(sumaria.pobre[~urbano], peso_hogar[~urbano])
codigos = sorted(base.ccdd.unique())
llaves_ok = all(df[col].str.len().eq(n).all() for df in (sumaria, miembros) for col, n in ANCHO.items() if col in df)

validaciones = [
    ("Llaves con sus ceros a la izquierda", "anchos fijos" if llaves_ok else "hay llaves recortadas",
     "conglome 6, vivienda 3, hogar 2, codperso 2, ubigeo 6", llaves_ok),
    ("Hogares únicos en la sumaria", f"{sumaria.duplicated(LLAVES).sum()} duplicados", "0",
     not sumaria.duplicated(LLAVES).any()),
    ("Personas únicas en miembros", f"{personas.duplicated(LLAVES + ['codperso']).sum()} duplicadas", "0",
     not personas.duplicated(LLAVES + ["codperso"]).any()),
    ("Residentes habituales", f"{len(personas):,}", f"{RESIDENTES:,}", len(personas) == RESIDENTES),
    ("La unión no pierde ni duplica personas", f"{len(base):,} filas, {(base._merge != 'both').sum()} sin hogar",
     f"{len(personas):,} filas, 0 sin hogar", len(base) == len(personas) and (base._merge == "both").all()),
    ("Departamentos (ubigeo[:2])", f"{len(codigos)}: {codigos[0]}–{codigos[-1]}", "25: 01–25",
     codigos == DEPARTAMENTOS),
    ("Factores de expansión completos y positivos",
     f"factor07 {sumaria.factor07.isna().sum()} vacíos, facpob07 {base.facpob07.isna().sum()} vacíos",
     "0 vacíos, todos > 0", bool((sumaria.factor07 > 0).all() and (base.facpob07 > 0).all())),
    ("Pobreza nacional (sumaria, factor07 × mieperho)", f"{pobreza_sumaria:.2f} %",
     f"{POBREZA_NACIONAL} ± {TOLERANCIA}", abs(pobreza_sumaria - POBREZA_NACIONAL) <= TOLERANCIA),
    ("Pobreza nacional (personas, facpob07)", f"{pobreza_personas:.2f} %",
     f"{POBREZA_NACIONAL} ± {TOLERANCIA}", abs(pobreza_personas - POBREZA_NACIONAL) <= TOLERANCIA),
    ("Pobreza urbana (estrato <= 5)", f"{urbana:.2f} %", f"{POBREZA_URBANA} ± {TOLERANCIA}",
     abs(urbana - POBREZA_URBANA) <= TOLERANCIA),
    ("Pobreza rural (estrato > 5)", f"{rural:.2f} %", f"{POBREZA_RURAL} ± {TOLERANCIA}",
     abs(rural - POBREZA_RURAL) <= TOLERANCIA),
]

# 6. Guardar: validacion.txt siempre; la base y los indicadores solo si todo pasa
SALIDAS.mkdir(exist_ok=True)
fallidas = [v for v in validaciones if not v[3]]
lineas = ["Validación ENAHO 2024 · módulos 34 (sumaria) y 02 (miembros)", ""]
lineas += [f"[{'OK' if ok else 'FALLA'}] {nombre}: {valor} (esperado: {criterio})"
           for nombre, valor, criterio, ok in validaciones]
lineas += ["", f"{len(validaciones) - len(fallidas)} de {len(validaciones)} validaciones aprobadas."]
texto = "\n".join(lineas)
(SALIDAS / "validacion.txt").write_text(texto + "\n", encoding="utf-8")
print(texto)

if fallidas:
    sys.exit(f"\nERROR: fallaron {len(fallidas)} validaciones; no se guardó la base. Revisen salidas/validacion.txt.")

base.drop(columns="_merge").to_parquet(SALIDAS / "personas_2024.parquet", index=False)

sumaria["peso"] = peso_hogar
sumaria.to_parquet(SALIDAS / "hogares_2024.parquet", index=False)      # para cifras por área y departamento
indicadores = sumaria.groupby("ccdd").apply(lambda d: pd.Series({
    "poblacion": d.peso.sum(),
    "pobreza_pct": pct(d.pobre, d.peso),
    "gasto_real_pc": promedio(d.gasto_real_pc, d.peso),
    "ingreso_real_pc": promedio(d.ingreso_real_pc, d.peso),
}), include_groups=False).round(2).reset_index()
indicadores.to_csv(SALIDAS / "indicadores.csv", index=False)
print("\nGuardados: salidas/personas_2024.parquet, salidas/hogares_2024.parquet, salidas/indicadores.csv")
