"""Análisis del punto crítico del KPI 1.2: tablas de insumo (script 18), motor de cálculo y página (país / región / comuna).
Ejecutar desde la raíz del proyecto:  python -I -m pytest tests -q   (venv: Data raw/.venv)"""
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parent.parent
DASH = ROOT / "Dashboards"
DP = ROOT / "Data processed"
sys.path.insert(0, str(DASH))

from components import critical_point as cp  # noqa: E402


def cargar_script(nombre):
    """Los scripts empiezan con número (no son importables con import): se cargan por ruta."""
    spec = importlib.util.spec_from_file_location(nombre, ROOT / "Scripts" / f"{nombre}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def datos():
    return dict(nac=pd.read_csv(DP / "kpi_pc_nacional.csv"), proy=pd.read_csv(DP / "proyeccion_envejecimiento_pais.csv"),
                par=pd.read_csv(DP / "kpi_pc_parametros_reforma.csv"), reg=pd.read_csv(DP / "kpi_pc_region.csv"),
                ind=pd.read_csv(DP / "indicadores_region.csv"), pr=pd.read_csv(DP / "kpi_proyeccion_regional.csv"))


# ───────────── tablas de insumo ─────────────
def test_sp_04a_serie_mensual_completa_y_cifras_de_control():
    s = pd.read_csv(DP / "sp_ingreso_imponible_nacional.csv")
    tot = s[(s.tipo == "Total") & (s.sexo == "Ambos")].set_index("periodo")
    meses = pd.period_range("2002-10", "2026-08", freq="M").strftime("%Y-%m")
    assert set(meses) <= set(tot.index), "faltan meses del cuadro 04A (correr Scripts/15)"
    assert tot.loc["2024-12", "cotizantes"] == 5_918_977 and tot.loc["2024-12", "ingreso_promedio_nom"] == 1_229_604
    assert tot.loc["2020-01", "ingreso_promedio_nom"] == 897_897  # primer mes que ya estaba descargado a mano
    assert tot.loc["2019-12", "cotizantes"] == 5_618_954  # mes bajado por el script 15 (coincide con la serie anual de cotizantes)


def test_cotizantes_04a_coinciden_con_la_serie_de_cotizantes_por_region():
    n = pd.read_csv(DP / "kpi_pc_nacional.csv").set_index("anio")
    tot = pd.read_csv(DP / "cotizantes_por_region.csv")
    tot = tot[tot.region_label == "Total"].set_index("anio").cotizantes
    assert (n.cotizantes_dic == tot.reindex(n.index)).all()


def test_ine_esi_2024_y_ocupados(datos):
    n = datos["nac"].set_index("anio")
    assert round(n.loc[2024, "ing_ocupados_mediano_nom"]) == 611_162
    assert 8_000_000 < n.loc[2024, "ocupados_ond"] < 10_000_000
    assert len(datos["reg"][datos["reg"].anio == 2024]) == 16


def test_ipc_deflactor_base_2025():
    d = pd.read_csv(DP / "ipc_anual.csv").set_index("anio")
    assert d.loc[2025, "deflactor_2025"] == pytest.approx(1.0)
    assert 1.03 < d.loc[2024, "deflactor_2025"] < 1.06  # inflación 2025 ≈ 4 %


def test_costo_vejez_2025_y_cuota_regional(datos):
    n = datos["nac"].set_index("anio")
    assert round(n.loc[2025, "costo_vejez_por_65_real25"] / 1e6, 2) == 2.15  # millones de pesos al año por persona de 65+
    r = datos["reg"]
    c = r[(r.anio == 2024)].cuota_gasto_vejez
    assert c.notna().all() and abs(c.sum() - 1) < 1e-9  # incluye Biobío (antes se perdía por la tilde de 'Bíobío')


def test_mediana_por_tramos_a_mano():
    s16 = cargar_script("18_kpi_punto_critico")
    g = pd.DataFrame({"tramo_desde_miles": [0, 100], "tramo_hasta_miles": [100, 200], "cotizantes": [10, 20]})
    assert s16.mediana_tramos(g) == pytest.approx(125_000)  # 15 de 30: 5/20 del segundo tramo
    g = pd.DataFrame({"tramo_desde_miles": [0, 100], "tramo_hasta_miles": [100, np.nan], "cotizantes": [10, 10]})
    assert s16.mediana_tramos(g) == pytest.approx(100_000)  # tramo abierto: usa el límite inferior


def test_mediana_de_los_cotizantes_es_menor_que_el_promedio(datos):
    n = datos["nac"].set_index("anio")
    assert (n.ingreso_imponible_mediano_nom < n.ingreso_imponible_prom_nom).all()
    assert 900_000 < n.loc[2025, "ingreso_imponible_mediano_nom"] < 1_100_000


def test_script_15_lee_la_fecha_del_titulo():
    s15 = cargar_script("15_descargar_sp_ingreso_imponible")
    t = "NÚMERO DE COTIZANTES E INGRESO IMPONIBLE PROMEDIO POR TIPO Y SEXO (1) (Al 31 de Diciembre de 2024)"
    assert s15.fecha_del_titulo(t) == 202412
    assert s15.fecha_del_titulo("OTRO CUADRO (Al 31 de Diciembre de 2024)") is None


def test_factor_pgu_250_sube_y_se_estabiliza(datos):
    f = datos["par"].set_index("anio").factor_costo_pgu
    assert f[2025] == 1.0 and f[2026] < f[2027] < f[2028]
    assert f[2028] == pytest.approx(f[2040]) and 1.09 < f[2028] < 1.11  # 250.000 / 224.004 sobre la parte PGU del gasto


# ───────────── motor ─────────────
def test_pais_2025_razon_de_soporte_con_datos_del_mismo_anio(datos):
    d = cp.serie_pais(datos["nac"], datos["proy"], datos["par"], cp.Escenario())
    f = cp.fila_anio(d, 2025)
    assert round(f.razon_soporte, 2) == 2.06  # 5.974.428 cotizantes / 2.906.461 personas de 65+ (INE 2025)
    assert round(f.carga_requerida, 3) == 0.067


def test_pais_punto_critico_por_defecto_y_orden_de_las_bases(datos):
    args = (datos["nac"], datos["proy"], datos["par"])
    a_prom = cp.punto_critico(cp.serie_pais(*args, cp.Escenario()))
    a_med = cp.punto_critico(cp.serie_pais(*args, cp.Escenario(estadistico="mediana")))
    b_prom = cp.punto_critico(cp.serie_pais(*args, cp.Escenario(base="B")))
    assert a_prom["estado"] == "cruza" and a_prom["anio"] == 2039
    assert a_med["anio"] < a_prom["anio"] < b_prom["anio"]  # mediana: menos ingreso -> antes; ocupados: más trabajadores -> después


def test_punto_critico_se_mueve_con_los_supuestos(datos):
    args = (datos["nac"], datos["proy"], datos["par"])
    base = cp.punto_critico(cp.serie_pais(*args, cp.Escenario()))["anio"]
    mas_sueldo = cp.punto_critico(cp.serie_pais(*args, cp.Escenario(crec_salarial=0.03)))
    mas_carga = cp.punto_critico(cp.serie_pais(*args, cp.Escenario(carga_max=0.15)))
    sin_pgu = cp.punto_critico(cp.serie_pais(*args, cp.Escenario(pgu_250=False)))
    assert (mas_sueldo["anio"] or 9999) > base and (mas_carga["anio"] or 9999) > base and sin_pgu["anio"] >= base


def test_punto_critico_estados(datos):
    args = (datos["nac"], datos["proy"], datos["par"])
    assert cp.punto_critico(cp.serie_pais(*args, cp.Escenario(carga_max=0.50)))["estado"] == "no_cruza"
    assert cp.punto_critico(cp.serie_pais(*args, cp.Escenario(carga_max=0.01)))["estado"] == "ya_superado"


def test_region_usa_2024_y_anclas_2035_2050(datos):
    dt = cp.datos_territorio(5, datos["reg"], datos["nac"], datos["ind"], datos["pr"])
    d = cp.serie_territorio(dt, datos["par"], cp.Escenario())
    assert d.anio.min() == 2024 and d.anio.max() == 2050
    assert list(d[d.ancla].anio) == [2024, 2035, 2050]
    f = cp.fila_anio(d, 2024)
    assert round(f.razon_soporte, 2) == 1.70 and 0.09 < f.carga_requerida < 0.105  # Valparaíso 2024
    assert cp.fila_anio(d, 2050).razon_soporte < f.razon_soporte


def test_comuna_hereda_de_la_region_y_conserva_su_estructura_de_edad(datos):
    dt = cp.datos_territorio(5, datos["reg"], datos["nac"], datos["ind"], datos["pr"])
    com = pd.read_csv(DP / "indicadores_comuna.csv")
    c = com[(com.region == 5)].iloc[0]
    dc = cp.comuna_desde_region(dt, float(c.pob_65_mas), float(c.pob_15_64))
    d = cp.serie_territorio(dc, datos["par"], cp.Escenario())
    assert cp.fila_anio(d, 2024).pob_65 == pytest.approx(c.pob_65_mas)
    assert dc["costo_65"] == dt["costo_65"] and dc["ing_A_promedio"] == dt["ing_A_promedio"]


# ───────────── página ─────────────
def correr(cambios):
    at = AppTest.from_file(str(DASH / "final_pages" / "objetivo1.py"), default_timeout=120)
    at.session_state["_nav_active"] = True
    at.run()
    for tipo, clave, valor in cambios:
        getattr(at, tipo)(key=clave).set_value(valor)
        at.run()
    return at


@pytest.mark.parametrize("cambios", [
    [],
    [("selectbox", "pc_territorio", "Valparaíso")],
    [("selectbox", "pc_territorio", "Valparaíso"), ("selectbox", "pc_comuna", "Viña del Mar")],
    [("radio", "pc_base", "Todos los ocupados"), ("radio", "pc_estadistico", "Mediana"), ("radio", "pc_vista", "Razón de soporte")],
    [("selectbox", "pc_territorio", "Ñuble"), ("radio", "pc_base", "Todos los ocupados"), ("radio", "pc_vista", "Razón de soporte")],
    [("slider", "pc_carga", 3.0)],
    [("slider", "pc_carga", 20.0)],
])
def test_pagina_punto_critico_corre(cambios):
    at = correr(cambios)
    assert not at.exception, [e.value for e in at.exception]
    assert any("Lectura" in m.value for m in at.markdown)


def test_pagina_pais_muestra_el_punto_critico_2039():
    at = correr([])
    metricas = {m.label: m.value for m in at.metric}
    assert metricas["Punto crítico"] == "2039"
    assert metricas["Cotizantes por 65+ (2025)"] == "2.06"
