"""KPI 1.1, causas: datos de la ENE, descomposición y contraste con la AAFP (Scripts/25, docs/EXPLORACION_COBERTURA.md).
Ejecutar desde la raíz del proyecto:  python -I -m pytest tests -q   (venv: Data raw/.venv)"""
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parent.parent
DP = ROOT / "Data processed"
sys.path.insert(0, str(ROOT / "Dashboards"))


@pytest.fixture(scope="module")
def s25():
    spec = importlib.util.spec_from_file_location("s25", ROOT / "Scripts" / "25_explorar_causas.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_se_reconocen_las_siete_series_regionales_de_la_ene(s25):
    claves = {r[0] for r in (s25.serie_regional(f) for f in sorted(s25.ENE_DIR.glob("*.xls"))) if r}
    assert claves == {"ocupados", "desocupados", "informales", "tasa_informal", "tasa_sector_informal", "tasa_informal_sin_agro",
                      "tasa_parcial_involuntario"}


def test_ene_reproduce_las_cifras_de_la_aafp_de_diciembre_2019():
    """El trimestre nov-ene es el «diciembre» del INE: los ocupados, la desocupación y la informalidad de 2019 coinciden con el anexo del estudio."""
    c = pd.read_csv(DP / "kpi_cobertura_contraste_aafp.csv")
    assert len(c) == 16
    assert c.dif_ocupados_pct.abs().max() < 0.01
    assert (c.desocupacion_ine_2019 - c.desocupacion_aafp_2019).abs().max() < 0.05
    assert (c.informalidad_ine_2019 - c.informalidad_aafp_2019).abs().max() < 0.05


def test_cotizantes_sobre_ocupados_es_la_misma_cifra_que_la_aafp():
    """Los cotizantes de diciembre de la Superintendencia son los «cotizantes del mes» del estudio: la cobertura sobre ocupados 2019 y 2024 coincide."""
    c = pd.read_csv(DP / "kpi_cobertura_contraste_aafp.csv")
    assert (c.cot_sobre_ocupados_2019 - c.cobertura_ocupados_aafp_2019).abs().max() < 0.06
    assert (c.cot_sobre_ocupados_2024_con_aafp - c.cobertura_ocupados_aafp_2024).abs().max() < 0.06


def test_los_tres_factores_reproducen_la_cobertura():
    f = pd.read_csv(DP / "kpi_cobertura_factores_anual.csv")
    prod = 100 * f.participacion * f.empleo * f.cotizacion
    assert np.allclose(prod, f.cobertura_pct)
    assert f.anio.min() == 2010 and f.anio.max() == 2023
    assert not ((f.anio < 2018) & f.territorio_id.isin([8, 16])).any()  # antes de 2018 solo vale Biobío y Ñuble juntas


def test_aportes_suman_exacto_la_diferencia_de_cobertura():
    d = pd.read_csv(DP / "kpi_cobertura_descomposicion.csv")
    f = pd.read_csv(DP / "kpi_cobertura_factores_anual.csv").set_index(["territorio_id", "anio"]).cobertura_pct
    for (tid, comp), g in d.groupby(["territorio_id", "comparacion"]):
        if comp.startswith("Nivel"):
            esperado = f[(tid, 2023)] - f[(0, 2023)]
        else:
            a0, a1 = int(comp[7:11]), int(comp[12:16])
            esperado = f[(tid, a1)] - f[(tid, a0)]
        assert g.aporte_pp.sum() == pytest.approx(esperado, abs=2e-3), (tid, comp)


def test_las_regiones_prioritarias_pierden_sobre_todo_por_cotizacion_de_los_ocupados():
    d = pd.read_csv(DP / "kpi_cobertura_descomposicion.csv")
    n = d[(d.comparacion == "Nivel frente a Chile en 2023") & d.territorio_id.isin([9, 16])].pivot(index="territorio_id", columns="factor", values="aporte_pp")
    assert (n.idxmin(axis=1) == "cotizacion").all() and n.cotizacion.max() < -5  # La Araucanía y Ñuble


def test_prueba_de_asignacion_regional_usa_la_metropolitana():
    t = pd.read_csv(DP / "kpi_cobertura_test_asignacion.csv")
    assert len(t) == 5 and (t.cotizantes_pct > t.ocupados_ene_pct).all()
    assert t.cotizantes_pct.between(40, 50).all() and t.pob_15_64_pct.between(38, 46).all()


def test_pib_regional_tiene_15_regiones_sin_magallanes():
    pib = pd.read_csv(DP / "pib_regional_anual.csv")
    assert pib.territorio_id.nunique() == 15 and 12 not in set(pib.territorio_id)
    assert pib.anio.min() == 2013 and pib.anio.max() == 2025


def test_regiones_trae_chile_y_las_columnas_de_la_ene():
    r = pd.read_csv(DP / "kpi_cobertura_regiones.csv").set_index("region_id").sort_index()
    for c in ("desocupacion_ene", "informalidad_ene", "participacion_mujeres_censo", "peso_cotizantes_pct"):
        assert c in r and r.loc[1:16, c].notna().all()
    assert r.loc[0, "informalidad_ene"] == pytest.approx(27.55, abs=0.05)
    assert r.loc[1:16, "peso_cotizantes_pct"].sum() == pytest.approx(100, abs=0.01)


def test_pagina_muestra_tendencia_descomposicion_y_cambia_de_ventana():
    import re
    from test_dashboard_smoke import SIGLAS_PROHIBIDAS
    at = AppTest.from_file(str(ROOT / "Dashboards" / "final_pages" / "objetivo1.py"), default_timeout=180).run()
    assert not at.exception, [e.value for e in at.exception]
    specs = lambda: [json.loads(el.proto.spec) for el in at.get("plotly_chart")]  # noqa: E731
    titulos = lambda: [s.get("layout", {}).get("title", {}).get("text", "") for s in specs()]  # noqa: E731
    vistos = list(titulos())
    assert any(x.startswith("Desde 2019 la cobertura de Chile") for x in vistos)
    i_desc = next(i for i, x in enumerate(vistos) if "la brecha con Chile viene sobre todo de" in x)
    i_fac = next(i for i, x in enumerate(vistos) if x.startswith("Las regiones con más"))
    assert i_desc < i_fac  # primero la aritmética, después las asociaciones
    at.radio(key="cob_ventana").set_value("Desde 2002, con regiones fusionadas").run()
    assert any(x.startswith("La cobertura de Chile subió de 30%") for x in titulos())
    vistos += titulos()
    at.checkbox(key="cob_sin_ajuste").set_value(True).run()
    assert not at.exception and any("◆ = Censo 2024" in x for x in titulos())
    assert any(t.get("type") == "scatter" and t.get("marker", {}).get("symbol") == "diamond" for s in specs() for t in s["data"])  # el Censo, aparte
    tend = next(s for s in specs() if s["layout"].get("title", {}).get("text", "").startswith("La cobertura de Chile subió de 28%"))
    assert tend["layout"]["yaxis"]["range"][0] == 0  # eje desde 0
    assert len(tend["layout"]["shapes"]) >= 13  # franja 2020-2021 en cada panel
    vistos += titulos()
    at.radio(key="cob_desc_comp").set_value("Cambio 2019-2023").run()
    assert not at.exception and any(x.startswith("Entre 2019 y 2023") for x in titulos())
    vistos += titulos()
    for t in vistos:  # pauta de la clase: títulos sin siglas, también en las variantes
        assert not re.search(SIGLAS_PROHIBIDAS, re.sub(r"<[^>]+>", " ", t)), t


def test_el_selector_de_criterio_cambia_las_regiones_analizadas():
    at = AppTest.from_file(str(ROOT / "Dashboards" / "final_pages" / "objetivo1.py"), default_timeout=180).run()
    assert not at.exception, [e.value for e in at.exception]

    def regiones_descomposicion():
        for el in at.get("plotly_chart"):
            sp = json.loads(el.proto.spec)
            if "la brecha con Chile viene sobre todo de" in sp.get("layout", {}).get("title", {}).get("text", ""):
                return set(sp["data"][0]["y"])

    assert regiones_descomposicion() == {"La Araucanía", "Valparaíso", "Biobío", "Los Ríos", "Los Lagos"}  # recomendada
    at.radio(key="cob_criterio").set_value("Mayor peso en los cotizantes").run()
    assert not at.exception and regiones_descomposicion() == {"Metropolitana", "Valparaíso", "Biobío", "Maule", "O'Higgins"}
    at.radio(key="cob_criterio").set_value("Mayor brecha de cotizantes").run()
    assert not at.exception and regiones_descomposicion() == {"La Araucanía", "Valparaíso", "Biobío", "Coquimbo", "Ñuble"}


def _vals(a):
    """Plotly serializa los arreglos numéricos en binario ({dtype, bdata}); aquí se vuelven lista."""
    import base64
    if isinstance(a, dict) and "bdata" in a:
        return np.frombuffer(base64.b64decode(a["bdata"]), dtype=np.dtype(a["dtype"])).tolist()
    return list(a)


def _spec_con_titulo(at, fragmento):
    for el in at.get("plotly_chart"):
        sp = json.loads(el.proto.spec)
        if fragmento in sp.get("layout", {}).get("title", {}).get("text", ""):
            return sp


def test_barras_del_cambio_desde_2022_marcan_las_5_prioritarias():
    at = AppTest.from_file(str(ROOT / "Dashboards" / "final_pages" / "objetivo1.py"), default_timeout=180).run()
    assert not at.exception, [e.value for e in at.exception]
    sp = _spec_con_titulo(at, "perdió la mayor cobertura desde 2022")
    barra = sp["data"][0]
    assert len(barra["y"]) == 16 and barra["marker"]["color"].count("#eb6834") == 5  # las 5 prioritarias, en naranja
    assert barra["y"][0] == "Arica y Parinacota" or min(barra["x"]) == barra["x"][list(barra["y"]).index("Arica y Parinacota")]
    assert any(s.get("x0") is not None and s["x0"] == s["x1"] for s in sp["layout"]["shapes"])  # línea punteada de Chile
    # al elegir otra lista cambian los colores pero siguen siendo 5
    at.radio(key="cob_criterio").set_value("Mayor peso en los cotizantes").run()
    assert _spec_con_titulo(at, "perdió la mayor cobertura desde 2022")["data"][0]["marker"]["color"].count("#eb6834") == 5


def test_grafico_largo_tiene_tres_lineas_desde_2002():
    at = AppTest.from_file(str(ROOT / "Dashboards" / "final_pages" / "objetivo1.py"), default_timeout=180).run()
    sp = _spec_con_titulo(at, "La distancia entre Magallanes y La Araucanía")
    lineas = [t for t in sp["data"] if t.get("mode") == "lines"]
    assert len(lineas) == 3 and all(_vals(t["x"])[0] == 2002 and _vals(t["x"])[-1] == 2025 for t in lineas)
    assert sp["layout"]["yaxis"]["range"][0] == 0
    at.radio(key="cob_largo_modo").set_value("Mayor caída desde 2022").run()
    assert _spec_con_titulo(at, "Magallanes y Valparaíso") is not None  # la prioritaria que más cayó


def test_descomposicion_permite_ver_las_16_regiones_con_las_5_marcadas():
    at = AppTest.from_file(str(ROOT / "Dashboards" / "final_pages" / "objetivo1.py"), default_timeout=180).run()
    clave = "la brecha con Chile viene sobre todo de"
    assert len(_spec_con_titulo(at, clave)["data"][0]["y"]) == 5
    at.radio(key="cob_desc_alcance").set_value("Las 16 regiones (las prioritarias en naranja)").run()
    assert not at.exception, [e.value for e in at.exception]
    sp = _spec_con_titulo(at, clave)
    barras = [t for t in sp["data"] if t["type"] == "bar"]
    assert len(barras) == 4 and all(len(b["y"]) == 16 for b in barras) and barras[0]["marker"]["color"].count("#eb6834") == 5
    assert len([s for s in sp["layout"]["shapes"] if s["x0"] == s["x1"]]) == 4  # la línea de Chile en cada panel
    total = _vals(barras[3]["x"])
    peor = barras[3]["y"][total.index(min(total))]
    assert sp["layout"]["yaxis"]["categoryarray"][-1] == peor  # la primera categoría va abajo: la que más pierde queda arriba


def test_escenarios_fijos_del_kpi_1_2():
    import sys
    sys.path.insert(0, str(ROOT / "Dashboards"))
    from components import critical_point as cp
    n, proy, par = (pd.read_csv(DP / f) for f in ("kpi_pc_nacional.csv", "proyeccion_envejecimiento_pais.csv", "kpi_pc_parametros_reforma.csv"))
    # el parámetro nuevo no cambia nada por defecto: la base sigue en 2038
    assert cp.punto_critico(cp.serie_pais(n, proy, par, cp.Escenario()))["anio"] == 2038
    esc = pd.read_csv(DP / "kpi_pc_escenarios_fijos.csv").set_index("clave")
    assert list(esc.index) == ["tope_10", "tope_11", "tope_12", "cobertura_cae", "sin_informalidad", "mitad_informalidad"]
    assert list(esc.carga_max[:3]) == [0.10, 0.11, 0.12]
    assert esc.loc["cobertura_cae", "cobertura_2050"] < 1 and esc.loc["cobertura_cae", "cobertura_salto"] == 1
    salto = esc.loc["sin_informalidad", "cobertura_salto"]
    assert 1.3 < salto < 1.5 and esc.loc["mitad_informalidad", "cobertura_salto"] == pytest.approx(1 + (salto - 1) / 2, abs=1e-5)
    anios = {}
    for k, r in esc.iterrows():
        d = cp.serie_pais(n, proy, par, cp.Escenario(carga_max=r.carga_max, cobertura_2050=r.cobertura_2050, cobertura_salto=r.cobertura_salto))
        anios[k] = cp.punto_critico(d)["anio"]
    assert anios == {"tope_10": 2038, "tope_11": 2044, "tope_12": 2048, "cobertura_cae": 2036, "sin_informalidad": 2055, "mitad_informalidad": 2048}


def test_pagina_muestra_los_escenarios_fijos_sin_cambiar_el_simulador():
    at = AppTest.from_file(str(ROOT / "Dashboards" / "final_pages" / "objetivo1.py"), default_timeout=180).run()
    assert not at.exception, [e.value for e in at.exception]
    sp = _spec_con_titulo(at, "El punto crítico va de 2036 a 2055")
    assert sp is not None
    for panel in ("xaxis", "xaxis2"):
        assert sp["layout"][panel]["range"][0] == 2025
    assert sp["layout"]["yaxis"]["range"][0] == 0
    # el simulador de arriba sigue igual: sus deslizadores y su resultado base
    assert at.slider(key="pc_carga").value == 10.0 and at.slider(key="pc_cobertura").value == 100
