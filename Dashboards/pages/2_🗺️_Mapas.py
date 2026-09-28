"""Mapas territoriales del envejecimiento — choropleth por comuna y por región."""
import pandas as pd
import plotly.express as px
import streamlit as st
from utils import load_csv, load_geojson, PLOTLY_LAYOUT, PLOTLY_DL_CONFIG

st.set_page_config(page_title="Mapas territoriales", page_icon="🗺️", layout="wide")
st.title("🗺️ Mapas territoriales del envejecimiento")

nivel = st.radio("Nivel", ["Comuna", "Región"], horizontal=True)

VARS_COMUNA = {
    "% población 65+": "pct_65_mas",
    "% población 0-14": "pct_0_14",
    "% población 80+": "pct_80_mas",
    "Índice de envejecimiento (65+/0-14 ×100)": "indice_envejecimiento",
    "Índice de dependencia de vejez": "indice_dependencia_vejez",
    "Edad mediana": "edad_mediana",
    "% urbano": "pct_urbano",
}
VARS_REGION = dict(VARS_COMUNA)

if nivel == "Comuna":
    geojson = load_geojson("comunas_chile.geojson")
    df = load_csv("indicadores_comuna.csv").rename(columns={"comuna": "comuna_id"})
    ingresos = load_csv("kpi_ingresos_comuna.csv")[["comuna_id", "ingreso_per_capita_prom", "n_muestra"]]
    df = df.merge(ingresos, on="comuna_id", how="left")
    VARS_COMUNA["Ingreso per cápita (CASEN 2022)"] = "ingreso_per_capita_prom"
    var_label = st.selectbox("Variable", list(VARS_COMUNA.keys()))
    var = VARS_COMUNA[var_label]
    loc_col, feat_key, name_col = "comuna_id", "properties.comuna_id", "comuna_nombre"
else:
    geojson = load_geojson("regiones_chile.geojson")
    df = load_csv("indicadores_region.csv").rename(columns={"region": "region_id"})
    pres = load_csv("kpi_presion_previsional_region.csv")[[
        "region_id", "cobertura_previsional_pct", "razon_soporte_previsional"
    ]]
    df = df.merge(pres, on="region_id", how="left")
    VARS_REGION["Cobertura previsional (%)"] = "cobertura_previsional_pct"
    VARS_REGION["Cotizantes por adulto mayor"] = "razon_soporte_previsional"
    var_label = st.selectbox("Variable", list(VARS_REGION.keys()))
    var = VARS_REGION[var_label]
    loc_col, feat_key, name_col = "region_id", "properties.region_id", "region_nombre"

fig = px.choropleth_map(
    df, geojson=geojson, locations=loc_col, featureidkey=feat_key,
    color=var, hover_name=name_col,
    hover_data={loc_col: False, var: ":.2f"},
    color_continuous_scale="Blues",
    map_style="carto-positron",
    center={"lat": -35.5, "lon": -71.5}, zoom=3.4,
    opacity=0.85,
)
fig.update_layout(**{**PLOTLY_LAYOUT, "margin": dict(l=0, r=0, t=30, b=0)}, height=720,
                   title=f"{var_label} — {nivel.lower()}")
st.plotly_chart(fig, use_container_width=True, config=PLOTLY_DL_CONFIG)

if nivel == "Comuna":
    st.caption("Nota: la comuna Antártica (12202) no tiene geometría publicada en la fuente usada y queda fuera del mapa (sí está en las tablas).")

with st.expander("Ver tabla"):
    cols = [name_col, var] if nivel == "Región" else [name_col, "region_nombre", var]
    st.dataframe(df[cols].sort_values(var, ascending=False), use_container_width=True, hide_index=True)
