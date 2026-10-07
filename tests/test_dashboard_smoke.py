"""Smoke tests: cada página del dashboard corre sin excepciones, y el entry point arma ambos modos.
Ejecutar desde la raíz del proyecto:  python -I -m pytest tests -q   (venv: Data raw/.venv)"""
import sys
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

DASH = Path(__file__).resolve().parent.parent / "Dashboards"
sys.path.insert(0, str(DASH))  # para importar utils / components en los tests de lógica

FINAL_PAGES = sorted(p.relative_to(DASH).as_posix() for p in (DASH / "final_pages").glob("*.py"))
DEV_PAGES = sorted(p.relative_to(DASH).as_posix() for p in (DASH / "pages").glob("*.py"))


def run_page(rel: str) -> AppTest:
    at = AppTest.from_file(str(DASH / rel), default_timeout=60)
    at.session_state["_nav_active"] = True  # como bajo st.navigation: page_config() queda en no-op
    return at.run()


@pytest.mark.parametrize("page", FINAL_PAGES + DEV_PAGES)
def test_page_runs_without_exception(page):
    at = run_page(page)
    assert not at.exception, [e.value for e in at.exception]


@pytest.mark.parametrize("mode", ["final", "dev"])
def test_entrypoint_builds_navigation(mode):
    at = AppTest.from_file(str(DASH / "Inicio.py"), default_timeout=60)
    at.session_state["dev_mode"] = mode == "dev"
    at.run()
    assert not at.exception, [e.value for e in at.exception]


def test_final_mode_has_no_dev_pages():
    from utils import MODES
    assert MODES == ("final", "dev")
    assert len(FINAL_PAGES) == 5 and len(DEV_PAGES) >= 8


def test_regression_national_support_ratio():
    """Valores que la presentación ya usa: no deben cambiar sin querer."""
    import pandas as pd
    pres = pd.read_csv(DASH.parent / "Data processed" / "kpi_presion_previsional_region.csv")
    nuble = pres[pres.region_nombre == "Ñuble"].iloc[0]
    assert round(nuble.cobertura_previsional_pct, 2) == 38.73
    assert round(nuble.razon_soporte_previsional, 2) == 1.54
    assert len(pres) == 16


def test_kpi_2_tables():
    """KPI 2.1 / 2.2 / 2.3: las tablas existen y reproducen cifras verificadas contra fuentes oficiales."""
    import pandas as pd
    dp = DASH.parent / "Data processed"
    g = pd.read_csv(dp / "gasto_proteccion_social.csv")
    pib = pd.read_csv(dp / "macro_pib_anual.csv").set_index("anio")
    ea = g[g.categoria == "Edad avanzada"].set_index("anio")
    # % del PIB propio == % del PIB publicado por DIPRES, todos los años
    propio = 100 * ea.gasto_corriente_mm / pib.pib_corriente_mm.reindex(ea.index)
    assert (propio - ea.pct_pib).abs().max() < 0.01
    pil = pd.read_csv(dp / "pgu_pbs_aps_nacional_anual.csv")
    tot = pil[(pil.tipo_beneficio == "Total") & (pil.anio == 2024)].monto_nominal_mm.iloc[0]
    assert abs(tot - 6376416.89) < 1  # resumen anual publicado 2024
    pob = pd.read_csv(dp / "pobreza_65_region.csv")
    assert len(pob) == 17 and (pob.region_id == 0).sum() == 1
    assert pob.pct_pobreza_65.between(0, 40).all() and (pob.ic95_inf <= pob.pct_pobreza_65).all()
    assert pob[pob.region_id == 0].pct_pobreza_65.iloc[0] < pob[pob.region_id == 0].pct_pobreza_menores_65.iloc[0]
