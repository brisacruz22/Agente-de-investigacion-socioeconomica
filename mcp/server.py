"""Servidor MCP del BCRP (tarea 4). Parte del proyecto de la sesión 04 (brisacruz22/mcp-bcrp).

    uv run pytest                 # desde la raíz del repo: 8 pruebas originales + 2 propias
    uv run mcp/server.py          # el servidor, por stdio (Claude Code lo levanta con .mcp.json)

Las cuentas las hace Python, no el modelo: así cada cifra sale de una llamada que se puede repetir.
"""

import json
import re
import time
import unicodedata
from functools import cache
from pathlib import Path

import httpx
import pandas as pd
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError


AQUI = Path(__file__).parent
RAIZ = AQUI.parent                                     # raíz del repo: el servidor vive en mcp/
CATALOGO = RAIZ / "datos" / "catalogo_bcrp.csv"
FIGURAS = RAIZ / "figuras"
URL_CATALOGO = "https://estadisticas.bcrp.gob.pe/estadisticas/series/metadata"
API = "https://estadisticas.bcrp.gob.pe/estadisticas/series/api"
SOLO_LECTURA = {"readOnlyHint": True, "openWorldHint": True}

mcp = FastMCP("bcrp", instructions=(
    "Series oficiales del Banco Central de Reserva del Perú (BCRP). Primero busca el código con buscar_series; "
    "luego usa resumen para variaciones, promedios y extremos, y serie para los datos. Antes de comparar o "
    "interpretar una serie, revisa su unidad, fuente y cobertura con metadatos. Para una misma serie en los "
    "departamentos usa comparar_departamentos; para guardar un gráfico, grafico. No calcules a mano: "
    "cita siempre el código de la serie y el periodo."))


def _sin_tildes(s):
    return unicodedata.normalize("NFD", str(s).lower()).encode("ascii", "ignore").decode()


@cache
def catalogo():
    """El catálogo oficial: 17 mil series en unos 7 MB. Se baja una vez y queda en datos/."""
    if not CATALOGO.exists():
        CATALOGO.parent.mkdir(exist_ok=True)
        r = httpx.get(URL_CATALOGO, timeout=120)
        r.raise_for_status()
        CATALOGO.write_text(r.content.decode("latin-1"), encoding="utf-8")
    df = pd.read_csv(CATALOGO, sep=";", dtype=str).fillna("")
    df = df.rename(columns={"Código de serie": "codigo", "Categoría de serie": "categoria", "Grupo de serie": "grupo",
                            "Nombre de serie": "nombre", "Frecuencia": "frecuencia",
                            "Fecha de actualización": "actualizada", "Fecha de inicio": "inicio",
                            "Fecha de fin": "fin", "Descripción de la serie": "descripcion",
                            "Metodología de la serie": "metodologia", "Unidad de medida": "unidad", "Escala": "escala",
                            "Geografía (País, Región de Perú)": "geografia", "Fuente": "fuente_original",
                            "Área que publica": "area"})
    df["texto"] = (df.categoria + " " + df.grupo + " " + df.nombre).map(_sin_tildes)
    return df


def _ficha(codigo):
    fila = catalogo().query("codigo == @codigo")
    if fila.empty:
        raise ToolError(f"No existe el código de serie {codigo!r}. Búsquenlo con buscar_series.")
    f = fila.iloc[0]
    return {"codigo": f.codigo, "nombre": f"{f.grupo} - {f.nombre}", "categoria": f.categoria,
            "frecuencia": f.frecuencia, "inicio": f.inicio, "actualizada": f.actualizada}


@mcp.tool(annotations=SOLO_LECTURA)
def buscar_series(texto: str, frecuencia: str | None = None, limite: int = 10) -> list[dict]:
    """Busca series del BCRP por palabras: todas deben aparecer en la categoría, el grupo o el nombre.

    Ejemplos: "ipc 12 meses", "tipo de cambio interbancario venta", "reservas internacionales netas",
    "tasa de referencia", "cobre precio". frecuencia: "Diaria", "Mensual", "Trimestral" o "Anual".
    Devuelve el código, el nombre completo, la frecuencia y desde cuándo hay datos. Si no hay resultados,
    prueben con menos palabras.
    """
    df = catalogo()
    m = pd.Series(True, index=df.index)
    for palabra in _sin_tildes(texto).split():
        m &= df.texto.str.contains(rf"\b{re.escape(palabra)}")    # inicio de palabra: "oro" no es "tesoro"
    if frecuencia:
        m &= df.frecuencia.str.lower() == frecuencia.lower()
    # primero las series vigentes y, entre ellas, las de nombre más corto (las más generales)
    sel = df[m]
    orden = sel.assign(vieja=sel.actualizada < "2025", largo=(sel.grupo + sel.nombre).str.len())
    return [_ficha(c) for c in orden.sort_values(["vieja", "largo"]).head(limite).codigo]


# Nombres de mes que usa el BCRP. Setiembre viene como "Set".
MESES = {"Ene": "01", "Feb": "02", "Mar": "03", "Abr": "04", "May": "05", "Jun": "06",
         "Jul": "07", "Ago": "08", "Set": "09", "Sep": "09", "Oct": "10", "Nov": "11", "Dic": "12"}


def _anio(a):
    """'26' -> '2026', '97' -> '1997'; '2025' se queda igual."""
    if len(a) == 4:
        return a
    return ("19" if int(a) > 50 else "20") + a


def _fecha_api(fecha, frecuencia):
    """Lo que recibe la herramienta -> lo que pide la API."""
    f = frecuencia.lower()
    if f == "diaria":
        return fecha                                   # "2026-10-01" va tal cual
    if f == "anual":
        return fecha[:4]                               # "2025"
    anio, mes = fecha.split("-")[:2]                   # "2025-01" o "2025-T1"
    return f"{anio}-{int(mes.upper().lstrip('T'))}"    # -> "2025-1"


def _periodo(nombre, frecuencia):
    """Lo que devuelve la API -> nuestro formato."""
    f = frecuencia.lower()
    if f == "diaria":                                  # "01.Oct.26" -> "2026-10-01"
        dia, mes, anio = nombre.split(".")
        return f"{_anio(anio)}-{MESES[mes]}-{dia}"
    if f == "mensual":                                 # "Ene.2025" -> "2025-01"
        mes, anio = nombre.split(".")
        return f"{_anio(anio)}-{MESES[mes]}"
    if f == "trimestral":                              # "T1.25" -> "2025-T1"
        t, anio = nombre.split(".")
        return f"{_anio(anio)}-{t}"
    return nombre                                      # anual: "2025"


def _pedir(url):
    """Si la API se satura, responde HTML en vez de JSON: espera y reintenta."""
    for intento in range(3):
        r = httpx.get(url, timeout=30)
        try:
            return r.json()
        except ValueError:
            time.sleep(2 * (intento + 1))
    raise ToolError("El BCRP no respondió con datos. Reintenta en unos segundos.")


@cache
def _serie(codigo, desde, hasta):
    ficha = _ficha(codigo)                             # si no existe, ToolError con el código
    frec = ficha["frecuencia"]
    url = f"{API}/{codigo}/json/{_fecha_api(desde, frec)}/{_fecha_api(hasta, frec)}"
    datos = []
    for p in _pedir(url).get("periods", []):
        valor = p["values"][0]
        if valor == "n.d.":                            # sin dato: se salta
            continue
        datos.append({"periodo": _periodo(p["name"], frec), "valor": float(valor)})
    return {"codigo": codigo, "nombre": ficha["nombre"], "frecuencia": frec,
            "datos": datos, "fuente": url}


@mcp.tool(annotations=SOLO_LECTURA)
def serie(codigo: str, desde: str, hasta: str) -> dict:
    """Datos de una serie del BCRP entre dos fechas, ambas incluidas, con la URL de la fuente.

    Primero busca el código con buscar_series. Fechas: "2025-01" (mensual), "2026-10-15" (diaria),
    "2025-T1" (trimestral), "2025" (anual). Ejemplo: serie("PN01273PM", "2026-01", "2026-09").
    """
    return _serie(codigo, desde, hasta)


# resumen: Python hace las cuentas, no el modelo
@mcp.tool(annotations=SOLO_LECTURA)
def resumen(codigo: str, desde: str, hasta: str) -> dict:
    """Resumen de una serie del BCRP entre dos fechas: primer y último dato, cambio, variación %,
    promedio, máximo y mínimo (con su periodo). Úsala para cualquier pregunta de variaciones o
    extremos en vez de calcular a mano. Fechas como en serie, ej. resumen("PN01273PM", "2025-12", "2026-09").

    Si la serie ya es una tasa (var%, tasas de interés), citen cambio, que está en puntos porcentuales, y no
    variacion_pct: la inflación que pasa de -2.85 a 3.65 da variacion_pct -227.78 aunque subió."""
    s = _serie(codigo, desde, hasta)
    datos = s["datos"]
    if not datos:
        raise ToolError(f"La serie {codigo} no tiene datos entre {desde} y {hasta}.")
    valores = pd.Series([d["valor"] for d in datos])
    primero, ultimo = datos[0], datos[-1]
    cambio = ultimo["valor"] - primero["valor"]
    return {
        "codigo": codigo, "nombre": s["nombre"],
        "primero": primero, "ultimo": ultimo,
        "cambio": round(cambio, 4),
        "variacion_pct": round(100 * cambio / primero["valor"], 2) if primero["valor"] else None,
        "promedio": round(float(valores.mean()), 4),
        "maximo": datos[int(valores.idxmax())],
        "minimo": datos[int(valores.idxmin())],
        "fuente": s["fuente"],
    }


# correlacion: uno de los ejemplos de herramienta de análisis del issue
@mcp.tool(annotations=SOLO_LECTURA)
def correlacion(codigo_a: str, codigo_b: str, desde: str, hasta: str) -> dict:
    """Correlación de Pearson entre dos series del BCRP de la misma frecuencia, en los periodos
    que comparten. Úsala para preguntas como «¿se mueven juntos el tipo de cambio y la inflación?».
    Ej.: correlacion("PN01273PM", "PN01207PM", "2023-01", "2026-09")."""
    a, b = _serie(codigo_a, desde, hasta), _serie(codigo_b, desde, hasta)
    da = pd.DataFrame(a["datos"]).set_index("periodo").valor
    db = pd.DataFrame(b["datos"]).set_index("periodo").valor
    juntos = pd.concat([da, db], axis=1, join="inner").dropna()
    if len(juntos) < 3:
        raise ToolError("Las series comparten menos de 3 periodos: revisen que tengan la misma frecuencia.")
    return {"correlacion": round(float(juntos.corr().iloc[0, 1]), 4), "n": len(juntos),
            "series": [a["nombre"], b["nombre"]], "fuentes": [a["fuente"], b["fuente"]]}


# ── Herramientas nuevas de la tarea 4 ──────────────────────────────────────────────────────────────────────────

# Departamentos del Perú con su código INEI (ccdd = ubigeo[:2]), para cruzar con la ENAHO.
# El BCRP separa a veces «Lima Metropolitana» y «Lima Provincias»: ambas son el 15 de la ENAHO.
DEPARTAMENTOS = {
    "amazonas": ("Amazonas", "01"), "ancash": ("Áncash", "02"), "apurimac": ("Apurímac", "03"),
    "arequipa": ("Arequipa", "04"), "ayacucho": ("Ayacucho", "05"), "cajamarca": ("Cajamarca", "06"),
    "callao": ("Callao", "07"), "cusco": ("Cusco", "08"), "huancavelica": ("Huancavelica", "09"),
    "huanuco": ("Huánuco", "10"), "ica": ("Ica", "11"), "junin": ("Junín", "12"),
    "la libertad": ("La Libertad", "13"), "lambayeque": ("Lambayeque", "14"),
    "lima metropolitana": ("Lima Metropolitana", "15"), "lima provincias": ("Lima Provincias", "15"),
    "lima y callao": ("Lima y Callao", "15+07"), "lima": ("Lima", "15"), "loreto": ("Loreto", "16"),
    "madre de dios": ("Madre de Dios", "17"), "moquegua": ("Moquegua", "18"), "pasco": ("Pasco", "19"),
    "piura": ("Piura", "20"), "puno": ("Puno", "21"), "san martin": ("San Martín", "22"),
    "tacna": ("Tacna", "23"), "tumbes": ("Tumbes", "24"), "ucayali": ("Ucayali", "25"),
}
# Los nombres largos primero, para que «lima metropolitana» gane a «lima»
_PATRON_DEP = re.compile(r"\b(" + "|".join(sorted(map(re.escape, DEPARTAMENTOS), key=len, reverse=True)) + r")\b")


def _departamento(texto):
    """'Oro - Cajamarca (grs.f)' -> ('Cajamarca', '06'); None si el texto no nombra un departamento."""
    m = _PATRON_DEP.search(_sin_tildes(texto))
    return DEPARTAMENTOS[m.group(1)] if m else None


def _unidad(ficha):
    """En las series regionales el catálogo deja vacía la unidad: está entre paréntesis en el nombre o el grupo."""
    if ficha.get("unidad"):
        return ficha["unidad"]
    for texto in (ficha["nombre_corto"], ficha["grupo"]):
        m = re.findall(r"\(([^()]*)\)", texto)
        if m:
            return m[-1]
    return ""


def _ficha_completa(codigo):
    fila = catalogo().query("codigo == @codigo")
    if fila.empty:
        raise ToolError(f"No existe el código de serie {codigo!r}. Búsquenlo con buscar_series.")
    f = fila.iloc[0]
    ficha = {"codigo": f.codigo, "nombre_corto": f.nombre, "grupo": f.grupo, "categoria": f.categoria,
             "unidad": f.unidad, "escala": f.escala, "frecuencia": f.frecuencia,
             "inicio": f.inicio, "fin": f.fin, "actualizada": f.actualizada,
             "fuente_original": f.fuente_original or "BCRP", "descripcion": f.descripcion,
             "metodologia": f.metodologia, "area": f.area,
             "ambito": {"PE": "Perú", "RE": "Departamental"}.get(f.geografia.strip(), "No indicado en el catálogo")}
    ficha["unidad"] = _unidad(ficha)
    dep = _departamento(f.grupo + " " + f.nombre) if ficha["ambito"] == "Departamental" else None
    ficha["departamento"], ficha["ccdd"] = dep if dep else (None, None)
    return ficha


@mcp.tool(annotations=SOLO_LECTURA)
def metadatos(codigo: str) -> dict:
    """Ficha completa de una serie del BCRP: unidad, fuente original, cobertura (inicio y fin), última
    actualización, ámbito (Perú o departamental), departamento y descripción.

    Úsala antes de comparar o interpretar una serie: dice en qué unidad está (el oro va en gramos finos y el cobre
    en toneladas), hasta cuándo hay datos (para declarar desfases con otras fuentes) y quién la produce.
    Ej.: metadatos("RD15548DA")."""
    return _ficha_completa(codigo)


def _firma(grupo, nombre):
    """El mismo indicador en distintos departamentos: el nombre del departamento se cambia por <dep>."""
    return _PATRON_DEP.sub("<dep>", _sin_tildes(f"{grupo} | {nombre}"))


def _frecuencia_de(periodo):
    if re.fullmatch(r"\d{4}", periodo):
        return "Anual"
    if re.fullmatch(r"\d{4}-T[1-4]", periodo, flags=re.I):
        return "Trimestral"
    if re.fullmatch(r"\d{4}-\d{2}", periodo):
        return "Mensual"
    raise ToolError(f"Periodo {periodo!r} no válido: usen '2022' (anual), '2022-T4' (trimestral) o '2022-12' (mensual).")


@mcp.tool(annotations=SOLO_LECTURA)
def comparar_departamentos(texto: str, periodo: str) -> dict:
    """El mismo indicador del BCRP para todos los departamentos que lo tienen, en un periodo, ordenado de mayor a
    menor y con el código INEI del departamento (ccdd) para cruzarlo con la ENAHO.

    texto: palabras del indicador, como en buscar_series (ej. "exportaciones tradicionales mineros",
    "produccion oro", "credito directo", "producto bruto interno constantes"). periodo: "2022" (anual),
    "2022-T4" (trimestral) o "2022-12" (mensual); la frecuencia sale del formato.
    Si las palabras calzan con varios indicadores, devuelve un error con las opciones para afinar la búsqueda.
    Los departamentos sin dato en ese periodo van en «faltantes»: no se inventan."""
    frec = _frecuencia_de(periodo)
    df = catalogo()
    df = df[(df.geografia.str.strip() == "RE") & (df.frecuencia == frec)]
    m = pd.Series(True, index=df.index)
    for palabra in _sin_tildes(texto).split():
        m &= df.texto.str.contains(rf"\b{re.escape(palabra)}")
    sel = df[m].copy()
    sel["firma"] = [_firma(g, n) for g, n in zip(sel.grupo, sel.nombre)]
    sel = sel[sel.firma.str.contains("<dep>", regex=False)]
    if sel.empty:
        raise ToolError(f"No hay series departamentales {frec.lower()}es con «{texto}». Prueben con menos palabras "
                        "o busquen primero con buscar_series.")
    firmas = sel.firma.value_counts()
    if len(firmas) > 1:
        opciones = "; ".join(firmas.index[:10])
        raise ToolError(f"«{texto}» calza con {len(firmas)} indicadores; agreguen palabras para elegir uno. "
                        f"Opciones: {opciones}")
    datos, faltantes, unidad = [], [], ""
    for codigo in sel.codigo:
        ficha = _ficha_completa(codigo)
        unidad = unidad or ficha["unidad"]
        try:
            s = _serie(codigo, periodo, periodo)
        except ToolError as e:
            faltantes.append({"departamento": ficha["departamento"], "codigo": codigo, "motivo": str(e)})
            continue
        if not s["datos"]:
            faltantes.append({"departamento": ficha["departamento"], "codigo": codigo, "motivo": "sin dato en el periodo"})
            continue
        datos.append({"departamento": ficha["departamento"], "ccdd": ficha["ccdd"], "codigo": codigo,
                      "valor": s["datos"][-1]["valor"], "fuente": s["fuente"]})
    datos.sort(key=lambda d: d["valor"], reverse=True)
    lima = [d["departamento"] for d in datos if d["ccdd"] in ("15", "15+07")]
    return {"indicador": sel.iloc[0].firma,
            "periodo": periodo, "unidad": unidad, "fuente_original": _ficha_completa(sel.iloc[0].codigo)["fuente_original"],
            "n": len(datos), "datos": datos, "faltantes": faltantes,
            "nota": ("El BCRP separa " + " y ".join(lima) + "; en la ENAHO ambas son el departamento 15.")
                    if len(lima) > 1 else ""}


def _etiqueta(ficha):
    """Etiqueta corta para un gráfico: el departamento si la serie es departamental; si no, el nombre."""
    return ficha["departamento"] or re.sub(r"\s*\([^()]*\)\s*$", "", ficha["nombre_corto"])


TIPOS_GRAFICO = ("linea", "area_apilada", "barras")


@mcp.tool(annotations={"readOnlyHint": False, "openWorldHint": True})
def grafico(codigos: list[str], desde: str, hasta: str, tipo: str = "linea", titulo: str | None = None,
            porcentaje: bool = False) -> dict:
    """Guarda en figuras/ un gráfico de una o varias series del BCRP (PNG a 200 dpi y un CSV con los datos graficados)
    y devuelve las rutas.

    tipo:
    - "linea": evolución de una o varias series, con la etiqueta al final de cada línea.
    - "area_apilada": composición en el tiempo (ej. exportaciones de un departamento por grupo de productos);
      con porcentaje=True muestra la participación de cada serie en el total.
    - "barras": barras horizontales ordenadas con el último valor de cada serie en el rango; sirve para los
      códigos que devuelve comparar_departamentos (usen desde = hasta = el periodo).
    El título debe decir lo que muestra el gráfico (el hallazgo), no solo el tema.
    Ej.: grafico(["PN01273PM"], "2022-01", "2024-12", "linea", "La inflación de Lima bajó de 8.8 % a 2.0 %")."""
    # Bases: python-graph-gallery.com/122-multiple-lines-chart, /web-line-chart-with-labels-at-line-end,
    # /255-percentage-stacked-area-chart y /2-horizontal-barplot (licencia 0BSD).
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    if tipo not in TIPOS_GRAFICO:
        raise ToolError(f"tipo {tipo!r} no válido: usen uno de {TIPOS_GRAFICO}.")
    if not codigos:
        raise ToolError("Den al menos un código de serie.")
    fichas = [_ficha_completa(c) for c in codigos]
    series = [_serie(c, desde, hasta) for c in codigos]
    vacias = [c for c, s in zip(codigos, series) if not s["datos"]]
    if vacias:
        raise ToolError(f"Sin datos entre {desde} y {hasta} para: {', '.join(vacias)}. Revisen la cobertura con metadatos.")
    etiquetas = [_etiqueta(f) for f in fichas]
    if len(set(etiquetas)) < len(etiquetas):                       # etiquetas repetidas: se usa el nombre completo
        etiquetas = [f"{f['grupo']} - {f['nombre_corto']}" for f in fichas]
    ancho = pd.concat({e: pd.DataFrame(s["datos"]).set_index("periodo").valor for e, s in zip(etiquetas, series)},
                      axis=1).sort_index()
    unidades = {f["unidad"] for f in fichas}
    unidad = unidades.pop() if len(unidades) == 1 else ""

    fig, ax = plt.subplots(figsize=(10, 5.5 if tipo != "barras" else max(4, 0.32 * len(codigos) + 1.5)))
    if tipo == "linea":
        x = range(len(ancho))
        finales = []
        for e in ancho.columns:
            ax.plot(x, ancho[e].values, lw=2)
            ultimo = ancho[e].last_valid_index()
            finales.append([ancho.index.get_loc(ultimo), ancho.at[ultimo, e], e, ax.lines[-1].get_color()])
        if len(ancho.columns) > 1:                               # etiquetas al final de cada línea
            separacion = (ax.get_ylim()[1] - ax.get_ylim()[0]) * 0.045
            y_anterior = None
            for x_fin, y_fin, texto, color in sorted(finales, key=lambda f: f[1]):
                y = y_fin if y_anterior is None else max(y_fin, y_anterior + separacion)   # sube si pisa a la de abajo
                ax.text(x_fin + 0.5, y, texto, color=color, va="center", fontsize=9, fontweight="bold")
                y_anterior = y
            ax.set_xlim(-0.5, len(ancho) - 1 + max(3, len(ancho) * 0.18))
        paso = max(1, len(ancho) // 8)
        ax.set_xticks(list(x)[::paso], ancho.index[::paso])
        ax.set_ylabel(unidad)
    elif tipo == "area_apilada":
        datos = ancho.fillna(0)
        if porcentaje:
            datos = datos.divide(datos.sum(axis=1), axis=0) * 100
        ax.stackplot(range(len(datos)), *[datos[c] for c in datos.columns], labels=datos.columns, alpha=0.85)
        ax.legend(loc="upper left", fontsize=8, frameon=False, ncol=2)
        ax.margins(0, 0)
        paso = max(1, len(datos) // 8)
        ax.set_xticks(range(0, len(datos), paso), datos.index[::paso])
        ax.set_ylabel("% del total" if porcentaje else unidad)
        ancho = datos
    else:                                                        # barras
        valores = ancho.ffill().iloc[-1].sort_values()
        ax.barh(valores.index, valores.values, color="#2E5E7E")
        for i, v in enumerate(valores.values):
            ax.text(v, i, f" {v:,.1f}", va="center", fontsize=8)
        ax.set_xlabel(unidad)
        ax.margins(x=0.12)
        ancho = valores.to_frame(f"{desde}" if desde == hasta else f"último valor {desde} a {hasta}")
    ax.set_title(titulo or (fichas[0]["grupo"] if len(fichas) > 1 else fichas[0]["nombre_corto"]),
                 loc="left", fontsize=12, fontweight="bold")
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="x" if tipo == "barras" else "y", alpha=0.3)
    fuentes = sorted({f["fuente_original"] for f in fichas})
    origen = "BCRP" if fuentes == ["BCRP"] else f"BCRP, con datos de {', '.join(f for f in fuentes if f != 'BCRP')}"
    pie = f"Fuente: {origen}. Series {', '.join(codigos[:6])}{' y otras' if len(codigos) > 6 else ''}."
    fig.text(0.01, 0.01, pie, fontsize=7, color="#555")
    fig.tight_layout(rect=(0, 0.04, 1, 1))

    FIGURAS.mkdir(exist_ok=True)
    clave = re.sub(r"[^A-Za-z0-9]+", "", "_".join(codigos))[:40]
    base = FIGURAS / f"bcrp_{tipo}_{clave}_{desde}_{hasta}"
    fig.savefig(base.with_suffix(".png"), dpi=200)
    plt.close(fig)
    ancho.to_csv(base.with_suffix(".csv"))
    return {"png": str(base.with_suffix(".png").relative_to(RAIZ)), "csv": str(base.with_suffix(".csv").relative_to(RAIZ)),
            "tipo": tipo, "series": dict(zip(codigos, etiquetas)), "unidad": unidad,
            "fuentes": [s["fuente"] for s in series]}


# Recurso: la ficha de cualquier serie, por su código
@mcp.resource("bcrp://serie/{codigo}")
def ficha(codigo: str) -> str:
    """Ficha de una serie del BCRP: nombre, categoría, frecuencia y desde cuándo hay datos."""
    return json.dumps(_ficha(codigo), ensure_ascii=False)


# Un recurso fijo, para que aparezca en el menú @ de Claude Code (las plantillas no salen ahí)
PRINCIPALES = ["PN01273PM", "PN01271PM", "PD04638PD"]


@mcp.resource("bcrp://series/principales")
def principales() -> str:
    """Fichas de las series más consultadas: inflación de Lima a 12 meses, IPC mensual y tipo de cambio."""
    return json.dumps([_ficha(c) for c in PRINCIPALES], ensure_ascii=False)


# Prompt: una receta de informe con cifras verificables
@mcp.prompt
def informe(tema: str) -> str:
    """Informe breve sobre un tema económico del Perú con cifras del BCRP."""
    return (f"Escribe un informe de 5 viñetas sobre «{tema}» con datos del BCRP. "
            "Busca los códigos con buscar_series y usa resumen o serie para cada cifra; no calcules a mano. "
            "En cada viñeta cita el código de la serie y el periodo.")


if __name__ == "__main__":
    mcp.run()