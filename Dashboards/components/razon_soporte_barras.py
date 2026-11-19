"""KPI 1.2: cotizantes por persona de 65+ en años pasados y en el escenario, como barras; compartido por las páginas final y extendida.

  - país (Scripts/32 hace el mismo PNG): 2010, 2015, 2020 y 2024 observados; 2030, 2040, 2050 y 2070 con la cobertura de 2025 constante
    (la misma serie del punto crítico, `pc_serie("pais", ...)`).
  - regiones (Scripts/33 -> kpi_razon_soporte_region_anios.csv): 2010, 2015, 2020 y 2024 observados; 2035 y 2050 del escenario regional con la
    cobertura de 2024 constante. Metropolitana frente a las regiones críticas (la lista recomendada del KPI 1.1) o todas las regiones.
"""
import pandas as pd
import streamlit as st
from utils import load_csv, es_cl, cargar_escenarios
from components import critical_point as cp
from components.charts import mostrar, estilo_kpi, support_ratio_bars, support_ratio_bars_panels, _titulo

ANIOS_PAIS = [2010, 2015, 2020, 2024, 2030, 2040, 2050, 2070]
METROPOLITANA = "Metropolitana"
VISTAS = ["Metropolitana y regiones críticas", "Todas las regiones"]


def _n(v: float) -> str:
    """Dos decimales con punto: _titulo y es_cl lo pasan al formato chileno."""
    return f"{v:.2f}"


def _barras_pais(pc_serie):
    cfg = cargar_escenarios()
    d, _ = pc_serie("pais", 0, 0, cp.Escenario(crec_salarial=cfg["crecimiento_salario_real"]["base"], carga_max=cfg["tope_carga"]["base"],
                                                 pgu_250=cfg["pgu_250"]))
    d = d[d.anio.isin(ANIOS_PAIS)].rename(columns={"razon_soporte": "razon"})[["anio", "razon"]]
    d["tipo"] = ["observado" if a <= cp.ANIO_BASE_REGION else "escenario" for a in d.anio]
    r0, r1, rf = d.iloc[0], d[d.anio == cp.ANIO_BASE_REGION].iloc[0], d.iloc[-1]
    titulo = _titulo(f"Chile pasó de {_n(r0.razon)} cotizantes por persona de 65+ en {int(r0.anio)} a {_n(r1.razon)} en {int(r1.anio)}; "
                     f"con la cobertura de 2025 constante llegaría a {_n(rf.razon)} en {int(rf.anio)}",
                     "Cotizantes de diciembre (con región) por persona de 65+; población 65+ del Censo 2024")
    return support_ratio_bars(d, titulo)


def _criticas() -> list:
    r = load_csv("kpi_cobertura_regiones.csv")
    return list(r[r.prioridad_rangos.notna()].sort_values("prioridad_rangos").region_nombre)


def _paneles_regiones(vista: str):
    d = load_csv("kpi_razon_soporte_region_anios.csv")
    criticas = _criticas()
    otras = sorted(set(d.region_nombre) - set(criticas) - {METROPOLITANA})
    orden = [METROPOLITANA] + criticas + (otras if vista == VISTAS[1] else [])
    r24 = d[d.anio == cp.ANIO_BASE_REGION].set_index("region_nombre").razon
    r50 = d[d.anio == 2050].set_index("region_nombre").razon
    menos = [n for n in criticas if r24[n] < r24[METROPOLITANA]]
    titulo = _titulo(f"{len(menos)} de las {len(criticas)} regiones críticas ya tienen menos cotizantes por persona de 65+ que la Metropolitana "
                     f"({_n(r24[METROPOLITANA])} en 2024)" + (" y todas bajan hacia 2050" if (r50 < r24).all() else ""),
                     "En negrita, las regiones críticas del KPI 1.1; mismo eje en todos los paneles",
                     ancho=70)
    fig = support_ratio_bars_panels(d, orden, titulo, columnas=3 if len(orden) <= 9 else 4, destacadas=tuple(criticas))
    return fig, criticas, menos, r24


def render_razon_soporte_barras(pc_serie):
    """Barras del país y paneles por región. `pc_serie`: la función de la página que corre el motor del punto crítico."""
    st.divider()
    st.markdown("#### Cotizantes por persona de 65+: del pasado al escenario")
    st.markdown("Los años pasados muestran cuánto ya se perdió; el escenario, hacia dónde va si la cobertura no cambia.")
    mostrar(estilo_kpi(_barras_pais(pc_serie), alto=480), num="1.2/rs_pais")
    st.markdown("##### ¿Y en las regiones críticas frente a la Metropolitana?")
    vista = st.radio("Regiones", VISTAS, horizontal=True, key="s12_barras_regiones")
    fig, criticas, menos, r24 = _paneles_regiones(vista)
    mostrar(estilo_kpi(fig, alto=fig.layout.height), num="1.2/rs_regiones_criticas" if vista == VISTAS[0] else "1.2/rs_regiones_todas")
    mas = [n for n in criticas if n not in menos]
    st.caption(es_cl(
        "Observado: cotizantes de diciembre (Superintendencia de Pensiones) sobre la población 65+ de cada región; para 2010, 2015 y 2020 la "
        "población es la proyección INE base 2017 llevada al nivel del Censo 2024 de cada región. Escenario 2035 y 2050: la cobertura de 2024 "
        "constante y la población 65+ regional del escenario (reparto de tasas nacionales; el INE no publica la proyección regional base 2024). "
        "Biobío y Ñuble se publicaron juntas hasta 2017: sus barras de 2010 y 2015 son el dato de las dos regiones, en tono claro. "
        + (f"Con más cotizantes por persona de 65+ que la Metropolitana en 2024: {', '.join(mas)} ({', '.join(_n(r24[n]) for n in mas)}); "
           "entra a la lista por otro factor (tendencia o tamaño), no por el nivel." if mas else "")))
