"""¿Mejoran el MCP y las skills las respuestas de Claude? Las mismas 10 preguntas en dos modos, contra la verdad.

    uv run evaluacion/evaluar.py                       # modos A y B, las 10 preguntas
    uv run evaluacion/evaluar.py --modos B --ids enaho_pobreza_puno   # probar una sola antes de correr todo

Modo A: sin MCP ni skills ni herramientas, desde una carpeta vacía (no ve CLAUDE.md, .claude/skills ni salidas/).
Modo B: desde la raíz del repo, con el MCP del BCRP, las skills y Bash/Read para que corran sus scripts.
Cada pregunta es una sesión independiente de claude -p (sin persistencia) y debe responder un JSON con el valor.
Escribe evaluacion/resultados.csv. Las herramientas se leen de la salida stream-json (lo que de verdad llamó),
no de lo que el modelo dice. La interpretación de las preguntas combinadas la califica una persona en la columna
interpretacion_ok, con el criterio de preguntas.csv.
"""
import argparse
import json
import subprocess
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

AQUI = Path(__file__).parent
RAIZ = AQUI.parent
MCP_JSON = RAIZ / ".mcp.json"
ESQUEMA = {"type": "object", "required": ["valor", "fuente", "interpretacion"],
           "properties": {"valor": {"type": ["number", "null"]}, "unidad": {"type": "string"},
                          "fuente": {"type": "string"}, "interpretacion": {"type": "string"}}}
INSTRUCCION = ("Responde con un solo número en «valor», en la unidad que pide la pregunta; si no puedes obtenerlo, "
               "usa null. En «fuente» di de dónde sale la cifra. En «interpretacion», una o dos oraciones.\n\n")
HERRAMIENTAS_B = "Bash,Read,Glob,Grep,Skill,ToolSearch"
MODOS = {
    "A": {"args": ["--tools", "", "--strict-mcp-config"], "cwd": None},            # cwd: carpeta temporal vacía
    "B": {"args": ["--tools", HERRAMIENTAS_B, "--strict-mcp-config", "--mcp-config", str(MCP_JSON),
                   "--allowedTools", HERRAMIENTAS_B + ",mcp__bcrp"], "cwd": RAIZ},
}


def leer_stream(texto):
    """De la salida stream-json saca las herramientas llamadas y el evento final («result»)."""
    herramientas, final = [], {}
    for linea in texto.splitlines():
        try:
            evento = json.loads(linea)
        except json.JSONDecodeError:
            continue
        if evento.get("type") == "assistant":
            for parte in evento.get("message", {}).get("content", []):
                if parte.get("type") == "tool_use" and parte["name"] != "StructuredOutput":  # así entrega el JSON
                    nombre = parte["name"]
                    if nombre == "Skill":                      # anotar qué skill se usó
                        nombre += ":" + str(parte.get("input", {}).get("skill", "?"))
                    herramientas.append(nombre)
        elif evento.get("type") == "result":
            final = evento
    return herramientas, final


def preguntar(pregunta, modo, modelo, carpeta_vacia):
    cmd = ["claude", "-p", INSTRUCCION + pregunta, "--output-format", "stream-json", "--verbose",
           "--json-schema", json.dumps(ESQUEMA), "--no-session-persistence", "--model", modelo, *MODOS[modo]["args"]]
    t = time.time()
    error = ""
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace",
                              timeout=1200 if modo == "B" else 300, cwd=MODOS[modo]["cwd"] or carpeta_vacia)
        herramientas, final = leer_stream(proc.stdout)
        if proc.returncode != 0 or not final:
            error = (proc.stderr or proc.stdout)[-300:]
    except subprocess.TimeoutExpired:
        herramientas, final, error = [], {}, "tiempo agotado"
    r = final.get("structured_output")
    if r is None:                                              # por si el JSON vino como texto en «result»
        try:
            r = json.loads(final.get("result", ""))
        except (json.JSONDecodeError, TypeError):
            r = {}
    return {"valor": r.get("valor"), "fuente_respuesta": r.get("fuente", ""),
            "interpretacion": r.get("interpretacion", ""),
            "herramientas": ", ".join(dict.fromkeys(herramientas)),   # sin repetidos, en orden de uso
            "n_llamadas": len(herramientas), "segundos": round(time.time() - t, 1),
            "turnos": final.get("num_turns"), "error": error}


def calificar(valor, verdad, tolerancia):
    if valor is None:
        return "no responde"
    return "acierta" if abs(valor - verdad) <= tolerancia else "se equivoca"


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--modos", nargs="+", default=["A", "B"], choices=list(MODOS))
    p.add_argument("--modelo", default="claude-opus-5-5")           # el mismo de la corrida del agente
    p.add_argument("--ids", nargs="+", help="solo estas preguntas (para probar)")
    p.add_argument("--paralelo", type=int, default=4, help="solo modo A; el B va de a una (limpiar.py escribe salidas/)")
    a = p.parse_args()
    if "B" in a.modos and not MCP_JSON.exists():
        raise SystemExit(f"Falta {MCP_JSON}. Conecten el servidor: claude mcp add --scope project bcrp -- uv run mcp/server.py")

    preguntas = pd.read_csv(AQUI / "preguntas.csv")
    if a.ids:
        preguntas = preguntas[preguntas.id.isin(a.ids)]
    print(f"{len(preguntas) * len(a.modos)} llamadas a claude -p con {a.modelo}...")
    respuestas = {}
    with tempfile.TemporaryDirectory() as vacia:
        if "A" in a.modos:
            with ThreadPoolExecutor(a.paralelo) as ex:
                for q, r in zip(preguntas.itertuples(), ex.map(lambda q: preguntar(q.pregunta, "A", a.modelo, vacia),
                                                               preguntas.itertuples())):
                    respuestas[(q.id, "A")] = r
        if "B" in a.modos:
            for q in preguntas.itertuples():
                print(f"  B · {q.id}")
                respuestas[(q.id, "B")] = preguntar(q.pregunta, "B", a.modelo, vacia)

    filas = [{"id": q.id, "fuente": q.fuente, "modo": m, "pregunta": q.pregunta, "verdad": q.verdad,
              "tolerancia": q.tolerancia, **respuestas[(q.id, m)],
              "resultado": calificar(respuestas[(q.id, m)]["valor"], q.verdad, q.tolerancia),
              "criterio_interpretacion": q.criterio_interpretacion if isinstance(q.criterio_interpretacion, str) else "",
              "interpretacion_ok": ""}                                # lo llena una persona en las combinadas
             for q in preguntas.itertuples() for m in a.modos]
    res = pd.DataFrame(filas)
    res.to_csv(AQUI / "resultados.csv", index=False, encoding="utf-8")

    print("\n" + res.pivot(index="id", columns="modo", values="valor").to_string())
    tabla = res.groupby("modo").resultado.value_counts().unstack(fill_value=0)
    tabla["segundos"] = res.groupby("modo").segundos.mean().round(1)
    print("\n" + tabla.to_string())
