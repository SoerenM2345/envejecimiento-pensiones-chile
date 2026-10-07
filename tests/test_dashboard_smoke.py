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
