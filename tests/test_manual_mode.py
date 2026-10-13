"""Modo manual: cada receta de docs/GUIA_KPIs_DASHBOARD.md se ejecuta sobre el Explorador (como lo haría una persona,
widget por widget) y debe reproducir la cifra que muestra el dashboard final. Si cambia el Explorador o las tablas,
estos tests avisan que la guía quedó desactualizada.

Ejecutar desde la raíz del proyecto:  python -I -m pytest tests -q
"""
import sys
from pathlib import Path

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

DASH = Path(__file__).resolve().parent.parent / "Dashboards"
sys.path.insert(0, str(DASH))  # utils / components, como al correr la app
PAGE = str(DASH / "pages" / "1_🔍_Explorador_de_datos.py")


def w(at, kind, label):
    """Widget del sidebar o de la página por tipo y etiqueta."""
    for scope in (at.sidebar, at.main):
        for x in getattr(scope, kind):
            if x.label == label:
                return x
    raise AssertionError(f"no hay {kind} con etiqueta {label!r}")


def receta(fuente, *, mezclar=None, calc=None, filtros=None, agrupar, columna, funcion="mean"):
    """Ejecuta una receta en el Explorador y devuelve la tabla agregada (DataFrame).
    mezclar=(segunda_fuente, clave, tipo_cruce); calc=(A, operador, B, factor, nombre); filtros={columna: [valores] o (desde, hasta)}."""
    at = AppTest.from_file(PAGE, default_timeout=60)
    at.session_state["_nav_active"] = True
    at.run()
    w(at, "selectbox", "Fuente principal").select(fuente).run()
    if mezclar:
        f2, clave, tipo = mezclar
        w(at, "checkbox", "Mezclar con una segunda fuente").check().run()
        w(at, "selectbox", "Segunda fuente").select(f2).run()
        w(at, "selectbox", "Cruzar por").select(clave).run()
        w(at, "radio", "Tipo de cruce").set_value(tipo).run()
    if calc:
        a, op, b, factor, nombre = calc
        w(at, "checkbox", "Agregar columna calculada").check().run()
        w(at, "selectbox", "A (columna)").select(a).run()
        w(at, "selectbox", "Operador").select(op).run()
        w(at, "selectbox", "B (columna)").select(b).run()
        w(at, "number_input", "Multiplicar el resultado por").set_value(factor).run()
        w(at, "text_input", "Nombre de la columna nueva").set_value(nombre).run()
    if filtros:
        w(at, "multiselect", "Columnas a filtrar").set_value(list(filtros)).run()
        for col, vals in filtros.items():
            if isinstance(vals, tuple):  # columna numérica -> slider de rango (desde, hasta)
                w(at, "slider", col).set_value(vals).run()
            else:  # columna de texto -> multiselect de valores
                w(at, "multiselect", col).set_value(vals).run()
    w(at, "multiselect", "Agrupar por").set_value(agrupar).run()
    w(at, "selectbox", "Columna a agregar").select(columna).run()
    w(at, "selectbox", "Función").select(funcion).run()
    assert not at.exception, [e.value for e in at.exception]
    return at.dataframe[-1].value  # la última tabla es el agregado


def valor(df, fila_col, fila_val, col):
    return float(df.loc[df[fila_col] == fila_val, col].iloc[0])


PRES = "kpi_presion_previsional_region.csv"
DP = DASH.parent / "Data processed"


def test_1_1_cobertura_precalculada_y_manual():
    pre = receta(PRES, agrupar=["region_nombre"], columna="cobertura_previsional_pct")
    assert round(valor(pre, "region_nombre", "Ñuble", "cobertura_previsional_pct"), 2) == 37.83
    man = receta(PRES, calc=("cotizantes_2024", "÷ dividir", "pob_15_64", 100.0, "cobertura_manual"),
                 agrupar=["region_nombre"], columna="cobertura_manual")
    assert round(valor(man, "region_nombre", "Ñuble", "cobertura_manual"), 2) == 37.83


def test_1_2_razon_de_soporte_actual_y_escenario():
    man = receta(PRES, calc=("cotizantes", "÷ dividir", "pob_65_mas", 1.0, "razon_manual"),
                 agrupar=["region_nombre"], columna="razon_manual")
    assert round(valor(man, "region_nombre", "Ñuble", "razon_manual"), 2) == 1.54
    esc = receta("kpi_proyeccion_regional.csv", mezclar=(PRES, "region_id", "left"),
                 calc=("cobertura_previsional_pct", "÷ dividir", "indice_dependencia_vejez_proy", 1.0, "razon_2035"),
                 filtros={"anio": (2035, 2035)}, agrupar=["region_nombre"], columna="razon_2035")
    esperado = 37.83 / 36.06
    assert abs(valor(esc, "region_nombre", "Ñuble", "razon_2035") - esperado) < 0.005


def test_1_2_punto_critico_razon_y_costo_por_persona_de_65():
    """Insumos del análisis del punto crítico: razón 2025 con datos del mismo año (INE 65+ 2025) y costo por persona de 65+."""
    r = receta("kpi_pc_nacional.csv", calc=("cotizantes_dic", "÷ dividir", "pob_65_mas_ine", 1.0, "razon_manual"),
               filtros={"anio": (2025, 2025)}, agrupar=["anio"], columna="razon_manual")
    assert round(valor(r, "anio", 2025, "razon_manual"), 2) == 2.06
    c = receta("kpi_pc_nacional.csv", filtros={"anio": (2025, 2025)}, agrupar=["anio"], columna="costo_vejez_por_65_real25")
    assert round(valor(c, "anio", 2025, "costo_vejez_por_65_real25") / 1e6, 2) == 2.15


def test_2_1_costo_por_adulto_mayor_y_pib_per_capita():
    costo = receta("gasto_proteccion_social.csv", mezclar=("proyeccion_envejecimiento_pais.csv", "anio", "left"),
                   calc=("gasto_mm_2025", "÷ dividir", "pob_65_mas", 1_000_000.0, "costo_65"),
                   filtros={"categoria": ["Edad avanzada"]}, agrupar=["anio"], columna="costo_65")
    g = pd.read_csv(DP / "gasto_proteccion_social.csv")
    p = pd.read_csv(DP / "proyeccion_envejecimiento_pais.csv").set_index("anio")
    ea = g[g.categoria == "Edad avanzada"].set_index("anio")
    esperado_2025 = ea.loc[2025, "gasto_mm_2025"] * 1e6 / p.loc[2025, "pob_65_mas"]
    assert abs(valor(costo, "anio", 2025, "costo_65") - esperado_2025) < 1
    assert round(valor(costo, "anio", 2025, "costo_65") / 1e6, 2) == 5.13  # lo que muestra la tarjeta del dashboard

    pibpc = receta("macro_pib_anual.csv", mezclar=("proyeccion_envejecimiento_pais.csv", "anio", "inner"),
                   calc=("pib_real_mm_2018", "÷ dividir", "pob_total", 1_000_000.0, "pib_pc_real"),
                   agrupar=["anio"], columna="pib_pc_real")
    var = valor(pibpc, "anio", 2025, "pib_pc_real") / valor(pibpc, "anio", 2016, "pib_pc_real") - 1
    assert round(100 * var) == 9  # +9% que muestra la tarjeta
    var_costo = valor(costo, "anio", 2025, "costo_65") / valor(costo, "anio", 2016, "costo_65") - 1
    assert round(100 * var_costo) == 11  # +11%


def test_2_2_pgu_y_pension_solidaria_sobre_pib():
    r = receta("pgu_pbs_aps_nacional_anual.csv", mezclar=("macro_pib_anual.csv", "anio", "left"),
               calc=("monto_nominal_mm", "÷ dividir", "pib_corriente_mm", 100.0, "pct_pib"),
               filtros={"tipo_beneficio": ["Total"]}, agrupar=["anio"], columna="pct_pib")
    assert round(valor(r, "anio", 2025, "pct_pib"), 2) == 2.07  # tarjeta del dashboard


def test_2_3_pobreza_65():
    r = receta("pobreza_65_region.csv", agrupar=["region_nombre"], columna="pct_pobreza_65")
    assert round(valor(r, "region_nombre", "Chile", "pct_pobreza_65"), 1) == 14.9
    assert r.sort_values("pct_pobreza_65").iloc[-1]["region_nombre"] == "La Araucanía"


def test_1_1_total_pais_sin_agrupar():
    """Agrupar por vacío = una cifra total: cotizantes 2024 ÷ pob_15_64 del país (46,5%, la línea 'País' del dashboard)."""
    def total(columna):
        at = AppTest.from_file(PAGE, default_timeout=60)
        at.session_state["_nav_active"] = True
        at.run()
        w(at, "selectbox", "Fuente principal").select(PRES).run()
        w(at, "multiselect", "Agrupar por").set_value([]).run()
        w(at, "selectbox", "Columna a agregar").select(columna).run()
        w(at, "selectbox", "Función").select("sum").run()
        assert not at.exception, [e.value for e in at.exception]
        return float(at.metric[-1].value.replace(",", ""))
    cobertura = 100 * total("cotizantes_2024") / total("pob_15_64")
    assert round(cobertura, 1) == 46.5
