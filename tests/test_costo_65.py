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
