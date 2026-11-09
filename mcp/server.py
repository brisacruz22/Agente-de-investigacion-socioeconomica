"""Servidor MCP del BCRP. Empiecen aquí: buscar_series ya funciona; completen los TODO hasta que pasen las pruebas.

    uv run pytest                                           # el contrato: las 8 pruebas deben pasar
    uv run server.py                                        # el servidor, por stdio
    claude mcp add --scope project bcrp -- uv run server.py # conectarlo a Claude Code

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
CATALOGO = AQUI / "datos" / "catalogo_bcrp.csv"
URL_CATALOGO = "https://estadisticas.bcrp.gob.pe/estadisticas/series/metadata"
API = "https://estadisticas.bcrp.gob.pe/estadisticas/series/api"
SOLO_LECTURA = {"readOnlyHint": True, "openWorldHint": True}

mcp = FastMCP("bcrp", instructions=(
    "Series oficiales del Banco Central de Reserva del Perú (BCRP). Primero busca el código con buscar_series; "
    "luego usa resumen para variaciones, promedios y extremos, y serie para los datos. No calcules a mano: "
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
                            "Fecha de actualización": "actualizada", "Fecha de inicio": "inicio"})
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


# TODO 1 · serie(codigo, desde, hasta) -> {"codigo", "nombre", "frecuencia", "datos": [{"periodo", "valor"}], "fuente"}
#   La API se llama así: f"{API}/{codigo}/json/{desde}/{hasta}" y responde
#   {"config": {...}, "periods": [{"name": "Ene.2025", "values": ["0.81"]}, ...]}
#   - Fechas que pide la API: 2025-1 (mensual y trimestral), 2025-01-15 (diaria), 2025 (anual).
#   - Nombres que devuelve: "Ene.2025" (mensual), "01.Oct.26" (diaria), "T1.25" (trimestral), "2025" (anual).
#     Setiembre viene como "Set". Devuelvan el periodo como "2025-01", "2026-10-01", "2025-T1" o "2025".
#   - Salten los valores "n.d." y usen la frecuencia de _ficha(codigo) para saber qué formato pedir.
#   - Si recibe muchos pedidos seguidos, la API responde una página HTML en vez de JSON: esperen unos segundos y
#     reintenten (y guarden en caché lo que ya bajaron).
#   - Un código que no existe debe dar un ToolError que diga el código.

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

# TODO 2 · resumen(codigo, desde, hasta): primero, ultimo, cambio, variacion_pct, promedio, maximo y minimo
#   (los tres últimos con su periodo). Úsenla para que el modelo nunca haga cuentas a mano.

# TODO 3 · Una herramienta suya, bien descrita. Ideas:
#   - comparar_paises con la API del Banco Mundial, que tampoco pide clave:
#     https://api.worldbank.org/v2/country/PER;CHL;COL/indicator/NY.GDP.MKTP.KD.ZG?format=json&date=2015:2025
#   - correlacion(codigo_a, codigo_b, desde, hasta)
#   - grafico(codigo, desde, hasta) que guarde un PNG en salidas/ y devuelva la ruta

# TODO 4 · Un recurso, por ejemplo la plantilla bcrp://serie/{codigo} con la ficha de la serie.

# TODO 5 · Un prompt, por ejemplo informe(tema) que pida citar el código y el periodo de cada cifra.


# TODO 2 · resumen: Python hace las cuentas, no el modelo
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


# TODO 3 · herramienta propia
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


# TODO 4 · recurso: la ficha de cualquier serie, por su código
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


# TODO 5 · prompt: una receta de informe con cifras verificables
@mcp.prompt
def informe(tema: str) -> str:
    """Informe breve sobre un tema económico del Perú con cifras del BCRP."""
    return (f"Escribe un informe de 5 viñetas sobre «{tema}» con datos del BCRP. "
            "Busca los códigos con buscar_series y usa resumen o serie para cada cifra; no calcules a mano. "
            "En cada viñeta cita el código de la serie y el periodo.")


if __name__ == "__main__":
    mcp.run()