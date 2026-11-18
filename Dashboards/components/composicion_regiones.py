"""KPI 1.1, estado actual: el mismo gráfico de «quién cotiza y por qué no cotiza el resto», una pestaña por cada región prioritaria."""
import pandas as pd
import streamlit as st

from components.charts import coverage_composition_chart, mostrar
from utils import es_cl, load_csv
from utils import subtitulo_visible as _subtitulo_visible

RAZONES = [  # grupos de kpi_cobertura_composicion_region.csv -> cómo se nombran en la frase
    (("Ni trabajan ni buscan",), "no participan en el mercado laboral"),
    (("Buscan trabajo (desocupados)",), "buscan trabajo"),
    (("No cotizan: ocupados informales", "No cotizan: ocupados formales fuera de la estadística"), "trabajan sin cotizar"),
]


def _frase(x: pd.DataFrame, chile: pd.DataFrame, nombre: str) -> str:
    """Qué cambia frente a Chile: los puntos de diferencia en cada una de las tres razones por las que no se cotiza (suman la diferencia de cobertura)."""
    g, c = x.set_index("grupo").pct_15_64, chile.set_index("grupo").pct_15_64
    cot, cot_chile = g.filter(like="Cotizan").sum(), c.filter(like="Cotizan").sum()
    partes = []
    for grupos, texto in RAZONES:
        d = sum(g[k] for k in grupos) - sum(c[k] for k in grupos)
        partes.append(f"{abs(d):.1f} puntos {'más' if d > 0 else 'menos'} {texto}")
    return (f"Qué muestra: lo mismo que arriba, para {nombre}. Cotizan {cot:.1f} % frente a {cot_chile:.1f} % de Chile; las razones por las que no cotiza el resto "
            f"cambian así frente a Chile: {partes[0]}, {partes[1]} y {partes[2]}.")


def render_composicion_regiones(prio: pd.DataFrame):
    """prio: regiones prioritarias del criterio elegido (`_prioritarias` de la página), en su orden."""
    d = load_csv("kpi_cobertura_composicion_region.csv")
    chile = d[d.region_id == 0]
    cob_chile = float(chile[chile.grupo.str.startswith("Cotizan")].pct_15_64.sum())
    st.markdown("##### Lo mismo en cada región prioritaria")
    st.markdown("Elige una región: es el mismo gráfico, con la cobertura de Chile como referencia. Las regiones son las de la lista prioritaria elegida más abajo "
                "(por defecto, la que combina nivel, tendencia y brecha).")
    tabs = st.tabs(prio.region_nombre.tolist())
    for tab, r in zip(tabs, prio.itertuples()):
        with tab:
            x = d[d.region_id == r.region_id]
            mostrar(coverage_composition_chart(x, r.region_nombre, cob_chile, f", {x.personas.sum() / 1e6:.2f} millones de personas (Censo 2024)"))
            _subtitulo_visible(_frase(x, chile, r.region_nombre))
    st.caption(es_cl(
        "Los independientes y voluntarios por región son un reparto con la proporción del país (la Superintendencia no publica los cotizantes por tipo y región); "
        "los informales de cada región vienen de la Encuesta Nacional de Empleo, llevados al nivel del Censo con el factor de esa región. Detalle en docs/supuestos_y_limitaciones.md, sección 7."))
