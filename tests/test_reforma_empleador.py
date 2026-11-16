"""Reforma de la cotización del empleador (Ley 21.735): destinos por escalón (KPI 1.3), efecto en el empleo formal (variantes del KPI 1.3 y escenarios del KPI 1.2).
Ejecutar desde la raíz del proyecto:  python -I -m pytest tests -q   (venv: Data raw/.venv)"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parent.parent
DASH = ROOT / "Dashboards"
DP = ROOT / "Data processed"
sys.path.insert(0, str(DASH))

from components import critical_point as cp  # noqa: E402

CFG = yaml.safe_load((ROOT / "config" / "escenarios.yaml").read_text(encoding="utf-8"))


def _textos(at: AppTest) -> str:
    return "\n".join(m.value for m in at.markdown)


def test_destinos_del_empleador_cuadran_con_la_tabla_1_de_la_nota_tecnica():
    d = pd.read_csv(DP / "kpi_reforma_empleador.csv")
    assert d.anio.tolist() == [2024] + list(range(2025, 2034)) + list(range(2045, 2055))
    assert np.allclose(d.cuenta_individual + d.seguro_social_sin_sis + d.sis, d.total_empleador)
    antes, fin, largo = d.iloc[0], d[d.anio == 2033].iloc[0], d[d.anio == 2054].iloc[0]
    assert antes.total_empleador == pytest.approx(0.0188) and antes.cuenta_individual == 0
    assert fin.total_empleador == pytest.approx(0.085) and fin.cuenta_individual == pytest.approx(0.045)
    assert fin.seguro_social_sin_sis + fin.sis == pytest.approx(0.040)  # 4,5 % a la cuenta individual y 4 % al Seguro Social
    assert fin.aumento_vs_antes == pytest.approx(0.0662)  # 8,5 % − 1,88 %
    assert largo.cuenta_individual == pytest.approx(0.06) and largo.total_empleador == pytest.approx(0.085)
    hoy = d[d.anio == 2026].iloc[0]  # agosto 2026 a julio 2027: 3,5 % de los cuales solo 0,1 punto va a la cuenta individual
    assert hoy.total_empleador == pytest.approx(0.035) and hoy.cuenta_individual == pytest.approx(0.001)


def test_factor_de_empleo_parte_en_uno_y_se_estabiliza_en_2033():
    f = pd.read_csv(DP / "kpi_reforma_empleo_factor.csv")
    d = pd.read_csv(DP / "kpi_reforma_empleador.csv").set_index("anio")
    dep = 0.992  # parte de dependientes entre los cotizantes de dic-2024 (cotizantes_por_tipo_sexo.csv)
    for clave, e in zip(("reforma_baja", "reforma_alta"), sorted(CFG["reforma_empleador"]["elasticidad_empleo_formal"]["variantes"], key=abs)):
        s = f[f.escenario == clave].set_index("anio")
        assert s.loc[2025, "factor_vs_2025"] == 1.0 and s.elasticidad.eq(e).all()
        assert s.factor_vs_2025.is_monotonic_decreasing and s.factor_vs_2025.iloc[-1] < 1
        assert s.loc[2033:, "factor_vs_2025"].nunique() == 1  # desde 2033 el costo ya no sube
        esperado = (1 + e * d.loc[2033, "aumento_vs_antes"] * dep) / (1 + e * d.loc[2025, "aumento_vs_antes"] * dep)
        assert s.loc[2033, "factor_vs_2025"] == pytest.approx(esperado, abs=2e-3)
    alta, baja = (f[(f.escenario == c) & (f.anio == 2033)].factor_vs_2025.iloc[0] for c in ("reforma_alta", "reforma_baja"))
    assert alta < baja < 1


def test_variantes_de_la_reforma_en_el_flujo_comisionable():
    f = pd.read_csv(DP / "kpi_flujo_comisionable.csv")
    f = f[(f.variante == "sin_sis") & (f.anio == 2033)].set_index("tipo")
    base, baja, alta = (f.loc[t, "cuentas_individuales"] for t in ("escenario", "escenario_reforma_baja", "escenario_reforma_alta"))
    assert alta < baja < base  # menos cotizantes, menos masa imponible, menos flujo a las cuentas individuales
    assert f.loc["escenario_reforma_alta", "estado"] == f.loc["escenario", "estado"]  # el gasto del Estado no depende del empleo formal
    assert abs(f.loc["escenario_reforma_alta", "kpi_1_3_pct"] - f.loc["escenario", "kpi_1_3_pct"]) < 1  # el efecto en el porcentaje es pequeño


def test_ruta_de_cobertura_es_neutra_por_defecto_y_escala_a_los_trabajadores():
    nac, proy, par = (pd.read_csv(DP / f) for f in ("kpi_pc_nacional.csv", "proyeccion_envejecimiento_pais.csv", "kpi_pc_parametros_reforma.csv"))
    base = cp.serie_pais(nac, proy, par, cp.Escenario())
    assert cp.punto_critico(base)["anio"] == 2038  # el resultado de siempre no cambia
    ruta = ((2025, 1.0), (2033, 0.9))
    con = cp.serie_pais(nac, proy, par, cp.Escenario(cobertura_ruta=ruta)).set_index("anio")
    sin = base.set_index("anio")
    assert con.loc[2025, "trabajadores"] == sin.loc[2025, "trabajadores"]  # los años observados no se tocan
    assert con.loc[2040, "trabajadores"] == pytest.approx(0.9 * sin.loc[2040, "trabajadores"])  # constante después del último punto
    assert con.loc[2029, "trabajadores"] == pytest.approx(0.95 * sin.loc[2029, "trabajadores"])  # lineal entre los puntos
    assert cp.punto_critico(con.reset_index())["anio_exacto"] < cp.punto_critico(base)["anio_exacto"]


def test_escenarios_de_la_reforma_en_el_kpi_1_2():
    esc = pd.read_csv(DP / "kpi_pc_escenarios_reforma.csv")
    assert esc.clave.tolist() == ["base", "reforma_baja", "reforma_alta"] and esc.carga_max.eq(CFG["tope_carga"]["base"]).all()
    nac, proy, par = (pd.read_csv(DP / f) for f in ("kpi_pc_nacional.csv", "proyeccion_envejecimiento_pais.csv", "kpi_pc_parametros_reforma.csv"))
    fac = pd.read_csv(DP / "kpi_reforma_empleo_factor.csv")
    exacto = {}
    for c in esc.clave:
        ruta = tuple((int(a), float(v)) for a, v in fac[fac.escenario == c][["anio", "factor_vs_2025"]].to_numpy())
        e = cp.Escenario(crec_salarial=CFG["crecimiento_salario_real"]["base"], pgu_250=CFG["pgu_250"], cobertura_ruta=ruta)
        pc = cp.punto_critico(cp.serie_pais(nac, proy, par, e))
        exacto[c] = pc["anio_exacto"]
    assert exacto["reforma_alta"] < exacto["reforma_baja"] < exacto["base"]
    assert exacto["base"] - exacto["reforma_alta"] < 2  # el canal del empleo adelanta el cruce menos de dos años: manda la demografía


@pytest.mark.parametrize("pagina", ["final_pages", "extended_pages"])
def test_las_paginas_muestran_los_bloques_de_la_reforma(pagina):
    at = AppTest.from_file(str(DASH / pagina / "objetivo1.py"), default_timeout=180)
    at.session_state["_nav_active"] = True
    at.run()
    assert not at.exception, [e.value for e in at.exception]
    texto = _textos(at)
    assert "¿Adónde va la cotización del empleador?" in texto
    assert "Con la reforma del empleador: dos escenarios frente a la base" in texto
