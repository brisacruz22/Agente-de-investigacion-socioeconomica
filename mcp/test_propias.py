"""Dos pruebas propias. Las 8 originales de la sesión 04 están en test_server.py, sin cambios.

    uv run pytest                 # desde la raíz del repo; meta: 10 passed
"""
import asyncio

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError

from server import mcp


def llamar(herramienta, **args):
    async def f():
        async with Client(mcp) as c:
            return (await c.call_tool(herramienta, args)).data
    return asyncio.run(f())


def test_metadatos_da_unidad_fuente_y_cobertura():
    """metadatos saca la unidad del nombre cuando el catálogo la deja vacía y reconoce el departamento."""
    m = llamar("metadatos", codigo="RD15548DA")                  # Oro - Cajamarca, anual
    assert m["unidad"] == "grs.f"
    assert m["fuente_original"] == "Ministerio de Energía y Minas"
    assert (m["departamento"], m["ccdd"]) == ("Cajamarca", "06")
    assert m["inicio"] == "2001" and m["fin"] >= "2025"
    with pytest.raises(ToolError, match="XX999"):
        llamar("metadatos", codigo="XX999")


def test_comparar_departamentos_trae_los_25_con_su_codigo_inei():
    """Las exportaciones mineras de 2022 existen para los 25 departamentos y vuelven ordenadas, con ccdd."""
    r = llamar("comparar_departamentos", texto="exportaciones tradicionales mineros", periodo="2022")
    assert r["n"] + len(r["faltantes"]) == 25
    assert r["n"] >= 20
    ccdd = [d["ccdd"] for d in r["datos"]]
    assert len(set(ccdd)) == len(ccdd) and all(len(c) == 2 for c in ccdd)
    valores = [d["valor"] for d in r["datos"]]
    assert valores == sorted(valores, reverse=True)
    assert all(d["fuente"].startswith("https://estadisticas.bcrp.gob.pe") for d in r["datos"])
