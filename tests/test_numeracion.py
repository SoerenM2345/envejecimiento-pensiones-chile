"""Numeración de gráficos y tablas (Dashboards/components/numeracion.py): 1.3.1, 1.3.2, ...
Ejecutar desde la raíz del proyecto:  python -I -m pytest tests/test_numeracion.py -q"""
import ast
import sys
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

DASH = Path(__file__).resolve().parent.parent / "Dashboards"
sys.path.insert(0, str(DASH))

from components.numeracion import ORDEN, numero  # noqa: E402

PAGINAS = {False: ["final_pages/objetivo1.py", "final_pages/objetivo2.py", "final_pages/problema.py"],
           True: ["extended_pages/objetivo1.py", "extended_pages/objetivo2.py", "extended_pages/problema.py"]}
COMPONENTES = sorted(p.relative_to(DASH).as_posix() for p in (DASH / "components").glob("*.py") if p.name not in ("charts.py", "numeracion.py"))
LLAMADAS_GRAFICO = {"mostrar", "_g21", "_grafico"}   # envoltorios que dibujan un gráfico: todos deben recibir num=


def _arbol(rel: str) -> ast.AST:
    return ast.parse((DASH / rel).read_text(encoding="utf-8"), rel)


def _nombre(llamada: ast.Call) -> str:
    f = llamada.func
    return f.id if isinstance(f, ast.Name) else f.attr if isinstance(f, ast.Attribute) else ""


def _claves_en(rel: str) -> set:
    """Claves de numeración que el archivo usa: textos «1.1/mapa» (con o sin sufijo «:a»), también dentro de f-strings y diccionarios."""
    claves = set()
    for n in ast.walk(_arbol(rel)):
        if isinstance(n, ast.Constant) and isinstance(n.value, str) and "/" in n.value:
            ref = n.value.partition(":")[0]
            kpi, _, nombre = ref.partition("/")
            if kpi in ORDEN and nombre and " " not in ref:
                claves.add(ref)
    return claves


@pytest.mark.parametrize("extendida", [False, True])
def test_numeros_unicos_y_sin_huecos(extendida):
    for kpi, claves in ORDEN.items():
        visibles = [c.lstrip("+") for c in claves if extendida or not c.startswith("+")]
        assert len(visibles) == len(set(visibles)), f"claves repetidas en {kpi}"
        nums = [numero(f"{kpi}/{c}", extendida) for c in visibles]
        assert nums == [f"{kpi}.{i}" for i in range(1, len(visibles) + 1)]


def test_la_version_final_no_cuenta_lo_exclusivo_de_la_extendida():
    assert numero("1.1/matriz", False) != numero("1.1/matriz", True)  # las páginas extendidas tienen gráficos extra antes de la matriz
    assert numero("1.1/sexo", False) == numero("1.1/sexo", True)  # lo exclusivo de la extendida se numera siempre con la lista extendida
    with pytest.raises(ValueError):
        numero("1.1/no_existe", True)
    assert numero("1.1/composicion_region:b", True).endswith("b")


@pytest.mark.parametrize("extendida", [False, True])
def test_cada_grafico_lleva_numero(extendida):
    """Todo dibujo de un gráfico pasa num=... (así ninguno queda sin número)."""
    for rel in PAGINAS[extendida] + COMPONENTES:
        for n in ast.walk(_arbol(rel)):
            if isinstance(n, ast.Call) and _nombre(n) in LLAMADAS_GRAFICO:
                assert any(k.arg == "num" for k in n.keywords), f"{rel}:{n.lineno}: {_nombre(n)}(...) sin num="


@pytest.mark.parametrize("extendida", [False, True])
def test_claves_usadas_y_registradas_coinciden(extendida):
    """Cada clave usada está en ORDEN, la versión final no usa las exclusivas de la extendida y todo lo registrado se usa en alguna parte."""
    registradas = {f"{kpi}/{c.lstrip('+')}" for kpi, cs in ORDEN.items() for c in cs if extendida or not c.startswith("+")}
    usadas = set().union(*(_claves_en(rel) for rel in PAGINAS[extendida] + COMPONENTES))
    assert usadas <= registradas, f"claves usadas que no están en ORDEN (o son solo de la extendida): {sorted(usadas - registradas)}"
    assert registradas <= usadas, f"claves de ORDEN que ninguna página usa: {sorted(registradas - usadas)}"


@pytest.mark.parametrize("pagina", [p for ps in PAGINAS.values() for p in ps])
def test_paginas_con_numeros_corren(pagina):
    at = AppTest.from_file(str(DASH / pagina), default_timeout=90)
    at.session_state["_nav_active"] = True
    at.session_state["ext_mode"] = pagina.startswith("extended")
    at.run()
    assert not at.exception, [e.value for e in at.exception]
    numeros = [m.value for m in at.markdown if "border-radius:999px" in m.value]
    assert numeros, "la página no dibuja ningún número"
    textos = [n.split(">")[-2].split("<")[0] for n in numeros]
    assert len(textos) == len(set(textos)), f"números repetidos en pantalla: {sorted(t for t in textos if textos.count(t) > 1)}"
