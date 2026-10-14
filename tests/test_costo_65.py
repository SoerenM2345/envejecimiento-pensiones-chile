"""KPI 2.1: cifras de control del análisis de costo por adulto mayor (Dashboards/components/cost_analysis.py)."""
import sys
from pathlib import Path

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
