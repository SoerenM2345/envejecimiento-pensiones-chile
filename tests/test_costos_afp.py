"""Scripts/27: resultados del sistema de AFP leídos de los informes de costos de administración de la Superintendencia."""
from pathlib import Path

import pandas as pd

DP = Path(__file__).resolve().parent.parent / "Data processed"


def test_resultados_afp_cuadran_con_los_informes():
    d = pd.read_csv(DP / "afp_resultados_sistema.csv").set_index("anio")
    assert list(d.index) == list(range(2016, 2026))
    # cifras publicadas (millones de pesos de cada año)
    assert d.loc[2025, ["ingresos_mm", "comisiones_mm", "gastos_mm", "ganancia_mm"]].tolist() == [1533038, 1189569, 604322, 691499]
    assert d.loc[2016, ["ingresos_mm", "comisiones_mm", "gastos_mm", "ganancia_mm"]].tolist() == [748085, 649870, 328551, 353180]
    assert d.loc[2025, "roe_pct"] == 23.21 and d.loc[2016, "roe_neta_pct"] == 16.6
    ing = d.comisiones_mm + d.encaje_mm + d.otros_ingresos_mm
    assert ((ing - d.ingresos_mm).abs() <= 3).all()
    assert (d.loc[2025, "comisiones_mm_2025"] == d.loc[2025, "comisiones_mm"])


def test_estructura_y_razones_del_sistema():
    """Cifras derivadas verificadas (docs/COSTOS_AFP_HALLAZGOS.md)."""
    d = pd.read_csv(DP / "afp_resultados_sistema.csv").set_index("anio")
    u = d.loc[2025]
    assert (u.personal_admin_pct, u.personal_ventas_pct, u.op_administracion_pct, u.op_computacion_pct, u.op_otros_pct,
            u.op_comercializacion_pct) == (30.8, 17.2, 20.9, 9.5, 5.9, 2.7)
    partes = 100 * (d.gastos_personal_mm + d.gastos_operacion_mm + d.depreciacion_mm + d.otros_gastos_mm) / d.gastos_mm
    assert ((partes - 100).abs() < 0.1).all()
    razon = 100 * d.gastos_mm / d.comisiones_mm
    assert round(razon[2016], 1) == 50.6 and round(razon[2020], 1) == 65.7 and round(razon[2025], 1) == 50.8
    assert round((u.personal_ventas_pct + u.op_comercializacion_pct) * u.gastos_mm / u.comisiones_mm, 1) == 10.1
    assert round(u.op_computacion_pct * u.gastos_mm / u.comisiones_mm, 1) == 4.8
    assert round(100 * u.encaje_mm / u.ingresos_mm, 1) == 19.0


def test_cuadros_por_administradora():
    a = pd.read_csv(DP / "afp_resultados_por_afp.csv")
    sis = a[a.afp == "Sistema"].set_index("anio")
    suma = a[a.afp != "Sistema"].groupby("anio").ingresos_ordinarios.sum()
    assert ((suma - sis.ingresos_ordinarios).abs() <= 2).all()
    q = a.assign(q=-100 * (a.gastos_personal + a.otros_gastos_operacion) / a.ingresos_ordinarios).set_index(["anio", "afp"]).q.round(1)
    assert (q[(2022, "Habitat")], q[(2025, "Habitat")], q[(2022, "Modelo")], q[(2025, "Modelo")], q[(2025, "Sistema")]) == (36.1, 37.8, 52.9, 41.7, 43.6)
    roe = a[a.anio == 2025].set_index("afp").roe_pct
    assert (roe["Uno"], roe["Provida"], roe["Sistema"]) == (64.84, 11.53, 23.21)


def test_motor_economia_administradoras():
    import sys
    sys.path.insert(0, str(DP.parent / "Dashboards"))
    from components import afp_economia as afe
    d = afe.serie_sistema(pd.read_csv(DP / "afp_resultados_sistema.csv"), pd.read_csv(DP / "afp_resultados_por_afp.csv"))
    pasos = afe.cascada(d, 2025)
    ingresos = sum(v for _, v, t in pasos[:3])
    gastos = -sum(v for _, v, t in pasos[3:7])
    assert abs(ingresos - gastos - pasos[7][1]) < 2 and abs(pasos[7][1] + pasos[8][1] - pasos[9][1]) < 2   # cuadra con el cuadro N° 1
    eq = afe.equilibrio(d, 2025, 5974428, 1294398.91)
    assert round(eq["comision_equilibrio_pct"], 2) == 0.65 and round(eq["comision_implicita_pct"], 2) == 1.28
    e = afe.estres_comision(d, 2025)
    assert e.resultado_mm.iloc[0] > 0 > e.resultado_mm.iloc[-1] and round(eq["baja_max_pct"]) == 49
