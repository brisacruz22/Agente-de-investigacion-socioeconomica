"""Limpia los módulos 34 (sumaria), 02 (miembros) y 05 (empleo) de la ENAHO 2024 y valida contra las cifras del INEI.

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
EMPLEO = RAIZ / "datos" / "966-Modulo05" / "enaho01a-2024-500.dta"
SALIDAS = RAIZ / "salidas"
LLAVES = ["conglome", "vivienda", "hogar"]
ANCHO = {"conglome": 6, "vivienda": 3, "hogar": 2, "codperso": 2, "ubigeo": 6}    # con sus ceros a la izquierda

# Referencias del issue 201 (ENAHO 2024)
POBREZA_NACIONAL, POBREZA_URBANA, POBREZA_RURAL = 27.6, 24.8, 39.3
TOLERANCIA = 0.1                                    # puntos porcentuales
RESIDENTES = 108_664
# Códigos de ubigeo[:2] (iguales a FIRST_IDDP del GeoJSON del curso); los nombres llevan tildes para gráficos y mapas
DEPARTAMENTOS = {
    "01": "Amazonas", "02": "Áncash", "03": "Apurímac", "04": "Arequipa", "05": "Ayacucho", "06": "Cajamarca",
    "07": "Callao", "08": "Cusco", "09": "Huancavelica", "10": "Huánuco", "11": "Ica", "12": "Junín",
    "13": "La Libertad", "14": "Lambayeque", "15": "Lima", "16": "Loreto", "17": "Madre de Dios", "18": "Moquegua",
    "19": "Pasco", "20": "Piura", "21": "Puno", "22": "San Martín", "23": "Tacna", "24": "Tumbes", "25": "Ucayali",
}
# Ramas: (nombre, primera y última división CIIU rev. 4), revisadas con enaho_tabla_ciiu_rev4.dta del módulo 05.
# Las divisiones que no están aquí son Servicios.
RAMAS = [("Agropecuaria", 1, 2), ("Pesca", 3, 3), ("Minería", 5, 9), ("Manufactura", 10, 33),
         ("Construcción", 41, 43), ("Comercio", 45, 47)]
# Composición del ingreso neto total (inghog2d): componente → variables de la sumaria (reference.md, secciones 04-09).
# Lo que no cubren estas variables queda como «otros» (la diferencia con inghog2d).
COMPONENTES = {
    "trabajo": ["ingnethd", "pagesphd", "ingindhd", "ingauthd", "insedlhd", "paesechd", "ingseihd", "isecauhd",
                "ingexthd"],
    "alquiler_imputado": ["ia01hd"],
    "transferencias": ["ingtrahd", "ingtexhd"],
    "extraordinarios": ["ingoexhd"],
    "rentas": ["ingrenhd"],
}


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


def rama(codigo):
    """Rama de un código CIIU rev. 4 (p506r4, ej. 111 = 0111): se mira la división, sus dos primeros dígitos."""
    division = int(codigo) // 100
    return next((nombre for nombre, desde, hasta in RAMAS if desde <= division <= hasta), "Servicios")


# 1. Leer
variables_ingreso = [v for lista in COMPONENTES.values() for v in lista]
sumaria = leer(SUMARIA, LLAVES + ["ubigeo", "dominio", "estrato", "mieperho", "pobreza", "factor07",
                                  "inghog2d", "gashog2d", "linea", "ld"] + variables_ingreso)
miembros = leer(MIEMBROS, LLAVES + ["codperso", "p204", "p205", "p206", "p207", "p208a", "facpob07"])
empleo = leer(EMPLEO, LLAVES + ["codperso", "ocu500", "p506r4", "fac500a"])

# 2. Filtrar residentes habituales (condición del INEI usada en la sesión 16)
residente = (((miembros.p204 == 1) & (miembros.p205 == 2)) |
             ((miembros.p204 == 2) & (miembros.p206 == 1)))
personas = miembros[residente].drop(columns=["p204", "p205", "p206"])

# 3. Unir: cada persona con su hogar. ubigeo, dominio y estrato vienen solo de la sumaria
base = personas.merge(sumaria, on=LLAVES, how="left", validate="m:1", indicator=True)

# 4. Construir
for df in (sumaria, base):
    df["ccdd"] = df.ubigeo.str[:2]
    df["departamento"] = df.ccdd.map(DEPARTAMENTOS)
    df["urbano"] = df.estrato <= 5
    df["pobre"] = df.pobreza <= 2
    df["gasto_real_pc"] = df.gashog2d / df.mieperho / 12 / df.ld       # soles mensuales por persona, a precios de Lima
    df["ingreso_real_pc"] = df.inghog2d / df.mieperho / 12 / df.ld
base["area"] = base.urbano.map({True: "Urbana", False: "Rural"})
peso_hogar = sumaria.factor07 * sumaria.mieperho    # personas que representa cada hogar

# Composición del ingreso: cada componente suma sus variables (vacío = 0); «otros» es lo que falta para inghog2d
for componente, variables in COMPONENTES.items():
    sumaria[f"ing_{componente}"] = sumaria[variables].fillna(0).sum(axis=1)
sumaria["ing_otros"] = sumaria.inghog2d - sumaria[[f"ing_{c}" for c in COMPONENTES]].sum(axis=1)

# Empleo: ocupados (ocu500 == 1, el módulo ya es de 14 años a más) que además son residentes habituales
ocupados = empleo[empleo.ocu500 == 1].merge(base[LLAVES + ["codperso", "ccdd", "departamento"]],
                                            on=LLAVES + ["codperso"], how="inner", validate="1:1")
ocupados["rama"] = ocupados.p506r4.map(rama)

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
     codigos == list(DEPARTAMENTOS)),
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
    ("Componentes del ingreso no superan inghog2d", f"{(sumaria.ing_otros < -1).sum()} hogares con «otros» < 0",
     "0 (tolerancia S/ 1)", not (sumaria.ing_otros < -1).any()),
    ("Ocupados con rama CIIU (p506r4) y factor (fac500a)",
     f"{ocupados.p506r4.isna().sum()} sin rama, {(ocupados.fac500a.isna() | (ocupados.fac500a <= 0)).sum()} sin factor",
     "0 y 0", bool(ocupados.p506r4.notna().all() and (ocupados.fac500a > 0).all())),
    ("Ocupados residentes en los 25 departamentos", f"{ocupados.ccdd.nunique()} ({len(ocupados):,} ocupados)", "25",
     ocupados.ccdd.nunique() == 25),
]

# 6. Guardar: validacion.txt siempre; la base y los indicadores solo si todo pasa
SALIDAS.mkdir(exist_ok=True)
fallidas = [v for v in validaciones if not v[3]]
lineas = ["Validación ENAHO 2024 · módulos 34 (sumaria), 02 (miembros) y 05 (empleo)", ""]
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
indicadores = sumaria.groupby(["ccdd", "departamento"]).apply(lambda d: pd.Series({
    "poblacion": d.peso.sum(),
    "pobreza_pct": pct(d.pobre, d.peso),
    "gasto_real_pc": promedio(d.gasto_real_pc, d.peso),
    "ingreso_real_pc": promedio(d.ingreso_real_pc, d.peso),
}), include_groups=False).reset_index()

# Composición: de cada sol de ingreso del departamento, cuánto viene de cada fuente. Se expande con factor07
# (hogares), no con factor07 × mieperho, porque es una proporción de totales y no un promedio por persona.
for componente in list(COMPONENTES) + ["otros"]:
    total = sumaria.groupby("ccdd").apply(
        lambda d: 100 * (d[f"ing_{componente}"] * d.factor07).sum() / (d.inghog2d * d.factor07).sum(),
        include_groups=False)
    indicadores[f"ing_{componente}_pct"] = indicadores.ccdd.map(total)

# Empleo por rama: % de ocupados de cada rama en el departamento, con fac500a; y la rama con más ocupados
empleo_rama = ocupados.pivot_table(index="ccdd", columns="rama", values="fac500a", aggfunc="sum", fill_value=0)
empleo_rama = 100 * empleo_rama.div(empleo_rama.sum(axis=1), axis=0)
indicadores["rama_principal"] = indicadores.ccdd.map(empleo_rama.idxmax(axis=1))
for nombre in empleo_rama.columns:
    indicadores[f"empleo_{nombre.lower().replace('í', 'i').replace('ó', 'o')}_pct"] = indicadores.ccdd.map(
        empleo_rama[nombre])

indicadores.round(2).to_csv(SALIDAS / "indicadores.csv", index=False)
print("\nGuardados: salidas/personas_2024.parquet, salidas/hogares_2024.parquet, salidas/indicadores.csv")
