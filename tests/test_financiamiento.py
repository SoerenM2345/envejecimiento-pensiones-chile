"""KPI 2.2, profundización «quién financia el Pilar y cuánto aguantan las reservas».
Cifras de control: informe mensual del FRP (DIPRES, julio 2026), estados financieros del FAPP, Ley 21.735 (Tabla 2) y SII.
Ejecutar desde la raíz:  "Data raw/.venv/bin/python" -I -m pytest tests -q"""
import sys
from pathlib import Path

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

DASH = Path(__file__).resolve().parent.parent / "Dashboards"
DP = DASH.parent / "Data processed"
sys.path.insert(0, str(DASH))

from components.cost_analysis import serie_historica  # noqa: E402
from components import financiamiento as fin  # noqa: E402


def L(name):
    return pd.read_csv(DP / name)


@pytest.fixture(scope="module")
def h():
    return serie_historica(L("gasto_proteccion_social.csv"), L("macro_pib_anual.csv"), L("proyeccion_envejecimiento_pais.csv"),
                           L("kpi_pc_nacional.csv"), L("pgu_pbs_aps_nacional_anual.csv"))


def proy(h, crec=0.02, pgu=True, fapp=True, ap=None):
    return fin.proyeccion_carga(h, L("pgu_pbs_aps_nacional_anual.csv"), L("macro_pib_anual.csv"), L("proyeccion_envejecimiento_pais.csv"),
                                L("kpi_pc_parametros_reforma.csv"), L("fapp_aporte_fiscal.csv") if ap is None else ap, crec, pgu, fapp)


def test_tablas_frp_fapp_aporte():
    frp = L("frp_reserva_anual.csv").set_index("anio")
    # informe mensual del FRP, julio 2026
    assert frp.loc[2025, "valor_final_musd"] == 10313.19 and frp.loc[2025, "retiros_musd"] == 332.39
    assert frp.loc[2025, "cartera_propia_musd"] == pytest.approx(10091.14, abs=0.01)
    assert round(frp.loc[2025, "cartera_propia_mm"]) == 9_194_845          # receta de la guía: US$ 10.091,14 M x $911,18
    assert (frp.valor_final_musd.iloc[:-1].values == frp.valor_inicial_musd.iloc[1:].values).all()   # encadenado año a año
    # el retiro financia ~4,5 % del Pilar en 2023-2025 (4,4 a 5,2 % desde 2022)
    assert frp.loc[2022:2025, "retiros_pct_pilar"].between(4.3, 5.3).all()
    assert round(frp.loc[2025, "retiros_pct_pilar"], 1) == 4.5
    fb = L("fapp_balance.csv").set_index("cierre")
    assert fb.loc["2025-12-31", "activos_mm"] == 486240.298 and fb.loc["2026-06-30", "patrimonio_mm"] == 25719.095
    assert (fb.activos_mm - fb.patrimonio_mm > fb.deuda_frp_mm).all()          # activos = deuda con el FRP + otros pasivos + patrimonio
    ap = L("fapp_aporte_fiscal.csv").set_index("anio")
    assert ap.loc[2028, "millones_utm"] == 2.2 and ap.loc[2037, "millones_utm"] == 15.0 and ap.loc[2050, "millones_utm"] == 15.0
    assert round(ap.loc[2037, "aporte_mm_2025"]) == round(15 * ap.utm_pesos_2025.iloc[0])   # millones de UTM x pesos = millones de pesos
    assert round(ap.utm_pesos_2025.iloc[0]) == 68640                                          # promedio de la UTM 2025 (SII)


def test_dolar_de_cierre_coincide_con_dipres():
    """El dólar del SII usado para el stock es el mismo que implica la tabla de activos en dólares de DIPRES."""
    frp = L("frp_reserva_anual.csv").set_index("anio")
    dip, pib = L("dipres_pasivos_activos_gc.csv"), L("macro_pib_anual.csv").set_index("anio")
    for a in (2022, 2023, 2024, 2025):
        x = dip[(dip.anio == a) & (dip.codigo.astype(str) == "5")]
        implicito = x[x.unidad == "% PIB"].valor.iloc[0] / 100 * pib.loc[a, "pib_corriente_mm"] / x[x.unidad == "MMUS$"].valor.iloc[0]
        assert abs(implicito - frp.loc[a, "tc_cierre"]) < 0.02


def test_alineacion_mismo_periodo(h):
    """Todo se ancla en 2025: el motor parte en el año base de las tablas que une, y lo regional va con el Censo 2024."""
    assert fin.ANIO_BASE == 2025 == int(h.index.max())
    p = proy(h)
    assert p.index[0] == fin.ANIO_BASE and p.index[-1] == fin.ANIO_FIN
    frp = L("frp_reserva_anual.csv")
    pil = L("pgu_pbs_aps_nacional_anual.csv")
    assert 2025 in set(frp.anio) and 2025 in set(pil.anio)
    assert fin.ANIO_REGIONAL == 2024 and "2024" in fin.TRIM_REGIONAL
    assert set(L("pgu_pbs_aps_region_trimestral.csv").trimestre) >= {fin.TRIM_REGIONAL}
    assert (Path(DASH.parent / "docs" / "alineacion_kpi_2_2.csv")).exists()


def test_el_valor_de_2025_es_el_ratio_1_original(h):
    p = proy(h)
    hist = fin.peso_historico(L("pgu_pbs_aps_nacional_anual.csv"), L("macro_pib_anual.csv"), L("gasto_proteccion_social.csv")).set_index("anio")
    assert round(hist.loc[2025, "pilar_pct_pib"], 2) == 2.07 and round(hist.loc[2025, "edad_avanzada_pct_pib"], 2) == 4.39
    assert abs(p.loc[2025, "pilar_pct_pib"] - hist.loc[2025, "pilar_pct_pib"]) < 1e-9
    assert p.loc[2025, "aporte_fapp"] == 0 and p.loc[2025, "incremento"] == 0


def test_aporte_fapp_empieza_en_2028(h):
    p = proy(h)
    assert (p.loc[:2027, "aporte_fapp"] == 0).all() and p.loc[2028, "aporte_fapp"] > 0
    assert round(p.loc[2037, "aporte_fapp"] / 1e12, 3) == 1.030
    assert (proy(h, fapp=False).aporte_fapp == 0).all()
    assert proy(h).loc[2037, "carga_pct_pib"] > proy(h, fapp=False).loc[2037, "carga_pct_pib"]


def test_invariantes_de_la_proyeccion(h):
    # más crecimiento del PIB: menos peso en el PIB; sin la PGU de $250.000: menos peso
    assert proy(h, crec=0.03).loc[2050, "pilar_pct_pib"] < proy(h, crec=0.01).loc[2050, "pilar_pct_pib"]
    assert proy(h, pgu=False).loc[2035, "pilar_pct_pib"] < proy(h, pgu=True).loc[2035, "pilar_pct_pib"]
    assert 2.4 < proy(h).loc[2030, "pilar_pct_pib"] < 2.5      # control: 2,46 % con los supuestos de partida
    assert proy(h).loc[2037, "carga_pct_pib"] == pytest.approx(2.84, abs=0.01)


def test_reserva_a_mano(h):
    """Comprobación hecha a mano con una trayectoria de tres años (2025 base, 2026 y 2027)."""
    d = pd.DataFrame({"pilar": [100.0, 110.0, 130.0], "carga": [100.0, 110.0, 130.0], "incremento": [0.0, 10.0, 30.0]},
                     index=pd.Index([2025, 2026, 2027], name="anio"))
    d2, res = fin.trayectoria_reserva(d, reserva0=40.0, r_real=0.10, cubre="incremento")
    assert list(d2.saldo) == pytest.approx([40.0, 44.0 - 10.0, 34.0 * 1.1 - 30.0])       # 40, 34, 7.4
    assert res["anio_agotamiento"] is None
    assert res["vp_gasto"] == pytest.approx(10 / 1.1 + 30 / 1.1 ** 2)
    assert res["ratio_cobertura"] == pytest.approx(40 / res["vp_gasto"]) and res["ratio_cobertura"] > 1
    _, res2 = fin.trayectoria_reserva(d, reserva0=30.0, r_real=0.10, cubre="incremento")
    assert res2["anio_agotamiento"] == 2027                                                 # 30 -> 23 -> -4,7
    _, res3 = fin.trayectoria_reserva(d, reserva0=40.0, r_real=0.10, cubre="total")
    assert res3["anio_agotamiento"] == 2026


def test_invariantes_de_la_reserva(h):
    r0 = L("frp_reserva_anual.csv").set_index("anio").loc[2025, "cartera_propia_mm"] * 1e6
    p = proy(h)
    _, base = fin.trayectoria_reserva(p, r0, 0.025, "incremento")
    _, mas = fin.trayectoria_reserva(p, r0 * 1.5, 0.025, "incremento")
    _, rend = fin.trayectoria_reserva(p, r0, 0.04, "incremento")
    _, todo = fin.trayectoria_reserva(p, r0, 0.025, "total")
    assert mas["anio_agotamiento"] >= base["anio_agotamiento"] and mas["ratio_cobertura"] > base["ratio_cobertura"]
    assert rend["anio_agotamiento"] >= base["anio_agotamiento"]
    assert todo["ratio_cobertura"] < base["ratio_cobertura"] and todo["anio_agotamiento"] < base["anio_agotamiento"]
    # control con los supuestos de partida: alcanza 1,3 años del gasto de 2025, se agota en 2033, cubre ~19 % del VP
    assert base["anios_gasto_2025"] == pytest.approx(1.31, abs=0.01) and base["anio_agotamiento"] == 2033
    assert base["ratio_cobertura"] == pytest.approx(0.185, abs=0.01) and todo["anio_agotamiento"] == 2027


def test_sensibilidad_de_los_supuestos_de_fecha(h):
    """Par de sensibilidad que respalda el texto de docs/GUIA: adelantar el primer aporte al FAPP un año (2027 en lugar de 2028, que es
    como lo dice el texto de DIPRES) o usar el dólar promedio en vez del de cierre mueve el año de agotamiento a lo más un año y el ratio < 1 punto
    (el dólar promedio, 4 puntos de reserva y 1 punto de ratio, sin cambiar el año)."""
    frp = L("frp_reserva_anual.csv").set_index("anio").loc[2025]
    r0 = frp.cartera_propia_mm * 1e6
    ap = L("fapp_aporte_fiscal.csv")
    _, base = fin.trayectoria_reserva(proy(h), r0, 0.025, "incremento")
    ap2 = ap.copy()
    ap2["anio"] = ap2.anio - 1
    _, ade = fin.trayectoria_reserva(proy(h, ap=ap2), r0, 0.025, "incremento")
    assert abs(ade["anio_agotamiento"] - base["anio_agotamiento"]) <= 1 and abs(ade["ratio_cobertura"] - base["ratio_cobertura"]) < 0.01
    _, prom = fin.trayectoria_reserva(proy(h), frp.cartera_propia_musd * frp.tc_prom * 1e6, 0.025, "incremento")
    assert prom["anio_agotamiento"] == base["anio_agotamiento"] and abs(prom["ratio_cobertura"] - base["ratio_cobertura"]) < 0.015


def test_fuentes_del_pilar():
    fu = fin.fuentes_pilar(L("frp_reserva_anual.csv"), L("kpi_pc_nacional.csv"))
    assert list(fu.anio) == [2022, 2023, 2024, 2025]
    assert fu.pct_frp.between(4.3, 5.3).all() and (fu.retiros_real < fu.pilar_real).all()
    assert round(fu.pilar_real.iloc[-1] / 1e12, 2) == 7.04


def test_dependencia_regional():
    r = fin.dependencia_regional(L("pgu_pbs_aps_region_trimestral.csv"), L("pgu_pbs_aps_nacional_anual.csv"),
                                 L("kpi_presion_previsional_region.csv"), L("kpi_pc_nacional.csv"))
    reg, nac = r[r.region_id != 0], r[r.region_id == 0].iloc[0]
    assert len(reg) == 16
    assert round(nac.pct_sin_pension) == 28 and round(nac.n_sin_pension, -3) == 593_000     # 592.885 PGU no contributiva (4.º trim. 2024)
    top = reg.sort_values("pct_sin_pension").iloc[-1]
    assert top.region_nombre == "La Araucanía" and round(top.pct_sin_pension) == 42
    assert reg.pct_sin_pension.min() == pytest.approx(23.2, abs=0.1)
    assert reg.pct_sin_pension.corr(reg.razon_soporte) < -0.3        # donde hay menos cotizantes por 65+, más gente depende solo de la PGU
    assert reg.peso_mes_por_65.between(150_000, 250_000).all()
    # costo de la PGU a quienes no tienen pensión propia: 28,5 % de la PGU de 2024 en pesos de 2025 (~0,5 % del PIB)
    assert nac.costo_sin_pension / 1e12 == pytest.approx(1.54, abs=0.02)
    assert nac.costo_sin_pension / (L("macro_pib_anual.csv").set_index("anio").loc[2024, "pib_corriente_mm"] * 1e6) == pytest.approx(0.0050, abs=0.0003)
    assert reg.costo_sin_pension.sum() == pytest.approx(nac.costo_sin_pension)
    for anio, veces in ((2035, 1.5), (2050, 2.04)):
        pr = fin.proyeccion_sin_pension(r, L("kpi_proyeccion_regional.csv"), anio)
        assert len(pr) == 16 and pr.n_anio.sum() / pr.n_2024.sum() == pytest.approx(veces, abs=0.05)


def _run():
    at = AppTest.from_file(str(DASH / "final_pages" / "objetivo2.py"), default_timeout=120)
    at.session_state["_nav_active"] = True
    return at.run()


def test_pagina_con_todos_los_caminos_de_los_controles():
    at = _run()
    assert not at.exception, [e.value for e in at.exception]
    assert {"Peso fiscal 2050", "Quién lo financia", "Reservas", "FAPP hoy", "Dónde"} <= {t.label for t in at.tabs}
    for key, values in {"k22_res": ["Solo FRP", "FRP + activos del FAPP"], "k22_cubre": ["Solo el alza sobre el peso de 2025", "Todo el gasto del Pilar"]}.items():
        for v in values:
            at.radio(key=key).set_value(v).run()
            assert not at.exception, (key, v, [e.value for e in at.exception])
    for key, vals in {"k22_pib": [0.0, 4.0], "k22_r": [0.0, 5.0]}.items():
        for v in vals:
            at.slider(key=key).set_value(v).run()
            assert not at.exception, (key, v, [e.value for e in at.exception])
    for key in ("k22_pgu", "k22_fapp"):
        at.checkbox(key=key).set_value(False).run()
        assert not at.exception, (key, [e.value for e in at.exception])
    # casillas del panel de fórmulas (mostrar u ocultar cada línea): una por una y todas apagadas
    claves = ("k22_v_obs", "k22_v_esc", "k22_v_gas", "k22_v_sal")
    at.checkbox(key="k22_pgu").set_value(True).run()
    at.checkbox(key="k22_fapp").set_value(True).run()
    for key in claves + ("k22_v_fapp",):
        at.checkbox(key=key).set_value(False).run()
        assert not at.exception, (key, [e.value for e in at.exception])
    assert all(not at.checkbox(key=k).value for k in claves)


def test_el_kpi_original_se_conserva():
    """Lo que ya citaba la presentación (2,07 % y 4,39 % en 2025) sigue en la tarjeta."""
    at = _run()
    metricas = {m.label: m.value for m in at.metric}
    assert metricas["(PGU + pensión solidaria) / PIB (2025)"] == "2,07%"
    assert metricas["Gasto en edad avanzada / PIB (2025)"] == "4,39%"
