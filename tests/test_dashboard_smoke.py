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
    # AppTest no reporta errores de sintaxis como excepción (la página queda vacía): compilar antes
    compile((DASH / page).read_text(encoding="utf-8"), page, "exec")
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
    assert len(FINAL_PAGES) == 6 and len(DEV_PAGES) >= 8  # 5 del dashboard + activar_dev


def test_regression_national_support_ratio():
    """Valores que la presentación ya usa: no deben cambiar sin querer."""
    import pandas as pd
    pres = pd.read_csv(DASH.parent / "Data processed" / "kpi_presion_previsional_region.csv")
    nuble = pres[pres.region_nombre == "Ñuble"].iloc[0]
    assert round(nuble.cobertura_previsional_pct, 2) == 37.83  # cotizantes 2024 (KPI 1.1)
    assert round(nuble.razon_soporte_previsional, 2) == 1.51  # cotizantes dic-2024 / Censo 2024
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


def test_kpi_1_3_participacion():
    """KPI 1.3: 12 meses por año, control de la ficha N° 157 y empleador solo desde 2025."""
    import pandas as pd
    dp = DASH.parent / "Data processed"
    fichas = pd.read_csv(dp / "fichas_previsionales_mensual.csv")
    f157 = fichas[fichas.n_ficha == 157].iloc[0]
    assert (f157.cotizantes, f157.ingreso_promedio) == (5795995, 1362207)
    assert abs(f157.aporte_trabajadores_mes / 1e6 - 789_500) < 100
    k = pd.read_csv(dp / "kpi_participacion_partes.csv").set_index("anio")
    assert list(k.index) == [2024, 2025] and (k.n_meses == 12).all()
    assert k.loc[2024, "aporte_empleador"] == 0 and k.loc[2025, "aporte_empleador"] == 283_048_436_000
    meses = pd.PeriodIndex(fichas.mes_ref_cotizantes, freq="M")
    for anio in (2024, 2025):  # 12 meses de referencia distintos por año
        assert sorted(m.month for m in meses if m.year == anio) == list(range(1, 13))
    f = pd.read_csv(dp / "kpi_flujo_comisionable.csv")
    assert set(f.variante) == {"sin_sis", "con_sis"}
    assert (f.n_meses == 12).all()
    sin = f[f.variante == "sin_sis"]
    real = sin[sin.tipo == "real"].set_index("anio")
    # la variante principal no cambia los años reales (57,0% y 55,5%)
    assert round(real.loc[2024, "kpi_1_3_pct"], 1) == 57.0 and round(real.loc[2025, "kpi_1_3_pct"], 1) == 55.5
    assert real.loc[2024, "empleador_ci"] == 0 and real.loc[2025, "seguro_social_fapp"] == 283_048_436_000
    esc = sin[sin.tipo == "escenario"].set_index("anio")
    assert list(esc.index) == list(range(2026, 2036))
    assert esc.kpi_1_3_pct.max() < real.loc[2025, "kpi_1_3_pct"]  # el escenario nunca vuelve al nivel de 2025
    assert (sin.cuentas_individuales + sin.seguro_social_fapp + sin.estado == sin.flujo_total).all()
    con = f[f.variante == "con_sis"]
    assert (con.cuentas_individuales + con.seguro_social_fapp + con.estado + con.sis == con.flujo_total).all()
    # mismo SIS en ambas variantes; con SIS el nivel es siempre menor
    assert (sin.sis.values == con.sis.values).all() and (con.kpi_1_3_pct.values < sin.kpi_1_3_pct.values).all()


def test_kpi_1_1_correlaciones():
    """KPI 1.1 diagnóstico: 16 regiones sin vacíos, misma cobertura que la tarjeta y signos esperados."""
    import pandas as pd
    dp = DASH.parent / "Data processed"
    reg = pd.read_csv(dp / "kpi_cobertura_correlaciones_region.csv")
    assert len(reg) == 16 and not reg.isna().any().any()
    pres = pd.read_csv(dp / "kpi_presion_previsional_region.csv").set_index("region_id")
    assert (reg.set_index("region_id").cobertura_previsional_pct == pres.cobertura_previsional_pct.reindex(reg.region_id)).all()
    assert abs(reg.share_cotizantes_pct.sum() - 100) < 0.1
    res = pd.read_csv(dp / "kpi_cobertura_correlaciones_resumen.csv").set_index("variable")
    assert (res.n == 16).all()
    assert res.loc["ingreso", "pearson_r"] > 0.6 and res.loc["pobreza_65", "pearson_r"] < -0.5
    assert res.loc["urbano", "pearson_r"] > 0.4 and res.loc["pct_65_mas", "pearson_r"] < 0


def test_kpi_1_2_razon_y_sensibilidad():
    """KPI 1.2: razón de soporte 2024 del país = 2,27 y tabla de sensibilidad 3 × 3 del punto crítico."""
    import pandas as pd
    dp = DASH.parent / "Data processed"
    pres = pd.read_csv(dp / "kpi_presion_previsional_region.csv")
    assert round(pres.cotizantes_2024.sum() / pres.pob_65_mas.sum(), 2) == 2.27
    sens = pd.read_csv(dp / "kpi_punto_critico_sensibilidad.csv")
    assert len(sens) == 9 and sens.es_base.sum() == 1
    assert sens.groupby("crecimiento_salario_real").size().eq(3).all() and sens.groupby("tope_carga").size().eq(3).all()
    base = sens[sens.es_base].iloc[0]
    assert (base.crecimiento_salario_real, base.tope_carga) == (0.01, 0.10)
    # más tope o más sueldo -> el punto crítico llega más tarde
    piv = sens.pivot(index="crecimiento_salario_real", columns="tope_carga", values="punto_critico")
    assert (piv.diff(axis=1).iloc[:, 1:] >= 0).all().all() and (piv.diff().iloc[1:] >= 0).all().all()


def test_kpis_1_2_1_3_2_2_leen_la_misma_config_de_escenarios():
    """Los supuestos de los escenarios vienen de un solo archivo: config/escenarios.yaml."""
    import yaml
    raiz = DASH.parent
    cfg = yaml.safe_load((raiz / "config" / "escenarios.yaml").read_text(encoding="utf-8"))
    assert cfg["crecimiento_salario_real"]["base"] == 0.01 and cfg["tope_carga"]["base"] == 0.10
    usan = {
        "KPI 1.3 (Scripts/15)": raiz / "Scripts" / "15_kpi_participacion_partes.py",
        "KPI 1.2 sensibilidad (Scripts/22)": raiz / "Scripts" / "22_punto_critico_sensibilidad.py",
        "KPI 1.2 y 1.3 (Objetivo 1)": DASH / "final_pages" / "objetivo1.py",
        "KPI 2.2 (Objetivo 2)": DASH / "final_pages" / "objetivo2.py",
    }
    for kpi, archivo in usan.items():
        texto = archivo.read_text(encoding="utf-8")
        assert "escenarios.yaml" in texto or "cargar_escenarios(" in texto, f"{kpi} no lee config/escenarios.yaml"
    import pandas as pd
    f = pd.read_csv(raiz / "Data processed" / "kpi_flujo_comisionable.csv")
    # KPI 1.3: el escenario base y las variantes salen de la config
    assert set(f.tipo) == {"real", "escenario", "escenario_crec_0", "escenario_crec_1_5"}


def test_kpi_2_2_sensibilidad_y_gasto_2025():
    """KPI 2.2: tabla de sensibilidad de 3 filas y gasto 2025 del motor = fila 'Total' del Pilar Solidario."""
    import pandas as pd
    import yaml
    from components.cost_analysis import serie_historica
    from components.financiamiento import proyeccion_carga
    dp = DASH.parent / "Data processed"
    cfg = yaml.safe_load((DASH.parent / "config" / "escenarios.yaml").read_text(encoding="utf-8"))
    sens = pd.read_csv(dp / "kpi_2_2_sensibilidad.csv")
    assert len(sens) == 3 and sens.es_base.sum() == 1
    assert sorted(sens.rentabilidad_real) == sorted([cfg["rentabilidad_real_reservas"]["base"]] + cfg["rentabilidad_real_reservas"]["variantes"])
    assert sens.cobertura_pct.is_monotonic_increasing  # más rentabilidad -> menos VP del gasto -> más cobertura
    leer = lambda f: pd.read_csv(dp / f)  # noqa: E731
    pil = leer("pgu_pbs_aps_nacional_anual.csv")
    h = serie_historica(leer("gasto_proteccion_social.csv"), leer("macro_pib_anual.csv"), leer("proyeccion_envejecimiento_pais.csv"),
                        leer("kpi_pc_nacional.csv"), pil, "mediana")
    p = proyeccion_carga(h, pil, leer("macro_pib_anual.csv"), leer("proyeccion_envejecimiento_pais.csv"), leer("kpi_pc_parametros_reforma.csv"),
                         leer("fapp_aporte_fiscal.csv"), cfg["crecimiento_pib_real"], cfg["pgu_250"], cfg["aporte_fapp"], cfg["horizonte_proyeccion"])
    total25 = pil[(pil.anio == 2025) & (pil.tipo_beneficio == "Total")].monto_nominal_mm.iloc[0] * 1e6
    assert abs(p.loc[2025, "pilar"] - total25) < 1e6 and round(total25 / 1e12, 2) == 7.04
    assert p.index.max() == cfg["horizonte_proyeccion"]


def test_objetivo_2_titulo_igual_en_config_y_dashboard():
    """El nombre del Objetivo 2 es el mismo en kpis.yaml (2.1-2.3), en la página y en la navegación."""
    import re
    import yaml
    cfg = yaml.safe_load((DASH.parent / "config" / "kpis.yaml").read_text(encoding="utf-8"))
    objetivos = {k["objetivo"] for k in cfg["kpis_presentacion"] if k["id"].startswith("2.")}
    assert len(objetivos) == 1
    titulo = objetivos.pop()
    pagina = (DASH / "final_pages" / "objetivo2.py").read_text(encoding="utf-8")
    assert re.search(r'TITULO_OBJETIVO_2 = "([^"]+)"', pagina).group(1) == titulo
    assert f'title="{titulo}"' in (DASH / "Inicio.py").read_text(encoding="utf-8")


def test_kpi_2_3_pobreza_cobertura():
    """KPI 2.3 diagnóstico: 16 regiones y la misma correlación que el resumen de cobertura."""
    import pandas as pd
    from scipy import stats
    dp = DASH.parent / "Data processed"
    pc = pd.read_csv(dp / "kpi_pobreza_cobertura_region.csv")
    assert len(pc) == 16 and not pc.isna().any().any()
    r = pd.read_csv(dp / "kpi_cobertura_correlaciones_resumen.csv").set_index("variable").loc["pobreza_65", "pearson_r"]
    assert abs(stats.pearsonr(pc.cobertura_previsional_pct, pc.pct_pobreza_65)[0] - r) < 1e-3 and r < 0


def test_formato_es_cl():
    from utils import es_cl
    assert es_cl("55.5%") == "55,5%" and es_cl("1,209 mil") == "1.209 mil" and es_cl("$1,281,744") == "$1.281.744"
    assert es_cl("p = 0,004") == "p = 0,004" and es_cl("$0,026 billones") == "$0,026 billones"
    assert es_cl("Ley 21.735") == "Ley 21.735" and es_cl("KPI 1.2 y KPI 1.3") == "KPI 1.2 y KPI 1.3" and es_cl("2038") == "2038"


def test_graficos_finales_pasan_por_mostrar():
    """En el modo final todos los gráficos se dibujan con charts.mostrar (texto oscuro y theme=None): ningún st.plotly_chart directo."""
    for f in (DASH / "final_pages").glob("*.py"):
        assert "st.plotly_chart(" not in f.read_text(encoding="utf-8"), f"{f.name} dibuja un gráfico sin charts.mostrar"


@pytest.mark.parametrize("page, clave", [("final_pages/objetivo1.py", "s11_vista_region"), ("final_pages/objetivo2.py", "s23_vista_region")])
def test_vista_en_personas_de_las_barras_por_region(page, clave):
    """KPI 1.1 y 2.3: la vista «Personas (mismo orden)» de las barras por región se dibuja sin errores."""
    at = run_page(page)
    at.radio(key=clave).set_value("Personas (mismo orden)").run()
    assert not at.exception
