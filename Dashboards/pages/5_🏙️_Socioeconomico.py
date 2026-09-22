"""Cruce con variables socioeconómicas: urbanización (Censo 2024, completa) e
ingresos (CASEN 2022, única fuente disponible — encuesta muestral, no censo)."""
import plotly.express as px
import streamlit as st
from utils import load_csv, kpi_card_row, PLOTLY_LAYOUT, MACROZONA, MACROZONA_ORDER, CATEGORICAL

st.set_page_config(page_title="Socioeconómico", page_icon="🏙️", layout="wide")
st.title("🏙️ Envejecimiento y variables socioeconómicas")
st.info(
    "El Censo 2024 es un **censo de derecho** y no pregunta ingresos. La única fuente de ingresos "
    "disponible es **CASEN 2022** (encuesta muestral, no censal — 334/346 comunas con estimación directa). "
    "La urbanización sí viene del propio Censo (100% de cobertura)."
)

urb = load_csv("kpi_urbanizacion_envejecimiento.csv")
ing = load_csv("kpi_ingreso_envejecimiento.csv").dropna(subset=["ingreso_per_capita_prom"])
ing = ing[ing.pob_total >= 500]
urb["macrozona"] = urb["region_nombre"].map(MACROZONA)
ing["macrozona"] = ing["region_nombre_corto"].map(MACROZONA)

p_urb = urb["pct_urbano"].corr(urb["pct_65_mas"])
s_urb = urb["pct_urbano"].corr(urb["pct_65_mas"], method="spearman")
p_ing = ing["ingreso_per_capita_prom"].corr(ing["pct_65_mas"])
s_ing = ing["ingreso_per_capita_prom"].corr(ing["pct_65_mas"], method="spearman")

kpi_card_row([
    ("Correlación % urbano vs % 65+", f"r = {p_urb:.2f}", f"Spearman ρ = {s_urb:.2f} · n={len(urb)} comunas"),
    ("Correlación ingreso vs % 65+", f"r = {p_ing:.2f}", f"Spearman ρ = {s_ing:.2f} · n={len(ing)} comunas"),
])

st.divider()
col1, col2 = st.columns(2)
with col1:
    fig = px.scatter(
        urb, x="pct_urbano", y="pct_65_mas", color="macrozona", category_orders={"macrozona": MACROZONA_ORDER},
        hover_name="comuna_nombre", hover_data={"pob_total": ":,"},
        color_discrete_sequence=CATEGORICAL,
        labels={"pct_urbano": "% población urbana", "pct_65_mas": "% población 65+"},
        trendline="ols", trendline_scope="overall", trendline_color_override="#52514e",
    )
    fig.update_layout(**PLOTLY_LAYOUT, title="Urbanización vs envejecimiento (346 comunas)")
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Comunas más rurales tienden a estar más envejecidas (correlación negativa moderada): el éxodo de "
               "población joven hacia zonas urbanas deja una estructura etaria más vieja en el campo.")

with col2:
    fig = px.scatter(
        ing, x="ingreso_per_capita_prom", y="pct_65_mas", color="macrozona", category_orders={"macrozona": MACROZONA_ORDER},
        hover_name="comuna_nombre", hover_data={"n_muestra": True},
        color_discrete_sequence=CATEGORICAL,
        labels={"ingreso_per_capita_prom": "Ingreso per cápita promedio ($, CASEN 2022)", "pct_65_mas": "% población 65+"},
        trendline="ols", trendline_scope="overall", trendline_color_override="#52514e",
    )
    fig.update_layout(**PLOTLY_LAYOUT, title="Ingreso per cápita vs envejecimiento (326 comunas, pob≥500)")
    st.plotly_chart(fig, use_container_width=True)
    st.caption("La relación NO es lineal simple (Pearson débil, Spearman moderado): conviven dos patrones de "
               "envejecimiento — comunas rurales pobres envejecidas por éxodo juvenil, y comunas urbanas ricas "
               "envejecidas 'in situ' (población que envejece sin irse). Ver tablas abajo.")

st.divider()
c1, c2 = st.columns(2)
with c1:
    st.subheader("Mayor ingreso per cápita")
    st.dataframe(
        ing.nlargest(8, "ingreso_per_capita_prom")[["comuna_nombre", "region_nombre_corto", "ingreso_per_capita_prom", "pct_65_mas"]],
        hide_index=True, use_container_width=True,
    )
with c2:
    st.subheader("Menor ingreso per cápita")
    st.dataframe(
        ing.nsmallest(8, "ingreso_per_capita_prom")[["comuna_nombre", "region_nombre_corto", "ingreso_per_capita_prom", "pct_65_mas"]],
        hide_index=True, use_container_width=True,
    )

st.divider()
st.subheader("Ingreso per cápita promedio por región (CASEN 2022)")
ing_region = load_csv("kpi_ingresos_region.csv")
fig = px.bar(ing_region.sort_values("ingreso_per_capita_prom"), x="ingreso_per_capita_prom", y="region_casen",
             orientation="h", color_discrete_sequence=[CATEGORICAL[0]],
             labels={"ingreso_per_capita_prom": "Ingreso per cápita promedio ($)", "region_casen": ""})
fig.update_layout(**PLOTLY_LAYOUT, title="Ingreso per cápita por región")
st.plotly_chart(fig, use_container_width=True)
