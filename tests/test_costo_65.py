"""KPI 2.1: cifras de control del análisis de costo por adulto mayor (Dashboards/components/cost_analysis.py)."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "Dashboards"))
from components.cost_analysis import serie_historica, proyeccion  # noqa: E402


def _csv(nombre):
    return pd.read_csv(ROOT / "Data processed" / f"{nombre}.csv")


@pytest.fixture(scope="module")
def h():
    return serie_historica(_csv("gasto_proteccion_social"), _csv("macro_pib_anual"), _csv("proyeccion_envejecimiento_pais"),
                           _csv("kpi_pc_nacional"), _csv("pgu_pbs_aps_nacional_anual"))


def test_componentes_suman_el_total(h):
    assert (h.pgu + h.pbs_aps + h.resto - h.gasto).abs().max() < 1
    assert (h.resto > 0).all()


def test_cifras_de_control_2025(h):
    u = h.loc[2025]
    assert u.costo_65 / 1e6 == pytest.approx(5.13, abs=0.01)
    assert 100 * u.cobertura == pytest.approx(80, abs=1)
    assert u.razon_necesaria == pytest.approx(6.3, abs=0.1)
    assert u.ocupados_por_65 == pytest.approx(3.3, abs=0.1)
    assert 100 * u.carga_requerida == pytest.approx(19, abs=1)
    assert u.costo_pct_pib_pc == pytest.approx(30, abs=1)


def test_pgu_parte_en_2022(h):
    assert h.loc[2021, "pgu"] == 0 and h.loc[2022, "pgu"] > 0
    assert h.loc[2022, "costo_65"] > h.loc[2021, "costo_65"] and h.loc[2025, "costo_65"] < h.loc[2022, "costo_65"]


def test_proyeccion_escenarios(h):
    pop, par = _csv("proyeccion_envejecimiento_pais"), _csv("kpi_pc_parametros_reforma")
    cte = proyeccion(h, pop, par, 0.02, "constante")
    crece = proyeccion(h, pop, par, 0.02, "crece")
    assert cte.loc[2025, "gasto"] == pytest.approx(h.loc[2025, "gasto"], rel=1e-6)
    assert crece.loc[2050, "gasto"] > cte.loc[2050, "gasto"]
    assert crece.loc[2050, "carga_requerida"] > cte.loc[2050, "carga_requerida"] > 0
    assert proyeccion(h, pop, par, 0.04, "crece").loc[2050, "pct_pib"] < crece.loc[2050, "pct_pib"]
    assert cte.loc[2050, "ocupados_por_65"] < h.loc[2025, "ocupados_por_65"]


def test_indicador_principal_es_consistente(h):
    """Costo por persona 65+ / PIB per cápita (corriente sobre corriente) = % del PIB x población total / población 65+."""
    u = h.loc[2025]
    assert u.costo_pct_pib_pc == pytest.approx(u.pct_pib * u.pob_total / u.pob_65, rel=0.01)
    assert h.costo_pct_pib_pc.iloc[0] == pytest.approx(33.2, abs=0.1)
    assert u.costo_pct_pib_pc == pytest.approx(30.2, abs=0.1)
    assert h.costo_pct_pib_pc.idxmax() == 2023


def test_deflactores_explican_por_que_no_se_compara_con_el_pib_real(h):
    """El PIB real encadenado usa el deflactor del PIB (+68 %), el gasto real usa el IPC (+51 %): no son comparables."""
    ipc = h.defl_ipc.iloc[0] / h.defl_ipc.iloc[-1] - 1
    pib = h.defl_pib.iloc[-1] / h.defl_pib.iloc[0] - 1
    assert ipc == pytest.approx(0.51, abs=0.01) and pib == pytest.approx(0.68, abs=0.01)
    # en precios corrientes el costo por persona 65+ pierde peso frente al PIB per cápita aunque en pesos reales (IPC) suba
    assert h.costo_65.iloc[-1] > h.costo_65.iloc[0] and h.costo_pct_pib_pc.iloc[-1] < h.costo_pct_pib_pc.iloc[0]


def test_base_mediana_o_promedio(h):
    prom = serie_historica(_csv("gasto_proteccion_social"), _csv("macro_pib_anual"), _csv("proyeccion_envejecimiento_pais"),
                           _csv("kpi_pc_nacional"), _csv("pgu_pbs_aps_nacional_anual"), "promedio")
    assert prom.loc[2025, "pago_plano"] == pytest.approx(h.loc[2025, "pago_plano"])          # el pago plano no depende de la base
    assert 100 * h.loc[2025, "carga_requerida"] == pytest.approx(19, abs=1)
    assert 100 * prom.loc[2025, "carga_requerida"] == pytest.approx(14, abs=1)
    assert h.loc[2025, "pago_plano"] == pytest.approx(131_000, abs=1_000)


def test_alineacion_temporal_ocupados_vs_poblacion_65():
    """Ocupados (oct-dic) sobre población 65+ a mitad de año: desfase ~4 meses. Par de sensibilidad: población 65+ interpolada a mediados de noviembre."""
    pop = _csv("proyeccion_envejecimiento_pais").set_index("anio").pob_65_mas
    nac = _csv("kpi_pc_nacional").set_index("anio")
    base = nac.loc[2025, "ocupados_ond"] / pop[2025]
    nov = nac.loc[2025, "ocupados_ond"] / (pop[2025] + 0.375 * (pop[2026] - pop[2025]))
    assert abs(nov / base - 1) < 0.02


def test_proyeccion_parte_del_dato_observado(h):
    pop, par = _csv("proyeccion_envejecimiento_pais"), _csv("kpi_pc_parametros_reforma")
    p = proyeccion(h, pop, par, 0.02, "constante")
    assert p.loc[2025, "costo_pct_pib_pc"] == pytest.approx(h.loc[2025, "costo_pct_pib_pc"], rel=0.01)
    assert p.loc[2025, "carga_requerida"] == pytest.approx(h.loc[2025, "carga_requerida"], rel=1e-6)


# ── Por qué suben los costos (KPI 2.1): descomposición exacta del Pilar ──
@pytest.fixture(scope="module")
def pilar():
    from components.cost_analysis import serie_historica, proyeccion
    P = ROOT / "Data processed"
    L = lambda f: pd.read_csv(P / f)  # noqa: E731
    h = serie_historica(L("gasto_proteccion_social.csv"), L("macro_pib_anual.csv"), L("proyeccion_envejecimiento_pais.csv"), L("kpi_pc_nacional.csv"),
                        L("pgu_pbs_aps_nacional_anual.csv"), "mediana")
    pr = proyeccion(h, L("proyeccion_envejecimiento_pais.csv"), L("kpi_pc_parametros_reforma.csv"), 0.02, "constante", True)
    return h, pr


def test_los_aportes_de_las_tres_piezas_suman_el_cambio_del_costo_del_pilar(pilar):
    from components.cost_analysis import descomponer_pilar
    h, pr = pilar
    for a0, a1 in ((2016, 2021), (2021, 2025), (2016, 2025), (2025, 2050)):
        d = descomponer_pilar(h, pr, a0, a1)
        assert sum(p["aporte"] for p in d["partes"]) == pytest.approx(d["costo1"] - d["costo0"], rel=1e-9)
        assert sum(p["parte"] for p in d["partes"]) == pytest.approx(1.0, rel=1e-9)
        assert d["costo1"] / d["costo0"] == pytest.approx(np.prod([p["razon"] for p in d["partes"]]), rel=1e-9)  # costo = personas × cobertura × monto


def test_el_motor_del_alza_pasa_de_la_politica_a_la_demografia(pilar):
    from components.cost_analysis import descomponer_pilar
    h, pr = pilar
    par = lambda d: {p["clave"]: 100 * p["parte"] for p in d["partes"]}  # noqa: E731
    antes, con_pgu, futuro = par(descomponer_pilar(h, pr, 2016, 2021)), par(descomponer_pilar(h, pr, 2021, 2025)), par(descomponer_pilar(h, pr, 2025, 2050))
    assert max(antes, key=antes.get) == "monto" and antes["monto"] > 55
    assert max(con_pgu, key=con_pgu.get) == "cobertura"
    assert max(futuro, key=futuro.get) == "pob_65" and futuro["pob_65"] > 80 and futuro["cobertura"] == pytest.approx(0, abs=1e-9)  # cobertura constante en el escenario
    todo = par(descomponer_pilar(h, pr, 2016, 2025))
    assert todo["monto"] > todo["cobertura"] > 0 and todo["monto"] > todo["pob_65"]  # el monto y la cobertura crecieron más que la población


def test_indices_del_costo_parten_en_100_y_el_pib_del_escenario_crece_2_por_ciento(pilar):
    from components.cost_analysis import indices_costo
    h, pr = pilar
    pasado, futuro = indices_costo(h, pr, 2016, 2025), indices_costo(h, pr, 2025, 2050)
    assert np.allclose(pasado.iloc[0], 100) and np.allclose(futuro.iloc[0], 100)
    assert pasado.pilar.iloc[-1] > pasado.monto.iloc[-1] > pasado.pob_65.iloc[-1] > pasado.pib.iloc[-1]
    assert futuro.pib.iloc[-1] == pytest.approx(100 * 1.02 ** 25, rel=1e-3)  # sin saltos de base entre el observado y el escenario


def test_pagina_2_1_explica_por_que_suben_los_costos():
    import json
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(str(ROOT / "Dashboards" / "extended_pages" / "objetivo2.py"), default_timeout=180).run()
    assert not at.exception, [e.value for e in at.exception]
    titulos = lambda: [json.loads(el.proto.spec).get("layout", {}).get("title", {}).get("text", "") for el in at.get("plotly_chart")]  # noqa: E731
    assert any(t.startswith("Hasta 2025 el costo del Pilar se multiplicó") for t in titulos())
    assert any(t.startswith("El alza del costo cambia de motor") for t in titulos())
    at.radio(key="c21_periodo").set_value("2025-2050 (escenario)").run()
    assert not at.exception and any("se multiplicaría" in t for t in titulos())
    sub = [m.value for m in at.markdown if m.value.startswith("##### ")]
    assert sub[:3] == ["##### 1. ¿Qué sube más rápido?", "##### 2. ¿De dónde viene el aumento?", "##### 3. Las razones una por una (resumen)"]
    assert any(t.value.index.name == "Posible razón" for t in at.get("table"))


# ---------------------------------------------------------------- costo total del Estado en la vejez (Pilar + «Edad avanzada»)
def _total(h, resto="no", con_fapp=True):
    from components.cost_analysis import gasto_total_vejez
    from components.financiamiento import proyeccion_carga
    carga = proyeccion_carga(h, _csv("pgu_pbs_aps_nacional_anual"), _csv("macro_pib_anual"), _csv("proyeccion_envejecimiento_pais"),
                             _csv("kpi_pc_parametros_reforma"), _csv("fapp_aporte_fiscal"), 0.02, True, con_fapp, 2050)
    return gasto_total_vejez(h, carga, _csv("pgu_pbs_aps_nacional_anual"), _csv("macro_pib_anual"), _csv("kpi_pc_nacional"), resto), carga


def test_costo_total_cuadra_con_el_pilar_y_edad_avanzada(h):
    """Chequeo a: la base de la descomposición (vejez, 6,25 billones) + invalidez = el Pilar total del KPI 2.2 (7,04 billones; 2,07 % del PIB)."""
    d, carga = _total(h)
    u = d.loc[2025]
    assert u.pilar_vejez / 1e12 == pytest.approx(6.25, abs=0.01)
    assert (u.pilar_vejez + u.pilar_invalidez) / 1e12 == pytest.approx(7.04, abs=0.01)
    assert u.pilar_pct == pytest.approx(2.07, abs=0.005) and u.total_pct == pytest.approx(4.39, abs=0.005)
    o = d[~d.escenario]
    assert ((o.pilar_vejez + o.resto - o.total).abs() < 1).all()                 # observado: vejez + resto = «Edad avanzada»
    assert ((o.pilar_vejez_pct + o.resto_pct - o.total_pct).abs() < 1e-9).all()
    e = d[d.escenario]
    assert np.allclose(e.pilar_pct, carga.loc[e.index, "pilar_pct_pib"]) and np.allclose(e.carga_pct, carga.loc[e.index, "carga_pct_pib"])
    assert e.resto.isna().all()                                                  # el resto no se proyecta salvo supuesto explícito
    d2, _ = _total(h, "constante")
    assert (d2[d2.escenario].resto == h.loc[2025].resto).all()


def test_aumentos_de_la_descomposicion_y_producto_del_indice(h):
    """Chequeo b: +1,8 y +3,0 billones (2016-2021, 2021-2025) y costo ×4,4 = monto ×2,1 × personas 65+ ×1,44 × cobertura ×1,47."""
    from components.cost_analysis import descomponer_pilar, indices_costo
    pr = proyeccion(h, _csv("proyeccion_envejecimiento_pais"), _csv("kpi_pc_parametros_reforma"), 0.02, "constante", True)
    a = descomponer_pilar(h, pr, 2016, 2021)
    b = descomponer_pilar(h, pr, 2021, 2025)
    assert (a["costo1"] - a["costo0"]) / 1e12 == pytest.approx(1.84, abs=0.01)
    assert (b["costo1"] - b["costo0"]) / 1e12 == pytest.approx(3.00, abs=0.01)
    i = indices_costo(h, pr, 2016, 2025).iloc[-1] / 100
    assert i.pilar == pytest.approx(i.monto * i.pob_65 * i.cobertura, rel=1e-9)
    assert (round(i.pilar, 1), round(i.monto, 1), round(i.pob_65, 2), round(100 * h.loc[2016].cobertura), round(100 * h.loc[2025].cobertura)) == (4.4, 2.1, 1.44, 55, 80)


def test_pagina_2_1_define_las_tres_piezas_antes_de_los_graficos(pilar):
    import json
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(str(ROOT / "Dashboards" / "extended_pages" / "objetivo2.py"), default_timeout=180).run()
    assert not at.exception, [e.value for e in at.exception]
    assert [e.label for e in at.expander if e.label.startswith("Definiciones y fórmulas")] == ["Definiciones y fórmulas: qué es cada pieza del costo"]
    formulas = [l.value for l in at.get("latex")]
    assert any("underbrace" in f and "Alcance" in f and "Monto por beneficio" in f for f in formulas)
    ejemplo = next(t.value for t in at.get("table") if t.value.index.name == "Pieza")
    assert ejemplo.index[-1].startswith("Costo del Pilar")
    veces = [float(v.replace(",", ".")) for v in ejemplo["Veces"]]
    assert veces[0] * veces[1] * veces[2] == pytest.approx(veces[3], rel=0.02)  # las tres piezas multiplicadas dan el alza del costo
    confusiones = next(t.value for t in at.get("table") if t.value.index.name == "Término parecido")
    assert any("KPI 1.1" in i for i in confusiones.index) and any("KPI 2.2" in i for i in confusiones.index)
    assert not any("cobertura" in n.lower() for n in ejemplo.index)  # «alcance»: «cobertura» es del KPI 1.1
    assert not any("$" in str(v) for v in confusiones.to_numpy().ravel())  # st.table lee markdown: dos «$» abren una fórmula; van como entidad
    textos = [m.value for m in at.markdown]
    primero_grafico = next(i for i, t in enumerate(textos) if t.startswith("##### 1. ¿Qué sube más rápido?"))
    assert any(t.startswith("**1. Personas de 65+**") for t in textos[:primero_grafico])  # las definiciones van antes
