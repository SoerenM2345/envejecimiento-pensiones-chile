"""Motor de «Costos y economía de las administradoras» (sin Streamlit ni lectura de archivos).

Fuente: Superintendencia de Pensiones, «Costos de administración de los Fondos de Pensiones» 2016-2025, procesados por
Scripts/27 en afp_resultados_sistema.csv (sistema) y afp_resultados_por_afp.csv (por administradora). Millones de pesos de cada
año; *_mm_2025 en pesos de 2025 (IPC anual). Ver docs/COSTOS_AFP_HALLAZGOS.md.

Separación estricta: aquí solo el negocio de las administradoras (comisión = ingreso, gastos de administración = costo). El costo
del Estado (Pilar Solidario) está en cost_analysis.py y financiamiento.py.
"""
import numpy as np
import pandas as pd

ANIOS_QUIEBRE = (2020, 2021)   # la Superintendencia reexpresó 2020 (división de Habitat): no comparar crecimientos que crucen este tramo


def serie_sistema(s: pd.DataFrame, por_afp: pd.DataFrame) -> pd.DataFrame:
    """Una fila por año con las razones del sistema. s = afp_resultados_sistema.csv; por_afp = afp_resultados_por_afp.csv.
    Razones en % de la comisión: costo total, venta (personal de ventas + comercialización) y computación; el reparto en % del gasto
    viene del informe con una decimal."""
    d = s.set_index("anio").copy()
    d["costo_sobre_comision"] = 100 * d.gastos_mm / d.comisiones_mm
    d["venta_pct_gasto"] = d.personal_ventas_pct + d.op_comercializacion_pct
    d["venta_sobre_comision"] = d.venta_pct_gasto * d.gastos_mm / d.comisiones_mm
    d["computacion_sobre_comision"] = d.op_computacion_pct * d.gastos_mm / d.comisiones_mm
    d["comision_sobre_ingresos"] = 100 * d.comisiones_mm / d.ingresos_mm
    d["encaje_sobre_ingresos"] = 100 * d.encaje_mm / d.ingresos_mm
    sis = por_afp[por_afp.afp == "Sistema"].set_index("anio")
    d["resultado_antes_impuesto_mm"] = sis.ganancia_antes_impuesto
    d["resultado_sin_encaje_mm"] = sis.ganancia_antes_impuesto - sis.encaje
    d["impuesto_mm"] = -sis.impuesto
    return d


def cascada(d: pd.DataFrame, anio: int) -> list:
    """Del ingreso a la ganancia de un año (millones de pesos del año): [(rótulo, valor, tipo)], tipo = 'abs' | 'rel' | 'total'.
    Ingresos − gastos = resultado antes de impuesto del cuadro N° 1; − impuesto = ganancia."""
    r = d.loc[anio]
    return [
        ("Comisiones", r.comisiones_mm, "abs"),
        ("Rentabilidad del encaje", r.encaje_mm, "rel"),
        ("Otros ingresos", r.otros_ingresos_mm, "rel"),
        ("Personal", -r.gastos_personal_mm, "rel"),
        ("Operación", -r.gastos_operacion_mm, "rel"),
        ("Depreciación", -r.depreciacion_mm, "rel"),
        ("Otros gastos", -r.otros_gastos_mm, "rel"),
        ("Antes de impuesto", r.resultado_antes_impuesto_mm, "total"),
        ("Impuesto", -r.impuesto_mm, "rel"),
        ("Ganancia", r.ganancia_mm, "total"),
    ]


def por_administradora(por_afp: pd.DataFrame, a0: int, a1: int) -> pd.DataFrame:
    """Costo sin depreciación ÷ ingresos ordinarios (%) en a0 y a1, crecimiento nominal de los ingresos y rentabilidad sobre patrimonio
    de a1, por administradora y sistema. Por AFP el informe no separa la comisión: se usan los ingresos ordinarios (incluyen otros
    ingresos operacionales), por eso la razón no es la misma que costo ÷ comisión del sistema."""
    a = por_afp[por_afp.anio.isin([a0, a1])].copy()
    a["costo_sin_dep"] = -(a.gastos_personal + a.otros_gastos_operacion)
    a["razon"] = 100 * a.costo_sin_dep / a.ingresos_ordinarios
    p = a.pivot(index="afp", columns="anio", values=["razon", "ingresos_ordinarios", "roe_pct"])
    out = pd.DataFrame({"razon_0": p[("razon", a0)], "razon_1": p[("razon", a1)],
                        "crec_ingresos_pct": 100 * (p[("ingresos_ordinarios", a1)] / p[("ingresos_ordinarios", a0)] - 1),
                        "roe_1": p[("roe_pct", a1)]})
    return out.sort_values("razon_1")


def equilibrio(d: pd.DataFrame, anio: int, cotizantes: float, ingreso_mensual: float) -> dict:
    """Comisión de equilibrio (escenario): costo anual por cotizante ÷ sueldo imponible anual. Comisión implícita: comisiones ÷
    (cotizantes × sueldo × 12); sobreestimada porque las comisiones incluyen pensionados, ahorro voluntario y Cuenta 2."""
    r = d.loc[anio]
    sueldo_anual = 12 * ingreso_mensual
    costo_cot = r.gastos_mm * 1e6 / cotizantes
    eq = 100 * costo_cot / sueldo_anual
    impl = 100 * r.comisiones_mm * 1e6 / (cotizantes * sueldo_anual)
    return dict(anio=anio, costo_por_cotizante=costo_cot, comision_equilibrio_pct=eq, comision_implicita_pct=impl,
                baja_max_pct=100 * (1 - r.gastos_mm / r.comisiones_mm), sueldo_mensual=ingreso_mensual)


def estres_comision(d: pd.DataFrame, anio: int, bajas=np.arange(0, 71, 5)) -> pd.DataFrame:
    """Escenario: si la comisión baja x % con los mismos gastos, resultado del negocio principal = comisiones − gastos (sin encaje, sin
    otros ingresos y antes de impuesto), millones de pesos del año. No es un pronóstico: no hay reacción de costos ni de afiliados."""
    r = d.loc[anio]
    b = np.asarray(bajas, float)
    res = r.comisiones_mm * (1 - b / 100) - r.gastos_mm
    return pd.DataFrame({"baja_pct": b, "resultado_mm": res})
