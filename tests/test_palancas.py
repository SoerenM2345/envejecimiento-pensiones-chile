"""KPI 1.1, cierre: palancas de las administradoras frente a la cobertura estancada (Scripts/31). Ejecutar desde la raíz:  python -I -m pytest tests -q"""
import sys
from pathlib import Path

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parent.parent
DP = ROOT / "Data processed"
sys.path.insert(0, str(ROOT / "Dashboards"))  # las páginas importan utils y components


def test_palancas_usan_las_personas_de_la_composicion_y_marcan_el_juicio():
    d = pd.read_csv(DP / "kpi_cobertura_palancas.csv")
    g = pd.read_csv(DP / "kpi_cobertura_composicion.csv").set_index("grupo").personas
    assert d.orden.tolist() == list(range(1, len(d) + 1)) and d.palanca.is_unique
    assert set(d.efecto) == {"Suma personas", "Protege lo que ya hay"} and set(d.alcance_afp) <= {"Directo", "Indirecto", "Ninguno"}
    assert set(d.respaldo) <= {"Ley", "Propuesta del gremio", "Juicio del equipo"} and d.fuente.notna().all()
    por = d.set_index("palanca").personas
    assert por["Formalizar el empleo"] == pytest.approx(g["No cotizan: ocupados informales"], abs=1)
    assert por["Cobrar las cotizaciones declaradas y no pagadas"] == pytest.approx(g["No cotizan: ocupados formales fuera de la estadística"], abs=1)
    cot = g["Cotizan: dependientes"] + g["Cotizan: independientes y voluntarios"]
    assert por["Avisar y cubrir las lagunas"] == pytest.approx(cot, abs=1)
    # solo la cobranza depende de la administradora y suma personas; las más grandes pasan por el Estado y el mercado laboral
    directas = d[(d.alcance_afp == "Directo") & (d.efecto == "Suma personas")]
    assert directas.palanca.tolist() == ["Cobrar las cotizaciones declaradas y no pagadas"]
    assert d[d.efecto == "Suma personas"].sort_values("personas").iloc[0].palanca == directas.palanca.iloc[0]  # y es la más pequeña de las que suman


@pytest.mark.parametrize("pagina", ["final_pages", "extended_pages"])
def test_las_paginas_muestran_las_palancas(pagina):
    at = AppTest.from_file(str(ROOT / "Dashboards" / pagina / "objetivo1.py"), default_timeout=180)
    at.session_state["_nav_active"] = True
    at.run()
    assert not at.exception, [e.value for e in at.exception]
    assert any("¿Qué puede hacer una administradora y qué le corresponde al Estado?" in m.value for m in at.markdown)
